import os
import shutil
import black
import logging
import yaml

from jinja2 import Template

from pystorz.store import utils
from pystorz.mgen.utils import yaml_files
from pystorz.mgen.meta import Struct, Resource


log = logging.getLogger(__name__)
log.debug("loading generator.py...")


def Generate(*models) -> None:
    structs = dict()
    resources = dict()

    for model in models:
        log.debug(f"Loading model {model}...")

        s, r = _load_model(model)

        structs.update(s)
        resources.update(r)

    res = _cleanup(
        _render(
            "mgen/templates/python.py",
            resources,
            _dependency_order(structs)))    

    # refactor and format python code
    res = _reformat_python_code(res)

    targetDir = "generated"

    if os.path.exists(targetDir):
        # delete the directory with contents
        shutil.rmtree(targetDir)

    utils.export_file(targetDir, "model.py", res)


    res = _render(
            "mgen/templates/javascript.js",
            resources,
            _dependency_order(structs))

    # refactor and format javascript code
    targetDir = "generated"

    utils.export_file(targetDir, "model.js", res)

    

def _load_model(path: str):
    yamls = yaml_files(path)
    structs = dict()
    resources = dict()

    for y in yamls:
        model = _read_model(y)

        for m in model["types"]:
            if m["kind"].lower() == "struct":
                if m["name"] in structs:
                    raise Exception("duplicate struct: {}".format(m["name"]))
                structs[m["name"]] = Struct(m)
                continue

            if m["kind"].lower() == "object":
                if m["name"] in resources:
                    raise Exception("duplicate object: {}".format(m["name"]))
                resources[m["name"]] = Resource(m)
                continue

            raise Exception("unknown kind: {}".format(m["kind"]))

    errors = _validate_model(structs, resources)
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


def _validate_model(structs, resources):
    errors = []
    known_types = ["string", "int", "float", "bool", "datetime"]

    for _, s in structs.items():
        known_types.append(s.name)

    for _, s in structs.items():
        for p in s.properties:
            if p.IsArray():
                elem_type = p.SubType()
                if elem_type not in known_types:
                    errors.append(
                        "struct {} property {}: unknown type: {}".format(
                            s.name, p.name, elem_type
                        )
                    )
                continue

            if p.IsMap():
                # map[int]string
                elem_type = p.SubType()
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

    for _, r in resources.items():
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


def _read_model(path: str):
    log.debug(f"reading model from {path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data


def _dependency_order(structs) -> list[Struct]:
    all_structs = {}
    dependencies = {}
    for _, s in structs.items():
        all_structs[s.name] = s
        dependencies[s.name] = set()

    known_types = ["string", "int", "float", "bool", "datetime"]

    for _, s in structs.items():
        for p in s.properties:
            if p.IsArray():
                elem_type = p.SubType()
                if elem_type not in known_types:
                    dependencies[s.name].add(elem_type)

                continue

            if p.IsMap():
                # map[string]bla
                elem_type = p.SubType()
                key_type = p.type[4:].split("]")[0]
                if key_type not in known_types:
                    raise Exception(
                        f"Invalid type {key_type} in {p.type}. Please use one of {known_types} as map key type"
                    )

                val_type = p.type[4:].split("]")[1]
                if val_type not in known_types:
                    dependencies[s.name].add(val_type)

                continue

            if p.type not in known_types:
                dependencies[s.name].add(p.type)

    ordered = []
    while len(ordered) < len(structs):
        did_stuff = False
        for _, s in structs.items():
            if s in ordered:
                continue

            if len(dependencies[s.name]) == 0:
                ordered.append(s)
                for k in dependencies.keys():
                    if s.name in dependencies[k]:
                        dependencies[k].remove(s.name)
                        did_stuff = True

        if not did_stuff and len(ordered) < len(structs):
            log.debug(f"dependencies: {dependencies}")
            log.debug(f"ordered: {[ o.name for o in ordered]}")
            log.debug(f"lengths: {len(dependencies)} {len(ordered)} {len(structs)}")

            raise Exception("Circular dependency detected")

    return ordered


def _render(rpath: str, resources, structs) -> str:
    path = os.path.join(utils.runtime_dir(), rpath)

    with open(path, "r") as f:
        content = f.read()

    t = Template(content)
    return t.render(resources=resources, structs=structs)


def _reformat_python_code(code_str):
    try:
        # Reformat the code string using the parsed AST.
        formatted_code = black.format_str(code_str, mode=black.FileMode())

        return formatted_code

    except Exception as e:
        log.error("failed to reformat code:", e)
        return code_str

def _cleanup(code_str):
    # remove empty lines
    code_str = code_str.replace("&#34;", '"')
    return os.linesep.join([s for s in code_str.splitlines() if s.strip()])
