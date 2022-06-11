import importlib.resources as ilr
import logging as log
import sqlite3 as sql

import discord

import resources


logger = log.getLogger(__name__)

with ilr.path(resources, "database.sqlite3") as p:
    PATH_TO_DATABASE = p


class DatabaseHandler(discord.Cog):
    """Entry point to databases for bots.

    Creates a connection and a cursor to the local database.
    """
    bot: discord.Bot
    __connection: sql.Connection
    __cursor: sql.Cursor

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.__connection = sql.connect(PATH_TO_DATABASE)
        self.__cursor = self.__connection.cursor()

    @property
    def con(self):
        return self.__connection

    @property
    def cursor(self):
        return self.__cursor


def setup(bot: discord.Bot):
    bot.add_cog(DatabaseHandler(bot))
    logger.info("Database handler cog was added to your bot")
