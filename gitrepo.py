from pygit2 import Repository
from pygit2 import GIT_SORT_TOPOLOGICAL, GIT_SORT_REVERSE

class GitRepo:
    def __init__(self, repo_path):
        self.repo = Repository(repo_path)

    def checkout_by(self, commit_id):
        ref = 'refs/tags/t-%s' % commit_id

        if self.repo.references.get(ref) is None:
            self.repo.create_reference(ref, commit_id)

        self.repo.checkout(ref)
        self.repo.references[ref].delete()

    def master(self):
        branch = self.repo.lookup_branch('master')
        self.repo.checkout(branch)

    def get_all_commit_id(self):
        self.master()
        return self.repo.walk(self.repo.head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE)
