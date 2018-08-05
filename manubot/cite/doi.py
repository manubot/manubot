import logging
import urllib.request

import requests


def get_short_doi_url(doi):
    """
    Get the shortDOI URL for a DOI.
    """
    quoted_doi = urllib.request.quote(doi)
    url = 'http://shortdoi.org/{}?format=json'.format(quoted_doi)
    try:
        response = requests.get(url).json()
        short_doi = response['ShortDOI']
        short_doi = short_doi[3:]  # Remove "10/" prefix
        short_url = 'https://doi.org/' + short_doi
        return short_url
    except Exception:
        logging.exception(f'shortDOI lookup failed for {doi}')
        return None


def get_doi_citeproc(doi):
    """
    Use Content Negotioation (http://citation.crosscite.org/docs.html) to
    retrieve the citeproc JSON citation for a DOI.
    """
    url = 'https://doi.org/' + urllib.request.quote(doi)
    header = {
        'Accept': 'application/vnd.citationstyles.csl+json',
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
        citeproc['short_url'] = short_doi_url
    return citeproc
