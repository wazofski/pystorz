worldName = "c137zxczx"
anotherWorldName = "j19zeta7 qweqw"
worldDescription = "zxkjhajkshdas world of argo"
newWorldDescription = "is only beoaoqwiewioqu"


def test_clear_everything():
    ret, err = clt.List(ctx, generated.WorldKindIdentity())
    assert err == None
    for r in ret:
        err = clt.Delete(ctx, r.Metadata().Identity())
        assert err == None

    ret, err = clt.List(ctx, generated.SecondWorldKindIdentity())
    assert err == None
    for r in ret:
        err = clt.Delete(ctx, r.Metadata().Identity())
        assert err == None

    ret, _ = clt.List(ctx, generated.SecondWorldKindIdentity())
    assert len(ret) == 0
    ret, _ = clt.List(ctx, generated.WorldKindIdentity())
    assert len(ret) == 0

    # ret, err = clt.List(ctx, generated.ThirdWorldKindIdentity())
    # assert err == None
    # for r in ret:
    #     err = clt.Delete(ctx, r.Metadata().Identity())
    #     assert err == None


def test_list_empty_lists():
    ret, err = clt.list(ctx, generated.WorldKindIdentity())
    assert err is None
    assert ret is not None
    assert len(ret) == 0


def test_post_objects():
    w = generated.WorldFactory()
    w.External().SetName("abc")
    ret, err = clt.create(ctx, w)
    assert err is None
    assert ret is not None
    assert len(ret.Metadata().Identity()) != 0


def test_list_single_object():
    ret, err = clt.list(ctx, generated.WorldKindIdentity())
    assert err is None
    assert ret is not None
    assert len(ret) == 1
    world = ret[0]
    assert world.External().Name() == "abc"


def test_post_other_objects():
    w = generated.SecondWorldFactory()
    w.External().SetName("abc")
    ret, err = clt.Create(ctx, w)
    assert err == None
    assert ret != None
    assert len(ret.Metadata().Identity()) != 0
    ret, err = clt.Get(ctx, ret.Metadata().Identity())
    assert err == None
    assert ret != None
    w = ret.(generated.SecondWorld)
    assert w != None
    ret, err = clt.Get(ctx, generated.SecondWorldIdentity("abc"))
    assert err == None
    assert ret != None
    w = ret.(generated.SecondWorld)
    assert w != None


def test_get_objects():
    ret, err = clt.Get(ctx, generated.WorldIdentity("abc"))
    assert err == None
    assert ret != None
    assert len(ret.Metadata().Identity()) != 0
    world = ret.(generated.World)
    assert world != None


def test_can_not_double_post_objects():
    w = generated.WorldFactory()

    w.External().SetName("abc")

    ret, err = clt.Create(ctx, w)

    assert err is not None
    assert ret is None


def test_can_put_objects():
    w = generated.WorldFactory()

    w.External().SetName("abc")
    w.External().SetDescription("def")

    ret, err = clt.Update(ctx,
                          generated.WorldIdentity("abc"),
                          w)

    assert err is None
    assert ret is not None

    world = ret.(generated.World)
    assert world is not None
    assert world.External().Description() == "def"


def test_can_put_change_naming_props():
    w = generated.WorldFactory()

    w.External().SetName("def")

    ret, err = clt.Update(ctx,
                          generated.WorldIdentity("abc"), w)
    assert err is None
    assert ret is not None

    world = ret.(generated.World)
    assert world is not None
    assert world.External().Name() == "def"

    ret, err = clt.Get(ctx,
                       generated.WorldIdentity("abc"))
    assert err is not None
    assert ret is None


def test_can_put_objects_by_id():
    ret, err = clt.Get(ctx,
                       generated.WorldIdentity("def"))
    assert err is None
    assert ret is not None

    world = ret.(generated.World)
    assert world is not None
    world.External().SetDescription("zxc")

    log.info(utils.PP(world))

    ret, err = clt.Update(ctx,
                          world.Metadata().Identity(), world)

    log.info(utils.PP(ret))

    assert err is None
    assert ret is not None

    world = ret.(generated.World)
    assert world is not None
    assert world.External().Description() == "zxc"


