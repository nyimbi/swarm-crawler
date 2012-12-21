import logging
import sys
import os
from pprint import pprint
from argparse import Action
from cliff.command import Command
from cliff.lister import Lister

from swarm.ext.articles.text import PageText
from werkzeug.utils import import_string

class int_or_float(Action):
    def __call__(self, parser, args, value, option_string=None):
        try:
            setattr(args, self.dest, int(value))
        except ValueError:
            val = float(value)
            if  val > 1.0 or val < 0.0:
                raise ValueError('greed should be integer or 0 > greed > 1.0')
            setattr(args, self.dest, val)

class import_object(Action):
    def __call__(self, parser, args, value, option_string=None):
        if isinstance(value, basestring):
            setattr(args, self.dest, import_string(value))
        else:
            setattr(args, self.dest, value)


class Crawl(Command):
    "Starts crawl process"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Crawl, self).get_parser(prog_name)

        parser.add_argument('--greed',
                            action=int_or_float,
                            default=1,
                            help='Greedness level. If GREED is int - limit by number of winner items.\r\nIf GREED is float - limit by proportion of winner items')

        parser.add_argument('--no-follow',
                            action='store_false',
                            default=True,
                            help='No follow links')

        parser.add_argument('--allow-links',
                            nargs='*',
                            help='Regexps for links to allow')

        parser.add_argument('--deny-links',
                            nargs='*',
                            help='Regexps for links to deny')

        parser.add_argument('--limit-domain',
                            nargs='*',
                            help='Limit crawled articles with domains. Dot started domains treated as domain name suffixes')

        parser.add_argument('--item-class',
                            action=import_object,
                            default=PageText,
                            help='Item class. default: swarm.ext.articles.text.PageText')

        parser.add_argument('urls', nargs='+', help='Start from urls')
        return parser

    def take_action(self, parsed_args):
        root_handler = logging.getLogger('')
        handlers = root_handler.handlers
        root_handler.handlers = []

        for article in self.app.articles('/crawl',
                                          urls=parsed_args.urls,
                                          greed=parsed_args.greed,
                                          limit_domains=parsed_args.limit_domain,
                                          follow=parsed_args.no_follow,
                                          allow_links=parsed_args.allow_links,
                                          deny_links=parsed_args.deny_links,
                                          ):
            print article.encode('utf-8')
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