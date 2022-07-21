import random
import logging

from discord import ButtonStyle, Interaction
from discord.ui import Button, View

import resources
from source.classes.exceptions import AlreadyEnrolledError, FullFireteamError


ID = int
_log = logging.getLogger(__name__)


class EnrollButton(Button):
    @staticmethod
    async def enroll(interaction: Interaction):
        from classes.optimized_post import OptimizedPost
        post = OptimizedPost.restore(interaction.message)
        user, group, response = interaction.user, interaction.custom_id.split('_')[0], interaction.response

        try:
            await getattr(post, f"alter_in_{group}")(user)
        except ValueError:
            _log.debug(f"{user} tested the system and tried to enroll to their LFG")
            await response.send_message("Ошибка: нельзя записаться к самому себе.", ephemeral=True)
            return
        except AlreadyEnrolledError:
            _log.debug(f"{user} tried to enroll to both fireteams to ID {post.id}")
            await response.send_message("Ошибка: нельзя записаться сразу в оба состава.", ephemeral=True)
            return
        except FullFireteamError:
            _log.debug(f"{user} tried to enroll to full {group} fireteam to ID {post.id}")
            await response.send_message("Ошибка: состав уже заполнен(", ephemeral=True)
            return

        _log.debug(f"{user} altered in {group} fireteam of post with ID {post.id}")
        await response.send_message(f"*\\*{random.choice(resources.reactions)}\\**", ephemeral=True)

    @classmethod
    def main(cls, message_id: ID):
        button = cls(label="Основной состав", style=ButtonStyle.blurple, custom_id=f"main_{message_id}")
        button.callback = cls.enroll
        return button

    @classmethod
    def reserve(cls, message_id: ID):
        button = cls(label="Резервный состав", style=ButtonStyle.green, custom_id=f"reserve_{message_id}")
        button.callback = cls.enroll
        return button


class EnrollView(View):
    def __init__(self, message_id: ID):
        super().__init__(EnrollButton.main(message_id), EnrollButton.reserve(message_id), timeout=None)
