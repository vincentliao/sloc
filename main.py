#! /usr/bin/python3

from gitrepo import GitRepo
import pygount
import os
import pathlib
import datetime

def source_scanner(folder, skip_path, suffix):
    files = list()
    for (dirpath, dirnames, filenames) in os.walk(folder, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in skip_path]
        files += [os.path.join(dirpath, file) for file in filenames if pathlib.Path(file).suffix in suffix ]
    return files

def sloc(project_path, skip_path, suffix):
    files = source_scanner(project_path, skip_path, suffix)
    for f in files:
        analysis = pygount.source_analysis(f, 'pygount')
        print('%s: %d' % (f, analysis.code))

if __name__ == '__main__':

    repo_path = '/workspace/kkboxmac'
    repo = GitRepo(repo_path + '/.git')
    for p in repo.get_all_commit_id():
        print('%s, %s' % (p.id, datetime.datetime.fromtimestamp(int(p.commit_time)).strftime('%Y-%m-%d %H:%M:%S')))
        repo.checkout_by(p.id)
        sloc(repo_path, ['.git'], ['.m', '.h', '.c', '.cpp'])
