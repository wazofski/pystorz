import logging

from datetime import datetime
from pystorz.internal import constants
from pystorz.store import store

log = logging.getLogger(__name__)

from pystorz.store import options


class MetaStore(store.Store):
    def __init__(self, schema: store.SchemaHolder, data: store.Store):
        self.Schema = schema
        self.Store = data

    def Create(self, obj: store.Object, *opt: options.CreateOption) -> store.Object:
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info("create {}".format(
            obj.Metadata().Kind()))

        original = self.Schema.ObjectForKind(obj.Metadata().Kind())
        if original is None:
            raise Exception(constants.ErrInvalidPath)

        obj.Metadata().SetIdentity(store.ObjectIdentityFactory())
        obj.Metadata().SetCreated(datetime.now())
        obj.Metadata().SetUpdated(obj.Metadata().Created())
        obj.Metadata().SetRevision(1)

        return self.Store.Create(original, *opt)

    def Update(
        self,
        identity: store.ObjectIdentity,
        obj: store.Object,
        *opt: options.UpdateOption,
    ) -> store.Object:
        if obj is None:
            return constants.ErrObjectNil

        log.info("update {}".format(identity))

        original = self.Store.Get(identity)
        
        obj.Metadata().SetKind(original.Metadata().Kind())
        obj.Metadata().SetIdentity(original.Metadata().Identity())
        obj.Metadata().SetCreated(original.Metadata().Created())
        obj.Metadata().SetUpdated(datetime.now())
        obj.Metadata().SetRevision(original.Metadata().Revision() + 1)
        
        return self.Store.Update(identity, obj, *opt)

    def Delete(self, identity: store.ObjectIdentity, *opt: options.DeleteOption):
        log.info("delete {}".format(identity))
        return self.Store.Delete(identity, *opt)

    def Get(
        self, identity: store.ObjectIdentity, *opt: options.GetOption
    ) -> store.Object:
        log.info("get {}".format(identity))
        return self.Store.Get(identity, *opt)

    def List(
        self, identity: store.ObjectIdentity, *opt: options.ListOption
    ) -> store.ObjectList:
        log.info("list {}".format(identity))
        return self.Store.List(identity, *opt)
