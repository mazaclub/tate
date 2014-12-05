#!/bin/bash

# You probably need to update only this link
# TODO Change for tate
ELECTRUM_URL=http://electrum.bitcoin.cz/download/Electrum-1.6.1.tar.gz
NAME_ROOT=tate1.6.1

# These settings probably don't need any change
export WINEPREFIX=/opt/wine-tate
PYHOME=c:/python26
PYTHON="wine $PYHOME/python.exe -OO -B"

# Let's begin!
cd `dirname $0`
set -e

cd tmp

# Download and unpack Tate
wget -O tate.tgz "$ELECTRUM_URL"
tar xf tate.tgz
mv Tate-* tate
rm -rf $WINEPREFIX/drive_c/tate
cp tate/LICENCE .
mv tate $WINEPREFIX/drive_c

# Copy ZBar libraries to electrum
#cp "$WINEPREFIX/drive_c/Program Files (x86)/ZBar/bin/"*.dll "$WINEPREFIX/drive_c/electrum/"

cd ..

rm -rf dist/$NAME_ROOT
rm -f dist/$NAME_ROOT.zip
rm -f dist/$NAME_ROOT.exe
rm -f dist/$NAME_ROOT-setup.exe

# For building standalone compressed EXE, run:
$PYTHON "C:/pyinstaller/pyinstaller.py" --noconfirm --ascii -w --onefile "C:/tate/tate"

# For building uncompressed directory of dependencies, run:
$PYTHON "C:/pyinstaller/pyinstaller.py" --noconfirm --ascii -w deterministic.spec

# For building NSIS installer, run:
wine "$WINEPREFIX/drive_c/Program Files (x86)/NSIS/makensis.exe" tate.nsi
#wine $WINEPREFIX/drive_c/Program\ Files\ \(x86\)/NSIS/makensis.exe electrum.nsis

cd dist
mv tate.exe $NAME_ROOT.exe
mv tate $NAME_ROOT
mv tate-setup.exe $NAME_ROOT-setup.exe
zip -r $NAME_ROOT.zip $NAME_ROOT
