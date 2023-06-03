from pystorz.store import options


class _HeaderOption(
    options.GetOption,
    options.CreateOption,
    options.UpdateOption,
    options.DeleteOption,
    options.ListOption,
):
    def __init__(self, function):
        self.function = function

    def ApplyFunction(self):
        return self.function

    def get_create_option(self) -> options.Option:
        return self

    def get_delete_option(self) -> options.Option:
        return self

    def get_get_option(self) -> options.Option:
        return self

    def get_update_option(self) -> options.Option:
        return self

    def get_list_option(self) -> options.Option:
        return self

    def get_header_option(self) -> options.Option:
        return self


def Header(key: str, val: str) -> _HeaderOption:
    def function(opts: options.OptionHolder):
        rest_opts = opts  # Assume that the `opts` argument is of type `RestOptions`
        if len(key.split(" ")) > 1:
            raise ValueError(f"invalid header name [{key}]")
        
        rest_opts.headers[key] = val

    return _HeaderOption(function)
