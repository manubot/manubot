import copy
import pytest

from manubot.cite.csl_dict import (
    csl_item_set_standard_id)



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

