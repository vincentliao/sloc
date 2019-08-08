
import sqlite3
import logging
import db_schema

log = logging.getLogger(name='DBA')
logging.basicConfig(level=logging.INFO)

class CRUD:
    def create(self):
        pass

    def read(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass

class Repository(CRUD):
    def __init__(self, _sno, _name, _path, _owner):
        pass

    def create(self, _name, _path, _owner):
        c = self.db_connector.cursor()




class Revision:
    def __init__(self, _sno, _hash, _commit_time, _repo_sno, _repo):
        pass

class Sloc:
    def __init__(self, _sno, _language, _filename, _source_line, _empty):
        pass


class DBA:
    def __init__(self, _db_name):
        self.schema = db_schema.schema
        self.db_name = _db_name

    def __enter__(self):
        log.debug('DBA enter')
        self.db_connector = sqlite3.connect(self.db_name)
        return self

    def __exit__(self, type, value, trace):
        log.debug('DBA exit.')
        self.db_connector.close()

    def create(self):
        log.info('Database created')
        c = self.db_connector.cursor()
        c.executescript(self.schema)
        self.db_connector.commit()

if __name__ == '__main__':

    with DBA('sloc_v2.db') as dba:
        dba.create()
        log.debug(f'schema = {dba.schema}')
