from pickle import dumps, loads
from datetime import datetime
from typing import TypeVar, NamedTuple, Iterator

import discord
from discord import Message, User, Embed

import source.queries as queries
from source.classes.exceptions import AlreadyEnrolledError, FullFireteamError
from source.database import connection
from resources.activities import profiles
from resources.constants import timezone, timings
from resources.design import colors


ID = int
OP = TypeVar('OP', bound='OptimizedPost')
EV = TypeVar('EV', bound='EnrollView')


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

    def __init__(self, message: Message, activity: str, time: datetime):
        self.message = message
        self.activity = activity
        self.time = time

    async def set_author(self, author: User):
        if author.bot:
            raise ValueError("a bot cannot be set as author of a post")

        if self.author == author.id:
            raise ValueError("this user is already the author of the post")

        if author.id in self._main:
            embed = await self.alter_in_main(author)
        elif author.id in self._reserve:
            embed = await self.alter_in_reserve(author)
        else:
            embed = self.new_embed()

        self.author = author.id

        embed.set_author(name=f"{author.display_name} собирает вас в")

        new_field = embed.fields[1].value.split("\n")
        new_field[0] = f"#1 - {author.mention} - {author.display_name}"
        embed._fields[1].value = "\n".join(new_field)

        connection.execute(queries.update.author, (self.author, self.id))
        connection.commit()

        await self.message.edit(embed=embed)

    async def set_time(self, time: datetime):
        self.time = time
        connection.execute(queries.update.unix_time, (self.time.timestamp(), self.id))
        connection.commit()

        embed = self.new_embed()
        embed.description = f"Время проведения: **{self.time:%d.%m.%Y} в {self.time:%H:%M} (UTC+3)**."

        await self.message.edit(embed=embed)

    async def set_note(self, note: str):
        embed = self.new_embed()
        embed._fields[0].value = note.replace("\\n", "\n")

        await self.message.edit(embed=embed)

    async def alter_in_main(self, user: User) -> Embed:
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
            new_value.append(f"#{len(self._main) + 1} - {user.mention} - {user.display_name}")

        connection.execute(queries.update.main, (dumps(self._main), self.id))
        connection.commit()

        embed._fields[1].value = "\n".join(new_value)

        await self.message.edit(embed=embed)
        return embed

    async def alter_in_reserve(self, user: User) -> Embed:
        if user.id == self.author:
            raise ValueError("author can't enroll to their post")

        if user.id in self._main:
            raise AlreadyEnrolledError("this user has already enrolled to reserve fireteam")

        embed = self.new_embed()
        new_value = embed._fields[2].value.split("\n")

        if not self._reserve:
            self._reserve.append(user.id)
            new_value = [f"#1 - {user.mention} - {user.display_name}"]
        elif user.id in self._reserve and len(self._reserve) == 1:
            self._reserve.remove(user.id)
            new_value = ["здесь ещё никого нет"]
        elif user.id in self._reserve:
            index = self._reserve.index(user.id)
            del self._reserve[index], new_value[index]
            new_value = [f"#{position}{string[2:]}" for position, string in enumerate(new_value, start=1)]
        elif len(self._reserve) >= 5:
            raise FullFireteamError("reserve fireteam is already full")
        else:
            self._reserve.append(user.id)
            new_value.append(f"#{len(self._reserve)} - {user.mention} - {user.display_name}")

        connection.execute(queries.update.reserve, (dumps(self._reserve), self.id))
        connection.commit()

        embed._fields[2].value = "\n".join(new_value)

        await self.message.edit(embed=embed)
        return embed

    async def cancel(self, reason: str) -> Embed:
        embed = self.new_embed()
        embed._colour = colors["cancel"]
        embed.set_author(
            name="Сбор был отменён."
        ).set_field_at(
            index=0, name=":closed_book: | Причина отмены сбора", inline=False, value=reason.replace("\\n", "\n")
        )

        connection.execute(queries.delete, (self.id,))
        connection.commit()

        await self.message.edit(embed=embed, view=None, delete_after=timings["delete"].seconds)
        return embed

    async def delete(self):
        connection.execute(queries.delete, (self.id,))
        connection.commit()

        await self.message.delete()

    def new_embed(self):
        return self.message.embeds[0].copy()

    @property
    def id(self):
        return self.message.id

    @property
    def main(self):
        return self._main

    @property
    def reserve(self):
        return self._reserve
    
    @classmethod
    async def create(cls, message: Message, activity: str, author: User, time: datetime, note: str) -> OP:
        post = cls(message, activity, time)
        post.author = author.id
        post._main = []
        post._reserve = []

        profile = profiles[post.activity]

        from source.classes.enroll_view import EnrollView
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
                text=f"ID: {post.id}"
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
                post.id
            )
        )
        connection.execute(queries.create, {
            "message_id": post.id,
            "channel_id": post.message.channel.id,
            "activity":   post.activity,
            "author":     post.author,
            "unix_time":  int(post.time.timestamp())
        })
        connection.commit()

        return post

    @classmethod
    def restore(cls, message: Message) -> OP:
        cursor = connection.cursor()

        cursor.execute(queries.fetch_by_message, (message.id,))
        if (record := cursor.fetchone()) is None:
            raise KeyError("this message is not a post")

        post = cls(message, record["activity"], datetime.fromtimestamp(record["unix_time"], timezone))
        post.author, post._main, post._reserve = record["author"], loads(record["main"]), loads(record["reserve"])

        return post

    @classmethod
    def deletion(cls) -> Iterator[tuple[ID, ID]]:
        cursor = connection.cursor()
        time = datetime.now(tz=timezone).replace(second=0, microsecond=0) - timings["delete"]
        cursor.execute(queries.fetch_by_time, (time.timestamp(),))

        for record in cursor.fetchall():
            yield record["channel_id"], record["message_id"]

    @classmethod
    def reminder(cls) -> Iterator[Notification]:
        cursor = connection.cursor()
        time = datetime.now(tz=timezone).replace(second=0, microsecond=0) + timings["notify"]
        cursor.execute(queries.fetch_by_time, (time.timestamp(),))

        for record in cursor.fetchall():
            yield Notification(
                record["channel_id"], record["message_id"],
                [record["author"]] + loads(record["main"]), loads(record["reserve"])
            )

    @classmethod
    def revival(cls) -> Iterator[EV]:
        cursor = connection.cursor()
        cursor.execute(queries.revive)

        from source.classes.enroll_view import EnrollView
        for record in cursor.fetchall():
            yield EnrollView(record["message_id"])
