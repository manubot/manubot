import collections
import json
import logging
import re


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
    result = response.json()
    if isinstance(result, dict):
        if result['title'] == 'Not found.':
            raise KeyError(f'Metadata for ISBN {isbn} not found at {url}')
        else:
            raise Exception(
                f'Unable to extract CSL from JSON metadata for ISBN {isbn}:\n'
                f'{json.dumps(result.text)}'
            )
    mediawiki, = result
    csl_data = collections.OrderedDict()
    csl_data['type'] = mediawiki.get('itemType', 'book')
    if 'title' in mediawiki:
        csl_data['title'] = mediawiki['title']
    if 'date' in mediawiki:
        match = year_pattern.search(mediawiki['date'])
        if match:
            year = int(match.group())
            csl_data['issued'] = {'date-parts': [[year]]}
        else:
            logging.debug(
                f'get_isbn_citeproc_citoid: issue extracting date for ISBN {isbn}\n'
                f'metadata retrieved from {url}\n'
                f'unable to extract year from date field: {mediawiki["date"]}'
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


year_pattern = re.compile(r'[0-9]{4}')
