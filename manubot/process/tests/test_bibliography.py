from manubot.pandoc.tests.test_bibliography import (
    bibliography_paths
)
from manubot.process.bibliography import (
    load_bibliography,
    load_manual_references,
)


def test_load_multiple_bibliography_paths():
    citation_to_csl_item = load_manual_references(bibliography_paths)
    print(list(citation_to_csl_item))

    assert 'doi:10.7554/elife.32822' in citation_to_csl_item
    csl_item_1 = citation_to_csl_item['doi:10.7554/elife.32822']
    assert csl_item_1['title'].startswith('Sci-Hub')

    # raw id corresponding to bibliography.bib
    assert 'raw:noauthor_techblog:_nodate' in citation_to_csl_item
    csl_item_2 = citation_to_csl_item['raw:noauthor_techblog:_nodate']
    assert csl_item_2['title'].startswith('TechBlog')

    # id inferred by pandoc-citeproc during bib2json conversion of .nbib file
    assert 'raw:Beaulieu-Jones2017' in citation_to_csl_item
    csl_item_3 = citation_to_csl_item['raw:Beaulieu-Jones2017']
    assert csl_item_3['author'][0]['family'] == 'Beaulieu-Jones'
