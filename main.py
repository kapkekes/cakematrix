from logging.config import dictConfig
from importlib.resources import path

from discord import Bot
from yaml import full_load

from secret import TOKEN

import config


if __name__ == '__main__':
    with path(config, "logging.yaml") as p, open(p, "r") as f:
        dictConfig(full_load(f.read()))

    cakematrix = Bot()
    cakematrix.load_extension("source.cogs.database_handler")
    cakematrix.load_extension("source.cogs.looking_for_group")
    cakematrix.run(TOKEN)
