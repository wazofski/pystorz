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
            return None

        self.DB = self.MakeConnection()

        # t = sqlite3.connect("asdsa")
        # err = self.DB.ping()
        # if err is not None:
        #     return err

        return self._prepareTables()

    def Create(self, obj, opt=[]):
        if obj is None:
            return None, constants.ErrObjectNil

        log.Printf("create %s", obj.PrimaryKey())

        copt = options.CommonOptionHolderFactory()
        for o in opt:
            err = o.ApplyFunction()(copt)
            if err is not None:
                return None, err

        lk = obj.Metadata().Kind().lower()
        path = "{}/{}".format(lk, obj.PrimaryKey())
        existing, _ = self.Get(store.ObjectIdentity(path))
        if existing is not None:
            return None, constants.ErrObjectExists

        err = self.TestConnection()
        if err is not None:
            return None, err

        err = self._setIdentity(
            obj.Metadata().Identity().Path(),
            obj.PrimaryKey(),
            obj.Metadata().Kind())

        if err is not None:
            return None, err

        err = self._setObject(obj.PrimaryKey(), obj.Metadata().Kind(), obj)
        if err is not None:
            return None, err

        return obj.Clone(), None

    def Update(self, identity, obj, *opt):
        log.Printf("update %s", identity.Path())
        copt = options.CommonOptionHolderFactory()

        for o in opt:
            err = o.ApplyFunction()(copt)
            if err is not None:
                return None, err

        if obj is None:
            return None, constants.ErrObjectNil

        existing, _ = self.Get(identity)
        if existing is None:
            return None, constants.ErrNoSuchObject

        err = self.TestConnection()
        if err is not None:
            return None, err

        err = self._removeIdentity(existing.Metadata().Identity().Path())
        if err is not None:
            log.Printf("%s", err)

        err = self._setIdentity(obj.Metadata().Identity().Path(),
                                obj.PrimaryKey(), obj.Metadata().Kind())

        if err is not None:
            return None, err

        err = self._removeObject(existing.PrimaryKey(),
                                 existing.Metadata().Kind())
        if err is not None:
            return None, err

        err = self._setObject(obj.PrimaryKey(), obj.Metadata().Kind(), obj)
        if err is not None:
            return None, err

        return obj.Clone(), None

    def Delete(self, identity, *opt):
        log.Printf("delete %s", identity.Path())
        copt = options.CommonOptionHolderFactory()

        for o in opt:
            err = o.ApplyFunction()(copt)
            if err is not None:
                return err

        existing, _ = self.Get(identity)
        if existing is None:
            return constants.ErrNoSuchObject

        err = self.TestConnection()
        if err is not None:
            return err

        err = self._removeIdentity(existing.Metadata().Identity().Path())
        if err is not None:
            return err

        return self._removeObject(existing.PrimaryKey(), existing.Metadata().Kind())

    def Get(self, identity, *opt):
        log.Printf("get %s", identity.Path())

        err = None
        copt = options.CommonOptionHolderFactory()
        for o in opt:
            err = o.ApplyFunction()(copt)
            if err != None:
                return None, err

        err = self.TestConnection()
        if err != None:
            return None, err

        pkey, typ, err = self.getIdentity(identity.Path())
        if err == None:
            return self._getObject(pkey, typ)

        tokens = identity.Path().split("/")
        if len(tokens) == 2:
            return self._getObject(tokens[1], tokens[0])

        return None, constants.ErrNoSuchObject

    def List(self, identity, *opt):
        print("list", identity)

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

        res = self._parseObjectRows(rows, identity.Type())
        # rows.Close()

        return res, None

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
        row = self.DB.execute(
            "SELECT Pkey, Type FROM IdIndex WHERE Path=?", path)
        result = row.fetchone()

        if result is not None:
            pkey, typ = result
            return pkey, typ, None
        else:
            return None, None, Exception("Identity not found")

    def _setIdentity(self, path, pkey, typ):
        query = ""
        existing_pkey, existing_typ, _ = self.getIdentity(path)

        if existing_pkey is not None and existing_typ is not None:
            query = "UPDATE IdIndex SET Pkey=?, Type=? WHERE Path=?"
        else:
            query = "INSERT INTO IdIndex (Pkey, Type, Path) VALUES (?, ?, ?)"

        try:
            self.DB.execute(query, pkey, typ.lower(), path)
        except Exception as e:
            return e

    def _removeIdentity(self, path):
        query = "DELETE FROM IdIndex WHERE Path = ?"

        try:
            self.DB.execute(query, path)
        except Exception as e:
            return e

    def _getObject(self, pkey, typ):
        cursor = self.DB.cursor()
        cursor.execute(
            "SELECT Object FROM Objects WHERE Pkey=? AND Type=?", pkey, typ.lower())
        result = cursor.fetchone()

        if result is not None:
            data = result[0]
            return self._parseObjectRow(data, typ)
        else:
            return None, Exception("Object not found")

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
            data = row[0]
            obj, error = self._parseObjectRow(data, typ)
            if error is not None:
                return None, error
            res.append(obj)
