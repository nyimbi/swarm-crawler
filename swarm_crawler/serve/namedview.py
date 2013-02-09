from functools import wraps
from flask import request, abort
from flask.views import MethodView

class NamedMethod(object):
    def __init__(self, name, http_method_name):
        self.name = name
        self.http_method_name = http_method_name

    def __call__(self, method):
        self.method = method
        if self.http_method_name is None:
            self.http_method_name = method.__name__
        self.http_method_name = self.http_method_name.lower()
        return self

def namedmethod(name, http_method_name=None):
    return NamedMethod(name, http_method_name)

class NamedMethodViewBase(MethodView.__metaclass__):
    def __new__(meta, name, bases, members):
        members['_namedmethods'] = {}
        namedmethods = ((name, namedmethod)\
                        for (name, namedmethod) \
                        in members.items() \
                        if isinstance(namedmethod, NamedMethod))
        for name, namedmethod in namedmethods:
            
            if not namedmethod.name in members['_namedmethods']:
                members['_namedmethods'][namedmethod.name] = {}

            members['_namedmethods']\
                   [namedmethod.name]\
                   [namedmethod.http_method_name] = namedmethod.method
            if not 'methods' in members:
                members['methods'] = []

            if not namedmethod.http_method_name in members['methods']:
                members['methods'].append(namedmethod.http_method_name)
        members = dict(((n,v) for (n,v) in members.items() \
                         if not isinstance(v, NamedMethod)))

        methods = [v.__name__.lower() for (n, v)\
                    in members.items() \
                    if callable(v) and v.__name__.lower() in \
                    ('get', 'post', 'put', 'patch', 'head', 'options', 'track', 'update')]
        if methods:
            if not 'methods' in members:
                members['methods'] = []
            members['methods'].extend(methods)
        return super(NamedMethodViewBase, meta)\
                .__new__(meta, name, bases, members)

class NamedMethodView(MethodView):
    __metaclass__ = NamedMethodViewBase
    __headername__ = 'X-View-Name'

    def dispatch_method(self, method, *args, **kwargs):
        if method is None and request.method == 'HEAD':
            method = getattr(self, 'get', None)
        return method(*args, **kwargs)    

    def get_named_method(self, name):
        meth = self._namedmethods.get(name, {}).get(request.method.lower(), None)
        if meth is not None:
            return meth.__get__(self, self.__class__)

    def dispatch_request(self, *args, **kwargs):
        if self.__headername__ in request.headers:
            method = self.get_named_method(request.headers[self.__headername__])
            if method is not None:
                return self.dispatch_method(method, *args, **kwargs)
        if not hasattr(self, request.method.lower()):
            abort(405)
        return super(NamedMethodView, self).dispatch_request(*args, **kwargs)

if __name__ == '__main__':
    import unittest
    from flask import Flask
    from pprint import pprint

    class TestedNamedView(NamedMethodView):
        @namedmethod('editor')
        def get(self):
            return 'editor get'

        @namedmethod('editor', 'post')
        def editor_post(self):
            return 'editor post'

        def post(self):
            return 'raw post'

    test = Flask(__name__)
    test.config['TESTING'] = True
    test.config['DEBUG'] = True
    test.config['SERVER_NAME'] = 'localhost:5000'

    test.add_url_rule('/test', view_func=TestedNamedView.as_view('test'))

    class TestNamedMethodView(unittest.TestCase):
        def setUp(self):
            self.client = test.test_client()

        def test_405(self):
            self.assertTrue(self.client.get('/test').status_code == 405)

        def test_named_get(self):
            self.assertTrue(''.join(self.client.get('/test',
                headers=[('X-View-Name', 'editor')]).response) == 'editor get')

        def test_raw_post(self):
            self.assertTrue(''.join(self.client.post('/test').response) == 'raw post')

        def test_named_post(self):
            self.assertTrue(''.join(self.client.post('/test',
                headers=[('X-View-Name', 'editor')]).response) == 'editor post')

    unittest.main()
    # test.run()