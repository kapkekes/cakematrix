from datetime import datetime
from sqlite3 import Connection, Row
from typing import List, Callable, Coroutine, Tuple

import pickle as pkl

from discord import Message, User, Interaction, Embed

from resources import timezone

import builders
import queries


Roster = Tuple[User, List[User], List[User]]


class Post:
    message: Message
    activity: str

    author: User
    time: datetime

    main: List[User]
    reserve: List[User]

    note: str

    _connection: Connection | None = None

    def __init__(self, activity: str, author: User, time: datetime, note: str = "empty"):
        self.activity = activity
        self.author = author
        self.time = time
        self.note = note

    @property
    def embed(self) -> Embed:
        return self.message.embeds[0]

    async def create(self, response: Interaction, callback: Callable[[Interaction], Coroutine]):
        self.message = response.message
        self.main = []
        self.reserve = []

        await self.message.edit(
            content="",
            embed=builders.create_embed(self),
            view=builders.create_enroll_view(response.message.id, callback)
        )

        self._connection.execute(queries.create_post, {
            "message_id": self.message.id,
            "channel_id": self.message.channel.id,
            "activity":   self.activity,
            "author_id":  self.author.id,
            "unix_time":  int(self.time.timestamp())
        })
        self._connection.commit()

    async def set_author(self, new_author: User):
        if new_author.bot:
            raise ValueError("a bot cannot be set as author of a post")

        if self.author == new_author:
            raise ValueError("this user is already the author of the post")

        embed = self.embed

        if new_author in self.main:
            self.main.remove(new_author)
            self._connection.execute(queries.update.main, (self._dump_main()))
            embed.set_field_at(
                index=1, name=":blue_square:  | Основной состав", inline=False,
                value=builders.numbered_list([self.author] + self.main)
            )
        elif new_author in self.reserve:
            self.reserve.remove(new_author)
            self._connection.execute(queries.update.main, (self._dump_main()))
            embed.set_field_at(
                index=2, name=":green_square:  | Резервный состав", inline=False,
                value=builders.numbered_list(self.reserve)
            )

        self.author = new_author
        self._connection.execute(
            queries.update.author_id, (self.author.id,)
        )
        self._connection.commit()

        await self.message.edit(
            embed=embed.set_author(
                name=f"{self.author.display_name} собирает вас в"
            )
        )

    async def set_time(self, new_time: datetime):
        self.time = new_time

        self._connection.execute(
            queries.update.unix_time, (self.time.timestamp(),)
        )
        self._connection.commit()

        embed = self.embed
        embed.description = f"Время проведения: **{self.time:%d.%m.%Y} в {self.time:%H:%M} (UTC+3)**."

        await self.message.edit(
            embed=self.embed.set_author(
                name=f"{self.author.display_name} собирает вас в"
            )
        )

    # TODO: create note setter
    async def set_note(self, new_note: str):
        ...

    # TODO: create fireteam management functions
    async def alter_to_main(self, user: User):
        ...

    async def alter_to_reserve(self, user: User):
        ...

    async def notify_users(self) -> List[User]:
        notifications = {
            "main": builders.notify_main(self.message.embeds[0]),
            "reserve": builders.notify_reserve(self.message.embeds[0])
        }

        record = self.fetch_record(self.message.id)

        author, main, reserve = self._indentify_users(
            self.message.mentions, record["author_id"], pkl.loads(record["main"]), pkl.loads(record["reserve"])
        )

        main.append(author)

        blocked = []

        for user in main:
            if user.can_send(notifications["main"]):
                await user.send(embed=notifications["main"])
            else:
                blocked.append(user)

        for user in reserve:
            if user.can_send(notifications["reserve"]):
                await user.send(embed=notifications["reserve"])
            else:
                blocked.append(user)

        return blocked

    def _dump_main(self) -> bytes:
        return pkl.dumps([user.id for user in self.main])

    def _dump_reserve(self) -> bytes:
        return pkl.dumps([user.id for user in self.reserve])

    @staticmethod
    def _indentify_users(users: List[User], author_id: int, main_id: List[int], reserve_id: List[int]) -> Roster:
        for candidate in users:
            if candidate.id == author_id:
                author = candidate
                break
        else:
            raise ValueError("can't identify the author of the post")

        def filter_and_sort(roster: List[int]) -> List[User]:
            return sorted(filter(lambda u: u in roster, users), key=lambda u: roster.index(u))

        return author, filter_and_sort(main_id), filter_and_sort(reserve_id)

    @classmethod
    def fetch_record(cls, message_id: int) -> Row:
        cursor = cls._connection.cursor()

        cursor.execute(queries.fetch_post, {"message_id": message_id})
        record: Row = cursor.fetchone()
        if record is None:
            raise KeyError("there are no post with the such message ID")

        return record

    @classmethod
    def set_connection(cls, connection: Connection):
        cls._connection = connection

    @classmethod
    def from_message(cls, message: Message):
        record = cls.fetch_record(message.id)

        author, main, reserve = cls._indentify_users(
            message.mentions, record["author_id"], pkl.loads(record["main"]), pkl.loads(record["reserve"])
        )

        post = cls(
            record["activity"], author, datetime.fromtimestamp(record["activity"], timezone)
        )

        post.message = message
        post.main = main
        post.reserve = reserve

        return post
