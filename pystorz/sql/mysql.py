import mysql.connector
from pystorz.sql.store import SqlStore


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
        self._cursor = None
        self.connection = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=self.database
        )
        return self.connection

    def cursor(self):
        if self.connection is None:
            self.connect()
        
        if self._cursor is None:
            self._cursor = self.connection.cursor()

        return self._cursor

    def close(self):
        if self._cursor:
            self._cursor.close()
        if self.connection:
            self.connection.close()

    def execute(self, query, params=None):
        if self._cursor is None:
            self.cursor()
        
        if params:
            self._cursor.execute(query, params)
        else:
            self._cursor.execute(query)

    def fetchall(self):
        return self._cursor.fetchall()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()


def MySqlStoreFactory(schema, host, port, user, password, database):
    def connector():
        return _MySQLAdapter(host, port, user, password, database)

    return SqlStore(schema, connector)
