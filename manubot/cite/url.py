import json
import logging
import re
from typing import Any, Dict

from .handlers import Handler

CSLItem = Dict[str, Any]


class Handler_URL(Handler):

    standard_prefix = "url"

    prefixes = [
        "url",
        "http",
        "https",
    ]

    def standardize_prefix_accession(self, accession):
        if self.prefix_lower != "url":
            accession = f"{self.prefix_lower}:{accession}"
        return self.standard_prefix, accession

    def get_csl_item(self, citekey):
        return get_url_csl_item(citekey.standard_accession)


def get_url_csl_item(url: str) -> CSLItem:
    """
    Get csl_item for a URL trying a sequence of strategies.

    This function uses a list of CSL JSON Item metadata retrievers, specified
    by the module-level variable `url_retrievers`. The methods are attempted
    in order, with this function returning the metadata from the first
    non-failing method.
    """
    for retriever in url_retrievers:
        try:
            return retriever(url)
        except Exception as error:
            logging.warning(
                f"Error in {retriever.__name__} for {url} "
                f"due to a {error.__class__.__name__}:\n{error}"
            )
            logging.info(error, exc_info=True)
    raise Exception(f"all get_url_csl_item methods failed for {url}")


def get_url_csl_item_zotero(url: str) -> CSLItem:
    """
    Use Zotero's translation-server to generate a CSL Item for the specified URL.
    """
    from manubot.cite.zotero import export_as_csl, web_query

    zotero_data = web_query(url)
    csl_data = export_as_csl(zotero_data)
    (csl_item,) = csl_data
    if not csl_item.get("URL"):
        # some Zotero translators don't set URL. https://github.com/manubot/manubot/issues/244
        csl_item["URL"] = url
    return csl_item


def get_url_csl_item_greycite(url: str) -> CSLItem:
    """
    Uses Greycite which has experiened uptime problems in the past.
    API calls seem to take at least 15 seconds. Browser requests are much
    faster. Setting header did not have an effect. Consider mimicking browser
    using selenium.

    More information on Greycite at:
    http://greycite.knowledgeblog.org/
    http://knowledgeblog.org/greycite
    https://arxiv.org/abs/1304.7151
    https://git.io/v9N2C
    """
    import requests

    from manubot.util import get_manubot_user_agent

    headers = {
        "Connection": "close",  # https://github.com/kennethreitz/requests/issues/4023
        "User-Agent": get_manubot_user_agent(),
    }
    response = requests.get(
        "http://greycite.knowledgeblog.org/json", params={"uri": url}, headers=headers
    )
    response.raise_for_status()
    # Some Greycite responses were valid JSON besides for an error appended
    # like "<p>*** Date set from uri<p>" or "<p>*** fetch error : 404<p>".
    pattern = re.compile(r"<p>\*\*\*.*<p>")
    text = pattern.sub("", response.text)
    csl_item = json.loads(text)
    csl_item["type"] = "webpage"
    return csl_item


def get_url_csl_item_manual(url: str) -> CSLItem:
    """
    Manually create csl_item for a URL.
    """
    return {"URL": url, "type": "webpage"}


url_retrievers = [
    get_url_csl_item_zotero,
    get_url_csl_item_greycite,
    get_url_csl_item_manual,
]
