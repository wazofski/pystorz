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

clt = store.Store()

world_id = None
worldName = "c137zxczx"
anotherWorldName = "j19zeta7 qweqw"
worldDescription = "zxkjhajkshdas world of argo"
newWorldDescription = "is only beoaoqwiewioqu"

@pytest.fixture
def sqlite():
    import os
    
    from pystorz.sql.store import SqliteStore, SqliteConnection
    from generated.model import Schema

    db_file = "test.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    global clt
    clt = SqliteStore(Schema(), SqliteConnection(db_file))


def test_clear_everything():
    ret = clt.List(model.WorldKindIdentity)
    for r in ret:
        clt.Delete(r.Metadata().Identity())

    ret = clt.List(model.SecondWorldKindIdentity)
    for r in ret:
        clt.Delete(r.Metadata().Identity())

    ret = clt.List(model.SecondWorldKindIdentity)
    assert len(ret) == 0
    ret = clt.List(model.WorldKindIdentity)
    assert len(ret) == 0

    # ret = clt.List(model.ThirdWorldKindIdentity)
    #
    # for r in ret:
    #     clt.Delete(r.Metadata().Identity())
    #


def test_list_empty_lists():
    ret = clt.List(model.WorldKindIdentity)

    assert ret is not None
    assert len(ret) == 0


def test_post_objects():
    w = model.WorldFactory()
    w.External().SetName("abc")
    ret = clt.Create(w)

    assert ret is not None
    assert len(str(ret.Metadata().Identity())) != 0


def test_list_single_object():
    ret = clt.List(model.WorldKindIdentity)

    assert ret is not None
    assert len(ret) == 1
    world = ret[0]
    assert world.External().Name() == "abc"


def test_post_other_objects():
    w = model.SecondWorldFactory()
    w.External().SetName("abc")
    ret = clt.Create(w)

    assert ret != None
    assert len(str(ret.Metadata().Identity())) != 0
    ret = clt.Get(ret.Metadata().Identity())

    assert ret != None
    w = ret
    assert w != None
    ret = clt.Get(model.SecondWorldIdentity("abc"))

    assert ret != None
    w = ret
    assert w != None


def test_get_objects():
    ret = clt.Get(model.WorldIdentity("abc"))

    assert ret != None
    assert len(str(ret.Metadata().Identity())) != 0
    world = ret
    assert world != None


def test_can_not_double_post_objects():
    w = model.WorldFactory()

    w.External().SetName("abc")

    err = None
    ret = None
    try:
        ret = clt.Create(w)
    except Exception as e:
        # log.error(e)
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))
    assert ret is None


def test_can_put_objects():
    w = model.WorldFactory()

    w.External().SetName("abc")
    w.External().SetDescription("def")

    ret = clt.Update(model.WorldIdentity("abc"), w)

    assert ret is not None

    world = ret
    assert world is not None
    assert world.External().Description() == "def"


def test_can_put_change_naming_props():
    # object name abc exists

    original = clt.Get(model.WorldIdentity("abc"))

    original.External().SetName("def")
    original.External().SetDescription("originally abc")
    ret = clt.Update(original.Metadata().Identity(), original)

    assert ret is not None

    obj_def = clt.Get(ret.Metadata().Identity())
    assert obj_def is not None
    assert obj_def.External().Name() == "def"
    assert obj_def.External().Description() == "originally abc"

    obj_def_by_name = clt.Get(model.WorldIdentity("def"))
    assert obj_def_by_name is not None
    assert obj_def_by_name.External().Name() == "def"
    assert obj_def_by_name.External().Description() == "originally abc"

    # object name abc should not exist

    try:
        ret = None
        ret = clt.Get(model.WorldIdentity("abc"))
    except Exception as e:
        err = e

    assert ret is None
    assert err is not None
    log.info("expected error: {}".format(str(err)))
    assert str(err) == constants.ErrNoSuchObject

    # good now we create object with name abc
    object_new_abc = model.WorldFactory()
    object_new_abc.External().SetName("abc")
    object_new_abc.External().SetDescription("new abc object")

    object_new_abc = clt.Create(object_new_abc)
    assert object_new_abc is not None

    ret = clt.Get(model.WorldIdentity("abc"))
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
        ret = clt.Update(object_new_abc.Metadata().Identity(), object_new_abc)
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))
    assert str(err) == constants.ErrObjectExists
    assert ret is None

    # confirm nothing changed in abc and def objects
    obj = clt.Get(model.WorldIdentity("abc"))
    assert obj is not None
    assert obj.External().Name() == "abc"
    assert obj.External().Description() == object_new_abc.External().Description()

    obj = clt.Get(model.WorldIdentity("def"))
    assert obj is not None
    assert obj.External().Name() == "def"
    assert obj.External().Description() == "originally abc"

    # clean up
    clt.Delete(model.WorldIdentity("abc"))


