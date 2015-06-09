#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import pycurl
from cStringIO import StringIO
from mod import  settings
from glob import glob

try:
    filename = sys.argv[1]
except IndexError:
    print "usage: " + __file__.split('/')[-1] + ' path [url]'
    sys.exit(1)

try:
    url = sys.argv[2]
except IndexError:
    if settings.DEV_ENVIRONMENT:
        url = 'localhost:8888'
    else:
        url = 'mod'

c = pycurl.Curl()
c.setopt(c.POST, 1)
c.setopt(c.HTTPPOST, [('update_package', (c.FORM_FILE, str(filename)))])
c.setopt(c.VERBOSE, 1)
c.setopt(c.WRITEFUNCTION, StringIO().write)
c.setopt(c.HEADERFUNCTION, StringIO().write)
c.setopt(c.URL, "http://%s/sdk/sysupdate" % url )
c.perform()

