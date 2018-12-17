from manubot.cite.url import get_url_citeproc_zotero


def test_get_url_citeproc_zotero():
    """
    This command creates two translation-server queries, which can be
    mimmicked via curl:
    ```
    curl --verbose \
      --header "Content-Type: text/plain" \
      --data 'https://nyti.ms/1NuB0WJ' \
      'https://translate.manubot.org/web'
    ```
    """
    url = 'https://nyti.ms/1NuB0WJ'
    csl_item = get_url_citeproc_zotero(url)
    assert csl_item['title'] == 'Unraveling the Ties of Altitude, Oxygen and Lung Cancer'
    assert csl_item['author'][0]['family'] == 'Johnson'
