import json
import logging


log = logging.getLogger(__name__)

from typing import Callable


class CommonOptionHolder:
    def __init__(self):
        self.filter = None
        self.order_by = None
        self.order_incremental = None
        self.page_size = None
        self.page_offset = None

    def common_options(self):
        return self


class Option:
    def ApplyFunction(self) -> Callable[[CommonOptionHolder], None]:
        raise NotImplementedError
    
    def ToJson(self) -> str:
        raise NotImplementedError

    def ToDict(self) -> dict:
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
        log.debug("parsing listdeleteoption: {}".format(jsn))

        data = jsn
        if isinstance(jsn, str):
            data = json.loads(jsn)

        if data["type"] == "in":
            return In(data["key"], data["values"])
        elif data["type"] == "eq":
            return Eq(data["key"], data["value"])
        elif data["type"] == "lt":
            return Lt(data["key"], data["value"])
        elif data["type"] == "lte":
            return Lte(data["key"], data["value"])
        elif data["type"] == "gt":
            return Gt(data["key"], data["value"])
        elif data["type"] == "gte":
            return Gte(data["key"], data["value"])
        elif data["type"] == "and":
            return And(*[ListDeleteOption.FromJson(f) for f in data["filters"]])
        elif data["type"] == "or":
            return Or(*[ListDeleteOption.FromJson(f) for f in data["filters"]])
        elif data["type"] == "not":
            return Not(ListDeleteOption.FromJson(data["filter"]))
        else:
            raise ValueError("Unknown type: {}".format(data["type"]))

    def ToJson(self) -> str:
        return json.dumps(self.ToDict())

    def ToDict(self) -> dict:
        copt = CommonOptionHolderFactory()
        self.ApplyFunction()(copt)
        if isinstance(copt.filter, Option):
            return copt.filter.ToDict()
        return {}

    def __str__(self) -> str:
        copt = CommonOptionHolderFactory()
        self.ApplyFunction()(copt)
        return str(copt.filter)
    

class OptionHolder:
    def common_options(self):
        raise NotImplementedError


class EqOption(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
    
    def ToDict(self):
        return {"type": "eq", "key": self.key, "value": self.value}

    def __str__(self):
        return "{} = {}".format(self.key, self.value)
    

class LtOption(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    def ToDict(self):
        return {"type": "lt", "key": self.key, "value": self.value}

    def __str__(self):
        return "{} < {}".format(self.key, self.value)


class LteOption(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    def ToDict(self):
        return {"type": "lte", "key": self.key, "value": self.value}

    def __str__(self):
        return "{} <= {}".format(self.key, self.value)


class GtOption(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
    
    def ToDict(self):
        return {"type": "gt", "key": self.key, "value": self.value}

    def __str__(self):
        return "{} > {}".format(self.key, self.value)


class GteOption(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        
    def ToDict(self):
        return {"type": "gte", "key": self.key, "value": self.value}

    def __str__(self):
        return "{} >= {}".format(self.key, self.value)


class AndOption(ListDeleteOption):
    def __init__(self, *filters: ListDeleteOption):
        self.filters = filters

    def ToDict(self):
        return {"type": "and", "filters": [f.ToDict() for f in self.filters]}

    def __str__(self):
        return "( {} )".format(
            " AND ".join([str(f) for f in self.filters]))


class OrOption(ListDeleteOption):
    def __init__(self, *filters: ListDeleteOption):
        self.filters = filters

    def ToDict(self):
        return {"type": "or", "filters": [f.ToDict() for f in self.filters]}

    def __str__(self):
        return "( {} )".format(
            " OR ".join([str(f) for f in self.filters]))


class NotOption(ListDeleteOption):
    def __init__(self, flt: ListDeleteOption):
        self.filter = flt

    def ToDict(self):
        return {"type": "not", "filter": self.filter.ToDict()}

    def __str__(self):
        return "( NOT {} )".format(self.filter)


class InOption(ListDeleteOption):
    def __init__(self, key: str, values: list):
        self.key = key
        self.values = values

    def ToDict(self):
        return {"type": "in", "key": self.key, "values": self.values}

    def __str__(self):
        return "({} IN ({}))".format(
            self.key, ", ".join([str(v) for v in self.values]))


def CommonOptionHolderFactory() -> CommonOptionHolder:
    return CommonOptionHolder()


class _ListDeleteOption(ListDeleteOption):
    def __init__(self, function):
        self.function = function

    def get_delete_option(self):
        return self

    def get_list_option(self):
        return self

    def ApplyFunction(self):
        return self.function


def And(*filters: ListDeleteOption) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = AndOption(*filters)

    return _ListDeleteOption(option_function)


def Or(*filters: ListDeleteOption) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = OrOption(*filters)

    return _ListDeleteOption(option_function)


def Not(filter: ListDeleteOption) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = NotOption(filter)

    return _ListDeleteOption(option_function)


def Eq(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = EqOption(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Lt(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = LtOption(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Gt(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = GtOption(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Lte(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = LteOption(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Gte(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = GteOption(key=prop, value=val)

    return _ListDeleteOption(option_function)


def In(key: str, values: list) -> ListDeleteOption:
    if not key or len(key) == 0:
        raise Exception("empty key for in filter")

    if not values or len(values) == 0:
        raise Exception("empty values for in filter")

    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = InOption(key, values)

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

    return _ListDeleteOption(option_function)


def PageOffset(po: int) -> ListOption:
    if po < 0:
        raise Exception("page offset cannot be negative")

    def option_function(options: OptionHolder):
        common_options = options.common_options()
        if common_options.page_offset is not None:
            raise Exception("page offset option has already been set")

        common_options.page_offset = po

    return _ListDeleteOption(option_function)


def Order(field, ascending=True):
    def f(options):
        common_options = options.common_options()
        if common_options.order_by is None:
            common_options.order_by = field
            common_options.order_incremental = ascending
        else:
            raise Exception("order by option has already been set")

    return _ListDeleteOption(f)
