import json
from pystorz.store import utils


class Option:
    def ApplyFunction(self):
        raise NotImplementedError


class CreateOption(Option):
    def get_create_option(self) -> Option:
        raise NotImplementedError


class GetOption(Option):
    def get_get_option(self) -> Option:
        raise NotImplementedError


class UpdateOption(Option):
    def get_update_option(self) -> Option:
        raise NotImplementedError


class ListOption(Option):
    def get_list_option(self) -> Option:
        raise NotImplementedError


class DeleteOption(Option):
    def get_delete_option(self) -> Option:
        raise NotImplementedError


class ListDeleteOption(ListOption, DeleteOption):
    @staticmethod
    def FromJson(jsn):
        data = json.loads(jsn)

        if data["type"] == "in":
            return InSetting(data["key"], data["values"])
        elif data["type"] == "eq":
            return EqSetting(data["key"], data["value"])
        elif data["type"] == "lt":
            return LtSetting(data["key"], data["value"])
        elif data["type"] == "lte":
            return LteSetting(data["key"], data["value"])
        elif data["type"] == "gt":
            return GtSetting(data["key"], data["value"])
        elif data["type"] == "gte":
            return GteSetting(data["key"], data["value"])
        elif data["type"] == "and":
            return AndSetting(*[ListDeleteOption.FromJson(f) for f in data["filters"]])
        elif data["type"] == "or":
            return OrSetting(*[ListDeleteOption.FromJson(f) for f in data["filters"]])
        elif data["type"] == "not":
            return NotSetting(ListDeleteOption.FromJson(data["filter"]))
        else:
            raise ValueError("Unknown type: {}".format(data["type"]))

    def ToJson(self):
        return json.dumps(self.ToDict())

    def ToDict(self):
        raise NotImplementedError


class OptionHolder:
    def common_options(self):
        raise NotImplementedError


class InOption(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))

    def ToDict(self):
        return {"type": "in", "key": self.key, "value": self.value}


class EqSetting(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))

    def ToDict(self):
        return {"type": "eq", "key": self.key, "value": self.value}


class LtSetting(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))

    def ToDict(self):
        return {"type": "lt", "key": self.key, "value": self.value}


class LteSetting(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))

    def ToDict(self):
        return {"type": "lte", "key": self.key, "value": self.value}


class GtSetting(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))

    def ToDict(self):
        return {"type": "gt", "key": self.key, "value": self.value}


class GteSetting(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))

    def ToDict(self):
        return {"type": "gte", "key": self.key, "value": self.value}


class AndSetting(ListDeleteOption):
    def __init__(self, *filters: list[ListDeleteOption]):
        self.filters = filters

    def ToDict(self):
        return {"type": "and", "filters": [f.ToDict() for f in self.filters]}


class OrSetting(ListDeleteOption):
    def __init__(self, *filters: list[ListDeleteOption]):
        self.filters = filters

    def ToDict(self):
        return {"type": "or", "filters": [f.ToDict() for f in self.filters]}


class NotSetting(ListDeleteOption):
    def __init__(self, flt: ListDeleteOption):
        self.filter = flt

    def ToDict(self):
        return {"type": "not", "filter": self.filter.ToDict() }


class InSetting(ListDeleteOption):
    def __init__(self, key: str, values: list):
        self.key = key
        self.values = values

    def ToDict(self):
        return {"type": "in", "key": self.key, "values": self.values}


class CommonOptionHolder:
    def __init__(self):
        self.filter = None
        self.order_by = None
        self.order_incremental = None
        self.page_size = None
        self.page_offset = None

    def common_options(self):
        return self


def CommonOptionHolderFactory() -> CommonOptionHolder:
    return CommonOptionHolder()


def And(*filters: list[ListDeleteOption]) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = AndSetting(*filters)

    return _ListDeleteOption(option_function)


def Or(*filters: list[ListDeleteOption]) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = OrSetting(*filters)

    return _ListDeleteOption(option_function)


def Not(filter: ListDeleteOption) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = NotSetting(filter)

    return _ListDeleteOption(option_function)


def Eq(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = EqSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Lt(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = LtSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Gt(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = GtSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Lte(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = LteSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Gte(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = GteSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def In(key: str, *values: list) -> ListDeleteOption:
    if not key or len(key) == 0:
        raise Exception("empty key for in filter")

    if not values or len(values) == 0:
        raise Exception("empty values for in filter")

    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = InSetting(key, *values)

    return _ListDeleteOption(option_function)


def PageSize(ps: int) -> ListOption:
    if ps < 0:
        raise Exception("page size cannot be negative")
    
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.page_size is not None:
            raise Exception("page size option has already been set")

        common_options.page_size = ps
        # logging.info(f"pagination size option {ps}")

    return _ListOption(option_function)


def PageOffset(po: int) -> ListOption:
    if po < 0:
        raise Exception("page offset cannot be negative")
    
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.page_offset is not None:
            raise Exception("page offset option has already been set")
        
        common_options.page_offset = po

    return _ListOption(option_function)


class _ListDeleteOption(ListDeleteOption):
    def __init__(self, function):
        self.function = function

    def get_delete_option(self):
        return self

    def get_list_option(self):
        return self


class _ListOption(ListOption):
    def __init__(self, function):
        self.function = function

    def get_list_option(self):
        return self


def Order(field, ascending=True):
    def f(options):
        common_options = options.common_options()
        if common_options.order_by is None:
            common_options.order_by = field
            common_options.order_incremental = ascending
        else:
            raise Exception("order by option has already been set")

    return _ListOption(f)
