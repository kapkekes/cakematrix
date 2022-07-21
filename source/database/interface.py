from importlib.resources import path
from sqlite3 import Connection, Row

from yaml import full_load

import config
import resources


with path(config, 'general.yaml') as settings_path, open(settings_path, 'r') as file:
    db_path = full_load(file.read()).get('path_to_database')

if db_path is None:
    with path(resources, 'database.sqlite3') as default_db_path:
        db_path = default_db_path


connection = Connection(db_path)
connection.row_factory = Row
