#!/usr/bin/env python

import os, json

from tornado import web, options, ioloop, template
from modcommon import lv2

PORT = 9000
ROOT = os.path.dirname(os.path.realpath(__file__))
HTML_DIR = os.path.join(ROOT, 'html')
WORKSPACE = os.path.join(ROOT, 'workspace')
UNITS_FILE = os.path.join(ROOT, 'units.ttl')

class BundleList(web.RequestHandler):
    def get(self):
        bundles = []
        for bundle in os.listdir(WORKSPACE):
            if os.path.exists(os.path.join(WORKSPACE, bundle, 'manifest.ttl')):
                bundles.append(bundle)
        self.set_header('Content-type', 'application/json')
        self.write(json.dumps(bundles))

class EffectList(web.RequestHandler):
    def get(self, bundle):
        path = os.path.join(WORKSPACE, bundle)
        if not os.path.exists(os.path.join(path, 'manifest.ttl')):
            raise web.HTTPError(404)
        package = lv2.Bundle(path, units_file=UNITS_FILE)
        self.set_header('Content-type', 'application/json')
        self.write(package.data)
        
        
class Index(web.RequestHandler):
    def get(self):
        path = 'index.html'
        loader = template.Loader(HTML_DIR)
        context = {}
        self.write(loader.load(path).generate(**context))

def run():
    application = web.Application([
            (r"/bundles", BundleList),
            (r"/effects/(.+)", EffectList),
            (r"/", Index),
            (r"/(.*)", web.StaticFileHandler, {"path": HTML_DIR}),
            ],
                                  debug=True)
    
    application.listen(PORT)
    options.parse_command_line()
    ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    run()
