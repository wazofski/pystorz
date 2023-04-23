from store import store

class Meta:
    def Kind(self) -> str:
        pass

    def Identity(self) -> store.ObjectIdentity:
        pass

    def Created(self) -> str:
        pass

    def Updated(self) -> str:
        pass

class MetaSetter:
    def SetKind(self, kind: str) -> None:
        pass

    def SetIdentity(self, identity: store.ObjectIdentity) -> None:
        pass

    def SetCreated(self, created: str) -> None:
        pass

    def SetUpdated(self, updated: str) -> None:
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

    def Kind(self) -> str:
        return self.kind_

    def Created(self) -> str:
        return self.created_

    def Updated(self) -> str:
        return self.updated_

    def Identity(self) -> store.ObjectIdentity:
        return self.identity_

    def SetKind(self, kind: str) -> None:
        self.kind_ = kind

    def SetIdentity(self, identity: store.ObjectIdentity) -> None:
        self.identity_ = identity

    def SetCreated(self, created: str) -> None:
        self.created_ = created

    def SetUpdated(self, updated: str) -> None:
        self.updated_ = updated

def MetaFactory(kind: str) -> Meta:
    emptyIdentity = store.ObjectIdentityFactory()
    
    mw = metaWrapper()
    mw.SetKind(kind)
    mw.SetIdentity(emptyIdentity)
    mw.SetCreated("")
    mw.SetUpdated("")

    return mw
