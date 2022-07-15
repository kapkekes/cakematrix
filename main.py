from logging.config import dictConfig
from importlib.resources import path

from discord import Bot
from yaml import full_load

import config
from secret import TOKEN


if __name__ == "__main__":
    with path(config, "logging.yaml") as path, open(path, "r") as file:
        dictConfig(full_load(file.read()))

    cakematrix = Bot()

    cakematrix.load_extension("source.cogs.database_handler")
    cakematrix.load_extension("source.cogs.looking_for_group")

    cakematrix.run(TOKEN)
