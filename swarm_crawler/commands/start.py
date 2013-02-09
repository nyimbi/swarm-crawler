import logging
import sys
import os
from importlib import import_module
from pprint import pprint
from argparse import Action
from cliff.command import Command
from cliff.lister import Lister

from werkzeug.utils import import_string

from swarm_crawler.app import map_datasources, non_fnmatchers
from swarm_crawler.dataset import get_dataset
from swarm_crawler.output import StdoutOutputHandler

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

class store_output_handler(Action):
    def __call__(self, parser, args, value, option_string=None):
        module_path, obj_path = value.split(':')
        obj = getattr(import_module(module_path), obj_path)
        if not callable(obj):
            obj = obj(parser.cmdapp)
        setattr(args, self.dest, obj)

class OutputHandlerCommand(Command):
    def get_parser(self, prog_name):
        parser = super(OutputHandlerCommand, self).get_parser(prog_name)
        parser.cmdapp = self
        parser.add_argument('-o', '--output',
                             metavar='OUTPUT',
                             dest='handle',
                             required=False,
                             default=StdoutOutputHandler(self),
                             action = store_output_handler, 
                             help = 'function or callable object class path')
        return parser


class StartDataset(CrawlerMixin, OutputHandlerCommand):
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
                args.handle(item)

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