"""Initializing script. Should be run for the first time.

Creates a database file with required tables.
"""


import os
import sqlite3 as sql
from importlib.resources import path

from yaml import full_load

import config
import resources
from source.queries import initialize_database


if __name__ == "__main__":
    with path(config, 'general.yaml') as settings_path, open(settings_path, 'r') as file:
        db_path = full_load(file.read()).get('path_to_database')

    if db_path is None:
        with path(resources, 'database.sqlite3') as default_db_path:
            db_path = default_db_path

    if not os.path.exists(db_path):
        with sql.connect(db_path) as connection:
            connection.executescript(initialize_database)
