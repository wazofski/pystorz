from pystorz.rest import server

from pystorz.mgen import builder

builder.Generate("tests/model")

from generated import model
from pystorz.sql.store import SqliteStore, SqliteConnection
from generated.model import Schema

srv = server.Server(
    model.Schema(),
    SqliteStore(
        Schema(),
        SqliteConnection("testsqlite.db")),
    server.Expose(
        model.WorldKind,
        server.ActionGet,
        server.ActionCreate,
        server.ActionUpdate,
        server.ActionDelete),
)

host = "localhost"
port = 8080
url = f"{host}:{port}"

srv.Serve(host, port)
srv.Join()