def test_can_put_objects_by_id():
    ret = clt.Get(model.WorldIdentity("def"))

    assert ret is not None

    world = ret
    assert world is not None
    world.External().SetDescription("zxc")

    log.info(utils.pps(world.ToJson()))

    ret = clt.Update(world.Metadata().Identity(), world)

    log.info(utils.pps(ret.ToJson()))

    assert ret is not None

    world = ret
    assert world is not None
    assert world.External().Description() == "zxc"


def test_cannot_put_nonexistent_objects():
    world = model.WorldFactory()
    assert world is not None
    world.External().SetName("zxcxzcxz")

    err = None
    try:
        ret = None
        ret = clt.Update(model.WorldIdentity("zcxzcxzc"), world)
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))
    assert ret is None


def test_cannot_put_nonexistent_objects_by_id():
    world = model.WorldFactory()
    world.External().SetName("zxcxzcxz")

    err = None
    try:
        ret = None
        ret = clt.Update(world.Metadata().Identity(), world)
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))

    assert ret is None


def test_cannot_put_objects_of_wrong_type():
    world = model.SecondWorldFactory()
    world.External().SetName("zxcxzcxz")

    err = None
    try:
        ret = None
        ret = clt.Update(model.WorldIdentity("qwe"), world)
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))

    assert ret is None


def test_can_get_objects():
    ret = clt.Get(model.WorldIdentity("def"))

    assert ret is not None

    world = ret
    assert world is not None


def test_can_get_objects_by_id():
    ret = clt.Get(model.WorldIdentity("def"))

    assert ret is not None

    world = ret
    assert world is not None

    ret = clt.Get(world.Metadata().Identity())

    assert ret is not None

    world = ret
    assert world is not None


def test_cannot_get_nonexistent_objects():
    err = None
    try:
        ret = None
        ret = clt.Get(model.WorldIdentity("zxcxzczx"))
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))

    assert ret is None


def test_cannot_get_nonexistent_objects_by_id():
    err = None
    try:
        ret = None
        ret = clt.Get(store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))

    assert ret is None


def test_can_delete_objects():
    w = model.WorldFactory()
    w.External().SetName("tobedeleted")

    ret = clt.Create(w)

    assert ret is not None

    clt.Delete(model.WorldIdentity(w.External().Name()))

    err = None
    try:
        ret = None
        ret = clt.Get(model.WorldIdentity(w.External().Name()))
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))

    assert ret is None


def test_can_delete_objects_by_id():
    w = model.WorldFactory()
    w.External().SetName("tobedeleted")

    ret = clt.Create(w)

    assert ret is not None
    w = ret

    clt.Delete(w.Metadata().Identity())

    err = None
    try:
        ret = None
        ret = clt.Get(w.Metadata().Identity())
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))

    assert ret is None


def test_delete_nonexistent_objects():
    err = None
    try:
        clt.Delete(model.WorldIdentity("akjsdhsajkhdaskjh"))
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


