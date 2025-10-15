import logging
from pymongo import MongoClient, ASCENDING, DESCENDING

from pystorz.internal import constants
from pystorz.store import store, options, utils


log = logging.getLogger(__name__)

COLLECTION_NAME = "objects"
DATABASE_NAME = "pystorz"
TIMEOUT = 10  # seconds


def _convert_filter(filterOption, sample):
    if isinstance(filterOption, options._ListDeleteOption):
        copt = options.CommonOptionHolderFactory()
        filterOption.ApplyFunction()(copt)
        filterOption = copt.filter

    if isinstance(filterOption, options.AndOption):
        return {"$and": [_convert_filter(f, sample) for f in filterOption.filters]}

    if isinstance(filterOption, options.OrOption):
        return {"$or": [_convert_filter(f, sample) for f in filterOption.filters]}

    if isinstance(filterOption, options.NotOption):
        return {"$nor": [_convert_filter(filterOption.filter, sample)]}

    if utils.object_path(sample, filterOption.key) is None:
        raise Exception(constants.ErrInvalidFilter)

    def convert_value(v):
        # return "'{}'".format(v)
        if isinstance(v, str):
            return utils.encode_string(v)
        return v

    if isinstance(filterOption, options.InOption):
        return {
            f"object.{filterOption.key}": {
                "$in": [convert_value(v) for v in filterOption.values]
            }
        }

    if isinstance(filterOption, options.EqOption):
        return {f"object.{filterOption.key}": filterOption.value}

    if isinstance(filterOption, options.LtOption):
        return {f"object.{filterOption.key}": {"$lt": filterOption.value}}

    if isinstance(filterOption, options.GtOption):
        return {f"object.{filterOption.key}": {"$gt": filterOption.value}}

    if isinstance(filterOption, options.LteOption):
        return {f"object.{filterOption.key}": {"$lte": filterOption.value}}

    if isinstance(filterOption, options.GteOption):
        return {f"object.{filterOption.key}": {"$gte": filterOption.value}}

    raise Exception(constants.ErrInvalidFilter)


