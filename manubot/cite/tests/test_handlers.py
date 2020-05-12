from ..handlers import _generate_prefix_to_handler, prefix_to_handler


def test_prefix_to_handler():
    """
    If this test fails, copy the output from `print(expected)`
    to use as the value for `handlers.prefix_to_handler`.
    """
    expected = _generate_prefix_to_handler()
    print(expected)
    assert prefix_to_handler == expected
