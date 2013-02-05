import unittest
import re
from urlparse import urlparse
from string import printable
from fnmatch import fnmatch, translate
from pprint import pprint

from swarm_articles.dataset.datasource import NoContentDatasource
from swarm_articles.dataset.tree import TrieTree
from swarm_articles.app import map_datasources
from swarm.ext.http.helpers import URL

def urls(*urls):
    return [URL(url) for url in urls]




class TestDatasetMapping(unittest.TestCase):
    def setUp(self):
        self.dataset = TrieTree(printable)

    def test_prefixed_mapping0(self):
        self.dataset[u'http://google.com/*'] = NoContentDatasource('', _matcher=u'http://google.com/*')
        self.dataset[u'http://google.com/test'] = NoContentDatasource('', _matcher=u'http://google.com/test')
        self.dataset[u'http://google.com/test*'] = NoContentDatasource('', _matcher=u'http://google.com/test*')
        self.dataset[u'http://google.com/testz'] = NoContentDatasource('', _matcher=u'http://google.com/testz')
        self.dataset[u'http://google.com/'] = NoContentDatasource('', _matcher=u'http://google.com/')
        self.dataset[u'*'] = NoContentDatasource('', _matcher=u'*')
        print
        res = dict((k._matcher if k is not None else None, v)\
                      for k,v in \
                      map_datasources(urls('http://google.com/test',
                                           'http://google.com/test/of/test&a=1',
                                           'http://google.com/test/of/testo',
                                           'http://google.com/quasd',
                                           'http://google.com/',
                                           'http://google.com/testz',
                                           'http://google.com/testz/a',
                                           'http://google.com',
                                           'http://gogle.com/'),
                                      self.dataset).items())
        self.assertTrue(res == { None: ['http://google.com', 'http://gogle.com/'],
                                 u'http://google.com/': ['http://google.com/'],
                                 u'http://google.com/*': ['http://google.com/quasd'],
                                 u'http://google.com/test': ['http://google.com/test'],
                                 u'http://google.com/test*': ['http://google.com/test/of/test&a=1',
                                                              'http://google.com/test/of/testo',
                                                              'http://google.com/testz/a'],
                                 u'http://google.com/testz': ['http://google.com/testz']})

        
if __name__ == '__main__':
    unittest.main()
