#! /usr/bin/python3

from gitrepo import GitRepo
import pygount
import os
import pathlib
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Repository, Revision, Sloc

import config

class SlocWorker:
    def __init__(self, _db):
        self.db = _db
        self.engine = create_engine(self.db, echo=False)

    def source_scanner(self, folder, skip_path, suffix):
        files = list()
        for (dirpath, dirnames, filenames) in os.walk(folder, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in skip_path]
            files += [os.path.join(dirpath, file) for file in filenames if pathlib.Path(file).suffix in suffix ]
        return files

    def scan_sloc(self, repo_name, repo_path, repo_owner, skip_path, suffix):
        Session = sessionmaker(bind=self.engine)
        s = Session()
        row_repo = self.load_repository(s, repo_name)
        repo = GitRepo(repo_path + '/.git')
        existing_revision = [ _.hash for _ in row_repo.revisions]
        print(existing_revision)

        for commit in repo.get_all_commit_id():
            date = datetime.datetime.fromtimestamp(int(commit.commit_time)).strftime('%Y-%m-%d %H:%M:%S')
            hash = str(commit.id)
            print('\n%s, %s' % (date, hash), end='')

            if hash not in existing_revision:
                print(' add', end='')
                existing_revision.append(hash)
                row_revision = Revision(hash=hash, commit_time=datetime.datetime.fromtimestamp(int(commit.commit_time)))
                row_repo.revisions.append(row_revision)
                repo.checkout_by(hash)

                row_revision.slocs = []
                for f in self.source_scanner(repo_path, skip_path, suffix):
                    analysis = pygount.source_analysis(f, 'pygount')
                    row_revision.slocs.append(Sloc(language=analysis.language, filename=f, source_line=analysis.code, empty_line=analysis.empty))

        # s.add(row_repo)
        s.commit()

    def load_repository(self, session, repo_name):
        return session.query(Repository).filter_by(name=repo_name).all()[0]

    def get_latest_sum(sloc_db, repo_name):
        Session = sessionmaker(bind=self.engine)
        s = Session()
        repo = s.query(Repository).filter_by(name=repo_name).all()[0]
        for r in repo.revisions:
            for sloc in r.slocs:
                print(sloc.filename)

if __name__ == '__main__':

    sw = SlocWorker('sqlite:///sloc.db')
    for info in config.info:
        sw.scan_sloc(repo_name=info['repo_name'],
            repo_path=info['repo_path'], repo_owner=info['repo_owner'],
            skip_path=info['skip_path'], suffix=info['suffix'])

    # read_sloc_sum('sqlite:///sloc.db', repo_name='gitbook_template')
