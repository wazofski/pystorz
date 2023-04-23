import json
import logging
from internal import constants
from store import store, options, utils


import sqlite3


log = logging.getLogger(__name__)


def SqliteConnection(path):

    def __call__():
        return sqlite3.connect(path)


# def MySqlConnection(path):

#     def __call__():
#         log.Printf("mysql connection %s", path)
#         return mysql.connect(path)


class SqliteStore:

    def __init__(self, Schema, DB, MakeConnection):
        self.Schema = Schema
        self.DB = DB
        self.MakeConnection = MakeConnection

    def TestConnection(self):
        if self.DB is not None:
            if self.DB.ping() is None:
                return None

        err = None
        self.DB, err = self.MakeConnection()
        if err is not None:
            return err

        err = self.DB.ping()
        if err is not None:
            return err

        return self.prepareTables()

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

        err = self.setIdentity(
            obj.Metadata().Identity().Path(),
            obj.PrimaryKey(),
            obj.Metadata().Kind())
        if err is not None:
            return None, err

        err = self.setObject(obj.PrimaryKey(), obj.Metadata().Kind(), obj)
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

        err = self.removeIdentity(existing.Metadata().Identity().Path())
        if err is not None:
            log.Printf("%s", err)

        err = self.setIdentity(obj.Metadata().Identity().Path(),
                               obj.PrimaryKey(), obj.Metadata().Kind())

        if err is not None:
            return None, err

        err = self.removeObject(existing.PrimaryKey(),
                                existing.Metadata().Kind())
        if err is not None:
            return None, err

        err = self.setObject(obj.PrimaryKey(), obj.Metadata().Kind(), obj)
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

        err = self.removeIdentity(existing.Metadata().Identity().Path())
        if err is not None:
            return err

        return self.removeObject(existing.PrimaryKey(), existing.Metadata().Kind())

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
            return self.getObject(pkey, typ)

        tokens = identity.Path().split("/")
        if len(tokens) == 2:
            return self.getObject(tokens[1], tokens[0])

        return None, constants.ErrNoSuchObject

    def List(self, identity, *opt):
        print("list", identity)

        if len(identity.Key()) > 0:
            return None, constants.ErrInvalidPath

        copt = options.CommonOptionHolderFactory()
        for o in opt:
            err = o.ApplyFunction()(copt)
            if err is not None:
                return None, err

        err = self.TestConnection()
        if err is not None:
            return None, err

        query = "SELECT Object FROM Objects WHERE Type = ?"

        # pkey filter
        if copt.KeyFilter is not None:
            query = query + \
                " AND Pkey IN ('{}')".format("', '".join(copt.KeyFilter))

        # prop filter
        if copt.PropFilter is not None:
            obj = self.Schema.ObjectForKind(identity.Type())
            if obj is None:
                return None, constants.ErrNoSuchObject
            if utils.ObjectPath(obj, copt.PropFilter.Key) is None:
                return None, constants.ErrInvalidFilter
            query = query + " AND json_extract(Object, '$.{}') = '{}'".format(
                copt.PropFilter.Key, copt.PropFilter.Value)

        if len(copt.OrderBy) > 0:
            query = "SELECT Object FROM Objects WHERE Type = ? ORDER BY json_extract(Object, '$.{}')".format(
                copt.OrderBy)
            if copt.OrderIncremental:
                query = query + " ASC"
            else:
                query = query + " DESC"

        if copt.PageSize > 0:
            query = query + " LIMIT {}".format(copt.PageSize)

        if copt.PageOffset > 0:
            query = query + " OFFSET {}".format(copt.PageOffset)

        print(query)

        rows, err = self.DB.Query(query, identity.Type())
        if err is not None:
            return None, err

        res = self._parseObjectRows(rows, identity.Type())
        rows.Close()

        return res, None

    def _prepareTables(self):
        create = '''
        CREATE TABLE IF NOT EXISTS IdIndex (
            Path VARCHAR(25) NOT NULL PRIMARY KEY,
            Pkey NVARCHAR(50) NOT NULL,
            Type VARCHAR(25) NOT NULL);
        '''
        try:
            self.DB.execute(create)
        except Exception as e:
            return e

        create = '''
        CREATE TABLE IF NOT EXISTS Objects (
            Pkey NVARCHAR(50) NOT NULL,
            Type VARCHAR(25) NOT NULL,
            Object JSON,
            PRIMARY KEY (Pkey,Type));
        '''
        try:
            self.DB.execute(create)
        except Exception as e:
            return e

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
        row = self.DB.execute(
            "SELECT Object FROM Objects WHERE Pkey=? AND Type=?", pkey, typ.lower())
        result = row.fetchone()

        if result is not None:
            data = result[0]
            return self.parseObjectRow(data, typ)
        else:
            return None, Exception("Object not found")

    def _setObject(self, pkey, typ, obj):
        query = ""
        existing_obj, _ = self.getObject(pkey, typ)

        if existing_obj is not None:
            query = "UPDATE Objects SET Object=? WHERE Pkey = ? AND Type = ?"
        else:
            query = "INSERT INTO Objects (Object, Pkey, Type) VALUES (?, ?, ?)"

        data = json.dumps(obj)

        try:
            self.DB.execute(query, data, pkey, typ.lower())
        except Exception as e:
            return e

    def _removeObject(self, pkey, typ):
        query = "DELETE FROM Objects WHERE Pkey = ? AND Type = ?"

        try:
            self.DB.execute(query, pkey, typ.lower())
        except Exception as e:
            return e

    def _parseObjectRow(self, data, typ):
        try:
            return utils.unmarshal_object(data, self.Schema, typ)
        except Exception as e:
            return None, e

    def _parseObjectRows(self, rows, typ):
        res = []
        for row in rows:
            data = row[0]
            obj, error = self._parseObjectRow(data, typ)
            if error is not None:
                return None, error
            res.append(obj)
