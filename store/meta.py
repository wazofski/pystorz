from store import store

class Meta:
    def kind(self) -> str:
        pass

    def identity(self) -> store.ObjectIdentity:
        pass

    def created(self) -> str:
        pass

    def updated(self) -> str:
        pass

class MetaSetter:
    def set_kind(self, kind: str) -> None:
        pass

    def set_identity(self, identity: store.ObjectIdentity) -> None:
        pass

    def set_created(self, created: str) -> None:
        pass

    def set_updated(self, updated: str) -> None:
        pass

class MetaHolder:
    def metadata(self) -> Meta:
        pass

class metaWrapper(Meta, MetaSetter):
    def __init__(self):
        self.kind_ = None
        self.identity_ = None
        self.created_ = None
        self.updated_ = None

    def kind(self) -> str:
        return self.kind_

    def created(self) -> str:
        return self.created_

    def updated(self) -> str:
        return self.updated_

    def identity(self) -> store.ObjectIdentity:
        return self.identity_

    def set_kind(self, kind: str) -> None:
        self.kind_ = kind

    def set_identity(self, identity: store.ObjectIdentity) -> None:
        self.identity_ = identity

    def set_created(self, created: str) -> None:
        self.created_ = created

    def set_updated(self, updated: str) -> None:
        self.updated_ = updated

def MetaFactory(kind: str) -> Meta:
    emptyIdentity = store.ObjectIdentityFactory()
    
    mw = metaWrapper()
    mw.set_kind(kind)
    mw.set_identity(emptyIdentity)
    mw.set_created("")
    mw.set_updated("")

    return mw
