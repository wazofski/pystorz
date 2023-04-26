import json
from datetime import datetime
from pystorz.store import store, utils


class Meta:
    def Kind(self) -> str:
        pass

    def Identity(self) -> store.ObjectIdentity:
        pass

    def Created(self) -> datetime:
        pass

    def Updated(self) -> datetime:
        pass

    def Revision(self) -> int:
        pass

    def ToJson(self) -> str:
        pass

    def FromDict(self, d: dict) -> None:
        pass

    def ToDict(self) -> str:
        pass


class MetaSetter:
    def SetKind(self, kind: str) -> None:
        pass

    def SetIdentity(self, identity: store.ObjectIdentity) -> None:
        pass

    def SetCreated(self, created: datetime) -> None:
        pass

    def SetUpdated(self, updated: datetime) -> None:
        pass

    def SetRevision(self, revision: int) -> None:
        pass


# class MetaHolder:
#     def metadata(self) -> Meta:
#         pass


class metaWrapper(Meta, MetaSetter):
    def __init__(self, kind):
        self.revision_ = 0
        self.kind_ = kind
        self.identity_ = store.ObjectIdentityFactory()
        self.created_ = ""
        self.updated_ = ""

    def Kind(self) -> str:
        return self.kind_

    def Created(self) -> datetime:
        return utils.datetime_parse(self.created_)

    def Updated(self) -> datetime:
        return utils.datetime_parse(self.updated_)

    def Identity(self) -> store.ObjectIdentity:
        return self.identity_

    def Revision(self) -> int:
        return self.revision_

    def SetKind(self, kind: str) -> None:
        self.kind_ = kind

    def SetIdentity(self, identity: store.ObjectIdentity) -> None:
        self.identity_ = identity

    def SetCreated(self, created: datetime) -> None:
        self.created_ = utils.datetime_string(created)

    def SetUpdated(self, updated: datetime) -> None:
        self.updated_ = utils.datetime_string(updated)

    def SetRevision(self, revision: int) -> None:
        self.revision_ = revision

    def ToJson(self) -> str:
        return json.dumps(self.ToDict())

    def ToDict(self) -> str:
        return {
            "kind": self.Kind(),
            "identity": str(self.Identity()),
            "created": self.created_,
            "updated": self.updated_,
            "revision": self.revision_,
        }

    def FromDict(self, d: dict) -> None:
        self.SetKind(d["kind"])
        self.SetIdentity(store.ObjectIdentityFactory())
        self.Identity().FromString(d["identity"])
        self.created_ = d["created"]
        self.updated_ = d["updated"]
        self.revision_ = d["revision"]


def MetaFactory(kind: str) -> Meta:
    return metaWrapper(kind)
    