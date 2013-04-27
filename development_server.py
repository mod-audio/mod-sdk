#!/usr/bin/env python

import os, json, random, subprocess
import Image

from tornado import web, options, ioloop, template
from modcommon import lv2

PORT = 9000
ROOT = os.path.dirname(os.path.realpath(__file__))
HTML_DIR = os.path.join(ROOT, 'html')
WORKSPACE = os.path.join(ROOT, 'workspace')
UNITS_FILE = os.path.join(ROOT, 'units.ttl')
PHANTOM_BINARY = os.path.join(ROOT, 'phantomjs-1.9.0-linux-x86_64/bin/phantomjs')
SCREENSHOT_SCRIPT = os.path.join(ROOT, 'screenshot.js')
MAX_THUMB_WIDTH = 64
MAX_THUMB_HEIGHT = 64

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

def tmp_filename():
    tmp_filename = ''.join([ random.choice('0123456789abcdef') for i in range(6) ])
    return '/tmp/%s.png' % tmp_filename
    
def make_screenshot(bundle, effect, width, height, callback):
    fname = tmp_filename()
    proc = subprocess.Popen([ PHANTOM_BINARY, 
                              SCREENSHOT_SCRIPT,
                              'http://localhost:%d/icon.html#%s,%s' % (PORT, bundle, effect),
                              fname,
                              width,
                              height,
                              ],
                            stdout=subprocess.PIPE)
    
    def proc_callback(fileno, event):
        if proc.poll() is None:
            return
        loop.remove_handler(fileno)
        fh = open(fname)
        os.remove(fname)
        callback(fh)
        
    loop = ioloop.IOLoop.instance()
    loop.add_handler(proc.stdout.fileno(), proc_callback, 16)
        
class IconScreenshot(web.RequestHandler):
    @web.asynchronous
    def get(self):
        def send_image(fh):
            self.set_header('Content-type', 'image/png')
            self.write(fh.read())
            self.finish()

        make_screenshot(self.get_argument('bundle'),
                        self.get_argument('effect'),
                        self.get_argument('width'),
                        self.get_argument('height'),
                        send_image)

class ThumbScreenshot(web.RequestHandler):
    @web.asynchronous
    def get(self):
        def handle_image(fh):
            img = Image.open(fh)
            width, height = img.size
            if width > MAX_THUMB_WIDTH:
                width = MAX_THUMB_WIDTH
                height = height * MAX_THUMB_WIDTH / width
            if height > MAX_THUMB_HEIGHT:
                height = MAX_THUMB_HEIGHT
                width = width * MAX_THUMB_HEIGHT / height
            img.thumbnail((width, height))
            fname = tmp_filename()
            img.save(fname)
            fh = open(fname)
            self.set_header('Content-type', 'image/png')
            self.write(fh.read())
            self.finish()
            os.remove(fname)

        make_screenshot(self.get_argument('bundle'),
                        self.get_argument('effect'),
                        self.get_argument('width'),
                        self.get_argument('height'),
                        handle_image)


def run():
    application = web.Application([
            (r"/bundles", BundleList),
            (r"/effects/(.+)", EffectList),
            (r"/", Index),
            (r"/icon_screenshot", IconScreenshot),
            (r"/thumb_screenshot", ThumbScreenshot),
            (r"/(.*)", web.StaticFileHandler, {"path": HTML_DIR}),
            ],
                                  debug=True)
    
    application.listen(PORT)
    options.parse_command_line()
    ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    run()
