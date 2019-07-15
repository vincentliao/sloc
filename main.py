#! /usr/bin/python3

from gitrepo import GitRepo
import pygount
import os
import pathlib
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Repository, Revision, Sloc

def source_scanner(folder, skip_path, suffix):
    files = list()
    for (dirpath, dirnames, filenames) in os.walk(folder, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in skip_path]
        files += [os.path.join(dirpath, file) for file in filenames if pathlib.Path(file).suffix in suffix ]
    return files

def get_sloc(sloc_db, repo_name, repo_path, repo_owner, skip_path, suffix):
    engine = create_engine(sloc_db, echo=False)
    Session = sessionmaker(bind=engine)
    s = Session()
    row_repo = Repository(name=repo_name, path=repo_path, owner=repo_owner)
    row_repo.revisions = []
    repo = GitRepo(repo_path + '/.git')
    for commit in repo.get_all_commit_id():
        date = datetime.datetime.fromtimestamp(int(commit.commit_time)).strftime('%Y-%m-%d %H:%M:%S')
        hash = commit.id
        print('%s, %s' % (date, hash))

        row_revision = Revision(hash=str(hash), commit_time=datetime.datetime.fromtimestamp(int(commit.commit_time)))
        row_repo.revisions.append(row_revision)
        repo.checkout_by(hash)

        row_revision.slocs = []
        for f in source_scanner(repo_path, skip_path, suffix):
            analysis = pygount.source_analysis(f, 'pygount')
            row_revision.slocs.append(Sloc(language=analysis.language, filename=f, source_line=analysis.code, empty_line=analysis.empty))

    s.add(row_repo)
    s.commit()

def sloc_gitbook_template():
    get_sloc(sloc_db='sqlite:///sloc.db', repo_name='gitbook_template',
            repo_path='/sloc/scan/gitbook_template', repo_owner='vincentliao',
            skip_path=['.git', 'images'], suffix=['.sh', '.css'])

def sloc_pygount():
    get_sloc(sloc_db='sqlite:///sloc.db', repo_name='pygount',
            repo_path='/sloc/scan/pygount', repo_owner='roskakori',
            skip_path=['.git', 'tests'], suffix=['.py'])

def get_latest_sum(sloc_db, repo_name):
    engine = create_engine(sloc_db, echo=False)
    Session = sessionmaker(bind=engine)
    s = Session()
    repo = s.query(Repository).filter_by(name=repo_name).all()[0]
    for r in repo.revisions:
        for sloc in r.slocs:
            print(sloc.filename)


if __name__ == '__main__':
    read_sloc_sum('sqlite:///sloc.db', repo_name='gitbook_template')
