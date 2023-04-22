import os, shutil
import black
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
            # "json",
        ]

        b = StringIO()

        b.write(render("mgen/templates/imports.pytext", {"imports": imports}))
        b.write(compileResources(resources))
        b.write(compileStructs(structs))

        res = b.getvalue().replace("&#34;", "\"")

        # refactor and format python code
        res = reformat_python_code(res)

        targetDir = "generated"
        
        if os.path.exists(targetDir):
            # delete the directory with contents
            shutil.rmtree(targetDir)

        utils.export_file(targetDir, "model.py", res)

        return None
    except Exception as e:
        raise e
        # return e


# class _Interface:
#     def __init__(self, Name: str, Methods: List[str], Implements: List[str]):
#         self.Name = Name
#         self.Methods = Methods
#         self.Implements = Implements


def compileResources(resources: List[_Resource]) -> str:
    b = StringIO()

    for r in resources:
        log.info(f"Compiling resource {r.Name}...")
        
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
        b.write(render("mgen/templates/meta.pytext", {"resource": r}))
        b.write(render("mgen/templates/clone.pytext", {"struct": s}))

    b.write(render("mgen/templates/schema.pytext", {"resources": resources}))

    return b.getvalue()


def compileStructs(structs: List[_Struct]) -> str:
    b = StringIO()

    for s in structs:
        b.write(compileStruct(s))

    return b.getvalue()


def compileStruct(s: _Struct) -> str:
    log.info(f"Compiling struct {s.Name}...")

    b = StringIO()
    methods = []

    s.Props = addDefaultPropValues(s.Props)

    for p in s.Props:
        if p.Name != "Meta":
            methods.append(f"{p.Name}() {p.Type}")

        if p.Name != "Meta" and p.Name != "External" and p.Name != "Internal":
            methods.append(f"Set{p.Name}(v {p.Type})")

        if p.Name == "External":
            b.write(render("mgen/templates/specinternal.pytext",
                    {'A': s.Name, 'B': p.Type}))

    impl = s.Implements + ["json.Unmarshaler"]

    b.write(render("mgen/templates/interface.pytext",
            {'Name': s.Name, 'Methods': methods, 'Implements': impl}))
    b.write(render("mgen/templates/structure.pytext", s.__dict__))
    b.write(render("mgen/templates/unmarshall.pytext", s.__dict__))

    return b.getvalue()


def render(rpath: str, data: dict) -> str:
    path = os.path.join(utils.runtime_dir(), rpath)

    with open(path, 'r') as f:
        content = f.read()

    t = Template(content)
    return t.render(data=data)


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


def reformat_python_code(code_str):
    try:
        # Parse the code string with Black's mode to get the abstract syntax tree (AST).
        # parsed_code = black.parse_string(code_str, mode=black.FileMode())

        # Reformat the code string using the parsed AST.
        formatted_code = black.format_str(code_str, mode=black.FileMode())

        return formatted_code

    except Exception as e:
        log.error("failed to reformat code:", e)
        return code_str