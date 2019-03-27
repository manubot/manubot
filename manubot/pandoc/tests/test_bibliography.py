import pathlib

import pytest

from manubot.pandoc.bibliography import (
    load_bibliography,
)

directory = pathlib.Path(__file__).parent
bibliography_paths = sorted(directory.glob('bibliographies/bibliography.*'))
bibliography_path_ids = [path.name for path in bibliography_paths]


def test_bibliography_paths():
    """
    Test that the correct number of bibliography files are detected.
    """
    assert len(bibliography_path_ids) == 4


@pytest.mark.parametrize('path', bibliography_paths, ids=bibliography_path_ids)
def test_load_bibliography_from_path(path):
    """
    Some of the bibliographies for this test were generated at
    https://zbib.org/c7f95cdef6d6409c92ffde24d519435d
    """
    path = directory / path
    csl_json = load_bibliography(path=path)
    assert len(csl_json) == 2
    assert csl_json[0]['title'].rstrip('.') == 'Sci-Hub provides access to nearly all scholarly literature'


@pytest.mark.parametrize('path', bibliography_paths, ids=bibliography_path_ids)
def test_load_bibliography_from_text(path):
    """
    https://zbib.org/c7f95cdef6d6409c92ffde24d519435d
    """
    text = directory.joinpath(path).read_text()
    input_format = path.suffix[1:]
    csl_json = load_bibliography(text=text, input_format=input_format)
    assert len(csl_json) == 2
    assert csl_json[0]['title'].rstrip('.') == 'Sci-Hub provides access to nearly all scholarly literature'
    if input_format in {'json', 'bib'}:
        assert csl_json[0].get('id') == 'doi:10.7554/elife.32822'
