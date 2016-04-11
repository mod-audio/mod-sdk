#!/bin/bash

set -e

if [ ! -d mod.lv2 ]; then
  echo "mod.lv2 bundle missing"
  exit
fi

if [ ! -d modgui.lv2 ]; then
  echo "modgui.lv2 bundle missing"
  exit
fi

if (! which lv2specgen.py >/dev/null); then
  echo "lv2specgen.py tool missing"
  exit
fi

if [ ! -d documentation ]; then
  mkdir documentation
fi

if [ ! -f documentation/style.css ]; then
  git clone git://github.com/moddevices/mod-sdk --depth 1 -b gh-pages documentation
fi

cp mod.lv2/*    documentation/mod/
cp modgui.lv2/* documentation/modgui/

lv2specgen.py $(pwd)/mod.lv2/manifest.ttl    /usr/share/lv2specgen/ ../style.css $(pwd)/documentation/mod/index.html    $(pwd)/documentation/mod    "" -i -p mod
lv2specgen.py $(pwd)/modgui.lv2/manifest.ttl /usr/share/lv2specgen/ ../style.css $(pwd)/documentation/modgui/index.html $(pwd)/documentation/modgui "" -i -p modgui
