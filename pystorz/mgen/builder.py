import os
import shutil
import black
import logging
from io import StringIO

from jinja2 import Template

from pystorz.mgen.loader import load_model, Resource, Struct, Prop, typeDefault
from pystorz.store import utils

log = logging.getLogger(__name__)
log.debug('loading builder.py...')


def Generate(*models) -> None:
    structs = []
    resources = []

    for model in models:
        log.debug(f"Loading model {model}...")
        
        s, r = load_model(model)
        
        structs.extend(s)
        resources.extend(r)

    imports = [
        "import json",
        "from pystorz.internal import constants",
        "from pystorz.store import utils",
        "from pystorz.store import store",
        "from datetime import datetime",
        "from typing import Type",
    ]

    b = StringIO()

    b.write(render("mgen/templates/imports.py", {"imports": imports}))

    b.write(compileStructs(structs))
    b.write(compileResources(resources))

    res = b.getvalue().replace("&#34;", "\"")

    # refactor and format python code
    res = reformat_python_code(res)

    targetDir = "generated"

    if os.path.exists(targetDir):
        # delete the directory with contents
        shutil.rmtree(targetDir)

    utils.export_file(targetDir, "model.py", res)


def compileResources(resources: list[Resource]) -> str:
    b = StringIO()

    for r in resources:
        log.debug(f"Compiling resource {r.name}...")

        props = [
            Prop(
                "Meta",
                "store.Meta",
                "metadata",
                f'store.MetaFactory("{r.name}")')
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
            "store.Object",
            props,
        )

        b.write(compileStruct(s))
        b.write(render("mgen/templates/meta.py", r))

    b.write(render("mgen/templates/schema.py", {"resources": resources}))

    return b.getvalue()


def compileStructs(structs: list[Struct]) -> str:
    b = StringIO()

    dep, nodep = checkDependencies(structs)

    for s in nodep:
        b.write(compileStruct(s))
    
    for s in dep:
        b.write(compileStruct(s))
    
    return b.getvalue()


def checkDependencies(structs: list[Struct]) -> tuple[list[Struct], list[Struct]]:
    dep = []
    nodep = []

    known_types = ["string", "int", "float", "bool", "datetime"]

    for s in structs:
        for p in s.properties:
            if p.IsArray():
                elem_type = p.SubType()
                if elem_type not in known_types:
                    dep.append(s)
                    break
                continue

            if p.IsMap():
                # map[int]string
                elem_type = p.SubType()
                key_type = p.type[4:].split("]")[0]
                val_type = p.type[4:].split("]")[1]
                if key_type not in known_types:
                    dep.append(s)
                    break

                if val_type not in known_types:
                    dep.append(s)
                    break
                continue

            if p.type not in known_types:
                dep.append(s)
                break
    
    for s in structs:
        if s not in dep:
            nodep.append(s)

    return (dep, nodep)


def compileStruct(s: Struct) -> str:
    log.debug(f"Compiling struct {s.name}...")

    b = StringIO()
    methods = []

    s.properties = addDefaultPropValues(s.properties)

    parent = s.implements

    for p in s.properties:
        if p.name != "Meta":
            # methods.append(f"{p.name}(self) -> {p.StrippedType()}")
            methods.append((f"{p.name}(self)", p.StrippedType()))

        if p.name != "Meta" and p.name != "External" and p.name != "Internal":
            # methods.append(f"Set{p.name}(self, val: {p.StrippedType()})")
            methods.append((f"Set{p.name}(self, val: {p.StrippedType()})", ""))

        if p.name == "External":
            parent = "store.ExternalHolder"
    
    b.write(
        render(
            "mgen/templates/interface.py",
            {
                'name': s.name,
                'methods': methods,
                'implements': parent
            }))

    if parent in ["store.Object", "store.ExternalHolder"]:
        b.write(render("mgen/templates/clone.py", s))

    b.write(render("mgen/templates/structure.py", s))
    b.write(render("mgen/templates/unmarshall.py", s))

    if parent in ["store.Object", "store.ExternalHolder"]:
        b.write(render("mgen/templates/cloneimp.py", s))

    return b.getvalue()


def render(rpath: str, data) -> str:
    path = os.path.join(utils.runtime_dir(), rpath)

    with open(path, 'r') as f:
        content = f.read()

    t = Template(content)
    return t.render(data=data)


def addDefaultPropValues(props: list[Prop]) -> list[Prop]:
    res = []

    for p in props:
        if len(p.default) > 0:
            res.append(p)
            continue

        res.append(Prop(p.name, p.type, p.json, typeDefault(p.type)))

    return res


def reformat_python_code(code_str):
    try:
        # Reformat the code string using the parsed AST.
        formatted_code = black.format_str(code_str, mode=black.FileMode())

        return formatted_code

    except Exception as e:
        log.error("failed to reformat code:", e)
        return code_str
