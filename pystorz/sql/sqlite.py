import sqlite3
from pystorz.sql.store import SqlStore


def SqliteStoreFactory(schema, path):
    def connector():
        return sqlite3.connect(path)

    return SqlStore(schema, connector)
