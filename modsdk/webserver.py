#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, lilv, json, random, subprocess, re, base64, shutil, time, pystache
from hashlib import sha1
from PIL import Image

from tornado import web, options, ioloop, template, httpclient
from modcommon import lv2
from modsdk.crypto import Sender
from modsdk.lilvlib import get_plugin_info
from modsdk.settings import (PORT, HTML_DIR, WIZARD_DB,
                             CONFIG_FILE, TEMPLATE_DIR, DEFAULT_ICON_TEMPLATE,
                             DEFAULT_SETTINGS_TEMPLATE, SCREENSHOT_SCRIPT, MAX_THUMB_WIDTH,
                             MAX_THUMB_HEIGHT, PHANTOM_BINARY)

global cached_plugins, cached_bundle_plugins
cached_plugins        = {}
cached_bundle_plugins = {}

def get_config(key, default=None):
    try:
        config = json.loads(open(CONFIG_FILE).read())
        return config[key]
    except:
        return default

class BundleList(web.RequestHandler):
    def get(self):
        bundles = []

        world = lilv.World()
        world.load_all()

        global cached_plugins, cached_bundle_plugins
        cached_plugins        = {}
        cached_bundle_plugins = {}

        for p in world.get_all_plugins():
            info   = get_plugin_info(world, p)
            bnodes = lilv.lilv_plugin_get_data_uris(p.me)

            it = lilv.lilv_nodes_begin(bnodes)
            while not lilv.lilv_nodes_is_end(bnodes, it):
                bundle = lilv.lilv_nodes_get(bnodes, it)
                it     = lilv.lilv_nodes_next(bnodes, it)

                if bundle is None:
                    continue
                if not lilv.lilv_node_is_uri(bundle):
                    continue

                bundle = os.path.dirname(lilv.lilv_uri_to_path(lilv.lilv_node_as_uri(bundle)))

                if not bundle.endswith(os.sep):
                    bundle += os.sep

                if bundle not in bundles:
                    bundles.append(bundle)
                    cached_bundle_plugins[bundle] = []

                for info2 in cached_bundle_plugins[bundle]:
                    if info2['uri'] == info['uri']:
                        break
                else:
                    cached_bundle_plugins[bundle].append(info)

            cached_plugins[info['uri']] = info

        del world

        self.set_header('Content-type', 'application/json')
        self.write(json.dumps(bundles))

class EffectList(web.RequestHandler):
    def get(self):
        bundle = self.get_argument('bundle')

        try:
            global cached_bundle_plugins
            data = cached_bundle_plugins[bundle]
        except:
            raise web.HTTPError(404)

        self.set_header('Content-type', 'application/json')
        self.write(json.dumps({ 'ok': True, 'data': data }))

class EffectImage(web.RequestHandler):
    def get(self, image):
        uri = self.get_argument('uri')

        try:
            global cached_plugins
            data = cached_plugins[uri]
        except:
            raise web.HTTPError(404)

        try:
            path = data['gui'][image]
        except:
            raise web.HTTPError(404)

        if not os.path.exists(path):
            raise web.HTTPError(404)

        self.set_header('Content-type', 'image/png')
        self.write(open(path, 'rb').read())

class EffectStylesheet(web.RequestHandler):
    def get(self):
        uri = self.get_argument('uri')

        try:
            global cached_plugins
            data = cached_plugins[uri]
        except:
            raise web.HTTPError(404)

        try:
            path = data['gui']['stylesheet']
        except:
            raise web.HTTPError(404)

        if not os.path.exists(path):
            raise web.HTTPError(404)

        content = open(path, 'rb').read()
        context = { 'ns': '?uri=%s' % data['uri'] }

        self.set_header('Content-type', 'text/css')
        self.write(pystache.render(content, context))

