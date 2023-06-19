import logging
from pystorz.store import store
from pystorz.store import options
from pystorz.internal import constants

log = logging.getLogger(__name__)


class RouteStore(store.Store):
    def __init__(self, mapping: dict, default=None):
        self.Default = default
        self.Mapping = {}

        for k, v in mapping.items():
            self.Mapping[k.lower().replace("/", "")] = v

    def Create(self, obj: store.Object, *opt: options.CreateOption) -> store.Object:
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info(f"create {obj.PrimaryKey()}")

        return self._getStore(obj.Metadata().Kind()).Create(obj, *opt)

    def Update(self, identity: store.ObjectIdentity, obj: store.Object, *opt: options.UpdateOption) -> store.Object:
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        log.info(f"update {identity.Path()}")

        return self._getStore(obj.Metadata().Kind()).Update(identity, obj, *opt)

    def Delete(self, identity: store.ObjectIdentity, *opt: options.DeleteOption):
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        
        log.info(f"delete {identity.Path()}")

        return self._getStore(identity.Type()).Delete(identity, *opt)

    def Get(self, identity: store.ObjectIdentity, *opt: options.GetOption) -> store.Object:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        
        log.info(f"get {identity.Path()}")

        return self._getStore(identity.Type()).Get(identity, *opt)

    def List(self, identity: store.ObjectIdentity, *opt: options.ListOption) -> store.ObjectList:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        log.info(f"list {identity.Type()}")

        return self._getStore(identity.Type()).List(identity, *opt)

    def _getStore(self, kind: str) -> store.Store:
        kind = kind.lower().replace("/", "")

        if kind in self.Mapping:
            return self.Mapping[kind]

        if self.Default is None:
            raise Exception(constants.ErrInvalidPath)

        log.debug(f"kind {kind} not found in mapping, using default store")
        return self.Default