def test_cannot_put_nonexistent_objects():
    world = generated.WorldFactory()
    assert world is not None
    world.External().SetName("zxcxzcxz")

    ret, err = clt.Update(ctx, generated.WorldIdentity("zcxzcxzc"), world)
    assert err is not None
    assert ret is None


def test_cannot_put_nonexistent_objects_by_id():
    world = generated.WorldFactory()
    world.External().SetName("zxcxzcxz")

    ret, err = clt.Update(ctx, world.Metadata().Identity(), world)
    assert err is not None
    assert ret is None


def test_cannot_put_objects_of_wrong_type():
    world = generated.SecondWorldFactory()
    world.External().SetName("zxcxzcxz")

    ret, err = clt.Update(ctx, generated.WorldIdentity("qwe"), world)
    assert err is not None
    assert ret is None


def test_can_get_objects():
    ret, err = clt.Get(ctx, generated.WorldIdentity("def"))
    assert err is None
    assert ret is not None

    world = ret.(generated.World)
    assert world is not None


def test_can_get_objects_by_id():
    ret, err = clt.Get(ctx, generated.WorldIdentity("def"))
    assert err is None
    assert ret is not None

    world = ret.(generated.World)
    assert world is not None

    ret, err = clt.Get(ctx, world.Metadata().Identity())
    assert err is None
    assert ret is not None

    world = ret.(generated.World)
    assert world is not None


def test_cannot_get_nonexistent_objects():
    ret, err = clt.Get(ctx, generated.WorldIdentity("zxcxzczx"))
    assert err is not None
    assert ret is None


