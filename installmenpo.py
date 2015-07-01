#!/usr/bin/env python
import subprocess
import os
import os.path as p
import platform as stdplatform
import sys
import uuid


def detect_arch():
    arch = stdplatform.architecture()[0]
    # need to be a little more sneaky to check the platform on Windows:
    # http://stackoverflow.com/questions/2208828/detect-64bit-os-windows-in-python
    if host_platform == 'Windows':
        if 'APPVEYOR' in os.environ:
            av_platform = os.environ['PLATFORM']
            if av_platform == 'x86':
                arch = '32bit'
            elif av_platform == 'x64':
                arch = '64bit'
            else:
                print('Was unable to interpret the platform "{}"'.format())
    return arch

host_platform = stdplatform.system()
host_arch = detect_arch()
install_path = './atomicmenpo'
abs_install_path = p.abspath(install_path)

# define our commands
if host_platform == 'Windows':
    script_dir_name = 'Scripts'
    temp_installer_path = p.join(abs_install_path, '{}.exe'.format(uuid.uuid4()))
else:
    script_dir_name = 'bin'
    temp_installer_path = p.join(abs_install_path, '{}.sh'.format(uuid.uuid4()))

miniconda_script_dir = lambda mc: p.join(mc, script_dir_name)

conda = lambda mc: p.join(miniconda_script_dir(mc), 'conda')
binstar = lambda mc: p.join(miniconda_script_dir(mc), 'binstar')
python = lambda mc: p.join(miniconda_script_dir(mc), 'python')


def url_for_platform_version(platform, py_version, arch):
    version = 'latest'
    base_url = 'http://repo.continuum.io/miniconda/Miniconda'
    platform_str = {'Linux': 'Linux',
                    'Darwin': 'MacOSX',
                    'Windows': 'Windows'}
    arch_str = {'64bit': 'x86_64',
                '32bit': 'x86'}
    ext = {'Linux': '.sh',
           'Darwin': '.sh',
           'Windows': '.exe'}

    if py_version == '3.4':
        base_url = base_url + '3'
    elif py_version != '2.7':
        raise ValueError("Python version must be '2.7 or '3.4'")
    return '-'.join([base_url, version,
                     platform_str[platform],
                     arch_str[arch]]) + ext[platform]



def execute(cmd, verbose=False, env_additions=None):
    r""" Runs a command, printing the command and it's output to screen.
    """
    env_for_p = os.environ.copy()
    if env_additions is not None:
        env_for_p.update(env_additions)
    if verbose:
        print('> {}'.format(' '.join(cmd)))
        if env_additions is not None:
            print('Additional environment variables: '
                  '{}'.format(', '.join(['{}={}'.format(k, v)
                                         for k, v in env_additions.items()])))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env_for_p)
    sentinal = ''
    if sys.version_info.major == 3:
        sentinal = b''
    for line in iter(proc.stdout.readline, sentinal):
        if verbose:
            if sys.version_info.major == 3:
                # convert bytes to string
                line = line.decode("utf-8")
            sys.stdout.write(line)
            sys.stdout.flush()
    output = proc.communicate()[0]
    if proc.returncode == 0:
        return
    else:
        e = subprocess.CalledProcessError(proc.returncode, cmd, output=output)
        print(' -> {}'.format(e.output))
        raise e


def execute_sequence(*cmds, **kwargs):
    r""" Execute a sequence of commands. If any fails, display an error.
    """
    verbose = kwargs.get('verbose', False)
    for cmd in cmds:
        execute(cmd, verbose)


def download_file(url, path_to_download):
    import urllib2
    f = urllib2.urlopen(url)
    with open(path_to_download, "wb") as fp:
        fp.write(f.read())
    fp.close()


# CONDACI CONVENIENCE FUNCTIONS

def acquire_miniconda(url, path_to_download):
    print('1. Downloading miniconda')
    download_file(url, path_to_download)


def install_miniconda(path_to_installer, path_to_install):
    print('2. Installing miniconda')
    if host_platform == 'Windows':
        execute([path_to_installer, '/S', '/D={}'.format(path_to_install)])
    else:
        execute(['chmod', '+x', path_to_installer])
        execute([path_to_installer, '-b', '-p', path_to_install])


def setup_miniconda(python_version, installation_path):
    url = url_for_platform_version(host_platform, python_version, host_arch)
    acquire_miniconda(url, temp_installer_path)
    install_miniconda(temp_installer_path, installation_path)
    # delete the installer now we are done
    os.unlink(temp_installer_path)
    conda_cmd = conda(installation_path)
    print("3. Installing menpo and it's dependencies (could take some time)")
    cmds = [[conda_cmd, 'update', '-q', '--yes', 'conda'],
            [conda_cmd, 'install', '-c', 'menpo', '-q', '--yes', 
                        'menpo', 'menpodetect', 'menpofit', 'menpo3d']]
    execute_sequence(*cmds)
    print("\nInstallation finished. See ./atomicmenpo/README.md for next steps.\n")
    print("To uninstall, simply delete the ./atomicmenpo folder.\n")


def resolve_mc(mc):
    if mc is not None:
        return mc
    else:
        return default_miniconda_dir


python = p.join(abs_install_path, 'miniconda', 'bin', 'python')


def version_of_package(package):
    return execute([python, '-c', 'import menpo; print(menpo.__version__)'])


if __name__ == "__main__":
    from argparse import ArgumentParser
    pa = ArgumentParser(
        description=r"""
        Installs Menpo next to this script in a folder called 'menpo'
        """)
    print('')
    print(' ATOMICMENPO - A standalone installation of the Menpo Project')
    print(' ------------------------------------------------------------')
    print('')
    print('This tool will install a self-contained version of menpo to {}'.format(install_path, abs_install_path))
    print('')
    print('Installation will require about 2.5GB of free space, and will')
    print('take approximately 10 minutes on a fast connnection.')
    print('')
    raw_input('To continue, press enter. To abort, press Ctrl-C.')
    print('')
    if p.isdir(abs_install_path):
        print('Warning: {} already exists - installation aborted.'.format(install_path))
        print('If you want to overite this install, delete the old'.format(install_path))
        print('folder and rerun this installer.\n'.format(install_path))
    else:
        os.mkdir(install_path)
        setup_miniconda('2.7', p.join(abs_install_path, 'miniconda'))

