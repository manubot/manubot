import pytest

from manubot.cite.zotero import web_query, search_query, export_as_csl


def test_web_query():
    """
    The translation-server web endpoint can be tested via curl:
    ```
    curl \
      --header "Content-Type: text/plain" \
      --data 'https://bigthink.com/neurobonkers/a-pirate-bay-for-science' \
      'https://translate.manubot.org/web'
    ```
    An outdated installation of translation-server caused the web query for this
    URL to be extraordinarily slow but has now been fixed. See
    https://github.com/zotero/translation-server/issues/63
    """
    url = "https://bigthink.com/neurobonkers/a-pirate-bay-for-science"
    zotero_data = web_query(url)
    assert isinstance(zotero_data, list)
    assert len(zotero_data) == 1
    assert zotero_data[0]["title"].startswith("Meet the Robin Hood of Science")


def test_export_as_csl():
    """
    CSL export can be tested via curl:
    ```
    curl \
      --header "Content-Type: application/json" \
      --data '[{"key": "IN22XN53", "itemType": "webpage", "date": "2016-02-09T20:12:00"}]' \
      'https://translate.manubot.org/export?format=csljson'
    ```
    """
    zotero_data = [
        {
            "key": "IN22XN53",
            "version": 0,
            "itemType": "webpage",
            "creators": [],
            "tags": [],
            "title": "Meet the Robin Hood of Science",
            "websiteTitle": "Big Think",
            "date": "2016-02-09T20:12:00",
            "url": "https://bigthink.com/neurobonkers/a-pirate-bay-for-science",
            "abstractNote": "How one researcher created a pirate bay for science more powerful than even libraries at top universities.",
            "language": "en",
            "accessDate": "2018-12-06T20:10:14Z",
        }
    ]
    csl_item = export_as_csl(zotero_data)[0]
    assert csl_item["title"] == "Meet the Robin Hood of Science"
    assert csl_item["container-title"] == "Big Think"


def test_web_query_returns_single_result_legacy_manubot_url():
    """
    Check that single=1 is specified for web queries. Without this, Zotero
    can prefer translators that return multiple choices. This occurs with legacy
    Manubot mansucripts, which get assigned the DOI translator as top priority.
    https://github.com/zotero/translation-server/issues/65
    ```
    curl \
      --header "Content-Type: text/plain" \
      --data 'https://greenelab.github.io/scihub-manuscript/v/cfe599e25405d38092bf972b6ea1c9e0dcf3deb9/' \
      'https://translate.manubot.org/web?single=1'
    ```
    """
    url = "https://greenelab.github.io/scihub-manuscript/v/cfe599e25405d38092bf972b6ea1c9e0dcf3deb9/"
    zotero_metadata = web_query(url)
    assert isinstance(zotero_metadata, list)
    assert len(zotero_metadata) == 1
    (zotero_metadata,) = zotero_metadata
    assert (
        zotero_metadata["title"]
        == "Sci-Hub provides access to nearly all scholarly literature"
    )


def test_web_query_returns_single_result_pubmed_url():
    """
    See test_web_query_returns_single_result_legacy_manubot_url docstring.
    ```
    curl \
      --header "Content-Type: text/plain" \
      --data 'https://www.ncbi.nlm.nih.gov/pubmed/?term=sci-hub%5Btitle%5D' \
      'https://translate.manubot.org/web?single=1'
    ```
    """
    url = "https://www.ncbi.nlm.nih.gov/pubmed/?term=sci-hub%5Btitle%5D"
    zotero_metadata = web_query(url)
    assert isinstance(zotero_metadata, list)
    assert len(zotero_metadata) == 1
    (zotero_metadata,) = zotero_metadata
    assert zotero_metadata["title"] == "sci-hub[title] - PubMed - NCBI"


def test_search_query_isbn():
    """
    The translation-server search endpoint can be tested via curl:
    ```
    curl \
      --header "Content-Type: text/plain" \
      --data 'isbn:9781339919881' \
      'https://translate.manubot.org/search'
    ```
    """
    identifier = "isbn:9781339919881"
    zotero_data = search_query(identifier)
    assert zotero_data[0]["title"].startswith("The hetnet awakens")


def test_search_query_arxiv():
    """
    Test citing https://arxiv.org/abs/1604.05363v1
    The translation-server search endpoint can be tested via curl:
    ```
    curl --verbose \
      --header "Content-Type: text/plain" \
      --data 'arxiv:1604.05363v1' \
      'https://translate.manubot.org/search'
    ```
    """
    identifier = "arxiv:1604.05363v1"
    zotero_data = search_query(identifier)
    assert (
        zotero_data[0]["title"]
        == "Comparing Published Scientific Journal Articles to Their Pre-print Versions"
    )
    assert zotero_data[0]["creators"][-1]["firstName"] == "Todd"
    assert zotero_data[0]["date"] == "2016-04-18"


@pytest.mark.parametrize(
    "identifier",
    [
        "30571677",  # https://www.ncbi.nlm.nih.gov/pubmed/30571677
        "doi:10.1371/journal.pcbi.1006561",  # https://doi.org/10.1371/journal.pcbi.1006561
    ],
)
def test_search_query(identifier):
    """
    The translation-server search endpoint can be tested via curl:
    ```
    curl --verbose \
      --header "Content-Type: text/plain" \
      --data '30571677' \
      'https://translate.manubot.org/search'
    ```
    translation-server does not support PMIDs with a `pmid:` prefix.
    https://github.com/zotero/translation-server/issues/71
    """
    zotero_data = search_query(identifier)
    assert zotero_data[0]["title"].startswith(
        "Ten simple rules for documenting scientific software"
    )
    assert zotero_data[0]["creators"][0]["lastName"] == "Lee"
