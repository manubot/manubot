import copy

import pytest

from manubot.cite.util import (
    citekey_pattern,
    citekey_to_csl_item,
    csl_item_set_standard_id,
    shorten_citekey,
    infer_citekey_prefix,
    inspect_citekey,
    standardize_citekey,
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
def test_citekey_pattern_match(citation_string):
    match = citekey_pattern.fullmatch(citation_string)
    assert match


@pytest.mark.parametrize("citation_string", [
    ('doi:10.5061/dryad.q447c/1'),
    ('@tag:abc123-'),
    ('@tag:abc123_'),
    ('@-tag:abc123'),
    ('@_tag:abc123'),
])
def test_citekey_pattern_no_match(citation_string):
    match = citekey_pattern.fullmatch(citation_string)
    assert match is None


@pytest.mark.parametrize("standard_citekey,expected", [
    ('doi:10.5061/dryad.q447c/1', 'kQFQ8EaO'),
    ('arxiv:1407.3561v1', '16kozZ9Ys'),
    ('pmid:24159271', '11sli93ov'),
    ('url:http://blog.dhimmel.com/irreproducible-timestamps/', 'QBWMEuxW'),
])
def test_shorten_citekey(standard_citekey, expected):
    short_citekey = shorten_citekey(standard_citekey)
    assert short_citekey == expected


@pytest.mark.parametrize("citekey,expected", [
    ('doi:10.5061/DRYAD.q447c/1', 'doi:10.5061/dryad.q447c/1'),
    ('doi:10.5061/dryad.q447c/1', 'doi:10.5061/dryad.q447c/1'),
    ('doi:10/b6vnmd', 'doi:10.1016/s0933-3657(96)00367-3'),
    ('doi:10/B6VNMD', 'doi:10.1016/s0933-3657(96)00367-3'),
    ('doi:10/xxxxxxxxxxxxxYY', 'doi:10/xxxxxxxxxxxxxyy'),  # passthrough non-existent shortDOI
    ('pmid:24159271', 'pmid:24159271'),
    ('isbn:1339919885', 'isbn:9781339919881'),
    ('isbn:1-339-91988-5', 'isbn:9781339919881'),
    ('isbn:978-0-387-95069-3', 'isbn:9780387950693'),
    ('isbn:9780387950938', 'isbn:9780387950938'),
    ('isbn:1-55860-510-X', 'isbn:9781558605107'),
    ('isbn:1-55860-510-x', 'isbn:9781558605107'),
])
def test_standardize_citekey(citekey, expected):
    """
    Standardize identifiers based on their source
    """
    output = standardize_citekey(citekey)
    assert output == expected


@pytest.mark.parametrize('citekey', [
    'doi:10.7717/peerj.705',
    'doi:10/b6vnmd',
    'pmcid:PMC4304851',
    'pmid:25648772',
    'arxiv:1407.3561',
    'isbn:978-1-339-91988-1',
    'isbn:1-339-91988-5',
    'wikidata:Q1',
    'wikidata:Q50051684',
    'url:https://peerj.com/articles/705/',
])
def test_inspect_citekey_passes(citekey):
    """
    These citekeys should pass inspection by inspect_citekey.
    """
    assert inspect_citekey(citekey) is None


@pytest.mark.parametrize(['citekey', 'contains'], [
    ('doi:10.771/peerj.705', 'Double check the DOI'),
    ('doi:10/b6v_nmd', 'Double check the shortDOI'),
    ('doi:7717/peerj.705', 'must start with `10.`'),
    ('doi:b6vnmd', 'must start with `10.`'),
    ('pmcid:25648772', 'must start with `PMC`'),
    ('pmid:PMC4304851', 'Should pmid:PMC4304851 switch the citation source to `pmcid`?'),
    ('isbn:1-339-91988-X', 'identifier violates the ISBN syntax'),
    ('wikidata:P212', 'item IDs must start with `Q`'),
    ('wikidata:QABCD', 'does not conform to the Wikidata regex'),
])
def test_inspect_citekey_fails(citekey, contains):
    """
    These citekeys should fail inspection by inspect_citekey.
    """
    report = inspect_citekey(citekey)
    assert report is not None
    assert isinstance(report, str)
    assert contains in report


@pytest.mark.xfail(reason='https://twitter.com/dhimmel/status/950443969313419264')
def test_citekey_to_csl_item_doi_datacite():
    citekey = 'doi:10.7287/peerj.preprints.3100v1'
    csl_item = citekey_to_csl_item(citekey)
    assert csl_item['id'] == '11cb5HXoY'
    assert csl_item['URL'] == 'https://doi.org/10.7287/peerj.preprints.3100v1'
    assert csl_item['DOI'] == '10.7287/peerj.preprints.3100v1'
    assert csl_item['type'] == 'report'
    assert csl_item['title'] == 'Sci-Hub provides access to nearly all scholarly literature'
    authors = csl_item['author']
    assert authors[0]['family'] == 'Himmelstein'
    assert authors[-1]['family'] == 'Greene'


def test_citekey_to_csl_item_arxiv():
    citekey = 'arxiv:cond-mat/0703470v2'
    csl_item = citekey_to_csl_item(citekey)
    assert csl_item['id'] == 'ES92tcdg'
    assert csl_item['URL'] == 'https://arxiv.org/abs/cond-mat/0703470v2'
    assert csl_item['number'] == 'cond-mat/0703470v2'
    assert csl_item['version'] == '2'
    assert csl_item['type'] == 'report'
    assert csl_item['container-title'] == 'arXiv'
    assert csl_item['title'] == 'Portraits of Complex Networks'
    authors = csl_item['author']
    assert authors[0]['literal'] == 'J. P. Bagrow'
    assert csl_item['DOI'] == '10.1209/0295-5075/81/68004'


def test_citekey_to_csl_item_pmc():
    """
    https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/pmc/?format=csl&id=3041534
    """
    citekey = f'pmcid:PMC3041534'
    csl_item = citekey_to_csl_item(citekey)
    assert csl_item['id'] == 'RoOhUFKU'
    assert csl_item['URL'] == 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3041534/'
    assert csl_item['container-title-short'] == 'Summit Transl Bioinform'
    assert csl_item['title'] == 'Secondary Use of EHR: Data Quality Issues and Informatics Opportunities'
    authors = csl_item['author']
    assert authors[0]['family'] == 'Botsis'
    assert csl_item['PMID'] == '21347133'
    assert csl_item['PMCID'] == 'PMC3041534'
    assert 'generated by Manubot' in csl_item['note']
    assert 'standard_id: pmcid:PMC3041534' in csl_item['note']


def test_citekey_to_csl_item_pubmed_1():
    """
    Generated from XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=21347133&rettype=full
    """
    citekey = 'pmid:21347133'
    csl_item = citekey_to_csl_item(citekey)
    assert csl_item['id'] == 'y9ONtSZ9'
    assert csl_item['type'] == 'article-journal'
    assert csl_item['URL'] == 'https://www.ncbi.nlm.nih.gov/pubmed/21347133'
    assert csl_item['container-title'] == 'Summit on translational bioinformatics'
    assert csl_item['title'] == 'Secondary Use of EHR: Data Quality Issues and Informatics Opportunities.'
    assert csl_item['issued']['date-parts'] == [[2010, 3, 1]]
    authors = csl_item['author']
    assert authors[0]['given'] == 'Taxiarchis'
    assert authors[0]['family'] == 'Botsis'
    assert csl_item['PMID'] == '21347133'
    assert csl_item['PMCID'] == 'PMC3041534'


def test_citekey_to_csl_item_pubmed_2():
    """
    Generated from XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=27094199&rettype=full
    """
    citekey = 'pmid:27094199'
    csl_item = citekey_to_csl_item(citekey)
    print(csl_item)
    assert csl_item['id'] == 'alaFV9OY'
    assert csl_item['type'] == 'article-journal'
    assert csl_item['URL'] == 'https://www.ncbi.nlm.nih.gov/pubmed/27094199'
    assert csl_item['container-title'] == 'Circulation. Cardiovascular genetics'
    assert csl_item['container-title-short'] == 'Circ Cardiovasc Genet'
    assert csl_item['page'] == '179-84'
    assert csl_item['title'] == 'Genetic Association-Guided Analysis of Gene Networks for the Study of Complex Traits.'
    assert csl_item['issued']['date-parts'] == [[2016, 4]]
    authors = csl_item['author']
    assert authors[0]['given'] == 'Casey S'
    assert authors[0]['family'] == 'Greene'
    assert csl_item['PMID'] == '27094199'
    assert csl_item['DOI'] == '10.1161/circgenetics.115.001181'


def test_citekey_to_csl_item_pubmed_with_numeric_month():
    """
    Generated from XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=29028984&rettype=full

    See https://github.com/manubot/manubot/issues/69
    """
    citekey = 'pmid:29028984'
    csl_item = citekey_to_csl_item(citekey)
    print(csl_item)
    assert csl_item['issued']['date-parts'] == [[2018, 3, 15]]


def test_citekey_to_csl_item_pubmed_book():
    """
    Extracting CSL metadata from books in PubMed is not supported.
    Logic not implemented to parse XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=29227604&rettype=full
    """
    with pytest.raises(NotImplementedError):
        citekey_to_csl_item('pmid:29227604')


def test_citekey_to_csl_item_isbn():
    csl_item = citekey_to_csl_item('isbn:9780387950693')
    assert csl_item['type'] == 'book'
    assert csl_item['title'] == 'Complex analysis'


@pytest.mark.parametrize(['citation', 'expect'], [
    ('doi:not-a-real-doi', 'doi:not-a-real-doi'),
    ('DOI:not-a-real-doi', 'doi:not-a-real-doi'),
    ('uRl:mixed-case-prefix', 'url:mixed-case-prefix'),
    ('raw:raw-citation', 'raw:raw-citation'),
    ('no-prefix', 'raw:no-prefix'),
    ('no-prefix:but-colon', 'raw:no-prefix:but-colon'),
])
def test_infer_citekey_prefix(citation, expect):
    assert infer_citekey_prefix(citation) == expect


@pytest.mark.parametrize(
    ['csl_item', 'standard_citation'],
    [
        (
            {'id': 'my-id', 'standard_citation': 'doi:10.7554/elife.32822'},
            'doi:10.7554/elife.32822',
        ),
        (
            {'id': 'doi:10.7554/elife.32822'},
            'doi:10.7554/elife.32822',
        ),
        (
            {'id': 'doi:10.7554/ELIFE.32822'},
            'doi:10.7554/elife.32822',
        ),
        (
            {'id': 'my-id'},
            'raw:my-id',
        ),
    ],
    ids=[
        'from_standard_citation',
        'from_doi_id',
        'from_doi_id_standardize',
        'from_raw_id',
    ]
)
def test_csl_item_set_standard_id(csl_item, standard_citation):
    output = csl_item_set_standard_id(csl_item)
    assert output is csl_item
    assert output['id'] == standard_citation


def test_csl_item_set_standard_id_repeated():
    csl_item = {
        'id': 'pmid:1',
        'type': 'article-journal',
    }
    # csl_item_0 = copy.deepcopy(csl_item)
    csl_item_1 = copy.deepcopy(csl_item_set_standard_id(csl_item))
    assert 'standard_citation' not in 'csl_item'
    csl_item_2 = copy.deepcopy(csl_item_set_standard_id(csl_item))
    assert csl_item_1 == csl_item_2


def test_csl_item_set_standard_id_note():
    """
    Test extracting standard_id from a note and setting additional
    note fields.
    """
    csl_item = {
        'id': 'original-id',
        'type': 'article-journal',
        'note': 'standard_id: doi:10.1371/journal.PPAT.1006256',
    }
    csl_item_set_standard_id(csl_item)
    assert csl_item['id'] == 'doi:10.1371/journal.ppat.1006256'
    from manubot.cite.citeproc import parse_csl_item_note
    note_dict = parse_csl_item_note(csl_item['note'])
    assert note_dict['original_id'] == 'original-id'
    assert note_dict['original_standard_id'] == 'doi:10.1371/journal.PPAT.1006256'
