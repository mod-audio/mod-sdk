#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import random
import re
import shutil
import subprocess
import pyinotify

from base64 import b64encode
from PIL import Image
from time import time
from tornado import web, options, ioloop, template, httpclient, websocket
from tornado.escape import squeeze, url_escape
from tornado.util import unicode_type
from .bundlemonitor import BundleMonitor
from modsdk.settings import (PORT, HTML_DIR, WIZARD_DB, DEVICE_MODE, IMAGE_VERSION,
                             CONFIG_FILE, CONFIG_DIR, TEMPLATE_DIR, LV2_DIR,
                             DEFAULT_DEVICE, DEFAULT_ICON_IMAGE,
                             DEFAULT_ICON_TEMPLATE, DEFAULT_SETTINGS_TEMPLATE,
                             MAX_THUMB_WIDTH, MAX_THUMB_HEIGHT,
                             SCREENSHOT_SCRIPT, PHANTOM_BINARY)

# pylilv is a PITA to install, don't require it
try:
    import lilv
    haveLilv = True
except:
    haveLilv = False

if haveLilv:
    print("Using pylilv for plugin info (with checks)")
    from modsdk.utils import (init as lv2_init2,
                              cleanup as lv2_cleanup2,
                              get_bundle_plugins as get_bundle_plugins2,
                              get_all_bundles)
    from modsdk.lilvlib import get_plugin_info as get_plugin_info2

    global _W

    def lv2_init():
        global _W
        _W = lilv.World()
        _W.load_all()
        lv2_init2()

    def lv2_cleanup():
        global _W
        _W = None
        lv2_cleanup2()

    def get_plugin_info(uri):
        global _W
        ps = _W.get_all_plugins()
        pn = _W.new_uri(uri)
        pl = ps.get_by_uri(pn)
        return get_plugin_info2(_W, pl, True)

    def get_bundle_plugins(bundle):
        return [get_plugin_info(p['uri']) for p in get_bundle_plugins2(bundle)]

# otherwise use raw lilv code, skipping checks
else:
    print("Using raw lilv for plugin info (without checks)")

    from modsdk.utils import (init as lv2_init,
                              cleanup as lv2_cleanup,
                              get_all_bundles,
                              get_bundle_plugins,
                              get_plugin_info)

def symbolify(name):
    if len(name) == 0:
        return "_"
    name = re.sub("[^_a-zA-Z0-9]+", "_", name)
    if name[0].isdigit():
        name = "_" + name
    return name

def get_config(key, default=None):
    if not os.path.exists(CONFIG_FILE):
        return default

    with open(CONFIG_FILE, 'r') as fh:
        config = json.load(fh)

    if key in config.keys():
        value = config[key]
        if value:
            return value

    return default

#def set_config(key, value):
    #if os.path.exists(CONFIG_FILE):
        #with open(CONFIG_FILE, 'r') as fh:
            #config = json.load(fh)
    #else:
        #config = {}

    #config[key] = value

    #with open(CONFIG_FILE, 'w') as fh:
        #json.dump(config, fh)

class TimelessRequestHandler(web.RequestHandler):
    def compute_etag(self):
        return None

    def set_default_headers(self):
        self._headers.pop("Date")

    def should_return_304(self):
        return False

class TimelessStaticFileHandler(web.StaticFileHandler):
    def get_cache_time(self, path, modified, mime_type):
        return 0

    def get_modified_time(self):
        return None

    def set_default_headers(self):
        self._headers.pop("Date")

    def set_extra_headers(self, path):
        self.set_header("Cache-Control", "public, max-age=31536000")

    def should_return_304(self):
        return self.check_etag_header()

