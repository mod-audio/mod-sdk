#!/usr/bin/env python

import os, glob, subprocess, random, argparse
from PIL import Image
from modsdk.webserver import make_application
from modsdk.cache import get_bundle_data
from modsdk.settings import (ROOT, PHANTOM_BINARY, SCREENSHOT_SCRIPT,
                             MAX_THUMB_WIDTH, MAX_THUMB_HEIGHT)

#maximum width and height
WIDTH = 1920
HEIGHT = 1080

# port used for the temporary webserver
PORT = 9123

class BundleQueue(object):
    def __init__(self, workspace, bundles):
        self.workspace = workspace
        self.bundle_queue = bundles
        self.webserver = make_application(port=PORT, workspace=workspace, output_log=False)
        self.webserver.add_callback(self.next_bundle)

    def run(self):
        self.webserver.start()

    def next_bundle(self):
        if len(self.bundle_queue) == 0:
            self.webserver.stop()
            return
        self.current_bundle = self.bundle_queue.pop(0)
        self.data = get_bundle_data(self.workspace, self.current_bundle)
        self.effect_queue = self.data['plugins'].keys()
        self.next_effect()

    def next_effect(self):
        if len(self.effect_queue) == 0:
            return self.next_bundle()
        self.current_effect = self.effect_queue.pop(0)
        try:
            self.data['plugins'][self.current_effect]['gui']['screenshot']
        except (TypeError, KeyError):
            return self.next_effect()

        fname = '/tmp/%s.png' % ''.join([ random.choice('0123456789abcdef') for i in range(6) ])
        proc = subprocess.Popen([ PHANTOM_BINARY, 
                                  SCREENSHOT_SCRIPT,
                                  'http://localhost:%d/icon.html#%s,%s' % (PORT, 
                                                                           self.current_bundle, 
                                                                           self.current_effect),
                                  fname,
                                  str(WIDTH),
                                  str(HEIGHT),
                                  ],
                                stdout=subprocess.PIPE)

        def proc_callback(fileno, event):
            if proc.poll() is None:
                return
            self.webserver.remove_handler(fileno)
            fh = open(fname)
            os.remove(fname)
            self.handle_image(fh)

        self.webserver.add_handler(proc.stdout.fileno(), proc_callback, 16)

    def handle_image(self, fh):
        img = Image.open(fh)
        img = self.crop(img)
        img.save(self.data['plugins'][self.current_effect]['gui']['screenshot'])
        width, height = img.size
        if width > MAX_THUMB_WIDTH:
            width = MAX_THUMB_WIDTH
            height = height * MAX_THUMB_WIDTH / width
        if height > MAX_THUMB_HEIGHT:
            height = MAX_THUMB_HEIGHT
            width = width * MAX_THUMB_HEIGHT / height
        img.convert('RGB')
        img.thumbnail((width, height), Image.ANTIALIAS)
        img.save(self.data['plugins'][self.current_effect]['gui']['thumbnail'])
        self.next_effect()

    def crop(self, img):
        # first find latest non-transparent pixel in both width and height
        min_x = WIDTH
        min_y = HEIGHT
        max_x = 0
        max_y = 0
        for i, px in enumerate(img.getdata()):
            if px[3] > 0:
                width = i % img.size[0]
                height = i / img.size[0]
                min_x = min(min_x, width)
                min_y = min(min_y, height)
                max_x = max(max_x, width)
                max_y = max(max_y, height)
        # now crop
        return img.crop((min_x, min_y, max_x, max_y))

def run():
    parser = argparse.ArgumentParser(description='Generates screenshot of all effects inside a bundle')
    parser.add_argument('bundles', help="The bundle path (a directory containing manifest.ttl file", type=str, nargs='+')

    args = parser.parse_args()
    workspace = None
    bundles = []
    for bundle in args.bundles:
        if bundle.endswith('/'):
            bundle = bundle[:-1]
        basedir = os.path.realpath(os.path.dirname(bundle))
        if not workspace:
            workspace = basedir
        assert workspace == basedir, "All bundles must be contained in same directory"
        bundles.append(bundle.split('/')[-1])

    BundleQueue(workspace, bundles).run()

if __name__ == '__main__':
    run()
