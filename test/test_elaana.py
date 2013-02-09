
from unittest import TestCase

from json import loads as json

import human_curl as requests # python-requests.org compatibile

from swarm.ext.http import HtmlSwarm

from swarm.ext.http.helpers import parser
from swarm import transport, swarm, define_swarm
from swarm_crawler.text import PageText

from swarm.helpers import show_in_browser

@parser
def pagination_links(html):
    return html.xpath('//a/@href')

define_swarm.start()
class Config(object):
    # DEBUG = True
    COMPETITORS = 2
    RELOADED_MODULE = 'swarm.ext.http.signal.cache'

elaana = HtmlSwarm(__name__)
elaana.config.from_object(Config)

@elaana.url('/test')
def ttt():
    with swarm('http://www.elaana.com/vb/t30926') << _:
        yield PageText(transport.content, url=transport.url).winner(0.05)
define_swarm.finish()

class TestElaana(TestCase):
    def test_elaana(self):
        for item in elaana('/test'):
            print item
            # print dparser.parse(item, fuzzy=True)