import logging

from pystorz.internal import constants
from pystorz.store import store

log = logging.getLogger(__name__)

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
            raise Exception(constants.ErrObjectNil)

        log.info("create {}".format(obj.PrimaryKey()))

        original = self.Schema.ObjectForKind(obj.Metadata().Kind())
        if original is None:
            raise Exception(constants.ErrInvalidPath)

        if isinstance(obj, store.ExternalHolder):
            original.ExternalInternalSet(obj.External())

        # ms = original.Metadata()
        # ms.SetIdentity(store.ObjectIdentityFactory())
        # ms.SetCreated(datetime.now())

        return self.Store.Create(original, *opt)

    def Update(
        self,
        identity: store.ObjectIdentity,
        obj: store.Object,
        *opt: options.UpdateOption,
    ) -> store.Object:
        if obj is None:
            return constants.ErrObjectNil

        log.info("update {}".format(identity.Path()))

        original = self.Store.Get(identity)
        if isinstance(obj, store.ExternalHolder):
            original.ExternalInternalSet(obj.External())

        # ms = original.Metadata()
        # ms.SetUpdated(datetime.now())
        return self.Store.Update(identity, original, *opt)

    def Delete(self, identity: store.ObjectIdentity, *opt: options.DeleteOption):
        log.info("delete {}".format(identity.Path()))
        return self.Store.Delete(identity, *opt)

    def Get(
        self, identity: store.ObjectIdentity, *opt: options.GetOption
    ) -> store.Object:
        log.info("get {}".format(identity.Path()))
        return self.Store.Get(identity, *opt)

    def List(
        self, identity: store.ObjectIdentity, *opt: options.ListOption
    ) -> store.ObjectList:
        log.info("list {}".format(identity.Type()))
        return self.Store.List(identity, *opt)
