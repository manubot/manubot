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

import panflute as pf

from manubot.cite.citekey import (
    is_valid_citekey,
)
from manubot.process.util import (
    get_citekeys_df,
    generate_csl_items,
    load_manual_references,
)


global_variables = {
    "manuscript_citekeys": list(),
}


def parse_args():
    """
    Read command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Pandoc filter for citation by persistent identifier"
    )
    parser.add_argument("target_format")
    parser.add_argument("--pandocversion", help="The pandoc version.")
    parser.add_argument(
        "--input",
        nargs="?",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
    )
    parser.add_argument(
        "--output",
        nargs="?",
        type=argparse.FileType("w", encoding="utf-8"),
        default=sys.stdout,
    )
    args = parser.parse_args()
    return args


def _get_citation_string_action(elem, doc):
    """
    Panflute action to extract citationId from all Citations in the AST.
    """
    if not isinstance(elem, pf.Citation):
        return None
    manuscript_citekeys = global_variables["manuscript_citekeys"]
    manuscript_citekeys.append(elem.id)
    return None


def _citation_to_id_action(elem, doc):
    """
    Panflute action to update the citationId of Citations in the AST
    with their manubot-created keys.
    """
    if not isinstance(elem, pf.Citation):
        return None
    mapper = global_variables["citekey_shortener"]
    if elem.id in mapper:
        elem.id = mapper[elem.id]
    return None


def process_citations(doc):
    """
    Apply citation-by-identifier to a Python object representation of
    Pandoc's Abstract Syntax Tree.

    The following Pandoc metadata fields are considered (NotImplemented):
    - bibliography (use to define reference metadata manually)
    - manubot-citekey-aliases (use to define tags for cite-by-id citations)
    - manubot-requests-cache-path
    - manubot-clear-requests-cache
    """

    doc.walk(_get_citation_string_action)
    manuscript_citekeys = set(global_variables["manuscript_citekeys"])
    manuscript_citekeys = sorted(
        filter(
            lambda x: is_valid_citekey(
                x, allow_tag=True, allow_raw=True, allow_pandoc_xnos=True
            ),
            manuscript_citekeys,
        )
    )
    global_variables["manuscript_citekeys"] = manuscript_citekeys
    tag_to_string = doc.get_metadata("citekey-aliases", default={}, builtin=True)
    citekeys_df = get_citekeys_df(manuscript_citekeys, tag_to_string)
    global_variables["citekeys_df"] = citekeys_df
    global_variables["citekey_shortener"] = dict(
        zip((citekeys_df["manuscript_citekey"]), citekeys_df["short_citekey"])
    )
    doc.walk(_citation_to_id_action)
    manual_refs = doc.get_metadata("references", default=[], builtin=True)
    bibliography_paths = doc.get_metadata("bibliography", default=[], builtin=True)
    if not isinstance(bibliography_paths, list):
        bibliography_paths = [bibliography_paths]
    manual_refs = load_manual_references(
        bibliography_paths, extra_csl_items=manual_refs
    )
    standard_citekeys = citekeys_df.standard_citekey.unique()
    csl_items = generate_csl_items(standard_citekeys, manual_refs)
    doc.metadata["references"] = csl_items


def main():
    args = parse_args()
    pf.debug(sys.argv)
    doc = pf.load(args.input)
    process_citations(doc)
    pf.dump(doc, args.output)


if __name__ == "__main__":
    main()
