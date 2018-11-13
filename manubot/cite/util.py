import logging
import re

from manubot.util import import_function


citeproc_retrievers = {
    'doi': 'manubot.cite.doi.get_doi_citeproc',
    'pmid': 'manubot.cite.pubmed.get_pubmed_citeproc',
    'pmcid': 'manubot.cite.pubmed.get_pmc_citeproc',
    'arxiv': 'manubot.cite.arxiv.get_arxiv_citeproc',
    'url': 'manubot.cite.url.get_url_citeproc',
}

"""
Regex to extract citations.

Same rules as pandoc, except more permissive in the following ways:

1. the final character can be a slash because many URLs end in a slash.
2. underscores are allowed in internal characters because URLs, DOIs, and
   citation tags often contain underscores.

If a citation string does not match this regex, it can be substituted for a
tag that does, as defined in citation-tags.tsv.

https://github.com/greenelab/manubot-rootstock/issues/2#issuecomment-312153192

Prototyped at https://regex101.com/r/s3Asz3/2
"""
citation_pattern = re.compile(
    r'(?<!\w)@[a-zA-Z0-9][\w:.#$%&\-+?<>~/]*[a-zA-Z0-9/]')


def standardize_citation(citation):
    """
    Standardize citation idenfiers based on their source
    """
    source, identifier = citation.split(':', 1)
    if source == 'doi':
        identifier = identifier.lower()
    return f'{source}:{identifier}'


regexes = {
    'pmid': re.compile(r'[1-9][0-9]{0,7}'),
    'doi': re.compile(r'10\.[0-9]{4,9}/\S+'),
}


def inspect_citation_identifier(citation):
    """
    Check citation identifiers adhere to expected formats. If an issue is
    detected a string describing the issue is returned. Otherwise returns None.
    """
    source, identifier = citation.split(':', 1)
    if source == 'pmid':
        # https://www.nlm.nih.gov/bsd/mms/medlineelements.html#pmid
        if identifier.startswith('PMC'):
            return (
                'PubMed Identifiers should start with digits rather than PMC. '
                f'Should {citation} switch the citation source to `pmcid`?'
            )
        elif not regexes['pmid'].fullmatch(identifier):
            return 'PubMed Identifiers should be 1-8 digits with no leading zeros.'
    if source == 'pmcid':
        # https://www.nlm.nih.gov/bsd/mms/medlineelements.html#pmc
        if not identifier.startswith('PMC'):
            return 'PubMed Central Identifiers must start with `PMC`.'
    if source == 'doi':
        # https://www.crossref.org/blog/dois-and-matching-regular-expressions/
        if not identifier.startswith('10.'):
            return (
                'DOIs must start with `10.`.'
            )
        elif not regexes['doi'].fullmatch(identifier):
            return (
                'identifier does not conform to the DOI regex. '
                'Double check the DOI.'
            )
    return None


def is_valid_citation_string(string):
    """
    Return True if string is a properly formatted citation. Return False if
    string is not a citation (i.e. it's an exempt category such as @fig) or is
    an invalid citation. In the case string is an invalid citation, an error is
    logged. This function does not catch all invalid citations, but instead
    performs cursory checks, such as citations adhere to the expected formats.
    No calls to external resources are used by these checks, so they will not
    detect citations to non-existent identifiers unless those identifiers
    violate their source's syntax.
    """
    if not string.startswith('@'):
        logging.error(f'{string} → does not start with @')
        return False
    citation = string[1:]
    try:
        source, identifier = citation.split(':', 1)
    except ValueError as e:
        logging.error(
            f'Citation not splittable via a single colon: {string}. '
            'Citation strings must be in the format of `@source:identifier`.'
        )
        return False

    if not source or not identifier:
        msg = f'{string} → blank source or identifier'
        logging.error(msg)
        return False

    # Exempted non-citation sources used for pandoc-fignos, pandoc-tablenos,
    # and pandoc-eqnos
    if source in {'fig', 'tbl', 'eq'}:
        return False

    # Check supported source type
    sources = {'tag', 'raw'} | set(citeproc_retrievers)
    if source not in sources:
        if source.lower() in sources:
            logging.error(
                f'Citation sources should be all lowercase.\n'
                f'Should {string} use "{source.lower()}" rather than "{source}"?'
            )
        else:
            logging.error(
                f'{string} → source "{source}" is not valid'
            )
        return False

    inspection = inspect_citation_identifier(citation)
    if inspection:
        logging.error(f'invalid {source} citation: {string}\n{inspection}')
        return False

    return True


def get_citation_id(standard_citation):
    """
    Get the citation_id for a standard_citation.
    """
    import hashlib
    import base62
    assert '@' not in standard_citation
    as_bytes = standard_citation.encode()
    blake_hash = hashlib.blake2b(as_bytes, digest_size=6)
    digest = blake_hash.digest()
    citation_id = base62.encodebytes(digest)
    return citation_id


def citation_to_citeproc(citation, prune=True):
    """
    Return a dictionary with citation metadata
    """
    assert citation == standardize_citation(citation)
    source, identifier = citation.split(':', 1)

    if source in citeproc_retrievers:
        citeproc_retriever = import_function(citeproc_retrievers[source])
        citeproc = citeproc_retriever(identifier)
    else:
        msg = f'Unsupported citation source {source} in {citation}'
        raise ValueError(msg)

    citation_id = get_citation_id(citation)
    from manubot.cite.citeproc import citeproc_passthrough
    citeproc = citeproc_passthrough(citeproc, set_id=citation_id, prune=prune)

    return citeproc
