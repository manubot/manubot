import logging
import urllib.request

import requests

from manubot.cite.pubmed import get_pubmed_ids_for_doi
from manubot.util import get_manubot_user_agent


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
        short_doi = short_doi[3:]  # Remove "10/" prefix
        short_url = 'https://doi.org/' + short_doi
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
