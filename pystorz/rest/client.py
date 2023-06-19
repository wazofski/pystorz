import json
import json
import uuid
import logging
import requests

from pystorz.rest import server, headers
from pystorz.store import store, utils, options
from pystorz.internal import constants

# from urllib.parse import urljoin, urlunparse, urlencode
from urllib.parse import quote, urlparse


log = logging.getLogger(__name__)


class RestOptions(options.CommonOptionHolder):
    def __init__(self):
        super().__init__()
        self.headers = {}

    def common_options(self) -> options.CommonOptionHolder:
        return self


def new_rest_options(d):
    res = RestOptions()
    res.headers = {}

    for h in d.headers:
        h.ApplyFunction()(res)

    return res


# def make_http_request(path, content, request_type, headers):
#     requests.packages.urllib3.disable_warnings()  # Disable SSL verification warning

#     req = requests.Request(request_type, path, data=content)

#     for k, v in headers.items():
#         req.headers[k] = v

#     with requests.Session() as session:
#         resp = session.send(req.prepare(), verify=False)

#         rd = resp.content

#         if resp.status_code < 200 or resp.status_code >= 300:
#             return rd, f"http {resp.status_code}"

#         return rd, None


def error_check(response):
    if len(response) == 0:
        return

    data = json.loads(response)
    if "errors" in data:
        raise Exception(data["errors"][0])

    if "error" in data:
        raise Exception(data["error"])


def make_path_for_type(base_url, obj):
    return "{}/{}".format(base_url, obj.Metadata().Kind().lower())


def remove_trailing_slash(val):
    if val.endswith("/"):
        return val[:-1]
    return val


def make_path_for_identity(base_url, identity, params):
    if len(params) > 0:
        return f"{base_url}/{remove_trailing_slash(identity.Path().lower())}?{params}"

    return f"{base_url}/{identity.Path().lower()}"


def list_parameters(ropt):
    opt = ropt.common_options()

    q = {}
    if opt.order_by:
        q[server.OrderByArg] = opt.order_by
        q[server.IncrementalArg] = str(opt.order_incremental).lower()

    if opt.page_offset and opt.page_offset > 0:
        q[server.PageOffsetArg] = str(opt.page_offset)

    if opt.page_size and opt.page_size > 0:
        q[server.PageSizeArg] = str(opt.page_size)

    # if opt.filter:
    #     q[server.FilterArg] = opt.filter.ToJson()

    return "&".join([f"{k}={quote(v)}" for k, v in q.items()])


def filter_parameter(ropt):
    opt = ropt.common_options()
    if opt.filter:
        return opt.filter.ToJson()

    return ""


def strip_serialize(object):
    data = object.ToDict()
    res = {}
    if "external" in data:
        res["external"] = data["external"]
    if "metadata" in data:
        res["metadata"] = data["metadata"]
    
    return json.dumps(res)


class Client(store.Store):
    def __init__(self, base_url, schema, *header_options: list[headers._HeaderOption]):
        self.base_url = base_url
        self.schema = schema
        self.headers = header_options

    def Create(self, obj: store.Object, *opt: options.CreateOption) -> store.Object:
        if obj is None:
            raise ValueError(constants.ErrObjectNil)

        log.info("get {}".format(obj.Metadata().Identity().Path()))

        copt = new_rest_options(self)
        for o in opt:
            o.ApplyFunction()(copt)

        data = self._process_request(
            make_path_for_type(self.base_url, obj),
            strip_serialize(obj),
            server.ActionCreate,
            copt.headers,
        )

        clone = obj.Clone()
        clone.FromJson(data)

        return clone

    def Get(self, identity: store.ObjectIdentity, *opt: options.GetOption) -> store.Object:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        log.info("get {}".format(identity.Path()))

        copt = new_rest_options(self)
        for o in opt:
            o.ApplyFunction()(copt)

        resp = self._process_request(
            make_path_for_identity(self.base_url, identity, ""),
            b"",
            server.ActionGet,
            copt.headers,
        )

        tp = identity.Type()
        if tp == "id":
            tp = utils.object_kind(json.loads(resp))

        return utils.unmarshal_object(resp, self.schema, tp)

    def Update(self, identity: store.ObjectIdentity, obj: store.Object, *opt: options.UpdateOption) -> store.Object:
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        
        log.info("update {}".format(identity.Path()))

        copt = new_rest_options(self)
        for o in opt:
            o.ApplyFunction()(copt)
        
        # if identity.Type() != obj.Metadata().Kind():
        #     log.debug("identity type: {}, object type: {}".format(
        #         identity.Type(),
        #         obj.Metadata().Kind()))
        #     raise Exception(constants.ErrObjectIdentityMismatch)

        data = self._process_request(
            make_path_for_identity(self.base_url, identity, ""),
            strip_serialize(obj),
            server.ActionUpdate,
            copt.headers,
        )

        clone = obj.Clone()
        clone.FromJson(data)

        return clone

    def Delete(self, identity: store.ObjectIdentity, *opt: options.DeleteOption):
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        
        log.info("delete {}".format(identity.Path()))

        copt = new_rest_options(self)
        for o in opt:
            o.ApplyFunction()(copt)

        params = list_parameters(copt)
        body = filter_parameter(copt)
        path = make_path_for_identity(self.base_url, identity, params)

        res = self._process_request(
            path,
            body,
            server.ActionDelete,
            copt.headers,
        )

        if res and len(res) > 0:
            log.debug("delete response: {}".format(res))

        return None

    def List(self, identity: store.ObjectIdentity, *opt: options.ListOption) -> store.ObjectList:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        if len(identity.Key()) > 0:
            raise Exception(constants.ErrInvalidPath)

        log.info("list {}".format(identity.Path()))

        copt = new_rest_options(self)
        for o in opt:
            o.ApplyFunction()(copt)

        params = list_parameters(copt)
        body = filter_parameter(copt)

        path = make_path_for_identity(self.base_url, identity, params)
        res = self._process_request(path, body, server.ActionGet, copt.headers)

        parsed = json.loads(res)

        marshalledResult = store.ObjectList()
        if len(parsed) == 0:
            return marshalledResult

        resource = self.schema.ObjectForKind(
            utils.object_kind(parsed[0]))

        for r in parsed:
            clone = resource.Clone()
            clone.FromDict(r)

            marshalledResult.append(clone)

        return marshalledResult

    def _make_request(self, path, content, request_type, headers):
        # headers.update(self.headers)
        log.debug(f"making {request_type} request to {path}")

        response = requests.request(
            request_type, path, data=content, headers=headers
        )

        # response.raise_for_status()

        return response.content
        # return str(response.content)

    def _process_request(self, request_url, content, method, headers):
        req_id = str(uuid.uuid4())

        request_url = request_url.lower()
        url = urlparse(request_url)
        path = url.path
        new_path = path.replace("//", "/")
        request_url = request_url.replace(path, new_path)

        headers["Origin"] = request_url.replace(url.path, "").replace(url.query, "")
        headers["X-Request-ID"] = req_id
        headers["Content-Type"] = "application/json"
        headers["X-Requested-With"] = "XMLHttpRequest"

        data = self._make_request(request_url, content, method, headers)
        try:
            error_check(data)
        except Exception as err:
            if len(content) > 0:
                try:
                    js = json.loads(content)
                    log.info("request content: %s", json.dumps(js))
                except ValueError:
                    log.info("request content: %s", content)

            if len(data) > 0:
                log.info("response content: %s", data)

            raise err

        return data
