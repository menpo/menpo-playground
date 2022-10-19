import contextlib
from functools import partial
import lzma
import os
from pathlib import Path
import pickle
import shutil
import tarfile
import time
import subprocess
import sys
from urllib.request import urlopen
import platform
from zipfile import ZipFile

IS_WINDOWS = platform.system() == 'Windows'
PLATFORM_STR = 'win' if IS_WINDOWS else 'unix'


@contextlib.contextmanager
def tmp_chdir(new_dir):
    cur_dir = os.getcwd()
    try:
        os.chdir(str(new_dir))
        yield
    finally:
        os.chdir(cur_dir)


def progress_bar_str(percentage, bar_length=20, bar_marker='=', show_bar=True):
    r"""
    Returns an `str` of the specified progress percentage. The percentage is
    represented either in the form of a progress bar or in the form of a
    percentage number. It can be combined with the :func:`print_dynamic`
    function.
    Parameters
    ----------
    percentage : `float`
        The progress percentage to be printed. It must be in the range
        ``[0, 1]``.
    bar_length : `int`, optional
        Defines the length of the bar in characters.
    bar_marker : `str`, optional
        Defines the marker character that will be used to fill the bar.
    show_bar : `bool`, optional
        If ``True``, the `str` includes the bar followed by the percentage,
        e.g. ``'[=====     ] 50%'``
        If ``False``, the `str` includes only the percentage,
        e.g. ``'50%'``
    Returns
    -------
    progress_str : `str`
        The progress percentage string that can be printed.
    Raises
    ------
    ValueError
        ``percentage`` is not in the range ``[0, 1]``
    ValueError
        ``bar_length`` must be an integer >= ``1``
    ValueError
        ``bar_marker`` must be a string of length 1
    Examples
    --------
    This for loop: ::
        n_iters = 2000
        for k in range(n_iters):
            print_dynamic(progress_bar_str(float(k) / (n_iters-1)))
    prints a progress bar of the form: ::
        [=============       ] 68%
    """
    if percentage < 0:
        raise ValueError("percentage is not in the range [0, 1]")
    elif percentage > 1:
        percentage = 1
    if not isinstance(bar_length, int) or bar_length < 1:
        raise ValueError("bar_length must be an integer >= 1")
    if not isinstance(bar_marker, str) or len(bar_marker) != 1:
        raise ValueError("bar_marker must be a string of length 1")
    # generate output string
    if show_bar:
        str_param = "[%-" + str(bar_length) + "s] %d%%"
        bar_percentage = int(percentage * bar_length)
        return str_param % (bar_marker * bar_percentage, percentage * 100)
    else:
        return "%d%%" % (percentage * 100)


def print_dynamic(str_to_print):
    r"""
    Prints dynamically the provided `str`, i.e. the `str` is printed and then
    the buffer gets flushed.
    Parameters
    ----------
    str_to_print : `str`
        The string to print.
    """
    sys.stdout.write("\r{}".format(str_to_print.ljust(80)))
    sys.stdout.flush()


def copy_and_yield(fsrc, fdst, length=1024*1024):
    """copy data from file-like object fsrc to file-like object fdst"""
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
        yield
        

def download_file(url, destination, verbose=False):
    r"""
    Download a file from a URL to a path, optionally reporting the progress
    Parameters
    ----------
    url : `str`
        The URL of a remote resource that should be downloaded
    destination : `Path`
        The path on disk that the file will be downloaded to
    verbose : `bool`, optional
        If ``True``, report the progress of the download dynamically.
    """
    req = urlopen(url)
    chunk_size_bytes = 512 * 1024

    with open(str(destination), 'wb') as fp:

        # Retrieve a generator that we can keep yielding from to download the
        # file in chunks.
        for _ in copy_and_yield(req, fp, length=chunk_size_bytes):
            pass

    req.close()


