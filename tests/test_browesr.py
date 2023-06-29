from config import globals
globals.logger_config()


# from tests.test_common import sqlite
from pystorz.browse import server
from generated import model


import logging

log = logging.getLogger(__name__)


def sqlite(db_file):
    import os

    from pystorz.sql.sqlite import SqliteStoreFactory
    from generated.model import Schema

    return SqliteStoreFactory(
            Schema(), db_file)



srv = server.Server(
    model.Schema(),
    sqlite("testsqlite.db"))

srv.Serve("localhost", 8080)
