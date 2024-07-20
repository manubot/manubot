import pytest

from manubot.cite.doi import (
    expand_short_doi,
    get_doi_csl_item,
    get_doi_csl_item_datacite,
    get_doi_csl_item_default,
    get_doi_csl_item_zotero,
)


def test_expand_short_doi():
    doi = expand_short_doi("10/b6vnmd")
    assert doi == "10.1016/s0933-3657(96)00367-3"


def test_expand_short_doi_invalid():
    with pytest.raises(ValueError, match="Handle not found. Double check short_doi"):
        expand_short_doi("10/b6vnmdxxxxxx")


def test_expand_short_doi_not_short():
    with pytest.raises(ValueError, match="shortDOIs start with `10/`"):
        expand_short_doi("10.1016/S0933-3657(96)00367-3")


def test_get_doi_csl_item_default():
    doi = "10.1101/142760"
    csl_item = get_doi_csl_item_default(doi)
    assert isinstance(csl_item, dict)
    assert csl_item["publisher"] == "Cold Spring Harbor Laboratory"


def test_get_doi_csl_item_zotero():
    """
    Test how get_doi_csl_item_zotero handles a DOI with a consortium author.
    https://github.com/manubot/manubot/issues/158
    """
    doi = "10.1038/ng.3834"
    csl_item = get_doi_csl_item_zotero(doi)
    assert isinstance(csl_item, dict)
    assert csl_item["author"][0]["literal"] == "GTEx Consortium"


def test_get_doi_csl_item():
    """
    Test URL is set with shortDOI when calling get_doi_csl_item.
    """
    doi = "10.1101/142760"
    csl_item = get_doi_csl_item(doi)
    assert isinstance(csl_item, dict)
    assert csl_item["URL"] == "https://doi.org/gbpvh5"


@pytest.mark.xfail(
    reason="DataCite Content Negotiation decided to stop supporting Crossref DOIs. https://github.com/crosscite/content-negotiation/issues/104"
)
def test_get_doi_crosscite_with_consortium_author():
    """
    Make sure the author "GTEx Consortium" is properly encoded
    using the `author.literal` CSL JSON field.

    References:

    - <https://github.com/manubot/manubot/issues/158>
    - <https://github.com/crosscite/content-negotiation/issues/92>
    """
    doi = "10.1038/ng.3834"
    csl_item = get_doi_csl_item_datacite(doi)
    assert isinstance(csl_item, dict)
    assert any(
        author.get("literal") == "GTEx Consortium" for author in csl_item["author"]
    )
