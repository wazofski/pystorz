# REST Server
REST API Server that exposes Store functionality

## Usage
```
srv = rest.Server(model.Schema(), store_to_expose,
    rest.TypeMethods(model.WorldKind,
        rest.ActionGet, rest.ActionCreate,
        rest.ActionDelete, rest.ActionUpdate),
    rest.TypeMethods("AnotherWorld", rest.ActionGet))

srv.serve(host, port) # blocking
```
