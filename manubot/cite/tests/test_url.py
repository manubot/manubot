import pytest

from manubot.cite.url import get_url_csl_item_zotero


def test_get_url_csl_item_zotero_nyt():
    """
    This command creates two translation-server queries. The first query is
    equivalent to:
    ```
    curl --verbose \
      --header "Content-Type: text/plain" \
      --data 'https://nyti.ms/1NuB0WJ' \
      'https://translate.manubot.org/web'
    ```
    """
    url = "https://nyti.ms/1NuB0WJ"
    csl_item = get_url_csl_item_zotero(url)
    assert (
        csl_item["title"] == "Unraveling the Ties of Altitude, Oxygen and Lung Cancer"
    )
    assert csl_item["author"][0]["family"] == "Johnson"


def test_get_url_csl_item_zotero_manubot():
    """
    This command creates two translation-server queries. The first query is
    equivalent to:
    ```
    curl --verbose \
      --header "Content-Type: text/plain" \
      --data 'https://greenelab.github.io/meta-review/v/0770300e1d5490a1ae8ff3a85ddca2cdc4ae0613/' \
      'https://translate.manubot.org/web'
    ```
    """
    url = "https://greenelab.github.io/meta-review/v/0770300e1d5490a1ae8ff3a85ddca2cdc4ae0613/"
    csl_item = get_url_csl_item_zotero(url)
    assert csl_item["title"] == "Open collaborative writing with Manubot"
    assert csl_item["author"][1]["family"] == "Slochower"
    # Zotero CSL exporter returns mixed string/int date-parts
    # https://github.com/zotero/zotero/issues/1603
    assert [int(x) for x in csl_item["issued"]["date-parts"][0]] == [2018, 12, 18]


@pytest.mark.skip(
    reason="test intermittently fails as metadata varies between two states"
)
def test_get_url_csl_item_zotero_github():
    """
    This command creates two translation-server queries. The first query is
    equivalent to:
    ```
    curl --verbose \
      --header "Content-Type: text/plain" \
      --data 'https://github.com/pandas-dev/pandas/tree/d5e5bf761092c59eeb9b8750f05f2bc29fb45927' \
      'https://translate.manubot.org/web'
    ```

    Note: this test may have temporary failures, due to performance of
          translation-server. It seems that sometimes translation-server
          returns a different title for the same URL. A real mystery.

    See also:
        https://github.com/manubot/manubot/pull/139#discussion_r328703233

    Proposed action:
        Probably should inquire upstream or change the test.
    """
    url = "https://github.com/pandas-dev/pandas/tree/d5e5bf761092c59eeb9b8750f05f2bc29fb45927"
    csl_item = get_url_csl_item_zotero(url)
    # FIXME: arbitraryly, csl_item['abstract'], and not csl_item['title'] contains the title.
    assert csl_item["title"].startswith("Flexible and powerful data analysis")
    assert csl_item["source"] == "GitHub"