class MongoStore(store.Store):
    def __init__(self, Schema, URI: str):
        self._schema = Schema
        self._URI = URI
        self._client = None
        self._db = DATABASE_NAME
        self._test_connection()

    def _test_connection(self):
        if self._client is not None:
            try:
                self._client.admin.command("ping")
                return
            except Exception:
                pass
        self._client = MongoClient(self._URI, serverSelectionTimeoutMS=TIMEOUT * 1000)
        self._client.admin.command("ping")
        self._prepare()

    def _prepare(self):
        collection = self._client[self._db][COLLECTION_NAME]
        collection.create_index([("idpath", ASCENDING)])
        collection.create_index([("pkpath", ASCENDING)])
        collection.create_index([("type", ASCENDING)])

    def Create(self, obj: store.Object, *opt: options.CreateOption) -> store.Object:
        if obj is None:
            raise Exception(constants.ErrObjectNil)
        log.info(f"create {obj.Metadata().Kind()} {obj.PrimaryKey()}")
        lk = obj.Metadata().Kind().lower()
        path = f"{lk}/{obj.PrimaryKey()}"
        existing = None
        try:
            existing = self.Get(store.ObjectIdentity(path))
        except Exception:
            pass
        if existing is not None:
            raise Exception(constants.ErrObjectExists)
        self._test_connection()
        typ = obj.Metadata().Kind().lower()
        collection = self._client[self._db][COLLECTION_NAME]
        record = {
            "idpath": obj.Metadata().Identity().Path(),
            "pkpath": f"{typ}/{obj.PrimaryKey()}",
            "pkey": obj.PrimaryKey(),
            "type": typ,
            "object": obj.ToDict(),
        }
        collection.insert_one(record)
        return obj.Clone()

    def Update(
        self,
        identity: store.ObjectIdentity,
        obj: store.Object,
        *opt: options.UpdateOption,
    ) -> store.Object:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        if obj is None:
            raise Exception(constants.ErrObjectNil)
        log.info(f"update {identity.Path()}")
        existing = self.Get(identity)
        if existing.Metadata().Kind() != obj.Metadata().Kind():
            raise Exception(constants.ErrObjectIdentityMismatch)
        if existing.PrimaryKey() != obj.PrimaryKey():
            if (
                existing.Metadata().Identity().Path()
                != obj.Metadata().Identity().Path()
            ):
                raise Exception(constants.ErrObjectIdentityMismatch)
            target_identity = store.ObjectIdentity(
                f"{existing.Metadata().Kind().lower()}/{obj.PrimaryKey()}"
            )
            target = None
            try:
                target = self.Get(target_identity)
            except Exception:
                pass
            if target is not None:
                raise Exception(constants.ErrObjectExists)
        self._test_connection()
        self.Delete(identity)
        return self.Create(obj)

    def Delete(self, identity: store.ObjectIdentity, *opt: options.DeleteOption):
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        log.info(f"delete {identity.Path()}")
        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)
        self._test_connection()
        collection = self._client[self._db][COLLECTION_NAME]
        if copt.filter is None:
            if self.Get(identity) is None:
                raise Exception(constants.ErrNoSuchObject)
            if identity.IsId():
                collection.delete_many({"idpath": identity.Path()})
            else:
                collection.delete_many({"pkpath": identity.Path()})
        else:
            obj = self._schema.ObjectForKind(identity.Type())
            if obj is None:
                raise Exception(constants.ErrNoSuchObject)

            filter_ = {
                "$and": [{"type": identity.Type()},
                         _convert_filter(copt.filter, obj)]
            }
            
            log.info(f"filter: {filter_}")
            collection.delete_many(filter_)

    def Get(
        self, identity: store.ObjectIdentity, *opt: options.GetOption
    ) -> store.Object:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        log.info(f"get {identity.Path()}")
        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)
        self._test_connection()
        collection = self._client[self._db][COLLECTION_NAME]
        res = None
        key = "idpath" if identity.IsId() else "pkpath"
        res = collection.find_one({key: identity.Path()})

        if res is None:
            raise Exception(constants.ErrNoSuchObject)

        resource = self._schema.ObjectForKind(res["type"])
        resource.FromDict(res["object"])
        return resource

    def List(
        self, identity: store.ObjectIdentity, *opt: options.ListOption
    ) -> store.ObjectList:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        log.info(f"list {identity.Path()}")
        if len(identity.Key()) > 0:
            raise Exception(constants.ErrInvalidPath)
        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        self._test_connection()
        collection = self._client[self._db][COLLECTION_NAME]
        filter_ = {"type": identity.Type()}

        if copt.filter:
            obj = self._schema.ObjectForKind(identity.Type())
            if obj is None:
                raise Exception(constants.ErrNoSuchObject)

            filter_ = {"$and": [filter_, _convert_filter(copt.filter, obj)]}
            log.info(f"filter: {filter_}")

        cur = collection.find(filter_)

        if copt.order_by:
            cur = cur.sort(
                f"object.{copt.order_by}",
                ASCENDING if copt.order_incremental else DESCENDING,
            )

        if copt.page_size is not None and copt.page_size > 0:
            cur = cur.limit(int(copt.page_size))
        if copt.page_offset is not None and copt.page_offset > 0:
            cur = cur.skip(int(copt.page_offset))

        rows = list(cur)
        res = store.ObjectList()
        for r in rows:
            try:
                resource = self._schema.ObjectForKind(identity.Type())
                resource.FromDict(r["object"])

                res.append(resource)
            except Exception as e:
                log.error(str(e))
                continue
        return res


def Factory(URI: str):
    def _factory(schema):
        client = MongoStore(schema, URI)
        log.info(f"initialized {URI}")
        return client, None

    return _factory
