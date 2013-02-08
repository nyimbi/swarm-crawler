from os import listdir as ls, path, unlink

from werkzeug.utils import cached_property

from swarm_crawler.dataset import get_dataset

from .base import Command, ShowOne, Lister

class NamedDatasetParser(object):
    def get_parser(self, prog_name):
        parser = self.__class__.__bases__[-1].\
                 get_parser.__get__(self, self.__class__)(prog_name)
        parser.add_argument('dataset', help='Dataset name')
        return parser

class DeleteDataset(NamedDatasetParser, Command):
    """Delete dataset"""
    def take_action(self, args):
        tree_path = path.join(self.app.crawler.instance_dir('dataset'),
                              args.dataset)
        unlink(tree_path)
        self.app.log.info('"%s" datset deleted')

class DatasetList(Lister):
    """List available datasets"""
    HEADER = ('Name', )
    def take_action(self, args):
        return self.HEADER, ((i,) for i in ls(self.app.crawler.instance_dir('dataset')))

class DatasetInfo(NamedDatasetParser, ShowOne):
    """Show dataset info"""
    def take_action(self, args):
        dataset = get_dataset(self.app.crawler, args.dataset)
        headers = ('Tree',)
        content = (''.join(dataset.pformat(indent='  ')),)
        return headers, content

class DatasetBackup(NamedDatasetParser, Command):
    """Back dataset up as a shell script"""
    def take_action(self, args):
        pass