class JsonRequestHandler(TimelessRequestHandler):
    def write(self, data):
        # TODO: if something is sending strings out, we need to stop it
        # it's likely something using write(json.dumps(...))
        # we want to prevent that as it causes issues under Mac OS

        if isinstance(data, (bytes, unicode_type, dict)):
            TimelessRequestHandler.write(self, data)
            self.finish()
            return

        self.set_header("Content-Type", "application/json; charset=UTF-8")

        if data is True:
            data = "true"

        elif data is False:
            data = "false"

        else:
            if not isinstance(data, list):
                print("FIXME: Got new data type for JsonRequestHandler.write():", type(data), "msg:", data)
            data = json.dumps(data)

        TimelessRequestHandler.write(self, data)
        self.finish()

class BundleList(JsonRequestHandler):
    def get(self):
        self.write(get_all_bundles())

class EffectList(JsonRequestHandler):
    def get(self):
        bundle = self.get_argument('bundle')
        data   = get_bundle_plugins(bundle)

        self.write({
            'ok': len(data) > 0,
            'data': data
        })

class EffectGet(JsonRequestHandler):
    def get(self):
        uri = self.get_argument('uri')

        # workaround to support fragment in URLs
        # https://github.com/ariya/phantomjs/issues/12667
        # https://github.com/moddevices/mod-sdk/issues/1
        uri = uri.replace('%23', '#')

        try:
            data = get_plugin_info(uri)
        except:
            print("get failed")
            raise web.HTTPError(404)

        self.write({
            'ok'  : True,
            'data': data
        })

class EffectResource(TimelessStaticFileHandler):

    def initialize(self):
        # Overrides StaticFileHandler initialize
        pass

    def get(self, path):
        path = path.replace("{{{cns}}}","").replace("{{{ns}}}","")

        try:
            uri = self.get_argument('uri')
        except:
            if path.endswith(".css"):
                self.absolute_path = os.path.join(HTML_DIR, 'resources', path)
                with open(self.absolute_path, 'r') as fd:
                    self.set_header('Content-type', 'text/css')
                    self.write(fd.read().replace("{{{cns}}}","_sdk").replace("{{{ns}}}",""))
                    return

            return self.shared_resource(path)

        try:
            root = get_plugin_info(uri)['gui']['resourcesDirectory']
        except:
            raise web.HTTPError(404)

        try:
            super(EffectResource, self).initialize(root)
            return super(EffectResource, self).get(path)
        except web.HTTPError as e:
            if e.status_code != 404:
                raise e
            self.shared_resource(path)
        except IOError:
            raise web.HTTPError(404)

    def shared_resource(self, path):
        super(EffectResource, self).initialize(os.path.join(HTML_DIR, 'resources'))
        return super(EffectResource, self).get(path)

class EffectImage(TimelessStaticFileHandler):
    def initialize(self):
        uri = self.get_argument('uri')

        try:
            data = get_plugin_info(uri)
        except:
            raise web.HTTPError(404)

        try:
            self.modgui = data['gui']
        except:
            raise web.HTTPError(404)

        try:
            root = self.modgui['resourcesDirectory']
        except:
            raise web.HTTPError(404)

        return TimelessStaticFileHandler.initialize(self, root)

    def parse_url_path(self, image):
        try:
            path = self.modgui[image]
        except:
            path = None

        if path is None or not os.path.exists(path):
            try:
                path = DEFAULT_ICON_IMAGE[image]
            except:
                raise web.HTTPError(404)
            else:
                TimelessStaticFileHandler.initialize(self, os.path.dirname(path))

        return path

class EffectFile(TimelessStaticFileHandler):
    def initialize(self):
        # return custom type directly. The browser will do the parsing
        self.custom_type = None

        uri = self.get_argument('uri')

        try:
            self.modgui = get_plugin_info(uri)['gui']
        except:
            raise web.HTTPError(404)

        try:
            root = self.modgui['resourcesDirectory']
        except:
            raise web.HTTPError(404)

        return TimelessStaticFileHandler.initialize(self, root)

    def parse_url_path(self, prop):
        try:
            path = self.modgui[prop]
        except:
            raise web.HTTPError(404)

        if prop in ("iconTemplate", "settingsTemplate", "stylesheet", "javascript"):
            self.custom_type = "text/plain; charset=UTF-8"

        return path

    def get_content_type(self):
        if self.custom_type is not None:
            return self.custom_type
        return TimelessStaticFileHandler.get_content_type(self)

