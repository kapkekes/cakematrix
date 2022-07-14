"""Initializing script. Should be run for the first time.

Creates a database file with required tables.
"""


import importlib.resources as imr
import os
import sqlite3 as sql

import resources
from source.queries import initialize_database


if __name__ == "__main__":
    with imr.path(resources, "database.sqlite3") as db_path:
        if not os.path.exists(db_path):
            with sql.connect(db_path) as connection:
                connection.executescript(initialize_database)
