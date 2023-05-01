import logging
import sqlite3
from pystorz.internal import constants
from pystorz.store import store, options, utils
from datetime import datetime

log = logging.getLogger(__name__)


def SqliteConnection(path):
    def func():
        return sqlite3.connect(path)

    return func


# def MySqlConnection(path):
#     def __call__():
#         log.Printf("mysql connection %s", path)
#         return mysql.connect(path)


class SqliteStore:
    def __init__(self, Schema, MakeConnection):
        self.Schema = Schema
        self.MakeConnection = MakeConnection
        self.DB = None

    def TestConnection(self):
        if self.DB is not None:
            return

        self.DB = self.MakeConnection()
        self._prepareTables()

        return self.DB.cursor()

    def Create(self, obj, opt=[]):
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info("create {}".format(obj.PrimaryKey()))

        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        lk = obj.Metadata().Kind().lower()
        path = "{}/{}".format(lk, obj.PrimaryKey())
        existing = None
        try:
            existing = self.Get(store.ObjectIdentity(path))
        except Exception as e:
            pass
        if existing is not None:
            raise Exception(constants.ErrObjectExists)

        self.TestConnection()

        obj.Metadata().SetCreated(datetime.now())
        obj.Metadata().SetUpdated(obj.Metadata().Created())
        obj.Metadata().SetRevision(1)

        try:
            # Start a transaction
            self.DB.execute("BEGIN")
            cursor = self.DB.cursor()

            self._setIdentity(
                cursor,
                obj.Metadata().Identity().Path(),
                obj.PrimaryKey(),
                obj.Metadata().Kind(),
            )

            self._setObject(cursor, obj.PrimaryKey(), obj.Metadata().Kind(), obj)

            # Commit the transaction
            self.DB.commit()
            return obj.Clone()
        except Exception as e:
            self.DB.rollback()
            raise e

    def Update(self, identity, obj, *opt):
        log.info("update {}".format(identity.Path()))

        copt = options.CommonOptionHolderFactory()

        for o in opt:
            o.ApplyFunction()(copt)

        if obj is None:
            raise Exception(constants.ErrObjectNil)

        existing = self.Get(identity)
        if existing is None:
            raise Exception(constants.ErrNoSuchObject)

        if existing.PrimaryKey() != obj.PrimaryKey():
            # log.info("primary key changed from {} to {}".format(
            #     existing.PrimaryKey(), obj.PrimaryKey())
            # )

            if existing.Metadata().Identity().Path() != obj.Metadata().Identity().Path():
                raise Exception(constants.ErrObjectIdentityMismatch)
            
            # see if there is an object with the new primary key value
            target_identity = store.ObjectIdentity(
                "{}/{}".format(
                    existing.Metadata().Kind().lower(), obj.PrimaryKey())
            )
            
            target = None
            try:
                target = self.Get(target_identity)
            except Exception as e:
                pass

            if target is not None:
                raise Exception(constants.ErrObjectExists)

        self.TestConnection()

        try:
            # Start a transaction
            self.DB.execute("BEGIN")
            cursor = self.DB.cursor()

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

            obj.Metadata().SetCreated(existing.Metadata().Created())
            obj.Metadata().SetUpdated(datetime.now())
            obj.Metadata().SetRevision(existing.Metadata().Revision() + 1)

            self._setObject(cursor, obj.PrimaryKey(), obj.Metadata().Kind(), obj)

            self.DB.commit()
            return obj.Clone()
        except Exception as e:
            self.DB.rollback()
            raise e

    def Delete(self, identity, *opt):
        log.info("delete {}".format(identity.Path()))
        copt = options.CommonOptionHolderFactory()

        for o in opt:
            o.ApplyFunction()(copt)

        existing = self.Get(identity)
        if existing is None:
            raise Exception(constants.ErrNoSuchObject)

        self.TestConnection()

        try:
            # Start a transaction
            self.DB.execute("BEGIN")
            cursor = self.DB.cursor()

            self._removeIdentity(cursor, existing.Metadata().Identity().Path())
            self._removeObject(
                cursor, existing.PrimaryKey(), existing.Metadata().Kind()
            )

            self.DB.commit()
        except Exception as e:
            self.DB.rollback()
            raise e

    def Get(self, identity, *opt):
        log.info("get {}".format(identity.Path()))

        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        self.TestConnection()

        cursor = self.DB.cursor()

        if identity.IsId():
            pkey, typ = self._getIdentity(cursor, identity.Path())
            return self._getObject(cursor, pkey, typ)
        
        return self._getObject(cursor, identity.Key(), identity.Type())

    def List(self, identity, *opt):
        log.info("list {}".format(identity))

        if len(identity.Key()) > 0:
            raise Exception(constants.ErrInvalidPath)

        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        self.TestConnection()

        cursor = self.DB.cursor()

        query = """SELECT Object FROM Objects 
        WHERE Type = '{}'""".format(
            identity.Type()
        )

        # pkey filter
        if copt.key_filter is not None:
            query += """
            AND Pkey IN ('{}')""".format(
                "', '".join(copt.key_filter)
            )

        # prop filter
        if copt.prop_filter is not None:
            obj = self.Schema.ObjectForKind(identity.Type())
            if obj is None:
                raise Exception(constants.ErrNoSuchObject)
            if utils.object_path(obj, copt.prop_filter.key) is None:
                raise Exception(constants.ErrInvalidFilter)
            query = query + " AND json_extract(Object, '$.{}') = {}".format(
                copt.prop_filter.key,
                copt.prop_filter.value
            )

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

        cursor = self.DB.cursor()
        self._do_query(cursor, query)
        rows = cursor.fetchall()

        return self._parseObjectRows(rows, identity.Type())

    def _prepareTables(self):
        create = """
        CREATE TABLE IF NOT EXISTS IdIndex (
            Path VARCHAR(25) NOT NULL PRIMARY KEY,
            Pkey NVARCHAR(50) NOT NULL,
            Type VARCHAR(25) NOT NULL);
        """

        cursor = self.DB.cursor()
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
        self.DB.commit()

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
        existing_pkey, existing_typ = None, None

        try:
            existing_pkey, existing_typ = self._getIdentity(cursor, path)
        except Exception as e:
            log.debug("identity get failed: {}".format(e))

        query = ""
        if existing_pkey is not None and existing_typ is not None:
            query = """UPDATE IdIndex SET Pkey='{}', Type='{}'
            WHERE Path='{}'""".format(
                pkey, typ.lower(), path
            )
        else:
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
        existing_obj = None

        try:
            existing_obj = self._getObject(cursor, pkey, typ)
        except Exception as e:
            log.debug("object get failed: {}".format(e))

        data = obj.ToJson()
        # encode the data so it doesn't contain any SQL unfriendly characters
        data = utils.encode_string(data)

        if existing_obj is not None:
            query = """UPDATE Objects SET Object='{}'
            WHERE Pkey = '{}' AND Type = '{}'""".format(
                data, pkey, typ.lower()
            )
        else:
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

    def _parseObjectRow(self, data, typ):
        return utils.unmarshal_object(data, self.Schema, typ)

    def _parseObjectRows(self, rows, typ):
        res = []
        for row in rows:
            data = utils.decode_string(row[0])
            res.append(self._parseObjectRow(data, typ))
        return res

    def _do_query(self, cursor, query):
        log.debug("running query: {}".format(query))

        cursor.execute(query)
