# REST Server
REST API Server that exposes Store functionality

## Usage
```
from pystorz.rest import server, client

srv = server.Server(
    model.Schema(),
    store_to_expose,
    server.Expose(
        model.WorldKind,
        server.ActionCreate,
        server.ActionGet,
        server.ActionDelete),
    server.Expose(
        model.AnotherWorldKind,
        server.ActionCreate,
        server.ActionGet),
    )

srv.serve(host, port) # blocking

# client Store
client = client.Client(
    url,
    model.Schema(),
    headers={
        "Content-Type": "application/json",
    })
```
