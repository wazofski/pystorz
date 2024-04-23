from pystorz.mgen.utils import capitalize


BASIC_TYPES = ["string", "int", "float", "bool", "datetime"]


def typeDefault(tp: str) -> str:
    if tp.startswith("list") or tp.startswith("[]"):
        return "list()"
        # return f"{tp} {{}}"
    if tp.startswith("dict") or tp.startswith("map"):
        return "dict()"
        # return f"make({tp})"

    if tp == "str" or tp == "string":
        return '""'

    if tp == "bool":
        return "False"

    if tp == "int":
        return "0"

    if tp == "float":
        return "0.0"

    if tp == "datetime":
        return '"0001-01-01T00:00:00.000000Z"'

    return f"{tp}Factory()"


class Property:
    def __init__(self, yaml):
        self.name = yaml["name"]
        self.type = yaml["type"]

    def Default(self):
        return typeDefault(self.type)

    def CapitalizedName(self):
        return capitalize(self.name)

    def IsMap(self):
        if len(self.type) < 3:
            return False

        return self.type[:3] == "map"

    def IsArray(self):
        if len(self.type) < 2:
            return False

        return self.type[:2] == "[]"

    def SubType(self):
        if self.IsMap() or self.IsArray():
            return self.type.split("]")[1]

        return self.type

    def IsComplexType(self):
        return self.SubType() not in BASIC_TYPES

    def StrippedType(self):
        if self.IsMap():
            return "dict"
        if self.IsArray():
            return "list"
        if self.type == "string":
            return "str"
        return self.type

    def ComplexTypeValueDefault(self):
        if self.type.startswith("[]"):
            return typeDefault(self.type[2:])

        if self.type.startswith("map"):
            closing_bracket_index = self.type.find("]")
            if closing_bracket_index == -1:
                raise Exception("invalid map type: {}".format(self.type))

            return typeDefault(self.type[closing_bracket_index + 1 :])

        raise Exception("unknown type: {}".format(self.type))

    def StrippedDefault(self):
        return typeDefault(self.StrippedType())


class Struct:
    def __init__(self, yaml):
        self.name = yaml["name"]
        self.properties = [Property(p) for p in yaml["properties"]]


class Resource:
    def __init__(self, yaml):
        self.name = yaml["name"]
        
        self.primary_key = "metadata.identity"
        if "primarykey" in yaml:
            self.primary_key = yaml["primarykey"]

        self.external = None
        if "external" in yaml:
            self.external = yaml["external"]
        
        self.internal = None
        if "internal" in yaml:
            self.internal = yaml["internal"]

    def PrimaryKeyFunctionCaller(self):
        tok = self.primary_key.split(".")
        return ".".join(["{}()".format(capitalize(t)) for t in tok])
    
    def IdentityPrefix(self):
        return self.name.lower()
