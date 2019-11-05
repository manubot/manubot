import pytest


from ..thumbnail import test_get_thumbnail_url


@pytest.mark.parametrize(
    ("thumbnail", "expected"),
    [
        (None, None),
        ("", None),
        ("http://example.com/thumbnail.png", "http://example.com/thumbnail.png"),
        ("https://example.com/thumbnail.png", "https://example.com/thumbnail.png"),
    ],
)
def test_get_thumbnail_url(thumbnail, expected):
    thumbnail_url = test_get_thumbnail_url(thumbnail)
    assert thumbnail_url == expected
