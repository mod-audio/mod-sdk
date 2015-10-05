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
PHANTOM_BINARY = '/usr/bin/phantomjs'
SCREENSHOT_SCRIPT = os.path.join(ROOT, 'screenshot.js')
MAX_THUMB_WIDTH = 256
MAX_THUMB_HEIGHT = 64

CONFIG_FILE = os.path.expanduser("~/.local/share/mod-data/sdk-config.json")
