function BundleMonitor() {
    this.notify = new Function();
    this.connect();
}

BundleMonitor.prototype.connect = function() {
    this.loaded = false;
    this.ws = new WebSocket('ws://' + document.location.host + '/monitor');

    this.ws.onmessage = function(message) {
        this.notify();
    }.bind(this);

    this.ws.onopen = function() {
        this.loaded = true;
        if (this.bundle) {
            this.watch(bundle);
        }
    }.bind(this)

    this.ws.onclose = this.reconnect.bind(this);
    this.ws.onerror = this.reconnect.bind(this);
}

BundleMonitor.prototype.watch = function(bundle, callback) {
    this.bundle = bundle;
    this.notify = callback;
    if (this.loaded) {
        this.ws.send(bundle);
    }
}

BundleMonitor.prototype.reconnect = function() {
    setTimeout(this.connect.bind(this), 1000);
}

