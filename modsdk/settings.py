#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys

PORT = 9000
ROOT = os.path.join(sys.prefix, 'share')
HTML_DIR = os.path.join(ROOT, 'html')
WORKSPACE = os.path.join(os.environ['HOME'], 'mod-workspace')
WIZARD_DB = os.path.join(HTML_DIR, 'resources/wizard.json')
UNITS_FILE = '/usr/lib/lv2/units.lv2/units.ttl'
CONFIG_FILE = os.path.join(WORKSPACE, 'config.json')
TEMPLATE_DIR = os.path.join(HTML_DIR, 'resources/templates')
DEFAULT_ICON_TEMPLATE = os.path.join(ROOT, 'html/resources/templates/pedal-default.html')
DEFAULT_SETTINGS_TEMPLATE = os.path.join(ROOT, 'html/resources/settings.html')
SCREENSHOT_SCRIPT = os.path.join(ROOT, 'screenshot.js')
MAX_THUMB_WIDTH = 256
MAX_THUMB_HEIGHT = 64
PHANTOM_BINARY = '/usr/bin/phantomjs'
