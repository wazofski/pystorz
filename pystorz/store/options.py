from typing import List, Optional
from pystorz.store import utils


class Option:
    def apply_function(self):
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
        raise NotImplementedError

    def ToJson(self):
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


class EqSetting(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class LtSetting(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class LteSetting(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class GtSetting(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class GteSetting(ListDeleteOption):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class AndSetting(ListDeleteOption):
    def __init__(self, *filters: List[ListDeleteOption]):
        self.filters = filters


class OrSetting(ListDeleteOption):
    def __init__(self, *filters: List[ListDeleteOption]):
        self.filters = filters


class NotSetting(ListDeleteOption):
    def __init__(self, flt: ListDeleteOption):
        self.filter = flt


class InSetting(ListDeleteOption):
    def __init__(self, key: str, values: List):
        self.key = key
        self.values = values


class CommonOptionHolder:
    def __init__(self):
        self.filter = None
        self.order_by = None
        self.order_incremental = None
        self.page_size = None
        self.page_offset = None

    def common_options(self) -> "CommonOptionHolder":
        return self


def CommonOptionHolderFactory() -> CommonOptionHolder:
    return CommonOptionHolder()


def And(*filters: List[ListDeleteOption]) -> ListDeleteOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = AndSetting(*filters)

    return _ListDeleteOption(option_function)


def Or(*filters: List[ListDeleteOption]) -> ListDeleteOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = OrSetting(*filters)

    return _ListDeleteOption(option_function)


def Not(filter: ListDeleteOption) -> ListDeleteOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = NotSetting(filter)

    return _ListDeleteOption(option_function)


def Eq(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = EqSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Lt(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = LtSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Gt(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = GtSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Lte(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = LteSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Gte(prop: str, val) -> ListDeleteOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = GteSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def In(key: str, *values: List) -> ListDeleteOption:
    if not key:
        raise Exception("empty key for in filter")
    
    if not values or len(values) == 0:
        raise Exception("empty values for in filter")

    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = InSetting(key, *values)

    return _ListDeleteOption(option_function)


def PageSize(ps: int) -> ListOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.page_size is not None and common_options.page_size > 0:
            raise Exception("page size option has already been set")

        common_options.page_size = ps
        # logging.info(f"pagination size option {ps}")

    return _ListOption(option_function)


def PageOffset(po: int) -> ListOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.page_offset is not None and common_options.page_offset > 0:
            raise Exception("page offset option has already been set")
        if common_options.page_offset is not None and common_options.page_offset < 0:
            raise Exception("page offset cannot be negative")

        common_options.page_offset = po

    return _ListOption(option_function)


class _ListDeleteOption(ListDeleteOption):
    def __init__(self, function):
        self.function = function

    def get_delete_option(self):
        return self

    def get_list_option(self):
        return self

    def ApplyFunction(self):
        return self.function


class _ListOption(ListOption):
    def __init__(self, function):
        self.function = function

    def get_list_option(self):
        return self

    def ApplyFunction(self):
        return self.function


def Order(field, ascending=True):
    def f(options):
        common_options = options.common_options()
        if common_options.order_by is None:
            common_options.order_by = field
            common_options.order_incremental = ascending
        else:
            raise Exception("order by option has already been set")

    return _ListOption(f)
