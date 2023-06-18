import logging
import mysql.connector
from pystorz.sql.store import SqlStore
from pystorz.sql.adapter import SQLAdapter


log = logging.getLogger(__name__)


def MySqlStoreFactory(schema, host, port, user, password, database):
    def connector():
        return _MySQLAdapter(host, port, user, password, database)

    return SqlStore(schema, connector)


class _MySQLAdapter(SQLAdapter):
    def __init__(self, host, port, username, password, database):
        super().__init__()

        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._database = database

    def connect(self):
        return mysql.connector.connect(
            host=self._host,
            port=self._port,
            user=self._username,
            password=self._password,
            database=self._database
        )
