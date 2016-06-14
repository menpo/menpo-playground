#!/bin/bash
set -e  # stop on errors

MINICONDA_URL=https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
if [[ $OSTYPE == darwin* ]]; then
    MINICONDA_URL=https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
fi

# Check we have 7z installed
7z -h > /dev/null

# Remove any existing artifacts
rm ./menpotoolbox.7z ./menpotoolbox.tar.gz || true

# Make sure there is no current build dir and create it
rm -r ./build || true
mkdir ./build

# Go into the temp build folder. Note that we do everything
# in this context from here on out.
cd ./build

# Make the directory which will be our final package
mkdir menpotoolbox

# Download the latest notebooks and add them to the toolbox
wget https://github.com/menpo/menpo-notebooks/archive/master.zip
unzip master.zip
cp -r menpo-notebooks-master/notebooks ./menpotoolbox/

# Add in our local scripts too (from the dir above)
cp ../unix/* ./menpotoolbox/

# Download the latest installer and make it runnable
wget $MINICONDA_URL -O miniconda.sh
chmod u+x miniconda.sh

# Install Miniconda inside as the src dir...
./miniconda.sh -b -p ./menpotoolbox/src

# ...and install the Menpo Project into it
./menpotoolbox/src/bin/conda install -y -c menpo menpoproject

# Remove dirs that are redundent at run time
rm -r ./menpotoolbox/src/include/* ./menpotoolbox/src/pkgs/*

# Prune out cached files
find ./menpotoolbox/src -name __pycache__ -type d -exec rm -rf {} \; || true

# Finally, zip the folder up real tight with 7zip
7z a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on ../menpotoolbox.7z ./menpotoolbox

# Zip it
zip -r ../menpotoolbox.zip ./menpotoolbox

# And create a tar.gz/tar.bz2
tar -zcvf ../menpotoolbox.tar.gz ./menpotoolbox
tar -jcvf ../menpotoolbox.tar.bz2 ./menpotoolbox