class EffectSave(JsonRequestHandler):
    def post(self):
        if not LV2_DIR:
            self.write(False)
            return

        uri = self.get_argument('uri')
        ttlText = self.get_argument('ttlText')
        filesToCopy = [os.path.join(HTML_DIR, "resources", fil) for fil in json.loads(self.get_argument('filesToCopy'))]
        iconTemplateData = self.get_argument('iconTemplateData')
        iconTemplateFile = self.get_argument('iconTemplateFile')
        stylesheetFile   = self.get_argument('stylesheetFile')

        for fil in filesToCopy:
            if not os.path.exists(fil):
                print("missing file:", fil)
                raise web.HTTPError(404)

        try:
            data = get_plugin_info(uri)
        except:
            print("ERROR in webserver.py: get_plugin_info for '%s' failed" % uri)
            self.write(False)
            return

        bundledir, resrcsdir, appendMode = self.get_bundle_location(data)

        bundledir = os.path.abspath(bundledir)
        resrcsdir = os.path.abspath(resrcsdir)
        lv2dir    = os.path.abspath(os.path.join(bundledir, os.path.pardir))

        if not os.path.exists(lv2dir):
             os.mkdir(lv2dir)
        if not os.path.exists(bundledir):
             os.mkdir(bundledir)
        if not os.path.exists(resrcsdir):
             os.mkdir(resrcsdir)

        if data['gui']['usingSeeAlso'] or appendMode:
            ttlFile = "modgui.ttl"
        else:
            ttlFile = "manifest.ttl"

        if appendMode:
            with open(os.path.join(bundledir, "manifest.ttl"), 'a') as fd:
                fd.write("<%s> rdfs:seeAlso <modgui.ttl> .\n" % (data['uri'],))

        with open(os.path.join(bundledir, ttlFile), 'w') as fd:
            fd.write(ttlText)

        with open(os.path.join(resrcsdir, iconTemplateFile), 'w') as fd:
            fd.write(iconTemplateData)

        with open(os.path.join(resrcsdir, stylesheetFile), 'w') as fd:
            stylesheetData = ""

            for fil in filesToCopy:
                if not fil.endswith(".css"):
                    continue
                with open(fil, 'r') as fild:
                    stylesheetData += fild.read()

            fd.write(stylesheetData)

        for fil in filesToCopy:
            if fil.endswith(".css"):
                continue

            localfile = fil.replace(HTML_DIR,"",1).replace("resources/","",1)
            if localfile[0] == "/":
                localfile = localfile[1:]
            localfile = os.path.join(resrcsdir, localfile)

            localdir  = os.path.dirname(localfile)
            localdir2 = os.path.dirname(localdir)

            if not os.path.exists(localdir2):
                os.mkdir(localdir2)
            if not os.path.exists(localdir):
                os.mkdir(localdir)

            with open(fil, 'rb') as fild:
                with open(localfile, 'wb') as locald:
                    locald.write(fild.read())

        lv2_cleanup()
        lv2_init()

        self.write(True)

    def get_bundle_location(self, data):
        # check for resourcesDirectory property (no modgui available if invalid)
        if not data['gui']['resourcesDirectory']:
            bundledir = data['bundles'][0]

            # check if we can use plugin bundle dir as output for modgui
            if os.path.isdir(bundledir) and os.access(bundledir, os.W_OK):
                resrcsdir = os.path.join(bundledir, "modgui")
                return (bundledir, resrcsdir, True)

        # check for modificableInPlace property (custom bundle.modgui folder)
        if data['gui']['modificableInPlace']:
            resrcsdir = data['gui']['resourcesDirectory']

            # make sure it's safe to use
            if os.path.isdir(resrcsdir) and os.access(resrcsdir, os.W_OK):
                bundledir = os.path.join(resrcsdir, os.path.pardir)
                return (bundledir, resrcsdir, False)

        # if we get here, we need to create a new modgui folder
        bundlname  = symbolify(data['name'])
        bundledir  = "%s/%s.modgui" % (LV2_DIR, bundlname)
        appendMode = False

        # never use modgui.ttl for new modguis
        data['gui']['usingSeeAlso'] = False

        # if bundle already exists, generate a new random bundle name
        if os.path.exists(bundledir):
            while True:
                bundledir = "%s/%s-%i.modgui" % (LV2_DIR, bundlname, random.randint(1,99999))
                if os.path.exists(bundledir):
                    continue
                break

        resrcsdir = os.path.join(bundledir, "modgui")
        return (bundledir, resrcsdir, False)

