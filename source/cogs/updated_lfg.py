import logging
import random
import sqlite3 as sql
from sqlite3 import Connection, Cursor

import discord
import discord.ext.tasks as tasks
import discord.ext.commands as commands
from discord import ApplicationContext, Bot, Cog, Option, Interaction, User

import source.queries as queries
import resources
from source.classes.optimized_post import OptimizedPost
from source.database import connection
from secret import GUILDS
from source.utilities import str_to_datetime


_log = logging.getLogger(__name__)

DECORATORS = {
    "create": {
        "guild_ids": GUILDS, "name": "собрать", "description": "создать сбор",
        "options": [
            Option(
                str, choices=resources.option_choices,
                name="активность", description="активность, в которую ведётся сбор"
            ),
            Option(
                str,
                name="время", description="время начала (в формате ДД.ММ-ЧЧ:ММ)"
            ),
            Option(
                str, default="отсутствует",
                name="заметка", description="заметка, прикреплённая к сбору (\\n для новой строки)"
            )
        ]
    },
    "change_author": {
        "guild_ids": GUILDS, "name": "передать_сбор", "description": "передать сбор другому пользователю",
        "options": [
            Option(
                str, name="идентификатор", description="уникальный номер сбора (находится в последней строчке сбора)",
            ),
            Option(
                discord.User, name="пользователь", description="новый лидер активности"
            )
        ]
    },
    "change_time": {
        "guild_ids": GUILDS, "name": "перенести_сбор", "description": "перенести сбор на другое время",
        "options": [
            Option(
                str, name="идентификатор", description="уникальный номер сбора (находится в последней строчке сбора)",
            ),
            Option(
                str, name="время", description="новое время сбора"
            )
        ]
    },
    "change_note": {
        "guild_ids": GUILDS, "name": "изменить_заметку", "description": "прикрепить новую заметку к сбору",
        "options": [
            Option(
                str, name="идентификатор", description="уникальный номер сбора (находится в последней строчке сбора)",
            ),
            Option(
                str, name="заметка", description="новая заметка (\\n для новой строки)", default="отсутствует"
            )
        ]
    },
    "cancel": {
        "guild_ids": GUILDS, "name": "отменить", "description": "отменить сбор",
        "options": [
            Option(
                str, name="идентификатор", description="уникальный номер сбора (находится в последней строчке сбора)",
            ),
            Option(
                str, name="причина", description="причина отмены сбора (\\n для новой строки)", default="не названа"
            )
        ]
    },
}


