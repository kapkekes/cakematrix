from sqlite3 import Connection, Cursor, connect
from pathlib import Path

from discord import Bot, Cog


class Database(Cog):
    bot: Bot
    __connection: Connection
    __cursor: Cursor

    def __init__(self, bot: Bot, db_path: Path):
        self.bot = bot
        self.__connection = connect(db_path)
        self.__cursor = self.__connection.cursor()

    def commit(self):
        self.__connection.commit()

    @property
    def cursor(self):
        return self.__cursor
