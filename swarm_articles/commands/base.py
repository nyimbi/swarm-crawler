from cliff.command import Command


class SwarmCommand(Command):
    def get_parser(self, prog_name):
        parser = super(SwarmCommand, self).get_parser(prog_name)
        parser.add_argument('instance', nargs=1, default='.swarm')
        return parser