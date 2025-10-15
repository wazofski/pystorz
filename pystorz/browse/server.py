import json

import logging

from pystorz.internal import constants
from pystorz.store import utils
from pystorz.store import store
from markupsafe import Markup

from flask import Flask, render_template


log = logging.getLogger(__name__)


def _json_response(code: int, data):
    try:
        ret = json.dumps(data)
        log.debug("""json response: 
    {}""".format(utils.pp(data)))

        return ret, code, {"Content-Type": "application/json"}
    except Exception as e:
        log.debug("json error: {}".format(e))
        return _error_response(500, str(e))


def _error_response(code: int, message: str):
    return _json_response(code, {"error": message})


def _handle_exceptions(e):
    # traceback.print_stack()

    error_code = 500
    msg = str(e)
    if msg == constants.ErrNoSuchObject:
        error_code = 404
    if msg == constants.ErrInvalidMethod:
        error_code = 405

    return _error_response(error_code, msg)


def format_json(value):
    # return Markup(value)
    return Markup(value.replace("'", "`"))


class Server:

    def __init__(self, schema: store.SchemaHolder, thestore: store.Store):
        self.Schema = schema
        self.Store = thestore

        template_folder = utils.runtime_dir() + "/browse/templates/"
        # log.info(template_folder)

        self.app = Flask(
            "pystorz",
            template_folder=template_folder)
        # self.app.register_error_handler(Exception, _handle_exceptions)

        self._register_handlers()

    def Serve(self, host: str, port: int):
        # launch a flask server to serve the html
        log.info("serving on {}:{}".format(host, port))

        self.app.run(host, port)
        # return self.Stop

    def _register_handlers(self):
        self._register_handler(
            "/", "index", self.make_index_handler(), methods=["GET"])
        self._register_handler(
            "/id/<id>",
            "id_handler",
            self.make_id_handler(),
            methods=["GET"],
        )

        for k in self.Schema.Types():
            self._register_handler(
                f"/{k.lower()}/<pkey>",
                f"{k}_handler",
                self.make_object_handler(k),
                methods=["GET"],
            )

            type_handler = self.make_type_handler(k)
            self._register_handler(
                f"/{k.lower()}", f"{k}_type_handler1", type_handler, methods=["GET"]
            )
            self._register_handler(
                f"/{k.lower()}/", f"{k}_type_handler2", type_handler, methods=["GET"]
            )

    def make_index_handler(self):
        def handler():
            return render_template(
                "index.html",
                types=self.Schema.Types())

        return handler

    def make_id_handler(self):
        def handler(id):
            robject = self.Store.Get(store.ObjectIdentity(id))
            return render_template(
                "viewer.html",
                title=id,
                data=format_json(robject.ToJson()),
            )

        return handler

    def make_object_handler(self, t):
        def handler(pkey):
            robject = self.Store.Get(
                store.ObjectIdentity(
                    "{}/{}".format(t.lower(), pkey)))
            return render_template(
                "viewer.html",
                title=t,
                data=format_json(robject.ToJson()),
            )

        return handler

    def make_type_handler(self, t):
        def handler():
            opts = []
            ret = self.Store.List(
                store.ObjectIdentity("{}/".format(t.lower())),
                *opts
            )

            ret = [r.ToDict() for r in ret]
            return render_template(
                "viewer.html",
                title=t,
                data=format_json(json.dumps(ret)),
            )

        return handler

    def _register_handler(self, path: str, name: str, func, methods: list):
        log.info("registering {} at {} with {}".format(name, path, methods))

        self.app.add_url_rule(path, name, func, methods=methods)
