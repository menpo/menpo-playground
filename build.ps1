$MINICONDA_URL = https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe
$wc = New-Object System.Net.WebClient

# Make sure there is no current build dir and create it
rm .\build -r -f 
mkdir .\build

# Download the latest installer
$wc.DownloadFile($MINICONDA_URL, "$PSScriptRoot\build\miniconda.exe")

# Install Miniconda inside as the src dir...
build\miniconda.exe -b -p ./build/miniconda

# # Download the latest notebooks and add them to the toolbox
# $NOTEBOOKS_URL = https://github.com/menpo/menpo-notebooks/archive/master.zip
# $wc.DownloadFile($NOTEBOOKS_URL, "$PSScriptRoot\notebooks.zip")
# unzip notebooks.zip
# cp -r menpo-notebooks-master/notebooks ./menpotoolbox/


# Add in our local scripts too (from the dir above)
# cp ../windows/* ./menpotoolbox/
