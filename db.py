from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

Base = declarative_base()

class Repository(Base):
    __tablename__ = 'repository'
    sno = Column(Integer, primary_key=True)
    name = Column(String(256))
    path = Column(String(256))
    owner = Column(String(100))

class Commit(Base):
    __tablename__ = 'commit'
    sno = Column(Integer, primary_key=True)
    hash = Column(String(32))
    commit_time = Column(DateTime)
    repo_sno = Column(Integer, ForeignKey('repository.sno'))
    repo = relationship('Repository', backref=backref('commit', order_by=sno))

class Sloc(Base):
    __tablename__ = 'sloc'
    sno = Column(Integer, primary_key=True)
    language = Column(String(256))
    filename = Column(String(256))
    source_line = Column(Integer)
    empty_line = Column(Integer)

def build_db():
    engine = create_engine('sqlite:///sloc.db', echo=True)
    Base.metadata.create_all(engine)

def test_data():
    engine = create_engine('sqlite:///sloc.db', echo=True)
    Session = sessionmaker(bind=engine)
    s = Session()
    repo = Repository(name='test_name', path='test_path', owner='test_owner')
    c1 = Commit('test_0000000001', DateTime(2019, 1, 1))
    repo.commit = [c1]
    s.add(repo)
    s.commit()

if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'build':
        build_db()
    elif sys.argv[1] == 'data':
        test_data()
