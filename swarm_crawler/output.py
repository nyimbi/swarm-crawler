class OutputHandler(object):
    '''
    Output handler is a class of handler object or function
    '''
    def __init__(self, cmdapp):
        self.cmdapp = cmdapp
    
    def __call__(self, item):
        return item

class StdoutOutputHandler(OutputHandler):
    def __call__(self, item):
        print item        