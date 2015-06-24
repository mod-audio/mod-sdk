=======
MOD SDK
=======

This SDK's goal is to allow LV2 plugin developers to implement the `MOD Gui extension <http://moddevices.com/ns/modgui>`. In MOD Gui, every plugin has a real pedal like representation in a web based environment, with several plugins in a pedalboard. For this, each plugin must have html code that allows the browser to properly render it.

This SDK provides the following funcionality:

* Allows developers to change the ttl, html and related files and imediately see changes
* A wizard for to choose and configure some interfaces that are already done, so that developer does not have to start from scratch
* Routines for installing the plugin at the MOD device / MOD host software and publishing it at MOD Cloud

To use the SDK, developers should put their LV2 bundles in $HOME/mod-workspace/ folder, run a local webserver (modsdk command) and open a webkit-based browser at http://localhost:9000. Everytime the page is reloaded, the ttl files will be parsed to display results accordinly.

Tip: follow the LV2 bundle recomendations and don't put several plugins in each bundle. If you do this, loading the page and generating thumbnails may take a lot of time.

Install
-------

Just type:

    $ pip install modsdk

You can get the `pip command here`_.

You'll need phantomjs to render screenshots and zlib to build png images with `pillow`_. If you use a Debian-based GNU/Linux distribution (like Ubuntu), you can do this with::

    $ sudo apt-get install zlib1g phantomjs

If you use Linux, install pyinotify. This is used to expire bundle cached data when ttl files are changed. Without pyinotify no cache will be used. To install it::

    $ pip install pyinotify

Run
---

Run the server::

    $ modsdk

Open your webkit based browser (I use Chromium) and point to http://localhost:9000.

.. _pip command here: http://pip.openplans.org/
.. _pillow: http://pillow.readthedocs.org/en/latest/

