import pytest
import logging

log = logging.getLogger(__name__)

from config import globals

globals.logger_config()


from pystorz.handler.store import HandlerStore
from pystorz.memory.memory import MemoryStore
from pystorz.meta.store import MetaStore
from pystorz.store import options
from generated import model



def base_store():
    return MetaStore(MemoryStore(model.Schema()))


def test_create_callback_modifies_object():
    def create_cb(obj, store):
        # change description before persisting
        obj.External().SetDescription("modified-by-cb")

    store = HandlerStore(base_store(), handlers={
                         model.WorldKind: {"create": create_cb}})

    w = model.WorldFactory()
    w.External().SetName("cbcreate")

    ret = store.Create(w)
    assert ret is not None

    got = store.Get(model.WorldIdentity("cbcreate"))
    assert got.External().Description() == "modified-by-cb"


def test_create_callback_abort():
    def create_cb(obj, store):
        raise Exception("fail-cb")

    store = HandlerStore(base_store(), handlers={
                         model.WorldKind: {"create": create_cb}})

    w = model.WorldFactory()
    w.External().SetName("cb-fail")

    with pytest.raises(Exception) as ei:
        store.Create(w)

    assert "fail-cb" in str(ei.value)


def test_update_callback_modifies_object():
    # no-op handler for create
    store = HandlerStore(base_store(), handlers={})

    w = model.WorldFactory()
    w.External().SetName("cbupdate")
    store.Create(w)

    def update_cb(obj, store):
        obj.External().SetDescription("updated-by-cb")

    # install update handler on inner handler store
    store._handlers = {model.WorldKind: {"update": update_cb}}

    # perform update
    existing = store.Get(model.WorldIdentity("cbupdate"))
    existing.External().SetDescription("client-set")
    store.Update(existing.Metadata().Identity(), existing)

    got = store.Get(model.WorldIdentity("cbupdate"))
    assert got.External().Description() == "updated-by-cb"


def test_delete_callback_called():
    called = {"count": 0}

    def delete_cb(obj, store):
        called["count"] += 1

    store = HandlerStore(
        base_store(), handlers={
            model.WorldKind: {"delete": delete_cb}})

    w = model.WorldFactory()
    w.External().SetName("cbdelete")
    store.Create(w)

    store.Delete(model.WorldIdentity("cbdelete"))

    assert called["count"] == 1


def test_get_and_list_do_not_invoke_callbacks():
    # create store without handlers, add two objects
    store = HandlerStore(base_store(), handlers={})

    a = model.WorldFactory()
    a.External().SetName("g1")
    b = model.WorldFactory()
    b.External().SetName("g2")

    store.Create(a)
    store.Create(b)

    # now install handlers that would raise if called
    def raising_cb(obj, s):
        raise Exception("should-not-be-called")

    store._handlers = {model.WorldKind: {"create": raising_cb, "update": raising_cb, "delete": raising_cb}}

    # Get and List should not trigger create/update/delete handlers
    got = store.Get(model.WorldIdentity("g1"))
    assert got is not None

    lst = store.List(model.WorldKindIdentity)
    assert len(lst) == 2


def test_create_callback_returns_replacement():
    def create_cb(obj, s):
        new = model.WorldFactory()
        new.External().SetName("repl")
        return new

    store = HandlerStore(base_store(), handlers={model.WorldKind: {"create": create_cb}})

    orig = model.WorldFactory()
    orig.External().SetName("orig")

    store.Create(orig)

    # original should not exist, replacement should
    with pytest.raises(Exception):
        store.Get(model.WorldIdentity("orig"))

    got = store.Get(model.WorldIdentity("repl"))
    assert got.External().Name() == "repl"


def test_create_callback_abort():
    def create_cb(obj, s):
        raise Exception("create-abort")

    store = HandlerStore(base_store(), handlers={model.WorldKind: {"create": create_cb}})

    w = model.WorldFactory()
    w.External().SetName("cba")

    with pytest.raises(Exception) as ei:
        store.Create(w)

    assert "create-abort" in str(ei.value)


def test_update_callback_modifies_and_returns_replacement():
    store = HandlerStore(base_store(), handlers={})

    w = model.WorldFactory()
    w.External().SetName("upd1")
    w.External().SetDescription("initial")
    store.Create(w)

    # handler that modifies in-place
    def update_cb_inplace(obj, s):
        obj.External().SetDescription("inplace")

    store._handlers = {model.WorldKind: {"update": update_cb_inplace}}

    existing = store.Get(model.WorldIdentity("upd1"))
    existing.External().SetDescription("client")
    store.Update(existing.Metadata().Identity(), existing)

    got = store.Get(model.WorldIdentity("upd1"))
    assert got.External().Description() == "inplace"

    # handler that returns replacement
    def update_cb_replace(obj, s):
        r = model.WorldFactory()
        r.External().SetName("upd1")
        r.External().SetDescription("replaced")
        return r

    store._handlers = {model.WorldKind: {"update": update_cb_replace}}

    existing = store.Get(model.WorldIdentity("upd1"))
    existing.External().SetDescription("client2")
    store.Update(existing.Metadata().Identity(), existing)

    got = store.Get(model.WorldIdentity("upd1"))
    assert got.External().Description() == "replaced"


def test_update_callback_abort():
    store = HandlerStore(base_store(), handlers={})

    w = model.WorldFactory()
    w.External().SetName("upd-abort")
    w.External().SetDescription("initial")
    store.Create(w)

    def update_cb(obj, s):
        raise Exception("update-fail")

    store._handlers = {model.WorldKind: {"update": update_cb}}

    existing = store.Get(model.WorldIdentity("upd-abort"))
    existing.External().SetDescription("client")

    with pytest.raises(Exception):
        store.Update(existing.Metadata().Identity(), existing)

    # ensure not updated
    got = store.Get(model.WorldIdentity("upd-abort"))
    assert got.External().Description() == "initial"


def test_delete_callback_called_and_with_filter():
    calls = []

    def delete_cb(obj, s):
        calls.append(obj.External().Name())

    store = HandlerStore(base_store(), handlers={model.WorldKind: {"delete": delete_cb}})

    for n in ["a", "b", "c"]:
        w = model.WorldFactory()
        w.External().SetName(n)
        store.Create(w)

    # delete a and b via filter
    store.Delete(model.WorldKindIdentity, options.In("external.name", ["a", "b"]))

    assert set(calls) == {"a", "b"}
    # a and b removed, c still present
    with pytest.raises(Exception):
        store.Get(model.WorldIdentity("a"))
    with pytest.raises(Exception):
        store.Get(model.WorldIdentity("b"))
    got = store.Get(model.WorldIdentity("c"))
    assert got is not None


def test_delete_with_filter_callback_abort():
    def delete_cb(obj, s):
        if obj.External().Name() == "bad":
            raise Exception("bad-cb")

    store = HandlerStore(base_store(), handlers={model.WorldKind: {"delete": delete_cb}})

    for n in ["good", "bad", "other"]:
        w = model.WorldFactory()
        w.External().SetName(n)
        store.Create(w)

    # Attempt to delete all; callback will raise for "bad" and abort
    with pytest.raises(Exception):
        store.Delete(model.WorldKindIdentity, options.In("external.name", ["good", "bad", "other"]))

    # ensure none were deleted
    assert store.Get(model.WorldIdentity("good")) is not None
    assert store.Get(model.WorldIdentity("bad")) is not None
    assert store.Get(model.WorldIdentity("other")) is not None
