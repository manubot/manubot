import pytest


from ..curie import curie_to_url, get_namespaces, get_prefixes


def test_get_namespaces():
    """
    ```shell
    # show regexes that do not match the sampleId
    pytest --capture=no --verbose manubot/cite/tests/test_curie.py
    ```
    """
    namespaces = get_namespaces(compile_patterns=True)
    assert isinstance(namespaces, list)
    for namespace in namespaces:
        # ensure prefix field exists
        assert namespace["prefix"]
        # check whether compiled pattern matches example identifier
        # do not fail when no match, since this is an upstream issue
        # https://github.com/identifiers-org/identifiers-org.github.io/issues/99
        compact_id = namespace["sampleId"]
        if namespace["namespaceEmbeddedInLui"]:
            compact_id = f"{namespace['prefix']}:{compact_id}"
        match = namespace["pattern"].fullmatch(namespace["sampleId"])
        if not match:
            print(
                f"{namespace['prefix']} regex "
                f"{namespace['pattern'].pattern} "
                f"does not match {compact_id}"
            )


def test_get_prefixes():
    prefixes = get_prefixes()
    assert isinstance(prefixes, set)
    assert "doid" in prefixes


@pytest.mark.parametrize(
    "curie, expected",
    [
        ("doi:10.1038/nbt1156", "https://identifiers.org/doi:10.1038/nbt1156"),
        ("DOI:10.1038/nbt1156", "https://identifiers.org/doi:10.1038/nbt1156"),
        ("arXiv:0807.4956v1", "https://identifiers.org/arxiv:0807.4956v1"),
        ("taxonomy:9606", "https://identifiers.org/taxonomy:9606"),
        ("CHEBI:36927", "https://identifiers.org/CHEBI:36927"),
        ("DOID:11337", "https://identifiers.org/DOID:11337"),
        (
            "clinicaltrials:NCT00222573",
            "https://identifiers.org/clinicaltrials:NCT00222573",
        ),
        # https://github.com/identifiers-org/identifiers-org.github.io/issues/99#issuecomment-614690283
        pytest.param(
            "GRO:0007133",
            "https://identifiers.org/GRO:0007133",
            marks=[pytest.mark.xfail],
        ),
    ],
)
def test_curie_to_url(curie, expected):
    url = curie_to_url(curie)
    assert url == expected
