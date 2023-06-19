import logging
log = logging.getLogger(__name__)


class SQLAdapter:
    def __init__(self):
        self._connection = None
        self._cursor = None

    def connect(self):
        raise NotImplementedError()

    def connection(self):
        if not self._connection:
            self._cursor = None
            self._connection = self.connect()

        return self._connection

    def cursor(self, retry=True):
        try:
            if not self._cursor:
                connection = self.connection()
                self._cursor = connection.cursor()

            return self._cursor
        except Exception as err:
            if not retry:
                raise err

        self._connection = None
        self._cursor = None
        return self.cursor(False)

    def close(self):
        try:
            if self._cursor:
                self._cursor.close()

            if self._connection:
                self._connection.close()
        except Exception as err:
            log.error("close", err)

        self._connection = None
        self._cursor = None

    def execute(self, query, params=None, retry=True):
        try:
            cursor = self.cursor()
            if params:
                return cursor.execute(query, params)
            else:
                return cursor.execute(query)
        except Exception as err:
            if not retry:
                raise err

        self._cursor = None
        self._connection = None
        return self.execute(query, params, False)

    def fetchall(self, retry=True):
        try:
            return self.cursor().fetchall()
        except Exception as err:
            if not retry:
                raise err

        self._cursor = None
        self._connection = None
        return self.fetchall(False)

    def fetchone(self, retry=True):
        try:
            return self.cursor().fetchone()
        except Exception as err:
            if not retry:
                raise err

        self._cursor = None
        self._connection = None
        return self.fetchone(False)

    def commit(self, retry=True):
        try:
            return self.connection().commit()
        except Exception as err:
            log.info(f"exception: {retry}")
            if not retry:
                raise err

        self._cursor = None
        self._connection = None
        return self.commit(False)

    def rollback(self, retry=True):
        try:
            return self.connection().rollback()
        except Exception as err:
            if not retry:
                raise err

        self._cursor = None
        self._connection = None
        return self.rollback(False)
