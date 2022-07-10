import datetime as dt
import importlib.resources as ilr
import pickle as pkl
import sqlite3 as sql
from dataclasses import dataclass

from logging import getLogger
from random import choice
from typing import List, Tuple, Callable, Dict

import discord
import discord.ext.tasks as tasks

from resources import timezone
from resources.activities import optionChoices
from source.exceptions import CogNotFoundError
from source.cogs.database_handler import DatabaseHandler
from utilities import str_to_datetime, datetime_to_str
from builders import create_embed, create_enroll_view, numbered_list, notify_main, notify_reserve
from secret import GUILDS

import source.queries as queries
import resources


logger = getLogger(__name__)

DECORATORS = {
    "enroll_create": {
        "guild_ids": GUILDS,
        "name": "собрать",
        "description": "создать сбор",
        "options": [
            discord.Option(
                str, choices=optionChoices,
                name="активность", description="активность, в которую ведётся сбор"
            ),
            discord.Option(
                str,
                name="время", description="время начала (в формате ДД.ММ-ЧЧ:ММ)"
            ),
            discord.Option(
                str, default="отсутствует",
                name="заметка", description="заметка, прикреплённая к сбору (\\n для новой строки)"
            )
        ]
    }
}





def parse_custom_id(custom_id: str) -> Tuple[str, int]:
    a, b = custom_id.split("_")
    return a, int(b)


with ilr.path(resources, "database.sqlite3") as p:
    PATH_TO_DATABASE = p


class LFG(discord.Cog):
    """Cog with looking-for-group functionality.

    Adds several slash commands for creating and managing LFG posts.
    """
    bot: discord.Bot
    _functions: Dict[str, Callable]

    def __init__(self, bot: discord.Bot):
        self.bot = bot

        async def enroll(interaction: discord.Interaction):
            db_handler: DatabaseHandler

            if (db_handler := self.bot.get_cog("DatabaseHandler")) is None:  # type: ignore
                return logger.error("LFG cog can't find a Database handler")

            user, response = interaction.user, interaction.response
            target, response_id = parse_custom_id(interaction.custom_id)
            opposite = "main" if target == "reserve" else "reserve"

            db_handler.cursor.execute(queries.fetch_post, (response_id,))

            if (row := db_handler.cursor.fetchone()) is None:
                logger.debug(f"{user} pushed strange button to enroll")
                return await response.send_message("Ошибка: записи... не существует¿", ephemeral=True)

            record = Record(response_id, row)

            if record.author_id == user.id:
                logger.debug(f"{user} tested the system and tried to enroll to their LFG")
                return await response.send_message("Ошибка: нельзя записаться к самому себе.", ephemeral=True)

            if user.id in getattr(record, opposite):
                logger.debug(f"{user} tried to enroll to both fireteams in activity with ID {response_id}")
                return await response.send_message("Ошибка: нельзя записаться сразу в оба состава.", ephemeral=True)

            if len(getattr(record, target)) >= 5:
                logger.debug(f"{user} tried to enroll to full {target} fireteam in activity with ID {response_id}")
                return await response.send_message("Ошибка: состав уже заполнен(", ephemeral=True)

            if user.id in getattr(record, target):
                logger.debug(f"{user} excluded from {target} fireteam, activity with ID {response_id}")
                getattr(record, target).remove(user.id)
            else:
                logger.debug(f"{user} enrolled to {target} fireteam, activity with ID {response_id}")
                getattr(record, target).append(user.id)

            db_handler.con.execute(getattr(queries.update, target), (getattr(record, target),))
            db_handler.con.commit()

            if fireteam == "main":
                write_to_database = (fetched_b, opposite_b, response_id)
                index = 1
                fetched.insert(0, author_id)
            else:
                write_to_database = (opposite_b, fetched_b, response_id)
                index = 2

            value = [await bot.fetch_user(int(user_id)) for user_id in fetched]

            db_handler.con.execute(QUERIES["enroll_update"], write_to_database)
            db_handler.con.commit()
            await response.send_message(f"*\\*{choice(resources.reactions)}\\**", delete_after=5)

            embed = interaction.message.embeds[0]
            embed._fields[index].value = numbered_list(value)
            await interaction.message.edit(embed=embed)

        self._functions["enroll"] = enroll

    @discord.slash_command(**DECORATORS["enroll_create"])
    async def create(self, context: discord.ApplicationContext, raid, time, note):
        db_handler: DatabaseHandler

        if (db_handler := self.bot.get_cog("DatabaseHandler")) is None:  # type: ignore
            return logger.error("LFG cog can't find a Database handler")

        author = context.user

        try:
            timestamp = str_to_datetime(time)
        except ValueError:
            logger.debug(f"{author} used /lfg command, but put incorrect format time")
            return await context.respond("Ошибка: время имеет некорректный формат.", ephemeral=True)

        response: discord.Interaction = await context.respond("Создаю сбор...")

        await response.edit_original_message(
            content="",
            embed=create_embed(raid, author, timestamp, note, response.id),
            view=create_enroll_view(response.id, self._functions["enroll"])
        )

        db_handler.con.execute(queries.create_post, (response.id, raid, author.id, timestamp.timestamp()), )
        db_handler.con.commit()

        logger.debug(f"{author} created a LFG post to {raid} on {timestamp}")


def setup(bot: discord.Bot):
    bot.add_cog(LFG(bot))
    logger.info("LFG cog was added to your bot")
