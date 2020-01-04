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
import logging
import sys

import panflute as pf

from manubot.cite.citekey import is_valid_citekey
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
        default="-",
    )
    parser.add_argument(
        "--output",
        nargs="?",
        type=argparse.FileType("w", encoding="utf-8"),
        default="-",
    )
    args = parser.parse_args()
    return args


def _get_citekeys_action(elem, doc):
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


def _get_reference_link_citekey_aliases(elem, doc):
    """
    Based on TypeScript implementation by phiresky at
    https://github.com/phiresky/pandoc-url2cite/blob/b28374a9a037a5ce1747b8567160d8dffd64177e/index.ts#L118-L152

    Uses markdown's link reference syntax to define citekey aliases (tags)
    https://spec.commonmark.org/0.29/#link-reference-definitions
    """
    if type(elem) != pf.Para:
        return
    while (
        len(elem.content) >= 3
        and type(elem.content[0]) == pf.Cite
        and len(elem.content[0].citations) == 1  # differs from pandoc-url2cite
        and type(elem.content[1]) == pf.Str
        and elem.content[1].text == ":"
    ):
        space_index = 3 if type(elem.content[2]) == pf.Space else 2
        destination = elem.content[space_index]
        if type(destination) == pf.Str:
            # paragraph starts with [@something]: something
            # save info to citekeys and remove from paragraph
            citekey = elem.content[0].citations[0].id  # differs from pandoc-url2cite
            citekey_aliases = global_variables["citekey_aliases"]
            if citekey in citekey_aliases:
                logging.warning(f"duplicate citekey {citekey}")
            citekey_aliases[citekey] = destination.text
            # found citation, add it to citekeys and remove it from document
            elem.content = elem.content[space_index + 1 :]
        if len(elem.content) > 0 and type(elem.content[0]) == pf.SoftBreak:
            elem.content.pop(0)


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
    global_variables["citekey_aliases"] = doc.get_metadata(
        "citekey-aliases", default={}, builtin=True
    )
    manuscript_citekeys = set(global_variables["manuscript_citekeys"])

    doc.walk(_get_reference_link_citekey_aliases)
    doc.walk(_get_citekeys_action)
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
    citekeys_df = get_citekeys_df(
        manuscript_citekeys, global_variables["citekey_aliases"]
    )
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
