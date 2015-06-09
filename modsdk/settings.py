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
    UNITS_FILE = os.path.join(os.path.join(CWD, 'units.ttl'))
elif os.path.exists(os.path.join(CWD, '..', 'html')):
    ROOT = os.path.join(os.path.join(CWD, '..'))
    UNITS_FILE = os.path.join(os.path.join(CWD, '..', 'units.ttl'))
else:
    ROOT = os.path.join(sys.prefix, 'share', 'modsdk')
    UNITS_FILE = '/usr/lib/lv2/units.lv2/units.ttl'

PORT = 9000
HTML_DIR = os.path.join(ROOT, 'html')
WIZARD_DB = os.path.join(HTML_DIR, 'resources/wizard.json')
TEMPLATE_DIR = os.path.join(HTML_DIR, 'resources/templates')
DEFAULT_ICON_TEMPLATE = os.path.join(ROOT, 'html/resources/templates/pedal-default.html')
DEFAULT_SETTINGS_TEMPLATE = os.path.join(ROOT, 'html/resources/settings.html')
SCREENSHOT_SCRIPT = os.path.join(ROOT, 'screenshot.js')
MAX_THUMB_WIDTH = 256
MAX_THUMB_HEIGHT = 64
PHANTOM_BINARY = '/usr/bin/phantomjs'

# TODO remove later
WORKSPACE = os.path.join(os.environ['HOME'], 'mod-workspace')
CONFIG_FILE = os.path.join(WORKSPACE, 'config.json')
