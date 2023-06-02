import json
import logging
import strings
import traceback

from typing import Dict, List
from urllib.parse import parse_qs, urlparse

from pystorz.internal import constants

from pystorz.store import store
from pystorz.store import options
from pystorz.store import utils

from pystorz.rest import internals

from flask import Flask


log = logging.getLogger(__name__)


FilterArg = "pf"
IncrementalArg = "inc"
PageSizeArg = "pageSize"
PageOffsetArg = "pageOffset"
OrderByArg = "orderBy"


app = Flask(
    __name__,
)


def handle_exceptions(e):
    traceback.print_exc()


def ok():
    return "ok", 200, {"Content-Type": "text/plain"}


def r404():
    return "not found", 404, {"Content-Type": "text/plain"}


def json_response(dictionary):
    import json

    return json.dumps(dictionary), 200, {"Content-Type": "application/json"}


app.register_error_handler(Exception, handle_exceptions)


class _Server:
    def __init__(self, schema: store.SchemaHolder, stor: store.Store, exposed: List[Dict[str, List[str]]]):
        self.Schema = schema
        self.Store = internals.internal_factory(schema, stor)

        self.Router = mux.NewRouter()
        self.Exposed = {}
        
        self.add_handler(self.Router, "/id/{id}", self.make_id_handler())
        for e in exposed:
            kind = e["Kind"]
            actions = e["Actions"]
            self.Exposed[kind] = actions

            self.add_handler(self.Router, f"/{kind}/{{pkey}}", self.make_object_handler(kind, actions))
            self.add_handler(self.Router, f"/{kind}", self.make_type_handler(kind, actions))
            self.add_handler(self.Router, f"/{kind}/", self.make_type_handler(kind, actions))

    def serve(self, host: str, port: int):
        server_address = (host, port)
        httpd = HTTPServer(server_address, self.Router)
        
        def shutdown():
            httpd.shutdown()
        
        log.Printf(f"listening on port {port}")
        
        return shutdown

    def add_handler(self, router: mux.Router, pattern: str, handler: _HandlerFunc):
        router.HandleFunc(pattern, handler)

        # for url in bad_urls:
        #     app.add_url_rule("/" + url.capitalize(), None,
        #                     finger, methods=["GET", "POST"])
        #     app.add_url_rule("/" + url.capitalize() + "/", None,
        #                     finger, methods=["GET", "POST"])
        #     app.add_url_rule("/" + url.capitalize() + "/<p>",
        #                     None, finger, methods=["GET", "POST"])
        #     app.add_url_rule("/" + url.capitalize() + "/<p>/<z>",
        #                     None, finger, methods=["GET", "POST"])
        #     app.add_url_rule("/" + url.capitalize() + "/<p>/<z>/",
        #                     None, finger, methods=["GET", "POST"])

    def make_id_handler(self) -> _HandlerFunc:
        def handler(w: http.server.BaseHTTPRequestHandler):
            prep_response(w)
            id = store.ObjectIdentity(mux.Vars(r)["id"])
            existing, _ = self.Store.Get(self.Context, id)

            robject = None
            if existing is not None:
                kind = existing.Metadata().Kind()
                data, err = read_stream(r.Body)
                if err is None:
                    robject, _ = unmarshal_object(data, self.Schema, kind)

                obj_methods = self.Exposed[kind]
                if obj_methods is None or not slices.Contains(obj_methods, r.Method):
                    report_error(w, constants.ErrInvalidMethod, http.StatusMethodNotAllowed)
                    return

            self.handle_path(w, r, id, robject)

        return handler

    def make_object_handler(self, t: str, methods: List[str]) -> _HandlerFunc:
        def handler(w: http.server.BaseHTTPRequestHandler):
            prep_response(w)
            robject = None
            id = store.ObjectIdentity(strings.ToLower(t) + "/" + mux.Vars(r)["pkey"])
            data, err = read_stream(r.Body)
            if err is None:
                robject, _ = unmarshal_object(data, self.Schema, t)

            if r.Method not in methods:
                report_error(w, constants.ErrInvalidMethod, http.StatusMethodNotAllowed)
                return

            self.handle_path(w, r, id, robject)

        return handler

    def make_type_handler(self, t: str, methods: List[str]) -> _HandlerFunc:
        def handler(w: http.server.BaseHTTPRequestHandler):
            prep_response(w)

            if r.Method not in methods:
                report_error(w, constants.ErrInvalidMethod, http.StatusMethodNotAllowed)
                return

            query_params = parse_qs(urlparse(r.url).query)

            opts = []
            filter_args = query_params.get(FilterArg)
            if filter_args:
                opts.append(options.ListDeleteOption.fromJson(filter_args[0]))

            page_size_args = query_params.get(PageSizeArg)
            if page_size_args:
                ps = int(page_size_args[0])
                opts.append(options.PageSize(ps))

            page_offset_args = query_params.get(PageOffsetArg)
            if page_offset_args:
                ps = int(page_offset_args[0])
                opts.append(options.PageOffset(ps))

            order_by_args = query_params.get(OrderByArg)
            if order_by_args:
                ob = order_by_args[0]
                opts.append(options.OrderBy(ob))

            order_inc_args = query_params.get(IncrementalArg)
            if order_inc_args:
                ob = True
                err = json.loads(order_inc_args[0], ob)
                if err is not None:
                    report_error(w, err, http.StatusBadRequest)
                    return
                if not ob:
                    opts.append(OrderDescending())

            ret, err = self.Store.List(
                self.Context,
                store.ObjectIdentity(f"{strings.ToLower(t)}/"),
                opts
            )

            if err is not None:
                report_error(w, err, http.StatusBadRequest)
                return
            elif ret is not None:
                resp, _ = json.Marshal(ret)
                write_response(w, resp)

        return handler

    def handle_path(self, w: http.server.BaseHTTPRequestHandler, r: http.server.BaseHTTPRequestHandler, identity: store.ObjectIdentity, object: Object):
        ret = None
        err = None

        if r.Method == http.MethodGet:
            ret, err = self.Store.Get(self.Context, identity)
            if err is not None:
                report_error(w, err, http.StatusNotFound)
                return
        elif r.Method == http.MethodPost:
            ret, err = self.Store.Create(self.Context, object)
            if err is not None:
                report_error(w, err, http.StatusNotAcceptable)
                return
        elif r.Method == http.MethodPut:
            ret, err = self.Store.Update(self.Context, identity, object)
            if err is not None:
                report_error(w, err, http.StatusNotAcceptable)
                return
        elif r.Method == http.MethodDelete:
            err = self.Store.Delete(self.Context, identity)
            if err is not None:
                report_error(w, err, http.StatusNotFound)
                return

        if err is None and ret is not None:
            resp, _ = json.Marshal(ret)
            write_response(w, resp)

    def listen(self, port: int) -> Callable:
        server_address = ("", port)
        httpd = HTTPServer(server_address, self.Router)
        print(f"Listening on port {port}")

        def shutdown():
            httpd.shutdown()

        return shutdown


