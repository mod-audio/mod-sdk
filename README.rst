=======
MOD SDK
=======

This SDK's goal is to allow LV2 plugin developers to implement the `MOD Gui extension <http://moddevices.com/ns/modgui>`.
In MOD Devices, every plugin has a real pedal like representation in a web based environment, with several plugins in a pedalboard.
For this, each plugin must have html code that allows the browser to properly render it.

This SDK provides the following funcionality:

* Allows developers to change the ttl, html and related files and imediately see changes
* A wizard for to choose and configure some interfaces that are already done, so that developer does not have to start from scratch
* Routines for installing the plugin at a MOD device

To use the SDK, developers should adjust their LV2_PATH to where LV2 bundles reside, run a local webserver (modsdk command) and open a webkit-based browser at http://localhost:9000.

Build
-------

We use lilv to scan plugins, phantomjs to render screenshots and `pillow`_ to build png images.
If you use a Debian-based GNU/Linux distribution (like Ubuntu), you can install all this with::

    $ sudo apt-get install liblilv-dev phantomjs python3-pil python3-pystache python3-tornado

After you have all dependencies installed, build it with::

    $ python3 setup.py build

Run
---

If you don't want to install, simply run::

    $ ./development_server.py

To install mod-sdk, run::

    $ [sudo] python3 setup.py install

After install you can run the server like so::

    $ modsdk

Then open your browser (webkit based is preferable) and point to http://localhost:9000.

.. _pillow: http://pillow.readthedocs.org/en/latest/
