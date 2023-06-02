import json
import json
import uuid
import logging
import requests

from pystorz.rest import server
from pystorz.store import store, utils, options
from pystorz.internal import constants

from urllib.parse import urlparse, urljoin, urlunparse, urlencode


log = logging.getLogger(__name__)


class RestOptions:
    def __init__(self):
        self.common_option_holder = options.CommonOptionHolderFactory()
        self.headers = {}

    def common_options(self):
        return self.common_option_holder


def new_rest_options(d):
    res = RestOptions()
    res.headers = {}

    for h in d.headers:
        h.apply_function()(res)

    return res


def make_http_request(path, content, request_type, headers):
    requests.packages.urllib3.disable_warnings()  # Disable SSL verification warning

    url = urlunparse(path)

    req = requests.Request(request_type, url, data=content)

    for k, v in headers.items():
        req.headers[k] = v

    with requests.Session() as session:
        resp = session.send(req.prepare(), verify=False)

        rd = resp.content

        if resp.status_code < 200 or resp.status_code >= 300:
            return rd, f"http {resp.status_code}"

        return rd, None


def error_check(response):
    if len(response) == 0:
        return

    um = {}

    err = json.loads(response, object_hook=lambda d: um.update(d))
    if err is None:
        if "errors" in um:
            raise ValueError(um["errors"][0])

        if "error" in um:
            m = um["error"]
            raise Exception(f"{m['internal_code']} {m['internal']}")


def make_path_for_type(base_url, obj):
    u = urljoin(base_url, obj.Metadata().Kind().lower())
    return u


def remove_trailing_slash(val):
    if val.endswith("/"):
        return val[:-1]
    return val


def make_path_for_identity(base_url, identity, params):
    if len(params) > 0:
        path = f"{base_url}/{remove_trailing_slash(identity.Path())}?{params}"
        u = urlparse(path)
        return u

    u = urljoin(base_url, identity.Path())
    return u


def to_bytes(obj):
    if obj is None:
        return b""

    jsn = json.dumps(obj)
    return jsn.encode("utf-8")


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

    if opt.filter:
        q[server.FilterArg] = opt.filter.ToJson()

    return urlencode(q)



import json


class StrippedObject:
    def __init__(self):
        self.External = {}


def strip_serialize(object):
    data = object.ToDict()
    for k, v in data.items():
        if k != "external":
            del data[k]

    return json.dumps(data)


class Client(store.Store):
    
    def __init__(self, base_url, schema, *header_options):
        self.base_url = urlparse(base_url)
        self.schema = schema
        self.headers = header_options

    def Create(self, obj, *opt):
        if obj is None:
            raise ValueError(constants.ErrObjectNil)

        log.info("get {}".format(obj.metadata().identity().path()))

        copt = new_rest_options(self)
        for o in opt:
            o.apply_function()(copt)

        data = self._process_request(
            make_path_for_type(self.base_url, obj),
            strip_serialize(obj),
            server.ActionCreate,
            copt.headers,
        )

        clone = obj.clone()
        clone.FromJson(data)
        
        return clone

    def Get(self, identity, *opt):
        log.info("get {}".format(identity.path()))

        copt = new_rest_options(self)
        for o in opt:
            o.apply_function()(copt)

        resp = self._process_request(
            make_path_for_identity(self.base_url, identity, ""),
            b"",
            server.ActionGet,
            copt.headers,
        )

        tp = identity.type()
        if tp == "id":
            tp = utils.object_kind(resp)

        return utils.unmarshal_object(resp, self.schema, tp)


    def Update(self, identity, obj, *opt):
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info("update {}".format(identity.path()))

        copt = new_rest_options(self)
        for o in opt:
            o.apply_function()(copt)
        
        data = self._process_request(
            make_path_for_identity(self.base_url, identity, ""),
            strip_serialize(obj),
            server.ActionUpdate,
            copt.headers,
        )

        clone = obj.clone()
        clone.FromJson(data)
        
        return clone

    def Delete(self, identity, *opt):
        log.info("delete {}".format(identity.path()))

        copt = new_rest_options(self)
        for o in opt:
            o.apply_function()(copt)

        self._process_request(
            make_path_for_identity(self.base_url, identity, ""),
            "",
            server.ActionDelete,
            copt.headers,
        )


    def List(self, identity, *opt):
        log.info("list {}".format(identity))

        copt = new_rest_options(self)
        for o in opt:
            o.ApplyFunction()(copt)

        params = list_parameters(copt)
        path = make_path_for_identity(self.base_url, identity, params)
        res = self._process_request(path, "", server.ActionGet, copt.headers)

        parsed = json.loads(res)

        marshalledResult = store.ObjectList()
        if len(parsed) == 0:
            return marshalledResult

        resource = self.schema.ObjectForKind(utils.ObjectKind(parsed[0]))

        for r in parsed:
            clone = resource.Clone()
            clone.FromDict(r)

            marshalledResult.append(clone)

        return marshalledResult


    def _make_request(self, path, content, request_type, headers):
        url = urljoin(self.base_url.geturl(), path)
        headers.update(self.headers)
        response = requests.request(request_type, url, data=content, headers=headers)
        response.raise_for_status()

        return response.content


    def _process_request(self, request_url, content, method, headers):
        req_id = str(uuid.uuid4())
        request_url.path = request_url.path.replace("//", "/")
        origin = request_url.geturl().replace(request_url.path, "")
        headers["Origin"] = origin.replace(request_url.query, "")
        headers["X-Request-ID"] = req_id
        headers["Content-Type"] = "application/json"
        headers["X-Requested-With"] = "XMLHttpRequest"

        log.info(f"{method.lower()} {request_url.geturl()}")

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
                log.info("response content: %s", data.decode("utf-8"))

            raise err

        return data
