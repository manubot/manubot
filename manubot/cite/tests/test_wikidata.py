from manubot.cite.wikidata import get_wikidata_citeproc


def test_get_wikidata_citeproc():
    """
    Test metadata extraction from https://www.wikidata.org/wiki/Q50051684
    """
    wikidata_id = 'Q50051684'
    csl_item = get_wikidata_citeproc(wikidata_id)
    assert 'Sci-Hub provides access to nearly all scholarly literature' in csl_item['title']
    assert csl_item['container-title'] == 'eLife'
    assert csl_item['DOI'] == '10.7554/elife.32822'


def test_get_wikidata_citeproc_author_ordering():
    """
    Test extraction of author ordering from https://www.wikidata.org/wiki/Q50051684.
    Wikidata uses a "series ordinal" qualifier that must be considered or else author
    ordering may be wrong.

    Author ordering was previously not properly set by the Wikidata translator
    https://github.com/zotero/translators/issues/1790
    """
    wikidata_id = 'Q50051684'
    csl_item = get_wikidata_citeproc(wikidata_id)
    family_names =[author['family'] for author in csl_item['author']]
    print(family_names)
    assert family_names == [
        'Himmelstein',
        'Romero',
        'Levernier',
        'Munro',
        'McLaughlin',
        'Greshake',  # actually should be Greshake Tzovaras
        'Greene',
    ]
