import pytest

from manubot.citations import (
    citation_to_citeproc,
    get_citation_id,
    standardize_citation,
)


@pytest.mark.parametrize("standard_citation,expected", [
    ('doi:10.5061/dryad.q447c/1', 'kQFQ8EaO'),
    ('arxiv:1407.3561v1', '16kozZ9Ys'),
    ('pmid:24159271', '11sli93ov'),
    ('url:http://blog.dhimmel.com/irreproducible-timestamps/', 'QBWMEuxW'),
])
def test_get_citation_id(standard_citation, expected):
    citation_id = get_citation_id(standard_citation)
    assert citation_id == expected


@pytest.mark.parametrize("citation,expected", [
    ('doi:10.5061/DRYAD.q447c/1', 'doi:10.5061/dryad.q447c/1'),
    ('doi:10.5061/dryad.q447c/1', 'doi:10.5061/dryad.q447c/1'),
    ('pmid:24159271', 'pmid:24159271'),
])
def test_standardize_citation(citation, expected):
    """
    Standardize idenfiers based on their source
    """
    output = standardize_citation(citation)
    assert output == expected


@pytest.mark.skip(reason="https://github.com/datacite/datacite/issues/187")
def test_citation_to_citeproc_doi_datacite():
    citation = 'doi:10.7287/peerj.preprints.3100v1'
    citeproc = citation_to_citeproc(citation)
    assert citeproc['id'] == '11cb5HXoY'
    assert citeproc['URL'] == 'https://doi.org/10.7287/peerj.preprints.3100v1'
    assert citeproc['DOI'] == '10.7287/peerj.preprints.3100v1'
    assert citeproc['type'] == 'report'
    assert citeproc['title'] == 'Sci-Hub provides access to nearly all scholarly literature'
    authors = citeproc['author']
    assert authors[0]['family'] == 'Himmelstein'
    assert authors[-1]['family'] == 'Greene'


def test_citation_to_citeproc_arxiv():
    citation = 'arxiv:cond-mat/0703470v2'
    citeproc = citation_to_citeproc(citation)
    assert citeproc['id'] == 'ES92tcdg'
    assert citeproc['URL'] == 'https://arxiv.org/abs/cond-mat/0703470v2'
    assert citeproc['arxiv_id'] == 'cond-mat/0703470v2'
    assert citeproc['version'] == '2'
    assert citeproc['type'] == 'report'
    assert citeproc['container-title'] == 'arXiv'
    assert citeproc['title'] == 'Portraits of Complex Networks'
    authors = citeproc['author']
    assert authors[0]['literal'] == 'J. P. Bagrow'
    assert citeproc['DOI'] == '10.1209/0295-5075/81/68004'


def test_citation_to_citeproc_pubmed():
    citation = 'pmid:21347133'
    citeproc = citation_to_citeproc(citation)
    assert citeproc['id'] == 'y9ONtSZ9'
    assert citeproc['URL'] == 'https://www.ncbi.nlm.nih.gov/pubmed/21347133'
    assert citeproc['container-title'] == 'Summit on Translational Bioinformatics'
    assert citeproc['title'] == 'Secondary Use of EHR: Data Quality Issues and Informatics Opportunities'
    authors = citeproc['author']
    assert authors[0]['family'] == 'Botsis'
    assert citeproc['PMID'] == '21347133'
    assert citeproc['PMCID'] == 'PMC3041534'