class EffectJavascript(web.RequestHandler):
    def get(self):
        uri = self.get_argument('uri')

        try:
            global cached_plugins
            data = cached_plugins[uri]
        except:
            raise web.HTTPError(404)

        try:
            path = data['gui']['javascript']
        except:
            raise web.HTTPError(404)

        if not os.path.exists(path):
            raise web.HTTPError(404)

        self.set_header('Content-type', 'text/javascript')
        self.write(open(path, 'rb').read())

class EffectSave(web.RequestHandler):
    def post(self):
        param = json.loads(self.request.body.decode("utf-8", errors="ignore"))

        bundle = os.path.basename(param['name']).replace(" ","_").replace("/","_")
        self.basedir = os.path.expanduser("~/.lv2/%s.modgui" % bundle)
        if not os.path.exists(self.basedir):
            os.mkdir(self.basedir)

        with open(os.path.join(self.basedir, "manifest.ttl"), 'w') as fd:
            fd.write(param['ttlText'])

        self.basedir = os.path.join(self.basedir, "modgui")
        if not os.path.exists(self.basedir):
            os.mkdir(self.basedir)

        ttl_data = param['ttlData']

        self.make_template(ttl_data['iconTemplate'], param['iconTemplate'])
        self.make_datafile(ttl_data['templateData'], param['data'])
        self.make_empty_image(ttl_data['screenshot'])
        self.make_empty_image(ttl_data['thumbnail'])

        self.set_header('Content-type', 'application/json')
        self.write(json.dumps(True))

    def make_template(self, name, template):
        dest = os.path.join(self.basedir, name)
        open(dest, 'w').write(template)

    def make_datafile(self, name, data):
        datafile = os.path.join(self.basedir, name)
        open(datafile, 'w').write(json.dumps(data, sort_keys=True, indent=4))

    def make_empty_image(self, name):
        image_path = os.path.join(self.basedir, name)

        if not os.path.exists(image_path):
            img = Image.new('RGBA', (1, 1), (255, 0, 0, 0))
            img.save(image_path)

class Index(web.RequestHandler):
    def get(self, path):
        if not path:
            path = 'index.html'
        loader = template.Loader(HTML_DIR)
        default_icon_template = open(DEFAULT_ICON_TEMPLATE).read()
        default_settings_template = open(DEFAULT_SETTINGS_TEMPLATE).read()
        context = {
            'default_icon_template': default_icon_template.replace("'", "\\'").replace("\n", "\\n"),
            'default_settings_template': default_settings_template.replace("'", "\\'").replace("\n", "\\n"),
            'wizard_db': json.dumps(json.loads(open(WIZARD_DB).read())),
            'default_developer': os.environ['USER'],
            'default_privkey': os.path.join(os.environ['HOME'], '.ssh', 'id_rsa'),
            }
        self.write(loader.load(path).generate(**context))

