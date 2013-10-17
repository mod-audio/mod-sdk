import os

PORT = 9000
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
HTML_DIR = os.path.join(ROOT, 'html')
WORKSPACE = os.path.join(ROOT, 'workspace')
WIZARD_DB = os.path.join(HTML_DIR, 'resources/wizard.json')
UNITS_FILE = os.path.join(ROOT, 'units.ttl')
CONFIG_FILE = os.path.join(ROOT, 'config.json')
TEMPLATE_DIR = os.path.join(HTML_DIR, 'resources/templates')
DEFAULT_ICON_TEMPLATE = os.path.join(ROOT, 'html/resources/templates/pedal-default.html')
DEFAULT_SETTINGS_TEMPLATE = os.path.join(ROOT, 'html/resources/settings.html')
SCREENSHOT_SCRIPT = os.path.join(ROOT, 'screenshot.js')
MAX_THUMB_WIDTH = 256
MAX_THUMB_HEIGHT = 64
PHANTOM_BINARY = os.path.join(ROOT, 'phantomjs-1.9.0-macosx/bin/phantomjs')

if not os.path.exists(PHANTOM_BINARY):
    PHANTOM_BINARY = os.path.join(ROOT, 'phantomjs-1.9.0-linux-x86_64/bin/phantomjs')

