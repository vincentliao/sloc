import logging
import pandas as pd
from bokeh.io import show, output_file
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.plotting import figure

log = logging.getLogger("figure_worker")
logging.basicConfig(level=logging.INFO)

class FigureWorker:
    def __init__(self, sloc_worker):
        self.sloc_worker = sloc_worker

    def figure_commits(self, repo_name):
        log.info(f'figure_commits({repo_name})')
        figure_title = "Commit Counts(%s)" % repo_name
        output_file("figure/figure_commits_%s.html" % repo_name)

        data = self.sloc_worker.load_revisions(repo_name)
        cm = pd.DataFrame.from_dict(data)
        cmt = cm.set_index('commit_time').groupby(pd.Grouper(freq='M'))

        date_tags = [str(x[0].date()) for x in cmt]
        commit_amount = [len(x[1]) for x in cmt]
        p = figure(x_range=date_tags, plot_height=250, title=figure_title)

        p.vbar(x=date_tags, top=commit_amount, width=0.9)
        p.xgrid.grid_line_color = None
        p.y_range.start = 0
        p.sizing_mode = 'scale_width'
        show(p)

    def figure_source_line(self, repo_name):
        log.info(f'figure_source_line({repo_name})')
        figure_title = "Source Code Lines(%s)" % repo_name
        output_file("figure/figure_source_line_%s.html" % repo_name)
        repo = self.sloc_worker.load_repository(self.sloc_worker.create_db_session(), repo_name)
        log.info(f'repo: {repo}')

        data = { 'hash': [], 'commit_time': [], 'sloc': [] }
        for r in repo.revisions:
            data['hash'].append(r.hash)
            data['commit_time'].append(r.commit_time)
            data['sloc'].append(r.slocs)

        cm = pd.DataFrame.from_dict(data)
        commits_freq = cm.set_index('commit_time').groupby(pd.Grouper(freq='M'))

        last_hash = ''
        last_total_lines = 0
        sloc_date = []
        sloc_info = []
        for commit in commits_freq:
            date = str(commit[0].date())
            if len(commit[1]['hash'])>0:
                last_hash = commit[1]['hash'][-1]
                sloc = commit[1]['sloc'][-1]
                last_total_lines = sum(s.source_line for s in sloc)
            sloc_date.append(date)
            sloc_info.append(last_total_lines)
            log.info('%s: %s sloc=%d', date, last_hash, last_total_lines)

        p = figure(x_range=sloc_date, title=figure_title)
        p.line(sloc_date, sloc_info, line_width=2)
        p.sizing_mode = 'scale_width'
        show(p)
