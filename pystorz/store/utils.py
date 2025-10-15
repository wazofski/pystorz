import os
import json
import time
import logging
import pathlib
import base64

from urllib.parse import quote, unquote

from jsonpath import JSONPath
from datetime import datetime

log = logging.getLogger(__name__)

# import gabs

from pystorz.internal import constants
from pystorz.store import store


# class _MetaHolder:
#     def __init__(self):
#         self.Metadata = None
#         self.External = None
#         self.Internal = None


def unmarshal_object(
    body, schema: store.SchemaHolder, kind: str
) -> store.Object:
    resource = schema.ObjectForKind(kind)
    resource.FromJson(body)
    return resource


def object_kind(data) -> str:
    if "metadata" not in data:
        return ""
    
    if "kind" not in data["metadata"]:
        return ""
    
    return data["metadata"]["kind"]


def pps(string: str) -> str:
    return pp(json.loads(string))


def pp(obj) -> str:
    return json.dumps(obj, indent=4)


def timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())


def serialize(mo: store.Object) -> str:
    if mo is None:
        raise Exception(constants.ErrObjectNil)
    return json.dumps(mo, default=lambda x: x.to_dict())


def object_path(obj: store.Object, path: str) -> object:
    data = obj.ToDict()
    ret = JSONPath("$.{}".format(path)).parse(data)
    if not ret or len(ret) == 0:
        return None
    return ret[0]


def export_file(target_dir: str, name: str, content: str) -> None:
    pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
    target_file = os.path.join(target_dir, name)
    with open(target_file, "w") as f:
        f.write(content)


def runtime_dir() -> str:
    return str(pathlib.Path(__file__).parent.parent.absolute())


def encode_string(string):
    return str(string).replace("'", "$%#")
    # encoded_message = base64.b64encode(string.encode('utf-8'))  # Encode the message as base64 bytes
    # return str(encoded_message, 'utf-8')  # Convert the bytes to a string


def decode_string(soup):
    return soup.replace("$%#", "'")
    # encoded_message = bytes(soup, 'utf-8')  # Convert the soup to bytes
    # return base64.b64decode(encoded_message).decode('utf-8')  # Decode the base64 bytes and convert to string


# encoding = 'ascii'
encoding = 'utf-8'
def base64_encode_string(string):
    # encoded_message = base64.b64encode(string.encode('utf-8'))  # Encode the message as base64 bytes
    # return str(encoded_message, 'utf-8')  # Convert the bytes to a string
    encoded_message = base64.b64encode(string.encode(encoding))  # Encode the message as base64 bytes
    return quote(str(encoded_message, encoding))  # Convert the bytes to a string


def base64_decode_string(soup):
    encoded_message = bytes(unquote(soup), encoding)  # Convert the soup to bytes
    return base64.b64decode(encoded_message).decode(encoding)  # Decode the base64 bytes and convert to string
