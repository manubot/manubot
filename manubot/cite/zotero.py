"""
Methods to interact with a Zotero translation-server.
https://github.com/zotero/translation-server

The Manubot team currently hosts a public translation server at
https://translate.manubot.org. More information on this instance at
https://github.com/greenelab/manubot/issues/82.
"""

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
    params = {
        'single': 1,
    }
    api_url = f'{base_url}/web'
    response = requests.post(api_url, params=params, headers=headers, data=str(url))
    try:
        zotero_data = response.json()
    except Exception as error:
        logging.warning(f'Error parsing web_query output as JSON for {url}:\n{response.text}')
        raise error
    if response.status_code == 300:
        # When single=1 is specified, multiple results should never be returned
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
    Export Zotero JSON data to CSL JSON using a translation-server /export query.
    Performs a similar query to the following curl command:
    ```
    curl --verbose \
      --data @items.json \
      --header 'Content-Type: application/json' \
      'https://translate.manubot.org/export?format=csljson'
    ```
    """
    api_url = f'{base_url}/export'
    params = {
        'format': 'csljson',
    }
    headers = {
        'User-Agent': get_manubot_user_agent(),
    }
    response = requests.post(api_url, params=params, headers=headers, json=zotero_data)
    if not response.ok:
        message = f'export_as_csl: translation-server returned status code {response.status_code}'
        logging.warning(f'{message} with the following output:\n{response.text}')
        raise requests.HTTPError(message)
    try:
        csl_json = response.json()
    except Exception as error:
        logging.warning(f'Error parsing export_as_csl output as JSON:\n{response.text}')
        raise error
    return csl_json
