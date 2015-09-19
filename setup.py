#!/usr/bin/python

# python setup.py sdist --format=zip,gztar

from setuptools import setup
import os
import sys
import platform
import imp


version = imp.load_source('version', 'lib/version.py')

if sys.version_info[:3] < (2, 7, 0):
    sys.exit("Error: Tate requires Python version >= 2.7.0...")



data_files = []
if platform.system() in [ 'Linux', 'FreeBSD', 'DragonFly']:
    usr_share = os.path.join(sys.prefix, "share")
    data_files += [
        (os.path.join(usr_share, 'applications/'), ['tate.desktop']),
        (os.path.join(usr_share, 'pixmaps/'), ['icons/tate.png'])
    ]


setup(
    name="Tate",
    version=version.ELECTRUM_VERSION,
    install_requires=[
        'slowaes>=0.1a1',
        'ecdsa>=0.9',
        'pbkdf2',
        'requests',
        'qrcode',
        'protobuf',
        'dnspython',
    ],
    package_dir={
        'tate': 'lib',
        'tate_gui': 'gui',
        'tate_plugins': 'plugins',
    },
    packages=['tate','tate_gui','tate_gui.qt','tate_plugins'],
    package_data={
        'tate': [
            'www/index.html',
            'wordlist/*.txt',
            'locale/*/LC_MESSAGES/electrum.mo',
        ],
        'tate_gui': [
            "qt/themes/cleanlook/name.cfg",
            "qt/themes/cleanlook/style.css",
            "qt/themes/sahara/name.cfg",
            "qt/themes/sahara/style.css",
            "qt/themes/dark/name.cfg",
            "qt/themes/dark/style.css",
        ]
    },
    scripts=['tate'],
    data_files=data_files,
    description="Lightweight Mazacoin Wallet",
    author="mazaclub",
    license="GNU GPLv3",
    long_description="""Lightweight Mazacoin Wallet"""
)
