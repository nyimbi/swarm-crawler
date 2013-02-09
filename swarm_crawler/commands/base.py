from werkzeug.utils import cached_property
from cliff.commandmanager import CommandManager
from cliff.command import Command
from cliff.lister import Lister
from cliff.show import ShowOne

class InstanceMixin(object):
    @cached_property
    def instance_dir(self):
        return self.app.crawler.instance_dir('dataset')

    def dataset(self, name):
        return path.join(self.instance_dir, name)

class Command(InstanceMixin, Command):
    pass

class Lister(InstanceMixin, Lister):
    pass

class ShowOne(InstanceMixin, ShowOne):
    pass