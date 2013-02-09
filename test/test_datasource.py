import unittest
from urlparse import urlparse
from swarm_crawler.dataset.datasource import NoContentDatasource
from swarm.ext.http.helpers import URL


def urls(*urls):
    return [URL(url) for url in urls]

def allowed(ds, *urls):
    return [ds.allowed(url) for url in urls]

class TestDatasourceFiltering(unittest.TestCase):
    def test_allowed_domains(self):
        self.assertTrue(allowed(NoContentDatasource('', 
                             allow_domains=['test*']),
                             *urls('http://google.com/')) == [False])

        self.assertTrue(allowed(NoContentDatasource('', 
                             allow_domains=['test*', 'google.com']),
                             *urls('http://google.com/')) == [True,])

    def test_denied_domains(self):
        self.assertTrue(allowed(NoContentDatasource('', 
                             deny_domains=['test*']),
                             *urls('http://google.com/')) == [True])

        self.assertTrue(allowed(NoContentDatasource('', 
                             deny_domains=['test*', 'google.com']),
                             *urls('http://google.com/')) == [False,])

    def test_allowed_denied_domains(self):
        self.assertTrue(allowed(NoContentDatasource('', 
                             deny_domains=['www.google.com'],
                             allow_domains=['*google.com*']),
                             *urls('http://google.com/',
                                'http://www.google.com/',
                                'http://www.google.com.ua/google.com.ua',
                                'http://yandex.ru/')) \
                        == [True, False, True, False])
    def test_allowed_denied_urls(self):
        self.assertTrue(allowed(NoContentDatasource('', 
                                     allow_urls=['*/test*'],
                                     deny_urls=['*google*']),
                                     *urls('http://google.com/test',
                                           'http://test.com/google/test'))\
                                     == [True, False])

    def test_allowed_denied_schemas(self):
        self.assertTrue(allowed(NoContentDatasource('',),
                                     *urls('http://google.com/test',
                                           'javascript://test.com/google/test',
                                           'https://test.com/google/test'))\
                                     == [True, False, True])

        self.assertTrue(allowed(NoContentDatasource('',allow_schemas=('http',)),
                                     *urls('http://google.com/test',
                                           'javascript://test.com/google/test',
                                           'https://test.com/google/test'))\
                                     == [True, False, False])
        
if __name__ == '__main__':
    unittest.main()