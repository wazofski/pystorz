import json
import yaml
import logging

from mgen.utils import capitalize, decapitalize, yaml_files

log = logging.getLogger(__name__)
log.debug('loading loader.py...')


def jopp(obj):
    # json pretty print
    jstring = '''JSON pretty print
''' + json.dumps(obj, indent=4, sort_keys=True)
    return jstring


class Model:
    def __init__(self, types=None):
        self.types = types or []


class Prop:
    def __init__(self, name, prop_type, json_str, default=None):
        self.name = name
        self.type = prop_type
        self.json = json_str
        self.default = default


class Struct:
    def __init__(self, name, implements=None, properties=None):
        self.name = name
        self.implements = implements or []
        self.properties = properties or []


class Resource:
    def __init__(self, name, external=None, internal=None, primary_key=None):
        self.name = name
        self.external = external
        self.internal = internal
        self.primary_key = primary_key

    def IdentityPrefix(self):
        return self.Name.lower()


def load_model(path: str):
    yamls = yaml_files(path)
    structs = []
    resources = []

    for y in yamls:
        model = read_model(y)

        log.debug("model: {}".format(jopp(model)))

        for m in model["types"]:
            if m["kind"] == "Struct":
                structs.append(Struct(
                    m["name"],
                    capitalize_props(m["properties"])
                ))
                continue
            if m["kind"] == "Object":
                pkey = "metadata.identity"
                mpkey = m["primarykey"]
                if len(mpkey) > 0:
                    pkey = mpkey
                pkey = make_prop_caller_string(pkey)

                ext = None
                if "external" in m:
                    ext = m["external"]
                intr = None
                if "internal" in m:
                    intr = m["internal"]

                resources.append(Resource(
                    m["name"],
                    ext,
                    intr,
                    pkey))
                continue

    return structs, resources


def read_model(path: str):
    log.debug(f"reading model from {path}")
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data


def capitalize_props(l: list):
    res = []
    for p in l:
        res.append(Prop(
            capitalize(p['name']),
            decapitalize(p['name']),
            p['type'],
            # p.default
        ))
    return res


def make_prop_caller_string(pkey: str):
    tok = pkey.split(".")
    cap = []
    for t in tok:
        cap.append("{}".format(capitalize(t)))

    return ".".join(cap)
