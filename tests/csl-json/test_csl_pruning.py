import json
import pathlib

import pytest

from manubot.cite.citeproc import remove_jsonschema_errors

directory = pathlib.Path(__file__).parent
csl_instances = [
    x.name for x in directory.glob('*-csl')
]


@pytest.mark.parametrize('name', csl_instances)
def test_remove_jsonschema_errors(name):
    data_dir = directory / name
    raw = json.loads(data_dir.joinpath('raw.json').read_text())
    expected = json.loads(data_dir.joinpath('pruned.json').read_text())
    pruned = remove_jsonschema_errors(raw)
    assert pruned == expected
