import importlib
import json
import logging
import os
import pathlib
import platform
import shlex
import shutil
import subprocess
import sys
import typing
from types import ModuleType

if typing.TYPE_CHECKING:
    # allow type annotations of lazy-imported packages
    import yaml

# Email address that forwards to Manubot maintainers
contact_email: str = "contact@manubot.org"


def import_function(name: str):
    """
    Import a function in a module specified by name. For example, if name were
    'manubot.cite.cite_command.cli_cite', the cli_cite function would be
    returned as an object. See https://stackoverflow.com/a/8790232/4651668.
    """
    module_name, function_name = name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def get_manubot_user_agent() -> str:
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


def shlex_join(split_command) -> str:
    """
    Backport shlex.join for Python < 3.8.
    Also cast all args to str to increase versatility.
    https://github.com/python/cpython/pull/7605
    https://bugs.python.org/issue22454
    """
    return " ".join(shlex.quote(str(arg)) for arg in split_command)


"""Valid schemes for HTTP URL detection"""
_http_url_schemes: set = {"http", "https"}


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
    import requests

    path_str = os.fspath(path)
    path_obj = pathlib.Path(path)
    supported_suffixes = {".json", ".yaml", ".yml", ".toml"}
    suffixes = set(path_obj.suffixes)
    if is_http_url(path_str):
        headers = {"User-Agent": get_manubot_user_agent()}
        response = requests.get(path_str, headers=headers)
        if not suffixes & supported_suffixes:
            # if URL has no supported suffixes, evaluate suffixes of final redirect
            suffixes = set(pathlib.Path(response.url).suffixes)
        text = response.text
    else:
        text = path_obj.read_text(encoding="utf-8-sig")
    if {".yaml", ".yml"} & suffixes:
        import yaml

        try:
            return yaml.safe_load(text)
        except yaml.parser.ParserError as error:
            _lint_yaml(path)
            raise error
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


"""
yamllint configuration as per https://yamllint.readthedocs.io/en/stable/configuration.html
"""
_yamllint_config = {
    "extends": "relaxed",
    "rules": {"line-length": "disable", "trailing-spaces": {"level": "warning"}},
}


def _lint_yaml(path):
    if not shutil.which("yamllint"):
        logging.info(f"yamllint executable not found, skipping linting for {path}")
        return
    args = [
        "yamllint",
        "--config-data",
        json.dumps(_yamllint_config, indent=None),
        os.fspath(path),
    ]
    sys.stderr.write(f"yamllint {path}:\n")
    subprocess.run(args, stdout=sys.stderr)


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


def _yaml_str_representer(dumper: "yaml.Dumper", data: str):
    """
    Use YAML literal block style for multiline strings.
    Based on https://stackoverflow.com/a/33300001/4651668
    """
    if len(data.splitlines()) > 1:
        # use literal block style for multiline strings
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def get_configured_yaml() -> ModuleType:
    """
    Return imported YAML library with Manubot configuration.
    The representers are only applied to yaml.dump, not yaml.safe_dump.
    """
    import yaml

    from manubot.cite.csl_item import CSL_Item

    yaml.add_representer(str, _yaml_str_representer)
    # CSL_Item: pyyaml chokes on dict subclass
    # https://github.com/yaml/pyyaml/issues/142
    # https://stackoverflow.com/a/50181505/4651668
    yaml.add_representer(
        CSL_Item,
        lambda dumper, data: dumper.represent_mapping(
            tag="tag:yaml.org,2002:map", mapping=data.items()
        ),
    )
    return yaml
