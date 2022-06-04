from logging import Formatter, LogRecord
from termcolor import colored
from typing import Dict, NoReturn

LEVEL_MAPPING: Dict[str, Dict] = {
    'CRITICAL': {'color': 'red', 'attrs': ['bold']},
    'ERROR':    {'color': 'red'},
    'WARNING':  {'color': 'yellow'},
    'INFO':     {'color': 'green'},
    'DEBUG':    {'color': 'blue'},
    'NOTSET':   {'color': 'white'},
}


class ColorfulFormatter(Formatter):
    __color_switch: bool

    def __init__(self, *args, use_color: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.__color_switch = use_color

    def format(self, record: LogRecord) -> str:
        text = super().format(record)

        if self.__color_switch:
            return colored(text, **LEVEL_MAPPING[record.levelname])

        return text

    def colors_off(self):
        self.__color_switch = False

    def colors_on(self) -> NoReturn:
        self.__color_switch = True