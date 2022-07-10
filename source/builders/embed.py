from typing import Iterable

from discord import User, Embed

from classes.post import Post
from resources.activities import profiles
from resources.design import colors


def numbered_list(users: Iterable[User]) -> str:
    result = "\n".join(f"**#{pos + 1}** {user.mention}" for pos, user in enumerate(users))
    return result if result != "" else "здесь никого нет..."


def lines(string: str) -> str:
    return string.replace("\\n", "\n")


def create_embed(post: Post) -> Embed:
    r = profiles[post.activity]

    return Embed(
        title=f"{r['name']}.\nРекомендуемая сила - {r['power']}.",
        description=f"Время проведения: **{post.time:%d.%m.%Y} в {post.time:%H:%M} (UTC+3)**.",
        colour=colors["raid"],
    ).set_author(
        name=f"{post.author.display_name} собирает вас в"
    ).set_thumbnail(
        url=r["thumbnail"]
    ).set_footer(
        text=f"ID: {post.message.id}"
    ).set_field_at(
        index=0, name=":ledger: | Заметка от лидера", inline=False, value=lines(post.note)
    ).set_field_at(
        index=1, name=":blue_square:  | Основной состав", inline=False, value=numbered_list([post.author])
    ).set_field_at(
        index=2, name=":green_square:  | Резервный состав", inline=False, value=numbered_list([])
    )


def notify_main(embed: Embed) -> Embed:
    return embed.set_author(name="Через 15 минут вы отправитесь в")


def notify_reserve(embed: Embed) -> Embed:
    return embed.set_author(name="Через 15 минут вы можете отправиться в")
