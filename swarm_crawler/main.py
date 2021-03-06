import logging
import sys
import os
import string
from argparse import Action


from datrie import Trie

from cliff.app import App
from cliff.commandmanager import CommandManager

from werkzeug.utils import import_string

DEFAULT_INSTANCE_PATH = './.swarm'

OPT_MODULES = {
    'cookies':'swarm.ext.http.signal.cookies',
    'cache':'swarm.ext.http.signal.cache',
}

class Unicode_Casting_Trie(Trie):
    def __setitem__(self, name, value):
        super(Unicode_Casting_Trie, self).__setitem__(unicode(name), value)

class CommandManager(CommandManager):
    def __init__(self, namespace):
        self.commands = Unicode_Casting_Trie(string.printable)
        self.namespace = namespace
        self._load_commands()

    def find_command(self, argv):
        cmd = u' '.join(argv)
        try:
            name = self.commands.prefixes(cmd)[-1]
        except IndexError:
            raise ValueError('Invalid command %r' % cmd)
        ep = self.commands[name]
        factory = ep.load()
        tail = [c for c in cmd[len(name):].split(u' ') if c]
        return (factory, name, tail)

class store_int(Action):
    def __call__(self, parser, args, value, option_string=None):
        setattr(args, self.dest, int(value))

class CrawlerApp(App):
    log = logging.getLogger(__name__)
    def configure_logging(self):
        pass

    def __init__(self):
        super(CrawlerApp, self).__init__(
            description='swarm crawler',
            version='0.0.1',
            command_manager=CommandManager('swarm_crawler.commands'),
            )

        self._clean_files = []

    def initialize_app(self, argv):
        from .app import crawler
        #get file config is configured

        if self.options.config and os.path.exists(self.options.config):
            crawler.config.root_path = '.'
            crawler.config.from_pyfile(self.options.config)

        if self.options.workers:
            crawler.competitors = crawler.config['COMPETITORS'] = self.options.workers

        #setup logging
        from breadability.logconfig import LOG

        crawler.config['DEBUG'] = crawler.debug = self.options.debug

        #configure signalsets fron args
        if crawler.reloaded_module is None:
            crawler.reloaded_module = ['swarm.ext.http.signal.unique_url',]
            # crawler.reloaded_module = []

        for name, mod in OPT_MODULES.items():
            if getattr(self.options, name):
                crawler.reloaded_module.append(import_string(mod))

        #setup instance papth
        crawler.instance_path = self.options.instance_path

        self.crawler = crawler

    def clean_up(self, cmd, result, err):
        self.clean_files()

    def clean_files(self):
        for path in self._clean_files:
            if os.path.exists(path) and os.path.isfile(path):
                os.unlink(path)


    def build_option_parser(self, *args, **kwargs):
        parser = super(CrawlerApp, self).build_option_parser(*args, **kwargs)
        parser.add_argument(
            '--instance',
            dest='instance_path',
            metavar='INSTANCE',
            action='store',
            default=DEFAULT_INSTANCE_PATH,
            help='Specify an instance folder (default: "%s")'%DEFAULT_INSTANCE_PATH,
            )

        parser.add_argument(
            '--workers',
            dest='workers',
            metavar='INTEGER',
            action=store_int,
            default=None,
            help='Set number of workers',
            )


        parser.add_argument(
            '--config',
            default='swarm_config.py',
            action='store',
            help='Specify config file',
            )

        for name in OPT_MODULES:
            parser.add_argument(
                '--%s'%name,
                default=False,
                action='store_true',
                help='Enable %s'%name,
                )


        return parser

def main(argv=sys.argv[1:]):
    crawler = CrawlerApp()
    return crawler.run(argv)