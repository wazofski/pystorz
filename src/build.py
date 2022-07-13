import os
import shutil
import sys
import logging
import logging.config
import yaml


TAB = '    '
ENDL = '''
'''


class StringBuilder:

    def __init__(self):
        self.c = ""
        self.t = 0

    def newline(self):
        self.c += ENDL
        return self

    def indent(self):
        self.t += 1
        return self

    def unindent(self):
        self.t -= 1
        return self

    def line(self, v):
        self.newline().c += TAB*self.t + v
        return self

    def write(self, name):
        with open(name, "w") as file:
            # Writing data to a file
            file.write(self.c)


config = dict()
with open('config/logger.yml', 'r') as f:
    from yaml import safe_load
    logging.config.dictConfig(safe_load(f.read()))


log = logging.getLogger("build")


def parse(model):
    res = []
    with open(model, "r") as stream:
        try:
            for r in yaml.safe_load_all(stream):
                res.append(r)
        except yaml.YAMLError as exc:
            log.error(exc)
    return res


def prepare_output(model):
    tok = model.split("/")
    dir = tok[len(tok)-1].split('.')[0]

    try:
        shutil.rmtree(dir)
    except:
        pass

    os.mkdir(dir)
    return dir


def generate(dir, k):
    def default(t):
        if t == "int":
            return 0
        if t == "string":
            return '""'
        if t == "bool":
            return "False"

        raise Exception("Unknown type: {}".format(t))

    b = StringBuilder()

    # imports

    # class def
    b.line("class {}:".format(k["name"]))
    b.newline()
    # constructor
    b.indent().line("def __init__(self):")
    b.indent()

    for p, t in k["props"].items():
        b.line("self.{} = {}".format(p, default(t)))

    b.unindent()
    b.newline()

    for p, t in k["props"].items():
        b.line("def get_{}(self):".format(p))
        b.indent().line("return self.{}".format(p)).unindent()

        b.newline()

        b.line("def set_{}(self, v):".format(p))
        b.indent().line("self.{} = v".format(p)).unindent()

        b.newline()

    b.write("{}/{}.py".format(dir, k["name"]))


def compile(model):
    log.debug("compiling {}".format(model))

    dir = prepare_output(model)

    types = parse(model)
    for k in types:
        generate(dir, k)


if __name__ == "__main__":
    compile(sys.argv[1])
