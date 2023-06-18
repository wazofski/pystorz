import logging
import sqlite3
from pystorz.sql.store import SqlStore
from pystorz.sql.adapter import SQLAdapter

log = logging.getLogger(__name__)


def SqliteStoreFactory(schema, path):
    def connector():
        return _SqliteAdapter(path)

    return SqlStore(schema, connector)


class _SqliteAdapter(SQLAdapter):
    def __init__(self, path):
        super().__init__()
        self._path = path

    def connect(self):
        return sqlite3.connect(self._path)