def report_error(w: http.server.BaseHTTPRequestHandler, err: Error, code: int):
    w.send_error(code, err)

def write_response(w: http.server.BaseHTTPRequestHandler, data: bytes):
    w.write(data)

def prep_response(w: http.server.BaseHTTPRequestHandler, r: http.server.BaseHTTPRequestHandler):
    log.Printf("%s %s", r.Method.lower(), r.url)
    w.headers["Content-Type"] = "application/json"


def add_handler(router: Router, pattern: str, handler: _HandlerFunc):
    router.add_route(pattern, handler)


def server(schema: store.SchemaHolder, stor: store.Store, exposed: List[_TypeMethods]) -> Endpoint:
    server = _Server(
        schema=schema,
        store=internals.internal_factory(stor, schema),
        exposed={},
    )

    add_handler(server.Router, "/id/{id}", server.make_id_handler())
    for e in exposed:
        server.Exposed[e.Kind] = e.Actions

        add_handler(
            server.Router,
            f"/{e.Kind}/{{pkey}}",
            server.make_object_handler(e.Kind, e.Actions)
        )
        add_handler(
            server.Router,
            f"/{e.Kind}",
            server.make_type_handler(e.Kind, e.Actions)
        )
        add_handler(
            server.Router,
            f"/{e.Kind}/",
            server.make_type_handler(e.Kind, e.Actions)
        )

    return server




# def serve():
#     # launch a flask server to serve the html
#     log.info(
#         "serving on {}:{}".format(
#             globals.SERVER_ADDRESS,
#             globals.SERVER_PORT,
#         ))

#     import cherrypy
#     cherrypy.tree.graft(app, '/')
#     cherrypy.config.update({
#         'server.socket_host': globals.SERVER_ADDRESS,
#         'server.socket_port': globals.SERVER_PORT,
#     })

#     cherrypy.config.update({
#         'log.access_file': '',  # Disable CherryPy's default access log
#         # 'log.screen': False,    # Disable logging to the console
#     })

#     # Enable access logging
#     cherrypy.log.access_log = log

#     try:
#         cherrypy.engine.start()
#         cherrypy.engine.block()
#     except KeyboardInterrupt:
#         cherrypy.engine.stop()

#     log.info('server stopped...')
