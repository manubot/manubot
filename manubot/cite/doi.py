import json
import logging
import urllib.parse
import urllib.request
from typing import Any, Callable, Optional

import requests

from manubot.util import get_manubot_user_agent

from .handlers import Handler
from .pubmed import get_pubmed_ids_for_doi


class Handler_DOI(Handler):

    standard_prefix = "doi"
    prefixes = [
        "doi",
        "shortdoi",
    ]
    accession_pattern = r"10\.[0-9]{4,9}/\S+"
    shortdoi_pattern = r"10/[a-zA-Z0-9]+"

    def inspect(self, citekey):
        identifier = citekey.accession
        if identifier.startswith("10."):
            # https://www.crossref.org/blog/dois-and-matching-regular-expressions/
            if not self._get_pattern().fullmatch(identifier):
                return (
                    "Identifier does not conform to the DOI regex. "
                    "Double check the DOI."
                )
        elif identifier.startswith("10/"):
            # shortDOI, see http://shortdoi.org
            if not self._get_pattern("shortdoi_pattern").fullmatch(identifier):
                return (
                    "Identifier does not conform to the shortDOI regex. "
                    "Double check the shortDOI."
                )
        else:
            return "DOIs must start with '10.' (or '10/' for shortDOIs)."

    def standardize_prefix_accession(self, accession):
        if accession.startswith("10/"):
            try:
                accession = expand_short_doi(accession)
            except Exception as error:
                # If DOI shortening fails, return the unshortened DOI.
                # DOI metadata lookup will eventually fail somewhere with
                # appropriate error handling, as opposed to here.
                logging.error(
                    f"Error in expand_short_doi for {accession} "
                    f"due to a {error.__class__.__name__}:\n{error}"
                )
                logging.info(error, exc_info=True)
        accession = accession.lower()
        return self.standard_prefix, accession

    def get_csl_item(self, citekey):
        return get_doi_csl_item(citekey.standard_accession)


def expand_short_doi(short_doi: str) -> str:
    """
    Convert a shortDOI to a regular DOI.
    """
    if not short_doi.startswith("10/"):
        raise ValueError(
            f"shortDOIs start with `10/`, but expand_short_doi received: {short_doi}"
        )
    url = f"https://doi.org/api/handles/{short_doi.lower()}"
    params = {"type": "HS_ALIAS"}
    response = requests.get(url, params=params)
    # response documentation at https://www.handle.net/proxy_servlet.html
    results = response.json()
    response_code = results.get("responseCode")  # Handle protocol response code
    if response_code == 100:
        raise ValueError(f"Handle not found. Double check short_doi: {short_doi}")
    if response_code == 200:
        raise ValueError(
            f"HS_ALIAS values not found. Double check short_doi: {short_doi}"
        )
    if response_code != 1:
        raise ValueError(
            f"Error response code of {response_code} returned by {response.url}"
        )
    values = results.get("values", [])
    for value in values:
        if value.get("type") == "HS_ALIAS":
            doi = value["data"]["value"]
            return doi.lower()
    raise RuntimeError(
        f'HS_ALIAS value not found by expand_short_doi("{short_doi}")\n'
        f"The following JSON was retrieved from {response.url}:\n"
        + json.dumps(results, indent=2)
    )


def get_short_doi_url(doi: str) -> Optional[str]:
    """
    Get the shortDOI URL for a DOI.
    """
    quoted_doi = urllib.request.quote(doi)
    url = f"http://shortdoi.org/{quoted_doi}?format=json"
    headers = {"User-Agent": get_manubot_user_agent()}
    try:
        response = requests.get(url, headers=headers).json()
        short_doi = response["ShortDOI"]
        short_url = "https://doi.org/" + short_doi[3:]  # Remove "10/" prefix
        return short_url
    except Exception:
        logging.warning(f"shortDOI lookup failed for {doi}", exc_info=True)
        return None


content_negotiation_url_datacite: str = "https://data.crosscite.org"
content_negotiation_url_default: str = "https://doi.org"


