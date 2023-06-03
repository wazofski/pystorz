import time
import logging
import requests

from config import globals

globals.logger_config()

log = logging.getLogger(__name__)

from pystorz.store import store
from pystorz.rest import server
from generated import model

def test_server_can_start():
    srv = server.Server(
        model.Schema(),
        store.Store(), # mock store
        server.Expose(
            model.WorldKind,
            server.ActionGet,
            server.ActionCreate,
            server.ActionUpdate,
            server.ActionDelete),
    )

    host = "http://localhost"
    port = 8080
    url = f"{host}:{port}"

    client = client.Client(url, model.Schema())
    srv.serve(host, port)
    time.sleep(3)


def test_sample_request():
    # make an http request to localhost:8080

    response = requests.request(
        "GET",
        "http://localhost:8080/worlds",
        "",
        headers={})

    assert response is not None
    assert response.status_code == 200
