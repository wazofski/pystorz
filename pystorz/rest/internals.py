import logging
from typing import Callable

from pystorz.internal import constants
from pystorz.store import store

log = logging.getLogger(__name__)

from datetime import datetime
from pystorz.store import options


class InternalStore:
    def __init__(self, schema: store.SchemaHolder, data: store.Store):
        self.Schema = schema
        self.Store = data


def internal_factory(schema: store.SchemaHolder, data: store.Store) -> store.Store:
    return InternalStore(schema, data)


class InternalStore(store.Store):
    def __init__(self, schema: store.SchemaHolder, data: store.Store):
        self.Schema = schema
        self.Store = data

    def Create(self, obj: store.Object, *opt: options.CreateOption) -> store.Object:
        if obj is None:
            return None, constants.ErrObjectNil

        log.info("create %s", obj.PrimaryKey())

        original = self.Schema.ObjectForKind(obj.Metadata().Kind())
        if original is None:
            return None, f"unknown kind {obj.Metadata().Kind()}"

        external_holder = (
            original.ExternalInternal()
            if isinstance(original, store.ExternalHolder)
            else None
        )
        obj_external_holder = (
            obj.ExternalInternal() if isinstance(obj, store.ExternalHolder) else None
        )
        if external_holder is not None and obj_external_holder is not None:
            external_holder.ExternalInternalSet(obj_external_holder.ExternalInternal())

        ms = original.Metadata()
        ms.SetIdentity(store.ObjectIdentityFactory())
        ms.SetCreated(datetime.now())

        return self.Store.Create(original, *opt)

    def Update(
        self,
        identity: store.ObjectIdentity,
        obj: store.Object,
        *opt: options.UpdateOption,
    ) -> store.Object:
        if obj is None:
            return None, constants.ErrObjectNil

        self.Log.info("update %s", identity.Path())

        original, err = self.Store.Get(identity)
        if err is not None:
            return None, err
        if original is None:
            return None, constants.ErrNoSuchObject

        external_holder = (
            original.ExternalInternal()
            if isinstance(original, store.ExternalHolder)
            else None
        )
        obj_external_holder = (
            obj.ExternalInternal() if isinstance(obj, store.ExternalHolder) else None
        )
        if external_holder is not None and obj_external_holder is not None:
            external_holder.ExternalInternalSet(obj_external_holder.ExternalInternal())

        ms = original.Metadata()
        ms.SetUpdated(datetime.now())

        return self.Store.Update(identity, original, *opt)

    def Delete(self, identity: store.ObjectIdentity, *opt: options.DeleteOption):
        log.info("delete %s", identity.Path())
        return self.Store.Delete(identity, *opt)

    def Get(
        self, identity: store.ObjectIdentity, *opt: options.GetOption
    ) -> store.Object:
        log.info("get %s", identity.Path())
        return self.Store.Get(identity, *opt)

    def List(
        self, identity: store.ObjectIdentity, *opt: options.ListOption
    ) -> store.ObjectList:
        log.info("list %s", identity.Type())
        return self.Store.List(identity, *opt)
