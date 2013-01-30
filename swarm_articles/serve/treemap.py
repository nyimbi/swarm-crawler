from os import path, listdir as ls, unlink
from shutil import move, copy
from collections import OrderedDict as odict, Sequence
import string

from werkzeug.utils import cached_property

from base64 import urlsafe_b64encode as encodestring, \
    urlsafe_b64decode as decodestring

from werkzeug.routing import UnicodeConverter

from flask import url_for, g, Response, request, current_app, render_template
from flask.ext.introspect import Tree, TreeView, TreeRootView, \
    ObjectViewMixin, DictViewMixin



from swarm.ext.articles.dataset.tree import TrieTree

from swarm.ext.articles.dataset.datasource import Datasource, ReadableDatasource
from swarm.ext.articles.dataset import get_dataset

from .namedview import NamedMethodView, namedmethod


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
    

    def get_names(self):
        return self.obj.children()

    def get_child(self, name):
        return self.obj[name]

    def get_cell(self, objname, name):
        if name == 'name':
            return objname
        else:
            return 'Dataset info'

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
            if request.values['copy'] == u'true':
                op = copy
            else:
                op = move
            op(dataset._path, path.join(dataset_dir, request.values['name']))
            
            # g.item.obj = get_dataset(current_app.commands.articles,
            #                      request.values['name'])
            
NOTEXTIST = object()

class DatasourceView(DatasetView):

    __type__ = Datasource
    __recursive__ = True
    __converter__ = 'base64'
    __converters__ = {'base64': Base64Converter}
    __cell__ = odict((('name', 'Name'), ('info', 'Info')))

    @cached_property
    def dataset(self):
        if self.parent.__class__.__name__ == 'DatasetView':
            return self.parent.obj
        else:
            return self.parent.dataset

    def get_names(self):
        return list(set(self.dataset.children(self.name) \
                            + self.obj.__dict__.keys()\
                            + list(set(dir(type(self.obj))).intersection(set(self.view.editable_fields)))))

    def get_child(self, name):
        if isinstance(name, unicode) and name in self.dataset:
            return self.dataset[name]
        child = self.obj.__dict__[name] \
                if name in self.obj.__dict__ \
                else getattr(type(self.obj), name)

        if child is None:
            child = self.view.editable_fields[name]()
        return child

    def get_cell(self, objname, name):
        if name == 'name':
            return objname
        else:
            return self.obj.describe()

    def delete_sub_items(self):
        for name, subitem in self:
            subitem.delete_sub_items()
            del subitem.dataset[name]



    class view(NamedMethodView):
        popupsets = ['popupset/datasource.xml']
        context = 'datasource-popupset'
        editable_fields = {'allow_schemas':list,
                           'deny_schemas':list,
                           'allow_domains':list,
                           'deny_domains':list,
                           'allow_urls':list,
                           'deny_urls':list,
                           'unique':bool,
                           'greed':int,
                           'tags':list}

        def get(self, item):
            return ('tree/children.xml', {})

        @namedmethod('editor', 'get')
        def get_editor(self, item):
            return ('tree/editor.xml', {})

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


class StringAttributeView(DatasourceView):
    __type__ = basestring

    class view(NamedMethodView):
        @classmethod
        def render(cls, name, view):
            return render_template('fields/basestring.xml', view=view)

        @namedmethod('editor', 'put')
        def put(self, item):
            setattr(item.parent.dataset[item.parent.name], item.name, request.values['value'])
            item.parent.dataset.save(item.parent.obj.dataset_path)
            item.obj = getattr(item.parent.dataset[item.parent.name], item.name)
            return ('fields/basestring.xml', {'view':item, 'status':'OK!'})

class StringSequenceAttributeView(DatasourceView):
    __type__ = Sequence

    class view(NamedMethodView):
        @classmethod
        def render(cls, name, view):
            return render_template('fields/sequence.xml', view=view)

        @namedmethod('editor', 'put')
        def put(self, item):
            n = int(request.values['n'])

            datasource = item.parent.dataset[item.parent.name]
            if not item.name in datasource.__dict__:
                default = getattr(datasource.__class__, item.name)
                if default is None:
                    datasource.__dict__[item.name] = []
                else:
                    datasource.__dict__[item.name] = default

            status = [None]*len(datasource.__dict__[item.name])
            if len(datasource.__dict__[item.name])>n:
                datasource.__dict__[item.name][n] = request.values['value']
                status[n] = '#0cf00c'
            else:
                datasource.__dict__[item.name].append(request.values['value'])
                status.append('#0cf00c')

            item.parent.dataset.save(item.parent.obj.dataset_path)
            item.obj = getattr(item.parent.dataset[item.parent.name], item.name)
            return ('fields/sequence.xml', {'view':item, 'status':status})

        @namedmethod('editor', 'delete')
        def delete(self, item):
            datasource = item.parent.dataset[item.parent.name]
            if not item.name in datasource.__dict__:
                return
            n = int(request.values['n'])
            if len(datasource.__dict__[item.name])<=n:
                return

            del datasource.__dict__[item.name][n]
            item.parent.dataset.save(item.parent.obj.dataset_path)
            return ('fields/sequence.xml', {'view':item})