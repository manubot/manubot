import pytest

from manubot.cite.doi import (
    expand_short_doi,
    DOI,
    get_doi_csl_item,
    get_doi_csl_item_zotero,
    get_doi_csl_item_crosscite,
)


class Test_DOI():

    def test_constructor(self):
        assert DOI('blah').identifier == 'blah'

    @pytest.mark.parametrize("identifier,expected", [
    ('10.5061/DRYAD.q447c/1', '10.5061/dryad.q447c/1'),
    ('10.5061/dryad.q447c/1', '10.5061/dryad.q447c/1'),
    ])
    def test_canonic_method_on_uppercase(self, identifier, expected):
        assert DOI(identifier).canonic().identifier == expected   

    @pytest.mark.parametrize("identifier,expected", [
    ('10/b6vnmd', '10.1016/s0933-3657(96)00367-3'),
    ('10/B6VNMD', '10.1016/s0933-3657(96)00367-3'),
    ])
    def test_canonic_method_on_short_doi(self, identifier, expected):
        assert DOI(identifier).canonic().identifier == expected   

    def test_canonic_method_on_passthrough(self):
        assert DOI('10/xxxxxxxxxxxxxYY').canonic().identifier == '10/xxxxxxxxxxxxxyy'

    @pytest.mark.skip 
    def test_csl_item(self, reason='Skipping in favour of integration test'):
        csl_item = DOI('10/b6vnmd').canonic().csl_item()
        assert csl_item['title'].startswith('An evaluation of machine-learning methods')      



def test_expand_short_doi():
    doi = expand_short_doi('10/b6vnmd')
    assert doi == "10.1016/s0933-3657(96)00367-3"


def test_expand_short_doi_invalid():
    with pytest.raises(ValueError, match='Handle not found. Double check short_doi'):
        expand_short_doi('10/b6vnmdxxxxxx')


def test_expand_short_doi_not_short():
    with pytest.raises(ValueError, match='shortDOIs start with `10/`'):
        expand_short_doi('10.1016/S0933-3657(96)00367-3')


def test_get_doi_csl_item_crosscite():
    doi = '10.1101/142760'
    csl_item = get_doi_csl_item_crosscite(doi)
    assert isinstance(csl_item, dict)
    csl_item['publisher'] == "Cold Spring Harbor Laboratory"


def test_get_doi_csl_item_zotero():
    """
    As of 2019-10-25, DOI Content Negotiation (i.e. crosscite) encodes the consurtium
    in author.name rather than author.literal. Zotero translation-server encodes
    the consortium in author.family, which is better than nothing since it's a valid
    CSL JSON field.
    https://github.com/manubot/manubot/issues/158
    """
    doi = '10.1038/ng.3834'
    csl_item = get_doi_csl_item_zotero(doi)
    assert isinstance(csl_item, dict)
    csl_item['author'][9]['family'] == "GTEx Consortium"


def test_get_doi_csl_item():
    """
    Test URL is set with shortDOI when calling get_doi_csl_item.
    """
    doi = '10.1101/142760'
    csl_item = get_doi_csl_item(doi)
    assert isinstance(csl_item, dict)
    assert csl_item['URL'] == "https://doi.org/gbpvh5"
