import uuid
import json

from datetime import datetime
from pystorz.internal import constants
from pystorz.store import options


def datetime_parse(dtstr) -> datetime:
    return datetime.strptime(dtstr, constants.DATETIME_FORMAT)


def datetime_string(dt) -> str:
    return dt.strftime(constants.DATETIME_FORMAT)


class ObjectIdentity:
    def __init__(self, id: str):
        self.id_ = id

    def FromString(self, str):
        self.id_ = str

    def __str__(self) -> str:
        return self.id_

    def Path(self) -> str:
        if '/' in self.id_:
            tokens = self.id_.split('/')
            return f"{tokens[0].lower()}/{tokens[1]}"
        else:
            return f"id/{self}"

    def IsId(self) -> bool:
        return '/' not in self.id_

    def Type(self) -> str:
        return self.Path().split('/')[0]

    def Key(self) -> str:
        tokens = self.Path().split('/')
        if len(tokens) > 1:
            return tokens[1]
        else:
            return ""

    def __eq__(self, other):
        if isinstance(other, ObjectIdentity):
            return self.id_ == other.id_
        elif isinstance(other, str):
            return self.id_ == other

        return False

    def __hash__(self):
        return hash(self.id_)

    def __len__(self):
        return len(self.id_)


class Meta:
    def Kind(self) -> str:
        raise NotImplementedError()

    def Identity(self) -> ObjectIdentity:
        raise NotImplementedError()

    def Created(self) -> datetime:
        raise NotImplementedError()

    def Updated(self) -> datetime:
        raise NotImplementedError()

    def Revision(self) -> int:
        raise NotImplementedError()

    def ToJson(self) -> str:
        raise NotImplementedError()

    def FromDict(self, d: dict):
        raise NotImplementedError()

    def ToDict(self) -> str:
        raise NotImplementedError()


class MetaSetter:
    def SetKind(self, kind: str):
        raise NotImplementedError()

    def SetIdentity(self, identity: ObjectIdentity):
        raise NotImplementedError()

    def SetCreated(self, created: datetime):
        raise NotImplementedError()

    def SetUpdated(self, updated: datetime):
        raise NotImplementedError()

    def SetRevision(self, revision: int):
        raise NotImplementedError()


class _MetaWrapper(Meta, MetaSetter):
    def __init__(self, kind):
        self.revision_ = 0
        self.kind_ = kind
        self.identity_ = ObjectIdentityFactory()
        self.created_ = ""
        self.updated_ = ""

    def Kind(self) -> str:
        return self.kind_

    def Created(self) -> datetime:
        return datetime_parse(self.created_)

    def Updated(self) -> datetime:
        return datetime_parse(self.updated_)

    def Identity(self) -> ObjectIdentity:
        return self.identity_

    def Revision(self) -> int:
        return self.revision_

    def SetKind(self, kind: str) -> None:
        self.kind_ = kind

    def SetIdentity(self, identity: ObjectIdentity) -> None:
        self.identity_ = identity

    def SetCreated(self, created: datetime) -> None:
        self.created_ = datetime_string(created)

    def SetUpdated(self, updated: datetime) -> None:
        self.updated_ = datetime_string(updated)

    def SetRevision(self, revision: int) -> None:
        self.revision_ = revision

    def ToJson(self) -> str:
        return json.dumps(self.ToDict())

    def ToDict(self) -> dict:
        return {
            "kind": self.Kind(),
            "identity": str(self.Identity()),
            "created": self.created_,
            "updated": self.updated_,
            "revision": self.revision_,
        }

    def FromDict(self, d: dict) -> None:
        self.SetKind(d["kind"])
        self.SetIdentity(ObjectIdentityFactory())
        self.Identity().FromString(d["identity"])
        self.created_ = d["created"]
        self.updated_ = d["updated"]
        self.revision_ = d["revision"]


def MetaFactory(kind: str) -> Meta:
    return _MetaWrapper(kind)


class Object:

    def __init__(self):
        raise Exception("Object is an interface")

    def Metadata(self) -> Meta:
        raise Exception("Object is an interface")

    def Clone(self):
        raise Exception("Object is an interface")

    def ToJson(self) -> str:
        raise Exception("Object is an interface")

    def FromJson(self, jstr):
        raise Exception("Object is an interface")

    def FromDict(self, dict) -> Exception:
        raise Exception("Object is an interface")

    def ToDict(self) -> dict:
        raise Exception("Object is an interface")

    def PrimaryKey(self) -> str:
        raise Exception("Object is an interface")


class ExternalHolder(Object):
    def SetExternal(self, obj: object):
        pass

    def External(self) -> object:
        pass


class ObjectList(list[Object]):
    pass


def ObjectIdentityFactory() -> ObjectIdentity:
    id = str(uuid.uuid1())
    id = id.replace("-", "")

    return ObjectIdentity(id)


class Store:
    def Get(self, identity: ObjectIdentity, *options: options.GetOption) -> Object:
        raise Exception("Object is an interface")

    def List(self, identity: ObjectIdentity, *options: options.ListOption) -> ObjectList:
        raise Exception("Object is an interface")

    def Create(self, obj: Object, *options: options.CreateOption) -> Object:
        raise Exception("Object is an interface")

    def Update(self, identity: ObjectIdentity, obj: Object, *options: options.UpdateOption) -> Object:
        raise Exception("Object is an interface")

    def Delete(self, identity: ObjectIdentity, *options: options.DeleteOption):
        raise Exception("Object is an interface")


class SchemaHolder:
    def ObjectForKind(self, kind: str) -> Object:
        raise Exception("Object is an interface")

    def Types(self) -> list[str]:
        raise Exception("Object is an interface")


class StoreJsonDecoder(json.JSONDecoder):

    def __init__(self, schema: SchemaHolder):
        super().__init__(object_hook=self.object_hook)
        self.schema = schema

    def object_hook(self, dct):
        # find the class
        class_name = dct["meta"]["kind"]
        instance = self.schema.ObjectForKind(class_name)
        if instance is None:
            raise Exception(f"cannot find kind: {class_name}")

        return instance.FromJson(dct)
