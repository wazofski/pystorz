import json
import io
import os
import time
# import logging
import pathlib
import string

# import gabs

from internal import constants
from store import store


class _MetaHolder:
    def __init__(self):
        self.Metadata = None
        # self.External = None
        # self.Internal = None


def clone_object(obj: store.Object, schema: store.SchemaHolder) -> store.Object:
    ret = schema.ObjectForKind(obj.Metadata().Kind())
    jsn = obj.ToJson()
    ret.FromJson(jsn)
    return ret


def unmarshal_object(body: bytes, schema: store.SchemaHolder, kind: str) -> store.Object:
    resource = schema.ObjectForKind(kind)
    err = json.loads(body, object_hook=lambda d: resource.__dict__.update(d))
    return resource, err


def object_kind(response: bytes) -> str:
    obj = _MetaHolder()
    err = json.loads(response, object_hook=lambda d: obj.__dict__.update(d))
    if err:
        return ""
    if obj.Metadata is None:
        return ""
    return obj.Metadata['kind']


def pp(obj: store.Object) -> str:
    jsn = json.dumps(obj, indent=4, default=lambda x: x.to_dict())
    return jsn


def timestamp() -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())


def serialize(mo: store.Object) -> bytes:
    if mo is None:
        raise constants.ErrObjectNil
    return json.dumps(mo, default=lambda x: x.to_dict())


def object_path(obj: store.Object, path: str) -> str:
    data = obj.ToJson()
    jsn = json.loads(data)
    if not jsn.path(path):
        return None
    ret = jsn.path(path).value
    if isinstance(ret, str):
        ret = ret.translate(str.maketrans('', '', string.punctuation))
    return ret


def export_file(target_dir: str, name: str, content: str) -> None:
    pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
    target_file = os.path.join(target_dir, name)
    with open(target_file, 'w') as f:
        f.write(content)


def runtime_dir() -> str:
    rd = pathlib.Path(__file__).parent.parent.absolute()
    return rd
