"""
Tools for manuscript thumbnial detection and processing.
"""
import functools
import pathlib
import subprocess
from urllib.parse import urlparse

# Valid schemes for URL detection
url_schemes = {"http", "https"}


def get_thumbnail_url(thumbnail=None):
    """
    Starting with a user-specified `thumbnail` as either a path, URL, or None,
    return a web-accessible URL with thumbnail. If provided `thumbnail` is a URL,
    return the URL unmodified. If `thumbnail` is None, search for `thumbnail.png`
    within the git repository from which this function is executed. If a local path
    is provided or detected, convert that path to a GitHub raw URL.
    """
    if not thumbnail:
        # thumbnail not provided, so find local path if exists
        thumbnail = _find_thumbnail_path()
    elif urlparse(thumbnail).scheme in url_schemes:
        # provided thumbnail is a URL. Pass it through.
        return thumbnail
    return _thumbnail_path_to_url(thumbnail)


def _find_thumbnail_path():
    """
    If this this function is executed with a working directory that is inside a git repository,
    return the path to a `thumbnail.png` file located anywhere in that repository.
    """
    directory = git_repository_root()
    if not directory:
        return None
    paths = directory.glob("**/thumbnail.png")
    paths = [path.relative_to(directory) for path in paths]
    paths = sorted(paths, key=lambda x: (len(x.parents), x))
    if not paths:
        return None
    return paths[0].as_posix()


def _thumbnail_path_to_url(path):
    """
    Convert a local thumbnail path (string) to a web-accessible URL using the GitHub
    repository location detected using `get_continuous_integration_parameters`.
    """
    if not path:
        return None
    from .ci import get_continuous_integration_parameters

    info = get_continuous_integration_parameters()
    try:
        url = f"https://github.com/{info['repo_slug']}/raw/{info['triggering_commit']}/{path}"
    except KeyError:
        return None
    return url


@functools.lru_cache()
def git_repository_root():
    """
    Return the path to repository root directory or None if indeterminate.
    """
    for cmd in (
        ["git", "rev-parse", "--show-superproject-working-tree"],
        ["git", "rev-parse", "--show-toplevel"],
    ):
        try:
            path = subprocess.check_output(cmd, universal_newlines=True).rstrip("\r\n")
            if path:
                return pathlib.Path(path)
        except (subprocess.CalledProcessError, OSError):
            pass
    return None
