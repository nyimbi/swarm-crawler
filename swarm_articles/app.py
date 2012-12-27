
import logging
from pprint import pprint
from urlparse import urlparse, urlunparse
import re

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
                        'ITEM_CLASS':PageText,
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

@parser
def document_urls(html):
    if html is None:
        return
    html.make_links_absolute(transport.url)
    for element, attribute, link, pos in html.iterlinks():
        if any((link.endswith(NON_DOCUMENT) for NON_DOCUMENT in swarm.object.config['NON_DOCUMENT_CONTENT'])):
            continue
        if not '#' in link:
            yield link
        else:
            yield urlunparse(urlparse(link)[:5] + ('',))

def filter_domains(urls, domains=[]):
    for url in urls:
        parsed = urlparse(url)
        for domain in domains:
            if domain.startswith('.') and parsed.hostname.endswith(domain[1:]):
                yield url
                break
            elif parsed.hostname == domain:
                yield url
                break

def filter_by_regexps(urls, regexps=[], allow=True):
    for url in urls:
        matches = any((re.match(regexp, url) for regexp in regexps))
        if allow and matches:
            yield url
        elif not allow and not matches:
            yield url

def crawl(  urls=[],
            greed=1,
            follow=True,
            allow_links=[],
            deny_links=[],
            limit_domains=[],
            item_class=None):

    if item_class is None:
        item_class = swarm.object.item_class

    with swarm(*urls) << 'greed, limit_domains, follow, allow_links, deny_links, item_class':
        yield item_class(transport.content,
                       url=transport.url).winner(greed=greed)
        if not follow:
            return
        urls = document_urls()
        if limit_domains:
            urls = filter_domains(urls, limit_domains)

        if allow_links:
            urls = filter_by_regexps(urls, allow_links)
        if deny_links:
            urls = filter_by_regexps(urls, deny_links, allow=False)

        crawl(urls=list(set(urls)),
              greed=greed,
              limit_domains=limit_domains,
              follow=follow,
              allow_links=allow_links,
              deny_links=deny_links,
              item_class=item_class)

@articles.url('/crawl')
def start(datasource=None, **kwargs):    
    if datasource is None:
        crawl(**kwargs)

define_swarm.finish()