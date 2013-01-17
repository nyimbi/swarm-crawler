from os import path, listdir as ls
from collections import OrderedDict as odict
from werkzeug.utils import cached_property

from base64 import (urlsafe_b64encode as encodestring,
                    urlsafe_b64decode as decodestring)


from werkzeug.routing import UnicodeConverter

from flask import url_for, g, Response
from flask.ext.introspect import Tree, TreeView, TreeRootView, ObjectViewMixin, DictViewMixin
from flask.views import MethodView

from swarm.ext.articles.dataset.tree import TrieTree
from swarm.ext.articles.dataset.datasource import Datasource

class EmbeddedAssetsTree(Tree):
    @cached_property
    def popupsets(self):
        return list(self.aggregate_typestree_list((self.root_class,),
                    'view.popupsets'))

    @cached_property
    def scripts(self):
        return list(self.aggregate_typestree_list((self.root_class,),
                    'view.scripts'))

class DatasetsDict(dict):
    def __init__(self, app):
        self.app = app
        self.dataset_dir = self.app.commands.articles.instance_dir('dataset')

    def keys(self):
        if not hasattr(self, '_keys'):
            self._keys = list(self.iterkeys())
        return self._keys

    def iterkeys(self):
        for name in ls(self.dataset_dir):
            yield name

    def __getitem__(self, name):
        if not dict.__contains__(self, name):
            dict.__setitem__(self,
                             name,
                             TrieTree.load(path.join(self.dataset_dir, name)))
        return dict.__getitem__(self, name)


class Base64Converter(UnicodeConverter):
    def to_python(self, value):
        tail = len(value) % 4 is 0 and 0 or 4 - len(value) % 4
        return decodestring(str(value) + tail*'=')

    def to_url(self, value):
        return encodestring(value).rstrip('=')       
SCRIPT = """<script type="text/javascript" src="%s"></script>"""

class TreeRootView(DictViewMixin, TreeRootView):
    class view(MethodView):
        popupsets = ['popupset/root.xml',]
        popupset = 'root-popupset'      

        scripts = (SCRIPT%url_for('ample.static', filename='underscore-min.js'),)
        def get(self, tree):
            print tree.popupsets
            return 'treechildren/root.xml', {}

        def put(self, tree):
            '''create new dataset'''
            print 'create new dataset', request.values


class DatasetView(DictViewMixin, TreeView):
    __type__ = TrieTree
    __headers__ = odict((('name', 'Name'),))
    
    def get_names(self):
        return self.obj.children()

    def get_child(self, name):
        return self.obj[name]

    class view(MethodView):
        popupsets = ['popupset/dataset.xml',]
        popupset = 'dataset-popupset'

        def get(self, item):
            return 'treechildren/dataset.xml', {}

        def put(self, item):
            '''create new datasource'''
            print 'create new datasource', request.values

        def delete(self, item):
            '''delete datset'''
            print 'delete', item, request.values

class DatasourceView(DatasetView):
    __type__ = Datasource
    __recursive__ = True
    __converter__ = 'base64'
    __converters__ = {'base64':Base64Converter}

    @cached_property
    def dataset(self):
        if self.parent.__class__.__name__ == 'DatasetView':
            return self.parent.obj
        else:
            return self.parent.dataset

    def get_names(self):
        return self.dataset.children(self.name) + self.obj.__dict__.keys()

    def get_child(self, name):
        if isinstance(name, unicode) and name in self.dataset:
            return self.dataset[name]

        return getattr(self.obj, name)

    class view(MethodView):
        popupsets = ['popupset/datasource.xml',]
        popupset = 'datasource-popupset'
        
        def get(self, item):
            return 'treechildren/dataset.xml', {}

        def delete(self, item):
            if request.values['subtree']:
                print 'delete subtree', item
            else:
                print 'delete', item

        def post(self, item):
            print 'change %s type to %s'%(item, request.values['typename'])