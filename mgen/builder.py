import os
import string
import logging
from typing import List
from io import StringIO

from jinja2 import Template

from mgen.loader import load_model, _Resource
from utils import utils

log = logging.getLogger(__name__)


class _Tuple:
    def __init__(self, A: str, B: str):
        self.A = A
        self.B = B


class _Prop:
    def __init__(self, name: str, json: str, type: str, default: str):
        self.Name = name
        self.Json = json
        self.Type = type
        self.Default = default

    def IsMap(self):
        if len(self.Type) < 3:
            return False

        return self.Type[:3] == "map"

    def IsArray(self):
        if len(self.Type) < 2:
            return False

        return self.Type[:2] == "[]"

    def StrippedType(self):
        if self.IsMap():
            return self.Type[self.Type.rfind("]")+1:]
        if self.IsArray():
            return self.Type[2:]
        return self.Type

    def StrippedDefault(self):
        return typeDefault(self.StrippedType())


class _Struct:
    def __init__(self, name: str, props: List[_Prop], implements: List[str]):
        self.Name = name
        self.Props = props
        self.Implements = implements


def Generate(model: str) -> None:
    try:
        structs, resources = load_model(model)

        imports = [
            "json",
        ]

        b = string.Template(
            render("templates/imports.pytext", {"imports": imports}))
        b.write(compileResources(resources))
        b.write(compileStructs(structs))

        res = b.getvalue().replace("&#34;", "\"")
        # res, err = Source(bytes(str.encode("utf-8")))

        # if err:
        #     log.error(err)
        #     res = str.encode("utf-8")

        targetDir = "generated"
        os.RemoveAll(targetDir)

        utils.ExportFile(targetDir, "objects.go", res.decode("utf-8"))

        return None
    except Exception as e:
        return e


# class _Interface:
#     def __init__(self, Name: str, Methods: List[str], Implements: List[str]):
#         self.Name = Name
#         self.Methods = Methods
#         self.Implements = Implements


def compileResources(resources: List[_Resource]) -> str:
    b = string.Template("")

    for r in resources:
        props = [
            {
                "Name": "Meta",
                "Type": "store.Meta",
                "Json": "metadata",
                "Default": f'store.MetaFactory("{r.Name}")'
            }
        ]

        if r.External:
            props.append({
                "Name": "External",
                "Type": r.External,
                "Json": "external"
            })

        if r.Internal:
            props.append({
                "Name": "Internal",
                "Type": r.Internal,
                "Json": "internal"
            })

        s = _Struct(
            Name=r.Name,
            Props=props,
            Embeds=[],
            Implements=[
                "store.Object"
            ]
        )

        b.write(compileStruct(s))
        b.write(render("templates/meta.pytext", {"resource": r}))
        b.write(render("templates/clone.pytext", {"struct": s}))

    b.write(render("templates/schema.pytext", {"resources": resources}))

    return b.getvalue()


def compileStructs(structs: List[_Struct]) -> str:
    b = string.Template("")

    for s in structs:
        b.write(compileStruct(s))

    return b.getvalue()


def compileStruct(s: _Struct) -> str:
    b = StringIO()
    methods = []

    s.Props = addDefaultPropValues(s.Props)

    for p in s.Props:
        if p.Name != "Meta":
            methods.append(f"{p.Name}() {p.Type}")

        if p.Name != "Meta" and p.Name != "External" and p.Name != "Internal":
            methods.append(f"Set{p.Name}(v {p.Type})")

        if p.Name == "External":
            b.write(render("templates/specinternal.pytext",
                    {'A': s.Name, 'B': p.Type}))

    impl = s.Implements + ["json.Unmarshaler"]

    b.write(render("templates/interface.pytext",
            {'Name': s.Name, 'Methods': methods, 'Implements': impl}))
    b.write(render("templates/structure.pytext", s.__dict__))
    b.write(render("templates/unmarshall.pytext", s.__dict__))

    return b.getvalue()


def render(rpath: str, data: dict) -> str:
    path = os.path.join(utils.RuntimeDir(), rpath)

    with open(path, 'r') as f:
        content = f.read()

    t = Template(content)
    return t.render(data)


def addDefaultPropValues(props: List[_Prop]) -> List[_Prop]:
    res = []

    for p in props:
        if len(p.Default) > 0:
            res.append(p)
            continue

        res.append(_Prop(p.Name, p.Json, p.Type, typeDefault(p.Type)))

    return res


def typeDefault(tp: str) -> str:
    if tp.startswith("[]"):
        return "list()"
        # return f"{tp} {{}}"
    if tp.startswith("map"):
        return "dict()"
        # return f"make({tp})"

    if tp == "string":
        return '""'
    if tp == "bool":
        return "False"
    if tp == "int":
        return "0"
    if tp == "float":
        return "0.0"
    return f"{tp}Factory()"