class Index(TimelessRequestHandler):
    def get(self, path):
        if not path:
            path = 'index.html'
        section = path.split('.',1)[0]

        if section == 'index':
            # Caching strategy.
            # 1. If we don't have a version parameter, redirect
            curVersion = self.get_version()
            try:
                version = url_escape(self.get_argument('v'))
            except web.MissingArgumentError:
                uri  = self.request.uri
                uri += '&' if self.request.query else '?'
                uri += 'v=%s' % curVersion
                self.redirect(uri)
                return
            # 2. Make sure version is correct
            if IMAGE_VERSION is not None and version != curVersion:
                uri = self.request.uri.replace('v=%s' % version, 'v=%s' % curVersion)
                self.redirect(uri)
                return

            lv2_cleanup()
            lv2_init()

        else:
            version = self.get_version()

        loader = template.Loader(HTML_DIR)

        with open(DEFAULT_ICON_TEMPLATE, 'r') as fd:
            default_icon_template = squeeze(fd.read().replace("'", "\\'"))

        with open(DEFAULT_SETTINGS_TEMPLATE, 'r') as fd:
            default_settings_template = squeeze(fd.read().replace("'", "\\'"))

        with open(WIZARD_DB, 'r') as fh:
            wizard_db = json.load(fh)

        context = {
            'default_device': DEFAULT_DEVICE,
            'default_icon_template': default_icon_template,
            'default_settings_template': default_settings_template,
            'version': version,
            'wizard_db': json.dumps(wizard_db),
            'device_mode': 'true' if DEVICE_MODE else 'false',
            'write_access': 'true' if LV2_DIR else 'false',
        }

        self.write(loader.load(path).generate(**context))

    def get_version(self):
        if IMAGE_VERSION is not None and len(IMAGE_VERSION) > 1:
            # strip initial 'v' from version if present
            version = IMAGE_VERSION[1:] if IMAGE_VERSION[0] == "v" else IMAGE_VERSION
            return url_escape(version)
        return str(int(time()))

