import logging
import mysql.connector
from pystorz.sql.store import SqlStore

log = logging.getLogger(__name__)

class _MySQLAdapter:
    def __init__(self, host, port, username, password, database):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.connection = None
        self._cursor = None

    def connect(self):
        try:
            self._cursor = None
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database
            )
            return self.connection
        except Exception as err:
            log.error("connect", err)
            raise err

    def cursor(self):
        try:
            if self.connection is None:
                self.connect()
            
            if self._cursor is None:
                self._cursor = self.connection.cursor()

            return self._cursor
        except Exception as err:
            log.error("cursor", err)
            raise err

    def close(self):
        try:
            if self._cursor:
                self._cursor.close()
            if self.connection:
                self.connection.close()
        except Exception as err:
            log.error("close", err)
            raise err
        self._cursor = None

    def execute(self, query, params=None):
        try:
            if self._cursor is None:
                self.cursor()
            
            if params:
                self._cursor.execute(query, params)
            else:
                self._cursor.execute(query)
        except Exception as err:
            log.error("execute", err)
            raise err

    def fetchall(self):
        try:
            return self._cursor.fetchall()
        except Exception as err:
            log.error("fetch all", err)
            raise err

    def commit(self):
        try:
            self.connection.commit()
        except Exception as err:
            log.error("commit", err)
            raise err
        self._cursor = None

    def rollback(self):
        try:
            self.connection.rollback()
        except Exception as err:
            log.error("rollback", err)
            raise err
        self._cursor = None


def MySqlStoreFactory(schema, host, port, user, password, database):
    def connector():
        return _MySQLAdapter(host, port, user, password, database)

    return SqlStore(schema, connector)