def norm_path(filepath):
    r"""
    Uses all the tricks in the book to expand a path out to an absolute one.
    """
    return Path(os.path.abspath(os.path.normpath(
        os.path.expandvars(os.path.expanduser(str(filepath))))))


def rm_dir(path) :
    if path.is_symlink():
        path.unlink()
    else: 
        shutil.rmtree(str(path))
    
def rm(path):
    if path.is_dir():
        rm_dir(path)
    else:
        path.unlink()
        

def cp(src, tgt):
    parent_dir = tgt.parent
    if not parent_dir.is_dir():
        parent_dir.mkdir(parents=True)
    if src.is_dir():
        shutil.copytree(str(src), str(tgt), symlinks=True)
    else:
        shutil.copy(str(src), str(tgt))

        
def cp_with_common_root(root, tgt_root, path):
    cp(path, tgt_root / path.relative_to(root))
    

def pathlib_glob_for_pattern(pattern):
    r"""Generator for glob matching a string path pattern
    Splits the provided ``pattern`` into a root path for pathlib and a
    subsequent glob pattern to be applied.
    Parameters
    ----------
    pattern : `str`
        Path including glob patterns. If no glob patterns are present and the
        pattern is a dir, a '**/*' pattern will be automatically added.
    sort : `bool`, optional
        If True, the returned paths will be sorted. If False, no guarantees are
        made about the ordering of the results.
    Yields
    ------
    Path : A path to a file matching the provided pattern.
    Raises
    ------
    ValueError
        If the pattern doesn't contain a '*' wildcard and is not a directory
    """
    pattern = norm_path(pattern)
    
    gsplit = str(pattern).split('*', 1)
    
    if len(gsplit) == 1:
        # no glob provided. Is the provided pattern an item?
        if pattern.exists():
            return [pattern]
        else:
            return []
    
    # There is a glob!
    
    preglob = gsplit[0]
    pattern = '*' + gsplit[1]
    
    if not os.path.isdir(preglob):
        # the glob pattern is in the middle of a path segment. pair back
        # to the nearest dir and add the reminder to the pattern
        preglob, pattern_prefix = os.path.split(preglob)
        pattern = pattern_prefix + pattern
    
    p = Path(preglob)
    return p.glob(str(pattern))


def operate_on_glob(f, root, pattern):
    root = Path(root)
    print(root / pattern)
    for path in pathlib_glob_for_pattern(root / pattern):
        rpath = path.relative_to(root)
        s = str(rpath) + '/' if path.is_dir() else str(rpath)
        print(' - {}'.format(s))
        f(path)
        
        
def whitelist(root, tgt_root, patterns, overwrite=False, rm_dir=True):
    print('>>> WHITELIST')
    root = norm_path(root)
    tgt_root = norm_path(tgt_root)
    if tgt_root.exists():
        if rm_dir:
            if overwrite and rm_dir:
                rm(tgt_root)
            else:
                raise ValueError('{} exists - pass overwrite if you wish to delete'.format(tgt_root))
    copy_f = partial(cp_with_common_root, root, tgt_root)
    for pattern in patterns:
        operate_on_glob(copy_f, root, pattern)
        
        
def blacklist(root, patterns):
    print('>>> BLACKLIST')
    root = norm_path(root)
    for pattern in patterns:
        operate_on_glob(rm, root, pattern)
        
        
def copy_dir_with_wb_lists(src, tgt, w_list, b_list, overwrite=False):
    whitelist(src, tgt, w_list, overwrite=overwrite)
    blacklist(tgt, b_list)
    
    
def extract_from_dir_with_wb_lists(src, tgt, w_list, b_list, overwrite=False):
    # Copy the content from the whitelist out to the tgt...
    whitelist(src, tgt, w_list, overwrite=overwrite)

    # ...and delete all the content we copied.
    blacklist(src, w_list)

    # Now copy *back* any content we didn't want to have
    # in the second set. Note the use of the rm_dir=False
    # option to allow us to copy to a 'dirty' dir. This
    # is fine as we know we are restoring files we just
    # removed.
    whitelist(tgt, src, b_list, rm_dir=False)

    # and finally blacklist the destination.
    blacklist(tgt, b_list)
    
    
