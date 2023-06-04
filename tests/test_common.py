from config import globals
import pytest

import time

import logging

log = logging.getLogger(__name__)

globals.logger_config()

from datetime import datetime
from generated import model

from pystorz.internal import constants
from pystorz.store import options, utils, store
from pystorz.meta.store import MetaStore

thestore = store.Store()

stopper = None
worldName = "c137zxczx"
anotherWorldName = "j19zeta7 qweqw"
worldDescription = "zxkjhajkshdas world of argo"
newWorldDescription = "is only beoaoqwiewioqu"


def sqlite(db_file="testsqlite.db"):
    import os

    from pystorz.sql.sqlite import SqliteStoreFactory
    from generated.model import Schema

    if os.path.exists(db_file):
        os.remove(db_file)

    schema = Schema()
    return MetaStore(
        schema,
        SqliteStoreFactory(schema, db_file))


def mysql():
    from pystorz.sql.mysql import MySqlStoreFactory
    from generated.model import Schema

    schema = Schema()
    return MetaStore(
        schema,
        MySqlStoreFactory(
            schema,
            "127.0.0.1",
            "3306",
            "root",
            "qwerasdf",
            "pystorztestdb"))


def rest():
    log.debug("server/client setup")
    
    sqlite_store = sqlite("restsqlite.db")

    from pystorz.rest import server, client

    srv = server.Server(
        model.Schema(),
        sqlite_store,
        server.Expose(
            model.WorldKind,
            server.ActionGet,
            server.ActionCreate,
            server.ActionUpdate,
            server.ActionDelete),
        server.Expose(
            model.SecondWorldKind,
            server.ActionGet,
            server.ActionCreate,
            server.ActionUpdate,
            server.ActionDelete),
    )

    host = "127.0.0.1"
    port = 8080
    url = f"http://{host}:{port}"

    global stopper
    stopper = srv.Serve(host, port)
    # time.sleep(3)

    return client.Client(url, model.Schema())


@pytest.fixture(params=[sqlite()])
# @pytest.fixture(params=[mysql()])
# @pytest.fixture(params=[rest()])
# @pytest.fixture(params=[sqlite(), rest()])
def thestore(request):
    return request.param


def test_clear_everything(thestore):
    ret = thestore.List(model.WorldKindIdentity)
    for r in ret:
        thestore.Delete(r.Metadata().Identity())

    ret = thestore.List(model.SecondWorldKindIdentity)
    for r in ret:
        thestore.Delete(r.Metadata().Identity())

    ret = thestore.List(model.SecondWorldKindIdentity)
    assert len(ret) == 0
    ret = thestore.List(model.WorldKindIdentity)
    assert len(ret) == 0

    # ret = thestore.List(model.ThirdWorldKindIdentity)
    #
    # for r in ret:
    #     thestore.Delete(r.Metadata().Identity())
    #


def test_list_empty_lists(thestore):
    ret = thestore.List(model.WorldKindIdentity)

    assert ret is not None
    assert len(ret) == 0


def test_post_objects(thestore):
    w = model.WorldFactory()
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


def test_post_other_objects(thestore):
    w = model.SecondWorldFactory()
    w.External().SetName("abc")
    ret = thestore.Create(w)

    assert ret != None
    assert len(str(ret.Metadata().Identity())) != 0
    ret = thestore.Get(ret.Metadata().Identity())

    assert ret != None
    w = ret
    assert w != None
    ret = thestore.Get(model.SecondWorldIdentity("abc"))

    assert ret != None
    w = ret
    assert w != None


def test_get_objects(thestore):
    ret = thestore.Get(model.WorldIdentity("abc"))

    assert ret != None
    assert len(str(ret.Metadata().Identity())) != 0
    world = ret
    assert world != None


def test_can_not_double_post_objects(thestore):
    w = model.WorldFactory()

    w.External().SetName("abc")

    err = None
    ret = None
    try:
        ret = thestore.Create(w)
    except Exception as e:
        # log.error(e)
        err = e

    assert err is not None
    assert str(err) == constants.ErrObjectExists
    assert ret is None


def test_can_put_objects(thestore):
    w = model.WorldFactory()

    w.External().SetName("abc")
    w.External().SetDescription("def")

    ret = thestore.Update(model.WorldIdentity("abc"), w)

    assert ret is not None

    world = ret
    assert world is not None
    assert world.External().Description() == "def"


