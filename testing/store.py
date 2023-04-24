import logging
from store import options, store, utils

log = logging.getLogger(__name__)


def common_test_suite(clt):
    from generated import model

    worldName = "c137zxczx"
    anotherWorldName = "j19zeta7 qweqw"
    worldDescription = "zxkjhajkshdas world of argo"
    newWorldDescription = "is only beoaoqwiewioqu"

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
            err = e

        assert err is not None
        log.info("expected err: {}".format(err))
        assert ret is None

    def test_can_put_objects():
        w = model.WorldFactory()

        w.External().SetName("abc")
        w.External().SetDescription("def")

        ret = clt.Update(
            model.WorldIdentity("abc"),
            w)

        assert ret is not None

        world = ret
        assert world is not None
        assert world.External().Description() == "def"

    def test_can_put_change_naming_props():
        w = model.WorldFactory()

        w.External().SetName("def")

        ret = clt.Update(
            model.WorldIdentity("abc"), w)

        assert ret is not None

        world = ret
        assert world is not None
        assert world.External().Name() == "def"

        try:
            ret = None
            ret = clt.Get(model.WorldIdentity("abc"))
        except Exception as e:
            err = e

        assert err is not None
        log.info("expected err: {}".format(err))

        assert ret is None

    def test_can_put_objects_by_id():
        ret = clt.Get(
            model.WorldIdentity("def"))

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
        log.info("expected err: {}".format(err))
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
        log.info("expected err: {}".format(err))

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
        log.info("expected err: {}".format(err))

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
        log.info("expected err: {}".format(err))

        assert ret is None

    def test_cannot_get_nonexistent_objects_by_id():
        err = None
        try:
            ret = None
            ret = clt.Get(store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
        except Exception as e:
            err = e

        assert err is not None
        log.info("expected err: {}".format(err))

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
        log.info("expected err: {}".format(err))

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
        log.info("expected err: {}".format(err))

        assert ret is None

    def test_delete_nonexistent_objects():
        err = None
        try:
            clt.Delete(model.WorldIdentity("akjsdhsajkhdaskjh"))
        except Exception as e:
            err = e

        assert err is not None
        log.info("expected err: {}".format(err))

    def test_delete_nonexistent_objects_by_id():
        err = None
        try:
            clt.Delete(store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
        except Exception as e:
            err = e

        assert err is not None
        log.info("expected err: {}".format(err))

    def test_get_nil_identity():
        err = None
        try:
            clt.Get("")
        except Exception as e:
            err = e

        assert err is not None
        log.info("expected err: {}".format(err))

    def test_create_nil_object():
        err = None
        try:
            clt.Create(None)
        except Exception as e:
            err = e

        assert err is not None
        log.info("expected err: {}".format(err))

    def test_put_nil_identity():
        err = None
        try:
            clt.Update("", model.WorldFactory())
        except Exception as e:
            err = e

        assert err is not None
        log.info("expected err: {}".format(err))

    def test_put_nil_object():
        err = None
        try:
            clt.Update(model.WorldIdentity("qwe"), None)
        except Exception as e:
            err = e

        assert err is not None
        log.info("expected err: {}".format(err))

    def test_delete_nil_identity():
        err = None
        try:
            clt.Delete("")
        except Exception as e:
            err = e

        assert err is not None
        log.info("expected err: {}".format(err))

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
        ret = clt.List(
            model.WorldKindIdentity)

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
        ret = clt.List(
            model.WorldKindIdentity,
            options.OrderBy("external.name"))

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
            options.OrderDescending())

        assert ret is not None
        assert len(ret) == 2

        world = ret[1]
        world2 = ret[0]
        assert world.External().Name() == worldName
        assert world2.External().Name() == anotherWorldName

    def test_list_and_paginate_multiple_objects():
        ret = clt.List(

            model.WorldKindIdentity,
            options.OrderBy("external.name"),
            options.PageSize(1)
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
            options.PageOffset(1)
        )

        assert ret is not None
        assert len(ret) == 1

        world = ret[0]
        assert world.External().Name() == anotherWorldName

        ret = clt.List(

            model.WorldKindIdentity,
            options.OrderBy("external.name"),
            options.PageOffset(1),
            options.PageSize(1000)
        )

        assert ret is not None
        assert len(ret) == 1

        world = ret[0]
        assert world.External().Name() == anotherWorldName

    def test_list_and_filter_by_primary_key():
        ret = clt.List(
            model.WorldKindIdentity)

        keys = []
        for o in ret:
            keys.append(o.PrimaryKey())

        assert len(keys) == 2

        ret = clt.List(
            model.WorldKindIdentity,
            options.KeyFilter(keys[0], keys[1]))

        assert len(ret) == 2

        for k in keys:
            ret = clt.List(
                model.WorldKindIdentity,
                options.KeyFilter(k))

            assert len(ret) == 1
            assert ret[0].PrimaryKey() == k

    def test_list_and_filter_by_nonexistent_props():
        ret = clt.List(
            model.WorldKindIdentity,
            options.PropFilter("metadata.askdjhasd", "asdsadas"))

        assert ret is None

    def test_cannot_list_specific_object():
        ret = clt.List(
            model.WorldIdentity(worldName))

        assert ret is None

    def test_cannot_list_specific_nonexistent_object():
        ret = clt.List(
            model.WorldIdentity("akjhdsjkhdaskjhdaskj"))

        assert ret is None

    world_id = ""

    def test_list_and_filter():
        ret = clt.List(
            model.WorldKindIdentity,
            options.PropFilter("external.name", worldName)
        )

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
            model.WorldKindIdentity,
            options.PropFilter("metadata.identity", str(world_id))
        )

        assert ret is not None
        assert len(ret) == 1

        world = ret[0]
        assert isinstance(world, model.World)
        assert world.External().Name() == worldName
        assert world.External().Description() == worldDescription

    log.info("Running common test suite using %s", clt)
    test_clear_everything()
    test_list_empty_lists()
    test_post_objects()
    test_list_single_object()
    test_post_other_objects()
    test_get_objects()
    test_can_not_double_post_objects()
    test_can_put_objects()
    test_can_put_change_naming_props()
    test_can_put_objects_by_id()
    test_cannot_put_nonexistent_objects()
    test_cannot_put_nonexistent_objects_by_id()
    test_cannot_put_objects_of_wrong_type()
    test_can_get_objects()
    test_can_get_objects_by_id()
    test_cannot_get_nonexistent_objects()
    test_cannot_get_nonexistent_objects_by_id()
    test_can_delete_objects()
    test_can_delete_objects_by_id()
    test_delete_nonexistent_objects()
    test_delete_nonexistent_objects_by_id()
    test_get_nil_identity()
    test_create_nil_object()
    test_put_nil_identity()
    test_put_nil_object()
    test_delete_nil_identity()
    test_create_multiple_objects()
    test_can_list_multiple_objects()
    test_can_list_and_sort_multiple_objects()
    test_list_and_paginate_multiple_objects()
    test_list_and_filter_by_primary_key()
    test_list_and_filter_by_nonexistent_props()
    test_cannot_list_specific_object()
    test_cannot_list_specific_nonexistent_object()
    test_list_and_filter()
    test_list_and_filter_by_id()
