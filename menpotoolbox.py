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
        copy_progress = copy_and_yield(req, fp, length=chunk_size_bytes)

        if verbose:
            # wrap the download object with print progress to log the status
            n_bytes = int(req.headers['content-length'])
            n_items = int(ceil((1.0 * n_bytes) / chunk_size_bytes))
            prefix = 'Downloading {}'.format(bytes_str(n_bytes))
            copy_progress = print_progress(copy_progress, n_items=n_items,
                                           show_count=False, prefix=prefix)

        for _ in copy_progress:
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
    
    
def load_list(path):
    patterns = [p.strip() for p in path.read_text().split('\n')]
    return [p for p in patterns if p != '' and not p.startswith('#')]


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
        tar.extractall(str(output_path), members=track_progress(tar))
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
        tar.extractall(str(output_path), members=timer(tar))
    
    return { p: time / total_time for p, time in times.items() }


def unpack_with_progress(bundle_path, output_path, report_every=1, cleanup=False):
    
    member_times = load_timings(bundle_path)
    
    def report_progress(members):
        
        progress = 0
        start = time.time()
        last_reported = 0
        
        for member in members:
            yield member
            progress += member_times[member.path]
            time_spent = time.time() - start
            total_time = time_spent / progress
            time_remaining = total_time - time_spent
            if time_spent - last_reported > report_every:
                last_reported = time_spent
                print('{:02.0%} - {:.0f} seconds remaining...'.format(progress, time_remaining))
            
    with tarfile.open(str(bundle_path), "r:xz") as tar:
        tar.extractall(str(output_path), members=report_progress(tar))
    
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


FINAL_TOOLBOX_PATH = norm_path('./build/menpotoolbox')
FINAL_SRC_DIR = FINAL_TOOLBOX_PATH / 'src'
FINAL_BUNDLE_PATH = FINAL_SRC_DIR / 'bundle.tar.xz'
MINICONDA_PATH = norm_path('./build/miniconda')


def install_deps():
    subprocess.call(['./build/miniconda/bin/conda', 'install', '-y', 'nomkl'])
    subprocess.call(['./build/miniconda/bin/conda', 'install', '-y', '-c', 'menpo', 'menpoproject'])
    subprocess.call(['./build/miniconda/bin/conda', 'remove', '-y', '--force', '-q', 'opencv3', 'pandas', 'qt', 'pyqt'])


def build():
    print('building menpotoolbox (without bundle)...')
    install_deps()
    # We aren't bundling, so go straight for the src dir

    # There's a lot of unneeded content in the miniconda dir
    # - to keep things compact, strip it down and save it into
    # the final src dir
    copy_dir_with_wb_lists(MINICONDA_PATH, FINAL_SRC_DIR,
                           *load_wb_lists('white_and_blacklists/extrenuous'), 
                           overwrite=True)

    # and finally save out the zip
    print('Saving out bundles..')
    shutil.make_archive('menpotoolbox', 'zip', str(FINAL_TOOLBOX_PATH), '.')
    shutil.make_archive('menpotoolbox', 'xztar', str(FINAL_TOOLBOX_PATH), '.')


def bundle():
    print('building menpotoolbox with self extraction...')
    install_deps()
    tmp_toolbox_path = norm_path('./build/tmp_menpotoolbox')
    timing_toolbox_path = norm_path('./build/tartime')

    reset_dir(FINAL_TOOLBOX_PATH)
    reset_dir(tmp_toolbox_path)
    reset_dir(timing_toolbox_path)

    tmp_src_dir = tmp_toolbox_path / 'src'

    # There's a lot of unneeded content in the miniconda dir
    # - to keep things compact, strip it down and save it into
    # our temp dir.
    copy_dir_with_wb_lists(MINICONDA_PATH, tmp_src_dir,
                           *load_wb_lists('white_and_blacklists/extrenuous'), 
                           overwrite=True)

    # We will compress the majority of this with LZMA2 - but we
    # just keep the base python install out to be able to unpack
    # after download.
    extract_from_dir_with_wb_lists(tmp_src_dir, FINAL_SRC_DIR, 
                                   *load_wb_lists('white_and_blacklists/bootstrap'), 
                                   overwrite=True)


    # Compress down the rest of the toolbox with LZMA2.
    pack(tmp_toolbox_path, FINAL_BUNDLE_PATH)

    # Unpack the archive and time it so we can offer a progress
    # indication on install as to how long it will be
    timings = unpack_and_time(FINAL_BUNDLE_PATH, timing_toolbox_path)

    # and save the timings down.
    dump_timings(timings, FINAL_BUNDLE_PATH)

    # save this installer in so we can unpack...
    cp(norm_path(__file__), FINAL_SRC_DIR / 'menpotoolbox.py')
    cp(norm_path('get_started'), FINAL_TOOLBOX_PATH / 'get_started')

    # and finally save out the zip
    print('Saving out bundle..')
    shutil.make_archive('menpotoolbox_bundle', 'zip', str(FINAL_TOOLBOX_PATH), '.')


def install():
    # install is only ever invoked from the toolkit dir - unpack the bundle right here...
    unpack_with_progress(norm_path('./src/bundle.tar.xz'), norm_path('.'), cleanup=True)
    # Finally, remove ourselves :)
    Path(__file__).unlink()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        cmd = sys.argv[1]
        if cmd == 'build':
            build()
        if cmd == 'bundle':
            bundle()
        elif cmd == 'install':
            install()
