import pytest

from manubot.cite.doi import (
    expand_short_doi,
    DOI
)

from manubot.cite.types import CiteKey


class Test_DOI():
    def test_citekey_handle_results_in_doi(self):    
       assert CiteKey("doi:blah").handle() == DOI("blah")


def test_expand_short_doi():
    doi = expand_short_doi('10/b6vnmd')
    assert doi == "10.1016/s0933-3657(96)00367-3"


def test_expand_short_doi_invalid():
    with pytest.raises(ValueError, match='Handle not found. Double check short_doi'):
        expand_short_doi('10/b6vnmdxxxxxx')


def test_expand_short_doi_not_short():
    with pytest.raises(ValueError, match='shortDOIs start with `10/`'):
        expand_short_doi('10.1016/S0933-3657(96)00367-3')
