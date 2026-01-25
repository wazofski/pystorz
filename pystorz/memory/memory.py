import logging

from pystorz.internal import constants
from pystorz.store import store, options, utils


log = logging.getLogger(__name__)


def _match_filter(filterOption, object, sample):
    # unwrap _ListDeleteOption
    if isinstance(filterOption, options._ListDeleteOption):
        copt = options.CommonOptionHolderFactory()
        filterOption.ApplyFunction()(copt)
        filterOption = copt.filter

    if isinstance(filterOption, options.AndOption):
        return all(_match_filter(f, object, sample) for f in filterOption.filters)

    if isinstance(filterOption, options.OrOption):
        return any(_match_filter(f, object, sample) for f in filterOption.filters)

    if isinstance(filterOption, options.NotOption):
        return not _match_filter(filterOption.filter, object, sample)

    # validate key exists on sample
    if utils.object_path(sample, filterOption.key) is None:
        raise Exception(constants.ErrInvalidFilter)

    val = utils.object_path(object, filterOption.key)

    # helper to compare numbers represented as strings
    def _try_numeric(a):
        try:
            return float(a)
        except Exception:
            return None

    if isinstance(filterOption, options.InOption):
        comp_vals = filterOption.values
        if val is None:
            return False
        return val in comp_vals

    if isinstance(filterOption, options.EqOption):
        return val == filterOption.value

    if isinstance(filterOption, options.LtOption):
        if val is None:
            return False
        a = _try_numeric(val)
        b = _try_numeric(filterOption.value)
        if a is not None and b is not None:
            return a < b
        return val < filterOption.value

    if isinstance(filterOption, options.GtOption):
        if val is None:
            return False
        a = _try_numeric(val)
        b = _try_numeric(filterOption.value)
        if a is not None and b is not None:
            return a > b
        return val > filterOption.value

    if isinstance(filterOption, options.LteOption):
        if val is None:
            return False
        a = _try_numeric(val)
        b = _try_numeric(filterOption.value)
        if a is not None and b is not None:
            return a <= b
        return val <= filterOption.value

    if isinstance(filterOption, options.GteOption):
        if val is None:
            return False
        a = _try_numeric(val)
        b = _try_numeric(filterOption.value)
        if a is not None and b is not None:
            return a >= b
        return val >= filterOption.value

    raise Exception(constants.ErrInvalidFilter)


class MemoryStore(store.Store):
    def __init__(self, Schema):
        self._schema = Schema
        # storage: dict[type] -> list of records
        # record: {idpath, pkpath, pkey, type, object}
        self._id_index = {}
        self._type_index = {}

    def Get(self, identity: store.ObjectIdentity, *opt: options.GetOption) -> store.Object:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        log.info(f"get {identity.Path()}")

        if identity.Path() in self._id_index:
            return self._id_index[identity.Path()].Clone()

        raise Exception(constants.ErrNoSuchObject)

    def Create(self, obj: store.Object, *opt: options.CreateOption) -> store.Object:
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info(f"create {obj.Metadata().Kind()} {obj.PrimaryKey()}")

        lk = obj.Metadata().Kind().lower()
        pkpath = f"{lk}/{obj.PrimaryKey()}"
        idpath = f"id/{obj.Metadata().Identity().Key()}"
        if idpath in self._id_index or pkpath in self._id_index:
            raise Exception(constants.ErrObjectExists)

        cloned = obj.Clone()

        self._id_index[idpath] = cloned
        self._id_index[pkpath] = cloned
        if lk not in self._type_index:
            self._type_index[lk] = dict()
        self._type_index[lk][cloned.ToJson()] = cloned

        return cloned.Clone()

    def List(self, identity: store.ObjectIdentity, *opt: options.ListOption) -> store.ObjectList:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        log.info(f"list {identity.Path()}")
        if len(identity.Key()) > 0:
            raise Exception(constants.ErrInvalidPath)

        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        records = self._type_index.get(identity.Type(), dict())
        filtered = records.values()

        if copt.filter:
            sample = self._schema.ObjectForKind(identity.Type())
            if sample is None:
                raise Exception(constants.ErrNoSuchObject)
            _match_filter(copt.filter, sample, sample)

            filtered = []
            for j, r in records.items():
                try:
                    if _match_filter(copt.filter, r, sample):
                        filtered.append(r)
                except Exception as e:
                    log.error(str(e))
                    continue
            
        # ordering
        if copt.order_by:
            filtered = sorted(
                filtered,
                key=lambda x: utils.object_path(x, copt.order_by),
                reverse=(not copt.order_incremental))

        # pagination
        if copt.page_offset is not None and copt.page_offset > 0:
            filtered = filtered[int(copt.page_offset):]
        if copt.page_size is not None and copt.page_size > 0:
            filtered = filtered[: int(copt.page_size)]

        res = store.ObjectList()
        for r in filtered:
            res.append(r.Clone())

        return res

    def Delete(self, identity: store.ObjectIdentity, *opt: options.DeleteOption):
        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        log.info(f"delete {identity.Path()}")
        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        if copt.filter is None:
            object_to_delete = self.Get(identity)

            lk = object_to_delete.Metadata().Kind().lower()

            idpath = f"id/{object_to_delete.Metadata().Identity().Key()}"
            pkpath = f"{lk}/{object_to_delete.PrimaryKey()}"
            print(f"Deleting idpath: {idpath}, pkpath: {pkpath}")
            if idpath in self._id_index:
                del self._id_index[idpath]
            if pkpath in self._id_index:
                del self._id_index[pkpath]

            del self._type_index[lk][object_to_delete.ToJson()]
            return

        sample = self._schema.ObjectForKind(identity.Type())
        if sample is None:
            raise Exception(constants.ErrNoSuchObject)

        objects = self.List(identity, *opt)
        for obj in objects:
            lk = obj.Metadata().Kind().lower()

            idpath = f"id/{obj.Metadata().Identity().Key()}"
            pkpath = f"{lk}/{obj.PrimaryKey()}"
            if idpath in self._id_index:
                del self._id_index[idpath]
            if pkpath in self._id_index:
                del self._id_index[pkpath]

            del self._type_index[lk][obj.ToJson()]

    def Update(self, identity: store.ObjectIdentity, obj: store.Object, *opt: options.UpdateOption) -> store.Object:
        if identity is None:
            raise Exception(constants.ErrInvalidPath)
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info(f"update {identity.Path()}")
        existing = self.Get(identity)
        if existing.Metadata().Kind() != obj.Metadata().Kind():
            raise Exception(constants.ErrObjectIdentityMismatch)

        if existing.PrimaryKey() != obj.PrimaryKey():
            if existing.Metadata().Identity().Path() != obj.Metadata().Identity().Path():
                raise Exception(constants.ErrObjectIdentityMismatch)

            target_identity = store.ObjectIdentity(
                f"{existing.Metadata().Kind().lower()}/{obj.PrimaryKey()}")
            target = None
            try:
                target = self.Get(target_identity)
            except Exception:
                pass
            if target is not None:
                raise Exception(constants.ErrObjectExists)

        print("updating object... {} -> {}".format(existing.PrimaryKey(), obj.PrimaryKey()))

        # remove old record and insert new
        idpath = f"id/{existing.Metadata().Identity().Key()}"
        self.Delete(store.ObjectIdentity(idpath))

        return self.Create(obj)


def MemoryStoreFactory(schema: store.SchemaHolder):
    return MemoryStore(schema)
