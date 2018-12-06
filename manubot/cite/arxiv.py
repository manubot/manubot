import collections
import logging
import re
import xml.etree.ElementTree

import requests

from manubot.util import get_manubot_user_agent


def get_arxiv_citeproc(arxiv_id):
    """
    Return citeproc item for an arXiv record.

    arxiv_id can be versioned, like `1512.00567v2`, or versionless, like
    `1512.00567`. If versionless, the arXiv API will return metadata for the
    latest version. Legacy IDs, such as `cond-mat/0703470v2`, are also
    supported.

    If arXiv has an associated DOI for the record, a warning is logged to
    alert the user that an alternative version of record exists.

    References:
    https://arxiv.org/help/api/index
    http://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html
    https://github.com/citation-style-language/schema/blob/master/csl-data.json
    """
    url = 'https://export.arxiv.org/api/query'
    params = {
        'id_list': arxiv_id,
        'max_results': 1,
    }
    headers = {
        'User-Agent': get_manubot_user_agent(),
    }
    response = requests.get(url, params, headers=headers)

    # XML namespace prefixes
    prefix = '{http://www.w3.org/2005/Atom}'
    alt_prefix = '{http://arxiv.org/schemas/atom}'

    # Parse XML
    xml_tree = xml.etree.ElementTree.fromstring(response.text)
    entry, = xml_tree.findall(prefix + 'entry')

    # Create dictionary for CSL Item
    csl_item = collections.OrderedDict()

    # Extract versioned arXiv ID
    url = entry.findtext(prefix + 'id')
    pattern = re.compile(r'arxiv.org/abs/(.+)')
    match = pattern.search(url)
    versioned_id = match.group(1)
    csl_item['number'] = versioned_id
    _, csl_item['version'] = versioned_id.rsplit('v', 1)
    csl_item['URL'] = 'https://arxiv.org/abs/' + versioned_id

    # Extrat CSL title field
    csl_item['title'] = entry.findtext(prefix + 'title')

    # Extract CSL date field
    published = entry.findtext(prefix + 'published')
    published, _ = published.split('T', 1)
    csl_item['issued'] = {'date-parts': [[int(x) for x in published.split('-')]]}

    # Extract authors
    authors = list()
    for elem in entry.findall(prefix + 'author'):
        name = elem.findtext(prefix + 'name')
        author = {'literal': name}
        authors.append(author)
    csl_item['author'] = authors

    # Set publisher to arXiv
    csl_item['container-title'] = 'arXiv'
    csl_item['publisher'] = 'arXiv'

    # Extract abstract
    abstract = entry.findtext(prefix + 'summary').strip()
    if abstract:
        csl_item['abstract'] = abstract

    # Check if the article has been published with a DOI
    DOI = entry.findtext('{http://arxiv.org/schemas/atom}doi')
    if DOI:
        csl_item['DOI'] = DOI
        journal_ref = entry.findtext(alt_prefix + 'journal_ref')
        msg = f'arXiv article {arxiv_id} published at https://doi.org/{DOI}'
        if journal_ref:
            msg += f' — {journal_ref}'
        logging.warning(msg)
    # Set CSL type to report for preprint
    csl_item['type'] = 'report'
    return csl_item
