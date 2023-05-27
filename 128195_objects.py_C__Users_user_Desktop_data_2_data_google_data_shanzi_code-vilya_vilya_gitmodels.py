from pygit2 import (
        Object,
        Signature,
        Tree,
        TreeEntry,
        )
from pygit2 import (
        GIT_REF_SYMBOLIC,
        GIT_FILEMODE_BLOB,
        GIT_FILEMODE_TREE,
        )

from .query import (
        CommitQuery,
        BranchQuery,
        FileQuery,
        )
import os

class InvalidProperty(Exception):

    def __init__(self, name, detail=''):
        self._name = name
        self._detail = detail

    def __unicode__(self):
        desc = u"Invalid Property '%s'"
        if self._detail:
            desc += '(%s)' % self._detail
        return desc


class ObjectProxy(object):

    def __init__(self, repo, obj):
        self._repo = repo
        self._object = obj

    def __getattr__(self, key):
        obj = getattr(self._object, key)
        if callable(obj):
            setattr(self, key, obj)
        return obj

    def __unicode__(self):
        return unicode(self.oid.hex)

    def __eq__(self, obj):
        try:
            return self.oid.hex == obj.oid.hex
        except:
            return False

    def __bool__(self):
        return True if self._object else False


class Reference(ObjectProxy):

    def __init__(self, repo, obj):
        if obj.type == GIT_REF_SYMBOLIC:
            obj = obj.resolve()
        super(Reference, self).__init__(repo, obj)

    @property
    def commits(self):
        query = CommitQuery(self._repo, Commit)
        return query.where(from_id=self.target)

    def __unicode__(self):
        return unicode(self.name)


class Branch(Reference):
    
    def add_commit(self, author, email, message, tree):
        commit = self.commits.create(
                self.name,
                self.commits.last.hex,
                author, email, message,
                tree)
        self._object = self._repo.lookup_branch(self.shorthand)
        return commit

class Tag(Reference):
    pass


class Commit(ObjectProxy):

    @property
    def files(self):
        query = FileQuery(self._repo, File)
        return query.where(commit=self._object)

    def __unicode__(self):
        return self._object.hex


class File(ObjectProxy):

    def __init__(self, repo, obj):
        if isinstance(obj, TreeEntry):
            self.name = obj.name
            self.filemode = obj.filemode
            obj = repo[obj.oid]
        return super(File, self).__init__(repo, obj)

    def isdir(self):
        return isinstance(self._object, Tree)

    def isfile(self):
        return not self.isdir()

    def listdir(self):
        return list(self)

    def writer(self):
        if self.isdir():
            return FileWriter(self._repo, self._object)

    def __iter__(self):
        if self.isdir():
            for entry in self._object:
                yield File(self._repo, entry)

    def __getitem__(self, key):
        if self.isdir():
            return File(self._repo, self._object[key])


class FileWriter(object):

    def __init__(self, repo, tree=None):
        super(FileWriter, self).__init__()
        self._repo = repo
        self._structure = {}
        self._treebuilder = repo.TreeBuilder(tree) if tree else repo.TreeBuilder()

    def log_operation(self, path, data=''):
        repo = self._repo
        placeholder = self._repo.create_blob(data) if data!=None else data
        components = path.split(os.path.sep)
        structure = self._structure
        for c in components[:-1]:
            if c: 
                structure[c] = structure.get(c) or {}
                structure = structure[c]
        structure[components[-1]] = placeholder

    def write(self, path, data=''):
        data = data or ''
        self.log_operation(path, data)

    def remove(self, path):
        self.log_operation(path, None)

    def _apply_change(self, treebuilder, dict_):
        repo = self._repo
        for k, v in dict_.iteritems():
            if isinstance(v, dict):
                subtree = treebuilder.get(k)
                subbuilder = repo.TreeBuilder(repo[subtree.oid]) if subtree else repo.TreeBuilder()
                oid = self._apply_change(subbuilder, v)
                treebuilder.insert(k, oid, GIT_FILEMODE_TREE)
            elif v:
                treebuilder.insert(k, v, GIT_FILEMODE_BLOB)
            else:
                treebuilder.remove(k)
        return treebuilder.write()

    def save(self):
        if self._structure:
            oid = self._apply_change(self._treebuilder, self._structure)
            return oid
