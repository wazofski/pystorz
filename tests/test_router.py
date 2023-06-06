import os
import pytest
import logging

from config import globals

log = logging.getLogger(__name__)

globals.logger_config()

from generated import model

from pystorz.meta.store import MetaStore
from pystorz.sql.sqlite import SqliteStoreFactory
from pystorz.router.store import RouteStore

def sqlite(db_file):
    if os.path.exists(db_file):
        os.remove(db_file)

    return MetaStore(
        SqliteStoreFactory(model.Schema(), db_file))


def router():
    return RouteStore(
        None,
        {
            model.WorldKind: sqlite("world.db"),
            model.SecondWorldKind: sqlite("second_world.db"),
        }
    )


@pytest.fixture(params=[router()])
def thestore(request):
    return request.param


def test_list_empty_lists(thestore):
    ret = thestore.List(model.WorldKindIdentity)

    assert ret is not None
    assert len(ret) == 0

    ret = thestore.List(model.SecondWorldKindIdentity)

    assert ret is not None
    assert len(ret) == 0



def test_post_objects(thestore):
    w = model.WorldFactory()
    w.External().SetName("abc")
    ret = thestore.Create(w)

    assert ret is not None
    assert len(str(ret.Metadata().Identity())) != 0

    w = model.SecondWorldFactory()
    w.External().SetName("abc")
    ret = thestore.Create(w)

    assert ret is not None
    assert len(str(ret.Metadata().Identity())) != 0


def test_list_single_object(thestore):
    ret = thestore.List(model.WorldKindIdentity)

    assert ret is not None
    assert len(ret) == 1
    world = ret[0]
    assert world.External().Name() == "abc"

    ret = thestore.List(model.SecondWorldKindIdentity)

    assert ret is not None
    assert len(ret) == 1
    world = ret[0]
    assert world.External().Name() == "abc"


def test_list_visa_versa_objects(thestore):
    stor1 = thestore._getStore(model.WorldKindIdentity.Type())
    stor2 = thestore._getStore(model.SecondWorldKindIdentity.Type())

    ret = stor2.List(model.WorldKindIdentity)
    assert ret is not None
    assert len(ret) == 0

    ret = stor1.List(model.SecondWorldKindIdentity)
    assert ret is not None
    assert len(ret) == 0


def test_cannot_post_other_objects(thestore):
    w = model.ThirdWorldFactory()
    w.External().SetName("abc")
    
    ret = None
    err = None
    try:
        ret = thestore.Create(w)
    except Exception as e:
        err = e
    
    assert ret == None
    assert err != None
