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

import pandas as pd
from bokeh.io import show, output_file
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.plotting import figure


log = logging.getLogger("sloc_main")

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
        if row_repo == None:
            row_repo = Repository(name=repo_name, path=repo_path, owner=repo_owner)
            s.add(row_repo)

        gitrepo = GitRepo(repo_path + '/.git')
        existing_revision = [ _.hash for _ in row_repo.revisions]
        log.info('repo_name: %s', row_repo.name)
        log.info('repo_path: %s', row_repo.path)
        log.info('repo_owner: %s', row_repo.owner)
        log.info('size of existing_revision: %d', len(existing_revision))

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
                    analysis = pygount.source_analysis(f, 'pygount')
                    row_revision.slocs.append(Sloc(language=analysis.language,
                                                   filename=f, source_line=analysis.code,
                                                   empty_line=analysis.empty))

        s.commit()
        log.info('End of scaning.')

    def load_repository(self, session, repo_name):
        log.info('load_repository: repo_name=%s', repo_name)
        repos = session.query(Repository).filter_by(name=repo_name).all()
        if len(repos) == 0:
            return None

        return repos[0]

    def figure_commits(self, repo_name):
        Session = sessionmaker(bind=self.engine)
        s = Session()
        repo = self.load_repository(s, repo_name)

        data = {
            'hash': [ r.hash for r in repo.revisions],
            'commit_time': [ r.commit_time for r in repo.revisions]
        }

        cm = pd.DataFrame.from_dict(data)
        cmt = cm.set_index('commit_time').groupby(pd.Grouper(freq='M'))

        figure_title = "Commit Counts(%s)" % repo_name
        output_file("figure_commits_%s.html" % repo_name)

        date_tags = [str(x[0].date()) for x in cmt]
        commit_amount = [len(x[1]) for x in cmt]
        p = figure(x_range=date_tags, plot_height=250, title=figure_title,
                   toolbar_location=None, tools="")

        p.vbar(x=date_tags, top=commit_amount, width=0.9)
        p.xgrid.grid_line_color = None
        p.y_range.start = 0
        show(p)


    def sloc_sum(self, repo_name):
        Session = sessionmaker(bind=self.engine)
        s = Session()
        repo = s.query(Repository).filter_by(name=repo_name).all()[0]
        for r in repo.revisions:
            for sloc in r.slocs:
                log.info('', sloc.filename)



if __name__ == '__main__':
    if '--debug' in sys.argv:
         logging.basicConfig(level=logging.INFO)

    sw = SlocWorker('sqlite:///sloc.db')

    # # scaning process of all project by config.py
    # for info in config.info:
    #     sw.scan_sloc(repo_name=info['repo_name'],
    #         repo_path=info['repo_path'], repo_owner=info['repo_owner'],
    #         skip_path=info['skip_path'], suffix=info['suffix'])

    sw.figure_commits('pygount')
