# -*- coding: utf-8 -*-

import os, pyinotify
from tornado import ioloop
from modsdk.settings import LV2_DIR

class EventHandler(pyinotify.ProcessEvent):

    def __init__(self, monitor):
        super(EventHandler, self).__init__()
        self.monitor = monitor

    def process_IN_CREATE(self, event):
        self.monitor.notify(event.pathname, event.maskname)
        if os.path.isdir(event.pathname):
            self.monitor.add_watch(event.pathname)

    def process_IN_DELETE(self, event):
        self.monitor.notify(event.pathname, event.maskname)

    def process_IN_CLOSE_WRITE(self, event):
        self.monitor.notify(event.pathname, event.maskname)

class BundleMonitor:

    def __init__(self, callback):
        self.callback = callback
        self.watches = []

        self.mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE  | pyinotify.IN_CLOSE_WRITE
        self.wm = pyinotify.WatchManager()
        self.notifier = pyinotify.Notifier(self.wm, EventHandler(self), timeout=0)

    def monitor(self, bundle):
        self.clear()
        path = os.path.join(LV2_DIR, bundle)
        self.add_watch(path)
        self.schedule()

    def add_watch(self, path):
        watch = self.wm.add_watch(path, self.mask, rec=True)
        self.watches.append(watch)
        
    def notify(self, pathname, maskname = None):
        self.callback()

    def schedule(self):
        ioloop.IOLoop.instance().add_callback(self.check)

    def check(self):
        self.notifier.process_events()
        if self.notifier.check_events():
            self.notifier.read_events()
        if len(self.watches) > 0:
            self.schedule()

    def clear(self):
        while len(self.watches) > 0:
            watch = self.watches.pop()
            for path, handler in watch.items():
                if os.path.exists(path):
                    self.wm.rm_watch(handler)
                
