from pickle import dumps, loads
from datetime import datetime
from sqlite3 import Connection
from typing import TypeVar, NamedTuple, Iterator

import discord
from discord import Message, User

import source.queries as queries
from source.classes.exceptions import AlreadyEnrolledError, FullFireteamError
from source.classes.enroll_view import EnrollView, Callback
from resources.activities import profiles
from resources.constants import timezone, timings
from resources.design import colors

ID = int
OP = TypeVar("OP", bound="OptimizedPost")


class Notification(NamedTuple):
    channel_id: ID
    message_id: ID

    main: list[ID]
    reserve: list[ID]


class OptimizedPost:
    message: Message
    activity: str
    time: datetime

    author: ID
    _main: list[ID]
    _reserve: list[ID]

    __connection: Connection

    def __init__(self, message: Message, activity: str, time: datetime):
        self.message = message
        self.activity = activity
        self.time = time

    def set_author(self, author: User):
        if author.bot:
            raise ValueError("a bot cannot be set as author of a post")

        if self.author == author.id:
            raise ValueError("this user is already the author of the post")

        self.author = author.id
        embed = self.new_embed()
        new_main_value = embed.fields[1].value.split("\n")

        if author.id in self._main:
            index = self._main.index(author.id)
            del new_main_value[index], self._main[index]
            self.__connection.execute(queries.update.main, (dumps(self._main), self.message.id))
        elif author.id in self._reserve:
            index = self._reserve.index(author.id)
            new_reserve_value = embed.fields[2].value.split("\n")
            del new_reserve_value[index], self._reserve[index]
            embed._fields[2].value = "\n".join(new_reserve_value)
            self.__connection.execute(queries.update.reserve, (dumps(self._reserve), self.message.id))

        new_main_value.insert(0, f"#1 - {author.mention} - {author.display_name}")
        embed._fields[1].value = "\n".join(new_main_value)

        self.__connection.execute(queries.update.author, (self.author, self.message.id))
        self.__connection.commit()

        return self.message.edit(embed=embed)

    def set_time(self, time: datetime):
        self.time = time
        self.__connection.execute(queries.update.unix_time, (self.time.timestamp(), self.message.id))
        self.__connection.commit()

        embed = self.new_embed()
        embed.description = f"Время проведения: **{self.time:%d.%m.%Y} в {self.time:%H:%M} (UTC+3)**."

        return self.message.edit(embed=embed)

    def set_note(self, note: str):
        embed = self.new_embed()
        embed._fields[0].value = note.replace("\\n", "\n")

        return self.message.edit(embed=embed)

    def alter_in_main(self, user: User):
        if user.id == self.author:
            raise ValueError("author can't enroll to their post")

        if user.id in self._reserve:
            raise AlreadyEnrolledError("this user has already enrolled to reserve fireteam")

        embed = self.new_embed()
        new_value = embed._fields[1].value.split("\n")

        if user.id in self._main:
            index = self._main.index(user.id)
            del self._main[index], new_value[index + 1]
            new_value = [f"#{position}{string[2:]}" for position, string in enumerate(new_value, start=1)]
        elif len(self._main) >= 5:
            raise FullFireteamError("main fireteam is already full")
        else:
            self._main.append(user.id)
            new_value += f"\n#{len(self._main)} - {user.mention} - {user.display_name}"

        self.__connection.execute(queries.update.main, (dumps(self._main), self.message.id))
        self.__connection.commit()

        embed._fields[1].value = "\n".join(new_value)

        return self.message.edit(embed=embed)

    def alter_in_reserve(self, user: User):
        if user.id == self.author:
            raise ValueError("author can't enroll to their post")

        if user.id in self._reserve:
            raise AlreadyEnrolledError("this user has already enrolled to reserve fireteam")

        embed = self.new_embed()
        new_value = embed._fields[2].value.split("\n")

        if not self._reserve:
            self._reserve.append(user.id)
            new_value = f"#1 - {user.mention} - {user.display_name}"
        elif user.id in self._reserve and len(self._reserve) == 1:
            self._reserve.remove(user.id)
            new_value = "здесь ещё никого нет"
        elif user.id in self._reserve:
            index = self._reserve.index(user.id)
            del self._reserve[index], new_value[index]
            new_value = [f"#{position}{string[2:]}" for position, string in enumerate(new_value, start=1)]
        elif len(self._reserve) >= 5:
            raise FullFireteamError("reserve fireteam is already full")
        else:
            self._reserve.append(user.id)
            new_value += f"\n#{len(self._reserve)} - {user.mention} - {user.display_name}"

        self.__connection.execute(queries.update.reserve, (dumps(self._reserve), self.message.id))
        self.__connection.commit()

        embed._fields[2].value = "\n".join(new_value)

        return self.message.edit(embed=embed)

    def cancel(self, reason: str):
        embed = self.new_embed()
        embed._colour = colors["cancel"]
        embed.set_author(
            name="Сбор был отменён."
        ).set_field_at(
            index=0, name=":closed_book: | Причина отмены сбора", inline=False, value=reason.replace("\\n", "\n")
        )

        self.__connection.execute(queries.delete, (self.message.id,))
        self.__connection.commit()

        return self.message.edit(embed=embed, view=None, delete_after=timings["delete"].seconds)

    def delete(self):
        self.__connection.execute(queries.delete, (self.message.id,))
        self.__connection.commit()

        return self.message.delete()

    def new_embed(self):
        return self.message.embeds[0].copy()

    @property
    def main(self):
        return self._main

    @property
    def reserve(self):
        return self._reserve

    @classmethod
    def set_connection(cls, connection: Connection):
        cls.__connection = connection

    @classmethod
    async def create(cls,
                     message: Message,
                     activity: str,
                     author: User,
                     time: datetime,
                     note: str,
                     main_callback: Callback,
                     reserve_callback: Callback) -> OP:
        post = cls(message, activity, time)
        post.author = author.id
        post._main = []
        post._reserve = []

        profile = profiles[post.activity]

        await post.message.edit(
            content="",
            embed=discord.Embed(
                title=f"{profile.name}.\nРекомендуемая сила - {profile.power}.", colour=colors["raid"],
                description=f"Время проведения: **{post.time:%d.%m.%Y} в {post.time:%H:%M} (UTC+3)**."
            ).set_author(
                name=f"{author.display_name} собирает вас в"
            ).set_thumbnail(
                url=profile.thumbnail_url
            ).set_footer(
                text=f"ID: {post.message.id}"
            ).add_field(
                name=":ledger: | Заметка от лидера", inline=False,
                value=note.replace("\\n", "\n")
            ).add_field(
                name=":blue_square:  | Основной состав", inline=False,
                value=f"#1 - {author.mention} - {author.display_name}"
            ).add_field(
                name=":green_square:  | Резервный состав", inline=False,
                value="здесь ещё никого нет"
            ),
            view=EnrollView(
                post.message.id, main_callback, reserve_callback
            )
        )

        return post

    @classmethod
    def restore(cls, message: Message):
        cursor = cls.__connection.cursor()

        cursor.execute(queries.fetch_by_message, (message.id,))
        if (record := cursor.fetchone()) is None:
            raise KeyError("this message is not a post")

        post = cls(message, record["activity"], datetime.fromtimestamp(record["unix_time"], timezone))
        post.author, post._main, post._reserve = record["author"], loads(record["main"]), loads(record["reserve"])

        return post

    @classmethod
    def deletion(cls) -> Iterator[tuple[ID, ID]]:
        cursor = cls.__connection.cursor()
        time = datetime.now(tz=timezone).replace(second=0, microsecond=0) - timings["delete"]
        cursor.execute(queries.fetch_by_time, (time.timestamp(),))

        for record in cursor.fetchall():
            yield record["channel_id"], record["message_id"]

    @classmethod
    def notification(cls) -> Iterator[Notification]:
        cursor = cls.__connection.cursor()
        time = datetime.now(tz=timezone).replace(second=0, microsecond=0) - timings["notify"]
        cursor.execute(queries.fetch_by_time, (time.timestamp(),))

        for record in cursor.fetchall():
            yield Notification(**record)