class Screenshot(web.RequestHandler):
    @web.asynchronous
    def get(self):
        self.bundle = self.get_argument('bundle')
        self.effect = self.get_argument('effect')
        self.width = self.get_argument('width')
        self.height = self.get_argument('height')

        self.make_screenshot()

    def tmp_filename(self):
        tmp_filename = ''.join([ random.choice('0123456789abcdef') for i in range(6) ])
        return '/tmp/%s.png' % tmp_filename

    def make_screenshot(self):
        fname = self.tmp_filename()
        proc = subprocess.Popen([ PHANTOM_BINARY,
                                  SCREENSHOT_SCRIPT,
                                  'http://localhost:%d/icon.html#%s,%s' % (PORT, self.bundle, self.effect),
                                  fname,
                                  self.width,
                                  self.height,
                                  ],
                                stdout=subprocess.PIPE)

        def proc_callback(fileno, event):
            if proc.poll() is None:
                return
            loop.remove_handler(fileno)
            fh = open(fname)
            os.remove(fname)
            self.handle_image(fh)

        loop = ioloop.IOLoop.instance()
        loop.add_handler(proc.stdout.fileno(), proc_callback, 16)

    def handle_image(self, fh):
        screenshot_data = fh.read()
        fh.seek(0)
        thumb_data = self.thumbnail(fh).read()

        self.save_icon(screenshot_data, thumb_data)

        result = {
            'ok': True,
            'screenshot': base64.b64encode(screenshot_data),
            'thumbnail': base64.b64encode(thumb_data),
            }

        self.set_header('Content-type', 'application/json')
        self.write(json.dumps(result))
        self.finish()

    def thumbnail(self, fh):
        img = Image.open(fh)
        width, height = img.size
        if width > MAX_THUMB_WIDTH:
            width = MAX_THUMB_WIDTH
            height = height * MAX_THUMB_WIDTH / width
        if height > MAX_THUMB_HEIGHT:
            height = MAX_THUMB_HEIGHT
            width = width * MAX_THUMB_HEIGHT / height
        img.convert('RGB')
        img.thumbnail((width, height), Image.ANTIALIAS)
        fname = self.tmp_filename()
        img.save(fname)
        fh = open(fname)
        os.remove(fname)
        return fh

    def save_icon(self, screenshot_data, thumb_data):
        #try:
            #data = get_bundle_data(WORKSPACE, self.bundle)
        #except IOError:
            raise web.HTTPError(404)

        #effect = data['plugins'][self.effect]

        #try:
            #basedir = effect['gui']['resourcesDirectory']
        #except:
            #basedir = os.path.join(WORKSPACE, self.bundle, 'modgui')
        #if not os.path.exists(basedir):
            #os.mkdir(basedir)

        #screenshot_path = effect['gui']['screenshot']
        #thumb_path = effect['gui']['thumbnail']

        #open(screenshot_path, 'w').write(screenshot_data)
        #open(thumb_path, 'w').write(thumb_data)

class BundlePost(web.RequestHandler):
    @web.asynchronous
    def get(self, destination, bundle):
        return
        #path = os.path.join(WORKSPACE, bundle)
        #package = lv2.BundlePackage(path, units_file=UNITS_FILE)

        #if destination == 'device':
            #address = self.get_address('device', 'sdk/install', 'http://localhost:8888')
            #return self.send_bundle(package, address)

        #if destination == 'cloud':
            #address = self.get_address('cloud', 'api/sdk/publish', 'http://cloud.portalmod.com')
            #fields = self.sign_bundle_package(bundle, package)
            #return self.send_bundle(package, address, fields)

    def get_address(self, key, uri, default):
        addr = get_config(key, default)
        if not addr.startswith('http://') and not addr.startswith('https://'):
            addr = 'http://%s' % addr
        if addr.endswith('/'):
            addr = addr[:-1]
        if uri.startswith('/'):
            uri = uri[1:]
        return '%s/%s' % (addr, uri)

    def sign_bundle_package(self, bundle, package):
        private_key = get_config('private_key',
                                 os.path.join(os.environ['HOME'], '.ssh', 'id_rsa'))
        developer_id = get_config('developer_id', os.environ['USER'])

        command = json.dumps({
                'developer': developer_id,
                'plugin': bundle,
                'checksum': sha1(package.read()).hexdigest(),
                'tstamp': time.time(),
                })
        package.seek(0)
        checksum = sha1(command).hexdigest()
        signature = Sender(private_key, checksum).pack()
        return {
            'command': command,
            'signature': signature,
            }

    def send_bundle(self, package, address, fields={}):
        content_type, body = self.encode_multipart_formdata(package, fields)
        headers = {
            'Content-Type': content_type,
            'Content-Length': str(len(body)),
            }

        client = httpclient.AsyncHTTPClient()
        client.fetch(address, self.handle_response, method='POST',
                     headers=headers, body=body, request_timeout=300)

    def handle_response(self, response):
        self.set_header('Content-type', 'application/json')
        if (response.code == 200):
            self.write(response.body)
        else:
            self.write(json.dumps({ 'ok': False,
                                    'error': response.body,
                                    }))
        self.finish()

    def encode_multipart_formdata(self, package, fields={}):
        boundary = '----------%s' % ''.join([ random.choice('0123456789abcdef') for i in range(22) ])
        body = []

        for (key, value) in fields.items():
            body.append('--%s' % boundary)
            body.append('Content-Disposition: form-data; name="%s"' % key)
            body.append('')
            body.append(value)

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
        confdir = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(confdir):
            os.mkdir(confdir)
        config = json.loads(self.request.body)
        open(CONFIG_FILE, 'w').write(json.dumps(config))
        self.set_header('Content-type', 'application/json')
        self.write(json.dumps(True))