def _get_doi_csl_item_negotiation(doi: str, content_negotiation_url: str):
    """
    Use Content Negotiation to retrieve the CSL Item metadata for a DOI.

    content_negotiation_url: base URL to use for content negotiation.
    Options include:
    1. The DataCite CN service <https://data.crosscite.org>
       Documented at <https://support.datacite.org/docs/datacite-content-resolver>
    2. The doi.org CN service <https://doi.org/>
       Documented at <https://citation.crosscite.org/docs.html>
    """
    url = urllib.parse.urljoin(content_negotiation_url, urllib.request.quote(doi))
    header = {
        "Accept": "application/vnd.citationstyles.csl+json",
        "User-Agent": get_manubot_user_agent(),
    }
    response = requests.get(url, headers=header)
    try:
        return response.json()
    except Exception as error:
        logging.error(
            f"Error fetching metadata for doi:{doi}.\n"
            f"Invalid response from {response.url}:\n{response.text}"
        )
        raise error


def get_doi_csl_item_datacite(doi: str):
    """
    As of 2022-01, the DataCite Content Negotiation restricted
    service to just DataCite DOIs, and began returning 404s for Crossref DOIs.
    https://github.com/crosscite/content-negotiation/issues/104
    """
    return _get_doi_csl_item_negotiation(doi, content_negotiation_url_datacite)


def get_doi_csl_item_default(doi: str):
    """
    doi.org content negotiation redirects to the content negotiation service of
    the Registration Agency, e.g. Crossref or DataCite.
    https://github.com/crosscite/content-negotiation/issues/104
    """
    return _get_doi_csl_item_negotiation(doi, content_negotiation_url_default)


def get_doi_csl_item_zotero(doi: str):
    """
    Generate CSL JSON Data for a DOI using Zotero's translation-server.
    """
    from manubot.cite.zotero import get_csl_item

    return get_csl_item(f"doi:{doi}")


def get_doi_csl_item_url(doi: str):
    """
    Generate CSL JSON Data for a DOI using Zotero's translation-server.
    This function converts the DOI to a URL that presumably resolves to the publisher's site.
    Zotero resolves and scrapes data from the resulting webpage.
    """
    from manubot.cite.url import get_url_csl_item_zotero

    return get_url_csl_item_zotero(f"https://doi.org/{doi}")


def augment_get_doi_csl_item(function: Callable[..., Any]):
    """
    Decorator providing edits to the csl_item returned by a get_doi_csl_item_* function.
    """

    def wrapper(doi: str):
        doi = doi.lower()
        csl_item = function(doi)
        csl_item["DOI"] = doi
        csl_item["URL"] = f"https://doi.org/{doi}"
        short_doi_url = get_short_doi_url(doi)
        if short_doi_url:
            csl_item["URL"] = short_doi_url
        try:
            csl_item.update(get_pubmed_ids_for_doi(doi))
        except Exception:
            logging.warning(
                f"Error calling get_pubmed_ids_for_doi for {doi}", exc_info=True
            )
        return csl_item

    return wrapper


@augment_get_doi_csl_item
def get_doi_csl_item(doi: str):
    """
    Generate CSL JSON Data for an DOI.

    This function uses a list of CSL JSON Item metadata retrievers, specified
    by the module-level variable `doi_retrievers`. The methods are attempted
    in order, with this function returning the metadata from the first
    non-failing method.
    """
    # FIXME: this function is repetitive with other get_*_csl_item functions.
    for retriever in doi_retrievers:
        try:
            return retriever(doi)
        except Exception as error:
            logging.warning(
                f"Error in {retriever.__name__} for {doi} "
                f"due to a {error.__class__.__name__}:\n{error}"
            )
            logging.info(error, exc_info=True)
    raise Exception(f"all get_doi_csl_item methods failed for {doi}")


doi_retrievers = [
    get_doi_csl_item_default,
    get_doi_csl_item_url,
    get_doi_csl_item_zotero,
]
"""
On retreiver ordering

1. get_doi_csl_item_default: try DOI metadata first as per the Registration Agency's Content Negotiation.
2. get_doi_csl_item_url: scrape data from the website where the DOI resolves.
3. get_doi_csl_item_zotero: use Zotero translation-server to get DOI metadata.
   Placed last since it's unlikely to work when get_doi_csl_item_default fails,
   since it also uses content negotiation.

get_doi_csl_item_datacite is not included because as of 2022-01 it only works for DataCite DOIs,
and get_doi_csl_item_default ends up redirecting to this endpoint for DataCite registered DOIs.
"""
