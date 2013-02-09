from swarm_crawler.dataset import get_dataset
from argparse import ArgumentParser
from .base import Command, ShowOne, Lister


class NamedDatasourceParser(object):
    def get_parser(self, prog_name):
        parser = self.__class__.__bases__[-1].\
                 get_parser.__get__(self, self.__class__)(prog_name)
        parser.add_argument('dataset', help='Dataset name')
        parser.add_argument('datasource', help='Datasource start url')
        return parser


class CreateDatasource(NamedDatasourceParser, Command):
    """Create datasource"""
    OMIT_DATASOURCE_ARGS = ['datasource', 'dataset', 'datasource_class']
    def get_parser(self, prog_name):
        parser = super(CreateDatasource, self).get_parser(prog_name)
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
        dataset = get_dataset(self.app.crawler, args.dataset)
        datasource = unicode(args.datasource)
        if datasource in dataset:
            raise ValueError('Datasource "%s" exists in "%s" dataset')

        kwargs = dict((key, getattr(args, key))\
                       for key in args.__dict__.keys()\
                       if not key in self.OMIT_DATASOURCE_ARGS)

        dataset[datasource] = args.datasource_class(dataset._path, **kwargs)
        dataset.save()

        self.app.log.info('Created "%s" datasource in "%s" dataset')


class DeleteDatasource(NamedDatasourceParser, Command):
    """Delete datasource"""
    def take_action(self, args):
        dataset = get_dataset(self.app.crawler, args.dataset)
        datasource = unicode(args.datasource)
        del dataset[datasource]
        dataset.save()