#!/usr/bin/env python

import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(ROOT)

import pycurl
from cStringIO import StringIO
from modcommon import lv2

try:
    dirname = sys.argv[1]
except IndexError:
    print "usage: " + __file__.split('/')[-1] + ' path [url]'
    sys.exit(1)

try:
    url = sys.argv[2]
except IndexError:
    url = 'mod'

if url.startswith('http://'):
    url = url[len('http://'):]

package = lv2.BundlePackage(dirname,
                            units_file='/usr/lib/lv2/units.lv2/units.ttl')
filename = '/tmp/%s.tgz' % package.uid
open(filename, 'w').write(package.read())

c = pycurl.Curl()
c.setopt(c.POST, 1)
c.setopt(c.HTTPPOST, [('package', (c.FORM_FILE, str(filename)))])
c.setopt(c.VERBOSE, 1)
c.setopt(c.WRITEFUNCTION, StringIO().write)
c.setopt(c.HEADERFUNCTION, StringIO().write)
c.setopt(c.URL, "http://%s/sdk/install" % url )
c.perform()

