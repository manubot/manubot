"""
Preliminary testing command:

pandoc \
  --to=plain \
  --standalone \
  --filter=pandoc-manubot-cite \
  --filter pandoc-citeproc \
  manubot/pandoc/tests/input-with-cites.md


pandoc \
  --to=json \
  manubot/pandoc/tests/input-with-cites.md \
  | python manubot/pandoc/cite.py markdown
"""

"""
https://github.com/jgm/pandocfilters
https://github.com/sergiocorreia/panflute
http://scorreia.com/software/panflute/code.html#panflute.elements.Citation
"""
import argparse
import sys

import panflute

from manubot.cite.util import (
    citation_to_citeproc,
    is_valid_citation_string,
    csl_item_set_standard_citation,
)
from manubot.process.util import (
    get_citation_df,
    generate_csl_items,
    read_manual_references,
)


global_variables = {
    'citation_strings': list(),
}


def parse_args():
    """
    Read command line arguments
    """
    parser = argparse.ArgumentParser(description='Pandoc filter for citation by persistent identifier')
    parser.add_argument('target_format')
    parser.add_argument('--pandocversion', help='The pandoc version.')
    parser.add_argument('--input', nargs='?', type=argparse.FileType('r', encoding='utf-8'), default=sys.stdin)
    parser.add_argument('--output', nargs='?', type=argparse.FileType('w', encoding='utf-8'), default=sys.stdout)
    args = parser.parse_args()
    return args


def _get_citation_string_action(elem, doc):
    """
    Panflute action to extract citationId from all Citations in the AST.
    """
    if not isinstance(elem, panflute.Citation):
        return None
    citation_strings = global_variables['citation_strings']
    citation_strings.append(elem.id)
    return None


def _citation_to_id_action(elem, doc):
    """
    Panflute action to update the citationId of Citations in the AST
    with their manubot-created keys.
    """
    if not isinstance(elem, panflute.Citation):
        return None
    mapper = global_variables['citation_id_mapper']
    citation_string = f'@{elem.id}'
    if citation_string in mapper:
        elem.id = mapper[citation_string]
    return None


def process_citations(doc):
    """
    Apply citation-by-identifier to a Python object representation of
    Pandoc's Abstract Syntax Tree.

    The following Pandoc metadata fields are considered (NotImplemented):
    - bibliography (use to define reference metadata manually)
    - manubot-citation-tags (use to define tags for cite-by-id citations)
    - manubot-requests-cache-path
    - manubot-clear-requests-cache
    """

    doc.walk(_get_citation_string_action)
    citations_strings = set(global_variables['citation_strings'])
    citations_strings = sorted(filter(
        lambda x: is_valid_citation_string(f'@{x}', allow_tag=True, allow_raw=True, allow_pandoc_xnos=True),
        citations_strings,
    ))
    global_variables['citation_strings'] = citations_strings
    tag_to_string = doc.get_metadata('citation-tags', default={}, builtin=True)
    citation_df = get_citation_df(citations_strings, tag_to_string)
    global_variables['citation_df'] = citation_df
    global_variables['citation_id_mapper'] = dict(zip(
        (f'@{x}' for x in citation_df['string']), citation_df['citation_id']))
    doc.walk(_citation_to_id_action)
    manual_refs = doc.get_metadata('references', default=[], builtin=True)
    manual_refs = read_manual_references(path=None, extra_csl_items=manual_refs)
    citations = citation_df.standard_citation.unique()
    csl_items = generate_csl_items(citations, manual_refs)
    doc.metadata['references'] = csl_items


def main():
    args = parse_args()
    panflute.debug(sys.argv)
    doc = panflute.load(args.input)
    process_citations(doc)
    panflute.dump(doc, args.output)


if __name__ == '__main__':
    main()
