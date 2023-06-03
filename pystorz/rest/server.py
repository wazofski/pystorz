import json
import logging
import traceback
import cherrypy

from pystorz.internal import constants
from urllib.parse import urlparse, parse_qs

from pystorz.store import store
from pystorz.store import options
from pystorz.store import utils

from pystorz.rest import internals

from flask import Flask, request


# from urllib.parse import parse_qs, urlparse


log = logging.getLogger(__name__)


FilterArg = "pf"
IncrementalArg = "inc"
PageSizeArg = "pageSize"
PageOffsetArg = "pageOffset"
OrderByArg = "orderBy"


ActionGet = "GET"
ActionCreate = "POST"
ActionUpdate = "PUT"
ActionDelete = "DELETE"


def _handle_exceptions(e):
    error_code = 500
    msg = str(e)
    if msg == constants.ErrNoSuchObject:
        error_code = 404
    if msg == constants.ErrInvalidMethod:
        error_code = 405

    return _error_response(error_code, msg)


def _json_response(code: int, data: dict):
    return json.dumps(data), code, {"Content-Type": "application/json"}


def _error_response(code: int, message: str):
    return _json_response(code, {"error": message})


def _make_id_handler(stor, schema, exposed):
    def handler(id):
        iddentifier = store.ObjectIdentity(id)
        existing = stor.Get(iddentifier)

        robject = None
        if existing is not None:
            kind = existing.Metadata().Kind()
            obj_methods = exposed[kind]
            if obj_methods is None or request.method not in obj_methods:
                return _error_response(405, constants.ErrInvalidMethod)

            robject = utils.unmarshal_object(request.content, schema, kind)

        return _handle_path(stor, iddentifier, robject)

    return handler


def _handle_path(
    stor: store.Store, identity: store.ObjectIdentity, object: store.Object
):
    ret = None
    if request.method == ActionGet:
        try:
            ret = stor.Get(identity)
        except Exception as e:
            return _error_response(404, str(e))
    elif request.method == ActionCreate:
        try:
            ret = stor.Create(object)
        except Exception as e:
            return _error_response(409, str(e))
    elif request.method == ActionUpdate:
        try:
            ret = stor.Update(identity, object)
        except Exception as e:
            return _error_response(409, str(e))
    elif request.method == ActionDelete:
        try:
            stor.Delete(identity)
        except Exception as e:
            return _error_response(404, str(e))

    if ret is not None:
        return _json_response(200, ret.ToDict())

    return _json_response(200, {})


def _make_object_handler(
    stor: store.Store, schema: store.SchemaHolder, t: str, methods: list
):
    def handler(pkey: str):
        id = store.ObjectIdentity("{}/{}".format(t.lower(), pkey))

        robject = utils.unmarshal_object(request.content, schema, t)

        if request.method not in methods:
            return _error_response(405, constants.ErrInvalidMethod)

        return _handle_path(stor, id, robject)

    return handler


def _make_type_handler(stor: store.Store, t: str, methods: list):
    def handler():
        if request.method not in methods:
            return _error_response(405, constants.ErrInvalidMethod)

        url = urlparse(request.url)
        query_params = parse_qs(url.query)

        opts = []
        if FilterArg in query_params:
            opts.append(options.ListDeleteOption.FromJson(query_params[FilterArg]))

        if PageSizeArg in query_params:
            ps = int(query_params[PageSizeArg])
            opts.append(options.PageSize(ps))

        if PageOffsetArg in query_params:
            ps = int(query_params[PageOffsetArg])
            opts.append(options.PageOffset(ps))

        if OrderByArg in query_params:
            ascending = True
            if IncrementalArg in query_params:
                ascending = query_params[IncrementalArg] != "true"

            opts.append(options.Order(query_params[OrderByArg], ascending))

        try:
            ret = stor.List(store.ObjectIdentity(t.lower() + "/"), opts)
            return _json_response(200, [r.ToDict() for r in ret])

        except Exception as e:
            return _error_response(400, str(e))

    return handler


class Expose:
    def __init__(self, kind: str, *actions: list):
        self.Kind = kind
        self.Actions = actions


class Server:
    def __init__(self, schema, thestore, *to_expose):
        self.Schema = schema
        self.Store = internals.internal_factory(schema, thestore)
        self.Exposed = {}

        accepted_actions = set([ActionGet, ActionCreate, ActionUpdate, ActionDelete])

        for e in to_expose:
            for a in e.Actions:
                if a not in accepted_actions:
                    raise Exception("invalid action: {}".format(a))

            self.Exposed[e.Kind] = e.Actions

        self.app = Flask(__name__)
        self.app.register_error_handler(Exception, _handle_exceptions)

        self._register_handlers()

    def Serve(self, host: str, port: int):
        # launch a flask server to serve the html
        log.info("serving on {}:{}".format(host, port))

        cherrypy.tree.graft(self.app, "/")
        cherrypy.config.update(
            {
                "server.socket_host": host,
                "server.socket_port": port,
            }
        )

        cherrypy.config.update(
            {
                "log.access_file": "",  # Disable CherryPy's default access log
                # 'log.screen': False,    # Disable logging to the console
            }
        )

        # Enable access logging
        cherrypy.log.access_log = log

        try:
            cherrypy.engine.start()
        except KeyboardInterrupt:
            cherrypy.engine.stop()

        log.info("server stopped...")

    def Join(self):
        cherrypy.engine.block()

    def _register_handlers(self):
        self.app.add_url_rule(
            "/id/<id>",
            "id_handler",
            _make_id_handler(self.Store, self.Schema, self.Exposed)
        )

        for k, v in self.Exposed.items():
            self.app.add_url_rule(
                f"/{k.lower()}/<pkey>",
                f"{k}_handler",
                _make_object_handler(self.Store, self.Schema, k, v),
            )

            type_handler = _make_type_handler(self.Store, k, v)

            self.app.add_url_rule(f"/{k.lower()}", f"{k}_type_handler1", type_handler)
            self.app.add_url_rule(f"/{k.lower()}/", f"{k}_type_handler2", type_handler)
