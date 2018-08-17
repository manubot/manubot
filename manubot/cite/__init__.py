import hashlib
import json
import logging
import pathlib
import re
import subprocess
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


def citation_to_citeproc(citation, prune=True):
    """
    Return a dictionary with citation metadata
    """
    assert citation == standardize_citation(citation)
    source, identifier = citation.split(':', 1)

    if source in citeproc_retrievers:
        citeproc = citeproc_retrievers[source](identifier)
    else:
        msg = f'Unsupported citation source {source} in {citation}'
        raise ValueError(msg)

    citation_id = get_citation_id(citation)
    citeproc = citeproc_passthrough(citeproc, set_id=citation_id, prune=prune)

    return citeproc


# For manubot cite, infer --format from --output filename extensions
extension_to_format = {
    '.txt': 'plain',
    '.md': 'markdown',
    '.docx': 'docx',
    '.html': 'html',
    '.xml': 'jats',
}


def add_subparser_cite(subparsers):
    parser = subparsers.add_parser(
        name='cite',
        help='citation to CSL command line utility',
        description='Retrieve bibliographic metadata for one or more citation identifiers.',
    )
    parser.add_argument(
        '--render',
        action='store_true',
        help='Whether to render CSL Data into a formatted reference list using Pandoc',
    )
    parser.add_argument(
        '--csl',
        default='https://github.com/greenelab/manubot-rootstock/raw/master/build/assets/style.csl',
        help="When --render, specify an XML CSL definition to style references. Pandoc's --csl option",
    )
    parser.add_argument(
        '--format',
        choices=list(extension_to_format.values()),
        help="Format to use for output file. If not specified, attempt to infer this from filename extension. Otherwise, default to plain",
    )
    parser.add_argument(
        '--output',
        type=pathlib.Path,
        help='specify a file to write output, otherwise default to stdout',
    )
    parser.add_argument(
        '--allow-invalid-csl-data',
        dest='prune_csl',
        action='store_false',
        help='allow CSL Items that do not conform to the JSON Schema. Skips CSL pruning.',
    )
    parser.add_argument(
        'citations',
        nargs='+',
        help='one or more (space separated) citations to produce CSL for',
    )
    parser.set_defaults(function=cli_cite)
    return parser


def call_pandoc(metadata, path, format='plain'):
    """
    path is the path to write to.
    """
    metadata_block = '---\n{yaml}\n...\n'.format(
        yaml=json.dumps(metadata, ensure_ascii=False, indent=2)
    )
    args = [
        'pandoc',
        '--filter', 'pandoc-citeproc',
        '--output', str(path) if path else '-',
    ]
    if format == 'markdown':
        args.extend(['--to', 'markdown_strict'])
    elif format == 'jats':
        args.extend(['--to', 'jats', '--standalone'])
    elif format == 'docx':
        args.extend(['--to', 'docx'])
    elif format == 'html':
        args.extend(['--to', 'html'])
    elif format == 'plain':
        # Do not use ALL_CAPS for bold & underscores for italics
        # https://github.com/jgm/pandoc/issues/4834#issuecomment-412972008
        filter_path = pathlib.Path(__file__).joinpath('..', 'plain-pandoc-filter.lua').resolve()
        assert filter_path.exists()
        args.extend([
            '--to', 'plain',
            '--lua-filter', str(filter_path),
        ])
    _check_pandoc_installation()
    logging.info('call_pandoc subprocess args:\n' + ' '.join(args))
    process = subprocess.run(
        args=args,
        input=metadata_block.encode(),
        stdout=subprocess.PIPE if path else sys.stdout,
        stderr=sys.stderr,
    )
    process.check_returncode()


def cli_cite(args):
    """
    Main function for the manubot cite command-line interface.

    Does not allow user to directly specify Pandoc's --to argument, due to
    inconsistent citaiton renderring by output format. See
    https://github.com/jgm/pandoc/issues/4834
    """
    # generate CSL JSON data
    csl_list = list()
    for citation in args.citations:
        citation = standardize_citation(citation)
        csl_list.append(citation_to_citeproc(citation, prune=args.prune_csl))

    # output CSL JSON data, if --render is False
    if not args.render:
        write_file = args.output.open('w') if args.output else sys.stdout
        with write_file:
            json.dump(csl_list, write_file, ensure_ascii=False, indent=2)
            write_file.write('\n')
        return

    # use Pandoc to render citations
    if not args.format and args.output:
        vars(args)['format'] = extension_to_format.get(args.output.suffix)
    if not args.format:
        vars(args)['format'] = 'plain'
    pandoc_metadata = {
        'nocite': '@*',
        'csl': args.csl,
        'references': csl_list,
    }
    call_pandoc(
        metadata=pandoc_metadata,
        path=args.output,
        format=args.format,
    )


def _check_pandoc_installation():
    """
    Log the system's pandoc and pandoc-citeproc versions if installed, otherwise exit program.
    """
    try:
        for command in 'pandoc', 'pandoc-citeproc':
            output = subprocess.check_output(
                args=[command, '--version'],
                universal_newlines=True
            )
            logging.info(output)
    except FileNotFoundError as error:
        logging.critical(
            f'FileNotFoundError error for system command "{command}". '
            f'Check that Pandoc is installed.'
        )
        raise SystemExit(1)
