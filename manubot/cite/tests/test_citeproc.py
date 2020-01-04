import json
import pathlib

import pytest

from manubot.cite.citeproc import remove_jsonschema_errors

directory = pathlib.Path(__file__).parent
csl_instances = [x.name for x in directory.glob("csl-json/*-csl")]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def test_json_is_readable_on_windows_in_different_oem_encoding():
    name = "crossref-deep-review-csl"
    path = directory / "csl-json" / name / "raw.json"
    content = path.read_text(encoding="utf-8-sig")
    assert content
    json1 = load_json(path)
    assert json1


@pytest.mark.parametrize("name", csl_instances)
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
    data_dir = directory / "csl-json" / name
    raw = load_json(data_dir / "raw.json")
    expected = load_json(data_dir / "pruned.json")
    pruned = remove_jsonschema_errors(raw)
    assert pruned == expected
