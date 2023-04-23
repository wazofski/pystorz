import os
import shutil
import black
import logging
from typing import List
from io import StringIO

from jinja2 import Template

from mgen.loader import load_model, Resource, Struct, Prop, typeDefault
from store import utils

log = logging.getLogger(__name__)
log.debug('loading builder.py...')


def Generate(model: str) -> None:
    try:
        structs, resources = load_model(model)

        imports = [
            "import json",
            "from store import utils",
            "from store import store",
            "from store import meta",
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
#         self.name = Name
#         self.Methods = Methods
#         self.implements = Implements


def compileResources(resources: List[Resource]) -> str:
    b = StringIO()

    for r in resources:
        log.info(f"Compiling resource {r.name}...")

        props = [
            Prop(
                "Meta",
                "store.Meta",
                "metadata",
                f'meta.MetaFactory("{r.name}")')
        ]

        if r.external:
            props.append(Prop(
                "External",
                r.external,
                "external"))

        if r.internal:
            props.append(Prop(
                "Internal",
                r.internal,
                "internal"))

        s = Struct(
            r.name,
            r.name,
            props,
        )

        b.write(compileStruct(s))
        b.write(render("mgen/templates/meta.pytext", r))

    b.write(render("mgen/templates/schema.pytext", {"resources": resources}))

    return b.getvalue()


def compileStructs(structs: List[Struct]) -> str:
    b = StringIO()

    for s in structs:
        b.write(compileStruct(s))

    return b.getvalue()


def compileStruct(s: Struct) -> str:
    log.info(f"Compiling struct {s.name}...")

    b = StringIO()
    methods = []

    s.properties = addDefaultPropValues(s.properties)

    for p in s.properties:
        if p.name != "Meta":
            methods.append(f"{p.name}(self) -> {p.StrippedType()}")

        if p.name != "Meta" and p.name != "External" and p.name != "Internal":
            methods.append(f"Set{p.name}(self, val: {p.StrippedType()})")

        if p.name == "External":
            b.write(render("mgen/templates/specinternal.pytext", None))

    # impl = s.implements + ["json.Unmarshaler"]

    b.write(render("mgen/templates/interface.pytext",
            {
                'name': s.name,
                'methods': methods,
                'implements': "store.Object"
            }))

    b.write(render("mgen/templates/structure.pytext", s))
    # b.write(render("mgen/templates/unmarshall.pytext", s))

    return b.getvalue()


def render(rpath: str, data) -> str:
    path = os.path.join(utils.runtime_dir(), rpath)

    with open(path, 'r') as f:
        content = f.read()

    t = Template(content)
    return t.render(data=data)


def addDefaultPropValues(props: List[Prop]) -> List[Prop]:
    res = []

    for p in props:
        if len(p.default) > 0:
            res.append(p)
            continue

        res.append(Prop(p.name, p.type, p.json, typeDefault(p.type)))

    return res


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
