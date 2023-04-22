import yaml
import logging
import string
import os

from mgen.utils import capitalize, decapitalize


log = logging.getLogger(__name__)


class Model:
    def __init__(self, types=None):
        self.types = types or []


class Prop:
    def __init__(self, name, prop_type, json_str, default):
        self.name = name
        self.type = prop_type
        self.json = json_str
        self.default = default


class Type:
    def __init__(self, name, kind=None, external=None, internal=None, primary_key=None, properties=None):
        self.name = name
        self.kind = kind
        self.external = external
        self.internal = internal
        self.primary_key = primary_key
        self.properties = properties or []


class Struct:
    def __init__(self, name, embeds=None, implements=None, properties=None):
        self.name = name
        self.embeds = embeds or []
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


def identity_prefix(resource):
    return resource.name.lower()


def read_model(path):
    log.info(f"reading model from {path}...")
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    types = []
    for t in data['types']:
        props = []
        for p in t.get('properties', []):
            prop = Prop(name=p['name'], prop_type=p['type'], json_str=p.get(
                'json', None), default=p.get('default', None))
            props.append(prop)
        type_obj = Type(name=t['name'], kind=t.get('kind', None), external=t.get('external', None),
                        internal=t.get('internal', None), primary_key=t.get('primarykey', None), properties=props)
        types.append(type_obj)
    return Model(types=types)


def capitalize_props(l):
    res = []
    for p in l:
        res.append(Prop(name=capitalize(p.name), json_str=decapitalize(
            p.name), prop_type=p.type, default=p.default))
    return res


def make_prop_caller_string(pkey):
    tok = pkey.split(".")
    cap = []
    for t in tok:
        cap.append(f"{capitalize(t)}()")
    return ".".join(cap)


def yaml_files(path):
    yamls = []
    for filename in os.listdir(path):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            yamls.append(os.path.join(path, filename))
    return yamls


def load_model(path):
    yamls = yaml_files(path)
    structs = []
    resources = []

    for y in yamls:
        log.info(f"Loading model from {y}...")

        model, err = read_model(y)
        if err is not None:
            log.fatal(err)

        for m in model['types']:
            if m['kind'] == 'Struct':
                structs.append(Struct(
                    name=m['name'],
                    props=capitalize_props(m['props'])
                ))
                continue
            if m['kind'] == 'Object':
                pkey = "metadata.identity"
                if len(m['pkey']) > 0:
                    pkey = m['pkey']
                pkey = make_prop_caller_string(pkey)

                resources.append(Resource(
                    name=m['name'],
                    external=m['external'],
                    internal=m['internal'],
                    primary_key=pkey,
                ))
                continue

    return structs, resources


def make_prop_caller_string(pkey):
    tok = pkey.split(".")
    cap = []
    for t in tok:
        cap.append(f"{string.capwords(t)}()")
    return ".".join(cap)


def yaml_files(path):
    yamls = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".yaml"):
                yamls.append(os.path.join(root, file))
    return yamls
