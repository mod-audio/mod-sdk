#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys

CWD = sys.path[0]

if not CWD:
    CWD = os.path.dirname(sys.argv[0])
if os.path.isfile(CWD):
    CWD = os.path.dirname(CWD)

if os.path.exists(os.path.join(CWD, 'html')):
    ROOT = CWD
elif os.path.exists(os.path.join(CWD, '..', 'html')):
    ROOT = os.path.join(os.path.join(CWD, '..'))
else:
    ROOT = os.path.join(sys.prefix, 'share', 'mod-sdk')

PORT = 9000
HTML_DIR = os.path.join(ROOT, 'html')
WIZARD_DB = os.path.join(HTML_DIR, 'resources/wizard.json')
TEMPLATE_DIR = os.path.join(HTML_DIR, 'resources/templates')
DEFAULT_DEVICE = "http://localhost:8888"
DEFAULT_ICON_TEMPLATE = os.path.join(HTML_DIR, 'resources/templates/pedal-default.html')
DEFAULT_SETTINGS_TEMPLATE = os.path.join(HTML_DIR, 'resources/settings.html')
DEFAULT_ICON_IMAGE = {
    'thumbnail' : os.path.join(HTML_DIR, 'resources/pedals/default-thumbnail.png'),
    'screenshot': os.path.join(HTML_DIR, 'resources/pedals/default-screenshot.png')
}
if os.path.exists('/usr/bin/phantomjs'):
    PHANTOM_BINARY = '/usr/bin/phantomjs'
else:
    PHANTOM_BINARY = '/usr/local/bin/phantomjs'
SCREENSHOT_SCRIPT = os.path.join(ROOT, 'screenshot.js')
MAX_THUMB_WIDTH = 256
MAX_THUMB_HEIGHT = 64

CONFIG_DIR = os.getenv("MOD_DATA_DIR", os.path.expanduser("~/.local/share/mod-data"))
CONFIG_FILE = os.path.join(CONFIG_DIR, "sdk-config.json")

DEVICE_MODE = bool(int(os.getenv("MOD_DEVICE_MODE", 0)))

LV2_PATH = os.getenv("LV2_PATH")

if not LV2_PATH: # might be set but empty
    LV2_DIR  = os.path.expanduser("~/.lv2")
    LV2_PATH = LV2_DIR + ":/usr/lib/lv2:/usr/local/lib/lv2"
else:
    for path in LV2_PATH.split(":"):
        if os.access(path, os.W_OK):
            LV2_DIR = path
            break
    else:
        LV2_DIR = ""

IMAGE_VERSION_PATH = os.environ.pop('MOD_IMAGE_VERSION_PATH', '/etc/mod-release/release')

if os.path.isfile(IMAGE_VERSION_PATH):
    with open(IMAGE_VERSION_PATH, 'r') as fh:
        IMAGE_VERSION = fh.read().strip() or None
else:
    IMAGE_VERSION = None
