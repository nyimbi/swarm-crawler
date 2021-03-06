from string import printable
import re
from urlparse import urlunparse
from itertools import chain, ifilter
from fnmatch import fnmatch

from werkzeug import cached_property

from swarm import transport, swarm
from swarm.ext.http.helpers import parser, URL
from ..text import PageText
from .tree import TrieTree as Tree


class DescribedMixin(object):
    @classmethod
    def info(cls):
        if cls.__doc__:
            yield cls.__doc__
        for base in cls.__bases__:
            if issubclass(base, DescribedMixin):
                for info in base.info():
                    yield info

    @classmethod
    def describe(cls):
        return 'Extracts ' + ' and '.join(cls.info())


class Datasource(object):
    __OMIT = ('dataset',)
    
    tags = None
    
    def __getstate__(self):
        return dict((k, v) for (k, v) in self.__dict__.items() \
                           if not k in self.__class__.__OMIT)

    RANGE = printable
    def __init__(self, dataset_path, **kwargs):
        self.dataset_path = dataset_path
        self.__dict__.update(kwargs)

    @cached_property
    def dataset(self):
        if self.dataset_path is not None:
            return Tree.load(self.dataset_path)

    def items(self):
        if False:
            yield

    def links(self):
        if False:
            yield

class LinksMixin(DescribedMixin):
    """links"""
    tests = ('deny_scheme',
             'allow_scheme',
             'deny_domain',
             'allow_domain',
             'deny_url',
             'allow_url',)

    modifiers = ('drop_fragment',)

    allow_schemas = None
    deny_schemas = ['javascript', 'mailto',]
    allow_domains = None
    deny_domains = None
    allow_urls = None
    deny_urls = [ '*.gif',
                  '*.jpeg',
                  '*.jpg',
                  '*.css',
                  '*.js',
                  '*.png',
                  '*.ico',
                  '*.xml'
                  ]
    unique = True

    cmdopts = { 'allow_schemas':{'default':allow_schemas,
                                 'nargs':'+',
                                 'help':'Allow only listed schemas'},
                'deny_schemas':{'default':deny_schemas,
                                'nargs':'+',
                                'help':'Deny listed schemas'},
                'allow_domains':{'default':allow_domains,
                                 'nargs':'+',
                                 'help':'Allow only listed domains (dot started treated as suffixes)'},
                'deny_domains':{'default':deny_domains,
                                 'nargs':'+',
                                 'help':'Deny listed domains (dot started treated as suffixes)'},
                'allow_urls':{'default':allow_urls,
                                 'nargs':'+',
                                 'help':'Regexps for allowed urls'},
                'deny_urls':{'default':deny_urls,
                             'nargs':'+',
                             'help':'Regexps for denied urls'},
                'no_unique':{'dest':'unique',
                             'default':unique,
                             'action':'store_false',
                             'help':'Disable following unique urls only'},
                }
    def fnmatch(self, value, matchers, ret):
        if any((fnmatch(value, matcher) for matcher in matchers)):
            return ret
        return not ret

    def deny_scheme(self, url):
        if not self.deny_schemas:
            return True
        
        return self.fnmatch(url.parsed.scheme, self.deny_schemas, False)

    def allow_scheme(self, url):
        if not self.allow_schemas:
            return True
        
        return self.fnmatch(url.parsed.scheme, self.allow_schemas, True)
    
    def deny_domain(self, url):
        if not self.deny_domains:
            return True
        return self.fnmatch(url.parsed.hostname, self.deny_domains, False)

    def allow_domain(self, url):
        if not self.allow_domains:
            return True

        return self.fnmatch(url.parsed.hostname, self.allow_domains, True)

    def allow_url(self, url):
        if not self.allow_urls:
            return True
        return self.fnmatch(urlunparse((None, None) + url.parsed[2:]),
                            self.allow_urls,
                            True)


    def deny_url(self, url):
        if not self.deny_urls:
            return True
        return self.fnmatch(urlunparse((None, None) + url.parsed[2:]),
                            self.deny_urls,
                            False)

    def drop_fragment(self, url):
        if not url.parsed.fragment:
            return url
        else:
            return URL(urlunparse(url.parsed[:5] + ('',)))

    def allowed(self, url):
        return all(getattr(self, test)(url) for test in self.tests)

    def modified(self, url):
        for modifier in (getattr(self, modifier) for modifier in self.modifiers):
            url = modifier(url)
        return url

    @parser
    def links(self, html):
        from swarm import swarm
        if html is None:
            return
        html.make_links_absolute(transport.url)
        for element, attribute, link, pos in html.iterlinks():
            url = URL(link)
            if not self.allowed(url):
                continue
            
            url = self.modified(url)
            if self.unique and self.is_unique(url):
                yield url
    
    def is_unique(self, url):
        if url in getattr(self, '_urls', []):
            return False
        elif not hasattr(self, '_urls'):
            self._urls = []
        self._urls.append(url)
        return True


class XpathParserMixin(DescribedMixin):
    """xpath selected content"""
    @parser
    def items(html):
        if False:
            yield

class ReadableMixin(DescribedMixin):
    """textual content"""
    greed = 1
    def items(self):
        yield PageText(transport.content, url=transport.url)\
              .winner(greed=self.greed)

class CmdlineArgsMixin(object):
    @classmethod
    def get_opts(cls):
        containers = cls.__bases__  + (cls,)
        return dict(ifilter(bool, chain(*(getattr(c,
                                                  'cmdopts',
                                                  {}).items() for c in containers))))

    @classmethod
    def populate_parser(cls, parser):
        for optname, kwargs in cls.get_opts().items():
            parser.add_argument('--%s'%optname.replace('_', '-'), **kwargs)

    def __unicode__(self):
        descr = 'Extract ' + ' and '.join(self.info())
        opts = []
        for optname in self.get_opts().keys():
            optvalue = getattr(self, optname, None)
            if optvalue and not optvalue == getattr(self.__class__, optname, None):
                opts += '%s:%s'%(optname, optvalue),

        return descr + (' (%s)'%(', '.join(opts)) if opts else '')


class NoContentDatasource(CmdlineArgsMixin, LinksMixin, Datasource):
    pass

class XpathContentOnlyDatasource(CmdlineArgsMixin, XpathParserMixin, Datasource):
    pass

class XpathDatasource(CmdlineArgsMixin, LinksMixin, XpathParserMixin, Datasource):
    pass

class ReadableContentOnlyDatasource(CmdlineArgsMixin, ReadableMixin, Datasource):
    pass

class ReadableDatasource(CmdlineArgsMixin, LinksMixin, ReadableMixin, Datasource):
    pass