import logging

from pystorz.internal import constants
from pystorz.store import store

log = logging.getLogger(__name__)

from pystorz.store import options


class InternalStore(store.Store):
    def __init__(self, schema: store.SchemaHolder, data: store.Store):
        self.Schema = schema
        self.Store = data

    def Create(self, obj: store.Object, *opt: options.CreateOption) -> store.Object:
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info("create {} {}".format(
            obj.Metadata().Kind(),
            obj.PrimaryKey()))

        original = self.Schema.ObjectForKind(obj.Metadata().Kind())
        if original is None:
            raise Exception(constants.ErrInvalidPath)

        if isinstance(original, store.ExternalHolder):
            original.SetExternal(obj.External())

        return self.Store.Create(original, *opt)

    def Update(
        self,
        identity: store.ObjectIdentity,
        obj: store.Object,
        *opt: options.UpdateOption,
    ) -> store.Object:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info("update {}".format(identity.Path()))

        original = self.Store.Get(identity)
        if isinstance(original, store.ExternalHolder):
            original.SetExternal(obj.External())

        if original.Metadata().Kind() != obj.Metadata().Kind():
            raise Exception(constants.ErrObjectIdentityMismatch)

        return self.Store.Update(identity, original, *opt)

    def Delete(self, identity: store.ObjectIdentity, *opt: options.DeleteOption):
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        log.info("delete {}".format(identity.Path()))
        return self.Store.Delete(identity, *opt)

    def Get(
        self, identity: store.ObjectIdentity, *opt: options.GetOption
    ) -> store.Object:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        log.info("get {}".format(identity.Path()))
        return self.Store.Get(identity, *opt)

    def List(
        self, identity: store.ObjectIdentity, *opt: options.ListOption
    ) -> store.ObjectList:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        log.info("list {}".format(identity.Path()))
        return self.Store.List(identity, *opt)
