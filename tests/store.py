import ast
import sys
import logging
import inspect

from datetime import datetime
from pystorz.store import options, store, utils
from pystorz.internal import constants
from generated import model

log = logging.getLogger(__name__)


# decorator for test functions
def test(fn):
    def wrapper(*args, **kwargs):
        try:
            fn(*args, **kwargs)
            print("********************* {} -> PASS".format(fn.__name__))
        except Exception as ex:
            print("********************* {} -> FAIL: {}".format(fn.__name__, str(ex)))
            raise ex

    return wrapper


def get_function_order():
    # Use ast to parse the source file and extract the function definitions
    source = open(__file__, "rt").read()
    module = ast.parse(source)

    functions = []
    for node in module.body:
        if isinstance(node, ast.FunctionDef):
            functions.append(node)

    # Sort the function definitions by their line numbers
    functions.sort(key=lambda f: f.lineno)

    # Print the functions in the order they appear in the source file
    res = []
    for function in functions:
        res.append(function.name)
    return res


def common_test_suite(store_to_use):
    global clt
    clt = store_to_use

    log.info("Running common test suite using %s", clt)

    to_run = dict()

    # find all functions inside this function with test decorator and run them
    for name, func in inspect.getmembers(sys.modules[__name__]):
        if not inspect.isfunction(func):
            continue

        # check if the function has the test decorator
        if name.startswith("test_"):
            to_run[name] = func
        # decorator_list = [d for d in reversed(inspect.getattr_static(func, "__decorators__", [])) if isinstance(d, test)]

        # decorator_list = inspect.getmembers(func.__class__, lambda x: isinstance(x, test))
        # if len(decorator_list) > 0:
        #     func()
        # if any(isinstance(d, test) for d in reversed(inspect.getattr_static(func, "__decorators__", []))):
        #     func()

    # run the functions in the order they appear in the source file
    for name in get_function_order():
        if name in to_run:
            to_run[name]()


clt = None
world_id = None
worldName = "c137zxczx"
anotherWorldName = "j19zeta7 qweqw"
worldDescription = "zxkjhajkshdas world of argo"
newWorldDescription = "is only beoaoqwiewioqu"


@test
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


@test
def test_list_empty_lists():
    ret = clt.List(model.WorldKindIdentity)

    assert ret is not None
    assert len(ret) == 0


@test
def test_post_objects():
    w = model.WorldFactory()
    w.External().SetName("abc")
    ret = clt.Create(w)

    assert ret is not None
    assert len(str(ret.Metadata().Identity())) != 0


@test
def test_list_single_object():
    ret = clt.List(model.WorldKindIdentity)

    assert ret is not None
    assert len(ret) == 1
    world = ret[0]
    assert world.External().Name() == "abc"


@test
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


@test
def test_get_objects():
    ret = clt.Get(model.WorldIdentity("abc"))

    assert ret != None
    assert len(str(ret.Metadata().Identity())) != 0
    world = ret
    assert world != None


@test
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


@test
def test_can_put_objects():
    w = model.WorldFactory()

    w.External().SetName("abc")
    w.External().SetDescription("def")

    ret = clt.Update(model.WorldIdentity("abc"), w)

    assert ret is not None

    world = ret
    assert world is not None
    assert world.External().Description() == "def"


@test
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


@test
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


@test
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


@test
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


@test
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


@test
def test_can_get_objects():
    ret = clt.Get(model.WorldIdentity("def"))

    assert ret is not None

    world = ret
    assert world is not None


@test
def test_can_get_objects_by_id():
    ret = clt.Get(model.WorldIdentity("def"))

    assert ret is not None

    world = ret
    assert world is not None

    ret = clt.Get(world.Metadata().Identity())

    assert ret is not None

    world = ret
    assert world is not None


@test
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


@test
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


@test
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


@test
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


@test
def test_delete_nonexistent_objects():
    err = None
    try:
        clt.Delete(model.WorldIdentity("akjsdhsajkhdaskjh"))
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


