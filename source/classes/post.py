from datetime import datetime
from random import choice
from sqlite3 import Connection, Row
from typing import List, Callable, Coroutine, Tuple

import pickle as pkl

from discord import Message, User, Interaction, Embed, InteractionMessage

from resources import timezone, emojis

import builders
import queries


Roster = Tuple[User, List[User], List[User]]


class AlreadyEnrolledError(Exception):
    pass


class FullFireteamError(Exception):
    pass


class Post:
    message: Message | InteractionMessage
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

    def mention_string(self):
        res = choice(emojis)
        itr = [self.author] + self.main + self.reserve

        for user in itr:
            res += f" {user.mention} {choice(emojis)}"

        return res

    async def create(
            self,
            response: Interaction,
            main_callback: Callable[[Interaction], Coroutine],
            reserve_callback: Callable[[Interaction], Coroutine]
    ):
        self.message = await response.original_message()
        self.main = []
        self.reserve = []

        await self.message.edit(
            content=self.mention_string(),
            embed=builders.create_embed(self),
            view=builders.create_enrollment_view(self.message.id, main_callback, reserve_callback)
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
            self._connection.execute(queries.update.main, (self._dump_main(), self.message.id))
            embed.set_field_at(
                index=1, name=":blue_square:  | Основной состав", inline=False,
                value=builders.numbered_list([new_author] + self.main)
            )
        elif new_author in self.reserve:
            self.reserve.remove(new_author)
            self._connection.execute(queries.update.reserve, (self._dump_reserve(), self.message.id))
            embed.set_field_at(
                index=2, name=":green_square:  | Резервный состав", inline=False,
                value=builders.numbered_list(self.reserve)
            )

        self.author = new_author
        self._connection.execute(
            queries.update.author_id, (self.author.id, self.message.id)
        )
        self._connection.commit()

        await self.message.edit(
            content=self.mention_string(),
            embed=embed.set_author(
                name=f"{self.author.display_name} собирает вас в"
            )
        )

    async def set_time(self, new_time: datetime):
        self.time = new_time

        self._connection.execute(
            queries.update.unix_time, (self.time.timestamp(), self.message.id)
        )
        self._connection.commit()

        embed = self.embed
        embed.description = f"Время проведения: **{self.time:%d.%m.%Y} в {self.time:%H:%M} (UTC+3)**."

        await self.message.edit(
            embed=self.embed.set_author(
                name=f"{self.author.display_name} собирает вас в"
            )
        )

    async def set_note(self, new_note: str):
        self.note = new_note

        await self.message.edit(
            embed=self.embed.set_field_at(
                index=0, name=":ledger: | Заметка от лидера", inline=False, value=builders.lines(self.note)
            )
        )

    async def alter_to_main(self, user: User):
        if self.author == user:
            raise ValueError("author can't enroll to their post")

        if user in self.reserve:
            raise AlreadyEnrolledError("this user has already enrolled to reserve fireteam")

        if user in self.main:
            self.main.remove(user)
        elif len(self.main) >= 5:
            raise FullFireteamError("main fireteam is already full")
        else:
            self.main.append(user)

        self._connection.execute(
            queries.update.main, (self._dump_main(), self.message.id)
        )
        self._connection.commit()
        await self.message.edit(
            content=self.mention_string(),
            embed=self.embed.set_field_at(
                index=1, name=":blue_square:  | Основной состав", inline=False,
                value=builders.numbered_list([self.author] + self.main)
            )
        )

    async def alter_to_reserve(self, user: User):
        if self.author == user:
            raise ValueError("author can't enroll to their post")

        if user in self.main:
            raise AlreadyEnrolledError("this user has already enrolled to main fireteam")

        if user in self.reserve:
            self.reserve.remove(user)
        elif len(self.reserve) >= 5:
            raise FullFireteamError("reserve fireteam is already full")
        else:
            self.reserve.append(user)

        self._connection.execute(
            queries.update.reserve, (self._dump_reserve(), self.message.id)
        )
        self._connection.commit()
        await self.message.edit(
            content=self.mention_string(),
            embed=self.embed.set_field_at(
                index=2, name=":green_square:  | Резервный состав", inline=False,
                value=builders.numbered_list(self.reserve)
            )
        )

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

    @property
    def embed(self) -> Embed:
        return self.message.embeds[0].copy()

    @staticmethod
    def _indentify_users(users: List[User], author_id: int, main_id: List[int], reserve_id: List[int]) -> Roster:
        for candidate in users:
            if candidate.id == author_id:
                author = candidate
                break
        else:
            raise ValueError("can't identify the author of the post")

        def filter_and_sort(roster: List[int]) -> List[User]:
            return sorted(filter(lambda u: u.id in roster, users), key=lambda u: roster.index(u.id))

        return author, filter_and_sort(main_id), filter_and_sort(reserve_id)

    @classmethod
    def fetch_record(cls, message_id: int) -> Row:
        cursor = cls._connection.cursor()

        cursor.execute(queries.fetch_post, (message_id, ))
        record = cursor.fetchone()
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
            record["activity"], author, datetime.fromtimestamp(record["unix_time"], timezone)
        )

        post.message = message
        post.main = main
        post.reserve = reserve

        return post
