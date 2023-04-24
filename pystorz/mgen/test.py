from pystorz.store import utils

def test_mgen():
    from generated.model import WorldFactory, WorldKind, Schema, NestedWorldFactory
    
    world = WorldFactory()

    # Test factory method
    assert world is not None
    assert world.External() is not None
    assert world.Internal() is not None

    # Test setters and getters
    world.External().SetName("abc")
    assert world.External().Name() == "abc"

    world.External().Nested().SetAlive(True)
    assert world.External().Nested().Alive() is True

    world.External().Nested().SetCounter(10)
    assert world.External().Nested().Counter() == 10

    world.Internal().SetDescription("qwe")
    assert world.Internal().Description() == "qwe"

    # Test metadata
    assert world.Metadata().Kind() == WorldKind

    # Test deserialization
    world.External().Nested().SetCounter(10)
    world.External().Nested().SetAlive(True)
    world.External().Nested().SetAnotherDescription("qwe")
    world.External().SetName("abc")
    world.Internal().SetDescription("qwe")
    world.Internal().SetList([NestedWorldFactory(), NestedWorldFactory()])

    world.Internal().SetMap({
        "a": NestedWorldFactory(),
        "b": NestedWorldFactory(),
    })

    world.Internal().Map()["a"].SetL1([False, False, True])

    data = world.ToJson()
    # print(utils.pps(data))
    
    newWorld = WorldFactory()
    newWorld.FromJson(data)
    
    # print(utils.pps(newWorld.ToJson()))

    assert newWorld.External().Nested().Alive() is True
    assert newWorld.External().Nested().Counter() == 10
    assert newWorld.External().Name() == "abc"
    assert newWorld.Internal().Description() == "qwe"
    assert len(newWorld.Internal().List()) == 2
    data2 = newWorld.ToJson()
    assert data == data2

    # Test schema
    schema = Schema()
    obj = schema.ObjectForKind(str(world.Metadata().Kind()))
    assert obj is not None
    anotherWorld = obj.Clone()
    assert anotherWorld is not None

    # Test cloning
    world.External().Nested().SetCounter(10)
    world.External().Nested().SetAlive(True)
    world.External().Nested().SetAnotherDescription("qwe")
    world.External().SetName("abc")
    world.Internal().SetDescription("qwe")
    world.Internal().SetList([NestedWorldFactory(), NestedWorldFactory()])

    world.Internal().SetMap({
        "a": NestedWorldFactory(),
        "b": NestedWorldFactory(),
    })

    world.Internal().Map()["a"].SetL1([False, False, True])

    newWorld = world.Clone()
    assert newWorld.External().Nested().Alive() is True
    assert newWorld.External().Nested().Counter() == 10
    assert newWorld.External().Nested().AnotherDescription() == "qwe"
    assert newWorld.External().Name() == "abc"
    assert newWorld.Internal().Description() == "qwe"
    assert len(newWorld.Internal().List()) == 2
