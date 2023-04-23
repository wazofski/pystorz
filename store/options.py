from typing import List, Optional
import logging


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


OptionFunction = callable[..., Optional[Exception]]


class PropFilterSetting:
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value


class KeyFilterSetting(List[str]):
    pass


class CommonOptionHolder:
    def __init__(self):
        self.prop_filter = None
        self.key_filter = None
        self.order_by = ""
        self.order_incremental = True
        self.page_size = 0
        self.page_offset = 0

    def common_options(self) -> 'CommonOptionHolder':
        return self


def common_option_holder_factory() -> CommonOptionHolder:
    return CommonOptionHolder()


def prop_filter(prop: str, val: str) -> ListOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.prop_filter is not None:
            return Exception("prop filter option already set")

        common_options.prop_filter = PropFilterSetting(key=prop, value=val)
        # opstr = json.dumps(common_options.prop_filter.__dict__)
        # logging.info(f"filter option {opstr}")
        return None

    return ListOption(option_function)


def key_filter(*keys: str) -> ListOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        if not keys:
            logging.info("ignoring empty key filter")
            return None

        common_options = options.common_options()
        if common_options.key_filter is not None:
            return Exception("key filter option already set")

        common_options.key_filter = KeyFilterSetting(keys)
        # opstr = json.dumps(common_options.key_filter.__dict__)
        # logging.info(f"filter option {opstr}")
        return None

    return ListOption(option_function)


def page_size(ps: int) -> ListOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.page_size > 0:
            return Exception("page size option has already been set")

        common_options.page_size = ps
        # logging.info(f"pagination size option {ps}")
        return None

    return ListOption(option_function)


def page_offset(po: int) -> ListOption:
    def option_function(options: OptionHolder) -> Optional[Exception]:
        common_options = options.common_options()
        if common_options.page_offset > 0:
            return Exception("page offset option has already been set")
        if common_options.page_offset < 0:
            return Exception("page offset cannot be negative")

        common_options.page_offset = po
        # logging.info(f"pagination offset option {po}")
        return None

    return ListOption(option_function)


class _ListOption(ListOption):
    def __init__(self, function):
        self.function = function
    
    def get_list_option(self):
        return self
    
    def apply_function(self):
        return self.function


def order_by(field):
    return _ListOption(
        lambda options: (
            setattr(options.common_options, 'order_by', field)
            if not options.common_options.order_by else
            ValueError('order by option has already been set')
        )
    )

def order_descending():
    return _ListOption(
        lambda options: (
            setattr(options.common_options, 'order_incremental', False)
            if options.common_options.order_incremental else
            ValueError('order incremental option has already been set')
        )
    )