class Screenshot(JsonRequestHandler):
    @web.asynchronous
    def get(self):
        self.uri    = self.get_argument('uri')
        self.width  = self.get_argument('width')
        self.height = self.get_argument('height')

        try:
            self.data = get_plugin_info(self.uri)
        except:
            self.data = None
            raise web.HTTPError(404)

        self.make_screenshot()

    def tmp_filename(self):
        tmp_filename = ''.join([ random.choice('0123456789abcdef') for i in range(6) ])
        return '/tmp/%s.png' % tmp_filename

    def make_screenshot(self):
        fname = self.tmp_filename()
        proc = subprocess.Popen([ PHANTOM_BINARY,
                                  SCREENSHOT_SCRIPT,
                                  'http://localhost:%d/icon.html#%s' % (PORT, self.uri),
                                  fname,
                                  self.width,
                                  self.height,
                                ],
                                stdout=subprocess.PIPE)

        def proc_callback(fileno, event):
            if proc.poll() is None:
                return
            loop.remove_handler(fileno)
            fh = open(fname, 'rb')
            os.remove(fname)
            self.handle_image(fh)

        loop = ioloop.IOLoop.instance()
        loop.add_handler(proc.stdout.fileno(), proc_callback, 16)

    def handle_image(self, fh):
        screenshot_path = self.data['gui']['screenshot']
        thumbnail_path  = self.data['gui']['thumbnail']

        if not os.path.exists(os.path.dirname(screenshot_path)):
            raise web.HTTPError(404)

        if not os.path.exists(os.path.dirname(thumbnail_path)):
            raise web.HTTPError(404)

        img = Image.open(fh)
        img = self.crop(img)
        img.convert('RGB')
        img.save(screenshot_path)
        width, height = img.size
        if width > MAX_THUMB_WIDTH:
            width = MAX_THUMB_WIDTH
            height = height * MAX_THUMB_WIDTH / width
        if height > MAX_THUMB_HEIGHT:
            height = MAX_THUMB_HEIGHT
            width = width * MAX_THUMB_HEIGHT / height
        img.thumbnail((width, height), Image.ANTIALIAS)
        img.save(thumbnail_path)

        screenshot_data = b""
        thumbnail_data  = b""

        with open(screenshot_path, 'rb') as fd:
            screenshot_data = fd.read()

        with open(thumbnail_path, 'rb') as fd:
            thumbnail_data = fd.read()

        result = {
            'ok': True,
            'screenshot': b64encode(screenshot_data).decode("utf-8", errors="ignore"),
            'thumbnail': b64encode(thumbnail_data).decode("utf-8", errors="ignore"),
        }

        self.write(result)

    def crop(self, img):
        # first find latest non-transparent pixel in both width and height
        min_x = int(self.width)
        min_y = int(self.height)
        max_x = 0
        max_y = 0
        cropd = False
        for i, px in enumerate(img.getdata()):
            if px[3] > 0:
                width = i % img.size[0]
                height = int(i / img.size[0])
                min_x = min(min_x, width)
                min_y = min(min_y, height)
                max_x = max(max_x, width)
                max_y = max(max_y, height)
                cropd = True
        if not cropd:
            return img
        # now crop
        return img.crop((min_x, min_y, max_x, max_y))

class BundlePost(web.RequestHandler):
    @web.asynchronous
    def get(self, bundle):
        while bundle.endswith(os.sep):
            bundle = bundle[:-1]

        address = get_config("device", DEFAULT_DEVICE)
        if not address.startswith(("http://", "https://")):
            address = "http://%s" % address
        if address.endswith("/"):
            address = address[:-1]
        address = "%s/sdk/install" % address

        bundlename = os.path.basename(bundle)
        tmpfile    = "/tmp/%s.tgz" % bundlename
        cwd        = os.path.abspath(os.path.join(bundle, os.path.pardir))

        proc = subprocess.Popen(['tar', 'chzf', tmpfile, '-C', cwd, '--hard-dereference', bundlename],
                                 cwd=cwd, stdout=subprocess.PIPE)

        def proc_callback(fileno, event):
            if proc.poll() is None:
                return
            loop.remove_handler(fileno)

            if not os.path.exists(tmpfile):
                print("ERROR in webserver.py: tar failed to create compressed bundle file")
                return

            with open(tmpfile, 'rb') as fh:
                data = b64encode(fh.read()).decode("utf-8", errors="ignore")

            os.remove(tmpfile)

            return self.send_bundle(bundlename, data, address)

        loop = ioloop.IOLoop.instance()
        loop.add_handler(proc.stdout.fileno(), proc_callback, 16)

    def send_bundle(self, bundlename, data, address, fields={}):
        content_type, body = self.encode_multipart_formdata(bundlename, data, fields)
        headers = {
            'Content-Type': content_type,
            'Content-Length': str(len(body)),
        }
        client = httpclient.AsyncHTTPClient()
        client.fetch(address, self.handle_response, method='POST',
                     headers=headers, body=body, request_timeout=300)

    def handle_response(self, response):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        if response.code == 200:
            self.write(response.body)
        else:
            self.write(json.dumps({
                'ok': False,
                'error': response.body,
            }))
        self.finish()

    def encode_multipart_formdata(self, bundlename, data, fields={}):
        boundary = '----------%s' % ''.join([ random.choice('0123456789abcdef') for i in range(22) ])
        body = []

        for (key, value) in fields.items():
            body.append('--%s' % boundary)
            body.append('Content-Disposition: form-data; name="%s"' % key)
            body.append('')
            body.append('%s' % value)

        body.append('--%s' % boundary)
        body.append('Content-Disposition: form-data; name="package"; filename="%s.tgz"' % bundlename)
        body.append('Content-Type: application/octet-stream')
        body.append('')
        body.append(data)

        body.append('--%s--' % boundary)
        body.append('')

        content_type = 'multipart/form-data; boundary=%s' % boundary
        body         = '\r\n'.join(body)

        return content_type, body

