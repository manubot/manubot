import json
import pathlib
import shutil
import subprocess

import pytest

from manubot.cite.util import (
    citation_pattern,
    citation_to_citeproc,
    get_citation_id,
    inspect_citation_identifier,
    standardize_citation,
)
from manubot.cite.pubmed import (
    get_pmcid_and_pmid_for_doi,
    get_pmid_for_doi,
    get_pubmed_ids_for_doi,
)


@pytest.mark.parametrize("citation_string", [
    ('@doi:10.5061/dryad.q447c/1'),
    ('@arxiv:1407.3561v1'),
    ('@doi:10.1007/978-94-015-6859-3_4'),
    ('@tag:tag_with_underscores'),
    ('@tag:tag-with-hyphens'),
    ('@url:https://greenelab.github.io/manubot-rootstock/'),
    ('@tag:abc123'),
    ('@tag:123abc'),
])
def test_citation_pattern_match(citation_string):
    match = citation_pattern.fullmatch(citation_string)
    assert match


@pytest.mark.parametrize("citation_string", [
    ('doi:10.5061/dryad.q447c/1'),
    ('@tag:abc123-'),
    ('@tag:abc123_'),
    ('@-tag:abc123'),
    ('@_tag:abc123'),
])
def test_citation_pattern_no_match(citation_string):
    match = citation_pattern.fullmatch(citation_string)
    assert match is None


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
    ('isbn:1339919885', 'isbn:9781339919881'),
    ('isbn:1-339-91988-5', 'isbn:9781339919881'),
    ('isbn:978-0-387-95069-3', 'isbn:9780387950693'),
    ('isbn:9780387950938', 'isbn:9780387950938'),
    ('isbn:1-55860-510-X', 'isbn:9781558605107'),
    ('isbn:1-55860-510-x', 'isbn:9781558605107'),
])
def test_standardize_citation(citation, expected):
    """
    Standardize idenfiers based on their source
    """
    output = standardize_citation(citation)
    assert output == expected


@pytest.mark.parametrize('citation', [
    'doi:10.7717/peerj.705',
    'pmcid:PMC4304851',
    'pmid:25648772',
    'arxiv:1407.3561',
    'isbn:978-1-339-91988-1',
    'isbn:1-339-91988-5',
    'wikidata:Q1',
    'wikidata:Q50051684',
    'url:https://peerj.com/articles/705/',
])
def test_inspect_citation_identifier_passes(citation):
    """
    These citations should pass inspection by inspect_citation_identifier.
    """
    assert inspect_citation_identifier(citation) is None


@pytest.mark.parametrize(['citation', 'contains'], [
    ('doi:10.771/peerj.705', 'Double check the DOI'),
    ('doi:7717/peerj.705', 'must start with `10.`'),
    ('pmcid:25648772', 'must start with `PMC`'),
    ('pmid:PMC4304851', 'Should pmid:PMC4304851 switch the citation source to `pmcid`?'),
    ('isbn:1-339-91988-X', 'identifier violates the ISBN syntax'),
    ('wikidata:P212', 'item IDs must start with `Q`'),
    ('wikidata:QABCD', 'does not conform to the Wikidata item ID regex'),
])
def test_inspect_citation_identifier_fails(citation, contains):
    """
    These citations should fail inspection by inspect_citation_identifier.
    """
    report = inspect_citation_identifier(citation)
    assert report is not None
    assert isinstance(report, str)
    assert contains in report


@pytest.mark.xfail(reason='https://twitter.com/dhimmel/status/950443969313419264')
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
    assert citeproc['number'] == 'cond-mat/0703470v2'
    assert citeproc['version'] == '2'
    assert citeproc['type'] == 'report'
    assert citeproc['container-title'] == 'arXiv'
    assert citeproc['title'] == 'Portraits of Complex Networks'
    authors = citeproc['author']
    assert authors[0]['literal'] == 'J. P. Bagrow'
    assert citeproc['DOI'] == '10.1209/0295-5075/81/68004'


def test_citation_to_citeproc_pmc():
    """
    https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/pmc/?format=csl&id=3041534
    """
    citation = f'pmcid:PMC3041534'
    citeproc = citation_to_citeproc(citation)
    assert citeproc['id'] == 'RoOhUFKU'
    assert citeproc['URL'] == 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3041534/'
    assert citeproc['container-title-short'] == 'AMIA Jt Summits Transl Sci Proc'
    assert citeproc['title'] == 'Secondary Use of EHR: Data Quality Issues and Informatics Opportunities'
    authors = citeproc['author']
    assert authors[0]['family'] == 'Botsis'
    assert citeproc['PMID'] == '21347133'
    assert citeproc['PMCID'] == 'PMC3041534'


def test_citation_to_citeproc_pubmed_1():
    """
    Generated from XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=21347133&rettype=full
    """
    citation = 'pmid:21347133'
    citeproc = citation_to_citeproc(citation)
    assert citeproc['id'] == 'y9ONtSZ9'
    assert citeproc['type'] == 'article-journal'
    assert citeproc['URL'] == 'https://www.ncbi.nlm.nih.gov/pubmed/21347133'
    assert citeproc['container-title'] == 'AMIA Joint Summits on Translational Science proceedings. AMIA Joint Summits on Translational Science'
    assert citeproc['title'] == 'Secondary Use of EHR: Data Quality Issues and Informatics Opportunities.'
    assert citeproc['issued']['date-parts'] == [[2010, 3, 1]]
    authors = citeproc['author']
    assert authors[0]['given'] == 'Taxiarchis'
    assert authors[0]['family'] == 'Botsis'
    assert citeproc['PMID'] == '21347133'
    assert citeproc['PMCID'] == 'PMC3041534'


