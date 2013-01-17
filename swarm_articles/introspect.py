from copy import copy
from operator import getitem, add, mul
from inspect import isgenerator
from collections import OrderedDict, Sequence, Mapping, defaultdict
from numbers import Number
from itertools import chain, compress, izip_longest
from weakref import ref


# from swarm.ext.articles.dataset.tree import TrieTree
from werkzeug.utils import cached_property

class class_property(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

class TreeViewBase(type):
    uninherited_map = {'__names__': 'names',
                       '__namedchild__': 'get_child',
                       '__namedheader__': 'get_header'}
    def __new__(meta, name, bases, members):        
        # print '!!', name
        copied = {}
        for _name, uninherited_name in meta.uninherited_map.items():
            #that methods renamed to internal names only if immediate base defines it
            for base in bases:
                if uninherited_name in base.__dict__:
                    copied[_name] = getattr(base, uninherited_name)

        new_type = super(TreeViewBase, meta).__new__(meta, name, bases, members)

        if bases == (object,):
            return new_type

        for _name, copied_method in meta.uninherited_map.items():
            if _name in copied:
                continue

            if copied_method in members:
                # print '\tSetting `%s` to `%s`'%(_name, members[copied_method])
                setattr(new_type, _name, members[copied_method].__get__(None, new_type))
                continue


            # print '\tSetting `%s` to `%s`'%(_name, getattr(TreeView, _name))
            setattr(new_type,
                    _name, 
                    getattr(TreeView, _name).__get__(None, new_type))

        for _name, copied_method in copied.items():
            if copied_method in members:
                # print '\tSetting `%s` to `%s`'%(_name, members[copied_method])
                setattr(new_type, _name, members[copied_method].__get__(None, new_type))
                continue

            # print '\tSetting `%s` to `%s`'%(_name, copied_method)
            setattr(new_type, _name, copied[_name].__get__(None, new_type))
        # pprint (dict(new_type.__dict__))
        return new_type

class TreeView(object):
    __metaclass__ = TreeViewBase
    __type__ = object

    def __init__(self, obj, tree, parent=None):
        self.obj = obj
        if isinstance(tree, ref):
            self._tree = tree
        else:
            self._tree = ref(tree)

        if isinstance(parent, ref):
            self._parent = parent
        elif parent is not None:
            self._parent = ref(parent)
        else:
            self._parent = parent
    @property
    def parent(self):
        if self._parent:
            return self._parent()

    @property
    def tree(self):
        if self._tree:
            return self._tree()


    def __names__(self):
        if False:
            yield

    def __namedchild__(self, name):
        pass

    def __namedheader__(self, item_name, header_key):
        return None

    def __children__(self, leafs=None):
        for name, value in self.__items__():
            cell = []
            tree = self.tree
            if 'get_header' in value.__class__.__dict__ or \
                not any((isinstance(value, leaf_class)\
                        for leaf_class 
                        in tree.leaf_classes)):
                for header_key in tree._header_keys:
                    cell.append(value.__namedheader__(name, header_key))

            yield name, cell, value

    def __items__(self):
        for name in self.__names__():
            value = self.__namedchild__(name)
            if not value:
                continue
            value = self.map(value, self.tree, parent=self.obj)
            if value:
                yield (name, value)

    def traverse(self, depth=0):
        for name, cell, view in self.__children__():
            yield depth, name, cell, view
            for item in view.traverse(depth+1):
                yield item

    def pformat(self, depth=0, indent='\t', format='%s%s: %s <%s>\n', indenter=mul):
        for depth, name, cell, view in self.traverse(depth):
            yield format%(indenter(indent, depth), name, cell, view)
            
    def pprint(self,  depth=0, indent='\t', format='%s%s: %s <%s>\n', indenter=mul):
        for s in self.pformat(depth, indent, format):
            print s,



    @staticmethod
    def _header_views(roots, leafs=[]):
        #views here corresponds to dict.view***()
        for root in roots:
            subs = root.__subclasses__()
            for sub in subs:
                if sub in leafs:
                    continue
                if '__headers__' in sub.__dict__:
                    yield sub.__headers__.viewitems()

            for item in TreeView._header_views(subs, leafs):
                yield item

    @class_property
    @classmethod
    def viewmap(cls):
        if not '_candidates' in cls.__dict__:
            setattr(cls, '_candidates', defaultdict(list))
            for sub in cls.__subclasses__():
                if '__type__' in sub.__dict__:
                    cls._candidates[sub.__dict__['__type__']].append(sub)

        return cls.__dict__['_candidates']

    @classmethod
    def candidates(cls, obj):
        for _type in cls.viewmap:
            if isinstance(obj, _type):
                for candidate in cls.viewmap[_type]:
                    yield candidate

    @classmethod
    def map(cls, obj, tree, candidates=None, parent=None):
        
        if candidates is None:
            candidates = list(cls.candidates(obj))
        else:
            candidates = copy(candidates)

        if not candidates:
            return

        if len(candidates) == 1:
            return candidates[0](obj, tree, parent)


        candidates = [c for c in candidates if hasattr(c, 'score')]
        scorers = [candidate.score for candidate in candidates]

        scores = izip_longest(*(((s, score) for s in score(obj)) for score in scorers),
                               fillvalue=(None, None))
        for score in scores:
            results = [s[0] for s in score]
            
            candidates = list(compress(candidates, 
                                       (r is not None for r in results)))
            if len(candidates) == 1:
                return candidates[0](obj, tree, parent)
            
            results = list(compress(results,
                                    (r is not None for r in results)))
            
            if all(results) or not any(results):
                continue

            candidates = list(compress(candidates,
                                       (r is not True for r in results)))

            if len(candidates) == 1:
                return candidates[0](obj, tree, parent)

        return candidates[0](obj, tree, parent)

    @classmethod
    def score(cls, obj):
        yield False

class Tree(object):
    def __init__(self,
                 objects,
                 leaf_classes,
                 primary=None,
                 root_view_classes=[TreeView,]):

        self.root_view_classes = root_view_classes
        self.leaf_classes = leaf_classes
        self._objects = objects
        self.primary_label = primary

    @cached_property
    def objects(self):
        if isinstance(self._objects, Sequence):
            return self._objects

        if isgenerator(self._objects):
            return list(self._objects)

        else:
            return [self._objects,]
    
    @cached_property
    def _headers(self):
        keys = []
        labels = []
        for key, label in chain(*TreeView._header_views(self.root_view_classes,
                                                        self.leaf_classes)):
            if not label in labels:
                keys.append(key)
                labels.append(label)
        return keys, labels

    @cached_property
    def _header_keys(self):
        return self._headers[0]

    @cached_property
    def _header_labels(self):
        return self._headers[1]

    def iter_roots(self, objects, view_classes):
        for obj in objects:
            for view_class in view_classes:
                view = view_class.map(obj, self, candidates=view_classes)
                if view:
                    yield view
                    break

    @cached_property
    def roots(self):
        return list(self.iter_roots(self.objects, self.root_view_classes))

    def iter_children(self, roots):
        for root in self.roots:
            for child in root.__children__():
                yield child
        if False:
            yield

    @cached_property
    def children(self):
        return list(self.iter_children(self.roots))

class ObjectViewMixin:
    def names(self):
        for k in self.obj.__dict__.iterkeys():
            if not k.startswith('__'):
                yield k

    def get_child(self, name, default=None):
        return getattr(self.obj, name)

    def get_header(self, item_name, key):
        return getattr(self.obj, key, None)


class DictViewMixin:
    def names(self):
        for k in self.obj.iterkeys():
            yield k

    def get_child(self, name, default=None):
        return getitem(self.obj, name)