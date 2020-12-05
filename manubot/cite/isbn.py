import json
import logging
import re

from .handlers import Handler


class Handler_ISBN(Handler):

    standard_prefix = "isbn"

    prefixes = [
        "isbn",
    ]

    def inspect(self, citekey):
        import isbnlib

        fail = isbnlib.notisbn(citekey.accession, level="strict")
        if fail:
            return f"identifier violates the ISBN syntax according to isbnlib v{isbnlib.__version__}"

    def standardize_prefix_accession(self, accession):
        from isbnlib import to_isbn13

        accession = to_isbn13(accession)
        return self.standard_prefix, accession

    def get_csl_item(self, citekey):
        return get_isbn_csl_item(citekey.standard_accession)


def get_isbn_csl_item(isbn: str):
    """
    Generate CSL JSON Data for an ISBN. Converts all ISBNs to 13-digit format.

    This function uses a list of CSL JSON Item metadata retrievers, specified
    by the module-level variable `isbn_retrievers`. The methods are attempted
    in order, with this function returning the metadata from the first
    non-failing method.
    """
    import isbnlib

    isbn = isbnlib.to_isbn13(isbn)
    for retriever in isbn_retrievers:
        try:
            return retriever(isbn)
        except Exception as error:
            logging.warning(
                f"Error in {retriever.__name__} for {isbn} "
                f"due to a {error.__class__.__name__}:\n{error}"
            )
            logging.info(error, exc_info=True)
    raise Exception(f"all get_isbn_csl_item methods failed for {isbn}")


def get_isbn_csl_item_zotero(isbn: str):
    """
    Generate CSL JSON Data for an ISBN using Zotero's translation-server.
    """
    from manubot.cite.zotero import get_csl_item

    return get_csl_item(f"isbn:{isbn}")


def get_isbn_csl_item_citoid(isbn: str):
    """
    Return CSL JSON Data for an ISBN using the Wikipedia Citoid API.
    https://en.wikipedia.org/api/rest_v1/#!/Citation/getCitation
    """
    import requests

    from manubot.util import get_manubot_user_agent

    headers = {"User-Agent": get_manubot_user_agent()}
    url = f"https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/{isbn}"
    response = requests.get(url, headers=headers)
    result = response.json()
    if isinstance(result, dict):
        if result["title"] == "Not found.":
            raise KeyError(f"Metadata for ISBN {isbn} not found at {url}")
        else:
            raise Exception(
                f"Unable to extract CSL from JSON metadata for ISBN {isbn}:\n"
                f"{json.dumps(result.text)}"
            )
    (mediawiki,) = result
    csl_item = dict()
    csl_item["type"] = mediawiki.get("itemType", "book")
    if "title" in mediawiki:
        csl_item["title"] = mediawiki["title"]
    if "author" in mediawiki:
        csl_author = list()
        for last, first in mediawiki["author"]:
            csl_author.append({"given": first, "family": last})
        if csl_author:
            csl_item["author"] = csl_author
    if "date" in mediawiki:
        year_pattern = re.compile(r"[0-9]{4}")
        match = year_pattern.search(mediawiki["date"])
        if match:
            year = int(match.group())
            csl_item["issued"] = {"date-parts": [[year]]}
        else:
            logging.debug(
                f"get_isbn_csl_item_citoid: issue extracting date for ISBN {isbn}\n"
                f"metadata retrieved from {url}\n"
                f'unable to extract year from date field: {mediawiki["date"]}'
            )
    if "publisher" in mediawiki:
        csl_item["publisher"] = mediawiki["publisher"]
    if "place" in mediawiki:
        csl_item["publisher-place"] = mediawiki["place"]
    if "volume" in mediawiki:
        csl_item["volume"] = mediawiki["volume"]
    if "edition" in mediawiki:
        csl_item["edition"] = mediawiki["edition"]
    if "abstractNote" in mediawiki:
        csl_item["abstract"] = mediawiki["abstractNote"]
    csl_item["ISBN"] = isbn
    if "source" in mediawiki:
        csl_item["source"] = mediawiki["source"][0]
    if "url" in mediawiki:
        csl_item["URL"] = mediawiki["url"]
    return csl_item


def get_isbn_csl_item_isbnlib(isbn: str):
    """
    Generate CSL JSON Data for an ISBN using isbnlib.
    """
    import isbnlib

    metadata = isbnlib.meta(isbn)
    csl_json = isbnlib.registry.bibformatters["csl"](metadata)
    csl_data = json.loads(csl_json)
    return csl_data


isbn_retrievers = [
    get_isbn_csl_item_zotero,
    get_isbn_csl_item_citoid,
    get_isbn_csl_item_isbnlib,
]
