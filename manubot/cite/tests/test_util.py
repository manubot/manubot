import copy

import pytest

from manubot.cite.util import (
    citekey_pattern,
    csl_item_set_standard_id,
    shorten_citekey,
    infer_citekey_prefix,
    inspect_citekey,
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
    ('doi:7717/peerj.705', "must start with '10.'"),
    ('doi:b6vnmd', "must start with '10.'"),
    ('pmcid:25648772', "must start with 'PMC'"),
    ('pmid:PMC4304851', "Should 'pmid:PMC4304851' switch the citation source to 'pmcid'?"),
    ('isbn:1-339-91988-X', 'identifier violates the ISBN syntax'),
    ('wikidata:P212', "item IDs must start with 'Q'"),
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
