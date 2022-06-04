from importlib.resources import path
from logging import getLogger

from discord import ApplicationContext, Bot, Cog, Option, slash_command

from source.exceptions import CogNotFoundError
from source.cogs.database_handler import DatabaseHandler
from secret import GUILDS

import resources


logger = getLogger(__name__)


decorators = {
    "create_lfg_post": {
        "guild_ids": GUILDS,
        "name": "lfg",
        "description": "create a LFG post",
        "name_localizations": {"ru": "собрать"},
        "description_localizations": {"ru": "создать сбор"},
        "options": [
            Option(
                str,
                name="lfg",
                descripiton="the target raid",
                name_localizations={"ru": "рейд"},
                description_localizations={"ru": "рейд, в который ведётся сбор"}
            ),
            Option(
                str,
                name="time",
                descripiton="the start time (in DD.MM-HH:MM format)",
                name_localizations={"ru": "время"},
                description_localizations={"ru": "время начала (в формате ДД.ММ-ЧЧ:ММ)"}
            ),
            Option(
                str,
                name="note",
                descripiton="the note, which will be written in the post (\\n for a new line)",
                name_localizations={"ru": "заметка"},
                description_localizations={"ru": "заметка, записана в сборе (\\n для новой строки)"},
                default="отсутствует",
            )
        ]
    }
}


with path(resources, "database.sqlite3") as p:
    PATH_TO_DATABASE = p


class LFG(Cog):
    """Cog with looking-for-group functionality.

    Adds several slash commands for creating and managing LFG posts.
    """
    bot: Bot
    __db_handler: DatabaseHandler

    def __init__(self, bot: Bot):
        self.bot = bot

        # Sadly, but the return type of the get_cog function is hardcoded as Cog
        self.__db_handler = bot.get_cog("DatabaseHandler")  # type: ignore

    @slash_command(**decorators["create_lfg_post"])
    async def create_lfg_post(self, context: ApplicationContext, raid, time, note):
        ...
        # author = context.user
        # logger.warning(f'{author} used {colored("/lfg", attrs=["bold"])}')
        #
        # try:
        #     timestamp = convert_to_datetime(time)
        # except ValueError:
        #     logger.warning(f'{author} put incorrect format time')
        #     return await context.respond('Ошибка: время имеет некорректный формат.', ephemeral=True)
        #
        # response: discord.Interaction = await context.respond('Создаю сбор...')
        # embed = emb.build_embed(raid, author, timestamp, note, response.id)
        # buttons = elm.create_enroll_view(response.id, enroll)
        #
        # await response.edit_original_message(content='', embed=embed, view=buttons)
        #
        # self.__db.create_lfg(response_id=response.id, activity=raid, author_id=author.id, timestamp=timestamp)


def setup(bot: Bot):
    if bot.get_cog("DatabaseHandler") is None:
        raise CogNotFoundError("LFG cog can't be added without Database cog; ensure, that you already added it.")

    bot.add_cog(LFG(bot))
    logger.info("LFG cog was added to your bot.")
