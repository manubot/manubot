import json
import logging
import urllib.request

import requests

from manubot.cite.pubmed import get_pubmed_ids_for_doi
from manubot.util import get_manubot_user_agent


def expand_short_doi(short_doi):
    """
    Convert a shortDOI to a regular DOI.
    """
    if not short_doi.startswith('10/'):
        raise ValueError(f'shortDOIs start with `10/`, but expand_short_doi received: {short_doi}')
    url = f'https://doi.org/api/handles/{short_doi.lower()}'
    params = {
        "type": "HS_ALIAS",
    }
    response = requests.get(url, params=params)
    # response documentation at https://www.handle.net/proxy_servlet.html
    results = response.json()
    response_code = results.get('responseCode')  # Handle protocol response code
    if response_code == 100:
        raise ValueError(f'Handle not found. Double check short_doi: {short_doi}')
    if response_code == 200:
        raise ValueError(f'HS_ALIAS values not found. Double check short_doi: {short_doi}')
    if response_code != 1:
        raise ValueError(f'Error response code of {response_code} returned by {response.url}')
    values = results.get('values', [])
    for value in values:
        if value.get('type') == 'HS_ALIAS':
            doi = value['data']['value']
            return doi.lower()
    raise RuntimeError(
        f'HS_ALIAS value not found by expand_short_doi("{short_doi}")\n'
        f'The following JSON was retrieved from {response.url}:\n'
        + json.dumps(results, indent=2)
    )


def get_short_doi_url(doi):
    """
    Get the shortDOI URL for a DOI.
    """
    quoted_doi = urllib.request.quote(doi)
    url = 'http://shortdoi.org/{}?format=json'.format(quoted_doi)
    headers = {
        'User-Agent': get_manubot_user_agent(),
    }
    try:
        response = requests.get(url, headers=headers).json()
        short_doi = response['ShortDOI']
        short_url = 'https://doi.org/' + short_doi[3:]  # Remove "10/" prefix
        return short_url
    except Exception:
        logging.warning(f'shortDOI lookup failed for {doi}', exc_info=True)
        return None


def get_doi_citeproc(doi):
    """
    Use Content Negotioation (http://citation.crosscite.org/docs.html) to
    retrieve the citeproc JSON citation for a DOI.
    """
    url = 'https://doi.org/' + urllib.request.quote(doi)
    header = {
        'Accept': 'application/vnd.citationstyles.csl+json',
        'User-Agent': get_manubot_user_agent(),
    }
    response = requests.get(url, headers=header)
    try:
        citeproc = response.json()
    except Exception as error:
        logging.error(f'Error fetching metadata for doi:{doi}.\n'
                      f'Invalid response from {response.url}:\n{response.text}')
        raise error
    citeproc['URL'] = f'https://doi.org/{doi}'
    short_doi_url = get_short_doi_url(doi)
    if short_doi_url:
        citeproc['URL'] = short_doi_url
    try:
        citeproc.update(get_pubmed_ids_for_doi(doi))
    except Exception:
        logging.warning(f'Error calling get_pubmed_ids_for_doi for {doi}', exc_info=True)
    return citeproc
