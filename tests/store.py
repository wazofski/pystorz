import ast
import sys
import logging
import inspect

import time
from datetime import datetime
from pystorz.store import options, store, utils
from pystorz.internal import constants
from generated import model

log = logging.getLogger(__name__)

# decorator for test functions
def test(fn):
    def wrapper(*args, **kwargs):
        try:
            fn(*args, **kwargs)
            print("********************* {} -> PASS".format(fn.__name__))
        except Exception as ex:
            print("********************* {} -> FAIL: {}".format(fn.__name__, str(ex)))
            raise ex

    return wrapper

def get_function_order():
    # Use ast to parse the source file and extract the function definitions
    source = open(__file__, "rt").read()
    module = ast.parse(source)

    functions = []
    for node in module.body:
        if isinstance(node, ast.FunctionDef):
            functions.append(node)

    # Sort the function definitions by their line numbers
    functions.sort(key=lambda f: f.lineno)

    # Print the functions in the order they appear in the source file
    res = []
    for function in functions:
        res.append(function.name)
    return res

def common_test_suite(store_to_use):
    global clt
    clt = store_to_use

    log.info("Running common test suite using %s", clt)

    to_run = dict()

    # find all functions inside this function with test decorator and run them
    for name, func in inspect.getmembers(sys.modules[__name__]):
        if not inspect.isfunction(func):
            continue

        # check if the function has the test decorator
        if name.startswith("test_"):
            to_run[name] = func
        # decorator_list = [d for d in reversed(inspect.getattr_static(func, "__decorators__", [])) if isinstance(d, test)]

        # decorator_list = inspect.getmembers(func.__class__, lambda x: isinstance(x, test))
        # if len(decorator_list) > 0:
        #     func()
        # if any(isinstance(d, test) for d in reversed(inspect.getattr_static(func, "__decorators__", []))):
        #     func()

    # run the functions in the order they appear in the source file
    for name in get_function_order():
        if name in to_run:
            to_run[name]()

