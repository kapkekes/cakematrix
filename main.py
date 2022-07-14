from logging.config import dictConfig
from importlib.resources import path

from discord import Bot
from yaml import full_load

import config
from secret import TOKEN


if __name__ == "__main__":
    with path(config, "logging.yaml") as p, open(p, "r") as f:
        dictConfig(full_load(f.read()))

    cakematrix = Bot()
    cakematrix.load_extensions(
        "source.cogs.database_handler",
        "source.cogs.looking_for_group",
        store=False
    )
    cakematrix.run(TOKEN)
