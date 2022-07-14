from typing import Iterable, TypeVar

from discord import User, Embed

from resources import colors, profiles


Post = TypeVar("Post")


def numbered_list(users: Iterable[User]) -> str:
    result = "\n".join(f"**#{pos} - ** {user.mention}" for pos, user in enumerate(users, 1))
    return result if result != "" else "здесь никого нет..."


def lines(string: str) -> str:
    return string.replace("\\n", "\n")


def create_embed(post: Post) -> Embed:
    profile = profiles[post.activity]

    return Embed(
        title=f"{profile.name}.\nРекомендуемая сила - {profile.power}.",
        description=f"Время проведения: **{post.time:%d.%m.%Y} в {post.time:%H:%M} (UTC+3)**.",
        colour=colors["raid"]
    ).set_author(
        name=f"{post.author.display_name} собирает вас в"
    ).set_thumbnail(
        url=profile.thumbnail_url
    ).set_footer(
        text=f"ID: {post.message.id}"
    ).add_field(
        name=":ledger: | Заметка от лидера", inline=False, value=lines(post.note)
    ).add_field(
        name=":blue_square:  | Основной состав", inline=False, value=numbered_list([post.author])
    ).add_field(
        name=":green_square:  | Резервный состав", inline=False, value=numbered_list([])
    )


def notify_main(embed: Embed) -> Embed:
    return embed.copy().set_author(name="Через 15 минут вы отправитесь в")


def notify_reserve(embed: Embed) -> Embed:
    return embed.copy().set_author(name="Через 15 минут вы можете отправиться в")
