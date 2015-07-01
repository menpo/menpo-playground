# ATOMIC MENPO

### What is atomicmenpo?
atomicmenpo is a one-click installer for the latest stable version of The Menpo
Project. atomicmenpo creates a single directory and installs all of Menpo
inside this folder in a completely isolated way. To remove, simply delete the
folder.


### How do I use it?

On Linux or OS X:

1. Download the [latest installer](https://raw.githubusercontent.com/menpo/atomicmenpo/master/installmenpo)
2. Place the file in a folder where you want to install Menpo
3. Open a terminal, `cd` to your chosen directory, and run the script:

```sh
> cd ./my_dir/
> ./installmenpo
```

That's it. You'll have a clean isolated install of Menpo ready to use at
`./atomicmenpo`. You'll also have example noteooks available at
`./menpo_notebooks`. Read `./atomicmenpo/README.md` to get started with Menpo.


### Can I move the atomicmenpo folder?

No. Python in general does not support being relocated very nicely. If you want
to move atomicmenpo some place else, just rerun the installer in the new place.

### Can I put my .py files and notebooks inside it?

No. Don't place anything inside `./atomicmenpo`. You may want to blow this away
in the future - keep your own code elsewhere.

### Why doesn't this work on Windows?

A key goal of this installer is giving less technical users confidence that we
aren't junking their system with a bunch of software they don't understand.
Fundamental limitations in Windows make it challenging to make a standalone
versions of Python-based projects like Menpo.

### Who is atomicmenpo for?

Atomicmenpo is ideal for people who are completely new to Python and are
interested to try out Menpo, perhaps for it's command line tools or
benchmarking feature. It tries to replicate as close as we can the experience
of downloading a traditional piece of software, running `make`, and having a
bunch of 'executables' ready to play with.

It's also useful for more advanced users as a convenient method to generate a
clean install of the latest stable version of menpo that is not only unrelated
to the system Python, but even unrelated to any existing conda installation.
atomicmenpo essentially runs the same bootstrapping script we use when
performing Continuous Integration (CI) testing, so if you are worried you have
in any way borked your existing menpo installation, it can be convenient to
download atomicmenpo to get a clean slate to test something out in.

### How does it work?

The installer itself is written in Python and is easy enough to follow.
Concretely though, it:

1. Downloads the latest version of Python 2 Miniconda for your platform
2. Installs Miniconda as normal to `./atomicmenpo/miniconda`
3. Updates `conda` in this new env
4. Installs `menpo` `menpodetect` `menpo3d` & `menpofit` from the `menpo` conda
 channel into the root environment of the newly installed env
5. Copies the example notebooks for all the projects into `./menpo_notebooks`
6. Downloads a `README.md` to ``./atomicmenpo/README.md`
7. Symlinks some binaries from `./atomicmenpo/miniconda/bin/` to `./atomicmenpo` for easy access
8. Cleans up after itself, removing the miniconda installer and purging the conda cache

The installer does not modify anything outside of the `./` folder.
This means that we cannot make our newly installed binaries globally available
(you cannot just open a terminal and run `ipython` for instance), but means
that atomicmenpo installs are nice and isolated.


### Why are you making another mechanism for Python installation? Isn't it confusing enough as it is?

atomicmenpo is **not a new way to install a general Python installation**. It
simply is a small script that calls the usual miniconda installer with some
opinionated stance on configuration. We aren't reinventing the wheel (tehe) here.
If you are already experienced with Python then feel free to `conda install
-c menpo menpo menpofit menpodetect menpo3d` and be glad that we have built all our binary dependencies so everything
just works on Linux Windows and OS X. If you really want to `pip install menpo`
you can, but you'll have a real fight on your hands to get all our binary
dependencies intalled. (Seriously, don't fight it, just use conda).

Our project unfortunately lies at the interaction of having very
challenging dependencies to install (hence our insistence on conda) and
appealing to people who may be completely new to the Python community.
A researcher who has solely used Matlab for 20 years is going to understandably
be intimidated by having to setup a 'correct' Python environment to just try and
call `menpofit`'s assortment of excellent face alignment techniques.
atomicmenpo lowers the barrier to entry considerably so we can welcome in such
users. Maybe they will see the light and embark upon learning about how to use
Python correctly - that's great, one day they won't need atomicmenpo any more.

### Wait, so is this the preferred way to install Menpo?

If you don't have a clue about Python and want to play with Menpo as soon as
possible, yes. If you are a experienced Python user, **no**. You should just
use conda as normal and conda install menpo.


### Why would I not just use this though? What's the benefit of having a proper conda installation?

Once you have been using Python a little you will realize that the structure of
conda (or virtualenv) where you have multiple isolated environments that can be
easily switched between is really valuable. You'll also want all those utilities
to be on your path at all times, so you don't have to live our of one folder on
your system like a hermit. Then you'll get to grips with installing development
versions of packages so you can edit them to contribute back to the community.
You'll discover git and it will transform the way you conduct your work or
research.

One day all this will make sense and you will want to maintain a global conda
install to make your life easier. Until then, atomicmenpo is here.

### Can I upgrade to newer versions of Menpo?

Sure, just run `./atomicmenpo/upgrade`


### Can I use development versions of Menpo?

No. Well, you can, but we aren't encouraging that. If you want to use
development builds of Menpo then you really should be managing a proper conda
installation.

### Can I install other Python packages?

Sure. First try `./atomicmenpo/conda install PACKAGENAME`. If that fails, go for
`./atomicmenpo/pip install PACKAGENAME`

### Wait, I screwed something up trying to install other packages. How do I reset atomicmenpo?

Just download the installer and run in a new dir to get everything fresh again.
