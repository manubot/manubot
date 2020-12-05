from typing import Any, Dict

from .handlers import Handler


class Handler_Wikidata(Handler):
    prefixes = ["wikidata"]
    standard_prefix = "wikidata"
    accession_pattern = r"Q[0-9]+"

    def inspect(self, citekey):
        """
        https://www.wikidata.org/wiki/Wikidata:Identifiers
        """
        accession = citekey.accession
        if not accession.startswith("Q"):
            return "Wikidata item IDs must start with 'Q'."
        elif not self._get_pattern().fullmatch(accession):
            return (
                "Accession does not conform to the Wikidata regex. "
                "Double check the entity ID."
            )

    def get_csl_item(self, citekey):
        return get_wikidata_csl_item(citekey.standard_accession)


def get_wikidata_csl_item(identifier: str) -> Dict[str, Any]:
    """
    Get a CSL JSON item with the citation metadata for a Wikidata item.
    identifier should be a Wikidata item ID corresponding to a citeable
    work, such as Q50051684.
    """
    url = f"https://www.wikidata.org/wiki/{identifier}"
    from manubot.cite.url import get_url_csl_item_zotero

    csl_item = get_url_csl_item_zotero(url)
    if "DOI" in csl_item:
        csl_item["DOI"] = csl_item["DOI"].lower()
    if "URL" not in csl_item:
        csl_item["URL"] = url
    return csl_item
