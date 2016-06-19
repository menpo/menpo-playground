Menpo Playground
================

Menpo Playground is a single directory that you can download from
[menpo.org](http://www.menpo.org) which contains  the latest stable version of
The Menpo Project. Download and unpack one `.zip` or `.tar.xz` file, and you 
instantly have access to:

1. A full isolated Python installation containing the Menpo Project with all its dependencies ready to go
2. A set of notebooks that you can run immediately to see how to use Menpo
3. Two command line tools, `menpofit`, and `menpodetect`, that can be used to locate bounding boxes and landmarks in challenging in-the-wild facial images.

There is no installation step, you just run executables in the downloaded folder.
To remove, simply delete the folder.

Building a Menpo Playground
---------------------------

This repository contains the code needed to build a Menpo Playground file.

Code in this repository must be run on each supported OS (Windows, Mac, Linux)
in order to generate OS-specific Menpo Playground artifacts.
There is no cross-compilation - a Windows host is needed to create the Windows
Menpo Playground.


###Windows
Run:
```
> build.cmd
```
The following **bundled** artifact is produced:

- `menpo_playground.zip`

###macOS & Linux: 
Run:
```
> ./build.sh
```
The following **static** artifacts are produced:

- `menpo_playground.tar.xz`
- `menpo_playground.zip`

Goals of the Menpo Playground
-----------------------------

Our goal with Menpo Playground is to lower the barrier to entry to Menpo 
for users. The Menpo Playground therefore should have the following 
characteristics:

- **Small**. The file we ask users to download should be made as small as 
possible.
- **Full featured**. One of the things that makes Menpo great is that all 
depenencies are handled for you, so we want the playground to feel like you
have access to everything you want in Menpo.
- **Simple**. The process from clicking the download link to getting to use
Menpo should be aggressively simplified as much as possible.


Clearly, the above goals are in competition with each other. A Zip file is
the simplest form of distribution, but it's poor compression leads to a large
file. We could strip out a bunch of features from Menpo to make something 
smaller, but that would water-down the appeal of the Playground being a
holistic tool that has everything you need.

Static vs Bundled builds 
------------------------

To try and optimise for the above three goals we have arrived at two means
of installation (and hence two build techniques) for Menpo Playground:
static, or bundled.

A **static build** is simply an archive of a folder that is ready to go with 
everything needed. Installation of a static install only requires the
user to extract the archive to any location on their system, then the tools
are ready to use. This optimizes for **simplicity**. For platforms where we
know users have access to powerful compression algorithms (namely, LZMA) this
is the build type we offer.

A static build is great if we can compress the build effectively using 
something like LZMA, but for platforms which don't have native LZMA support 
like Windows and OS X pre-Yosemite, requiring users to have third-party 
extractors hurts **simplicity**.

In fact on Windows, Zip, with it's pretty poor compression ratios is the 
only game in town (unless you go for a self-extracting archive).

A **bundled build** is a solution to this issue. Python 3.3+ includes LZMA
support, so we can ship a .zip file containing only the files needed to 
perform LZMA extraction. The rest of the content in the build is internally
bundled into a `tar.xz` file that can be unpacked by a single command after
unzipping. The user experience with a bundled build is as follows:

1. Download `menpo-playground.zip` and extract it.
2. Discover the unpacked folder contains the following:
```
src/
Get Started.cmd
Get Started readme.md  
```
3. Double click `Get Started` (Windows), and an extraction occurs with
accurate ETA
4. After extraction you are left in the exact same state as a 
**static install** (the get started files are swept away automatically).
