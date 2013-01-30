from os import path, listdir as ls, unlink
from shutil import move
from collections import OrderedDict as odict
import string

from werkzeug.utils import cached_property

from base64 import urlsafe_b64encode as encodestring, \
    urlsafe_b64decode as decodestring

from werkzeug.routing import UnicodeConverter

from flask import url_for, g, Response, request, current_app
from flask.ext.introspect import Tree, TreeView, TreeRootView, \
    ObjectViewMixin, DictViewMixin



from swarm.ext.articles.dataset.tree import TrieTree

from swarm.ext.articles.dataset.datasource import Datasource, ReadableDatasource
from swarm.ext.articles.dataset import get_dataset

from .namedview import NamedMethodView


class EmbeddedAssetsTree(Tree):

    @cached_property
    def popupsets(self):
        return list(self.aggregate_typestree_list((self.root_class, ),
                    'view.popupsets'))

    @cached_property
    def scripts(self):
        return list(self.aggregate_typestree_list((self.root_class, ),
                    'view.scripts'))


class DatasetsDict(dict):

    def __init__(self, app):
        self.app = app
        self.dataset_dir = \
            self.app.commands.articles.instance_dir('dataset')

    def keys(self):
        if not hasattr(self, '_keys'):
            self._keys = list(self.iterkeys())
        return self._keys

    def iterkeys(self):
        for name in ls(self.dataset_dir):
            yield name

    def __getitem__(self, name):
        if not dict.__contains__(self, name):
            dict.__setitem__(self, name,
                             TrieTree.load(path.join(self.dataset_dir,
                             name)))
        return dict.__getitem__(self, name)


class Base64Converter(UnicodeConverter):

    def to_python(self, value):
        tail = len(value) % 4 is 0 and 0 or 4 - len(value) % 4
        return decodestring(str(value) + tail * '=')

    def to_url(self, value):
        return encodestring(value).rstrip('=')


SCRIPT = """<script type="text/javascript" src="%s"></script>"""


class TreeRootView(DictViewMixin, TreeRootView):

    class view(NamedMethodView):

        popupsets = ['popupset/root.xml']
        context = 'root-popupset'

        scripts = (SCRIPT % url_for('static',
                   filename='underscore-min.js'), )

        def get(self, tree):
            return ('tree/children.xml', {})

        def put(self, tree):
            '''create new dataset'''

            dataset = get_dataset(current_app.commands.articles,
                                  request.values['name'])
            dataset.save()
            return ('tree/children.xml', {})


class DatasetView(DictViewMixin, TreeView):

    __type__ = TrieTree
    __headers__ = odict((('name', 'Name'), ))

    def get_names(self):
        return self.obj.children()

    def get_child(self, name):
        return self.obj[name]

    class view(NamedMethodView):

        popupsets = ['popupset/dataset.xml']
        context = 'dataset-popupset'

        def get(self, item):
            return ('tree/children.xml', {})

        def put(self, item):
            '''create new datasource'''
            dataset = get_dataset(current_app.commands.articles,
                      item.name)

            item.obj[request.values['name']] \
                = current_app.commands.articles\
                  .datasources[request.values['type']](dataset._path)
            item.obj.save(dataset._path)
            return ('tree/children.xml', {})

        def delete(self, item):
            '''delete dataset'''
            unlink(path.join(item.parent.obj.dataset_dir, item.name))
            g.item = item.parent
            return ('tree/children.xml', {})

        def post(self, item):
            dataset = get_dataset(current_app.commands.articles, item.name)
            dataset_dir = path.abspath(path.dirname(dataset._path))
            move(dataset._path, path.join(dataset_dir, request.values['name']))
            
            # g.item.obj = get_dataset(current_app.commands.articles,
            #                      request.values['name'])
            


class DatasourceView(DatasetView):

    __type__ = Datasource
    __recursive__ = True
    __converter__ = 'base64'
    __converters__ = {'base64': Base64Converter}

    @cached_property
    def dataset(self):
        if self.parent.__class__.__name__ == 'DatasetView':
            return self.parent.obj
        else:
            return self.parent.dataset

    def get_names(self):
        return self.dataset.children(self.name) \
            + self.obj.__dict__.keys()

    def get_child(self, name):
        if isinstance(name, unicode) and name in self.dataset:
            return self.dataset[name]

        return getattr(self.obj, name)

    def delete_sub_items(self):
        for name, subitem in self:
            subitem.delete_sub_items()
            del subitem.dataset[name]

    class view(NamedMethodView):

        popupsets = ['popupset/datasource.xml']
        context = 'datasource-popupset'

        def get(self, item):
            return ('tree/children.xml', {})

        def delete(self, item):            
            if 'subnodes' in request.values:
                item.delete_sub_items()
            del item.dataset[item.name]    
            item.dataset.save(item.obj.dataset_path)
            # return ('tree/children.xml', {})

        def post(self, item):
            newobj = current_app.commands.articles.\
                      datasources[request.values['typename']](item.obj.dataset_path)
            for name, value in item.obj.__dict__.items():
                setattr(newobj, name, value)
            item.dataset[item.name] = newobj
            item.dataset.save(item.obj.dataset_path)

            # return ('tree/children.xml', {})


