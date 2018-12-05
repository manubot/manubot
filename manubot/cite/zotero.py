import requests

from manubot.util import get_manubot_user_agent

base_url = 'https://translate.manubot.org'


def web_query(url):
    """
    Return Zotero citation metadata for a URL
    """
    headers = {
        'User-Agent': get_manubot_user_agent(),
        'Content-Type': 'text/plain',
    }
    api_url = f'{base_url}/web'
    response = requests.post(api_url, headers=headers, data=str(url))
    return response.json()


def search_query(identifier):
    """
    Supports DOI, ISBN, PMID, arXiv ID.
    curl -d 10.2307/4486062 -H 'Content-Type: text/plain' http://127.0.0.1:1969/search
    """
    api_url = f'{base_url}/search'
    headers = {
        'User-Agent': get_manubot_user_agent(),
        'Content-Type': 'text/plain',
    }
    response = requests.post(api_url, headers=headers, data=str(identifier))
    return response.json()


def export_as_csl(zotero_data):
    """
    curl -d @items.json -H 'Content-Type: application/json' 'http://127.0.0.1:1969/export?format=bibtex'
    """
    api_url = f'{base_url}/export'
    params = {
        'format': 'csljson',
    }
    headers = {
        'User-Agent': get_manubot_user_agent(),
    }
    response = requests.post(api_url, params=params, headers=headers, json=zotero_data)
    csl_json = response.json()
    return csl_json

if __name__ == '__main__':
    import json
    data = web_query('http://docs.python-requests.org/en/master/user/quickstart/')
    print(json.dumps(data, indent=2))
    csl_json = export_as_csl(data)
    print(json.dumps(csl_json, indent=2))