def _load_a_list(path):
    patterns = [p.strip() for p in path.read_text().split('\n')]
    return [p for p in patterns if p != '' and not p.startswith('#')]

def load_list(path):
    list = _load_a_list(path)
    platform_specific_list_path = Path(str(path) + '.' + PLATFORM_STR)
    if platform_specific_list_path.is_file():
        print('{} exists - loading and adding'.format(platform_specific_list_path))
        list = list + _load_a_list(platform_specific_list_path)
    return list


def load_wb_lists(path):
    path = Path(path)
    return (load_list(path.with_suffix('.whitelist')),
            load_list(path.with_suffix('.blacklist')))


def reset_dir(path):
    if path.exists():
        rm(path)
    path.mkdir()
    

def pack(src, bundle_path):
    with tarfile.open(str(bundle_path), "w:xz") as tar:
        tar.add(str(src), arcname='.')

        
def track_progress(members):
    for member in members:
        print(member)
        # this will be the current file being extracted
        yield member

        
def unpack(bundle_path, output_path, members=None, cleanup=False):
    with tarfile.open(str(bundle_path), "r:xz") as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, str(output_path), members=track_progress(tar))
    if cleanup:
        rm(bundle_path)


def unpack_and_time(bundle_path, output_path):
    times = {}
    total_time = 0
    
    def timer(members):
        nonlocal total_time
        for member in members:
            t1 = time.time()
            yield member
            delta = time.time() - t1
            total_time += delta
            times[member.path] = delta 
    
    with tarfile.open(str(bundle_path), "r:xz") as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, str(output_path), members=timer(tar))
    
    return { p: time / total_time for p, time in times.items() }

def unpack_with_progress(bundle_path, output_path, report_every=0.1, cleanup=False):
    
    member_times = load_timings(bundle_path)
    bar_length = 50
    def report_progress(members):
        
        progress = 0
        start = time.time()
        last_reported = 0
        
        for member in members:
            yield member
            progress += member_times[member.path]
            time_spent = time.time() - start
            if progress != 0:
                total_time = time_spent / progress
            else:
                # By default assume 1 minute to unpack
                total_time = 60
            time_remaining = total_time - time_spent
            if time_spent - last_reported > report_every:
                last_reported = time_spent
                progress_bar = progress_bar_str(progress, bar_length=bar_length)
                print_dynamic('  {} - {:.0f} seconds to go'.format(progress_bar, time_remaining))
            
    with tarfile.open(str(bundle_path), "r:xz") as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, str(output_path), members=report_progress(tar))

    print_dynamic('  {} - finished.      '.format(
        progress_bar_str(1, bar_length=bar_length)))
    print('')
    if cleanup:
        rm(bundle_path)
        rm(timings_path_for_bundle(bundle_path)) 
    
    
def timings_path_for_bundle(bundle_path):
    return bundle_path.with_name('timings.pkl.xz')
    
    
def dump_timings(timings, bundle_path):
    with lzma.open(str(timings_path_for_bundle(bundle_path)), 'wb') as f:
        pickle.dump(timings, f, protocol=4)
        
        
def load_timings(bundle_path):
    with lzma.open(str(timings_path_for_bundle(bundle_path)), 'rb') as f:
        timings = pickle.load(f)
        
    return timings

PROJECT_DIR = norm_path('.')
BUILD_DIR = PROJECT_DIR / 'build'
PLAYGROUND_NAME = 'menpo_playground'
FINAL_ARCHIVE_PATH = PROJECT_DIR / PLAYGROUND_NAME

FINAL_TOOLBOX_PATH = BUILD_DIR / PLAYGROUND_NAME
FINAL_SRC_DIR = FINAL_TOOLBOX_PATH / 'src'

