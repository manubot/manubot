def get_wikidata_citeproc(identifier):
    """
    Get a CSL JSON item with the citation metadata for a Wikidata item.
    identifier should be a Wikidata item ID corresponding to a citeable
    work, such as Q50051684.
    """
    url = f'https://www.wikidata.org/wiki/{identifier}'
    from manubot.cite.url import get_url_citeproc_zotero
    csl_item = get_url_citeproc_zotero(url)
    if not 'URL' in csl_item:
        csl_item['URL'] = url
    return csl_item


if __name__ == '__main__':
    import json
    identifier = 'Q50051684'
    csl_json = get_wikidata_citeproc(identifier)
    print(json.dumps(csl_json, indent=2))
