from logging import getLogger
from random import choice
from typing import Callable, Dict
from sqlite3 import Cursor

import discord

from source.classes.post import Post, AlreadyEnrolledError, FullFireteamError
from resources.activities import optionChoices
from utilities import str_to_datetime
from secret import GUILDS

import resources


logger = getLogger(__name__)

DECORATORS = {
    "create": {
        "guild_ids": GUILDS,
        "name": "собрать",
        "description": "создать сбор",
        "options": [
            discord.Option(
                str, choices=optionChoices,
                name="активность", description="активность, в которую ведётся сбор"
            ),
            discord.Option(
                str,
                name="время", description="время начала (в формате ДД.ММ-ЧЧ:ММ)"
            ),
            discord.Option(
                str, default="отсутствует",
                name="заметка", description="заметка, прикреплённая к сбору (\\n для новой строки)"
            )
        ]
    },
    "change_author": {
        "guild_ids": GUILDS,
        "name": "передать_сбор",
        "description": "передать сбор другому пользователю",
        "options": [
            discord.Option(
                str, name="идентификатор", description="уникальный номер сбора (находится в последней строчке сбора)",
            ),
            discord.Option(
                discord.User, name="пользователь", description="новый лидер активности"
            )
        ]
    }
}


class LFG(discord.Cog):
    """Cog with looking-for-group functionality.

    Adds several slash commands for creating and managing LFG posts.
    """
    bot: discord.Bot
    _functions: Dict[str, Callable]

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self._functions = {}

        def callback_builder(group: str):
            async def enroll(interaction: discord.Interaction):
                record = Post.fetch_record(int(interaction.custom_id.split("_")[1]))
                channel = await self.bot.fetch_channel(record["channel_id"])

                post = Post.from_message(
                    await channel.fetch_message(interaction.message.id)
                )

                user, response = interaction.user, interaction.response

                try:
                    await getattr(post, f"alter_to_{group}")(interaction.user)
                except ValueError:
                    logger.debug(f"{user} tested the system and tried to enroll to their LFG")
                    return await response.send_message("Ошибка: нельзя записаться к самому себе.", ephemeral=True)
                except AlreadyEnrolledError:
                    logger.debug(f"{user} tried to enroll to both fireteams to ID {post.message.id}")
                    return await response.send_message("Ошибка: нельзя записаться сразу в оба состава.", ephemeral=True)
                except FullFireteamError:
                    logger.debug(f"{user} tried to enroll to full {group} fireteam to ID {post.message.id}")
                    return await response.send_message("Ошибка: состав уже заполнен(", ephemeral=True)

                await response.send_message(f"*\\*{choice(resources.reactions)}\\**", delete_after=5)

            return enroll

        self._functions["main"] = callback_builder("main")
        self._functions["reserve"] = callback_builder("reserve")

    @discord.slash_command(**DECORATORS["create"])
    async def create(self, context: discord.ApplicationContext, raid, time, note):
        author = context.user

        try:
            timestamp = str_to_datetime(time)
        except ValueError:
            logger.debug(f"{author} used /lfg command, but put incorrect format time")
            return await context.respond("Ошибка: время имеет некорректный формат.", ephemeral=True)

        response: discord.Interaction = await context.respond("Создаю сбор...")

        post = Post(raid, author, timestamp, note)
        await post.create(
            response=response,
            main_callback=self._functions["main"],
            reserve_callback=self._functions["reserve"],
        )

        logger.debug(f"{author} created a LFG post to {raid} on {timestamp}")

    @discord.slash_command(**DECORATORS["change_author"])
    async def change_author(self, context: discord.ApplicationContext, raw_post_id: str, new_author: discord.User):
        author = context.author

        try:
            post_id = int(raw_post_id)
            record = Post.fetch_record(post_id)
        except ValueError | KeyError:
            logger.debug(f"{author} used /change_author command, but put incorrect ID")
            return await context.respond("Ошибка: не могу найти данную запись.", ephemeral=True)

        if record["author_id"] != author.id:
            logger.debug(f"{author} used /change_author command without access to the mentioned post")
            return await context.respond("Ошибка: вы не являетесь лидером данного сбора.", ephemeral=True)

        channel = await self.bot.fetch_channel(record["channel_id"])

        post = Post.from_message(
            await channel.fetch_message(post_id)
        )

        try:
            await post.set_author(new_author)
        except ValueError:
            return await context.respond("Ошибка: данный пользователь не может быть лидером сбора.", ephemeral=True)

        await context.respond(f"*\\*{choice(resources.reactions)}\\**", delete_after=resources.reaction_delete_time)


def setup(bot: discord.Bot):
    if (db_handler := bot.get_cog("DatabaseHandler")) is None:
        return logger.error("LFG cog can't find a Database handler")

    Post.set_connection(db_handler.con)  # type: ignore
    bot.add_cog(LFG(bot))
    logger.info("LFG cog was added to your bot")
