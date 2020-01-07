def get_wikidata_csl_item(identifier):
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
