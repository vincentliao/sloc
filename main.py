#! /usr/bin/python3

from gitrepo import GitRepo
import pygount
import os
import pathlib
import datetime
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Repository, Revision, Sloc
import config
import logging
import lexers
from difflib import SequenceMatcher

from figure_worker import FigureWorker

log = logging.getLogger("sloc_main")

class SlocWorker:
    def __init__(self, _db):
        self.db = _db
        self.engine = create_engine(self.db, echo=False)
        lexers.load()

    def load_repository(self, session, repo_name):
        log.info('load_repository: repo_name=%s', repo_name)
        repos = session.query(Repository).filter_by(name=repo_name).all()
        if len(repos) == 0:
            return None

        return repos[0]

    def create_db_session(self):
        Session = sessionmaker(bind=self.engine)
        return Session()

    def source_scanner(self, folder, skip_path, suffix):
        files = list()
        for (dirpath, dirnames, filenames) in os.walk(folder, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in skip_path]
            files += [os.path.join(dirpath, file) for file in filenames if pathlib.Path(file).suffix in suffix ]
        return files

    def scan_sloc(self, repo_name, repo_path, repo_owner, skip_path, suffix):
        db_session = self.create_db_session()
        row_repo = self.load_repository(db_session, repo_name)
        if row_repo == None:
            row_repo = Repository(name=repo_name, path=repo_path, owner=repo_owner)
            db_session.add(row_repo)

        gitrepo = GitRepo(repo_path + '/.git')
        existing_revision = [ _.hash for _ in row_repo.revisions]
        log.info('repo_name: %s', row_repo.name)
        log.info('repo_path: %s', row_repo.path)
        log.info('repo_owner: %s', row_repo.owner)
        log.info('size of existing_revision: %d', len(existing_revision))

        analysis_cache = {}
        for commit in gitrepo.get_all_commit_id():
            date = datetime.datetime.fromtimestamp(int(commit.commit_time)).strftime('%Y-%m-%d %H:%M:%S')
            hash = str(commit.id)
            log.info('%s, %s' % (date, hash))

            if hash not in existing_revision:
                log.info('add revision')
                existing_revision.append(hash)
                row_revision = Revision(hash=hash,
                                        commit_time=datetime.datetime.fromtimestamp(int(commit.commit_time)))
                row_repo.revisions.append(row_revision)
                gitrepo.checkout_by(hash)

                row_revision.slocs = []
                for f in self.source_scanner(repo_path, skip_path, suffix):
                    fcontent = ''
                    with open(f, 'rb') as fh:
                        fcontent = fh.read()

                    if f in analysis_cache and analysis_cache[f][1] == fcontent:
                        analysis = analysis_cache[f][0]
                        # log.info('Use cache in analysis: %s', f)
                    else:
                        analysis = pygount.source_analysis(f, group='pygount', encoding='automatic')
                        analysis_cache[f] = (analysis, fcontent)
                        log.info('Analysis: %s', f)

                    row_revision.slocs.append(Sloc(language=analysis.language,
                                                   filename=f, source_line=analysis.code,
                                                   empty_line=analysis.empty))
            db_session.commit()

        log.info('End of scaning.')

if __name__ == '__main__':
    if '--debug' in sys.argv:
         logging.basicConfig(level=logging.INFO)

    sw = SlocWorker('sqlite:///sloc.db')

    # scaning process of all project by config.py
    if '--build' in sys.argv:
        for info in config.info:
             sw.scan_sloc(repo_name=info['repo_name'],
                 repo_path=info['repo_path'], repo_owner=info['repo_owner'],
                 skip_path=info['skip_path'], suffix=info['suffix'])

    if '--figure' in sys.argv:

        fi = sys.argv.index('--figure')
        repo_name = sys.argv[fi+1]

        fw = FigureWorker(sw)
        fw.figure_source_line(repo_name)
