import json
import pathlib

import pytest

from manubot.cite.citeproc import remove_jsonschema_errors

directory = pathlib.Path(__file__).parent
csl_instances = [
    x.name for x in directory.glob('csl-json/*-csl')
]


@pytest.mark.parametrize('name', csl_instances)
def test_remove_jsonschema_errors(name):
    """
    Tests whether CSL pruning of raw.json produces the expected pruned.json.
    The fidelity of the remove_jsonschema_errors implementation is
    difficult to assess theoretically, therefore its performance should be
    evaluated empirically with thorough test coverage. It is recommended that
    all conceivable conformations of invalid CSL that citeproc methods may
    generate be tested.

    To create a new test case, derive pruned.json from raw.json, by manually
    deleting any invalid fields. Do not use `manubot cite` to directly generate
    pruned.json as that also relies on remove_jsonschema_errors for pruning.
    """
    data_dir = directory / 'csl-json' / name
    raw = json.loads(data_dir.joinpath('raw.json').read_text())
    expected = json.loads(data_dir.joinpath('pruned.json').read_text())
    pruned = remove_jsonschema_errors(raw)
    assert pruned == expected
