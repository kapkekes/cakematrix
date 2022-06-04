from importlib.resources import path
from logging import getLogger
from sqlite3 import Connection, Cursor, connect

from discord import Bot, Cog

import resources


logger = getLogger(__name__)


with path(resources, "database.sqlite3") as p:
    PATH_TO_DATABASE = p


class DatabaseHandler(Cog):
    """Entry point to databases for bots.

    Creates a connection and a cursor to the local database.
    """
    bot: Bot
    __connection: Connection
    __cursor: Cursor

    def __init__(self, bot: Bot):
        self.bot = bot
        self.__connection = connect(PATH_TO_DATABASE)
        self.__cursor = self.__connection.cursor()

    def commit(self):
        """
        Shortcut to connection.commit()
        """
        self.__connection.commit()

    @property
    def cursor(self):
        return self.__cursor

    @property
    def connection(self):
        return self.__connection


def setup(bot: Bot):
    bot.add_cog(DatabaseHandler(bot))
    logger.info("Database handler cog was added to your bot.")