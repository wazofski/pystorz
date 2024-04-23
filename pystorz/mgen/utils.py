import os
import re
import json
import logging

log = logging.getLogger(__name__)
log.debug('loading utils.py...')


def yaml_files(path):
    res = []

    lib_regex = re.compile(r"^\w+\.(?:yaml|yml)$")

    for root, dirs, files in os.walk(path):
        for name in files:
            if lib_regex.match(name):
                log.debug(f"found yaml file: {name}")
                res.append(os.path.join(root, name))

    return res

def capitalize(s):
    return s[:1].upper() + s[1:]

def decapitalize(s):
    return s[:1].lower() + s[1:]

def read_file(path):
    with open(path, "rb") as f:
        return f.read()

def jopp(obj):
    # json pretty print
    jstring = """JSON pretty print
""" + json.dumps(
        obj, indent=4, sort_keys=True
    )
    return jstring