import collections
import json
import logging


def get_isbn_citeproc(isbn):
    return get_isbn_citeproc_citoid(isbn)


def get_isbn_citeproc_isbnlib(isbn):
    """
    Generate CSL JSON Data for an ISBN using isbnlib.
    """
    import isbnlib
    metadata = isbnlib.meta(isbn, cache=None)
    csl_json = isbnlib.registry.bibformatters['csl'](metadata)
    csl_data = json.loads(csl_json)
    return csl_data


def get_isbn_citeproc_citoid(isbn):
    """
    Return CSL JSON Data for an ISBN using the Wikipedia Citoid API.
    https://en.wikipedia.org/api/rest_v1/#!/Citation/getCitation
    """
    import isbnlib
    import requests
    isbn = isbnlib.to_isbn13(isbn)
    url = f'https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/{isbn}'
    response = requests.get(url)
    mediawiki, = response.json()
    csl_data = collections.OrderedDict()
    csl_data['type'] = mediawiki.get('itemType', 'book')
    if 'title' in mediawiki:
        csl_data['title'] = mediawiki['title']
    if 'date' in mediawiki:
        try:
            date_parts = [int(x) for x in mediawiki['date'].split('-')]
            csl_data['issued'] = {'date-parts': [date_parts]}
        except Exception:
            logging.warning(
                f'Error parsing issued date for ISBN {isbn}.\n'
                f'Metadata retrieved by get_isbn_citeproc_citoid from {url}\n'
                f'The following value was returned for the date field:\n'
                f"{mediawiki['date']}"
            )
    if 'publisher' in mediawiki:
        csl_data['publisher'] = mediawiki['publisher']
    if 'place' in mediawiki:
        csl_data['publisher-place'] = mediawiki['place']
    if 'volume' in mediawiki:
        csl_data['volume'] = mediawiki['volume']
    if 'edition' in mediawiki:
        csl_data['edition'] = mediawiki['edition']
    if 'abstractNote' in mediawiki:
        csl_data['abstract'] = mediawiki['abstractNote']
    csl_data['ISBN'] = isbn
    if 'source' in mediawiki:
        csl_data['source'] = mediawiki['source'][0]
    if 'url' in mediawiki:
        csl_data['URL'] = mediawiki['url']
    return csl_data
