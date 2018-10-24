"""
This file was derived from https://github.com/fnielsen/scholia/blob/d0184888559f68dafb8d63f105dbb09369438900/scholia/api.py.
The GPLv3 license was inherited for this file from the scholia source code.
See the full license at https://git.io/fxMYx.

Copyright (C) 2016-2018  Finn Årup Nielsen
Copyright (C) 2018-present  Manubot Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

"""api.

Usage:
  scholia.api get <qs>...
  scholia.api q-to-classes <q>
  scholia.api q-to-name <q>
  scholia.api search [options] <query>

Options:
  --limit=<limit>  Number of search results to return [default: 10]

Description:
  Interface to the Wikidata API and its bibliographic data.

Examples
--------
  $ python -m scholia.api get Q26857876 Q21172284 | wc
      2    1289   16174

  $ python -m scholia.api q-to-classes Q28133147
  Q13442814

"""

import requests


HEADERS = {
    'User-Agent': 'Scholia',
}


def get_wikidata_citeproc(wikidata_id):
    """
    Return a CSL JSON Item for a Wikidata bibliographic entity.
    """
    entity, = wb_get_entities([wikidata_id]).values()
    return entity_to_csl_item(entity)


def entity_to_csl_item(entity):
    """
    Convert Wikidata entry into a CSL JSON Data Item.
    """
    csl_item = dict()
    csl_item['author'] = [{'literal': author} for author in entity_to_authors(entity)]
    csl_item['title'] = entity_to_title(entity)
    csl_item['container'] = entity_to_journal_title(entity)
    csl_item['volume'] = entity_to_volume(entity)
    csl_item['page'] = entity_to_pages(entity)
    csl_item['DOI'] = entity_to_doi(entity)
    csl_item['URL'] = entity_to_full_text_url(entity)
    csl_item['locator'] = entity['id']
    csl_item['source'] = 'Wikidata'
    csl_item['issued'] = {'date-parts': [entity_to_year_month_day(entity)]}
    return csl_item


def is_human(entity):
    """Return true if entity is a human.

    Parameters
    ----------
    entity : dict
        Structure with Wikidata entity.

    Returns
    -------
    result : bool
        Result of comparison.

    """
    classes = entity_to_classes(entity)
    return 'Q5' in classes


def select_value_by_language_preferences(
        choices, preferences=('en', 'de', 'fr')):
    """Select value based on language preference.

    Parameters
    ----------
    choices : dict
        Dictionary with language as keys and strings as values.
    preferences : list or tuple
        Iterator

    Returns
    -------
    value : str
        Selected string. Returns an empty string if there is no choices.

    Examples
    --------
    >>> choices = {'da': 'Bog', 'en': 'Book', 'de': 'Buch'}
    >>> select_value_by_language_preferences(choices)
    'Book'

    """
    if not choices:
        return ''
    for preference in preferences:
        if preference in choices:
            return choices[preference]
    else:
        # Select a random one
        return next(choices.itervalues())


def wb_get_entities(qs):
    """Get entities from Wikidata.

    Query the Wikidata webservice via is API.

    Parameters
    ----------
    qs : list of str
        List of strings, each with a Wikidata item identifier.

    Returns
    -------
    data : dict of dict
        Dictionary of dictionaries.

    """
    if not qs:
        return {}

    if len(qs) > 50:
        raise NotImplementedError("Cannot handle over 50 qs yet")

    ids = "|".join(qs)
    params = {
        'action': 'wbgetentities',
        'ids': ids,
        'format': 'json',
    }
    headers = {
        'User-Agent': 'Scholia',
    }
    response_data = requests.get(
        'https://www.wikidata.org/w/api.php',
        headers=headers, params=params).json()
    if 'entities' in response_data:
        return response_data['entities']

    # TODO: Make informative/better error handling
    if 'error' in response_data:
        message = response_data['error'].get('info', '')
        message += ", id=" + response_data['error'].get('id', '')
        raise Exception(message)

    # Last resort
    raise Exception('API error')


def entity_to_authors(entity, return_humanness=False):
    """Extract authors from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item
    return_humanness : bool
        Toogle whether return argument should contain be a list of strings or a
        list of tuples with both name and an indication of whether the author
        is a human. Some authors are organizations and formatting of authors
        may need to distinguish between humans and organizations.

    Returns
    -------
    authors : list of str or list of two-tuple
        List with each element representing an author. Each element may either
        be a string with the author name or a tuple with the author name and
        a boolean indicating humanness of the author.

    """
    def statement_to_order(statement):
        LARGE = 10000000
        if 'P1545' in statement.get('qualifiers', []):
            for qualifier in statement['qualifiers']['P1545']:
                # The data value is a string type
                # TODO: handle exceptions?
                return int(qualifier['datavalue']['value'])
        else:
            return LARGE

    qs = []
    orders = []
    claims = entity['claims']
    if 'P50' in claims:
        for statement in claims['P50']:
            qs.append(statement['mainsnak']['datavalue']['value']['id'])
            orders.append(statement_to_order(statement))
    entities = wb_get_entities(qs)

    authornames = []
    if 'P2093' in claims:
        for statement in claims['P2093']:
            value = statement['mainsnak']['datavalue']['value']
            authornames.append((statement_to_order(statement), value, True))

    authors = []
    for order, q in zip(orders, qs):
        label = entity_to_label(entities[q])
        authors.append((order, label, is_human(entities[q])))

    authors.extend(authornames)

    authors.sort()

    if return_humanness:
        return [(author, humanness) for _, author, humanness in authors]
    else:
        return [author for _, author, _ in authors]


def entity_to_classes(entity):
    """Extract 'instance_of' classes.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item

    Returns
    -------
    classes : list of str
        List of strings.

    Examples
    --------
    >>> entities = wb_get_entities(['Q28133147'])
    >>> classes = entity_to_classes(list(entities.values())[0])
    >>> 'Q13442814' in classes
    True

    """
    classes = []
    for statement in entity['claims'].get('P31', []):
        classes.append(statement['mainsnak']['datavalue']['value']['id'])
    return classes


def entity_to_doi(entity):
    """Extract DOI of publication from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item

    Returns
    -------
    doi : str
        DOI as string. An empty string is returned if the field is not set.

    Examples
    --------
    >>> entities = wb_get_entities(['Q24239902'])
    >>> doi = entity_to_doi(entities['Q24239902'])
    >>> doi == '10.1038/438900A'
    True

    """
    for statement in entity['claims'].get('P356', []):
        doi = statement['mainsnak']['datavalue']['value']
        return doi
    else:
        return ''


def entity_to_full_text_url(entity):
    """Extract full text URL of publication from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item

    Returns
    -------
    url : str
        URL as string. An empty string is returned if the field is not set.

    Examples
    --------
    >>> entities = wb_get_entities(['Q28374293'])
    >>> url = entity_to_full_text_url(entities['Q28374293'])
    >>> url == ('http://papers.nips.cc/paper/'
    ...         '5872-efficient-and-robust-automated-machine-learning.pdf')
    True

    """
    for statement in entity['claims'].get('P953', []):
        url = statement['mainsnak']['datavalue']['value']
        return url
    else:
        return ''


def entity_to_journal_title(entity):
    """Extract journal of publication from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item

    Returns
    -------
    journal : str
        Journal as string. An empty string is returned if the field is not set.

    Examples
    --------
    >>> entities = wb_get_entities(['Q24239902'])
    >>> journal = entity_to_journal_title(entities['Q24239902'])
    >>> journal == 'Nature'
    True

    """
    for statement in entity['claims'].get('P1433', []):
        journal_item = statement['mainsnak']['datavalue']['value']['id']
        journal_entities = wb_get_entities([journal_item])
        claims = journal_entities[journal_item]['claims']
        titles = {}
        for journal_statement in claims.get('P1476', []):
            value = journal_statement['mainsnak']['datavalue']['value']
            titles[value['language']] = value['text']
        return select_value_by_language_preferences(titles)

    return ''


def entity_to_label(entity):
    """Extract label from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item

    Returns
    -------
    label : str
        String with label.

    """
    for language in ['en', 'de', 'da', 'fr', 'es']:
        if language in entity['labels']:
            return entity['labels'][language]['value']
    return ''


def entity_to_year_month_day(entity):
    """Extract month of publication from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item.
    language : str
        Language, if none, returns the month as a string with the month number.

    Returns
    -------
    year, month, day : tuple
        year, month, day as ints

    """
    for statement in entity['claims'].get('P577', []):
        timestamp = statement['mainsnak']['datavalue']['value']['time']
        year, month, day = map(int, timestamp[1:11].split('-'))
        return [year, month, day]


def entity_to_month(entity, language='en'):
    """Extract month of publication from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item.
    language : str
        Language, if none, returns the month as a string with the month number.

    Returns
    -------
    month : str or None
        Month as string.

    """
    for statement in entity['claims'].get('P577', []):
        date = statement['mainsnak']['datavalue']['value']['time']
        month = date[6:8]
        if language is None:
            return month
        elif language == 'en':
            return MONTH_NUMBER_TO_MONTH['en'][int(month) - 1]
        else:
            raise ValueError('language "{}" not support'.format(language))
    return None


def entity_to_name(entity):
    """Extract the name of the item.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item representing a person.

    Returns
    -------
    name : str or None
        Name of person.

    Examples
    --------
    >>> entities = wb_get_entities(['Q8219'])
    >>> name = entity_to_name(list(entities.values())[0])
    >>> name == 'Uta Frith'
    True

    """
    if 'labels' in entity:
        labels = entity['labels']
        if 'en' in labels:
            return labels['en']['value']
        else:
            for label in labels.values():
                return label['value']
    return None


def entity_to_pages(entity):
    """Extract pages of publication from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item

    Returns
    -------
    pages : str
        Pages as string. An empty string is returned if the field is not set.

    Examples
    --------
    >>> entities = wb_get_entities(['Q24239902'])
    >>> pages = entity_to_pages(entities['Q24239902'])
    >>> pages == '900-901'
    True

    """
    for statement in entity['claims'].get('P304', []):
        pages = statement['mainsnak']['datavalue']['value']
        return pages
    else:
        return ''


def entity_to_title(entity):
    """Extract title from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item.

    Returns
    -------
    title : str or None
        Title as string. If the title is not set then None is returned.

    """
    for statement in entity['claims'].get('P1476', []):
        title = statement['mainsnak']['datavalue']['value']['text']
        return title
    return None


def entity_to_volume(entity):
    """Extract volume of publication from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item

    Returns
    -------
    volume : str
        Volume as string. An empty string is returned if the field is not set.

    Examples
    --------
    >>> entities = wb_get_entities(['Q21172284'])
    >>> volume = entity_to_volume(entities['Q21172284'])
    >>> volume == '12'
    True

    """
    for statement in entity['claims'].get('P478', []):
        volume = statement['mainsnak']['datavalue']['value']
        return volume
    else:
        return ''


def entity_to_year(entity):
    """Extract year of publication from entity.

    Parameters
    ----------
    entity : dict
        Dictionary with Wikidata item

    Returns
    -------
    year : str or None
        Year as string.

    """
    for statement in entity['claims'].get('P577', []):
        date = statement['mainsnak']['datavalue']['value']['time']
        year = date[1:5]
        return year
    return None


def search(query, limit=10):
    """Search Wikidata.

    Parameters
    ----------
    query : str
        Query string.
    limit : int, optional
        Number of maximum search results to return.

    Returns
    -------
    result : list of dicts

    """
    # Query the Wikidata API
    response = requests.get(
        "https://www.wikidata.org/w/api.php",
        params={
            'action': 'query',
            'list': 'search',
            'srlimit': limit,
            'srsearch': query,
            'srwhat': 'text',
            'format': 'json',
        },
        headers=HEADERS)

    # Convert the response
    response_data = response.json()
    items = response_data['query']['search']
    results = [
        {'q': item['title'],
         'description': item['snippet']}
        for item in items]

    return results


def main():
    """Handle command-line arguments."""
    from docopt import docopt

    arguments = docopt(__doc__)

    if arguments['get']:
        qs = arguments['<qs>']
        entities = wb_get_entities(qs)
        for q in qs:
            print(entities[q])

    elif arguments['q-to-classes']:
        q = arguments['<q>']
        entities = wb_get_entities([q])
        classes = entity_to_classes(entities[q])
        for class_ in classes:
            print(class_)

    elif arguments['q-to-name']:
        q = arguments['<q>']
        entities = wb_get_entities([q])
        print(entity_to_name(entities[q]))

    elif arguments['search']:
        query = arguments['<query>']
        limit = int(arguments['--limit'])
        results = search(query, limit=limit)
        for item in results:
            print("{q} {description}".format(**item).encode('utf-8'))


if __name__ == '__main__':
    main()
