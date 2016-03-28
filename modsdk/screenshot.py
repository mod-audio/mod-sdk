#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, glob, subprocess, random, argparse
from PIL import Image
from modsdk.settings import (ROOT, PHANTOM_BINARY, SCREENSHOT_SCRIPT,
                             MAX_THUMB_WIDTH, MAX_THUMB_HEIGHT)
from modsdk.webserver import (make_application,
                              lv2_init, lv2_cleanup,
                              get_bundle_plugins,
                              get_plugin_info)

#maximum width and height
WIDTH = 1920
HEIGHT = 1080

# port used for the temporary webserver
PORT = 9123

class BundleQueue(object):
    def __init__(self, bundles):
        bundles = [os.path.abspath(b) for b in bundles]

        # make a list of plugin info related to our bundles
        self.bundles_info = dict((b, []) for b in bundles)

        # load info from all the bundles
        loaded_bundles = []

        for bundle in bundles:
            plugins = get_bundle_plugins(bundle)

            if len(plugins) == 0:
                continue
            if bundle in loaded_bundles:
                continue
            loaded_bundles.append(bundle)

            self.bundles_info[bundle] = plugins

        # save list of bundles that we want to generate screenshots for
        self.bundle_queue = loaded_bundles

        # create web server
        self.webserver = make_application(port=PORT, output_log=True)
        self.webserver.add_callback(self.next_bundle)

    def run(self):
        self.webserver.start()

    def tmp_filename(self):
        tmp_filename = ''.join([ random.choice('0123456789abcdef') for i in range(6) ])
        return '/tmp/%s.png' % tmp_filename

    def next_bundle(self):
        if len(self.bundle_queue) == 0:
            self.webserver.stop()
            return
        self.current_bundle = self.bundle_queue.pop(0)
        self.effect_queue = self.bundles_info[self.current_bundle]
        self.next_effect()

    def next_effect(self):
        if len(self.effect_queue) == 0:
            return self.next_bundle()
        self.current_effect = self.effect_queue.pop(0)
        try:
            self.current_effect['gui']['screenshot']
            self.current_effect['gui']['thumbnail']
        except (TypeError, KeyError):
            return self.next_effect()

        fname = self.tmp_filename()
        proc = subprocess.Popen([ PHANTOM_BINARY,
                                  SCREENSHOT_SCRIPT,
                                  'http://localhost:%d/icon.html#%s' % (PORT, self.current_effect['uri']),
                                  fname,
                                  str(WIDTH),
                                  str(HEIGHT),
                                ],
                                stdout=subprocess.PIPE)

        def proc_callback(fileno, event):
            if proc.poll() is None:
                return
            self.webserver.remove_handler(fileno)
            fh = open(fname, 'rb')
            os.remove(fname)
            self.handle_image(fh)

        self.webserver.add_handler(proc.stdout.fileno(), proc_callback, 16)

    def handle_image(self, fh):
        img = Image.open(fh)
        img = self.crop(img)
        img.save(self.current_effect['gui']['screenshot'])
        width, height = img.size
        if width > MAX_THUMB_WIDTH:
            width = MAX_THUMB_WIDTH
            height = height * MAX_THUMB_WIDTH / width
        if height > MAX_THUMB_HEIGHT:
            height = MAX_THUMB_HEIGHT
            width = width * MAX_THUMB_HEIGHT / height
        img.convert('RGB')
        img.thumbnail((width, height), Image.ANTIALIAS)
        img.save(self.current_effect['gui']['thumbnail'])
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
        return img.crop([int(i) for i in (min_x, min_y, max_x, max_y)])

def run():
    parser = argparse.ArgumentParser(description='Generates screenshot of all effects inside a bundle')
    parser.add_argument('bundles', help="The bundle path (a directory containing manifest.ttl file", type=str, nargs='+')

    args = parser.parse_args()
    bundles = []

    for bundle in args.bundles:
        if not bundle.endswith(os.sep):
            bundle += os.sep
        if bundle not in bundles:
            bundles.append(bundle)

    lv2_init()
    BundleQueue(bundles).run()
    lv2_cleanup()

if __name__ == '__main__':
    run()
