$MINICONDA_URL = "https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe"
$wc = New-Object System.Net.WebClient

# # Make sure there is no current build dir and create it
New-Item "$PSScriptRoot\build" -type directory -force

# # Download the latest installer
$wc.DownloadFile($MINICONDA_URL, "$PSScriptRoot\build\miniconda.exe")

# Install Miniconda inside as the src dir...
# See http://stackoverflow.com/a/1742758 for the | Out-Null business.
build\miniconda.exe /S /AddToPath=0 /NoRegistry=1 /D="$PSScriptRoot\build\miniconda" | Out-Null
