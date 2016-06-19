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

./build/miniconda/bin/python ./menpo_playground.py build
