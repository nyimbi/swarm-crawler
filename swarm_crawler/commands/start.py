import logging
import sys
import os
from pprint import pprint
from argparse import Action
from cliff.command import Command
from cliff.lister import Lister

from werkzeug.utils import import_string

from swarm.ext.crawler.app import map_datasources, non_fnmatchers
from swarm.ext.crawler.dataset import get_dataset

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
    def crawl(self, urls, datasource):
        for item in self.app.crawler('/crawl', urls=urls,
                                                datasource=datasource):
            yield item


class StartDatasource(CrawlerMixin, Command):
    """Start crawl data with defined datasource type"""
    def get_parser(self, prog_name):
        parser = super(StartDatasource, self).get_parser(prog_name)

        parser.add_argument('urls', metavar='URL', nargs='+', help='Start from urls')

        subparsers = parser.add_subparsers(title='Valid datasource types')
        for name, datasource in self.app.crawler.datasources.items():
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

        root_handler.handlers = handlers


class StartDataset(CrawlerMixin, Command):
    """Start crawl data with named dataset"""
    def get_parser(self, prog_name):
        parser = super(StartDataset, self).get_parser(prog_name)
        parser.add_argument('dataset', help='Use named dataset')
        return parser

    def take_action(self, args):
        root_handler = logging.getLogger('')
        handlers = root_handler.handlers
        root_handler.handlers = []
        dataset = get_dataset(self.app.crawler, args.dataset)
        urls = non_fnmatchers(dataset)
        for datasource, urls in map_datasources(urls, dataset).items():
            for item in self.crawl(urls, datasource):
                print item.encode('utf-8')

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

        for item in self.app.crawler.restore(parsed_args.id):
            print item.encode('utf-8')
        
        root_handler.handlers = handlers


class RestoreList(Lister):
    "List saved processes"    
    log = logging.getLogger(__name__)
    HEADER = ('PID', 'Items', 'Tasks')
    def take_action(self, parsed_args):
        l = []

        pending_path = self.app.crawler.instance_dir('pending')
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