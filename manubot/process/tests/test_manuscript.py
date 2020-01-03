from manubot.process.manuscript import get_citekeys, update_manuscript_citekeys


def test_get_citekeys_1():
    text = """
    Sci-Hub has released article request records from its server logs, covering 165 days from September 2015 through February 2016 [@doi:10.1126/science.352.6285.508; @doi:10.1126/science.aaf5664; @doi:10.5061/dryad.q447c/1].
    We filtered for valid requests by excluding DOIs not included in our literature catalog and omitting requests that occurred before an article's publication date.

    Figure {@fig:citescore}B shows that articles from highly cited journals were visited much more frequently on average.

    @10.5061/bad_doi says blah but @url:https://www.courtlistener.com/docket/4355308/1/elsevier-inc-v-sci-hub/ disagrees.
    """
    citekeys = get_citekeys(text)
    expected = sorted(
        [
            "doi:10.1126/science.352.6285.508",
            "doi:10.1126/science.aaf5664",
            "doi:10.5061/dryad.q447c/1",
            "url:https://www.courtlistener.com/docket/4355308/1/elsevier-inc-v-sci-hub/",
        ]
    )
    assert citekeys == expected


def test_update_manuscript_citekeys():
    """
    Test that text does not get converted to:

    > our new Manubot tool [@cTN2TQIL-rootstock; @cTN2TQIL] for automating
    manuscript generation.

    See https://github.com/manubot/manubot/issues/9
    """
    string_to_id = {
        "url:https://github.com/manubot/manubot": "mNMayr3f",
        "url:https://github.com/greenelab/manubot-rootstock": "1B7Y2HVtw",
    }
    text = "our new Manubot tool [@url:https://github.com/greenelab/manubot-rootstock; @url:https://github.com/manubot/manubot] for automating manuscript generation."
    text = update_manuscript_citekeys(text, string_to_id)
    assert "[@1B7Y2HVtw; @mNMayr3f]" in text