MINICONDA_PATH = BUILD_DIR / 'miniconda'
MINICONDA_BIN_PATH = MINICONDA_PATH / ('Scripts' if IS_WINDOWS else 'bin')
CONDA_PATH_STR = str(MINICONDA_BIN_PATH / 'conda')
PYTHON_PATH_STR =  str(MINICONDA_PATH / 'python') if IS_WINDOWS else str(MINICONDA_BIN_PATH / 'python')

def install_deps():
    # Ideally we would like to do this to keep the download small - but this is
    # not possible as dlib currently is compiled into MKL.
    # if not IS_WINDOWS:
    #     # Don't install MKL unless on windows (where we have no choice)
    #     subprocess.call([CONDA_PATH_STR, 'install', '-y', 'nomkl'])

    subprocess.call([CONDA_PATH_STR, 'install', '-q', '-y', '-c', 'menpo', 'menpoproject'])
    
    if not IS_WINDOWS:
        # Add workerbee if not on Windows for running parallel experiments:
        #  - https://github.com/menpo/workerbee
        # and for now add scikit-sparse manually
        subprocess.call([CONDA_PATH_STR, 'install', '-y', '-c', 'menpo', 'workerbee', 'scikit-sparse'])
        
    
    # subprocess.call([CONDA_PATH_STR, 'remove',  '-q', '-y', '--force',  'pandas', 'qt', 'pyqt'])
   
    # now call our warmup script to do any pre-processing (e.g. model download)
    subprocess.call([PYTHON_PATH_STR, 'warmup.py'])

def install_notebooks():
    print('  - Downloading and installing notebooks...')
    download_file('https://github.com/menpo/menpo-notebooks/archive/master.zip', norm_path('./build/notebooks.zip'))
    with ZipFile('./build/notebooks.zip') as zip:
        zip.extractall(path='./build/notebooks')
    cp(Path('./build/notebooks/menpo-notebooks-master/'), FINAL_TOOLBOX_PATH / 'notebooks')


def install_root_content():
    whitelist(Path('root'), FINAL_TOOLBOX_PATH, ['*'], rm_dir=False)
    whitelist(Path(PLATFORM_STR), FINAL_TOOLBOX_PATH, ['*'], rm_dir=False)


def deps_notebooks_root_content():
    # Make sure our destination is clean.
    print('  - clearing final build dir...')
    reset_dir(FINAL_TOOLBOX_PATH)

    print('  - installing deps...')
    install_deps()
    print('  - installing notebooks...')
    install_notebooks()
    print('  - installing root content...')
    install_root_content()


def build():
    print('=========== BUILD ===========')
    print('----- 1. INSTALL CONTENT -----')
    deps_notebooks_root_content()

    # There's a lot of unneeded content in the miniconda dir
    # - to keep things compact, strip it down and save it into
    # the final src dir
    print('----- 2. PRUNE INSTALLATION -----')
    copy_dir_with_wb_lists(MINICONDA_PATH, FINAL_SRC_DIR,
                           *load_wb_lists('white_and_blacklists/extrenuous'), 
                           overwrite=True)

    # and finally save out the zip
    print('----- 3. EXPORT ARCHIVE -----')
    if IS_WINDOWS:
        print('  - On Windows: building {}.zip...'.format(PLAYGROUND_NAME))
        print('    (Are you sure you want to build and not bundle on Windows? This will be a large .zip...)')
        with tmp_chdir(BUILD_DIR):
            shutil.make_archive(str(FINAL_ARCHIVE_PATH), 'zip', 
                                root_dir='./', base_dir=PLAYGROUND_NAME)
    else:
        print('  - On Mac/Linux: building {}.tar.xz...'.format(PLAYGROUND_NAME))
        # OS X Yosemite+ and Ubuntu? supports tar.xz out of the box.
        with tmp_chdir(BUILD_DIR):
            shutil.make_archive(str(FINAL_ARCHIVE_PATH), 'xztar', 
                                root_dir='./', base_dir=PLAYGROUND_NAME)


