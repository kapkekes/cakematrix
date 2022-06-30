from typing import Iterable
from datetime import datetime

from discord import User, Embed

from resources.activities import profiles
from resources.design import colors


def numbered_list(users: Iterable[User]) -> str:
    result = "\n".join(f"**#{pos + 1}** {user.mention} - {user.name}" for pos, user in enumerate(users))
    return result if result != "" else "здесь никого нет..."


def lines(string: str) -> str:
    return string.replace("\\n", "\n")


def build_lfg_embed(raid_id: str, author: User, time: datetime, note: str, response_id: int) -> Embed:
    r = profiles[raid_id]
    return Embed.from_dict({
        "type": "rich",
        "title": f"{r['name']}.\nРекомендуемая сила - {r['power']}.",
        "description": f"Время проведения: **{time:%d.%m.%Y} в {time:%H:%M} (UTC+3)**.",
        "color": colors["raid"],
        "fields": [
            {
                "name": ":ledger: | Заметка от лидера",
                "value": lines(note),
                "inline": False
            },
            {
                "name": ":blue_square:  | Основной состав",
                "value": numbered_list([author]),
                "inline": False
            },
            {
                "name": ":green_square:  | Резервный состав",
                "value": numbered_list([]),
                "inline": False
            },
        ],
        "thumbnail": {
            "url": r["thumbnail"]
        },
        "author": {
            "name": f"{author.display_name} собирает вас в"
        },
        "footer": {
            "text": f"ID: {response_id}"
        },
    })


def notify_main(embed: Embed) -> Embed:
    return embed.set_author(name="Через 15 минут вы отправитесь в")


def notify_reserve(embed: Embed) -> Embed:
    return embed.set_author(name="Через 15 минут вы можете отправиться в")