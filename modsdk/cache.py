import os

try:
    import pyinotify

    class WorkspaceCache(dict):
        """
        This dict is used to store the bundle data indexed by bundle name.
        It uses pyinotify to monitor workspace directory and remove bundle cache
        when any modification to that bundle is done in filesystem.
        """
        def __init__(self, basedir):
            self.basedir = os.path.realpath(basedir)
            self.monitoring = False
            self.monitor()

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
            else:
                for key in self.keys():
                    self.pop(key)
                self.monitor()

        def notify(self, path):
            path = path[len(self.basedir)+1:]
            bundle = path.split('/')[0]
            if self.get(bundle) is not None:
                print "%s modified, clearing %s cache" % (path, bundle)
                self.pop(bundle)

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

    class WorkspaceCache(dict):
        def __init__(self, basedir):
            super(WorkspaceCache, self).__init__()
        def cycle(self):
            for key in self.keys():
                self.pop(key)
