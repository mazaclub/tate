#!/bin/bash

# You probably need to update only this link
# TODO Change for Tate
ELECTRUM_GIT_URL=git://github.com/spesmilo/electrum.git
BRANCH=master
NAME_ROOT=tate

# These settings probably don't need any change
export WINEPREFIX=/opt/wine-tate
PYHOME=c:/python26
PYTHON="wine $PYHOME/python.exe -OO -B"

# Let's begin!
cd `dirname $0`
set -e

cd tmp

if [ -d "tate-git" ]; then
    # GIT repository found, update it
    echo "Pull"

    cd tate-git
    git pull
    cd ..

else
    # GIT repository not found, clone it
    echo "Clone"

    git clone -b $BRANCH $ELECTRUM_GIT_URL tate-git
fi

cd tate-git
COMMIT_HASH=`git rev-parse HEAD | awk '{ print substr($1, 0, 11) }'`
echo "Last commit: $COMMIT_HASH"
cd ..


rm -rf $WINEPREFIX/drive_c/tate
cp -r tate-git $WINEPREFIX/drive_c/tate
cp tate-git/LICENCE .

# Build Qt resources
wine $WINEPREFIX/drive_c/Python26/Lib/site-packages/PyQt4/pyrcc4.exe C:/tate/icons.qrc -o C:/tate/lib/icons_rc.py

# Copy ZBar libraries to electrum
#cp "$WINEPREFIX/drive_c/Program Files (x86)/ZBar/bin/"*.dll "$WINEPREFIX/drive_c/electrum/"

cd ..

rm -rf dist/

# For building standalone compressed EXE, run:
$PYTHON "C:/pyinstaller/pyinstaller.py" --noconfirm --ascii -w --onefile "C:/tate/tate"

# For building uncompressed directory of dependencies, run:
$PYTHON "C:/pyinstaller/pyinstaller.py" --noconfirm --ascii -w deterministic.spec

# For building NSIS installer, run:
wine "$WINEPREFIX/drive_c/Program Files (x86)/NSIS/makensis.exe" tate.nsi
#wine $WINEPREFIX/drive_c/Program\ Files\ \(x86\)/NSIS/makensis.exe electrum.nsis

DATE=`date +"%Y%m%d"`
cd dist
mv tate.exe $NAME_ROOT-$DATE-$COMMIT_HASH.exe
mv tate $NAME_ROOT-$DATE-$COMMIT_HASH
mv tate-setup.exe $NAME_ROOT-$DATE-$COMMIT_HASH-setup.exe
zip -r $NAME_ROOT-$DATE-$COMMIT_HASH.zip $NAME_ROOT-$DATE-$COMMIT_HASH
