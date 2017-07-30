import pytest

from manubot.citations import (
    citation_to_metadata,
    get_citation_id,
    standardize_identifier,
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


@pytest.mark.parametrize("source,identifier,expected", [
    ('doi', '10.5061/DRYAD.q447c/1', '10.5061/dryad.q447c/1'),
    ('doi', '10.5061/dryad.q447c/1', '10.5061/dryad.q447c/1'),
    ('pmid', '24159271', '24159271'),
])
def test_standardize_identifier(source, identifier, expected):
    """
    Standardize idenfiers based on their source
    """
    output = standardize_identifier(source, identifier)
    assert output == expected


def test_citation_to_metadata_doi_datacite():
    citation = 'doi:10.7287/PeerJ.Preprints.3100v1'
    result = citation_to_metadata(citation)
    assert result['source'] == 'doi'
    assert result['identifer'] == '10.7287/peerj.preprints.3100v1'
    assert result['standard_citation'] == 'doi:10.7287/peerj.preprints.3100v1'
    assert result['citation_id'] == '11cb5HXoY'
    citeproc = result['citeproc']
    assert citeproc['id'] == '11cb5HXoY'
    assert citeproc['URL'] == 'https://doi.org/10.7287/peerj.preprints.3100v1'
    assert citeproc['DOI'] == '10.7287/peerj.preprints.3100v1'
    assert citeproc['type'] == 'report'
    assert citeproc['title'] == 'Sci-Hub provides access to nearly all scholarly literature'
    authors = citeproc['author']
    assert authors[0]['family'] == 'Himmelstein'
    assert authors[-1]['family'] == 'Greene'


def test_citation_to_metadata_arxiv():
    citation = 'arxiv:cond-mat/0703470v2'
    result = citation_to_metadata(citation)
    assert result['source'] == 'arxiv'
    assert result['identifer'] == 'cond-mat/0703470v2'
    assert result['standard_citation'] == 'arxiv:cond-mat/0703470v2'
    print(result)
    assert result['citation_id'] == 'ES92tcdg'
    citeproc = result['citeproc']
    assert citeproc['id'] == 'ES92tcdg'
    assert citeproc['URL'] == 'https://arxiv.org/abs/cond-mat/0703470v2'
    assert citeproc['version'] == '2'
    assert citeproc['type'] == 'report'
    assert citeproc['container-title'] == 'arXiv'
    assert citeproc['title'] == 'Portraits of Complex Networks'
    authors = citeproc['author']
    assert authors[0]['literal'] == 'J. P. Bagrow'
    assert citeproc['DOI'] == '10.1209/0295-5075/81/68004'
