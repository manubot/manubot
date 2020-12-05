"""
Methods to interact with a Zotero translation-server.
https://github.com/zotero/translation-server

The Manubot team currently hosts a public translation server at
https://translate.manubot.org. More information on this instance at
https://github.com/manubot/manubot/issues/82.
"""

import json
import logging
from typing import Any, Dict, List

import requests

from manubot.util import get_manubot_user_agent, is_http_url

ZoteroRecord = Dict[str, Any]
ZoteroData = List[ZoteroRecord]
# for the purposes of this module, the CSL Items and Zotero Data have the same type
CSLItem = ZoteroRecord
CSLItems = ZoteroData

base_url = "https://translate.manubot.org"
"""URL that provides access to the Zotero translation-server API"""


def web_query(url: str) -> ZoteroData:
    """
    Return Zotero citation metadata for a URL as a list containing a single element that
    is a dictionary with the URL's metadata.
    """
    headers = {"User-Agent": get_manubot_user_agent(), "Content-Type": "text/plain"}
    params = {"single": 1}
    api_url = f"{base_url}/web"
    response = requests.post(api_url, params=params, headers=headers, data=str(url))
    try:
        zotero_data = response.json()
    except Exception as error:
        logging.warning(
            f"Error parsing web_query output as JSON for {url}:\n{response.text}"
        )
        raise error
    if response.status_code == 300:
        # When single=1 is specified, multiple results should never be returned
        logging.warning(
            f"web_query returned multiple results for {url}:\n"
            + json.dumps(zotero_data, indent=2)
        )
        raise ValueError(f"multiple results for {url}")
    zotero_data = _passthrough_zotero_data(zotero_data)
    return zotero_data


def search_query(identifier: str) -> ZoteroData:
    """
    Retrive Zotero metadata for a DOI, ISBN, PMID, or arXiv ID.
    Example usage:

    ```shell
    curl --silent \
      --data '10.2307/4486062' \
      --header 'Content-Type: text/plain' \
      http://127.0.0.1:1969/search
    ```
    """
    api_url = f"{base_url}/search"
    headers = {"User-Agent": get_manubot_user_agent(), "Content-Type": "text/plain"}
    response = requests.post(api_url, headers=headers, data=str(identifier))
    try:
        zotero_data = response.json()
    except Exception as error:
        logging.warning(
            f"Error parsing search_query output as JSON for {identifier}:\n{response.text}"
        )
        raise error
    zotero_data = _passthrough_zotero_data(zotero_data)
    return zotero_data


def _passthrough_zotero_data(zotero_data: ZoteroData) -> ZoteroData:
    """
    Address known issues with Zotero metadata.
    Assumes zotero data should contain a single bibliographic record.
    """
    if not isinstance(zotero_data, list):
        raise ValueError("_passthrough_zotero_data: zotero_data should be a list")
    if len(zotero_data) > 1:
        # Sometimes translation-server creates multiple data items for a single record.
        # If so, keep only the parent item, and remove child items (such as notes).
        # https://github.com/zotero/translation-server/issues/67
        zotero_data = zotero_data[:1]
    return zotero_data


def export_as_csl(zotero_data: ZoteroData) -> CSLItems:
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
    api_url = f"{base_url}/export"
    params = {"format": "csljson"}
    headers = {"User-Agent": get_manubot_user_agent()}
    response = requests.post(api_url, params=params, headers=headers, json=zotero_data)
    if not response.ok:
        message = f"export_as_csl: translation-server returned status code {response.status_code}"
        logging.warning(f"{message} with the following output:\n{response.text}")
        raise requests.HTTPError(message)
    try:
        csl_items = response.json()
    except Exception as error:
        logging.warning(f"Error parsing export_as_csl output as JSON:\n{response.text}")
        raise error
    return csl_items


def get_csl_item(identifier: str) -> CSLItem:
    """
    Use a translation-server search query followed by an export query
    to return a CSL Item (the first & only record of the returned CSL JSON).
    """
    zotero_data = search_query(identifier)
    csl_items = export_as_csl(zotero_data)
    (csl_item,) = csl_items
    return csl_item


def search_or_web_query(identifier: str) -> ZoteroData:
    """
    Detect whether `identifier` is a URL. If so,
    retrieve zotero metadata using a /web query.
    Otherwise, retrieve zotero metadata using a /search query.
    """
    if is_http_url(identifier):
        zotero_data = web_query(identifier)
    else:
        zotero_data = search_query(identifier)
    return zotero_data
