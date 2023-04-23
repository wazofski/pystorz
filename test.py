from mgen.builder import Generate
from mgen.test import test_mgen

import logging, logging.config

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

from sql.store import SqliteStore, SqliteConnection
from generated.model import Schema

clt = SqliteStore(Schema(), SqliteConnection("test.db"))
from testing.store import common_test_suite

common_test_suite(clt)
