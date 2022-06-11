from importlib.resources import path, contents, read_text
from logging import getLogger
from random import choice

from discord import ApplicationContext, Bot, Cog, Interaction, Option, slash_command

from resources.activities import optionChoices
from source.exceptions import CogNotFoundError
from source.cogs.database_handler import DatabaseHandler
from utilities.conventers import str_to_datetime
from builders import build_embed, build_enroll_view, numbered_list
from secret import GUILDS

import source.queries
import resources


logger = getLogger(__name__)


DECORATORS = {
    "create": {
        "guild_ids": GUILDS,
        "name": "lfg",
        "description": "create a LFG post",
        "name_localizations": {"ru": "собрать"},
        "description_localizations": {"ru": "создать сбор"},
        "options": [
            Option(
                str,
                name="raid", choices=optionChoices,
                description="the target raid",
                name_localizations={"ru": "рейд"},
                description_localizations={"ru": "рейд, в который ведётся сбор"}
            ),
            Option(
                str,
                name="time",
                description="the start time (in DD.MM-HH:MM format)",
                name_localizations={"ru": "время"},
                description_localizations={"ru": "время начала (в формате ДД.ММ-ЧЧ:ММ)"}
            ),
            Option(
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
    query[:-4]: ' '.join(read_text(source.queries, query).split())
    for query in [file for file in contents(source.queries) if ".sql" in file.lower()]
}
OPPOSITE = {
    "main": "reserve",
    "reserve": "main"
}
LOL = ["пух", "жмых", "ебуньк", "ту-дуц"]

with path(resources, "database.sqlite3") as p:
    PATH_TO_DATABASE = p


class LFG(Cog):
    """Cog with looking-for-group functionality.

    Adds several slash commands for creating and managing LFG posts.
    """
    bot: Bot
    db_handler: DatabaseHandler

    def __init__(self, bot: Bot):
        self.bot = bot

        # Sadly, but the return type of the get_cog function is hardcoded as Cog
        self.db_handler = bot.get_cog("DatabaseHandler")  # type: ignore

    @slash_command(**DECORATORS["create"])
    async def create(self, context: ApplicationContext, raid, time, note):
        author = context.user

        try:
            timestamp = str_to_datetime(time)
        except ValueError:
            logger.debug(f"{author} used /lfg command, but put incorrect format time")
            return await context.respond("Ошибка: время имеет некорректный формат.", ephemeral=True)

        response: Interaction = await context.respond("Создаю сбор...")

        await response.edit_original_message(
            content="",
            embed=build_embed(raid, author, timestamp, note, response.id),
            view=build_enroll_view(response.id, pass_to_enroll(self))
        )

        self.db_handler.cursor.execute(QUERIES["create"], (response.id, raid, author.id, timestamp))
        self.db_handler.commit()

        logger.debug(f"{author} created a LFG post to {raid} on {timestamp}")


def pass_to_enroll(cog: LFG):
    db_handler = cog.db_handler
    bot = cog.bot

    async def enroll(interaction: Interaction):
        fireteam, response_id = interaction.custom_id.split('_')
        response_id = int(response_id)

        db_handler.cursor.execute(QUERIES["fetch"], (response_id,))
        user = interaction.user
        response = interaction.response

        if (result := db_handler.cursor.fetchone()) is None:
            logger.debug(f"{user} pushed strange button to enroll")
            return await response.send_message("Ошибка: записи... не существует¿", ephemeral=True)

        (_, _, author_id, time, main, reserve) = result

        fetcher = {
            "main": (main, reserve),
            "reserve": (reserve, main)
        }

        fetched, opposite = fetcher[fireteam]
        fetched = [int(i) for i in fetched.split()]
        opposite = [int(i) for i in opposite.split()]

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

        fetched = " ".join(map(str, fetched))
        value = []

        if fireteam == "main":
            t = (author_id, time, fetched, reserve, response_id)
            index = 1
            name = ":blue_square:  | Основной состав"
            value.append(author_id)
        else:
            t = (author_id, time, main, fetched, response_id)
            index = 2
            name = ":green_square:  | Резервный состав"

        value += fetched
        value = [await bot.fetch_user(int(user_id)) for user_id in fetched]

        db_handler.cursor.execute(QUERIES["update"], t)
        db_handler.commit()
        await response.send_message(f"*\\*{choice(LOL)}\\**", delete_after=5)

        embed = interaction.message.embeds[0]._fields
        embed.set_field_at(index, name=name, inline=False, value=numbered_list(value))
        await interaction.message.edit(embed=embed)

    return enroll


def setup(bot: Bot):
    if bot.get_cog("DatabaseHandler") is None:
        raise CogNotFoundError("LFG cog can't be added without Database cog; ensure, that you already added it.")

    bot.add_cog(LFG(bot))
    logger.info("LFG cog was added to your bot")
