import pytest

from manubot import utilities


@pytest.mark.parametrize("standard_citation,expected", [
    ('doi:10.5061/dryad.q447c/1', 'kQFQ8EaO'),
    ('arxiv:1407.3561v1', '16kozZ9Ys'),
    ('pmid:24159271', '11sli93ov'),
    ('url:http://blog.dhimmel.com/irreproducible-timestamps/', 'QBWMEuxW'),
])
def test_get_citation_id(standard_citation, expected):
    citation_id = utilities.get_citation_id(standard_citation)
    assert citation_id == expected
