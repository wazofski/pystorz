import json
import logging
import traceback

# from urllib.parse import parse_qs, urlparse

from pystorz.internal import constants

from pystorz.store import store
from pystorz.store import options
from pystorz.store import utils

from pystorz.rest import internals

from flask import Flask, request


log = logging.getLogger(__name__)


FilterArg = "pf"
IncrementalArg = "inc"
PageSizeArg = "pageSize"
PageOffsetArg = "pageOffset"
OrderByArg = "orderBy"


ActionCreate = "POST"
ActionUpdate = "PUT"
ActionDelete = "DELETE"
ActionGet = "GET"


def _handle_exceptions(e):
    log.error(e)
    traceback.print_exc()


def _json_response(code: int, data: dict):
    return json.dumps(data), code, {"Content-Type": "application/json"}


def _error_response(code: int, message: str):
    return _json_response(code, {"error": message})


def _make_id_handler(stor, schema, exposed):
    def handler(id_param):
        id = store.ObjectIdentity(id_param)
        existing = stor.Get(id)

        robject = None
        if existing is not None:
            kind = existing.Metadata().Kind()
            obj_methods = exposed[kind]
            if obj_methods is None or request.method not in obj_methods:
                return _error_response(405, constants.ErrInvalidMethod)

            robject = utils.unmarshal_object(request.content, schema, kind)

        return _handle_path(stor, id, robject)

    return handler


def _handle_path(
    stor: store.Store,
    identity: store.ObjectIdentity,
    object: store.Object):
    
    ret = None
    if request.ethod == ActionGet:
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


# def _make_object_handler(stor: store.Store, schema: store.SchemaHolder, t: str, methods: List[str]):
#     def handler(pkey: str):
#         robject = None
#         id = store.ObjectIdentity(t.lower() + "/" + pkey)
#         data = read_stream(r.Body)
#         if err is None:
#             robject, _ = unmarshal_object(data, self.Schema, t)

#         if r.Method not in methods:
#             report_error(w, constants.ErrInvalidMethod, http.StatusMethodNotAllowed)
#             return

#         self.handle_path(w, r, id, robject)

#     return handler


# def _make_type_handler(stor: store.Store, t: str, methods: List[str]):
#     def handler(w: http.server.BaseHTTPRequestHandler):
#         if r.Method not in methods:
#             report_error(w, constants.ErrInvalidMethod, http.StatusMethodNotAllowed)
#             return

#         query_params = parse_qs(urlparse(r.url).query)

#         opts = []
#         filter_args = query_params.get(FilterArg)
#         if filter_args:
#             opts.append(options.ListDeleteOption.fromJson(filter_args[0]))

#         page_size_args = query_params.get(PageSizeArg)
#         if page_size_args:
#             ps = int(page_size_args[0])
#             opts.append(options.PageSize(ps))

#         page_offset_args = query_params.get(PageOffsetArg)
#         if page_offset_args:
#             ps = int(page_offset_args[0])
#             opts.append(options.PageOffset(ps))

#         order_by_args = query_params.get(OrderByArg)
#         if order_by_args:
#             ob = order_by_args[0]
#             opts.append(options.OrderBy(ob))

#         order_inc_args = query_params.get(IncrementalArg)
#         if order_inc_args:
#             ob = True
#             err = json.loads(order_inc_args[0], ob)
#             if err is not None:
#                 report_error(w, err, http.StatusBadRequest)
#                 return
#             if not ob:
#                 opts.append(OrderDescending())

#         ret = self.Store.List(
#             self.Context, store.ObjectIdentity(f"{strings.ToLower(t)}/"), opts
#         )

#         if err is not None:
#             report_error(w, err, http.StatusBadRequest)
#             return
#         elif ret is not None:
#             resp, _ = json.Marshal(ret)
#             write_response(w, resp)

#     return handler


class Expose:
    def __init__(self, kind: str, *actions: list):
        self.Kind = kind
        self.Actions = actions


class Server:
    def __init__(self, schema, thestore, to_expose):
        self.Schema = schema
        self.Store = internals.internal_factory(schema, thestore)
        self.Exposed = {}

        for e in to_expose:
            self.Exposed[e.Kind] = e.Actions

        self.app = Flask(__name__)
        self.app.register_error_handler(Exception, _handle_exceptions)

    def serve(self, host: str, port: int):
        # launch a flask server to serve the html
        log.info("serving on {}:{}".format(host, port))

        import cherrypy

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
            cherrypy.engine.block()
        except KeyboardInterrupt:
            cherrypy.engine.stop()

        log.info("server stopped...")

    def register_handlers(self):
        self.app.add_url_rule(
            "/id/<id>",
            _make_id_handler(
                self.Store,
                self.Schema,
                self.Exposed)
        )

        # self.add_handler(self.Router, "/id/{id}", )
        # for e in exposed:
        #     kind = e["Kind"]
        #     actions = e["Actions"]
        #     self.Exposed[kind] = actions

        #     self.add_handler(self.Router, f"/{kind}/{{pkey}}", self.make_object_handler(kind, actions))
        #     self.add_handler(self.Router, f"/{kind}", self.make_type_handler(kind, actions))
        #     self.add_handler(self.Router, f"/{kind}/", self.make_type_handler(kind, actions))

        # add_handler(server.Router, "/id/{id}", server.make_id_handler())
        # for e in exposed:
        #     server.Exposed[e.Kind] = e.Actions

        #     add_handler(
        #         server.Router,
        #         f"/{e.Kind}/{{pkey}}",
        #         server.make_object_handler(e.Kind, e.Actions)
        #     )
        #     add_handler(
        #         server.Router,
        #         f"/{e.Kind}",
        #         server.make_type_handler(e.Kind, e.Actions)
        #     )
        #     add_handler(
        #         server.Router,
        #         f"/{e.Kind}/",
        #         server.make_type_handler(e.Kind, e.Actions)
        #     )


# def add_handler(router: mux.Router, pattern: str, handler: _HandlerFunc):
#     app.add_url_rule("/" + url.capitalize() + "/", None,
#                     finger, methods=["GET", "POST"])
