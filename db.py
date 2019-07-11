from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref

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
    repo_sno = Column(Integer, ForeignKey('respository.sno'))
    hash = Column(String(32))
    commit_time = Column(DateTime())

class Sloc(Base):
    __tablename__ = 'sloc'
    sno = Column(Integer, primary_key=True)
    commit_sno = Column(Integer, ForeignKey('commit.sno'))
    language = Column(String(256))
    filename = Column(String(256))
    source_line = Column(Integer)
    empty_line = Column(Integer)
