import datetime
import importlib.resources as ilr
import pickle as pkl

from logging import getLogger
from random import choice
from typing import List, Tuple

import discord
import discord.ext.tasks as tasks

from resources.activities import optionChoices
from source.exceptions import CogNotFoundError
from source.cogs.database_handler import DatabaseHandler
from utilities import str_to_datetime, datetime_to_str
from builders import build_lfg_embed, build_enroll_view, numbered_list, notify_main, notify_reserve
from secret import GUILDS

import source.queries
import resources


logger = getLogger(__name__)

DECORATORS = {
    "enroll_create": {
        "guild_ids": GUILDS,
        "name": "lfg",
        "description": "create a LFG post",
        "name_localizations": {"ru": "собрать"},
        "description_localizations": {"ru": "создать сбор"},
        "options": [
            discord.Option(
                str,
                name="raid", choices=optionChoices,
                description="the target raid",
                name_localizations={"ru": "рейд"},
                description_localizations={"ru": "рейд, в который ведётся сбор"}
            ),
            discord.Option(
                str,
                name="time",
                description="the start time (in DD.MM-HH:MM format)",
                name_localizations={"ru": "время"},
                description_localizations={"ru": "время начала (в формате ДД.ММ-ЧЧ:ММ)"}
            ),
            discord.Option(
                str,
                name="note", default="отсутствует",
                description="the note, which will be written in the post (\\n for a new line)",
                name_localizations={"ru": "заметка"},
                description_localizations={"ru": "заметка, записана в сборе (\\n для новой строки)"}
            )
        ]
    }
}
QUERIES = {
    query[:-4]: ' '.join(ilr.read_text(source.queries, query).split())
    for query in [file for file in ilr.contents(source.queries) if ".sql" in file.lower()]
}
REACTIONS = [
    "пух",
    "жмых",
    "ту-дуц",
]

with ilr.path(resources, "database.sqlite3") as p:
    PATH_TO_DATABASE = p


def dumps_empty() -> bytes:
    return pkl.dumps(list())


class LFG(discord.Cog):
    """Cog with looking-for-group functionality.

    Adds several slash commands for creating and managing LFG posts.
    """
    bot: discord.Bot
    db_handler: DatabaseHandler

    def __init__(self, bot: discord.Bot):
        self.bot = bot

        # Sadly, but the return type of the get_cog function is hardcoded as Cog
        self.db_handler = bot.get_cog("DatabaseHandler")  # type: ignore

        self.notify.start()

    @discord.slash_command(**DECORATORS["enroll_create"])
    async def create(self, context: discord.ApplicationContext, raid, time, note):
        author = context.user

        try:
            timestamp = str_to_datetime(time)
        except ValueError:
            logger.debug(f"{author} used /lfg command, but put incorrect format time")
            return await context.respond("Ошибка: время имеет некорректный формат.", ephemeral=True)

        response: discord.Interaction = await context.respond("Создаю сбор...")

        await response.edit_original_message(
            content="",
            embed=build_lfg_embed(raid, author, timestamp, note, response.id),
            view=build_enroll_view(response.id, pass_to_enroll(self))
        )

        self.db_handler.con.execute(
            QUERIES["enroll_create"],
            (response.id, raid, author.id, timestamp, dumps_empty(), dumps_empty())
        )
        self.db_handler.con.commit()

        logger.debug(f"{author} created a LFG post to {raid} on {timestamp}")

    @tasks.loop(seconds=60)
    async def notify(self):
        self.db_handler.cursor.execute(QUERIES["notify"], (datetime_to_str(datetime.datetime.now()),))

        raw_posts: List[Tuple[int, int, bytes, bytes]] = list(map(tuple, self.db_handler.cursor.fetchall()))

        posts: List[Tuple[int, List[int], List[int]]] = [
            (response_id, [] + pkl.loads(main), pkl.loads(reserve))
            for response_id, author_id, main, reserve in raw_posts
        ]

        del raw_posts

        for response_id, main, reserve in posts:
            embed = self.bot.get_message(response_id).embeds[0]

            embed = notify_main(embed)
            for user_id in main:
                user = await self.bot.fetch_user(user_id)

                if user.can_send(discord.Embed):
                    await user.send(embed=embed)

            embed = notify_reserve(embed)
            for user_id in reserve:
                user = await self.bot.fetch_user(user_id)

                if user.can_send(discord.Embed):
                    await user.send(embed=embed)


def pass_to_enroll(cog: LFG):
    db_handler = cog.db_handler
    bot = cog.bot

    async def enroll(interaction: discord.Interaction):
        fireteam, response_id = interaction.custom_id.split('_')
        response_id = int(response_id)

        db_handler.cursor.execute(QUERIES["enroll_fetch"], (response_id,))
        user, response = interaction.user, interaction.response

        if (result := db_handler.cursor.fetchone()) is None:
            logger.debug(f"{user} pushed strange button to enroll")
            return await response.send_message("Ошибка: записи... не существует¿", ephemeral=True)

        author_id: int
        fetched_b: bytes
        opposite_b: bytes

        if fireteam == "main":
            author_id, fetched_b, opposite_b = result
        elif fireteam == "reserve":
            author_id, opposite_b, fetched_b = result
        else:
            logger.debug(f"{user} pushed strange button to enroll")
            return await response.send_message("Ошибка: выбрана несуществующая группа¿", ephemeral=True)

        fetched: List[int] = pkl.loads(fetched_b)
        opposite: List[int] = pkl.loads(opposite_b)

        if user.id == author_id:
            logger.debug(f"{user} tested the system and tried to enroll to their LFG")
            return await response.send_message("Ошибка: нельзя записаться к самому себе.", ephemeral=True)

        if user.id in opposite:
            logger.debug(f"{user} tried to enroll to both fireteams in activity with ID {response_id}")
            return await response.send_message("Ошибка: нельзя записаться сразу в оба состава.", ephemeral=True)

        if len(fetched) >= 5:
            logger.debug(f"{user} tried to enroll to full {fireteam} fireteam in activity with ID {response_id}")
            return await response.send_message("Ошибка: состав уже заполнен(", ephemeral=True)

        if user.id in fetched:
            logger.debug(f"{user} excluded from {fireteam} fireteam, activity with ID {response_id}")
            fetched.remove(user.id)
        else:
            logger.debug(f"{user} enrolled to {fireteam} fireteam, activity with ID {response_id}")
            fetched.append(user.id)

        fetched_b = pkl.dumps(fetched)
        opposite_b = pkl.dumps(opposite)

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
        await response.send_message(f"*\\*{choice(REACTIONS)}\\**", delete_after=5)

        embed = interaction.message.embeds[0]
        embed._fields[index].value = numbered_list(value)
        await interaction.message.edit(embed=embed)

    return enroll


def setup(bot: discord.Bot):
    if bot.get_cog("DatabaseHandler") is None:
        raise CogNotFoundError("LFG cog can't be added without Database cog; ensure, that you already added it.")

    bot.add_cog(LFG(bot))
    logger.info("LFG cog was added to your bot")