class LookingForGroup(Cog):
    bot: Bot

    def __init__(self, bot: Bot):
        self.bot = bot

        self.reminder.start()
        self.clear.start()

    async def fetch_and_auth(self, context: ApplicationContext, raw_message_id: str) -> OptimizedPost | None:
        author = context.author

        try:
            message_id = int(raw_message_id)
        except ValueError:
            _log.debug(f"{author} used managing command, but put something strange to ID field")
            return None

        cursor = connection.cursor()
        cursor.execute(queries.fetch_by_message, (message_id,))
        if (record := cursor.fetchone()) is None:
            _log.debug(f"{author} used managing command, but put incorrect ID")
            return None

        channel = await self.bot.fetch_channel(record["channel_id"])
        post = OptimizedPost.restore(await channel.fetch_message(message_id))

        if post.author != author.id:
            _log.debug(f"{author} used managing command without access to the mentioned post")
            await context.respond("Ошибка: вы не являетесь лидером данного сбора.", ephemeral=True)
            return None

        return post

    async def send_to_multiple(self, *user_ids, **kwargs) -> list[User]:
        failed = []

        for user_id in user_ids:
            user = await self.bot.fetch_user(user_id)

            try:
                await user.send(**kwargs)
            except discord.Forbidden:
                failed.append(user)

        return failed

    @commands.Cog.listener(name="on_connect")
    async def revive_posts(self):
        await self.bot.wait_until_ready()

        for view in OptimizedPost.revival():
            self.bot.add_view(view)

    @discord.slash_command(**DECORATORS["create"])
    async def create(self, context: ApplicationContext, activity: str, str_time: str, note: str):
        author = context.author

        try:
            time = str_to_datetime(str_time)
        except ValueError:
            _log.debug(f"{author} used /create, but put incorrect format time")
            await context.respond("Ошибка: время имеет некорректный формат.", ephemeral=True)
            return

        response: Interaction = await context.respond("Создаю сбор...")
        await OptimizedPost.create(
            await response.original_message(),
            activity, author, time, note
        )

        _log.debug(f"{author} created a LFG post to {activity} on {time}")

    @discord.slash_command(**DECORATORS["change_author"])
    async def change_author(self, context: ApplicationContext, raw_message_id: str, new_author: User):
        if (post := await self.fetch_and_auth(context, raw_message_id)) is None:
            return

        await context.defer(ephemeral=True)
        response = context.response

        try:
            await post.set_author(new_author)
        except ValueError:
            _log.debug(f"{context.author} used /change_author, but chose incorrect new author")
            await response.edit_message(content="Ошибка: данный пользователь не может быть лидером сбора.")
            return

        _log.debug(f"{context.author} set {new_author} as leader in post with ID {post.id}")
        await context.respond(f"*\\*{random.choice(resources.reactions)}\\**", ephemeral=True)

    @discord.slash_command(**DECORATORS["change_time"])
    async def change_time(self, context: ApplicationContext, raw_message_id: str, new_str_time: str):
        if (post := await self.fetch_and_auth(context, raw_message_id)) is None:
            return

        await context.defer(ephemeral=True)
        response = context.response

        try:
            new_time = str_to_datetime(new_str_time)
        except ValueError:
            _log.debug(f"{context.author} used /change_time, but put incorrect format time")
            await response.edit_message(content="Ошибка: время имеет некорректный формат.")
            return

        await post.set_time(new_time)
        _log.debug(f"{context.author} postponed post with ID {post.id} to {new_time}")
        await context.respond(f"*\\*{random.choice(resources.reactions)}\\**", ephemeral=True)

    @discord.slash_command(**DECORATORS["change_note"])
    async def change_note(self, context: ApplicationContext, raw_message_id: str, new_note: str):
        if (post := await self.fetch_and_auth(context, raw_message_id)) is None:
            return

        await context.defer(ephemeral=True)

        await post.set_note(new_note)
        _log.debug(f"{context.author} changed note in post with ID {post.id}")
        await context.respond(f"*\\*{random.choice(resources.reactions)}\\**", ephemeral=True)

    @discord.slash_command(**DECORATORS["cancel"])
    async def cancel(self, context: ApplicationContext, raw_message_id: str, reason: str):
        if (post := await self.fetch_and_auth(context, raw_message_id)) is None:
            return

        await context.defer(ephemeral=True)

        embed = await post.cancel(reason)
        embed.set_author(
            name="Сбор, в который вы записались, был отменён."
        )

        blocked = await self.send_to_multiple(*(post.main + post.reserve), embed=embed)
        _log.debug(f"{context.author} cancelled post with ID {post.id}")

        if len(blocked) > 0:
            _log.warning(f"failed to send messages to {', '.join(map(str, blocked))}")

        await context.respond(f"*\\*{random.choice(resources.reactions)}\\**", ephemeral=True)

    @tasks.loop(minutes=1)
    async def reminder(self):
        for ids in OptimizedPost.reminder():
            channel = await self.bot.fetch_channel(ids.channel_id)
            message = await channel.fetch_message(ids.message_id)

            blocked = await self.send_to_multiple(*ids.main, embed=message.embeds[0].copy().set_author(
                name="Через 15 минут вы отправитесь в"
            ))
            blocked += await self.send_to_multiple(*ids.reserve, embed=message.embeds[0].copy().set_author(
                name="Через 15 минут вы можете отправиться в"
            ))

            if len(blocked) > 0:
                _log.warning(f"failed to send messages to {', '.join(map(str, blocked))}")

    @tasks.loop(minutes=1)
    async def clear(self):
        for channel_id, message_id in OptimizedPost.deletion():
            channel = await self.bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)

            connection.execute(queries.delete, (message_id,))
            connection.commit()
            await message.delete()


def setup(bot: Bot):
    bot.add_cog(LookingForGroup(bot))
    _log.info("LFG cog was successfully added to the bot")