def test_can_put_change_naming_props(thestore):
    # object name abc exists

    original = thestore.Get(model.WorldIdentity("abc"))

    original.External().SetName("def")
    original.External().SetDescription("originally abc")
    ret = thestore.Update(original.Metadata().Identity(), original)

    assert ret is not None

    obj_def = thestore.Get(ret.Metadata().Identity())
    assert obj_def is not None
    assert obj_def.External().Name() == "def"
    assert obj_def.External().Description() == "originally abc"

    obj_def_by_name = thestore.Get(model.WorldIdentity("def"))
    assert obj_def_by_name is not None
    assert obj_def_by_name.External().Name() == "def"
    assert obj_def_by_name.External().Description() == "originally abc"

    # object name abc should not exist

    try:
        ret = None
        ret = thestore.Get(model.WorldIdentity("abc"))
    except Exception as e:
        err = e

    assert ret is None
    assert err is not None
    assert str(err) == constants.ErrNoSuchObject

    # good now we create object with name abc
    object_new_abc = model.WorldFactory()
    object_new_abc.External().SetName("abc")
    object_new_abc.External().SetDescription("new abc object")

    object_new_abc = thestore.Create(object_new_abc)
    assert object_new_abc is not None

    ret = thestore.Get(model.WorldIdentity("abc"))
    assert ret is not None
    assert ret.External().Name() == "abc"
    assert ret.External().Description() == object_new_abc.External().Description()

    # now we try to change name of new object abc to def

    object_new_abc = ret
    object_new_abc.External().SetName("def")

    # now what if there is another object with the new name?

    err = None
    try:
        ret = None
        ret = thestore.Update(object_new_abc.Metadata().Identity(), object_new_abc)
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrObjectExists
    assert ret is None

    # confirm nothing changed in abc and def objects
    obj = thestore.Get(model.WorldIdentity("abc"))
    assert obj is not None
    assert obj.External().Name() == "abc"
    assert obj.External().Description() == object_new_abc.External().Description()

    obj = thestore.Get(model.WorldIdentity("def"))
    assert obj is not None
    assert obj.External().Name() == "def"
    assert obj.External().Description() == "originally abc"

    # clean up
    thestore.Delete(model.WorldIdentity("abc"))


def test_can_put_objects_by_id(thestore):
    ret = thestore.Get(model.WorldIdentity("def"))

    assert ret is not None

    world = ret
    assert world is not None
    world.External().SetDescription("zxc")

    log.info(utils.pps(world.ToJson()))

    ret = thestore.Update(world.Metadata().Identity(), world)

    log.info(utils.pps(ret.ToJson()))

    assert ret is not None

    world = ret
    assert world is not None
    assert world.External().Description() == "zxc"


def test_cannot_put_nonexistent_objects(thestore):
    world = model.WorldFactory()
    assert world is not None
    world.External().SetName("zxcxzcxz")

    err = None
    try:
        ret = None
        ret = thestore.Update(model.WorldIdentity("zcxzcxzc"), world)
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrNoSuchObject
    assert ret is None


def test_cannot_put_nonexistent_objects_by_id(thestore):
    world = model.WorldFactory()
    world.External().SetName("zxcxzcxz")

    err = None
    try:
        ret = None
        ret = thestore.Update(world.Metadata().Identity(), world)
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrNoSuchObject
    assert ret is None


def test_cannot_put_objects_of_wrong_type(thestore):
    world = model.SecondWorldFactory()
    world.External().SetName("zxcxzcxz")

    thestore.Create(world)

    existing_world = thestore.List(model.WorldKindIdentity)[0]
    assert existing_world is not None

    err = None
    try:
        ret = None
        ret = thestore.Update(existing_world.Metadata().Identity(), world)
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrObjectIdentityMismatch
    assert ret is None


def test_can_get_objects(thestore):
    ret = thestore.Get(model.WorldIdentity("def"))

    assert ret is not None

    world = ret
    assert world is not None


def test_can_get_objects_by_id(thestore):
    ret = thestore.Get(model.WorldIdentity("def"))

    assert ret is not None

    world = ret
    assert world is not None

    ret = thestore.Get(world.Metadata().Identity())

    assert ret is not None

    world = ret
    assert world is not None


