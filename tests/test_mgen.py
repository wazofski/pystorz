from config import globals

from datetime import datetime
from pystorz.mgen.generator import Generate

import logging

log = logging.getLogger(__name__)

globals.logger_config()


def test_mgen_can_generate():
    # ensure empty directory before generating
    import os, shutil

    generated_model_path = "generated"
    if os.path.exists(generated_model_path):
        shutil.rmtree(generated_model_path)

    Generate(globals.TEST_MODEL_PATH)


def test_generated_model():
    from generated import model

    world = model.WorldFactory()

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
    assert world.Metadata().Kind() == model.WorldKind

    # Test deserialization
    world.External().Nested().SetCounter(10)
    world.External().Nested().SetAlive(True)
    world.External().Nested().SetAnotherDescription("qwe")
    world.External().SetName("abc")
    world.Internal().SetDescription("qwe")
    world.Internal().SetList([model.NestedWorldFactory(), model.NestedWorldFactory()])

    world.Internal().SetMap(
        {
            "a": model.NestedWorldFactory(),
            "b": model.NestedWorldFactory(),
        }
    )

    world.Internal().Map()["a"].SetL1([False, False, True])


def test_serialization():
    from generated import model

    world = model.WorldFactory()
    world.External().SetName("abc")
    world.Internal().SetDescription("qwe")
    world.Internal().SetList([model.NestedWorldFactory(), model.NestedWorldFactory()])

    world.Internal().SetMap(
        {
            "a": model.NestedWorldFactory(),
            "b": model.NestedWorldFactory(),
        }
    )

    world.External().Nested().SetCounter(10)
    world.External().Nested().SetAlive(True)
    world.External().Nested().SetAnotherDescription("qwe")

    data = world.ToJson()

    newWorld = model.WorldFactory()
    newWorld.FromJson(data)

    assert newWorld.External().Nested().Alive() is True
    assert newWorld.External().Nested().Counter() == 10
    assert newWorld.External().Name() == "abc"
    assert newWorld.Internal().Description() == "qwe"
    assert len(newWorld.Internal().List()) == 2
    data2 = newWorld.ToJson()
    assert data == data2


def test_schema():
    from generated import model

    world = model.WorldFactory()

    schema = model.Schema()
    obj = schema.ObjectForKind(str(world.Metadata().Kind()))
    obj.External().SetName("abc")
    assert obj is not None

    anotherWorld = obj.Clone()
    assert anotherWorld is not None
    assert anotherWorld.Metadata().Kind() == world.Metadata().Kind()
    assert anotherWorld.External().Name() == obj.External().Name()


def test_cloning():
    from generated import model

    world = model.WorldFactory()

    world.External().Nested().SetCounter(10)
    world.External().Nested().SetAlive(True)
    world.External().Nested().SetAnotherDescription("qwe")
    world.External().SetName("abc")
    world.Internal().SetDescription("qwe")
    world.Internal().SetList([model.NestedWorldFactory(), model.NestedWorldFactory()])

    world.Internal().SetMap(
        {
            "a": model.NestedWorldFactory(),
            "b": model.NestedWorldFactory(),
        }
    )

    world.Internal().Map()["a"].SetL1([False, False, True])

    newWorld = world.Clone()
    assert newWorld.External().Nested().Alive() is True
    assert newWorld.External().Nested().Counter() == 10
    assert newWorld.External().Nested().AnotherDescription() == "qwe"
    assert newWorld.External().Name() == "abc"
    assert newWorld.Internal().Description() == "qwe"
    assert len(newWorld.Internal().List()) == 2


def test_datetime_property_type():
    from generated import model

    world = model.WorldFactory()
    world.External().SetName(test_datetime_property_type)
    dt = datetime.now()
    world.External().SetDate(dt)

    assert world.External().Date() == dt
