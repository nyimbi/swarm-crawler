import logging
from copy import copy
import sys
import re
from fnmatch import fnmatch, translate
from collections import defaultdict

from werkzeug.datastructures import ImmutableDict
from werkzeug.utils import import_string

from swarm.helpers import obj_converter
from swarm.config import ConfigAttribute
from swarm import transport, swarm, define_swarm
from swarm.ext.http import HtmlSwarm
from swarm.ext.http.helpers import parser
from swarm.ext.crawler.text import PageText
from swarm.ext.crawler.helpers import included_local_path

def dict_converter(dct):
    with included_local_path():
        d = {}
        for key in dct:
            d[key] = import_string(dct[key])
        return d

class CrawlerSwarm(HtmlSwarm):
    default_config = ImmutableDict(HtmlSwarm.default_config,
                     **{'SAVE_STATE':True,
                        'DATASOURCES': {'no-content':'swarm.ext.crawler.dataset.datasource.NoContentDatasource',
                                        'xpath-content-only':'swarm.ext.crawler.dataset.datasource.XpathContentOnlyDatasource',
                                        'xpath':'swarm.ext.crawler.dataset.datasource.XpathDatasource',
                                        'readable-content-only':'swarm.ext.crawler.dataset.datasource.ReadableContentOnlyDatasource',
                                        'readable':'swarm.ext.crawler.dataset.datasource.ReadableDatasource'
                                        },
                        'OUTPUT':{}
                    })

    item_class = ConfigAttribute('ITEM_CLASS', get_converter=obj_converter)
    datasources = ConfigAttribute('DATASOURCES', get_converter = dict_converter)
    output = ConfigAttribute('OUTPUT', get_converter = dict_converter)

FNMATCHER_SUFFIX_LEN = len(translate('')) - 1
def is_fnmatcher(re_pattern):
    return translate(re_pattern).replace('\\', '')[:-FNMATCHER_SUFFIX_LEN] != re_pattern\
            or bool(re.match(r'^.*\[.*\].*$', re_pattern))

def non_fnmatchers(dataset):
    return [url for url in dataset.keys() if not is_fnmatcher(url)]

define_swarm.start()

crawler = CrawlerSwarm(__name__)

def map_to_datasource(url, dataset):
    url = unicode(url)
    for prefix in reversed(dataset.prefixes(url)):
        if prefix == url:
            return dataset[prefix]
        for suffix in reversed(list(dataset.suffixes(prefix))):
            if url == prefix+suffix or fnmatch(url, prefix+suffix):
                return dataset[prefix+suffix]
        if fnmatch(url, prefix):
            return dataset[prefix]

def map_datasources(urls, dataset):
    _map = defaultdict(list)

    for url in urls:
        datasource = map_to_datasource(url, dataset)
        _map[datasource].append(url)
    return _map

define_swarm.start()

def crawl(urls, datasource):
    with swarm(*urls) << 'datasource':
        for item in datasource.items():
            yield item

        for (datasource, urls) \
            in map_datasources(datasource.links(),
                               datasource.dataset).items():
            crawl(urls, datasource)

@crawler.url('/crawl')
def start(urls=[], datasource=None):
    crawl(urls, datasource)

define_swarm.finish()