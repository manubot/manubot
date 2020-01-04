"""Tests rest of functions in manubot.cite, not covered by test_citekey_api.py."""

import pytest

from manubot.cite.citekey import (
    citekey_pattern,
    shorten_citekey,
    infer_citekey_prefix,
    inspect_citekey,
    url_to_citekey,
)


@pytest.mark.parametrize(
    "citation_string",
    [
        ("@doi:10.5061/dryad.q447c/1"),
        ("@arxiv:1407.3561v1"),
        ("@doi:10.1007/978-94-015-6859-3_4"),
        ("@tag:tag_with_underscores"),
        ("@tag:tag-with-hyphens"),
        ("@url:https://greenelab.github.io/manubot-rootstock/"),
        ("@tag:abc123"),
        ("@tag:123abc"),
    ],
)
def test_citekey_pattern_match(citation_string):
    match = citekey_pattern.fullmatch(citation_string)
    assert match


@pytest.mark.parametrize(
    "citation_string",
    [
        ("doi:10.5061/dryad.q447c/1"),
        ("@tag:abc123-"),
        ("@tag:abc123_"),
        ("@-tag:abc123"),
        ("@_tag:abc123"),
    ],
)
def test_citekey_pattern_no_match(citation_string):
    match = citekey_pattern.fullmatch(citation_string)
    assert match is None


@pytest.mark.parametrize(
    "standard_citekey,expected",
    [
        ("doi:10.5061/dryad.q447c/1", "kQFQ8EaO"),
        ("arxiv:1407.3561v1", "16kozZ9Ys"),
        ("pmid:24159271", "11sli93ov"),
        ("url:http://blog.dhimmel.com/irreproducible-timestamps/", "QBWMEuxW"),
    ],
)
def test_shorten_citekey(standard_citekey, expected):
    short_citekey = shorten_citekey(standard_citekey)
    assert short_citekey == expected


@pytest.mark.parametrize(
    "citekey",
    [
        "doi:10.7717/peerj.705",
        "doi:10/b6vnmd",
        "pmcid:PMC4304851",
        "pmid:25648772",
        "arxiv:1407.3561",
        "arxiv:1407.3561v1",
        "arxiv:math.GT/0309136",
        "arxiv:math.GT/0309136v1",
        "arxiv:hep-th/9305059",
        "arxiv:hep-th/9305059v2",
        "isbn:978-1-339-91988-1",
        "isbn:1-339-91988-5",
        "wikidata:Q1",
        "wikidata:Q50051684",
        "url:https://peerj.com/articles/705/",
    ],
)
def test_inspect_citekey_passes(citekey):
    """
    These citekeys should pass inspection by inspect_citekey.
    """
    assert inspect_citekey(citekey) is None


@pytest.mark.parametrize(
    ["citekey", "contains"],
    [
        ("doi:10.771/peerj.705", "Double check the DOI"),
        ("doi:10/b6v_nmd", "Double check the shortDOI"),
        ("doi:7717/peerj.705", "must start with '10.'"),
        ("doi:b6vnmd", "must start with '10.'"),
        ("pmcid:25648772", "must start with 'PMC'"),
        (
            "pmid:PMC4304851",
            "Should 'pmid:PMC4304851' switch the citation source to 'pmcid'?",
        ),
        ("isbn:1-339-91988-X", "identifier violates the ISBN syntax"),
        ("wikidata:P212", "item IDs must start with 'Q'"),
        ("wikidata:QABCD", "does not conform to the Wikidata regex"),
        ("arxiv:YYMM.number", "must conform to syntax"),
    ],
)
def test_inspect_citekey_fails(citekey, contains):
    """
    These citekeys should fail inspection by inspect_citekey.
    """
    report = inspect_citekey(citekey)
    assert report is not None
    assert isinstance(report, str)
    assert contains in report


@pytest.mark.parametrize(
    ["citation", "expect"],
    [
        ("doi:not-a-real-doi", "doi:not-a-real-doi"),
        ("DOI:not-a-real-doi", "doi:not-a-real-doi"),
        ("uRl:mixed-case-prefix", "url:mixed-case-prefix"),
        ("raw:raw-citation", "raw:raw-citation"),
        ("no-prefix", "raw:no-prefix"),
        ("no-prefix:but-colon", "raw:no-prefix:but-colon"),
    ],
)
def test_infer_citekey_prefix(citation, expect):
    assert infer_citekey_prefix(citation) == expect