def bundle():
    print('=========== BUNDLE ===========')
    print('----- 1. INSTALL CONTENT -----')
    deps_notebooks_root_content()

    # There's a lot of unneeded content in the miniconda dir
    # - to keep things compact, strip it down and save it into
    # our temp dir.
    print('----- 2. PRUNE INSTALLATION -----')
    copy_dir_with_wb_lists(MINICONDA_PATH, FINAL_SRC_DIR,
                           *load_wb_lists('white_and_blacklists/extrenuous'), 
                           overwrite=True)

    # We need a few dirs for bundling - make sure it's all clean.
    bundle_toolbox_path = norm_path('./build/bundletoolbox')
    timing_toolbox_path = norm_path('./build/tartime')
    
    print('  - cleaning temp dirs...')
    reset_dir(bundle_toolbox_path)
    reset_dir(timing_toolbox_path)

    bundle_src_dir = bundle_toolbox_path / 'src'
    bundle_path = bundle_src_dir / 'bundle.tar.xz'

    # We will compress the majority of this with LZMA2 - but we
    # just keep the base python install out to be able to unpack
    # after download.
    print('----- 3. EXTRACT BOOTSTRAP INSTALL -----')
    extract_from_dir_with_wb_lists(FINAL_SRC_DIR, bundle_src_dir, 
                                   *load_wb_lists('white_and_blacklists/bootstrap'), 
                                   overwrite=True)

    # Compress down the rest of the toolbox with LZMA2.
    print('----- 4. LMZA COMPRESS FULL INSTALL -----')
    print('  - Building src/bundle.tar.xz...')
    pack(FINAL_TOOLBOX_PATH, bundle_path)

    # Unpack the archive and time it so we can offer a progress
    # indication on install as to how long it will be
    print('  - Timing unpack of src/bundle.tar.xz...')
    timings = unpack_and_time(bundle_path, timing_toolbox_path)

    # and save the timings down.
    print('  - Saving timings to src/timings.pkl.xz...')
    dump_timings(timings, bundle_path)

    # save this installer in so we can unpack...
    print('  - Adding src/{}.py and get_started to unpack...'.format(PLAYGROUND_NAME))
    cp(norm_path(__file__), bundle_src_dir / '{}.py'.format(PLAYGROUND_NAME))
    bundle_content_dir = norm_path(__file__).parent / 'bundle'
    if IS_WINDOWS:
        cp(bundle_content_dir / 'get_started.cmd', bundle_toolbox_path / 'Get Started.cmd')
    else:
        cp(bundle_content_dir / 'get_started.sh', bundle_toolbox_path / 'get_started')

    cp(bundle_content_dir / 'readme_{}.md'.format(PLATFORM_STR), 
       bundle_toolbox_path / 'Get Started readme.md')

    # and finally save out the zip
    print('  - Building {}.zip...'.format(PLAYGROUND_NAME))
    shutil.make_archive(PLAYGROUND_NAME, 'zip', str(bundle_toolbox_path), '.')


UNBUNDLE_START_STRING = '''

                         Welcome to Menpo Playground!
                         ----------------------------

  We just need to do some housekeeping and then you will be good to go. 
 
  Nothing outside this folder will be touched.
'''

UNBUNDLE_FINISH_STRING = '''
  All done!

  Check out README.md to see how to use this Menpo Playground.

  Have fun!

'''


def install():
    print(UNBUNDLE_START_STRING)
    # install is only ever invoked from src dir - so we can trivialy locate the bundle.
    file_path = Path(__file__)
    src_dir = file_path.parent
    unpack_with_progress(src_dir / 'bundle.tar.xz', src_dir.parent, cleanup=True)
    # Finally, remove ourselves :)
    file_path.unlink()
    print(UNBUNDLE_FINISH_STRING)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        cmd = sys.argv[1]
        if cmd == 'build':
            build()
        if cmd == 'bundle':
            bundle()
        elif cmd == 'install':
            install()
