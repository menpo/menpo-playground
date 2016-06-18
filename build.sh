#!/bin/bash
set -e  # stop on errors

MINICONDA_URL=https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
if [[ $OSTYPE == darwin* ]]; then
    MINICONDA_URL=https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
fi

# Make sure there is no current build dir and create it
rm -r ./build || true
mkdir ./build

# Download the latest installer and make it runnable
wget $MINICONDA_URL -O ./build/miniconda.sh
chmod u+x ./build/miniconda.sh
./build/miniconda.sh -b -p ./build/miniconda

./build/miniconda/bin/python ./menpotoolbox.py build
# run this to re-enable bundle builds (maybe for windows?)
# ./build/miniconda/bin/python ./menpotoolbox.py bundle

# Download the latest notebooks and add them to the toolbox
# wget https://github.com/menpo/menpo-notebooks/archive/master.zip
# unzip master.zip
# cp -r menpo-notebooks-master/notebooks ./menpotoolbox/

# Add in our local scripts too (from the dir above)
# cp ../unix/* ./menpotoolbox/
