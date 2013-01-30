import logging
from pprint import pprint
from urlparse import urlparse, urlunparse
import re
from collections import defaultdict

from werkzeug.datastructures import ImmutableDict
from werkzeug.utils import import_string

from swarm.helpers import obj_converter
from swarm.config import ConfigAttribute
from swarm import transport, swarm, define_swarm
from swarm.ext.http import HtmlSwarm
from swarm.ext.http.helpers import parser
from swarm.ext.articles.text import PageText

def dict_converter(dct):
    d = {}
    for key in dct:
        d[key] = import_string(dct[key])
    return d

class ArticlesSwarm(HtmlSwarm):
    default_config = ImmutableDict(HtmlSwarm.default_config,
                     **{'NON_CONTENT':[ '.gif',
                                        '.jpeg',
                                        '.jpg',
                                        '.css',
                                        '.js',
                                        '.png',
                                        '.ico',
                                        '.xml'],
                        'SAVE_STATE':True,
                        'DATASOURCES': {'no-content':'swarm.ext.articles.dataset.datasource.NoContentDatasource',
                                        'xpath-content-only':'swarm.ext.articles.dataset.datasource.XpathContentOnlyDatasource',
                                        'xpath':'swarm.ext.articles.dataset.datasource.XpathDatasource',
                                        'readable-content-only':'swarm.ext.articles.dataset.datasource.ReadableContentOnlyDatasource',
                                        'readable':'swarm.ext.articles.dataset.datasource.ReadableDatasource'
                                        }
                    })

    item_class = ConfigAttribute('ITEM_CLASS', get_converter=obj_converter)
    datasources = ConfigAttribute('DATASOURCES', get_converter = dict_converter)

define_swarm.start()

articles = ArticlesSwarm(__name__)

def map_datasources(urls, dataset, default=None):
    if dataset is None:
        if default is not None:
            return {default:urls}
        else:
            return {}
    
    _map = defaultdict(list)
    
    for url in urls:
        ds_keys = dataset.prefixes(url)
        if ds_keys:
            datasource = dataset[ds_keys[-1]]
        elif default:
            datasource = default
        else:
            continue
        _map[datasource].append(url)
    return _map

define_swarm.start()

test = ArticlesSwarm(__name__)

def crawl(urls, datasource, default='*'):
    with swarm(*urls) << 'datasource, default':
        for item in datasource.items():
            yield item

        for datasource, urls in map_datasources(datasource.links(),
                                                datasource.dataset,
                                                default=default).items():
            crawl(urls, datasource, default)

@articles.url('/crawl')
def start(urls=[], datasource=None, default=None):
    crawl(urls, datasource, default=default)

define_swarm.finish()