import pytest

from manubot.cite.zotero import (
    web_query,
    search_query,
    export_as_csl
)


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
    url = 'https://bigthink.com/neurobonkers/a-pirate-bay-for-science'
    zotero_data = web_query(url)
    assert isinstance(zotero_data, list)
    assert len(zotero_data) == 1
    assert zotero_data[0]['title'] == "Meet the Robin Hood of Science"


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
    assert csl_item['title'] == "Meet the Robin Hood of Science"
    assert csl_item['container-title'] == 'Big Think'


def test_web_query_fails_with_multiple_results():
    url = 'https://www.ncbi.nlm.nih.gov/pubmed/?term=sci-hub%5Btitle%5D'
    with pytest.raises(ValueError, match='multiple results'):
        web_query(url)


def test_search_query():
    """
    The translation-server search endpoint can be tested via curl:
    ```
    curl \
      --header "Content-Type: text/plain" \
      --data 'isbn:9781339919881' \
      'https://translate.manubot.org/search'
    ```
    """
    identifier = 'isbn:9781339919881'
    zotero_data = search_query(identifier)
    assert zotero_data[0]['title'].startswith('The hetnet awakens')
