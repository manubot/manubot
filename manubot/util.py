import importlib
import json
import logging
import platform
import shlex
import sys

# Email address that forwards to Manubot maintainers
contact_email = "contact@manubot.org"


def import_function(name):
    """
    Import a function in a module specified by name. For example, if name were
    'manubot.cite.cite_command.cli_cite', the cli_cite function would be
    returned as an object. See https://stackoverflow.com/a/8790232/4651668.
    """
    module_name, function_name = name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def get_manubot_user_agent():
    """
    Return a User-Agent string for web request headers to help services
    identify requests as coming from Manubot.
    """
    try:
        from manubot import __version__ as manubot_version
    except ImportError:
        manubot_version = ""
    return (
        f"manubot/{manubot_version} "
        f"({platform.system()}; Python/{sys.version_info.major}.{sys.version_info.minor}) "
        f"<{contact_email}>"
    )


def shlex_join(split_command):
    """
    Backport shlex.join for Python < 3.8.
    Also cast all args to str to increase versatility.
    https://github.com/python/cpython/pull/7605
    https://bugs.python.org/issue22454
    """
    return " ".join(shlex.quote(str(arg)) for arg in split_command)


"""Valid schemes for HTTP URL detection"""
_http_url_schemes = {"http", "https"}


def is_http_url(string: str) -> bool:
    """
    Return whether `string` is an HTTP(s) Uniform Resource Locator (URL).
    """
    from urllib.parse import urlparse

    parsed_url = urlparse(string)
    return parsed_url.scheme in _http_url_schemes


def read_serialized_data(path: str):
    """
    Read seralized data from a local file path or web-address.
    If file format extension is not detected in path, assumes JSON.
    If a URL does not contain the appropriate suffix, one workaround
    is to hack the fragment like https://example.org#/variables.toml
    """
    import os
    import pathlib
    import requests

    path_str = os.fspath(path)
    path_lib = pathlib.Path(path)
    supported_suffixes = {".json", ".yaml", ".yml", ".toml"}
    suffixes = set(path_lib.suffixes)
    if is_http_url(path_str):
        response = requests.get(path_str)
        if not suffixes & supported_suffixes:
            # if URL has no supported suffixes, evaluate suffixes of final redirect
            suffixes = set(pathlib.Path(response.url).suffixes)
        text = response.text
    else:
        text = path_lib.read_text(encoding="utf-8-sig")
    if {".yaml", ".yml"} & suffixes:
        import yaml

        return yaml.safe_load(text)
    if ".toml" in suffixes:
        import toml

        return toml.loads(text)
    if ".json" not in suffixes:
        logging.info(
            f"read_serialized_data cannot infer serialization format from the extension of {path_str!r}. "
            f"Supported extensions are {', '.join(supported_suffixes)}. "
            "Assuming JSON."
        )
    return json.loads(text)


def read_serialized_dict(path: str) -> dict:
    """
    Read serialized data, confirming that the top-level object is a dictionary.
    Delegates to `read_serialized_data`.
    """
    data = read_serialized_data(path)
    if isinstance(data, dict):
        return data
    raise TypeError(
        f"Expected data encoded by {path!r} to be a dictionary at the top-level. "
        f"Received {data.__class__.__name__!r} instead."
    )
