import json
import logging
import sqlite3
from internal import constants
from store import store, options, utils


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

        # TODO check connection

    def Create(self, obj, opt=[]):
        if obj is None:
            raise Exception(constants.ErrObjectNil)

        log.info("create {}".format(obj.PrimaryKey()))

        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        lk = obj.Metadata().Kind().lower()
        path = "{}/{}".format(lk, obj.PrimaryKey())
        existing = self.Get(store.ObjectIdentity(path))
        if existing is not None:
            raise Exception(constants.ErrObjectExists)

        self.TestConnection()

        self._setIdentity(
            obj.Metadata().Identity().Path(),
            obj.PrimaryKey(),
            obj.Metadata().Kind())

        self._setObject(obj.PrimaryKey(), obj.Metadata().Kind(), obj)

        return obj.Clone()

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

        self.TestConnection()

        self._removeIdentity(existing.Metadata().Identity().Path())
        self._setIdentity(obj.Metadata().Identity().Path(),
                          obj.PrimaryKey(), obj.Metadata().Kind())

        self._removeObject(existing.PrimaryKey(),
                           existing.Metadata().Kind())
        
        self._setObject(obj.PrimaryKey(), obj.Metadata().Kind(), obj)
        
        return obj.Clone()

    def Delete(self, identity, *opt):
        log.info("delete {}".format(identity.Path()))
        copt = options.CommonOptionHolderFactory()

        for o in opt:
            o.ApplyFunction()(copt)
        
        existing = self.Get(identity)
        if existing is None:
            raise Exception(constants.ErrNoSuchObject)

        self.TestConnection()
        
        self._removeIdentity(existing.Metadata().Identity().Path())        
        self._removeObject(existing.PrimaryKey(), existing.Metadata().Kind())

    def Get(self, identity, *opt):
        log.info("get {}".format(identity.Path()))

        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)
        
        self.TestConnection()
        
        pkey, typ, err = self._getIdentity(identity.Path())
        if err == None:
            return self._getObject(pkey, typ)

        tokens = identity.Path().split("/")
        if len(tokens) == 2:
            return self._getObject(tokens[1], tokens[0])

        return None, constants.ErrNoSuchObject

    def List(self, identity, *opt):
        log.info("list {}".format(identity))

        if len(identity.Key()) > 0:
            return None, constants.ErrInvalidPath

        copt = options.CommonOptionHolderFactory()
        for o in opt:
            o.ApplyFunction()(copt)

        err = self.TestConnection()
        if err is not None:
            return None, err

        query = "SELECT Object FROM Objects WHERE Type = '{}'".format(
            identity.Type())

        # pkey filter
        if copt.key_filter is not None:
            query = query + \
                " AND Pkey IN ('{}')".format("', '".join(copt.key_filter))

        # prop filter
        if copt.prop_filter is not None:
            obj = self.Schema.ObjectForKind(identity.Type())
            if obj is None:
                return None, constants.ErrNoSuchObject
            if utils.ObjectPath(obj, copt.prop_filter.Key) is None:
                return None, constants.ErrInvalidFilter
            query = query + " AND json_extract(Object, '$.{}') = '{}'".format(
                copt.prop_filter.Key, copt.prop_filter.Value)

        if len(copt.order_by) > 0:
            query = "SELECT Object FROM Objects WHERE Type = '{}' ORDER BY json_extract(Object, '$.{}')".format(
                identity.Type(), copt.order_by)
            if copt.order_incremental:
                query = query + " ASC"
            else:
                query = query + " DESC"

        if copt.page_size > 0:
            query = query + " LIMIT {}".format(copt.page_size)

        if copt.page_offset > 0:
            query = query + " OFFSET {}".format(copt.page_offset)

        print(query)
        cursor = self.DB.cursor()

        cursor.execute(query)
        rows = cursor.fetchall()

        return self._parseObjectRows(rows, identity.Type())

    def _prepareTables(self):
        create = '''
        CREATE TABLE IF NOT EXISTS IdIndex (
            Path VARCHAR(25) NOT NULL PRIMARY KEY,
            Pkey NVARCHAR(50) NOT NULL,
            Type VARCHAR(25) NOT NULL);
        '''

        cursor = self.DB.cursor()

        cursor.execute(create)

        create = '''
        CREATE TABLE IF NOT EXISTS Objects (
            Pkey NVARCHAR(50) NOT NULL,
            Type VARCHAR(25) NOT NULL,
            Object JSON,
            PRIMARY KEY (Pkey,Type));
        '''

        cursor.execute(create)

    def _getIdentity(self, path):
        cursor = self.DB.cursor()
        cursor.execute(
            "SELECT Pkey, Type FROM IdIndex WHERE Path='{}'".format(path))
        result = cursor.fetchone()

        if result is not None:
            pkey, typ = result
            return pkey, typ
        else:
            raise Exception(constants.ErrNoSuchObject)

    def _setIdentity(self, path, pkey, typ):
        query = ""
        existing_pkey, existing_typ, _ = self.getIdentity(path)

        if existing_pkey is not None and existing_typ is not None:
            query = "UPDATE IdIndex SET Pkey='{}', Type='{}' WHERE Path='{}'".format(pkey, typ, path)
        else:
            query = "INSERT INTO IdIndex (Pkey, Type, Path) VALUES ('{}', '{}', '{}')".format(pkey, typ, path)

        cur = self.DB.cursor()
        cur.execute(query)

    def _removeIdentity(self, path):
        query = "DELETE FROM IdIndex WHERE Path = '{}'".format(path)

        self.DB.execute(query)

    def _getObject(self, pkey, typ):
        cursor = self.DB.cursor()
        cursor.execute(
            "SELECT Object FROM Objects WHERE Pkey='{}' AND Type='{}'".format(pkey, typ.lower()))
        result = cursor.fetchone()

        if result is not None:
            data = result[0]
            return self._parseObjectRow(data, typ)
        else:
            raise Exception(constants.ErrNoSuchObject)

    def _setObject(self, pkey, typ, obj):
        query = ""
        existing_obj, _ = self._getObject(pkey, typ)

        if existing_obj is not None:
            query = "UPDATE Objects SET Object=? WHERE Pkey = ? AND Type = ?"
        else:
            query = "INSERT INTO Objects (Object, Pkey, Type) VALUES (?, ?, ?)"

        data = obj.ToJson()

        cursor = self.DB.cursor()
        cursor.execute(query, data, pkey, typ.lower())

    def _removeObject(self, pkey, typ):
        query = "DELETE FROM Objects WHERE Pkey = ? AND Type = ?"
        cursor = self.DB.cursor()
        cursor.execute(query, pkey, typ.lower())

    def _parseObjectRow(self, data, typ):
        return utils.unmarshal_object(data, self.Schema, typ)

    def _parseObjectRows(self, rows, typ):
        res = []
        for row in rows:
            res.append(self._parseObjectRow(row[0], typ))
        return res