def test_citation_to_citeproc_pubmed_2():
    """
    Generated from XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=27094199&rettype=full
    """
    citation = 'pmid:27094199'
    citeproc = citation_to_citeproc(citation)
    print(citeproc)
    assert citeproc['id'] == 'alaFV9OY'
    assert citeproc['type'] == 'article-journal'
    assert citeproc['URL'] == 'https://www.ncbi.nlm.nih.gov/pubmed/27094199'
    assert citeproc['container-title'] == 'Circulation. Cardiovascular genetics'
    assert citeproc['container-title-short'] == 'Circ Cardiovasc Genet'
    assert citeproc['page'] == '179-84'
    assert citeproc['title'] == 'Genetic Association-Guided Analysis of Gene Networks for the Study of Complex Traits.'
    assert citeproc['issued']['date-parts'] == [[2016, 4]]
    authors = citeproc['author']
    assert authors[0]['given'] == 'Casey S'
    assert authors[0]['family'] == 'Greene'
    assert citeproc['PMID'] == '27094199'
    assert citeproc['DOI'] == '10.1161/circgenetics.115.001181'


def test_citation_to_citeproc_pubmed_with_numeric_month():
    """
    Generated from XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=29028984&rettype=full

    See https://github.com/greenelab/manubot/issues/69
    """
    citation = 'pmid:29028984'
    citeproc = citation_to_citeproc(citation)
    print(citeproc)
    assert citeproc['issued']['date-parts'] == [[2018, 3, 15]]


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


def test_citation_to_citeproc_pubmed_book():
    """
    Extracting CSL metadata from books in PubMed is not supported.
    Logic not implemented to parse XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=29227604&rettype=full
    """
    with pytest.raises(NotImplementedError):
        citation_to_citeproc('pmid:29227604')


def test_citation_to_citeproc_isbn():
    csl_item = citation_to_citeproc('isbn:9780387950693')
    assert csl_item['type'] == 'book'
    assert csl_item['title'] == 'Complex analysis'


@pytest.mark.xfail(reason="Quotation in title removed at some upstream point")
def test_citation_to_citeproc_isbnlib_title_with_quotation_mark():
    from manubot.cite.isbn import get_isbn_citeproc_isbnlib
    csl_item = get_isbn_citeproc_isbnlib('9780312353780')
    assert csl_item['type'] == 'book'
    assert csl_item['title'].startswith('"F" is for Fugitive')


def test_get_isbn_citeproc_citoid_weird_date():
    """
    isbn:9780719561023 has a date value of "(2004 printing)"
    https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/9780719561023
    """
    from manubot.cite.isbn import get_isbn_citeproc_citoid
    csl_item = get_isbn_citeproc_citoid('9780719561023')
    assert csl_item['issued']['date-parts'] == [[2004]]
    assert csl_item['ISBN'] == '9780719561023'


def test_get_isbn_citeproc_citoid_not_found():
    """
    isbn:9781439566039 is not found by Citoid:
    https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/9781439566039
    """
    from manubot.cite.isbn import get_isbn_citeproc_citoid
    with pytest.raises(KeyError, match=r'Metadata for ISBN [0-9]{10,13} not found'):
        get_isbn_citeproc_citoid('9781439566039')


def test_cite_command_empty():
    process = subprocess.run(
        ['manubot', 'cite'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(process.stderr)
    assert process.returncode == 2
    assert 'the following arguments are required: citations' in process.stderr


def test_cite_command_stdout():
    process = subprocess.run(
        ['manubot', 'cite', 'arxiv:1806.05726v1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(process.stderr)
    assert process.returncode == 0
    csl, = json.loads(process.stdout)
    assert csl['URL'] == 'https://arxiv.org/abs/1806.05726v1'


def test_cite_command_file(tmpdir):
    path = pathlib.Path(tmpdir) / 'csl-items.json'
    process = subprocess.run(
        ['manubot', 'cite', '--output', str(path), 'arxiv:1806.05726v1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(process.stderr.decode())
    assert process.returncode == 0
    with path.open() as read_file:
        csl, = json.load(read_file)
    assert csl['URL'] == 'https://arxiv.org/abs/1806.05726v1'


@pytest.mark.parametrize(['args', 'expected'], [
    ([], 'references-plain.txt'),
    (['--format', 'plain'], 'references-plain.txt'),
    (['--format', 'markdown'], 'references-markdown.md'),
    (['--format', 'html'], 'references-html.html'),
    (['--format', 'jats'], 'references-jats.xml'),
], ids=['no-args', '--format=plain', '--format=markdown', '--format=html', '--format=jats'])
@pytest.mark.skipif(
    not shutil.which('pandoc'),
    reason='pandoc installation not found on system'
)
@pytest.mark.skipif(
    not shutil.which('pandoc-citeproc'),
    reason='pandoc-citeproc installation not found on system'
)
def test_cite_command_render_stdout(args, expected):
    """
    Note that this test may fail if the Pandoc version is not recent enough to
    support --lua-filter (introduced in pandoc 2.0) or URLs for --csl.
    """
    expected = (
        pathlib.Path(__file__).parent
        .joinpath('cite-command-rendered', expected)
        .read_text()
    )
    args = [
        'manubot', 'cite', '--render',
        '--csl', 'https://github.com/greenelab/manubot-rootstock/raw/e83e51dcd89256403bb787c3d9a46e4ee8d04a9e/build/assets/style.csl',
        'arxiv:1806.05726v1', 'doi:10.6084/m9.figshare.5346577.v1', 'pmid:29618526',
    ] + args
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(' '.join(process.args))
    print(process.stdout)
    print(process.stderr)
    assert process.stdout == expected
