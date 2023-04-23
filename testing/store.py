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
        ret, err = clt.List(model.WorldKindIdentity())
        assert err == None
        for r in ret:
            err = clt.Delete(r.Metadata().Identity())
            assert err == None

        ret, err = clt.List(model.SecondWorldKindIdentity())
        assert err == None
        for r in ret:
            err = clt.Delete(r.Metadata().Identity())
            assert err == None

        ret, _ = clt.List(model.SecondWorldKindIdentity())
        assert len(ret) == 0
        ret, _ = clt.List(model.WorldKindIdentity())
        assert len(ret) == 0

        # ret, err = clt.List(model.ThirdWorldKindIdentity())
        # assert err == None
        # for r in ret:
        #     err = clt.Delete(r.Metadata().Identity())
        #     assert err == None

    def test_list_empty_lists():
        ret, err = clt.list(model.WorldKindIdentity())
        assert err is None
        assert ret is not None
        assert len(ret) == 0

    def test_post_objects():
        w = model.WorldFactory()
        w.External().SetName("abc")
        ret, err = clt.create(w)
        assert err is None
        assert ret is not None
        assert len(ret.Metadata().Identity()) != 0

    def test_list_single_object():
        ret, err = clt.list(model.WorldKindIdentity())
        assert err is None
        assert ret is not None
        assert len(ret) == 1
        world = ret[0]
        assert world.External().Name() == "abc"

    def test_post_other_objects():
        w = model.SecondWorldFactory()
        w.External().SetName("abc")
        ret, err = clt.Create(w)
        assert err == None
        assert ret != None
        assert len(ret.Metadata().Identity()) != 0
        ret, err = clt.Get(ret.Metadata().Identity())
        assert err == None
        assert ret != None
        w = ret
        assert w != None
        ret, err = clt.Get(model.SecondWorldIdentity("abc"))
        assert err == None
        assert ret != None
        w = ret
        assert w != None

    def test_get_objects():
        ret, err = clt.Get(model.WorldIdentity("abc"))
        assert err == None
        assert ret != None
        assert len(ret.Metadata().Identity()) != 0
        world = ret
        assert world != None

    def test_can_not_double_post_objects():
        w = model.WorldFactory()

        w.External().SetName("abc")

        ret, err = clt.Create(w)

        assert err is not None
        assert ret is None

    def test_can_put_objects():
        w = model.WorldFactory()

        w.External().SetName("abc")
        w.External().SetDescription("def")

        ret, err = clt.Update(
                              model.WorldIdentity("abc"),
                              w)

        assert err is None
        assert ret is not None

        world = ret
        assert world is not None
        assert world.External().Description() == "def"

    def test_can_put_change_naming_props():
        w = model.WorldFactory()

        w.External().SetName("def")

        ret, err = clt.Update(
                              model.WorldIdentity("abc"), w)
        assert err is None
        assert ret is not None

        world = ret
        assert world is not None
        assert world.External().Name() == "def"

        ret, err = clt.Get(
                           model.WorldIdentity("abc"))
        assert err is not None
        assert ret is None

    def test_can_put_objects_by_id():
        ret, err = clt.Get(
                           model.WorldIdentity("def"))
        assert err is None
        assert ret is not None

        world = ret
        assert world is not None
        world.External().SetDescription("zxc")

        log.info(utils.pp(world))

        ret, err = clt.Update(
                              world.Metadata().Identity(), world)

        log.info(utils.pp(ret))

        assert err is None
        assert ret is not None

        world = ret
        assert world is not None
        assert world.External().Description() == "zxc"

    def test_cannot_put_nonexistent_objects():
        world = model.WorldFactory()
        assert world is not None
        world.External().SetName("zxcxzcxz")

        ret, err = clt.Update(model.WorldIdentity("zcxzcxzc"), world)
        assert err is not None
        assert ret is None

    def test_cannot_put_nonexistent_objects_by_id():
        world = model.WorldFactory()
        world.External().SetName("zxcxzcxz")

        ret, err = clt.Update(world.Metadata().Identity(), world)
        assert err is not None
        assert ret is None

    def test_cannot_put_objects_of_wrong_type():
        world = model.SecondWorldFactory()
        world.External().SetName("zxcxzcxz")

        ret, err = clt.Update(model.WorldIdentity("qwe"), world)
        assert err is not None
        assert ret is None

    def test_can_get_objects():
        ret, err = clt.Get(model.WorldIdentity("def"))
        assert err is None
        assert ret is not None

        world = ret
        assert world is not None

    def test_can_get_objects_by_id():
        ret, err = clt.Get(model.WorldIdentity("def"))
        assert err is None
        assert ret is not None

        world = ret
        assert world is not None

        ret, err = clt.Get(world.Metadata().Identity())
        assert err is None
        assert ret is not None

        world = ret
        assert world is not None

    def test_cannot_get_nonexistent_objects():
        ret, err = clt.Get(model.WorldIdentity("zxcxzczx"))
        assert err is not None
        assert ret is None

    def test_cannot_get_nonexistent_objects_by_id():
        ret, err = clt.Get(store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
        assert err is not None
        assert ret is None

    def test_can_delete_objects():
        w = model.WorldFactory()
        w.External().SetName("tobedeleted")

        ret, err = clt.Create(w)
        assert err is None
        assert ret is not None

        err = clt.Delete(model.WorldIdentity(w.External().Name()))
        assert err is None

        ret, err = clt.Get(model.WorldIdentity(w.External().Name()))
        assert err is not None
        assert ret is None

    def test_can_delete_objects_by_id():
        w = model.WorldFactory()
        w.External().SetName("tobedeleted")

        ret, err = clt.Create(w)
        assert err is None
        assert ret is not None
        w = ret

        err = clt.Delete(w.Metadata().Identity())
        assert err is None

        ret, err = clt.Get(w.Metadata().Identity())
        assert err is not None
        assert ret is None

    def test_delete_nonexistent_objects():
        err = clt.Delete(model.WorldIdentity("akjsdhsajkhdaskjh"))
        assert err is not None

    def test_delete_nonexistent_objects_by_id():
        err = clt.Delete(store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
        assert err is not None

    def test_get_nil_identity():
        _, err = clt.Get("")
        assert err is not None

    def test_create_nil_object():
        _, err = clt.Create(None)
        assert err is not None

    def test_put_nil_identity():
        _, err = clt.Update("", model.WorldFactory())
        assert err is not None

    def test_put_nil_object():
        _, err = clt.Update(model.WorldIdentity("qwe"), None)
        assert err is not None

    def test_delete_nil_identity():
        err = clt.Delete("")
        assert err is not None

    def test_create_multiple_objects():
        ret, err = clt.list(model.WorldKindIdentity())
        assert err is None

        for r in ret:
            err = clt.delete(r.Metadata().Identity())
            assert err is None

        world = model.WorldFactory()
        world.External().SetName(worldName)
        world.External().SetDescription(worldDescription)

        world2 = model.WorldFactory()
        world2.External().SetName(anotherWorldName)
        world2.External().SetDescription(newWorldDescription)

        _, err = clt.create(world)
        assert err is None
        _, err = clt.create(world2)
        assert err is None

        world3 = model.SecondWorldFactory()
        world3.External().SetName(anotherWorldName)
        world3.External().SetDescription(newWorldDescription)

        _, err = clt.create(world3)
        assert err is None

    def test_can_list_multiple_objects(self):
        ret, err = clt.List(
            model.WorldKindIdentity())

        self.assertIsNone(err)
        self.assertIsNotNone(ret)
        self.assertEqual(len(ret), 2)

        ret.sort(key=lambda r: r.External().Name())

        world = ret[0]
        self.assertEqual(world.External().Name(), worldName)
        self.assertEqual(world.External().Description(), worldDescription)

        world2 = ret[1]
        self.assertEqual(world2.External().Name(), anotherWorldName)
        self.assertEqual(world2.External().Description(), newWorldDescription)

    def test_can_list_and_sort_multiple_objects(self):
        ret, err = clt.List(
            model.WorldKindIdentity(),
            options.OrderBy("external.name"))

        self.assertIsNone(err)
        self.assertIsNotNone(ret)
        self.assertEqual(len(ret), 2)

        world = ret[0]
        self.assertEqual(world.External().Name(), worldName)
        self.assertEqual(world.External().Description(), worldDescription)

        world2 = ret[1]
        self.assertEqual(world2.External().Name(), anotherWorldName)
        self.assertEqual(world2.External().Description(), newWorldDescription)

        ret, err = clt.List(
            model.WorldKindIdentity(),
            options.OrderBy("external.name"),
            options.OrderDescending())

        self.assertIsNone(err)
        self.assertIsNotNone(ret)
        self.assertEqual(len(ret), 2)

        world = ret[1]
        world2 = ret[0]
        self.assertEqual(world.External().Name(), worldName)
        self.assertEqual(world2.External().Name(), anotherWorldName)

    def test_list_and_paginate_multiple_objects():
        ret, err = clt.list(
            
            model.WorldKindIdentity(),
            options.OrderBy("external.name"),
            options.PageSize(1)
        )

        assert err is None
        assert ret is not None
        assert len(ret) == 1

        world = ret[0]
        assert world.External().Name() == worldName
        assert world.External().Description() == worldDescription

        ret, err = clt.list(
            
            model.WorldKindIdentity(),
            options.OrderBy("external.name"),
            options.PageSize(1),
            options.PageOffset(1)
        )

        assert err is None
        assert ret is not None
        assert len(ret) == 1

        world = ret[0]
        assert world.External().Name() == anotherWorldName

        ret, err = clt.list(
            
            model.WorldKindIdentity(),
            options.OrderBy("external.name"),
            options.PageOffset(1),
            options.PageSize(1000)
        )

        assert err is None
        assert ret is not None
        assert len(ret) == 1

        world = ret[0]
        assert world.External().Name() == anotherWorldName

    def test_list_and_filter_by_primary_key():
        ret, err = clt.List(
            model.WorldKindIdentity())

        assert err is None

        keys = []
        for o in ret:
            keys.append(o.PrimaryKey())

        assert len(keys) == 2

        ret, err = clt.List(
            model.WorldKindIdentity(),
            options.KeyFilter(keys[0], keys[1]))

        assert err is None
        assert len(ret) == 2

        for k in keys:
            ret, err = clt.List(
                model.WorldKindIdentity(),
                options.KeyFilter(k))

            assert err is None
            assert len(ret) == 1
            assert ret[0].PrimaryKey() == k

    def test_list_and_filter_by_nonexistent_props():
        ret, err = clt.List(
            
            model.WorldKindIdentity(),
            options.PropFilter("metadata.askdjhasd", "asdsadas"))

        assert err is not None
        assert ret is None

    def test_cannot_list_specific_object():
        ret, err = clt.List(
            model.WorldIdentity(worldName))

        assert ret is None
        assert err is not None

    def test_cannot_list_specific_nonexistent_object():
        ret, err = clt.List(
            model.WorldIdentity("akjhdsjkhdaskjhdaskj"))

        assert ret is None
        assert err is not None

    world_id = ""

    def test_list_and_filter():
        ret, err = clt.List(
            model.WorldKindIdentity(),
            options.PropFilter("external.name", worldName)
        )

        assert err is None
        assert ret is not None
        assert len(ret) == 1

        world = ret[0]
        assert isinstance(world, model.World)
        assert world.External().Name() == worldName
        assert world.External().Description() == worldDescription
        global world_id
        world_id = world.Metadata().Identity()

    def test_list_and_filter_by_id():
        ret, err = clt.List(
            model.WorldKindIdentity(),
            options.PropFilter("metadata.identity", str(world_id))
        )

        assert err is None
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
