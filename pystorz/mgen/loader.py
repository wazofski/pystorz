import json
import yaml
import logging

from pystorz.mgen.utils import capitalize, decapitalize, yaml_files

log = logging.getLogger(__name__)
log.debug("loading loader.py...")


def jopp(obj):
    # json pretty print
    jstring = """JSON pretty print
""" + json.dumps(
        obj, indent=4, sort_keys=True
    )
    return jstring


class Model:
    def __init__(self, types=None):
        self.types = types or []


class Prop:
    def __init__(self, name, prop_type, json_str, default=""):
        self.name = name
        self.type = prop_type
        self.json = json_str
        self.default = default

    def IsMap(self):
        if len(self.type) < 3:
            return False

        return self.type[:3] == "map"

    def IsArray(self):
        if len(self.type) < 2:
            return False

        return self.type[:2] == "[]"

    def StrippedType(self):
        if self.IsMap():
            return "dict"
        if self.IsArray():
            return "list"
        if self.type == "string":
            return "str"
        return self.type

    def ComplexTypeValueDefault(self):
        return complexTypeValueDefault(self.type)

    def StrippedDefault(self):
        return typeDefault(self.StrippedType())


class Struct:
    def __init__(self, name, implements="", properties=[]):
        self.name = name
        self.implements = implements
        self.properties = properties


class Resource:
    def __init__(self, name, external=None, internal=None, primary_key=None):
        self.name = name
        self.external = external
        self.internal = internal
        self.primary_key = primary_key

    def IdentityPrefix(self):
        return self.name.lower()


def load_model(path: str):
    yamls = yaml_files(path)
    structs = []
    resources = []
    struct_cache = set()
    resource_cache = set()

    for y in yamls:
        model = read_model(y)

        # log.debug("model: {}".format(jopp(model)))

        for m in model["types"]:
            if m["kind"].lower() == "struct":
                if m["name"] in struct_cache:
                    raise Exception("duplicate struct: {}".format(m["name"]))
                struct_cache.add(m["name"])

                structs.append(Struct(m["name"], "", capitalize_props(m["properties"])))
                continue
            if m["kind"].lower() == "object":
                if m["name"] in resource_cache:
                    raise Exception("duplicate object: {}".format(m["name"]))
                resource_cache.add(m["name"])

                pkey = "metadata.identity"
                if "primarykey" in m:
                    pkey = m["primarykey"]
                pkey = make_prop_caller_string(pkey)

                ext = None
                if "external" in m:
                    ext = m["external"]
                intr = None
                if "internal" in m:
                    intr = m["internal"]

                resources.append(Resource(m["name"], ext, intr, pkey))
                continue

            raise Exception("unknown kind: {}".format(m["kind"]))

    errors = validate_model(structs, resources)
    if len(errors) > 0:
        raise Exception(
            """model validation failed:
    {}""".format(
                """
    """.join(
                    errors
                )
            )
        )

    return structs, resources


def validate_model(structs, resources):
    errors = []
    known_types = ["string", "int", "float", "bool", "datetime"]

    for s in structs:
        known_types.append(s.name)

    for s in structs:
        for p in s.properties:
            if p.IsArray():
                elem_type = p.type[2:]
                if elem_type not in known_types:
                    errors.append(
                        "struct {} property {}: unknown type: {}".format(
                            s.name, p.name, elem_type
                        )
                    )
                continue

            if p.IsMap():
                # map[int]string
                key_type = p.type[4:].split("]")[0]
                val_type = p.type[4:].split("]")[1]
                if key_type not in known_types:
                    errors.append(
                        "struct {} property {}: unknown type: {}".format(
                            s.name, p.name, elem_type
                        )
                    )
                if val_type not in known_types:
                    errors.append(
                        "struct {} property {}: unknown type: {}".format(
                            s.name, p.name, elem_type
                        )
                    )
                continue

            if p.type not in known_types:
                errors.append(
                    "struct {} property {}: unknown type: {}".format(
                        s.name, p.name, p.type
                    )
                )

    for r in resources:
        if r.external is None and r.internal is None:
            errors.append("resource {} has no internal and external".format(r.name))
            continue

        if r.external is not None:
            if r.external not in known_types:
                errors.append(
                    "resource {} external: unknown type: {}".format(r.name, r.external)
                )

        if r.internal is not None:
            if r.internal not in known_types:
                errors.append(
                    "resource {} internal: unknown type: {}".format(r.name, r.internal)
                )

    return errors


def read_model(path: str):
    log.debug(f"reading model from {path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data


def capitalize_props(l: list):
    res = []
    for p in l:
        res.append(
            Prop(
                capitalize(p["name"]),
                p["type"],
                decapitalize(p["name"]),
                # p.default
            )
        )
    return res


def make_prop_caller_string(pkey: str):
    tok = pkey.split(".")
    cap = []
    for t in tok:
        cap.append("{}()".format(capitalize(t)))

    return ".".join(cap)


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


def complexTypeValueDefault(tp: str) -> str:
    log.debug(f"typeValueDefault: {tp}")

    if tp.startswith("[]"):
        return typeDefault(tp[2:])

    if tp.startswith("map"):
        closing_bracket_index = tp.find("]")
        if closing_bracket_index == -1:
            raise Exception("invalid map type: {}".format(tp))

        return typeDefault(tp[closing_bracket_index + 1 :])

    raise Exception("unknown type: {}".format(tp))
