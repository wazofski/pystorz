from typing import List, Optional
import logging
from pystorz.store import utils


class Option:
    def apply_function(self):
        raise NotImplementedError


class CreateOption(Option):
    def get_create_option(self) -> Option:
        raise NotImplementedError


class DeleteOption(Option):
    def get_delete_option(self) -> Option:
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


class OptionHolder:
    def common_options(self):
        raise NotImplementedError


class PropFilterSetting:
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value
        if isinstance(self.value, str):
            self.value = "'{}'".format(utils.encode_string(self.value))


class KeyFilterSetting(List[str]):
    pass


class CommonOptionHolder:
    def __init__(self):
        self.prop_filter = None
        self.key_filter = None
        self.order_by = None
        self.order_incremental = None
        self.page_size = None
        self.page_offset = None

    def common_options(self) -> "CommonOptionHolder":
        return self


def CommonOptionHolderFactory() -> CommonOptionHolder:
    return CommonOptionHolder()


def PropFilter(prop: str, val: str) -> ListOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.prop_filter is not None:
            raise Exception("prop filter option already set")

        common_options.prop_filter = PropFilterSetting(key=prop, value=val)
        # opstr = json.dumps(common_options.prop_filter.__dict__)
        # logging.info(f"filter option {opstr}")

    return _ListOption(option_function)


def KeyFilter(*keys: str) -> ListOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        if not keys:
            logging.info("ignoring empty key filter")
            return

        common_options = options.common_options()
        if common_options.key_filter is not None:
            raise Exception("key filter option already set")

        common_options.key_filter = KeyFilterSetting(keys)
        # opstr = json.dumps(common_options.key_filter.__dict__)
        # logging.info(f"filter option {opstr}")

    return _ListOption(option_function)


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


class _ListOption(ListOption):
    def __init__(self, function):
        self.function = function

    def get_list_option(self):
        return self

    def ApplyFunction(self):
        return self.function


def OrderBy(field):
    def f(options):
        common_options = options.common_options()
        if common_options.order_by is None:
            common_options.order_by = field
        else:
            raise Exception("order by option has already been set")

    return _ListOption(f)


def OrderDescending():
    def f(options):
        common_options = options.common_options()
        if common_options.order_incremental is None:
            common_options.order_incremental = False
        else:
            raise Exception("order incremental option has already been set")

    return _ListOption(f)
