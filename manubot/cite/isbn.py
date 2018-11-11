import json


def get_isbn_citeproc(isbn):
    return get_isbn_citeproc_isbnlib(isbn)


def get_isbn_citeproc_isbnlib(isbn):
    import isbnlib
    metadata = isbnlib.meta(isbn, cache=None)
    csl_json = isbnlib.registry.bibformatters['csl'](metadata)
    csl_data = json.loads(csl_json)
    return csl_data


def get_isbn_citeproc_citoid(isbn):
    """
    https://en.wikipedia.org/api/rest_v1/#!/Citation/getCitation
    """
    raise NotImplementedError