@pytest.mark.parametrize(
    ["url", "citekey"],
    [
        ("https://www.doi.org/", "url:https://www.doi.org/",),
        (
            "https://www.doi.org/factsheets/Identifier_Interoper.html",
            "url:https://www.doi.org/factsheets/Identifier_Interoper.html",
        ),
        (
            "https://doi.org/10.1097%2F00004032-200403000-00012",
            "doi:10.1097/00004032-200403000-00012",
        ),
        ("http://dx.doi.org/10.7554/eLife.46574", "doi:10.7554/eLife.46574"),
        ("https://doi.org/10/b6vnmd#anchor", "doi:10/b6vnmd"),
        # ShortDOI URLs without `10/` prefix not yet supported`
        ("https://doi.org/b6vnmd", "url:https://doi.org/b6vnmd"),
        (
            "https://www.biorxiv.org/about-biorxiv",
            "url:https://www.biorxiv.org/about-biorxiv",
        ),
        ("https://sci-hub.tw/10.1038/nature19057", "doi:10.1038/nature19057"),
        ("https://www.biorxiv.org/content/10.1101/087619v3", "doi:10.1101/087619"),
        ("https://www.biorxiv.org/content/10.1101/087619v3.full", "doi:10.1101/087619"),
        (
            "https://www.biorxiv.org/content/early/2017/08/31/087619.full.pdf",
            "doi:10.1101/087619",
        ),
        (
            "https://www.biorxiv.org/content/10.1101/2019.12.11.872580v1",
            "doi:10.1101/2019.12.11.872580",
        ),
        (
            "https://www.biorxiv.org/content/10.1101/2019.12.11.872580v1.full.pdf+html",
            "doi:10.1101/2019.12.11.872580",
        ),
        (
            "https://www.biorxiv.org/content/10.1101/2019.12.11.872580v1.full.pdf",
            "doi:10.1101/2019.12.11.872580",
        ),
        ("https://www.ncbi.nlm.nih.gov", "url:https://www.ncbi.nlm.nih.gov"),
        (
            "https://www.ncbi.nlm.nih.gov/pubmed",
            "url:https://www.ncbi.nlm.nih.gov/pubmed",
        ),
        ("https://www.ncbi.nlm.nih.gov/pubmed/31233491", "pmid:31233491"),
        ("https://www.ncbi.nlm.nih.gov/pmc/", "url:https://www.ncbi.nlm.nih.gov/pmc/"),
        (
            "https://www.ncbi.nlm.nih.gov/pmc/about/intro/",
            "url:https://www.ncbi.nlm.nih.gov/pmc/about/intro/",
        ),
        ("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4304851/", "pmcid:PMC4304851"),
        (
            "https://www.wikidata.org/wiki/Wikidata:Main_Page",
            "url:https://www.wikidata.org/wiki/Wikidata:Main_Page",
        ),
        ("https://www.wikidata.org/wiki/Q50051684", "wikidata:Q50051684"),
        ("https://arxiv.org/", "url:https://arxiv.org/"),
        (
            "https://arxiv.org/list/q-fin/recent",
            "url:https://arxiv.org/list/q-fin/recent",
        ),
        ("https://arxiv.org/abs/1912.03529v1", "arxiv:1912.03529v1"),
        ("https://arxiv.org/pdf/1912.03529v1.pdf", "arxiv:1912.03529v1"),
        ("https://arxiv.org/ps/1912.03529v1", "arxiv:1912.03529v1"),
        ("https://arxiv.org/abs/math.GT/0309136", "arxiv:math.GT/0309136"),
        ("https://arxiv.org/abs/hep-th/9305059", "arxiv:hep-th/9305059"),
        ("https://arxiv.org/pdf/hep-th/9305059.pdf", "arxiv:hep-th/9305059"),
    ],
)
def test_url_to_citekey(url, citekey):
    assert url_to_citekey(url) == citekey
