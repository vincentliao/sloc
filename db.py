from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import datetime

Base = declarative_base()

class Repository(Base):
    __tablename__ = 'repository'
    sno = Column(Integer, primary_key=True)
    name = Column(String(256))
    path = Column(String(256))
    owner = Column(String(100))
    revisions = relationship('Revision', backref='repository', lazy='joined')

class Revision(Base):
    __tablename__ = 'revision'
    sno = Column(Integer, primary_key=True)
    hash = Column(String(32))
    commit_time = Column(DateTime)
    repo_sno = Column(Integer, ForeignKey('repository.sno'))
    repo = relationship('Repository', back_populates='revisions')
    slocs = relationship('Sloc', lazy='joined')

class Sloc(Base):
    __tablename__ = 'sloc'
    sno = Column(Integer, primary_key=True)
    language = Column(String(256))
    filename = Column(String(256))
    source_line = Column(Integer)
    empty_line = Column(Integer)

    revision_sno = Column(Integer, ForeignKey('revision.sno'))
    revision = relationship('Revision', back_populates='slocs')

def build_db():
    engine = create_engine('sqlite:///sloc.db', echo=True)
    Base.metadata.create_all(engine)

def test_data():
    engine = create_engine('sqlite:///sloc.db', echo=True)
    Session = sessionmaker(bind=engine)
    s = Session()
    repo = Repository(name='test_name', path='test_path', owner='test_owner')
    repo2 = Repository(name='repo2', path='repo_path', owner='vincentliao')

    sloc1 = Sloc(language='Java', filename='a.java', source_line=20, empty_line=2)
    sloc2 = Sloc(language='Cpp', filename='c.cpp', source_line=30, empty_line=3)

    r1 = Revision(hash='test_0000000002', commit_time=datetime.datetime.now())
    repo2.revisions = [r1]

    r1.slocs = [sloc1, sloc2]
    repo.revisions = [Revision(hash='test_0000000001', commit_time=datetime.datetime.now())]
    s.add(repo)
    s.add(repo2)
    s.commit()

def query():
    engine = create_engine('sqlite:///sloc.db')
    Session = sessionmaker(bind=engine)
    s = Session()
    repos = s.query(Repository).all()
    print('count = %d name=%s' % (len(repos), repos[0].name) )

    for repo in repos:
        for r in repo.revisions:
            for sloc in r.slocs:
                print(sloc.filename)

if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'build':
        build_db()
    elif sys.argv[1] == 'data':
        test_data()
    elif sys.argv[1] == 'query':
        query()
