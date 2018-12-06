import json
import logging

import requests

from manubot.util import get_manubot_user_agent

base_url = 'https://translate.manubot.org'


def web_query(url):
    """
    Return Zotero citation metadata for a URL as a list containing a single element that
    is a dictionary with the URL's metadata.
    """
    headers = {
        'User-Agent': get_manubot_user_agent(),
        'Content-Type': 'text/plain',
    }
    api_url = f'{base_url}/web'
    response = requests.post(api_url, headers=headers, data=str(url))
    try:
        zotero_data = response.json()
    except Exception as error:
        logging.warning(f'Error parsing web_query output as JSON for {url}:\n{response.text}')
        raise error
    if response.status_code == 300:
        logging.warning(
            f'web_query returned multiple results for {url}:\n' +
            json.dumps(zotero_data, indent=2)
        )
        raise ValueError(f'multiple results for {url}')
    return zotero_data


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
    try:
        return response.json()
    except Exception as error:
        logging.warning(f'Error parsing search_query output as JSON for {identifier}:\n{response.text}')
        raise error


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
    try:
        csl_json = response.json()
    except Exception as error:
        logging.warning(f'Error parsing export_as_csl output as JSON:\n{response.text}')
        raise error
    return csl_json


if __name__ == '__main__':
    import json
    #data = web_query('http://docs.python-requests.org/en/master/user/quickstart/')
    url = 'https://www.ncbi.nlm.nih.gov/pubmed/?term=crispr'
    data = web_query(url)
    print(json.dumps(data, indent=2))
    csl_json = export_as_csl(data)
    print(json.dumps(csl_json, indent=2))
