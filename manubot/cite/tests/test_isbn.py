import pytest

from manubot.cite.isbn import (
    get_isbn_csl_item_citoid,
    get_isbn_csl_item_isbnlib,
    get_isbn_csl_item_zotero,
)


@pytest.mark.xfail(reason="Quotation in title removed at some upstream point")
def test_citekey_to_csl_item_isbnlib_title_with_quotation_mark():
    csl_item = get_isbn_csl_item_isbnlib("9780312353780")
    assert csl_item["type"] == "book"
    assert csl_item["title"].startswith('"F" is for Fugitive')


def test_get_isbn_csl_item_citoid_weird_date():
    """
    isbn:9780719561023 has a date value of "(2004 printing)"
    https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/9780719561023
    """
    csl_item = get_isbn_csl_item_citoid("9780719561023")
    assert csl_item["issued"]["date-parts"] == [[2004]]
    assert csl_item["ISBN"] == "9780719561023"


def test_get_isbn_csl_item_citoid_not_found():
    """
    isbn:9781439566039 is not found by Citoid:
    https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/9781439566039
    """
    with pytest.raises(KeyError, match=r"Metadata for ISBN [0-9]{10,13} not found"):
        get_isbn_csl_item_citoid("9781439566039")


def test_get_isbn_csl_item_zotero_with_note_issue():
    """
    translation-server returns two metadata records for this ISBN.
    The second has itemType=note and previously caused CSL export to fail.
    https://github.com/zotero/translation-server/issues/67
    """
    isbn = "9780262517638"
    csl_item = get_isbn_csl_item_zotero(isbn)
    assert csl_item["author"][0]["family"] == "Suber"
