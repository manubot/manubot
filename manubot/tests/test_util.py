import manubot.util

import pytest


def test_shlex_join():
    import pathlib

    args = ["command", "positional arg", "path_arg", pathlib.Path("path")]
    output = manubot.util.shlex_join(args)
    assert output == "command 'positional arg' path_arg path"


raw_repo_url = (
    "https://github.com/manubot/manubot/raw/ebac7abd754015a5ec24a6fff39c35a72d4dffb0/"
)
raw_manuscript_url = f"{raw_repo_url}manubot/process/tests/manuscripts/example/"


def test_read_serialized_data_url_yaml():
    url = raw_manuscript_url + "content/metadata.yaml"
    obj = manubot.util.read_serialized_data(url)
    assert obj["title"] == "Example manuscript for testing"
    obj = manubot.util.read_serialized_dict(url)
    assert obj["title"] == "Example manuscript for testing"


def test_read_serialized_data_url_json():
    url = raw_manuscript_url + "content/manual-references.json"
    obj = manubot.util.read_serialized_data(url)
    assert obj[0]["container-title"] == "Engineuring"
    with pytest.raises(TypeError, match="Received 'list' instead"):
        manubot.util.read_serialized_dict(url)


def test_read_serialized_dict_url_toml():
    url = raw_repo_url + "pyproject.toml"
    obj = manubot.util.read_serialized_dict(url)
    assert "black" in obj["tool"]
