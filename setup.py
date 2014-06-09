from setuptools import setup, find_packages
import os, sys

MANIFEST = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'MANIFEST.in')

def data_dir(prefix, dirname):
    data_files = []
    html_files = []
    for fname in os.listdir(dirname):
        fname = os.path.join(dirname, fname)
        if os.path.isfile(fname):
            html_files.append(fname)
            open(MANIFEST, 'a').write('include %s\n' % fname)
        if os.path.isdir(fname):
            data_files += data_dir(prefix, fname)
    return [ (os.path.join(prefix, dirname), html_files) ] + data_files

open(MANIFEST, 'w').write('include screenshot.js\n')
share = os.path.join(sys.prefix, 'share')
data_files = data_dir(share, 'html')
data_files += [(share, ['screenshot.js'])]

setup(name = 'modsdk',
      version = '1.1.1',
      description = 'MOD plugin SDK.',
      author = "Luis Fagundes",
      author_email = "lhfagundes@hacklab.com.br",
      license = "GPLv3",
      packages = find_packages(),
      install_requires = ['rdflib>=3.4.0', 'whoosh>=2.4.1', 'pymongo>=2.5', 'pystache>=0.5.3', 'pillow>=2.4.0', 'tornado>=3.2', 'modcommon>=0.99.0' ],
      data_files = data_files,
      entry_points = {
          'console_scripts': [
            'modsdk = modsdk.webserver:run',
            'modsdk-screenshot = modsdk.screenshot:run',
            ]
          },
      classifiers = [
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
        ],
      include_package_data = True,
      url = 'http://github.com/portalmod/mod-sdk',
      
)
