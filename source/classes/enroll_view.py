from enum import Enum
from typing import Callable, Coroutine

from discord import ButtonStyle, Interaction
from discord.ui import Button, View


ID = int


class ButtonType(Enum):
    main = 1
    reserve = 2


STYLES = {
    ButtonType.main: {
        "label": "Основной состав",
        "style": ButtonStyle.blurple
    },
    ButtonType.reserve: {
        "label": "Резервный состав",
        "style": ButtonStyle.green
    }
}


class EnrollButton(Button):
    def __init__(self, button_type: ButtonType, message_id: ID, callback: Callable[[Interaction], Coroutine]):
        super().__init__(
            **STYLES[button_type],
            custom_id=f"{button_type.name}_{message_id}"
        )

        self.callback = callback


class EnrollView(View):
    def __init__(
            self,
            message_id: ID,
            main_callback: Callable[[Interaction], Coroutine],
            reserve_callback: Callable[[Interaction], Coroutine]
    ):
        super().__init__(
            EnrollButton(
                ButtonType.main, message_id, main_callback
            ),
            EnrollButton(
                ButtonType.reserve, message_id, reserve_callback
            ),
            timeout=None
        )

    @staticmethod
    def restore(
            simple_view: View,
            main_callback: Callable[[Interaction], Coroutine],
            reserve_callback: Callable[[Interaction], Coroutine]
    ):
        simple_view.children[0].callback = main_callback
        simple_view.children[1].callback = reserve_callback