class BulkTemplateLoader(web.RequestHandler):
    def get(self):
        self.set_header('Content-type', 'text/javascript')
        basedir = TEMPLATE_DIR
        for template in os.listdir(basedir):
            if not re.match('^[a-z0-9_-]+\.html$', template):
                continue
            contents = open(os.path.join(basedir, template)).read()
            template = template[:-5]
            self.write("TEMPLATES['%s'] = '%s';\n\n"
                       % (template,
                          contents.replace("'", "\\'").replace("\n", "\\n")
                          )
                       )

class EffectResource(web.StaticFileHandler):

    def initialize(self):
        # Overrides StaticFileHandler initialize
        pass

    def get(self, path):
        try:
            uri = self.get_argument('uri')
        except:
            return self.shared_resource(path)

        try:
            global cached_plugins
            data = cached_plugins[uri]
        except:
            raise web.HTTPError(404)

        try:
            root = data['gui']['resourcesDirectory']
        except:
            raise web.HTTPError(404)

        try:
            super(EffectResource, self).initialize(root)
            super(EffectResource, self).get(path)
        except web.HTTPError as e:
            if e.status_code != 404:
                raise e
            self.shared_resource(path)
        except IOError:
            raise web.HTTPError(404)

    def shared_resource(self, path):
        super(EffectResource, self).initialize(os.path.join(HTML_DIR, 'resources'))
        super(EffectResource, self).get(path)

def make_application(port=PORT, output_log=True):
    application = web.Application([
            (r"/bundles", BundleList),
            (r"/effects", EffectList),
            (r"/effect/image/(screenshot|thumbnail).png", EffectImage),
            (r"/effect/stylesheet.css", EffectStylesheet),
            (r"/effect/gui.js", EffectJavascript),
            (r"/effect/save", EffectSave),
            (r"/config/get", ConfigurationGet),
            (r"/config/set", ConfigurationSet),
            (r"/(icon.html)?", Index),
            (r"/screenshot", Screenshot),
            (r"/post/(device|cloud)/(.+)/?", BundlePost),
            (r"/js/templates.js$", BulkTemplateLoader),
            (r"/resources/(.*)", EffectResource),
            (r"/(.*)", web.StaticFileHandler, {"path": HTML_DIR}),
            ], debug=True)

    application.listen(port)
    if output_log:
        options.parse_command_line()

    return ioloop.IOLoop.instance()

def check_environment():
    issues = []
    if not os.path.isfile(PHANTOM_BINARY):
        issues.append("PhantomJS not found. Please install it and make sure the binary is located at %s" % PHANTOM_BINARY)
    if len(issues) == 0:
        return True
    print("\nPlease configure your environment properly. The following issues were found:\n")
    for issue in issues:
        print("  - %s" % issue)
    print("")
    return False

def welcome_message():
    print("")
    print("Welcome to the MOD-SDK")
    print("The goal of this SDK is to implement the MODGUI specification for LV2, so you must be familiar with LV2 first.")
    print("Please check http://lv2plug.in/ if you need help on that.")
    print("")
    print("To start testing your plugin interfaces, open your webkit-based browser (Google Chrome, Chromium, Safari)"
          " and point to http://localhost:%d" % PORT)

def run():
    if check_environment():
        welcome_message()
        make_application().start()

if __name__ == "__main__":
    run()
