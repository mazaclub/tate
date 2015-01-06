#!/usr/bin/python

# python setup.py sdist --format=zip,gztar

from setuptools import setup
import os
import sys
import platform
import imp


version = imp.load_source('version', 'lib/version.py')
util = imp.load_source('version', 'lib/util.py')

if sys.version_info[:3] < (2, 6, 0):
    sys.exit("Error: Tate requires Python version >= 2.6.0...")

usr_share = '/usr/share'
if not os.access(usr_share, os.W_OK):
    usr_share = os.getenv("XDG_DATA_HOME", os.path.join(os.getenv("HOME"), ".local", "share"))

data_files = []
if (len(sys.argv) > 1 and (sys.argv[1] == "sdist")) or (platform.system() != 'Windows' and platform.system() != 'Darwin'):
    print "Including all files"
    data_files += [
        (os.path.join(usr_share, 'applications/'), ['tate.desktop']),
        (os.path.join(usr_share, 'app-install', 'icons/'), ['icons/tate.png'])
    ]
    if not os.path.exists('locale'):
        os.mkdir('locale')
    for lang in os.listdir('locale'):
        if os.path.exists('locale/%s/LC_MESSAGES/electrum.mo' % lang):
            data_files.append((os.path.join(usr_share, 'locale/%s/LC_MESSAGES' % lang), ['locale/%s/LC_MESSAGES/electrum.mo' % lang]))


appdata_dir = util.appdata_dir()
if not os.access(appdata_dir, os.W_OK):
    appdata_dir = os.path.join(usr_share, "tate")

data_files += [
    (appdata_dir, ["data/README"]),
    (os.path.join(appdata_dir, "cleanlook"), [
        "data/cleanlook/name.cfg",
        "data/cleanlook/style.css"
    ]),
    (os.path.join(appdata_dir, "sahara"), [
        "data/sahara/name.cfg",
        "data/sahara/style.css"
    ]),
    (os.path.join(appdata_dir, "dark"), [
        "data/dark/name.cfg",
        "data/dark/style.css"
    ])
]

for lang in os.listdir('data/wordlist'):
    data_files.append((os.path.join(appdata_dir, 'wordlist'), ['data/wordlist/%s' % lang]))


setup(
    name="Tate",
    version=version.ELECTRUM_VERSION,
    install_requires=[
        'slowaes',
        'ecdsa>=0.9',
        'pbkdf2',
        'requests',
        'pyasn1',
        'pyasn1-modules',
        'qrcode',
        'SocksiPy-branch',
        'tlslite'
    ],
    package_dir={
        'tate': 'lib',
        'tate_gui': 'gui',
        'tate_plugins': 'plugins',
    },
    scripts=['tate'],
    data_files=data_files,
    py_modules=[
        'tate.account',
        'tate.bitcoin',
        'tate.blockchain',
        'tate.bmp',
        'tate.commands',
        'tate.daemon',
        'tate.i18n',
        'tate.interface',
        'tate.mnemonic',
        'tate.msqr',
        'tate.network',
        'tate.network_proxy',
        'tate.old_mnemonic',
        'tate.paymentrequest',
        'tate.paymentrequest_pb2',
        'tate.plugins',
        'tate.qrscanner',
        'tate.simple_config',
        'tate.synchronizer',
        'tate.transaction',
        'tate.util',
        'tate.verifier',
        'tate.version',
        'tate.wallet',
        'tate.x509',
        'tate_gui.gtk',
        'tate_gui.qt.__init__',
        'tate_gui.qt.amountedit',
        'tate_gui.qt.console',
        'tate_gui.qt.history_widget',
        'tate_gui.qt.icons_rc',
        'tate_gui.qt.installwizard',
        'tate_gui.qt.lite_window',
        'tate_gui.qt.main_window',
        'tate_gui.qt.network_dialog',
        'tate_gui.qt.password_dialog',
        'tate_gui.qt.paytoedit',
        'tate_gui.qt.qrcodewidget',
        'tate_gui.qt.qrtextedit',
        'tate_gui.qt.receiving_widget',
        'tate_gui.qt.seed_dialog',
        'tate_gui.qt.transaction_dialog',
        'tate_gui.qt.util',
        'tate_gui.qt.version_getter',
        'tate_gui.stdio',
        'tate_gui.text',
        'tate_plugins.btchipwallet',
        'tate_plugins.coinbase_buyback',
        'tate_plugins.cosigner_pool',
        'tate_plugins.exchange_rate',
        'tate_plugins.greenaddress_instant',
        'tate_plugins.labels',
        'tate_plugins.trezor',
        'tate_plugins.virtualkeyboard',
    ],
    description="Lightweight Mazacoin Wallet",
    author="Thomas Voegtlin; forked for Mazacoin by mazaclub",
    author_email="thomasv1@gmx.de",
    license="GNU GPLv3",
    # TODO Change for tate
    url="https://electrum.org",
    long_description="""Lightweight Mazacoin Wallet. A Mazacoin-compatible fork of Electrum."""
)
