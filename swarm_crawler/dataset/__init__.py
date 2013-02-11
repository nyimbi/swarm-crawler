from os import path

from .datasource import Datasource
from .tree import TrieTree as Tree
from ..helpers import included_local_path

def save(_path):
    def _save(self, *args, **kwargs):
        Tree.save.__get__(self, self.__class__)(_path)
    return _save

def get_dataset(app, name):
    with included_local_path():
        _dataset = path.join(app.instance_dir('dataset'), name)
        if not path.exists(_dataset):
            tree = Tree(Datasource.RANGE)
        else:
            tree = Tree.load(_dataset)
        tree.save = save(_dataset).__get__(tree, tree.__class__)
        tree._path = _dataset
        tree._name = name
        return tree
