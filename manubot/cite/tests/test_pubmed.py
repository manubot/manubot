import pytest

from manubot.cite.pubmed import (
    get_pmcid_and_pmid_for_doi,
    get_pmid_for_doi,
    get_pubmed_ids_for_doi,
)


@pytest.mark.parametrize(('doi', 'pmid'), [
    ('10.1098/rsif.2017.0387', '29618526'),  # in PubMed and PMC
    ('10.1161/CIRCGENETICS.115.001181', '27094199'),  # in PubMed but not PMC
    ('10.7717/peerj-cs.134', None),  # DOI in journal not indexed by PubMed
    ('10.1161/CIRC', None),  # invalid DOI
])
def test_get_pmid_for_doi(doi, pmid):
    output = get_pmid_for_doi(doi)
    assert pmid == output


@pytest.mark.parametrize(('doi', 'id_dict'), [
    ('10.1098/rsif.2017.0387', {'PMCID': 'PMC5938574', 'PMID': '29618526'}),
    ('10.7554/ELIFE.32822', {'PMCID': 'PMC5832410', 'PMID': '29424689'}),
    ('10.1161/CIRCGENETICS.115.001181', {}),  # only in PubMed, not in PMC
    ('10.7717/peerj.000', {}),  # Non-existent DOI
    ('10.peerj.000', {}),  # malformed DOI
])
def test_get_pmcid_and_pmid_for_doi(doi, id_dict):
    output = get_pmcid_and_pmid_for_doi(doi)
    assert id_dict == output


@pytest.mark.parametrize(('doi', 'id_dict'), [
    ('10.1098/rsif.2017.0387', {'PMCID': 'PMC5938574', 'PMID': '29618526'}),
    ('10.7554/ELIFE.32822', {'PMCID': 'PMC5832410', 'PMID': '29424689'}),
    ('10.1161/CIRCGENETICS.115.001181', {'PMID': '27094199'}),  # only in PubMed, not in PMC
    ('10.7717/peerj.000', {}),  # Non-existent DOI
])
def test_get_pubmed_ids_for_doi(doi, id_dict):
    output = get_pubmed_ids_for_doi(doi)
    assert id_dict == output
