
import logging
from pprint import pprint
from urlparse import urlparse, urlunparse
import re

from werkzeug.datastructures import ImmutableDict

from swarm import transport, swarm, define_swarm
from swarm.ext.http import HtmlSwarm
from swarm.ext.http.helpers import parser
from swarm.ext.articles.text import PageText

class ArticlesSwarm(HtmlSwarm):
    default_config = ImmutableDict(HtmlSwarm.default_config,
                     **{'NON_DOCUMENT_CONTENT':['.gif',
                                                '.jpeg',
                                                '.jpg',
                                                '.css',
                                                '.js',
                                                '.png',
                                                '.ico',
                                                '.xml'],
                        'SAVE_STATE':True,
                    })

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
            limit_domains=[],):

    with swarm(*urls) << 'greed, limit_domains, follow, allow_links, deny_links':
        yield PageText(transport.content,
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

        urls = list(set(urls))
        crawl(urls=urls,
              greed=greed,
              limit_domains=limit_domains,
              follow=follow,
              allow_links=allow_links,
              deny_links=deny_links)

@articles.url('/start')
def start(datasource=None, **kwargs):    
    if datasource is None:
        crawl(**kwargs)

define_swarm.finish()