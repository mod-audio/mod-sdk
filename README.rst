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

We use python 3.5, `lilv` to scan plugins, `phantomjs` to render screenshots and `pillow`_ to build png images.
If you use a Debian-based GNU/Linux distribution (like Ubuntu), you can install all this with::

    $ sudo apt-get install build-essential liblilv-dev phantomjs python3-pil python3-pystache python3-tornado python3-setuptools python3-pyinotify

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

Docker Image
------------

You can also use the SDK Docker Image.

Choose a folder where you will store your LV2 plugins bundles. In this folder place all the bundles you want to test with the SDK

Pull the SDK image from Docker Hub::

    $ docker pull moddevices/modsdk

You only need to run this command the first time. It will download the image and store it locally.

Once the download is completed, run the following command, replacing the path with the path of the folder where you are storing your LV2 bundles::

    $ docker run -p 9000:9000 -v /Users/my-user/my-lv2-folder:/lv2 moddevices/modsdk

Now open your browser and visit http://localhost:9000.

Building the Docker Image
_________________________

If you want to build the image locally using the provided Dockerfile, from the root of this repository type::

    $ docker build -t modsdk .

