import uuid
import json
import logging
from typing import List



class Object:
    def MetaHolder(self):
        pass

    def Clone(self):
        pass

    def ToJson(self):
        pass
    
    def FromDict(self, dict) -> Exception:
        pass

    def PrimaryKey(self) -> str:
        pass


class ExternalHolder:
    def ExternalInternalSet(self, obj: object):
        pass

    def ExternalInternal(self) -> object:
        pass


class ObjectList(List[Object]):
    pass


class ObjectIdentity(str):
    pass


def ObjectIdentityFactory() -> ObjectIdentity:
    id = str(uuid.uuid1())
    id = id.replace("-", "")
    id = id[5:25]

    return ObjectIdentity(id)


def Path(self) -> str:
    if '/' in self:
        tokens = self.split('/')
        return f"{tokens[0].lower()}/{tokens[1]}"
    else:
        return f"id/{self}"


def Type(self) -> str:
    return Path(self).split('/')[0]


def Key(self) -> str:
    tokens = Path(self).split('/')
    if len(tokens) > 1:
        return tokens[1]
    else:
        return ""


class Store:
    def Get(self, identity: ObjectIdentity, *options) -> Object:
        pass

    def List(self, identity: ObjectIdentity, *options) -> ObjectList:
        pass

    def Create(self, obj: Object, *options) -> Object:
        pass

    def Delete(self, identity: ObjectIdentity, *options) -> Exception:
        pass

    def Update(self, identity: ObjectIdentity, obj: Object, *options) -> Object:
        pass


class SchemaHolder:
    def ObjectForKind(self, kind: str) -> Object:
        pass

    def Types(self) -> List[str]:
        pass


class Factory:
    def __call__(self, schema: SchemaHolder) -> Store:
        pass


def New(schema: SchemaHolder, factory: Factory) -> Store:
    return factory(schema)


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