def test_cannot_get_nonexistent_objects_by_id():
    ret, err = clt.Get(ctx, store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
    assert err is not None
    assert ret is None


def test_can_delete_objects():
    w = generated.WorldFactory()
    w.External().SetName("tobedeleted")

    ret, err = clt.Create(ctx, w)
    assert err is None
    assert ret is not None

    err = clt.Delete(ctx, generated.WorldIdentity(w.External().Name()))
    assert err is None

    ret, err = clt.Get(ctx, generated.WorldIdentity(w.External().Name()))
    assert err is not None
    assert ret is None


def test_can_delete_objects_by_id():
    w = generated.WorldFactory()
    w.External().SetName("tobedeleted")

    ret, err = clt.Create(ctx, w)
    assert err is None
    assert ret is not None
    w = ret

    err = clt.Delete(ctx, w.Metadata().Identity())
    assert err is None

    ret, err = clt.Get(ctx, w.Metadata().Identity())
    assert err is not None
    assert ret is None


def test_delete_nonexistent_objects():
    err = clt.Delete(ctx, generated.WorldIdentity("akjsdhsajkhdaskjh"))
    Expect(err).ToNot(BeNil())

def test_delete_nonexistent_objects_by_id():
    err = clt.Delete(ctx, store.ObjectIdentity("id/kjjakjjsadldkjalkdajs"))
    Expect(err).ToNot(BeNil())

def test_get_nil_identity():
    _, err = clt.Get(ctx, "")
    Expect(err).ToNot(BeNil())

def test_create_nil_object():
    _, err = clt.Create(ctx, None)
    Expect(err).ToNot(BeNil())

def test_put_nil_identity():
    _, err = clt.Update(ctx, "", generated.WorldFactory())
    Expect(err).ToNot(BeNil())

def test_put_nil_object():
    _, err = clt.Update(ctx, generated.WorldIdentity("qwe"), None)
    Expect(err).ToNot(BeNil())

def test_delete_nil_identity():
    err = clt.Delete(ctx, "")
    Expect(err).ToNot(BeNil())


def test_create_multiple_objects():
    ret, err = clt.list(ctx, generated.WorldKindIdentity())
    assert err is None

    for r in ret:
        err = clt.delete(ctx, r.Metadata().Identity())
        assert err is None

    world = generated.WorldFactory()
    world.External().SetName(worldName)
    world.External().SetDescription(worldDescription)

    world2 = generated.WorldFactory()
    world2.External().SetName(anotherWorldName)
    world2.External().SetDescription(newWorldDescription)

    _, err = clt.create(ctx, world)
    assert err is None
    _, err = clt.create(ctx, world2)
    assert err is None

    world3 = generated.SecondWorldFactory()
    world3.External().SetName(anotherWorldName)
    world3.External().SetDescription(newWorldDescription)

    _, err = clt.create(ctx, world3)
    assert err is None


def test_can_list_multiple_objects(self):
    ret, err = clt.List(
        ctx, generated.WorldKindIdentity())

    self.assertIsNone(err)
    self.assertIsNotNone(ret)
    self.assertEqual(len(ret), 2)

    ret.sort(key=lambda r: r.(generated.World).External().Name())

    world = ret[0].(generated.World)
    self.assertEqual(world.External().Name(), worldName)
    self.assertEqual(world.External().Description(), worldDescription)

    world2 = ret[1].(generated.World)
    self.assertEqual(world2.External().Name(), anotherWorldName)
    self.assertEqual(world2.External().Description(), newWorldDescription)


def test_can_list_and_sort_multiple_objects(self):
    ret, err = clt.List(
        ctx,
        generated.WorldKindIdentity(),
        options.OrderBy("external.name"))

    self.assertIsNone(err)
    self.assertIsNotNone(ret)
    self.assertEqual(len(ret), 2)

    world = ret[0].(generated.World)
    self.assertEqual(world.External().Name(), worldName)
    self.assertEqual(world.External().Description(), worldDescription)

    world2 = ret[1].(generated.World)
    self.assertEqual(world2.External().Name(), anotherWorldName)
    self.assertEqual(world2.External().Description(), newWorldDescription)

    ret, err = clt.List(
        ctx,
        generated.WorldKindIdentity(),
        options.OrderBy("external.name"),
        options.OrderDescending())

    self.assertIsNone(err)
    self.assertIsNotNone(ret)
    self.assertEqual(len(ret), 2)

    world = ret[1].(generated.World)
    world2 = ret[0].(generated.World)
    self.assertEqual(world.External().Name(), worldName)
    self.assertEqual(world2.External().Name(), anotherWorldName)


def test_list_and_paginate_multiple_objects():
    ret, err = clt.list(
        ctx,
        generated.WorldKindIdentity(),
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
        ctx,
        generated.WorldKindIdentity(),
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
        ctx,
        generated.WorldKindIdentity(),
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
        ctx, generated.WorldKindIdentity())

    assert err is None

    keys = []
    for o in ret:
        keys.append(o.PrimaryKey())

    assert len(keys) == 2

    ret, err = clt.List(
        ctx, generated.WorldKindIdentity(),
        options.KeyFilter(keys[0], keys[1]))

    assert err is None
    assert len(ret) == 2

    for k in keys:
        ret, err = clt.List(
            ctx, generated.WorldKindIdentity(),
            options.KeyFilter(k))

        assert err is None
        assert len(ret) == 1
        assert ret[0].PrimaryKey() == k

def test_list_and_filter_by_nonexistent_props():
    ret, err = clt.List(
        ctx,
        generated.WorldKindIdentity(),
        options.PropFilter("metadata.askdjhasd", "asdsadas"))

    assert err is not None
    assert ret is None

def test_cannot_list_specific_object():
    ret, err = clt.List(
        ctx, generated.WorldIdentity(worldName))

    assert ret is None
    assert err is not None

def test_cannot_list_specific_nonexistent_object():
    ret, err = clt.List(
        ctx, generated.WorldIdentity("akjhdsjkhdaskjhdaskj"))

    assert ret is None
    assert err is not None


world_id = ""

def test_list_and_filter():
    ret, err = clt.List(
        ctx,
        generated.WorldKindIdentity(),
        options.PropFilter("external.name", worldName)
    )

    assert err is None
    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, generated.World)
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription
    global world_id
    world_id = world.Metadata().Identity()

def test_list_and_filter_by_id():
    ret, err = clt.List(
        ctx, generated.WorldKindIdentity(),
        options.PropFilter("metadata.identity", str(world_id))
    )

    assert err is None
    assert ret is not None
    assert len(ret) == 1

    world = ret[0]
    assert isinstance(world, generated.World)
    assert world.External().Name() == worldName
    assert world.External().Description() == worldDescription
