import os
import sys

sys.path.append("src")

from pystorz.mgen.builder import Generate
from pystorz.mgen.test import test_mgen

import logging, logging.config

import yaml
with open('config/logger.yml', 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f.read()))

log = logging.getLogger(__name__)


def test_mgen_can_generate():
    err = Generate("tests/model")
    
    assert err is None

log.debug("starting test_mgen_can_generate")

test_mgen_can_generate()
test_mgen()

def test_sqlite_store():
    from pystorz.sql.store import SqliteStore, SqliteConnection
    from generated.model import Schema

    db_file = "test.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    clt = SqliteStore(Schema(), SqliteConnection(db_file))
    from tests.store import common_test_suite

    common_test_suite(clt)

test_sqlite_store()
