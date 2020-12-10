"""
Tools for manuscript metadata processing including thumbnail detection and processing.
"""
import functools
import logging
import pathlib
import subprocess
from typing import Optional
from urllib.parse import urljoin


def get_header_includes(variables: dict) -> str:
    """
    Render `header-includes-template.html` using information from `variables`.
    """
    from .util import template_with_jinja2

    path = pathlib.Path(__file__).parent.joinpath("header-includes-template.html")
    try:
        template = path.read_text(encoding="utf-8-sig")
        return template_with_jinja2(template, variables)
    except Exception:
        logging.exception(f"Error generating header-includes.")
        return ""


def get_thumbnail_url(thumbnail=None):
    """
    Starting with a user-specified `thumbnail` as either a path, URL, or None,
    return an absolute URL pointing to the thumbnail image. If the provided `thumbnail`
    is a URL, return this URL unmodified. If `thumbnail` is None, search for `thumbnail.png`
    within the git repository from which this function is executed. If `thumbnail`
    is a local path, the path should be relative to root directory of the git repository
    it is located in. If a local path is provided or detected,
    it is converted to a GitHub raw URL.
    """
    from manubot.util import is_http_url

    if not thumbnail:
        message = "get_thumbnail_url: thumbnail location not explicitly provided. "
        thumbnail = _find_thumbnail_path()
        message += (
            f"Thumbnail detected at {thumbnail!r}"
            if thumbnail
            else "No local thumbnail detected"
        )
        logging.debug(message)
    elif is_http_url(thumbnail):
        logging.debug("provided thumbnail is a URL. Pass it through.")
        return thumbnail
    return _thumbnail_path_to_url(thumbnail)


def _find_thumbnail_path():
    """
    If this this function is executed with a working directory that is inside a git repository,
    return the path to a `thumbnail.png` file located anywhere in that repository. Otherwise,
    return `None`.
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
    Convert a local thumbnail path (string) to an absolute URL using the GitHub
    repository location detected using `get_continuous_integration_parameters`.
    """
    if not path:
        return None
    from .ci import get_continuous_integration_parameters

    info = get_continuous_integration_parameters()
    try:
        url = f"https://github.com/{info['repo_slug']}/raw/{info['triggering_commit']}/{path}"
    except (TypeError, KeyError):
        return None
    return url


@functools.lru_cache()
def git_repository_root():
    """
    Return the path to repository root directory or `None` if indeterminate.
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


def get_manuscript_urls(html_url: Optional[str] = None) -> dict:
    """
    Return a dictionary with URLs for a manuscript.
    An example for a manuscript where all URLs get set, inferred from continuous integration environment variables, is:
    ```python
    {
        "html_url": "https://manubot.github.io/rootstock/",
        "pdf_url": "https://manubot.github.io/rootstock/manuscript.pdf",
        "html_url_versioned": "https://manubot.github.io/rootstock/v/7cf9071212ce33116ad09cf2237a370b180a3c35/",
        "pdf_url_versioned": "https://manubot.github.io/rootstock/v/7cf9071212ce33116ad09cf2237a370b180a3c35/manuscript.pdf",
    }
    ```

    Provide `html_url` to set a custom domain.
    If `html_url="https://git.dhimmel.com/bitcoin-whitepaper/"`,
    the return dictionary will be like:
    ```python
    {
        "html_url": "https://git.dhimmel.com/bitcoin-whitepaper/",
        "pdf_url": "https://git.dhimmel.com/bitcoin-whitepaper/manuscript.pdf",
        "html_url_versioned": "https://git.dhimmel.com/bitcoin-whitepaper/v/cb1f2c12eec8b56db9ef5f641ec805e2d449d319/",
        "pdf_url_versioned": "https://git.dhimmel.com/bitcoin-whitepaper/v/cb1f2c12eec8b56db9ef5f641ec805e2d449d319/manuscript.pdf",
    }
    ```
    Note the trailing `/` in `html_url`, which is required for proper functioning.
    """
    import requests

    from .ci import get_continuous_integration_parameters

    urls = dict()
    ci_params = get_continuous_integration_parameters()
    if html_url is None:
        if not ci_params:
            return urls
        html_url = "https://{repo_owner}.github.io/{repo_name}/".format(**ci_params)
    urls["html_url"] = html_url
    urls["pdf_url"] = urljoin(html_url, "manuscript.pdf")
    if not ci_params:
        return urls
    urls["html_url_versioned"] = urljoin(html_url, "v/{commit}/".format(**ci_params))
    urls["pdf_url_versioned"] = urljoin(urls["html_url_versioned"], "manuscript.pdf")
    response = requests.head(html_url, allow_redirects=True)
    if not response.ok:
        logging.warning(
            "html_url is not web accessible. "
            f"{html_url} returned status code {response.status_code}. "
            "Ignore this warning if the manuscript has not yet been deployed for the first time. "
        )
    if response.history:
        logging.info(
            "html_url includes redirects. In order of oldest to most recent:\n"
            + "\n".join(x.url for x in response.history + [response])
        )
    return urls


def get_software_versions() -> dict:
    """
    Return a dictionary of software versions for softwares components:

    - manubot_version: the semantic version number of the manubot python package.
    - rootstock_commit: the version of the rootstock repository, as a commit hash,
      included in the manuscript repository.

    Values whose detection fails are set to None.
    """
    from manubot import __version__ as manubot_version

    return {
        "manubot_version": manubot_version,
        "rootstock_commit": get_rootstock_commit(),
    }


def get_rootstock_commit() -> Optional[str]:
    """
    Return the most recent commit in common between the git repository
    this function is run within (usually a Manubot manuscript repository)
    and the `main` branch of the `rootstock` remote.

    WARNING: This function may modify the git repository its executed within:

    - if the repository has not set the `roostock` remote, it is set to
      point to the default Rootstock repository of <https://github.com/manubot/rootstock>.
    - fetches the latest commits in the `main` branch of the `rootstock` remote
    """
    from manubot.util import shlex_join

    # add rootstock remote if remote is not already set
    rootstock_remote = "https://github.com/manubot/rootstock.git"
    args = ["git", "remote", "add", "rootstock", rootstock_remote]
    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        logging.info(
            "get_rootstock_commit added a `rootstock` remote to the git repository."
        )
    # find most recent common ancestor commit
    try:
        args = ["git", "fetch", "rootstock", "main"]
        subprocess.check_output(args, stderr=subprocess.PIPE, universal_newlines=True)
        args = ["git", "merge-base", "HEAD", "rootstock/main"]
        output = subprocess.check_output(
            args, stderr=subprocess.PIPE, universal_newlines=True
        )
    except subprocess.CalledProcessError as error:
        logging.warning(
            f"get_rootstock_commit: {shlex_join(error.cmd)!r} returned exit code {error.returncode} "
            f"with the following stdout:\n{error.stdout}\n"
            f"And the following stderr:\n{error.stderr}"
        )
        return None
    rootstock_commit = output.strip()
    return rootstock_commit
