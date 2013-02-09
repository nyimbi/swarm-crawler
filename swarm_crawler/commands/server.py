from cliff.command import Command

from ..serve import web

class Web(Command):
    def take_action(self, args):
        web.commands = self.app
        web.run()