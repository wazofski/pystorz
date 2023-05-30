from typing import List, Optional
import logging
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


class OptionHolder:
    def common_options(self):
        raise NotImplementedError


class KeyFilterSetting(List[str]):
    pass


class ExpSetting:
    def __init__(self):
        raise NotImplementedError


class EqSetting(ExpSetting):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class LtSetting(ExpSetting):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class LteSetting(ExpSetting):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class GtSetting(ExpSetting):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class GteSetting(ExpSetting):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class AndSetting(ExpSetting):
    def __init__(self, *filters: List[ExpSetting]):
        self.filters = filters


class OrSetting(ExpSetting):
    def __init__(self, *filters: List[ExpSetting]):
        self.filters = filters


class NotSetting(ExpSetting):
    def __init__(self, flt: ExpSetting):
        self.filter = flt


class CommonOptionHolder:
    def __init__(self):
        self.filter = None
        self.key_filter = None
        self.order_by = None
        self.order_incremental = None
        self.page_size = None
        self.page_offset = None

    def common_options(self) -> "CommonOptionHolder":
        return self


def CommonOptionHolderFactory() -> CommonOptionHolder:
    return CommonOptionHolder()


def And(*filters: List[ExpSetting]):
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = AndSetting(*filters)

    return _ListDeleteOption(option_function)


def Or(*filters: List[ExpSetting]):
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = OrSetting(*filters)

    return _ListDeleteOption(option_function)


def Not(filter: ExpSetting):
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = NotSetting(filter)

    return _ListDeleteOption(option_function)


def Eq(prop: str, val):
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = EqSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Lt(prop: str, val):
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = LtSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Gt(prop: str, val):
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = GtSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Lte(prop: str, val):
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = LteSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def Gte(prop: str, val):
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.filter is not None:
            raise Exception("prop filter option already set")

        common_options.filter = GteSetting(key=prop, value=val)

    return _ListDeleteOption(option_function)


def KeyFilter(*keys):
    def option_function(options: OptionHolder) -> Optional[Exception]:
        if not keys:
            logging.info("ignoring empty key filter")
            return

        common_options = options.common_options()
        if common_options.key_filter is not None:
            raise Exception("key filter option already set")

        common_options.key_filter = KeyFilterSetting(keys)

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
        # logging.info(f"pagination offset option {po}")

    return _ListOption(option_function)


class _ListDeleteOption(ListOption, DeleteOption):
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
