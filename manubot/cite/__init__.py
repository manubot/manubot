import argparse
import hashlib
import json
import logging
import re
import sys

import base62

from manubot.cite.arxiv import get_arxiv_citeproc
from manubot.cite.doi import get_doi_citeproc
from manubot.cite.pubmed import (
    get_pmc_citeproc,
    get_pubmed_citeproc,
)
from manubot.cite.url import get_url_citeproc
from manubot.cite.citeproc import citeproc_passthrough

citeproc_retrievers = {
    'doi': get_doi_citeproc,
    'pmid': get_pubmed_citeproc,
    'pmcid': get_pmc_citeproc,
    'arxiv': get_arxiv_citeproc,
    'url': get_url_citeproc,
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


def is_valid_citation_string(string):
    """
    Return True if the citation string is a properly formatted citation.
    Return False if improperly formatted or a non-citation.
    """
    if not string.startswith('@'):
        logging.error(f'{string} → does not start with @')
        return False

    try:
        source, identifier = string.lstrip('@').split(':', 1)
    except ValueError as e:
        logging.error(f'Citation not splittable: {string}')
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
    if source != 'tag' and source not in citeproc_retrievers:
        logging.error(f'{string} → source "{source}" is not valid')
        return False

    return True


def get_citation_id(standard_citation):
    """
    Get the citation_id for a standard_citation.
    """
    assert '@' not in standard_citation
    as_bytes = standard_citation.encode()
    blake_hash = hashlib.blake2b(as_bytes, digest_size=6)
    digest = blake_hash.digest()
    citation_id = base62.encodebytes(digest)
    return citation_id


def citation_to_citeproc(citation):
    """
    Return a dictionary with citation metadata
    """
    assert citation == standardize_citation(citation)
    source, identifier = citation.split(':', 1)

    if source in citeproc_retrievers:
        citeproc = citeproc_retrievers[source](identifier)
    else:
        msg = f'Unsupported citation  source {source} in {citation}'
        raise ValueError(msg)

    citation_id = get_citation_id(citation)
    citeproc = citeproc_passthrough(citeproc, set_id=citation_id)

    return citeproc


def configure_cite_argparser(parser):
    parser.add_argument('citations', nargs='+',
                        help='one or more (space separated) citations to produce CSL for')
    parser.add_argument('--file', type=argparse.FileType('w'), default=sys.stdout,
                        help='specify a file to write CSL output, otherwise default to stdout')
    return parser


def cli_cite(args):
    csl_list = list()
    for citation in args.citations:
        citation = standardize_citation(citation)
        csl_list.append(citation_to_citeproc(citation))
    with args.file as write_file:
        json.dump(csl_list, write_file, ensure_ascii=False, indent=2)
