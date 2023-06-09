import logging
import threading
import sqlparse

from pystorz.internal import constants
from pystorz.store import store, options, utils

log = logging.getLogger(__name__)


class SqlStore(store.Store):
    def __init__(self, Schema, connector):
        self._schema = Schema
        self._makeConnection = connector
        self._connection_cache = {}

    def _connection(self):
        tid = threading.get_ident()
        if tid not in self._connection_cache:
            self._connection_cache[tid] = self._makeConnection()
            self._prepareTables(self._connection_cache[tid])

        return self._connection_cache[tid]

    def Create(self, obj, *opt):
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info("create {} {}".format(
            obj.Metadata().Kind(),
            obj.PrimaryKey()))

        # copt = options.CommonOptionHolderFactory()
        # for o in opt:
        #     o.ApplyFunction()(copt)

        lk = obj.Metadata().Kind().lower()
        path = "{}/{}".format(lk, obj.PrimaryKey())
        existing = None
        try:
            existing = self.Get(store.ObjectIdentity(path))
        except Exception as e:
            pass

        if existing is not None:
            raise Exception(constants.ErrObjectExists)

        db = self._connection()

        try:
            # Start a transaction
            db.execute("BEGIN")
            cursor = db.cursor()

            self._setIdentity(
                cursor,
                obj.Metadata().Identity().Path(),
                obj.PrimaryKey(),
                obj.Metadata().Kind(),
            )

            self._setObject(cursor, obj.PrimaryKey(), obj.Metadata().Kind(), obj)

            # Commit the transaction
            db.commit()
            return obj.Clone()
        except Exception as e:
            db.rollback()
            raise e

    def Update(self, identity, obj, *opt):
        # copt = options.CommonOptionHolderFactory()
        # for o in opt:
        #     o.ApplyFunction()(copt)

        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info("update {}".format(identity.Path()))

        existing = self.Get(identity)
        if existing.Metadata().Kind() != obj.Metadata().Kind():
            raise Exception(constants.ErrObjectIdentityMismatch)

        if existing.PrimaryKey() != obj.PrimaryKey():
            # log.info("primary key changed from {} to {}".format(
            #     existing.PrimaryKey(), obj.PrimaryKey())
            # )

            if (
                existing.Metadata().Identity().Path()
                != obj.Metadata().Identity().Path()
            ):
                raise Exception(constants.ErrObjectIdentityMismatch)

            # see if there is an object with the new primary key value
            target_identity = store.ObjectIdentity(
                "{}/{}".format(existing.Metadata().Kind().lower(), obj.PrimaryKey())
            )

            target = None
            try:
                target = self.Get(target_identity)
            except Exception as e:
                pass

            if target is not None:
                raise Exception(constants.ErrObjectExists)

        db = self._connection()

        try:
            # Start a transaction
            db.execute("BEGIN")
            cursor = db.cursor()

            self._removeIdentity(cursor, existing.Metadata().Identity().Path())

            obj.Metadata().SetIdentity(existing.Metadata().Identity())

            self._setIdentity(
                cursor,
                obj.Metadata().Identity().Path(),
                obj.PrimaryKey(),
                obj.Metadata().Kind(),
            )

            self._removeObject(
                cursor, existing.PrimaryKey(), existing.Metadata().Kind()
            )

            self._setObject(cursor, obj.PrimaryKey(), obj.Metadata().Kind(), obj)

            db.commit()
            return obj.Clone()
        except Exception as e:
            db.rollback()
            raise e

    def Delete(self, identity, *opt):
        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        log.info("delete {}".format(identity.Path()))
        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        existing = None
        if copt.filter is None:
            existing = self.Get(identity)

        db = self._connection()

        # try:
        # Start a transaction
        db.execute("BEGIN")
        cursor = db.cursor()

        if copt.filter is None:
            self._removeIdentity(cursor, existing.Metadata().Identity().Path())
            self._removeObject(
                cursor, existing.PrimaryKey(), existing.Metadata().Kind()
            )
        else:
            clause = self._buildFilterClause(copt, identity)
            keys = self._getObjectKeys(cursor, identity.Type(), clause)

            self._removeObjects(cursor, identity.Type(), clause)
            self._removeIdentities(cursor, identity.Type(), keys)

        db.commit()
        # except Exception as e:
        #     db.rollback()
        #     raise e

    def Get(self, identity, *opt):
        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        log.info("get {}".format(identity.Path()))

        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        db = self._connection()
        cursor = db.cursor()

        res = None
        if identity.IsId():
            pkey, typ = self._getIdentity(cursor, identity.Path())
            res = self._getObject(cursor, pkey, typ)
        else:
            res = self._getObject(cursor, identity.Key(), identity.Type())
        
        db.commit()
        return res

    def List(self, identity, *opt: list[options.ListOption]):
        if identity is None:
            raise Exception(constants.ErrInvalidPath)

        log.info("list {}".format(identity.Path()))

        if len(identity.Key()) > 0:
            raise Exception(constants.ErrInvalidPath)

        copt = options.CommonOptionHolderFactory()

        for o in opt:
            o.ApplyFunction()(copt)

        db = self._connection()
        cursor = db.cursor()

        query = """SELECT Object FROM Objects 
        WHERE Type = '{}'""".format(
            identity.Type()
        )

        query += self._buildFilterClause(copt, identity)

        if copt.order_by is not None and len(copt.order_by) > 0:
            query += """
            ORDER BY json_extract(Object, '$.{}')""".format(
                copt.order_by
            )
            if copt.order_incremental is None or copt.order_incremental:
                query = query + " ASC"
            else:
                query = query + " DESC"

        if copt.page_size is not None and copt.page_size > 0:
            query = query + " LIMIT {}".format(copt.page_size)

        if copt.page_offset is not None and copt.page_offset > 0:
            query = query + " OFFSET {}".format(copt.page_offset)

        self._do_query(cursor, query)
        rows = cursor.fetchall()

        res = self._parseObjectRows(rows, identity.Type())
        db.commit()
        return res

    def _prepareTables(self, db):
        create = """
        CREATE TABLE IF NOT EXISTS IdIndex (
            Path VARCHAR(75) NOT NULL PRIMARY KEY,
            Pkey NVARCHAR(50) NOT NULL,
            Type VARCHAR(25) NOT NULL);
        """

        cursor = db.cursor()
        self._do_query(cursor, create)

        create = """
        CREATE TABLE IF NOT EXISTS Objects (
            Pkey NVARCHAR(50) NOT NULL,
            Type VARCHAR(25) NOT NULL,
            Object JSON,
            PRIMARY KEY (Pkey,Type));
        """

        cursor.execute(create)
        cursor.close()

        db.commit()

    def _getIdentity(self, cursor, path):
        query = """SELECT Pkey, Type FROM IdIndex 
        WHERE Path='{}'""".format(
            path
        )

        self._do_query(cursor, query)
        result = cursor.fetchone()

        if result is not None:
            pkey, typ = result
            return pkey, typ
        else:
            raise Exception(constants.ErrNoSuchObject)

    def _setIdentity(self, cursor, path, pkey, typ):
        # existing_pkey, existing_typ = None, None

        # try:
        #     existing_pkey, existing_typ = self._getIdentity(cursor, path)
        # except Exception as e:
        #     log.debug("identity get failed: {}".format(e))

        # query = ""
        # if existing_pkey is not None and existing_typ is not None:
        #     query = """UPDATE IdIndex SET Pkey='{}', Type='{}'
        #     WHERE Path='{}'""".format(
        #         pkey, typ.lower(), path
        #     )
        # else:
        query = """INSERT INTO IdIndex (Pkey, Type, Path)
        VALUES ('{}', '{}', '{}')""".format(
            pkey, typ.lower(), path
        )

        self._do_query(cursor, query)

    def _removeIdentity(self, cursor, path):
        query = """DELETE FROM IdIndex
        WHERE Path = '{}'""".format(
            path
        )

        self._do_query(cursor, query)

    def _getObject(self, cursor, pkey, typ):
        query = """SELECT Object FROM Objects
        WHERE Pkey='{}' AND Type='{}'""".format(
            pkey, typ.lower()
        )

        self._do_query(cursor, query)
        result = cursor.fetchone()

        if result is not None:
            data = result[0]
            data = utils.decode_string(data)
            return self._parseObjectRow(data, typ)
        else:
            raise Exception(constants.ErrNoSuchObject)

    def _setObject(self, cursor, pkey, typ, obj):
        query = ""
        # existing_obj = None

        # try:
        #     existing_obj = self._getObject(cursor, pkey, typ)
        # except Exception as e:
        #     log.debug("object get failed: {}".format(e))

        data = obj.ToJson()
        # encode the data so it doesn't contain any SQL unfriendly characters
        data = utils.encode_string(data)

        # if existing_obj is not None:
        #     query = """UPDATE Objects SET Object='{}'
        #     WHERE Pkey = '{}' AND Type = '{}'""".format(
        #         data, pkey, typ.lower()
        #     )
        # else:
        query = """INSERT INTO Objects (Object, Pkey, Type)
        VALUES ('{}', '{}', '{}')""".format(
            data, pkey, typ.lower()
        )

        self._do_query(cursor, query)

    def _removeObject(self, cursor, pkey, typ):
        query = """DELETE FROM Objects
        WHERE Pkey = '{}' AND Type = '{}'""".format(
            pkey, typ.lower()
        )

        self._do_query(cursor, query)

    def _getObjectKeys(self, cursor, typ, clause):
        query = """SELECT Pkey FROM Objects
        WHERE Type = '{}' {}""".format(
            typ.lower(),
            clause,
        )

        self._do_query(cursor, query)
        rows = cursor.fetchall()
        res = []
        for row in rows:
            res.append(row[0])
        return res

    def _removeIdentities(self, cursor, typ, keys):
        batch_size = 100
        for i in range(0, len(keys), batch_size):
            batch = keys[i : i + batch_size]
            clause = "Pkey IN ({})".format(",".join(["'{}'".format(k) for k in batch]))

            query = """DELETE FROM IdIndex
                WHERE Type = '{}' AND {}""".format(
                typ.lower(),
                clause,
            )

            self._do_query(cursor, query)

    def _removeObjects(self, cursor, typ, clause):
        query = """DELETE FROM Objects
        WHERE Type = '{}' {}""".format(
            typ.lower(),
            clause,
        )

        self._do_query(cursor, query)

    def _parseObjectRow(self, data, typ):
        return utils.unmarshal_object(data, self._schema, typ)

    def _parseObjectRows(self, rows, typ):
        res = []
        for row in rows:
            data = utils.decode_string(row[0])
            res.append(self._parseObjectRow(data, typ))
        return res

    def _do_query(self, cursor, query):
        log.debug("running query: {}".format(query))

        statements = sqlparse.parse(query)
        if len(statements) > 1:
            raise Exception(constants.ErrInvalidRequest)

        cursor.execute(query)

    def _buildFilterClause(self, copt, identity):
        if copt.filter is None:
            return ""

        sample = self._schema.ObjectForKind(identity.Type())
        # if sample is None:
        #     raise Exception(constants.ErrInvalidPath)

        return """
            AND ({})
            """.format(
            self._convertFilter(copt.filter, sample)
        )

    def _convertFilter(self, filterOption, sample):
        if isinstance(filterOption, options._ListDeleteOption):
            copt = options.CommonOptionHolderFactory()
            filterOption.ApplyFunction()(copt)
            filterOption = copt.filter

        if isinstance(filterOption, options.AndOption):
            return "( {} )".format(
                " AND ".join(
                    [self._convertFilter(f, sample) for f in filterOption.filters]
                )
            )

        if isinstance(filterOption, options.OrOption):
            return "( {} )".format(
                " OR ".join(
                    [self._convertFilter(f, sample) for f in filterOption.filters]
                )
            )

        if isinstance(filterOption, options.NotOption):
            return "( NOT {} )".format(
                self._convertFilter(filterOption.filter, sample)
            )

        if utils.object_path(sample, filterOption.key) is None:
            raise Exception(constants.ErrInvalidFilter)

        def convert_value(v):
            # return "'{}'".format(v)
            if isinstance(v, str):
                return "'{}'".format(utils.encode_string(v))
            elif isinstance(v, bool):
                return str(v).lower()
            else:
                return str(v)
        
        if isinstance(filterOption, options.InOption):
            values = ", ".join([convert_value(v) for v in filterOption.values])

            return " json_extract(Object, '$.{}') IN ({})".format(
                filterOption.key, values
            )

        if isinstance(filterOption, options.EqOption):
            return " json_extract(Object, '$.{}') = {} ".format(
                filterOption.key, convert_value(filterOption.value)
            )

        if isinstance(filterOption, options.LtOption):
            return " json_extract(Object, '$.{}') < {} ".format(
                filterOption.key, convert_value(filterOption.value)
            )

        if isinstance(filterOption, options.GtOption):
            return " json_extract(Object, '$.{}') > {} ".format(
                filterOption.key, convert_value(filterOption.value)
            )

        if isinstance(filterOption, options.LteOption):
            return " json_extract(Object, '$.{}') <= {} ".format(
                filterOption.key, convert_value(filterOption.value)
            )

        if isinstance(filterOption, options.GteOption):
            return " json_extract(Object, '$.{}') >= {} ".format(
                filterOption.key, convert_value(filterOption.value)
            )

        raise Exception(constants.ErrInvalidFilter)
