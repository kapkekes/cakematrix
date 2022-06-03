import importlib.resources as imr
import os
import sqlite3 as sql

import source
import resources


if __name__ == '__main__':
    with imr.path(resources, 'database.sqlite3') as db_path:
        if not os.path.exists(db_path):
            with sql.connect(db_path) as connection:
                cursor = connection.cursor()
                query = " ".join(imr.read_text(source, 'init_db.sql').split())
                cursor.executescript(query)
                cursor.close()
                connection.commit()
