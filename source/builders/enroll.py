from typing import Callable, Coroutine

from discord import ButtonStyle, Interaction
from discord.ui import Button, View


LABELS = {
    "main": "Основной состав",
    "reserve": "Резервный состав",
}

COLORS = {
    "main": ButtonStyle.blurple,
    "reserve": ButtonStyle.green,
}


class EnrollButton(Button):
    def __init__(self, enroll_type: str, response_id: int, callback: Callable[[Interaction], Coroutine]):
        super().__init__(label=LABELS[enroll_type], style=COLORS[enroll_type], custom_id=f"{enroll_type}_{response_id}")
        self.callback = callback


def create_enroll_view(response_id: int, callback: Callable[[Interaction], Coroutine]) -> View:
    return View(
        EnrollButton("main", response_id, callback), EnrollButton("reserve", response_id, callback), timeout=None
    )
