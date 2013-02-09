class OutputHandler(object):
    def __init__(self, cmdapp):
        self.cmdapp = cmdapp
    
    def __call__(self, item):
        return item

class StdoutOutputHandler(OutputHandler):
    def __call__(self, item):
        print item        