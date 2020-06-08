from ..handlers import _generate_prefix_to_handler, prefix_to_handler

import pytest


def test_prefix_to_handler():
    """
    If this test fails, copy the output from `print(expected)`
    to use as the value for `handlers.prefix_to_handler`.
    """
    expected = _generate_prefix_to_handler()
    print(expected)
    assert prefix_to_handler == expected


@pytest.mark.parametrize("prefix", ["raw", "tag"])
def test_legacy_prefixes_are_unhandled(prefix):
    """
    For backwards compatability, these prefixes should be unhandled.
    In the past, these prefixes referred to citekeys that were not
    resolvable identifiers by themselves.
    """
    assert prefix not in prefix_to_handler
