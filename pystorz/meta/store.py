from pystorz.store import options
import logging

from datetime import datetime
from pystorz.internal import constants
from pystorz.store import store

log = logging.getLogger(__name__)


class MetaStore(store.Store):
    def __init__(self, data: store.Store):
        self._Store = data

    def Create(self, obj: store.Object, *opt: options.CreateOption) -> store.Object:
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info("create {} {}".format(
            obj.Metadata().Kind(), obj.PrimaryKey()))

        meta = obj.Metadata()
        if isinstance(meta, store.MetaSetter):
            meta.SetIdentity(store.ObjectIdentityFactory())
            meta.SetCreated(datetime.now())
            meta.SetUpdated(obj.Metadata().Created())
            meta.SetRevision(1)

        return self._Store.Create(obj, *opt)

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

        original = self._Store.Get(identity)
        # if original.Metadata().Kind() != obj.Metadata().Kind():
        #     return constants.ErrObjectIdentityMismatch

        # obj.Metadata().SetKind(original.Metadata().Kind())
        meta = obj.Metadata()
        if isinstance(meta, store.MetaSetter):
            meta.SetIdentity(original.Metadata().Identity())
            meta.SetCreated(original.Metadata().Created())
            meta.SetUpdated(datetime.now())
            meta.SetRevision(original.Metadata().Revision() + 1)

        return self._Store.Update(identity, obj, *opt)

    def Delete(self, identity: store.ObjectIdentity, *opt: options.DeleteOption):
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        log.info("delete {}".format(identity.Path()))
        return self._Store.Delete(identity, *opt)

    def Get(
        self, identity: store.ObjectIdentity, *opt: options.GetOption
    ) -> store.Object:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        log.info("get {}".format(identity.Path()))
        return self._Store.Get(identity, *opt)

    def List(
        self, identity: store.ObjectIdentity, *opt: options.ListOption
    ) -> store.ObjectList:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        log.info("list {}".format(identity.Path()))
        return self._Store.List(identity, *opt)
