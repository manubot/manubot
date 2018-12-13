import pytest

from manubot.cite.isbn import (
    get_isbn_citeproc_citoid,
    get_isbn_citeproc_isbnlib,
)


@pytest.mark.xfail(reason="Quotation in title removed at some upstream point")
def test_citation_to_citeproc_isbnlib_title_with_quotation_mark():
    csl_item = get_isbn_citeproc_isbnlib('9780312353780')
    assert csl_item['type'] == 'book'
    assert csl_item['title'].startswith('"F" is for Fugitive')


def test_get_isbn_citeproc_citoid_weird_date():
    """
    isbn:9780719561023 has a date value of "(2004 printing)"
    https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/9780719561023
    """
    csl_item = get_isbn_citeproc_citoid('9780719561023')
    assert csl_item['issued']['date-parts'] == [[2004]]
    assert csl_item['ISBN'] == '9780719561023'


def test_get_isbn_citeproc_citoid_not_found():
    """
    isbn:9781439566039 is not found by Citoid:
    https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/9781439566039
    """
    with pytest.raises(KeyError, match=r'Metadata for ISBN [0-9]{10,13} not found'):
        get_isbn_citeproc_citoid('9781439566039')
