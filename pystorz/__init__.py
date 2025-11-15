"""
pystorz package - re-export public API

This file demonstrates how to make classes and functions from submodules
importable directly from the top-level package.

Examples:
    Instead of: from pystorz.submodule.nested import MyClass
    You can do: from pystorz import MyClass
"""

# ABSTRACT
from pystorz.store.store import Store

# OPTIONS
from pystorz.store.options import (
    Eq, Gt, Gte, Lt, Lte,
    In,
    And, Or, Not,
    PageOffset, PageSize,
    Order
)

# CODE GENERATION
from pystorz.mgen.generator import Generate

# REST
from pystorz.rest.client import Client as RESTClient
from pystorz.rest.server import Server as RESTServer

# BROWSER
from pystorz.browse.server import Server as BrowseServer

# FUNCTIONAL
from pystorz.router.store import RouterStore
from pystorz.meta.store import MetaStore

# SQL
from pystorz.sql.sqlite import SqliteStoreFactory
from pystorz.sql.mysql import MySqlStoreFactory as MySQLStoreFactory

# MONGO
from pystorz.mongo.mongo import MongoStoreFactory


# Define __all__ to explicitly declare what's exported
__all__ = [
    "Store",
    "Eq", "Gt", "Gte", "Lt", "Lte",
    "In",
    "And", "Or", "Not",
    "PageOffset", "PageSize",
    "Order",
    "Generate",
    "RESTClient", "RESTServer",
    "BrowseServer",
    "RouterStore", "MetaStore",
    "SqliteStoreFactory", "MySQLStoreFactory",
    "MongoStoreFactory"
]
