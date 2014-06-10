import os
from datetime import timedelta
from tornado import ioloop
from modsdk.settings import UNITS_FILE
from modcommon import lv2

class WorkspaceCache(dict):
    """
    This dict is used to store the bundle data indexed by bundle name.
    It uses pyinotify to monitor workspace directory and remove bundle cache
    when any modification to that bundle is done in filesystem.
    """

    def __init__(self, basedir, enabled=True):
        self.enabled = enabled

        try:
            import pyinotify
        except ImportError:
            self.enabled = False
            return

        self.basedir = os.path.realpath(basedir)
        self.monitoring = False
        self.cycle()

    def monitor(self):
        if not os.path.isdir(self.basedir) or self.monitoring:
            return

        self.monitoring = True

        self.wm = pyinotify.WatchManager()
        self.mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE  | pyinotify.IN_CLOSE_WRITE

        self.notifier = pyinotify.Notifier(self.wm, EventHandler(self), timeout=1)

        self.register_dir(self.basedir)

        super(WorkspaceCache, self).__init__()

    def register_dir(self, path):
        self.wm.add_watch(path, self.mask, rec=True)
        try:
            for filename in os.listdir(path):
                filename = os.path.join(path, filename)
                self.notify(filename)
                if os.path.isdir(filename):
                    self.register_dir(filename)
        except OSError:
            # Directory might have been removed
            pass

    def cycle(self):
        if self.monitoring:
            self.notifier.process_events()
            if self.notifier.check_events():
                self.notifier.read_events()
            ioloop.IOLoop.instance().add_callback(self.cycle)
        else:
            for key in self.keys():
                self.pop(key)
            self.monitor()
            # add_timeout instead of add_callback avoids eating a lot of cpu
            # in an infinite loop
            ioloop.IOLoop.instance().add_timeout(timedelta(milliseconds=1), self.cycle)


    def notify(self, path):
        path = path[len(self.basedir)+1:]
        bundle = path.split('/')[0]
        if self.get(bundle) is not None:
            print "%s modified, clearing %s cache" % (path, bundle)
            self.pop(bundle)

try:
    import pyinotify
    class EventHandler(pyinotify.ProcessEvent):

        def __init__(self, monitor):
            super(EventHandler, self).__init__()
            self.monitor = monitor

        def process_IN_CREATE(self, event):
            self.monitor.notify(event.pathname)
            if os.path.isdir(event.pathname):
                self.monitor.register_dir(event.pathname)

        def process_IN_DELETE(self, event):
            self.monitor.notify(event.pathname)

        def process_IN_CLOSE_WRITE(self, event):
            self.monitor.notify(event.pathname)
except ImportError:
    pass

BUNDLE_CACHE = None

#singleton
def get_cache_instance(workspace):
    global BUNDLE_CACHE
    if BUNDLE_CACHE:
        return BUNDLE_CACHE
    BUNDLE_CACHE = WorkspaceCache(workspace)
    return BUNDLE_CACHE

def disable_cache(workspace):
    get_cache_instance(workspace).enabled = False
    
def get_bundle_data(workspace, bundle):
    if BUNDLE_CACHE.enabled and BUNDLE_CACHE.get(bundle):
        return BUNDLE_CACHE[bundle]
    path = os.path.join(workspace, bundle)
    open(os.path.join(path, 'manifest.ttl'))
    package = lv2.Bundle(path, units_file=UNITS_FILE, allow_inconsistency=True)
    if BUNDLE_CACHE.enabled:
        BUNDLE_CACHE[bundle] = package.data
    return package.data


