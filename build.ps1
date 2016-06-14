$MINICONDA_URL = https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe
$NOTEBOOKS_URL = https://github.com/menpo/menpo-notebooks/archive/master.zip
$wc = New-Object System.Net.WebClient

# Remove any existing artifact
rm menpotoolbox.7z

# Make sure there is no current build dir and create it
rm .\build -r -f 
mkdir .\build

# Go into the temp build folder. Note that we do everything
# in this context from here on out.
cd .\build

# Make the directory which will be our final package
mkdir .\menpotoolbox

# Download the latest notebooks and add them to the toolbox
$wc.DownloadFile($NOTEBOOKS_URL, "$PSScriptRoot\notebooks.zip")
unzip notebooks.zip
cp -r menpo-notebooks-master/notebooks ./menpotoolbox/

# Add in our local scripts too (from the dir above)
cp ../windows/* ./menpotoolbox/

# Download the latest installer
$wc.DownloadFile($MINICONDA_URL, "$PSScriptRoot\miniconda.exe")

# Install Miniconda inside as the src dir...
miniconda.exe -b -p ./menpotoolbox/src

# ...and install the Menpo Project into it
menpotoolbox/src/bin/conda install -y -c menpo menpoproject

# Remove dirs that are redundent at run time
include
pkgs
Library/include
Library/libboost_test_exec_monitor-vc140-mt-gd-1_59.lib
Doc
Uninstall-Anaconda.exe
Scripts/ffplay.exe
Lib/test

# strip all Python debug symbols and pycache files
.pdb  Python debug symbols
find ./menpotoolbox/src -name __pycache__ -type d -exec rm -rf {} \; || true

# Finally, zip the folder up real tight with 7zip
7z a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on ../menpotoolbox.7z ./menpotoolbox
