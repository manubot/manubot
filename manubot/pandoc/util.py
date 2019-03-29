import logging
import shutil
import subprocess
import functools


@functools.lru_cache()
def get_pandoc_info():
    """
    Return path and version information for the system's pandoc and
    pandoc-citeproc commands. When Pandoc is installed,
    the output will look like:
    {
        'pandoc': True,
        'pandoc path': '/PATH_TO_EXECUTABLES/pandoc',
        'pandoc version': (2, 5),
        'pandoc-citeproc': True,
        'pandoc-citeproc path': '/PATH_TO_EXECUTABLES/pandoc-citeproc',
        'pandoc-citeproc version': (0, 15),
    }
    If the executables are missing, the output will be like:
    {
        'pandoc': False,
        'pandoc-citeproc': False,
    }
    """
    stats = dict()
    for command in 'pandoc', 'pandoc-citeproc':
        path = shutil.which(command)
        stats[command] = bool(path)
        if not path:
            continue
        version = subprocess.check_output(
            args=[command, '--version'],
            universal_newlines=True,
        )
        logging.debug(version)
        version, *discard = version.splitlines()
        discard, version = version.strip().split()
        from packaging.version import parse as parse_version
        version = parse_version(version).release
        stats[f'{command} version'] = version
        stats[f'{command} path'] = path
    logging.info('\n'.join(f'{k}: {v}' for k, v in stats.items()))
    return stats
