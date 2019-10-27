from manubot.pandoc.util import get_pandoc_version


def test_get_pandoc_version():
    version = get_pandoc_version()
    assert isinstance(version, tuple)
    assert len(version) >= 2
    for v in version:
        assert isinstance(v, int)
