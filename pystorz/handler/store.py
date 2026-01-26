import logging
from typing import Callable, Dict

from pystorz.store import store, options
from pystorz.internal import constants

log = logging.getLogger(__name__)


class HandlerStore(store.Store):
    """A simple store wrapper that invokes user-provided callbacks for CRUD
    operations on a per-kind basis.

    Handlers format: { '<KindName>' : { 'create': func, 'update': func, 'delete': func } }
    Each callback is called with signature: callback(obj, store)
    - For Create/Update the callback may modify and/or return a replacement object.
    - If a callback raises an exception, the underlying store operation is not performed.
    """

    def __init__(self, inner: store.Store, handlers: Dict[str, Dict[str, Callable]] = {}):
        self._inner = inner
        self._handlers = handlers or {}

    def _get_handler(self, kind: str, op: str):
        if kind in self._handlers and op in self._handlers[kind]:
            return self._handlers[kind][op]
        lk = kind.lower()
        if lk in self._handlers and op in self._handlers[lk]:
            return self._handlers[lk][op]
        return None

    def Create(self, obj: store.Object, *opt: options.CreateOption) -> store.Object:
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        kind = obj.Metadata().Kind()
        cb = self._get_handler(kind, constants.ActionCreate)
        if cb:
            result = cb(obj, self)
            if result is not None:
                obj = result

        return self._inner.Create(obj, *opt)

    def Update(self, identity: store.ObjectIdentity, obj: store.Object, *opt: options.UpdateOption) -> store.Object:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        kind = obj.Metadata().Kind()
        cb = self._get_handler(kind, constants.ActionUpdate)
        if cb:
            result = cb(obj, self)
            if result is not None:
                obj = result

        return self._inner.Update(identity, obj, *opt)

    def Delete(self, identity: store.ObjectIdentity, *opt: options.DeleteOption):
        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        # If a filter is provided, obtain the list of objects that would be deleted
        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        # When filter is provided, List() will return the objects to delete.
        if copt.filter is not None:
            objs = self._inner.List(identity, *opt)
            # run callbacks for all and abort if any raises
            for o in objs:
                cb = self._get_handler(
                    o.Metadata().Kind(), constants.ActionDelete)
                if cb:
                    cb(o, self)

            # perform deletion per-object to be safe
            for o in objs:
                self._inner.Delete(o.Metadata().Identity())

            return

        # No filter: delete single object by identity
        # fetch object to pass to callback
        obj = self._inner.Get(identity)
        cb = self._get_handler(obj.Metadata().Kind(), constants.ActionDelete)
        if cb:
            cb(obj, self)

        return self._inner.Delete(identity, *opt)

    def Get(self, identity: store.ObjectIdentity, *opt: options.GetOption) -> store.Object:
        return self._inner.Get(identity, *opt)

    def List(self, identity: store.ObjectIdentity, *opt: options.ListOption) -> store.ObjectList:
        return self._inner.List(identity, *opt)


def HandlerStoreFactory(inner: store.Store, handlers: Dict[str, Dict[str, Callable]] | None = None):
    return HandlerStore(inner, handlers)
