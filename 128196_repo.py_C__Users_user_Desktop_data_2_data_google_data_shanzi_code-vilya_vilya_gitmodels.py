import os
import gzip
import shutil
from cStringIO import StringIO
from pygit2 import (
        Repository,
        init_repository,
        clone_repository)

from .objects import (
        Reference,
        Branch,
        Tag,
        Commit,
        File,
        )

from .query import (
        BranchQuery,
        TagQuery,
        CommitQuery,
        )



class GitRepo(Repository):

    @classmethod
    def create(cls, path, bare=True):
        init_repository(path, bare=True)
        return cls.get(path=path)

    @classmethod
    def get(cls, path):
        if os.path.isdir(path):
            return cls(path)

    def get_obj(self, key):
        return super(GitRepo, self).get(key)

    def delete(self):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path)

    def archive(self):
        content = self._jagare_repo.archive()
        outbuffer = StringIO()
        zipfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=outbuffer)
        zipfile.writelines(content)
        zipfile.close()
        out = outbuffer.getvalue()

    @property
    def updated_at(self):
        commit = self.commits.get('HEAD')
        if not commit:
            return 0
        return int(commit.author_timestamp)

    @property
    def commits(self):
        return CommitQuery(self, Commit) 

    @property
    def branches(self):
        return BranchQuery(self, Branch)

    @property
    def tags(self):
        return TagQuery(self, Tag)

    @property
    def head(self):
        return self.commits.get(ref='HEAD')

    @property
    def files(self):
        return self.head.files

    def writer(self):
        if self.head:
            return self.files.writer()
        else:
            from .objects import FileWriter
            return FileWriter(self)