class ConfigurationGet(JsonRequestHandler):
    def get(self):
        config = {
            "device": DEFAULT_DEVICE,
        }

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as fh:
                config.update(json.load(fh))

        if not config["device"]:
            config["device"] = DEFAULT_DEVICE

        self.write(config)

class ConfigurationSet(JsonRequestHandler):
    def post(self):
        config  = json.loads(self.request.body.decode("utf-8", errors="ignore"))
        confdir = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(confdir):
            os.mkdir(confdir)
        with open(CONFIG_FILE, 'w') as fh:
            json.dump(config, fh)
        self.write(True)

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

class BundleMonitorWebsocket(websocket.WebSocketHandler):
    def open(self):
        self.monitor = BundleMonitor(self.notify)

    def on_message(self, bundle):
        self.monitor.monitor(bundle)

    def on_close(self):
        self.monitor.clear()

    def notify(self):
        self.write_message("reload")

def make_application(port=PORT, output_log=False):
    application = web.Application([
            (r"/bundles", BundleList),
            (r"/effects", EffectList),
            (r"/effect/get/", EffectGet),
            (r"/effect/image/(screenshot|thumbnail).png", EffectImage),
            (r"/effect/file/(.*)", EffectFile),
            (r"/effect/save", EffectSave),
            (r"/config/get", ConfigurationGet),
            (r"/config/set", ConfigurationSet),
            (r"/(icon.html)?", Index),
            (r"/screenshot", Screenshot),
            (r"/post/(.+)/?", BundlePost),
            (r"/js/templates.js$", BulkTemplateLoader),
            (r"/resources/(.*)", EffectResource),
            (r"/monitor", BundleMonitorWebsocket),
            (r"/(.*)", web.StaticFileHandler, {"path": HTML_DIR}),
            ], debug=output_log)

    application.listen(port)
    if output_log:
        options.parse_command_line()

    return ioloop.IOLoop.instance()

def check_environment():
    issues = []
    if not os.path.isfile(PHANTOM_BINARY):
        issues.append("PhantomJS not found. Please install it and make sure the binary is located at %s" % PHANTOM_BINARY)

    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    if len(issues) == 0:
        return True
    print("\nPlease configure your environment properly. The following issues were found:\n")
    for issue in issues:
        print("  - %s" % issue)
    print("")
    return True

def welcome_message():
    print("")
    print("Welcome to the MOD-SDK")
    print("The goal of this SDK is to implement the MODGUI specification for LV2, so you must be familiar with LV2 first.")
    print("Please check http://lv2plug.in/ if you need help on that.")
    print("")
    print("To start testing your plugin interfaces, open your webkit-based browser (Google Chrome, Chromium, Safari)"
          " and point to http://localhost:%d" % PORT)

def run():
    if not check_environment():
        return

    lv2_init()
    welcome_message()
    make_application().start()
    lv2_cleanup()

if __name__ == "__main__":
    run()
