from logging import Handler, Formatter, LogRecord
from typing import Any, Dict, NoReturn

from requests import post
from termcolor import colored


TERMINAL_MAPPING: Dict[str, Dict] = {
    'CRITICAL': {'color': 'red', 'attrs': ['bold']},
    'ERROR':    {'color': 'red'},
    'WARNING':  {'color': 'yellow'},
    'INFO':     {'color': 'green'},
    'DEBUG':    {'color': 'blue'},
    'NOTSET':   {'color': 'white'},
}

DISCORD_MAPPING: Dict[str, str] = {
    'CRITICAL': "```diff\n- {}\n```",
    'ERROR':    "```1c\n# {}\n```",
    'WARNING':  "```fix\n^ {}\n```",
    'INFO':     "```diff\n+ {}\n```",
    'DEBUG':    "```asciidoc\n= {}\n```",
    'NOTSET':   "```diff\n% {}\n```",
}


class TerminalColorfulFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        return colored(super().format(record), **TERMINAL_MAPPING[record.levelname])


class DiscordColorfulFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        return DISCORD_MAPPING[record.levelname].format(super().format(record))


class WebhookHandler(Handler):
    webhook_url: str

    def __init__(self, webhook_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.webhook_url = webhook_url

    def format(self, record: LogRecord) -> dict[str, Any]:
        return {"content": super().format(record)}

    # TODO: Add correct error handling
    def emit(self, record: LogRecord) -> None:
        post(self.webhook_url, self.format(record))