def test_cannot_get_nonexistent_objects(thestore):
    err = None
    try:
        ret = None
        ret = thestore.Get(model.WorldIdentity("zxcxzczx"))
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrNoSuchObject
    assert ret is None


def test_cannot_get_nonexistent_objects_by_id(thestore):
    err = None
    try:
        ret = None
        ret = thestore.Get(store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrNoSuchObject
    assert ret is None


def test_can_delete_objects(thestore):
    w = model.WorldFactory()
    w.External().SetName("tobedeleted")

    ret = thestore.Create(w)

    assert ret is not None

    thestore.Delete(model.WorldIdentity(w.External().Name()))

    err = None
    try:
        ret = None
        ret = thestore.Get(model.WorldIdentity(w.External().Name()))
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrNoSuchObject
    assert ret is None


def test_can_delete_objects_by_id(thestore):
    w = model.WorldFactory()
    w.External().SetName("tobedeleted")

    ret = thestore.Create(w)

    assert ret is not None
    w = ret

    thestore.Delete(w.Metadata().Identity())

    err = None
    try:
        ret = None
        ret = thestore.Get(w.Metadata().Identity())
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrNoSuchObject
    assert ret is None


def test_delete_nonexistent_objects(thestore):
    err = None
    try:
        thestore.Delete(model.WorldIdentity("akjsdhsajkhdaskjh"))
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrNoSuchObject


def test_delete_nonexistent_objects_by_id(thestore):
    err = None
    try:
        thestore.Delete(store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrNoSuchObject


def test_get_nil_identity(thestore):
    err = None
    try:
        thestore.Get(None)
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrInvalidPath


def test_list_nil_identity(thestore):
    err = None
    try:
        thestore.List(None)
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrInvalidPath

# def test_list_invalid_identity(thestore):
#     err = None
#     try:
#         thestore.List(store.ObjectIdentity("aksjdhsajkd/"))
#     except Exception as e:
#         err = e

#     assert err is not None
#     assert str(err) == constants.ErrInvalidPath

def test_create_nil_object(thestore):
    err = None
    try:
        thestore.Create(None)
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrObjectNil


def test_put_nil_identity(thestore):
    err = None
    try:
        thestore.Update(None, model.WorldFactory())
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrInvalidPath


def test_put_nil_object(thestore):
    err = None
    try:
        thestore.Update(model.WorldIdentity("qwe"), None)
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrObjectNil


def test_delete_nil_identity(thestore):
    err = None
    try:
        thestore.Delete(None)
    except Exception as e:
        err = e

    assert err is not None
    assert str(err) == constants.ErrInvalidPath


def test_delete_empty_identity(thestore):
    err = None
    try:
        thestore.Delete(model.WorldIdentity(""))
    except Exception as e:
        err = e

    assert err is not None
    # assert str(err) == constants.ErrNoSuchObject


def test_create_multiple_objects(thestore):
    ret = thestore.List(model.WorldKindIdentity)

    for r in ret:
        thestore.Delete(r.Metadata().Identity())

    world = model.WorldFactory()
    world.External().SetName(worldName)
    world.External().SetDescription(worldDescription)

    world2 = model.WorldFactory()
    world2.External().SetName(anotherWorldName)
    world2.External().SetDescription(newWorldDescription)

    thestore.Create(world)

    thestore.Create(world2)

    world3 = model.SecondWorldFactory()
    world3.External().SetName(anotherWorldName)
    world3.External().SetDescription(newWorldDescription)

    thestore.Create(world3)


def test_can_list_multiple_objects(thestore):
    ret = thestore.List(model.WorldKindIdentity)

    assert ret is not None
    assert len(ret) == 2

    ret.sort(key=lambda r: r.External().Name())

    world = ret[0]
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription

    world2 = ret[1]
    assert world2.External().Name() == anotherWorldName
    assert world2.External().Description() == newWorldDescription


def test_can_list_and_sort_multiple_objects(thestore):
    ret = thestore.List(model.WorldKindIdentity, options.Order("external.name"))

    assert ret is not None
    assert len(ret) == 2

    world = ret[0]
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription

    world2 = ret[1]
    assert world2.External().Name() == anotherWorldName
    assert world2.External().Description() == newWorldDescription

    ret = thestore.List(
        model.WorldKindIdentity,
        options.Order("external.name", False)
    )

    assert ret is not None
    assert len(ret) == 2

    world = ret[1]
    world2 = ret[0]
    assert world.External().Name() == worldName
    assert world2.External().Name() == anotherWorldName


def test_list_and_paginate_multiple_objects(thestore):
    ret = thestore.List(
        model.WorldKindIdentity,
        options.Order("external.name"),
        options.PageSize(1)
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription

    ret = thestore.List(
        model.WorldKindIdentity,
        options.Order("external.name"),
        options.PageSize(1),
        options.PageOffset(1)
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert world.External().Name() == anotherWorldName

    ret = thestore.List(
        model.WorldKindIdentity,
        options.Order("external.name"),
        options.PageOffset(1),
        options.PageSize(1000)
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert world.External().Name() == anotherWorldName


def test_list_and_filter_by_primary_key(thestore):
    ret = thestore.List(model.WorldKindIdentity)

    keys = []
    for o in ret:
        keys.append(o.PrimaryKey())

    assert len(keys) == 2

    ret = thestore.List(
        model.WorldKindIdentity,
        options.In("external.name", [keys[0], keys[1]])
    )

    assert len(ret) == 2

    for k in keys:
        ret = thestore.List(
            model.WorldKindIdentity,
            options.In("external.name", [k]))

        assert len(ret) == 1
        assert ret[0].PrimaryKey() == k


def test_list_and_filter_by_nonexistent_props(thestore):
    try:
        thestore.List(
            model.WorldKindIdentity,
            options.Eq("metadata.askdjhasd", "asdsadas"),
        )
        assert False
    except Exception as e:
        assert str(e) == constants.ErrInvalidFilter


def test_cannot_list_specific_object(thestore):
    try:
        thestore.List(model.WorldIdentity(worldName))
        assert False
    except Exception as e:
        assert str(e) == constants.ErrInvalidPath


def test_cannot_list_specific_nonexistent_object(thestore):
    try:
        thestore.List(model.WorldIdentity("akjhdsjkhdaskjhdaskj"))
        assert False
    except Exception as e:
        assert str(e) == constants.ErrInvalidPath


def test_list_and_eq_filter(thestore):
    # ret = thestore.List(model.WorldKindIdentity)
    # for r in ret:
    #     log.info("object {}".format(utils.pps(r.ToJson())))

    ret = thestore.List(
        model.WorldKindIdentity,
        options.Eq("external.name", worldName))

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, model.World)
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription


def test_list_and_filter_by_id(thestore):
    ret = thestore.List(
        model.WorldKindIdentity,
        options.Eq("external.name", worldName))
    
    world_id = ret[0].Metadata().Identity()
    
    ret = thestore.List(
        model.WorldKindIdentity,
        options.Eq("metadata.identity", str(world_id))
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, model.World)
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription


def test_list_and_filter_by_nonexistent_id(thestore):
    ret = thestore.List(
        model.WorldKindIdentity,
        options.Eq("metadata.identity", "asdasdasd")
    )

    assert ret is not None
    assert len(ret) == 0


def test_metadata_updates(thestore):
    # create a new world
    name = "test_metadata_updates"
    world = model.WorldFactory()
    world.External().SetName(name)

    # log.debug(">> creating world: {}".format(name))

    ret = thestore.Create(world)
    assert ret is not None
    r = ret.Metadata().Revision()
    assert r == 1

    # check the created time
    meta_id = ret.Metadata().Identity()
    # log.debug("meta_id: {}".format(meta_id))

    assert meta_id is not None
    assert len(str(meta_id)) > 0

    ct = ret.Metadata().Created()
    assert ct is not None

    world.External().SetDescription("test_metadata_updates")

    # log.debug(">> updating world: {}".format(name))
    ret = thestore.Update(model.WorldIdentity(name), world)

    assert ret is not None
    assert ret.Metadata().Revision() == 2

    # meta id must be the same
    meta_id2 = ret.Metadata().Identity()
    # log.debug("meta_id2: {}".format(meta_id2))
    assert meta_id2 is not None
    assert len(str(meta_id2)) > 0
    assert meta_id == meta_id2

    # check the updated time
    ut = ret.Metadata().Updated()
    assert ut is not None
    assert ut > ct

    # check the created time must be the same
    ct2 = ret.Metadata().Created()
    assert ct2 is not None
    assert ct2 == ct

    # do a get and check the times
    # log.debug(">> getting world: {}".format(name))
    ret = thestore.Get(model.WorldIdentity(name))
    assert ret is not None
    assert ret.Metadata().Revision() == 2

    # check the created time must be the same
    ct3 = ret.Metadata().Created()
    assert ct3 is not None
    assert ct3 == ct

    # meta id must be the same
    meta_id2 = ret.Metadata().Identity()
    assert meta_id2 is not None
    assert len(meta_id2) > 0
    assert meta_id == meta_id2

    # check the updated time must be the same
    # check the updated time
    ut2 = ret.Metadata().Updated()
    assert ut2 is not None
    assert ut2 == ut
    assert ut2 > ct

    world = model.WorldFactory()
    newName = "test_metadata_updates22"
    world.External().SetName(newName)
    world.External().SetDescription("test_metadata_updates2222")

    ret33 = thestore.Update(model.WorldIdentity(name), world)
    assert ret33 is not None
    
    newName = "test_metadata_updates222"
    ret.External().SetName(newName)
    ret.External().SetDescription("test_metadata_updates22222")
    ret = thestore.Update(meta_id2, ret)

    # check the created time must be the same
    ct3 = ret.Metadata().Created()
    assert ct3 is not None
    assert ct3 == ct
    assert ret.Metadata().Revision() == 4

    # meta id must be the same
    meta_id2 = ret.Metadata().Identity()
    assert meta_id2 is not None
    assert len(meta_id2) > 0
    assert meta_id == meta_id2

    # check the updated time
    ut3 = ret.Metadata().Updated()
    ct3 = ret.Metadata().Created()
    assert ut3 > ut2
    assert ct3 == ct


def test_datetime_property_type(thestore):
    name = "test_datetime_property_type"
    world = model.WorldFactory()
    world.External().SetName(name)
    dt = datetime.now()
    world.External().SetDate(dt)

    assert world.External().Date() == dt

    ret = thestore.Create(world)
    assert ret is not None

    ndt = datetime.now()
    world.External().SetDate(ndt)
    ret = thestore.Update(ret.Metadata().Identity(), world)

    assert ret is not None

    # check the updated time
    rdt = ret.External().Date()
    assert rdt is not None
    assert rdt > dt

    # do a get and check the times
    ret = thestore.Get(model.WorldIdentity(name))
    assert ret is not None

    # check the updated time
    rdt2 = ret.External().Date()
    assert rdt2 is not None
    assert rdt2 > dt
    assert rdt2 == ndt


def test_weird_characters(thestore):
    world = model.WorldFactory()
    world.External().SetName("test_weird_characters")
    world.External().SetAlive(True)
    world.External().SetCounter(123)
    desc = "a's gone to $ with a # then did a ` WHERE an IN''SERT INTO'"
    world.External().SetDescription(desc)
    ret = thestore.Create(world)
    assert ret is not None

    ret = thestore.Get(model.WorldIdentity("test_weird_characters"))
    assert ret is not None
    assert ret.External().Description() == desc

    # list and filter
    ret = thestore.List(
        model.WorldKindIdentity, options.Eq("external.description", desc)
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, model.World)
    assert world.External().Name() == "test_weird_characters"
    assert world.External().Description() == desc


def test_list_and_filter_by_types(thestore):
    ret = thestore.List(model.WorldKindIdentity, options.Eq("external.counter", 123))

    assert ret is not None
    assert len(ret) == 1

    ret = thestore.List(model.WorldKindIdentity, options.Eq("external.alive", True))

    assert ret is not None
    assert len(ret) == 1


def test_list_and_filter_and_sort(thestore):
    ret = thestore.List(model.WorldKindIdentity)
    total_length = len(ret)
    for r in ret:
        r.External().SetAlive(True)
        thestore.Update(r.Metadata().Identity(), r)

    ret[0].External().SetAlive(False)
    thestore.Update(ret[0].Metadata().Identity(), ret[0])

    ret = thestore.List(
        model.WorldKindIdentity,
        options.Eq("external.alive", True),
        options.Order("external.name"),
    )

    assert ret is not None
    assert len(ret) == total_length - 1

    world = ret[0]
    # abc is not alive so the next one is anotherWorldName
    assert world.External().Name() == anotherWorldName

    ret = thestore.List(
        model.WorldKindIdentity,
        options.Eq("external.alive", True),
        options.Order("external.name", False),
    )

    assert ret is not None
    assert len(ret) == total_length - 1

    world = ret[0]
    # abc is not alive so the next one is anotherWorldName
    assert world.External().Name() != anotherWorldName


def test_list_and_map_of_struct(thestore):
    world = model.WorldFactory()
    world.External().SetName("test_list_and_map_of_struct")

    nested = model.NestedWorldFactory()
    nested.SetCounter(123)
    nested.SetAlive(True)

    world.External().Nested().SetL1([nested])
    world.External().Nested().SetL2({"nested": nested})

    d = world.External().Nested().L2()
    assert d["nested"].Counter() == 123
    l = world.External().Nested().L1()
    assert l[0].Counter() == 123

    ret = thestore.Create(world)
    assert ret is not None
    d = world.External().Nested().L2()
    assert d["nested"].Counter() == 123
    l = world.External().Nested().L1()
    assert l[0].Counter() == 123

    ret = thestore.Get(model.WorldIdentity("test_list_and_map_of_struct"))
    assert ret is not None

    d = world.External().Nested().L2()
    assert d["nested"].Counter() == 123
    assert d["nested"].Alive()

    l = world.External().Nested().L1()
    assert l[0].Counter() == 123
    assert l[0].Alive()


def test_list_and_not_eq_filter(thestore):
    ret = thestore.List(model.WorldKindIdentity)
    total_length = len(ret)

    ret = thestore.List(
        model.WorldKindIdentity, options.Not(options.Eq("external.name", worldName))
    )

    assert ret is not None
    assert len(ret) == total_length - 1

    for w in ret:
        assert w.External().Name() != worldName


def test_list_and_lt_gt_filter(thestore):
    ret = thestore.List(model.WorldKindIdentity)
    total_length = len(ret)
    i = 0
    for r in ret:
        r.External().SetCounter(i)
        thestore.Update(r.Metadata().Identity(), r)
        i += 10

    half = 10 * total_length // 2

    ret = thestore.List(model.WorldKindIdentity, options.Lt("external.counter", half))

    assert ret is not None
    for r in ret:
        assert r.External().Counter() < half

    ret = thestore.List(model.WorldKindIdentity, options.Gt("external.counter", half))

    assert ret is not None
    for r in ret:
        assert r.External().Counter() > half

    ret = thestore.List(
        model.WorldKindIdentity, options.Not(options.Lt("external.counter", half))
    )

    assert ret is not None
    for r in ret:
        assert r.External().Counter() >= half

    ret = thestore.List(
        model.WorldKindIdentity, options.Not(options.Gt("external.counter", half))
    )

    assert ret is not None
    for r in ret:
        assert r.External().Counter() <= half

    ret = thestore.List(
        model.WorldKindIdentity, options.Not(options.Lte("external.counter", half))
    )

    assert ret is not None
    for r in ret:
        assert r.External().Counter() > half

    ret = thestore.List(
        model.WorldKindIdentity, options.Not(options.Gte("external.counter", half))
    )

    assert ret is not None
    for r in ret:
        assert r.External().Counter() < half

    ret = thestore.List(model.WorldKindIdentity, options.Lte("external.counter", half))

    assert ret is not None
    for r in ret:
        assert r.External().Counter() <= half

    ret = thestore.List(model.WorldKindIdentity, options.Gte("external.counter", half))

    assert ret is not None
    for r in ret:
        assert r.External().Counter() >= half


def test_list_and_in_int_filter(thestore):
    ret = thestore.List(
        model.WorldKindIdentity, options.In("external.counter", [10, 20, 30, 40])
    )

    assert ret is not None
    assert len(ret) == 4

    ret = thestore.List(
        model.WorldKindIdentity,
        options.Not(options.In("external.counter", [10, 20, 30, 40])),
    )

    assert ret is not None
    assert len(ret) == 2

    for r in ret:
        assert r.External().Counter() not in [10, 20, 30, 40]


def test_list_and_in_bool_filter(thestore):
    ret = thestore.List(
        model.WorldKindIdentity,
        options.In("external.alive", [True])
    )

    assert ret is not None
    for r in ret:
        assert r.External().Alive()

    ret = thestore.List(
        model.WorldKindIdentity,
        options.In("external.alive", [False]),
    )

    assert ret is not None
    for r in ret:
        assert not r.External().Alive()

    ret = thestore.List(
        model.WorldKindIdentity,
        options.In("external.counter", [True]),
    )

    assert ret is not None
    assert len(ret) == 0


def test_list_and_AND_filter(thestore):
    ret = thestore.List(
        model.WorldKindIdentity, options.In("external.counter", [20, 30, 40, 50])
    )

    alive_count = 0
    for r in ret:
        if r.External().Alive():
            alive_count += 1

    ret = thestore.List(
        model.WorldKindIdentity,
        options.And(
            options.In("external.counter", [20, 30, 40, 50]),
            options.Eq("external.alive", True),
        ),
    )

    assert ret is not None
    assert len(ret) == alive_count
    assert alive_count < 4
    assert alive_count > 0

    for r in ret:
        assert r.External().Counter() in [20, 30, 40, 50]
        assert r.External().Alive()

    ret = thestore.List(
        model.WorldKindIdentity,
        options.And(
            options.In("external.counter", [20, 30, 40, 50]),
            options.Not(options.Eq("external.alive", True)),
        ),
    )

    assert ret is not None
    assert len(ret) == 4 - alive_count

    for r in ret:
        assert r.External().Counter() in [20, 30, 40, 50]
        assert not r.External().Alive()


def test_list_and_OR_filter(thestore):
    ret = thestore.List(
        model.WorldKindIdentity,
    )

    total_length = len(ret)

    alive_count = 0
    not_alive_counters = []
    for r in ret:
        if r.External().Alive():
            alive_count += 1
        else:
            not_alive_counters.append(r.External().Counter())

    ret = thestore.List(
        model.WorldKindIdentity,
        options.Or(
            options.In("external.counter", not_alive_counters),
            options.Eq("external.alive", True),
        ),
    )

    assert ret is not None
    assert len(ret) == total_length

    ret = thestore.List(
        model.WorldKindIdentity,
        options.Or(
            options.Not(options.In("external.counter", not_alive_counters)),
            options.Eq("external.alive", True),
        ),
    )

    assert ret is not None
    assert len(ret) == alive_count


def test_delete_filtered(thestore):
    ret = thestore.List(model.WorldKindIdentity, options.Eq("external.alive", True))
    assert ret is not None
    alive_count = len(ret)
    assert alive_count > 0

    thestore.Delete(model.WorldKindIdentity, options.Eq("external.alive", True))

    ret = thestore.List(model.WorldKindIdentity)
    assert ret is not None
    assert len(ret) > 0
    for r in ret:
        assert r.External().Alive() == False


def test_sql_injection(thestore):
    # try to add a sql injection into a list query
    ret = thestore.List(
        model.WorldKindIdentity,
        options.Eq("external.name", "'; DROP TABLE Objects; --"),
    )
    assert ret is not None
    assert len(ret) == 0

    # try to add a sql injection into a naming property
    world = model.WorldFactory()
    world.External().SetName("', '', ''); DROP TABLE Objects; --")
    world.External().SetCounter(1)
    errored = False
    try:
        thestore.Create(world)
    except Exception as ex:
        log.info("Caught exception: {}".format(ex))
        errored = True

    # try to add a sql injection into another property
    world = model.WorldFactory()
    name = "sqlinjector"
    world.External().SetName(name)
    desc = "'); DROP TABLE Objects; --"
    world.External().SetDescription(desc)
    world.External().SetCounter(1)
    thestore.Create(world)

    ret = thestore.List(
        model.WorldKindIdentity, options.Eq("external.name", "sqlinjector")
    )
    assert ret[0].External().Description() == desc
    ret = thestore.Get(
        model.WorldIdentity(name), options.Eq("external.name", "sqlinjector")
    )
    assert ret.External().Description() == desc

    ret.External().SetName("', '', ''); DROP TABLE Objects; --")
    errored = False
    try:
        thestore.Update(ret.Metadata().Identity(), ret)
    except Exception as ex:
        log.info("Caught exception: {}".format(ex))
        errored = True

    assert errored


@pytest.mark.skip
def test_performance(thestore):
    NUMBER_OF_OBJECTS = 1000

    log.info("Creating {} objects".format(NUMBER_OF_OBJECTS))
    graph_create = [0.0] * NUMBER_OF_OBJECTS
    tc1 = time.time()
    objects = set()
    for i in range(NUMBER_OF_OBJECTS):
        t11 = time.time()
        world = model.WorldFactory()
        world.External().SetName("world-{}".format(i))
        world.External().SetCounter(i)
        world.External().SetAlive(i % 2 == 0)
        thestore.Create(world)
        t22 = time.time()

        objects.add(world)

        # append milliseconds it took for a single create
        graph_create[i] = t22 - t11
    tc2 = time.time()

    log.info("Updating {} objects".format(NUMBER_OF_OBJECTS))
    graph_update = [0.0] * NUMBER_OF_OBJECTS
    i = 0
    tu1 = time.time()
    for o in objects:
        t11 = time.time()
        o.External().SetAlive(not o.External().Alive())
        thestore.Update(o.Metadata().Identity(), o)
        t22 = time.time()

        # append milliseconds it took for a single create
        graph_update[i] = t22 - t11
        i += 1

    tu2 = time.time()

    tl1 = time.time()
    log.info("Listing {} objects".format(NUMBER_OF_OBJECTS))
    thestore.List(model.WorldKindIdentity)
    tl2 = time.time()

    tlh1 = time.time()
    log.info("Listing {} objects".format(NUMBER_OF_OBJECTS // 2))
    thestore.List(model.WorldKindIdentity, options.Eq("external.alive", True))
    tlh2 = time.time()

    tg1 = time.time()
    graph_get = [0.0] * NUMBER_OF_OBJECTS
    log.info("Getting {} objects".format(NUMBER_OF_OBJECTS))
    for i in range(NUMBER_OF_OBJECTS):
        tgg1 = time.time()
        thestore.Get(model.WorldIdentity("world-{}".format(i)))
        tgg2 = time.time()
        graph_get[i] = tgg2 - tgg1

    tg2 = time.time()

    td1 = time.time()
    graph_del = [0.0] * NUMBER_OF_OBJECTS
    log.info("Deleting {} objects".format(NUMBER_OF_OBJECTS))
    for i in range(NUMBER_OF_OBJECTS):
        tgg1 = time.time()
        thestore.Delete(model.WorldIdentity("world-{}".format(i)))
        tgg2 = time.time()
        graph_del[i] = tgg2 - tgg1

    td2 = time.time()

    for i in range(NUMBER_OF_OBJECTS):
        world = model.WorldFactory()
        world.External().SetName("world-{}".format(i))
        world.External().SetCounter(1000)
        world.External().SetAlive(i % 2 == 0)
        thestore.Create(world)

    tdd1 = time.time()
    thestore.Delete(model.WorldKindIdentity, options.Eq("external.counter", 1000))
    tdd2 = time.time()

    ret = thestore.List(model.WorldKindIdentity)
    assert ret is not None
    assert len(ret) > 0
    for r in ret:
        assert r.External().Counter() != 1000

    log.info(f"Performance results: {NUMBER_OF_OBJECTS} objects")
    log.info("Create: \t\t\t{}s".format(tc2 - tc1))
    log.info("Update: \t\t\t{}s".format(tu2 - tu1))
    log.info("List Half:\t\t{}s".format(tlh2 - tlh1))
    log.info("List: \t\t\t{}s".format(tl2 - tl1))
    log.info("Get:\t\t\t{}s".format(tg2 - tg1))
    log.info("Delete: \t\t\t{}s".format(td2 - td1))
    log.info("Delete Batch: \t\t{}s".format(tdd2 - tdd1))

    # plot the rest of the graphs
    import matplotlib.pyplot as plt

    plt.figure()
    plt.plot(graph_create, label="create")
    plt.savefig("perf_create.png")

    plt.figure()
    plt.plot(graph_update, label="update")
    plt.savefig("perf_update.png")

    plt.figure()
    plt.plot(graph_get, label="get")
    plt.savefig("perf_get.png")

    plt.figure()
    plt.plot(graph_del, label="delete")
    plt.savefig("perf_delete.png")


def test_cleanup(thestore):
    global stopper
    if stopper is not None:
        stopper()
        stopper = None
