import logging


from swarm import transport, swarm, define_swarm
from swarm.ext.http import HtmlSwarm
from swarm.ext.articles.text import PageText
 
define_swarm.start()

articles = HtmlSwarm(__name__)

@articles.url('/crawl/<path:url>')
def crawl(url, greed=1):
    with swarm(url) << 'greed':
        yield PageText(transport.content,
                           url=transport.url).winner(greed=greed)

define_swarm.finish()