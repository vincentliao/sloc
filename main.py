#! /usr/bin/python3

from gitrepo import GitRepo
import pygount
import os
import pathlib
import datetime
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import lazyload
from db import Repository, Revision, Sloc
import config
import logging
import lexers

import click

from figure_worker import FigureWorker

log = logging.getLogger("sloc_main")

class SlocWorker:
    def __init__(self, _db):
        self.db = _db
        self.engine = create_engine(self.db, echo=False)
        lexers.load()

    def load_repository(self, session, repo_name):
        log.info(f'load_repository: repo_name={repo_name}')
        repos = session.query(Repository).options(lazyload(Repository.revisions).subqueryload(Revision.slocs)).filter_by(name=repo_name).all()
        if len(repos) == 0:
            return None
        log.info(f'{repo_name} loaded.')
        return repos[0]

    def load_revisions(self, repo_name):
        session = self.create_db_session()
        repos = session.query(Repository).options(lazyload(Repository.revisions)).filter_by(name=repo_name).all()
        sno = repos[0].sno
        rev_collect = session.query(Revision).options(lazyload(Revision.slocs)).filter_by(repo_sno=sno).all()

        data = { 'hash': [], 'commit_time': [] }
        for r in rev_collect:
            data['hash'].append(r.hash)
            data['commit_time'].append(r.commit_time)

        return data

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
        log.info(f'repo_name: {row_repo.name}')
        log.info(f'repo_path: {row_repo.path}')
        log.info(f'repo_owner: {row_repo.owner}')
        log.info(f'size of existing_revision: {len(existing_revision)}')

        analysis_cache = {}
        for commit in gitrepo.get_all_commit_id():
            date = datetime.datetime.fromtimestamp(int(commit.commit_time)).strftime('%Y-%m-%d %H:%M:%S')
            hash = str(commit.id)
            log.info(f'{date}, {hash}')

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
                        log.info(f'Analysis: {f}')

                    row_revision.slocs.append(Sloc(language=analysis.language,
                                                   filename=f, source_line=analysis.code,
                                                   empty_line=analysis.empty))
            db_session.commit()

        log.info('End of scaning.')

@click.command()
@click.option('--debug', '-d', is_flag=True, help='Debug mode')
@click.option('--build-all', '-ba', 'buildall', is_flag=True, help='build all')
@click.option('--figure', '-f', 'figure', default=1, help='draw a figure for the repo')
@click.argument('repo_name')
def sloc(debug, buildall, figure, repo_name):

    if debug:
        logging.basicConfig(level=logging.DEBUG)

    sw = SlocWorker('sqlite:///sloc.db')

    if buildall:
        for info in config.info:
             sw.scan_sloc(repo_name=info['repo_name'],
                 repo_path=info['repo_path'], repo_owner=info['repo_owner'],
                 skip_path=info['skip_path'], suffix=info['suffix'])

    if figure == 0:
        fw = FigureWorker(sw)
        fw.figure_source_line(repo_name)
    elif figure ==1:
        fw = FigureWorker(sw)
        fw.figure_commits(repo_name)



if __name__ == '__main__':
    sloc()
