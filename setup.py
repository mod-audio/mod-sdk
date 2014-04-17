from setuptools import setup, find_packages
import os

setup(name = 'mod-sdk',
      version = '0.99.0',
      description = 'MOD plugin SDK.',
      author = "Luis Fagundes",
      author_email = "lhfagundes@hacklab.com.br",
      license = "GPLv3",
      packages = find_packages(),
      install_requires = ['rdflib>=3.4.0', 'whoosh>=2.4.1', 'pymongo>=2.5', 'pystache>=0.5.3', 'pillow>=2.4.0', 'tornado>=3.2', 'modcommon>=0.99.0' ],
      entry_points = {
          'console_scripts': [
            'modsdk = modsdk.webserver:run',
            ]
          },
      classifiers = [
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
        ],
      url = 'http://github.com/portalmod/mod-sdk',
      
)
