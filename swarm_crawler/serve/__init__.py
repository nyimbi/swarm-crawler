from os import path
from pprint import pprint
from collections import Sequence
from itertools import chain

from flask import Flask, current_app, render_template

from flask.ext.introspect import blueprint as rest
from flask.ext.ample import AmpleMarkup


class Config(object):

    DEBUG = True
    DEFAULT_DATASOURCE_TYPE = 'readable'
    SERVER_NAME = 'localhost:5000'

web = Flask(__name__)

web.config.from_object(Config)
AmpleMarkup(web)

with web.app_context():
    from treemap import *


def get_objects():
    return DatasetsDict(current_app)


datasets = rest(
    'dataset',
    __name__,
    get_objects,
    template_base='dataset-tree-page.html',
    xhr_template_base='xml-fragment.xml',
    roots=DatasetView,
    tree_class=EmbeddedAssetsTree,
    super_root_class=TreeRootView,
    leaf_classes = (DatasourceView,)
    )

editor = rest(
    'editor',
    __name__,
    get_objects,
    template_base='editor-page.xml',
    xhr_template_base='xml-fragment.xml',
    roots=DatasetView,
    # tree_class=EmbeddedAssetsTree,
    super_root_class=TreeRootView,
    leaf_classes = ()
    )

web.register_blueprint(datasets, url_prefix='/dataset')
web.register_blueprint(editor, url_prefix='/edit')

@web.context_processor
def define_datasource_types():
    return {'datasource_types':dict((name, ds.describe()) \
                                    for (name, ds) \
                                    in web.commands.crawler.datasources.items()),
            'zip':zip,
            'getattr':getattr,
            'hasattr':hasattr,
            'enumerate':enumerate}