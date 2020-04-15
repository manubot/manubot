from ..curie import get_namespaces, get_prefixes


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
        namespace["prefix"]
        # check whether compiled pattern matches example identifier
        # do not fail when no match, since this is an upstream issue
        # https://github.com/identifiers-org/identifiers-org.github.io/issues/99
        match = namespace["pattern"].fullmatch(namespace["sampleId"])
        if not match:
            print(
                f"{namespace['prefix']} regex "
                f"{namespace['pattern'].pattern} "
                f"does not match {namespace['sampleId']}"
            )


def test_get_prefixes():
    prefixes = get_prefixes()
    assert isinstance(prefixes, set)
    assert "doid" in prefixes
