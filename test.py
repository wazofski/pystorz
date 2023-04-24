from mgen.builder import Generate
from mgen.test import test_mgen

import logging, logging.config

import os
import yaml
with open('config/logger.yml', 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f.read()))

log = logging.getLogger(__name__)


def test_mgen_can_generate():
    err = Generate("testing/model")
    
    assert err is None

log.debug("starting test_mgen_can_generate")

test_mgen_can_generate()
test_mgen()

def test_sqlite_store():
    from sql.store import SqliteStore, SqliteConnection
    from generated.model import Schema

    db_file = "test.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    clt = SqliteStore(Schema(), SqliteConnection(db_file))
    from testing.store import common_test_suite

    common_test_suite(clt)

test_sqlite_store()
