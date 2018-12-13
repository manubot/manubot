from manubot.cite.url import get_url_citeproc_zotero


def test_get_url_citeproc_zotero():
    url = 'https://nyti.ms/1NuB0WJ'
    csl_item = get_url_citeproc_zotero(url)
    assert csl_item['title'] == 'Unraveling the Ties of Altitude, Oxygen and Lung Cancer'
    assert csl_item['author'][0]['family'] == 'Johnson'
