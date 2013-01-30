import logging
import sys
import os
from pprint import pprint
from argparse import Action
from cliff.command import Command
from cliff.lister import Lister

from werkzeug.utils import import_string

from swarm.ext.articles.app import map_datasources
from swarm.ext.articles.dataset import get_dataset

class int_or_float(Action):
    def __call__(self, parser, args, value, option_string=None):
        try:
            setattr(args, self.dest, int(value))
        except ValueError:
            val = float(value)
            if  val > 1.0 or val < 0.0:
                raise ValueError('greed should be integer or 0 > greed > 1.0')
            setattr(args, self.dest, val)


class CrawlerMixin(object):
    def crawl(self, urls, datasource, default):
        for item in self.app.articles('/crawl', urls=urls,
                                                datasource=datasource,
                                                default=default):
            yield item


class StartText(CrawlerMixin, Command):
    "Start crawl textual data (breadability)"
    datasource_name = 'readable'
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(StartText, self).get_parser(prog_name)

        parser.add_argument('urls', metavar='URL', nargs='+', help='Start from urls')
        
        parser.add_argument('--no-follow',
                            default=True,
                            action='store_false',
                            dest='follow',
                            help='Not follow links. Only texts for supplied urls will be restored')
        self.app.articles.datasources[self.datasource_name].populate_parser(parser)
        return parser

    def take_action(self, args):
        root_handler = logging.getLogger('')
        handlers = root_handler.handlers
        root_handler.handlers = []

        if args.follow:
            ds_class = self.app.articles.datasources[self.datasource_name]
        else:
            ds_class = self.app.articles.datasources[self.datasource_name+'-content-only']

        datasource = ds_class(None, dataset=None, **args.__dict__)

        for item in self.crawl(args.urls, datasource, datasource):
            print item.encode('utf-8')
            print '>>'

        root_handler.handlers = handlers


class StartDatasource(CrawlerMixin, Command):
    """Start crawl data with defined datasource type"""
    def get_parser(self, prog_name):
        parser = super(StartDatasource, self).get_parser(prog_name)

        parser.add_argument('urls', metavar='URL', nargs='+', help='Start from urls')

        subparsers = parser.add_subparsers(title='Valid datasource types')
        for name, datasource in self.app.articles.datasources.items():
            info = list(datasource.info())
            help = 'Extracts ' + ' and '.join(info)
            if len(info) == 1:
                help += ' only'
            subparser = subparsers.add_parser(name, help=help)
            datasource.populate_parser(subparser)
            subparser.set_defaults(datasource_class=datasource)
        return parser        
    
    def take_action(self, args):
        root_handler = logging.getLogger('')
        handlers = root_handler.handlers
        root_handler.handlers = []

        datasource = args.datasource_class(None, dataset=None, **args.__dict__)
        for item in self.crawl(args.urls, datasource, datasource):
            print item.encode('utf-8')
            print '>>'

        root_handler.handlers = handlers


class StartDataset(CrawlerMixin, Command):
    """Start crawl data with named dataset"""
    def get_parser(self, prog_name):
        parser = super(StartDataset, self).get_parser(prog_name)

        parser.add_argument('--urls', metavar='URL', nargs='+', help='Start from urls')
        parser.add_argument('dataset', help='Use named dataset')
        return parser

    def take_action(self, args):
        root_handler = logging.getLogger('')
        handlers = root_handler.handlers
        root_handler.handlers = []
        dataset = get_dataset(self.app.articles, args.dataset)
        if args.urls:
            urls = args.urls
        else:
            urls = dataset.keys()

        for datasource, urls in map_datasources(urls, dataset, None).items():
            for item in self.crawl(urls, datasource, None):
                print item.encode('utf-8')
                print '>>'

        root_handler.handlers = handlers

class Restore(Command):
    "Restore saved process"
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Restore, self).get_parser(prog_name)

        parser.add_argument('id', help='Session id')
        return parser

    def take_action(self, parsed_args):
        root_handler = logging.getLogger('')
        handlers = root_handler.handlers
        root_handler.handlers = []

        for article in self.app.articles.restore(parsed_args.id):
            print article.encode('utf-8')
            print '>>'    
        
        root_handler.handlers = handlers


class RestoreList(Lister):
    "List saved processes"    
    log = logging.getLogger(__name__)
    HEADER = ('PID', 'Items', 'Tasks')
    def take_action(self, parsed_args):
        l = []

        pending_path = self.app.articles.instance_dir('pending')
        for pid in os.listdir(pending_path):
            sublist = [pid,]
            pidpath = os.path.join(pending_path, pid)
            items = os.path.join(pidpath, 'items')
            if os.path.exists(items):
                sublist.append(len(os.listdir(items)))
            else:
                sublist.append(0)

            tasks = os.path.join(pidpath, 'tasks')
            if os.path.exists(tasks):
                sublist.append(len(os.listdir(tasks)))
            else:
                sublist.append(0)
            l.append(sublist)


        return self.HEADER, l