@test
def test_delete_nonexistent_objects_by_id():
    err = None
    try:
        clt.Delete(store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


@test
def test_get_nil_identity():
    err = None
    try:
        clt.Get("")
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


@test
def test_create_nil_object():
    err = None
    try:
        clt.Create(None)
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


@test
def test_put_nil_identity():
    err = None
    try:
        clt.Update("", model.WorldFactory())
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


@test
def test_put_nil_object():
    err = None
    try:
        clt.Update(model.WorldIdentity("qwe"), None)
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


@test
def test_delete_nil_identity():
    err = None
    try:
        clt.Delete("")
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


@test
def test_delete_empty_identity():
    err = None
    try:
        clt.Delete(model.WorldIdentity(""))
    except Exception as e:
        err = e

    assert err is not None
    log.info("expected error: {}".format(str(err)))


@test
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


@test
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


@test
def test_can_list_and_sort_multiple_objects():
    ret = clt.List(model.WorldKindIdentity, options.OrderBy("external.name"))

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
        options.OrderBy("external.name"),
        options.OrderDescending(),
    )

    assert ret is not None
    assert len(ret) == 2

    world = ret[1]
    world2 = ret[0]
    assert world.External().Name() == worldName
    assert world2.External().Name() == anotherWorldName


@test
def test_list_and_paginate_multiple_objects():
    ret = clt.List(
        model.WorldKindIdentity, options.OrderBy("external.name"), options.PageSize(1)
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription

    ret = clt.List(
        model.WorldKindIdentity,
        options.OrderBy("external.name"),
        options.PageSize(1),
        options.PageOffset(1),
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert world.External().Name() == anotherWorldName

    ret = clt.List(
        model.WorldKindIdentity,
        options.OrderBy("external.name"),
        options.PageOffset(1),
        options.PageSize(1000),
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert world.External().Name() == anotherWorldName


@test
def test_list_and_filter_by_primary_key():
    ret = clt.List(model.WorldKindIdentity)

    keys = []
    for o in ret:
        keys.append(o.PrimaryKey())

    assert len(keys) == 2

    ret = clt.List(model.WorldKindIdentity, options.KeyFilter(keys[0], keys[1]))

    assert len(ret) == 2

    for k in keys:
        ret = clt.List(model.WorldKindIdentity, options.KeyFilter(k))

        assert len(ret) == 1
        assert ret[0].PrimaryKey() == k


@test
def test_list_and_filter_by_nonexistent_props():
    try:
        clt.List(
            model.WorldKindIdentity,
            options.PropFilter("metadata.askdjhasd", "asdsadas"),
        )
        assert False
    except Exception as e:
        log.info("expected error: {}".format(str(e)))


@test
def test_cannot_list_specific_object():
    try:
        clt.List(model.WorldIdentity(worldName))
        assert False
    except Exception as e:
        log.info("expected error: {}".format(str(e)))


@test
def test_cannot_list_specific_nonexistent_object():
    try:
        clt.List(model.WorldIdentity("akjhdsjkhdaskjhdaskj"))
        assert False
    except Exception as e:
        log.info("expected error: {}".format(str(e)))


@test
def test_list_and_filter():
    # ret = clt.List(model.WorldKindIdentity)
    # for r in ret:
    #     log.info("object {}".format(utils.pps(r.ToJson())))

    ret = clt.List(
        model.WorldKindIdentity, options.PropFilter("external.name", worldName)
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, model.World)
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription
    global world_id
    world_id = world.Metadata().Identity()


@test
def test_list_and_filter_by_id():
    ret = clt.List(
        model.WorldKindIdentity, options.PropFilter("metadata.identity", str(world_id))
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, model.World)
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription


@test
def test_list_and_filter_by_nonexistent_id():
    ret = clt.List(
        model.WorldKindIdentity, options.PropFilter("metadata.identity", "asdasdasd")
    )

    assert ret is not None
    assert len(ret) == 0


@test
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


@test
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


@test
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
    ret = clt.List(
        model.WorldKindIdentity, options.PropFilter("external.description", desc)
    )

    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, model.World)
    assert world.External().Name() == "test_weird_characters"
    assert world.External().Description() == desc


@test
def test_list_and_filter_by_types():
    ret = clt.List(model.WorldKindIdentity,
                   options.PropFilter("external.counter", 123))

    assert ret is not None
    assert len(ret) == 1

    ret = clt.List(model.WorldKindIdentity,
                   options.PropFilter("external.alive", True))

    assert ret is not None
    assert len(ret) == 1