def test_delete_nonexistent_objects_by_id():
    err = None
    try:
        clt.Delete(store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


def test_get_nil_identity():
    err = None
    try:
        clt.Get("")
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


def test_create_nil_object():
    err = None
    try:
        clt.Create(None)
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


def test_put_nil_identity():
    err = None
    try:
        clt.Update("", model.WorldFactory())
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


def test_put_nil_object():
    err = None
    try:
        clt.Update(model.WorldIdentity("qwe"), None)
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


def test_delete_nil_identity():
    err = None
    try:
        clt.Delete("")
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


def test_delete_empty_identity():
    err = None
    try:
        clt.Delete(model.WorldIdentity(""))
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


def test_create_multiple_objects():
    ret = clt.List(model.WorldKindIdentity)

    for r in ret:
        clt.Delete(r.Metadata().Identity())

    world = model.WorldFactory()
    world.External().SetName(worldName)
    world.External().SetDescription(worldDescription)

    world2 = model.WorldFactory()
    world2.External().SetName(anotherWorldName)
    world2.External().SetDescription(newWorldDescription)

    clt.Create(world)

    clt.Create(world2)

    world3 = model.SecondWorldFactory()
    world3.External().SetName(anotherWorldName)
    world3.External().SetDescription(newWorldDescription)

    clt.Create(world3)


def test_can_list_multiple_objects():
    ret = clt.List(model.WorldKindIdentity)

    assert ret is not None
    assert len(ret) == 2

    ret.sort(key=lambda r: r.External().Name())

    world = ret[0]
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription

    world2 = ret[1]
    assert world2.External().Name() == anotherWorldName
    assert world2.External().Description() == newWorldDescription


def test_can_list_and_sort_multiple_objects():
    ret = clt.List(model.WorldKindIdentity, options.Order("external.name"))

    assert ret is not None
    assert len(ret) == 2

    world = ret[0]
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription

    world2 = ret[1]
    assert world2.External().Name() == anotherWorldName
    assert world2.External().Description() == newWorldDescription

    ret = clt.List(
        model.WorldKindIdentity,
        options.Order("external.name", False),
    )

    assert ret is not None
    assert len(ret) == 2

    world = ret[1]
    world2 = ret[0]
    assert world.External().Name() == worldName
    assert world2.External().Name() == anotherWorldName


def test_list_and_paginate_multiple_objects():
    ret = clt.List(
        model.WorldKindIdentity, options.Order("external.name"), options.PageSize(1)
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription

    ret = clt.List(
        model.WorldKindIdentity,
        options.Order("external.name"),
        options.PageSize(1),
        options.PageOffset(1),
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert world.External().Name() == anotherWorldName

    ret = clt.List(
        model.WorldKindIdentity,
        options.Order("external.name"),
        options.PageOffset(1),
        options.PageSize(1000),
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert world.External().Name() == anotherWorldName


def test_list_and_filter_by_primary_key():
    ret = clt.List(model.WorldKindIdentity)

    keys = []
    for o in ret:
        keys.append(o.PrimaryKey())

    assert len(keys) == 2

    ret = clt.List(
        model.WorldKindIdentity, options.In("external.name", [keys[0], keys[1]])
    )

    assert len(ret) == 2

    for k in keys:
        ret = clt.List(model.WorldKindIdentity, options.In("external.name", [k]))

        assert len(ret) == 1
        assert ret[0].PrimaryKey() == k


def test_list_and_filter_by_nonexistent_props():
    try:
        clt.List(
            model.WorldKindIdentity,
            options.Eq("metadata.askdjhasd", "asdsadas"),
        )
        assert False
    except Exception as e:
        log.info("expected error: {}".format(str(e)))


def test_cannot_list_specific_object():
    try:
        clt.List(model.WorldIdentity(worldName))
        assert False
    except Exception as e:
        log.info("expected error: {}".format(str(e)))


def test_cannot_list_specific_nonexistent_object():
    try:
        clt.List(model.WorldIdentity("akjhdsjkhdaskjhdaskj"))
        assert False
    except Exception as e:
        log.info("expected error: {}".format(str(e)))


def test_list_and_eq_filter():
    # ret = clt.List(model.WorldKindIdentity)
    # for r in ret:
    #     log.info("object {}".format(utils.pps(r.ToJson())))

    ret = clt.List(model.WorldKindIdentity, options.Eq("external.name", worldName))

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, model.World)
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription
    global world_id
    world_id = world.Metadata().Identity()


def test_list_and_filter_by_id():
    ret = clt.List(
        model.WorldKindIdentity, options.Eq("metadata.identity", str(world_id))
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, model.World)
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription


def test_list_and_filter_by_nonexistent_id():
    ret = clt.List(
        model.WorldKindIdentity, options.Eq("metadata.identity", "asdasdasd")
    )

    assert ret is not None
    assert len(ret) == 0


def test_metadata_updates():
    # create a new world
    name = "test_metadata_updates"
    world = model.WorldFactory()
    world.External().SetName(name)

    # log.debug(">> creating world: {}".format(name))

    ret = clt.Create(world)
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
    ret = clt.Update(model.WorldIdentity(name), world)

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
    ret = clt.Get(model.WorldIdentity(name))
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

    err = None
    ret33 = None
    try:
        ret33 = clt.Update(model.WorldIdentity(name), world)
    except Exception as e:
        err = e
        log.info("expected error: {}".format(str(e)))
    assert err is not None
    assert ret33 is None
    assert str(err) == constants.ErrObjectIdentityMismatch

    newName = "test_metadata_updates22"
    ret.External().SetName(newName)
    ret.External().SetDescription("test_metadata_updates2222")
    ret = clt.Update(meta_id2, ret)

    # check the created time must be the same
    ct3 = ret.Metadata().Created()
    assert ct3 is not None
    assert ct3 == ct
    assert ret.Metadata().Revision() == 3

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


def test_datetime_property_type():
    name = "test_datetime_property_type"
    world = model.WorldFactory()
    world.External().SetName(name)
    dt = datetime.now()
    world.External().SetDate(dt)

    assert world.External().Date() == dt

    ret = clt.Create(world)
    assert ret is not None

    ndt = datetime.now()
    world.External().SetDate(ndt)
    ret = clt.Update(world.Metadata().Identity(), world)

    assert ret is not None

    # check the updated time
    rdt = ret.External().Date()
    assert rdt is not None
    assert rdt > dt

    # do a get and check the times
    ret = clt.Get(model.WorldIdentity(name))
    assert ret is not None

    # check the updated time
    rdt2 = ret.External().Date()
    assert rdt2 is not None
    assert rdt2 > dt
    assert rdt2 == ndt


def test_weird_characters():
    world = model.WorldFactory()
    world.External().SetName("test_weird_characters")
    world.External().SetAlive(True)
    world.External().SetCounter(123)
    desc = "a's gone to $ with a # then did a ` WHERE an IN''SERT INTO'"
    world.External().SetDescription(desc)
    ret = clt.Create(world)
    assert ret is not None

    ret = clt.Get(model.WorldIdentity("test_weird_characters"))
    assert ret is not None
    assert ret.External().Description() == desc

    # list and filter
    ret = clt.List(model.WorldKindIdentity, options.Eq("external.description", desc))

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, model.World)
    assert world.External().Name() == "test_weird_characters"
    assert world.External().Description() == desc


def test_list_and_filter_by_types():
    ret = clt.List(model.WorldKindIdentity, options.Eq("external.counter", 123))

    assert ret is not None
    assert len(ret) == 1

    ret = clt.List(model.WorldKindIdentity, options.Eq("external.alive", True))

    assert ret is not None
    assert len(ret) == 1


def test_list_and_filter_and_sort():
    ret = clt.List(model.WorldKindIdentity)
    total_length = len(ret)
    for r in ret:
        r.External().SetAlive(True)
        clt.Update(r.Metadata().Identity(), r)

    ret[0].External().SetAlive(False)
    clt.Update(ret[0].Metadata().Identity(), ret[0])

    ret = clt.List(
        model.WorldKindIdentity,
        options.Eq("external.alive", True),
        options.Order("external.name"),
    )

    assert ret is not None
    assert len(ret) == total_length - 1

    world = ret[0]
    # abc is not alive so the next one is anotherWorldName
    assert world.External().Name() == anotherWorldName

    ret = clt.List(
        model.WorldKindIdentity,
        options.Eq("external.alive", True),
        options.Order("external.name", False),
    )

    assert ret is not None
    assert len(ret) == total_length - 1

    world = ret[0]
    # abc is not alive so the next one is anotherWorldName
    assert world.External().Name() != anotherWorldName


def test_list_and_map_of_struct():
    world = model.WorldFactory()
    world.External().SetName("test_list_and_map_of_struct")

    nested = model.NestedWorldFactory()
    nested.SetCounter(123)
    nested.SetAlive(True)

    world.Internal().SetList([nested])
    world.Internal().SetMap({"nested": nested})

    d = world.Internal().Map()
    assert d["nested"].Counter() == 123
    l = world.Internal().List()
    assert l[0].Counter() == 123

    ret = clt.Create(world)
    assert ret is not None
    d = ret.Internal().Map()
    assert d["nested"].Counter() == 123
    l = ret.Internal().List()
    assert l[0].Counter() == 123

    ret = clt.Get(model.WorldIdentity("test_list_and_map_of_struct"))
    assert ret is not None

    d = ret.Internal().Map()
    assert d["nested"].Counter() == 123
    assert d["nested"].Alive()

    l = ret.Internal().List()
    assert l[0].Counter() == 123
    assert l[0].Alive()


def test_list_and_not_eq_filter():
    ret = clt.List(model.WorldKindIdentity)
    total_length = len(ret)

    ret = clt.List(
        model.WorldKindIdentity, options.Not(options.Eq("external.name", worldName))
    )

    assert ret is not None
    assert len(ret) == total_length - 1

    for w in ret:
        assert w.External().Name() != worldName


def test_list_and_lt_gt_filter():
    ret = clt.List(model.WorldKindIdentity)
    total_length = len(ret)
    i = 0
    for r in ret:
        r.External().SetCounter(i)
        clt.Update(r.Metadata().Identity(), r)
        i += 10

    half = 10 * total_length // 2

    ret = clt.List(model.WorldKindIdentity, options.Lt("external.counter", half))

    assert ret is not None
    for r in ret:
        assert r.External().Counter() < half

    ret = clt.List(model.WorldKindIdentity, options.Gt("external.counter", half))

    assert ret is not None
    for r in ret:
        assert r.External().Counter() > half

    ret = clt.List(
        model.WorldKindIdentity, options.Not(options.Lt("external.counter", half))
    )

    assert ret is not None
    for r in ret:
        assert r.External().Counter() >= half

    ret = clt.List(
        model.WorldKindIdentity, options.Not(options.Gt("external.counter", half))
    )

    assert ret is not None
    for r in ret:
        assert r.External().Counter() <= half

    ret = clt.List(
        model.WorldKindIdentity, options.Not(options.Lte("external.counter", half))
    )

    assert ret is not None
    for r in ret:
        assert r.External().Counter() > half

    ret = clt.List(
        model.WorldKindIdentity, options.Not(options.Gte("external.counter", half))
    )

    assert ret is not None
    for r in ret:
        assert r.External().Counter() < half

    ret = clt.List(model.WorldKindIdentity, options.Lte("external.counter", half))

    assert ret is not None
    for r in ret:
        assert r.External().Counter() <= half

    ret = clt.List(model.WorldKindIdentity, options.Gte("external.counter", half))

    assert ret is not None
    for r in ret:
        assert r.External().Counter() >= half


def test_list_and_in_int_filter():
    ret = clt.List(
        model.WorldKindIdentity, options.In("external.counter", [10, 20, 30, 40])
    )

    assert ret is not None
    assert len(ret) == 4

    ret = clt.List(
        model.WorldKindIdentity,
        options.Not(options.In("external.counter", [10, 20, 30, 40])),
    )

    assert ret is not None
    assert len(ret) == 2

    for r in ret:
        assert r.External().Counter() not in [10, 20, 30, 40]


def test_list_and_AND_filter():
    ret = clt.List(
        model.WorldKindIdentity, options.In("external.counter", [20, 30, 40, 50])
    )

    alive_count = 0
    for r in ret:
        if r.External().Alive():
            alive_count += 1

    ret = clt.List(
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

    ret = clt.List(
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


def test_list_and_OR_filter():
    ret = clt.List(
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

    ret = clt.List(
        model.WorldKindIdentity,
        options.Or(
            options.In("external.counter", not_alive_counters),
            options.Eq("external.alive", True),
        ),
    )

    assert ret is not None
    assert len(ret) == total_length

    ret = clt.List(
        model.WorldKindIdentity,
        options.Or(
            options.Not(options.In("external.counter", not_alive_counters)),
            options.Eq("external.alive", True),
        ),
    )

    assert ret is not None
    assert len(ret) == alive_count


def test_delete_filtered():
    ret = clt.List(model.WorldKindIdentity, options.Eq("external.alive", True))
    assert ret is not None
    alive_count = len(ret)
    assert alive_count > 0

    clt.Delete(model.WorldKindIdentity, options.Eq("external.alive", True))

    ret = clt.List(model.WorldKindIdentity)
    assert ret is not None
    assert len(ret) > 0
    for r in ret:
        assert r.External().Alive() == False


def test_sql_injection():
    # try to add a sql injection into a list query
    ret = clt.List(model.WorldKindIdentity, options.Eq("external.name", "'; DROP TABLE Objects; --"))
    assert ret is not None
    assert len(ret) == 0

    # try to add a sql injection into a naming property
    world = model.WorldFactory()
    world.External().SetName("', '', ''); DROP TABLE Objects; --")
    world.External().SetCounter(1)
    errored = False
    try:
        clt.Create(world)
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
    clt.Create(world)

    ret = clt.List(model.WorldKindIdentity, options.Eq("external.name", "sqlinjector"))
    assert ret[0].External().Description() == desc
    ret = clt.Get(model.WorldIdentity(name), options.Eq("external.name", "sqlinjector"))
    assert ret.External().Description() == desc
    
    ret.External().SetName("', '', ''); DROP TABLE Objects; --")
    errored = False
    try:
        clt.Update(ret.Metadata().Identity(), ret)
    except Exception as ex:
        log.info("Caught exception: {}".format(ex))
        errored = True
    
    assert errored

def test_performance():
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
        clt.Create(world)
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
        clt.Update(o.Metadata().Identity(), o)
        t22 = time.time()

        # append milliseconds it took for a single create
        graph_update[i] = t22 - t11
        i += 1
    
    tu2 = time.time()

    tl1 = time.time()
    log.info("Listing {} objects".format(NUMBER_OF_OBJECTS))
    clt.List(model.WorldKindIdentity)
    tl2 = time.time()

    tlh1 = time.time()
    log.info("Listing {} objects".format(NUMBER_OF_OBJECTS // 2))
    clt.List(model.WorldKindIdentity, options.Eq("external.alive", True))
    tlh2 = time.time()

    tg1 = time.time()
    graph_get = [0.0] * NUMBER_OF_OBJECTS
    log.info("Getting {} objects".format(NUMBER_OF_OBJECTS))
    for i in range(NUMBER_OF_OBJECTS):
        tgg1 = time.time()
        clt.Get(model.WorldIdentity("world-{}".format(i)))
        tgg2 = time.time()
        graph_get[i] = tgg2 - tgg1

    tg2 = time.time()

    td1 = time.time()
    graph_del = [0.0] * NUMBER_OF_OBJECTS
    log.info("Deleting {} objects".format(NUMBER_OF_OBJECTS))
    for i in range(NUMBER_OF_OBJECTS):
        tgg1 = time.time()
        clt.Delete(model.WorldIdentity("world-{}".format(i)))
        tgg2 = time.time()
        graph_del[i] = tgg2 - tgg1

    td2 = time.time()

    for i in range(NUMBER_OF_OBJECTS):
        world = model.WorldFactory()
        world.External().SetName("world-{}".format(i))
        world.External().SetCounter(1000)
        world.External().SetAlive(i % 2 == 0)
        clt.Create(world)
    
    tdd1 = time.time()
    clt.Delete(model.WorldKindIdentity, options.Eq("external.counter", 1000))
    tdd2 = time.time()

    ret = clt.List(model.WorldKindIdentity)
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

    # with info logs
    # Performance results: 10000 objects
    # Create: 	    5.962012052536011s
    # Update: 		7.063429117202759s
    # List Half:   	0.2144460678100586s
    # List: 		0. 41225194931030273s
    # Get:		    0.9138858318328857s
    # Delete: 		4.72649621963501s

    # with no logs
    # Create: 		5.244661092758179s
    # Update: 		6.249370098114014s
    # List Half:	0.21255111694335938s
    # List: 		0.40752696990966797s
    # Get:		    0.6312203407287598s
    # Delete: 		3.8235106468200684s
