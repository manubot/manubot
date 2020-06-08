import pytest


from ..curie import curie_to_url, get_namespaces, get_prefix_to_namespace


def test_get_namespaces_with_compile_patterns():
    """
    To see printed output when this test passes, run:

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
            compact_id = f"{namespace['curiePrefix']}:{compact_id}"
        match = namespace["compiled_pattern"].fullmatch(compact_id)
        if not match:
            print(
                f"{namespace['prefix']} regex "
                f"{namespace['compiled_pattern'].pattern} "
                f"does not match {compact_id}"
            )
        if namespace["prefix"] != namespace["curiePrefix"].lower():
            print(
                f"{namespace['prefix']} identifiers use "
                f"curiePrefix {namespace['curiePrefix']}"
            )


def test_get_prefix_to_namespace():
    prefix_to_namespace = get_prefix_to_namespace()
    assert isinstance(prefix_to_namespace, dict)
    assert "doid" in prefix_to_namespace
    namespace = prefix_to_namespace["doid"]
    namespace["curiePrefix"] = "DOID"


@pytest.mark.parametrize(
    "curie, expected",
    [
        ("doi:10.1038/nbt1156", "https://identifiers.org/doi:10.1038/nbt1156"),
        ("DOI:10.1038/nbt1156", "https://identifiers.org/doi:10.1038/nbt1156"),
        ("arXiv:0807.4956v1", "https://identifiers.org/arxiv:0807.4956v1"),
        ("taxonomy:9606", "https://identifiers.org/taxonomy:9606"),
        ("CHEBI:36927", "https://identifiers.org/CHEBI:36927"),
        ("ChEBI:36927", "https://identifiers.org/CHEBI:36927"),
        ("DOID:11337", "https://identifiers.org/DOID:11337"),
        ("doid:11337", "https://identifiers.org/DOID:11337"),
        (
            "clinicaltrials:NCT00222573",
            "https://identifiers.org/clinicaltrials:NCT00222573",
        ),
        # https://github.com/identifiers-org/identifiers-org.github.io/issues/99#issuecomment-614690283
        pytest.param(
            "GRO:0007133",
            "https://identifiers.org/GRO:0007133",
            id="gramene.growthstage",
        ),
    ],
)
def test_curie_to_url(curie, expected):
    url = curie_to_url(curie)
    assert url == expected


def test_curie_to_url_bad_curie():
    with pytest.raises(ValueError):
        curie_to_url("this.is.not:a_curie")
