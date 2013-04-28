#!/usr/bin/env python

import os, json, random, subprocess, re
import Image

from tornado import web, options, ioloop, template, httpclient
from modcommon import lv2

PORT = 9000
ROOT = os.path.dirname(os.path.realpath(__file__))
HTML_DIR = os.path.join(ROOT, 'html')
WORKSPACE = os.path.join(ROOT, 'workspace')
UNITS_FILE = os.path.join(ROOT, 'units.ttl')
CONFIG_FILE = os.path.join(ROOT, 'config.json')
PHANTOM_BINARY = os.path.join(ROOT, 'phantomjs-1.9.0-linux-x86_64/bin/phantomjs')
SCREENSHOT_SCRIPT = os.path.join(ROOT, 'screenshot.js')
MAX_THUMB_WIDTH = 64
MAX_THUMB_HEIGHT = 64

def get_config(key, default=None):
    try:
        config = json.loads(open(CONFIG_FILE).read())
        return config[key]
    except:
        return default

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

def save_icon_image(bundle, effect, prefix, data):
    path = os.path.join(WORKSPACE, bundle)
    package = lv2.Bundle(path, units_file=UNITS_FILE)
    effect = package.data['plugins'][effect]
    slug = effect['name'].lower()
    slug = re.sub('\s+', '-', slug)
    slug = re.sub('[^a-z0-9-]', '', slug)
    slug = '%s-%s.png' % (prefix, slug)
    img_name = os.path.join(effect['icon']['basedir'], slug)
    open(img_name, 'w').write(data)

class IconScreenshot(web.RequestHandler):
    @web.asynchronous
    def get(self):
        bundle = self.get_argument('bundle')
        effect = self.get_argument('effect')

        def send_image(fh):
            self.set_header('Content-type', 'image/png')
            data = fh.read()
            save_icon_image(bundle, effect, 'icon', data)
            self.write(data)
            self.finish()

        make_screenshot(bundle, effect, 
                        self.get_argument('width'),
                        self.get_argument('height'),
                        send_image)

class ThumbScreenshot(web.RequestHandler):
    @web.asynchronous
    def get(self):
        bundle = self.get_argument('bundle')
        effect = self.get_argument('effect')

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
            data = fh.read()
            save_icon_image(bundle, effect, 'thumb', data)
            self.write(data)
            self.finish()
            os.remove(fname)

        make_screenshot(bundle, effect,
                        self.get_argument('width'),
                        self.get_argument('height'),
                        handle_image)

class BundleInstall(web.RequestHandler):
    @web.asynchronous
    def get(self, bundle):
        path = os.path.join(WORKSPACE, bundle)
        package = lv2.BundlePackage(path, units_file=UNITS_FILE)
        content_type, body = self.encode_multipart_formdata(package)

        headers = {
            'Content-Type': content_type,
            'Content-Length': str(len(body)),
            }

        client = httpclient.AsyncHTTPClient()
        addr = get_config('device', 'http://localhost:8888')
        if not addr.startswith('http://') and not addr.startswith('https://'):
            addr = 'http://%s' % addr
        if addr.endswith('/'):
            addr = addr[:-1]
        client.fetch('%s/sdk/install' % addr,
                     self.handle_response,
                     method='POST', headers=headers, body=body)

    def handle_response(self, response):
        self.set_header('Content-type', 'application/json')
        if (response.code == 200):
            self.write(json.dumps({ 'ok': json.loads(response.body) }))
        else:
            self.write(json.dumps({ 'ok': False,
                                    'error': response.body,
                                    }))
        self.finish()
        
    def encode_multipart_formdata(self, package):
        boundary = '----------%s' % ''.join([ random.choice('0123456789abcdef') for i in range(22) ])
        body = []

        body.append('--%s' % boundary)
        body.append('Content-Disposition: form-data; name="package"; filename="%s.tgz"' % package.uid)
        body.append('Content-Type: application/octet-stream')
        body.append('')
        body.append(package.read())
        
        body.append('--%s--' % boundary)
        body.append('')

        content_type = 'multipart/form-data; boundary=%s' % boundary

        return content_type, '\r\n'.join(body)

class ConfigurationGet(web.RequestHandler):
    def get(self):
        try:
            config = json.loads(open(CONFIG_FILE).read())
        except:
            config = {}
        self.set_header('Content-type', 'application/json')
        self.write(json.dumps(config))

class ConfigurationSet(web.RequestHandler):
    def post(self):
        config = json.loads(self.request.body)
        open(CONFIG_FILE, 'w').write(json.dumps(config))
        self.set_header('Content-type', 'application/json')
        self.write(json.dumps(True))

def run():
    application = web.Application([
            (r"/bundles", BundleList),
            (r"/effects/(.+)", EffectList),
            (r"/config/get", ConfigurationGet),
            (r"/config/set", ConfigurationSet),
            (r"/", Index),
            (r"/icon_screenshot", IconScreenshot),
            (r"/thumb_screenshot", ThumbScreenshot),
            (r"/install/(.+)/?", BundleInstall),
            (r"/(.*)", web.StaticFileHandler, {"path": HTML_DIR}),
            ],
                                  debug=True)
    
    application.listen(PORT)
    options.parse_command_line()
    ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    run()
