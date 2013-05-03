=======
MOD SDK
=======

This SDK's goal is to allow LV2 plugin developers to implement the `MOD Gui extension <http://portalmod.com/ns/modgui>`. In MOD Gui, every plugin has a real pedal like representation in a web based environment, with several plugins in a pedalboard. For this, each plugin must have html code that allows the browser to properly render it.

This SDK provides the following funcionality:

* Allows developers to change the ttl, html and related files and imediately see changes
* A wizard for to choose and configure some interfaces that are already done, so that developer does not have to start from scratch
* Routines for installing the plugin at the MOD device / MOD host software and publishing it at MOD Cloud

To use the SDK, developers should put their LV2 bundles in workspace/ folder, inside the SDK, run a local webserver and open a webkit-based browser at http://localhost:9000. Everytime the page is reloaded, the ttl files will be parsed to display results accordinly.

Tip: follow the LV2 bundle recomendations and don't put several plugins in each bundle. If you do this, loading the page and generating thumbnails may take a lot of time.

Install
-------

These are instructions for installing in 64-bit Debian based Linux environment. It will work in x86 and Mac, but you might need to adjust the instructions.

The following packages will be required:

    $ sudo apt-get install python-virtualenv python-pip git zlib1g:amd64

Create a python virtualenv::

    $ virtualenv modsdk-env
    $ source modsdk-env/bin/activate

Install the mod-python library::

    $ pip install -e git+https://github.com/portalmod/mod-python.git@new_interface#egg=mod-python

Install PIL (it needs this symlink to be compiled with zlib support) and tornado::

    $ sudo ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
    $ pip install PIL tornado

Download PhantomJS::

    $ wget https://phantomjs.googlecode.com/files/phantomjs-1.9.0-linux-x86_64.tar.bz2
    $ tar jxf phantomjs-1.9.0-linux-x86_64.tar.bz2
    $ rm phantomjs-1.9.0-linux-x86_64.tar.bz2

Run the server::

    $ ./development_server.py

Open your webkit based browser (I use Chromium) and point to __http://localhost:9000__
