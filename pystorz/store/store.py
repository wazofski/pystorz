import uuid
import json


class Object:

    def __init__(self):
        raise Exception("Object is an interface")

    def Metadata(self):
        pass

    def Clone(self):
        pass

    def ToJson(self) -> str:
        pass

    def FromJson(self, jstr):
        pass

    def FromDict(self, dict) -> Exception:
        pass

    def ToDict(self) -> dict:
        pass

    def PrimaryKey(self) -> str:
        pass


class ExternalHolder(Object):
    def ExternalInternalSet(self, obj: object):
        pass

    def ExternalInternal(self) -> object:
        pass


class ObjectList(list[Object]):
    pass


class ObjectIdentity:
    def __init__(self, id: str):
        self.id_ = id

    def FromString(self, str) -> Exception:
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


def ObjectIdentityFactory() -> ObjectIdentity:
    id = str(uuid.uuid1())
    id = id.replace("-", "")
    
    return ObjectIdentity(id)


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

    def Types(self) -> list[str]:
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
