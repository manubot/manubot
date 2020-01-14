"""
This module defines a pandoc filter for manubot cite functionality.

Related development commands:

```shell
# export to plain text
pandoc \
  --to=plain \
  --standalone \
  --bibliography=manubot/pandoc/tests/test_cite_filter/bibliography.json \
  --bibliography=manubot/pandoc/tests/test_cite_filter/bibliography.bib \
  --filter=pandoc-manubot-cite \
  --filter=pandoc-citeproc \
  manubot/pandoc/tests/test_cite_filter/input.md

# call the filter manually using pandoc JSON output
pandoc \
  --to=json \
  manubot/pandoc/tests/test_cite_filter/input.md \
  | python manubot/pandoc/test_cite.py markdown
```

Related resources on pandoc filters:

- [python pandocfilters package](https://github.com/jgm/pandocfilters)
- [python panflute package](https://github.com/sergiocorreia/panflute)
- [panflute Citation class](http://scorreia.com/software/panflute/code.html#panflute.elements.Citation)
"""
import argparse
import logging
import pathlib

import panflute as pf

from manubot.cite.citekey import is_valid_citekey
from manubot.process.util import (
    get_citekeys_df,
    generate_csl_items,
    load_manual_references,
    write_citekeys_tsv,
    write_csl_json,
)


global_variables = {
    "manuscript_citekeys": list(),
}


def parse_args():
    """
    Read command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Pandoc filter for citation by persistent identifier. "
        "Filters are command-line programs that read and write a JSON-encoded abstract syntax tree for Pandoc. "
        "Unless you are debugging, run this filter as part of a pandoc command by specifying --filter=pandoc-manubot-cite."
    )
    parser.add_argument(
        "target_format",
        help="output format of the pandoc command, as per Pandoc's --to option",
    )
    parser.add_argument(
        "--input",
        nargs="?",
        type=argparse.FileType("r", encoding="utf-8"),
        help="path read JSON input (defaults to stdin)",
    )
    parser.add_argument(
        "--output",
        nargs="?",
        type=argparse.FileType("w", encoding="utf-8"),
        help="path to write JSON output (defaults to stdout)",
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
    Extract citekey aliases from the document that were defined
    using markdown's link reference syntax.
    https://spec.commonmark.org/0.29/#link-reference-definitions

    Based on pandoc-url2cite implementation by phiresky at
    https://github.com/phiresky/pandoc-url2cite/blob/b28374a9a037a5ce1747b8567160d8dffd64177e/index.ts#L118-L152
    """
    if type(elem) != pf.Para:
        # require link reference definitions to be in their own paragraph
        return
    while (
        len(elem.content) >= 3
        and type(elem.content[0]) == pf.Cite
        and len(elem.content[0].citations) == 1
        and type(elem.content[1]) == pf.Str
        and elem.content[1].text == ":"
    ):
        # paragraph consists of at least a Cite (with one Citaiton),
        # a Str (equal to ":"), and additional elements, such as a
        # link destination and possibly more link-reference definitions.
        space_index = 3 if type(elem.content[2]) == pf.Space else 2
        destination = elem.content[space_index]
        if type(destination) == pf.Str:
            # paragraph starts with `[@something]: something`
            # save info to citekeys and remove from paragraph
            citekey = elem.content[0].citations[0].id
            citekey_aliases = global_variables["citekey_aliases"]
            if (
                citekey in citekey_aliases
                and citekey_aliases[citekey] != destination.text
            ):
                logging.warning(f"multiple aliases defined for @{citekey}")
            citekey_aliases[citekey] = destination.text
            # found citation, add it to citekeys and remove it from document
            elem.content = elem.content[space_index + 1 :]
        # remove leading SoftBreak, before continuing
        if len(elem.content) > 0 and type(elem.content[0]) == pf.SoftBreak:
            elem.content.pop(0)


def process_citations(doc):
    """
    Apply citation-by-identifier to a Python object representation of
    Pandoc's Abstract Syntax Tree.

    The following Pandoc metadata fields are considered:

    - bibliography (use to define reference metadata manually)
    - citekey-aliases (use to define tags for cite-by-id citations)
    - manubot-requests-cache-path
    - manubot-clear-requests-cache
    - manubot-output-citekeys: path to write TSV table of citekeys
    - manubot-output-bibliography: path to write generated CSL JSON bibliography
    """
    citekey_aliases = doc.get_metadata("citekey-aliases", default={})
    if not isinstance(citekey_aliases, dict):
        logging.warning(
            f"Expected metadata.citekey-aliases to be a dict, "
            f"but received a {citekey_aliases.__class__.__name__}. Disregarding."
        )
        citekey_aliases = dict()

    global_variables["citekey_aliases"] = citekey_aliases
    doc.walk(_get_reference_link_citekey_aliases)
    doc.walk(_get_citekeys_action)
    manuscript_citekeys = global_variables["manuscript_citekeys"]
    manuscript_citekeys = sorted(
        filter(
            lambda x: is_valid_citekey(
                x, allow_tag=True, allow_raw=True, allow_pandoc_xnos=True
            ),
            set(manuscript_citekeys),
        )
    )
    global_variables["manuscript_citekeys"] = manuscript_citekeys
    citekeys_df = get_citekeys_df(
        manuscript_citekeys, global_variables["citekey_aliases"],
    )
    global_variables["citekeys_df"] = citekeys_df
    global_variables["citekey_shortener"] = dict(
        zip((citekeys_df["manuscript_citekey"]), citekeys_df["short_citekey"])
    )
    doc.walk(_citation_to_id_action)
    manual_refs = doc.get_metadata("references", default=[])
    bibliography_paths = doc.get_metadata("bibliography", default=[])
    if not isinstance(bibliography_paths, list):
        bibliography_paths = [bibliography_paths]
    manual_refs = load_manual_references(
        bibliography_paths, extra_csl_items=manual_refs
    )
    standard_citekeys = citekeys_df.standard_citekey.unique()
    requests_cache_path = doc.get_metadata("manubot-requests-cache-path")
    if requests_cache_path:
        pathlib.Path(requests_cache_path).parent.mkdir(parents=True, exist_ok=True)
    csl_items = generate_csl_items(
        citekeys=standard_citekeys,
        manual_refs=manual_refs,
        requests_cache_path=doc.get_metadata("manubot-requests-cache-path"),
        clear_requests_cache=doc.get_metadata("manubot-clear-requests-cache", False),
    )
    write_citekeys_tsv(citekeys_df, path=doc.get_metadata("manubot-output-citekeys"))
    write_csl_json(csl_items, path=doc.get_metadata("manubot-output-bibliography"))
    # Update pandoc metadata with fields that this filter
    # has either consumed, created, or modified.
    doc.metadata["bibliography"] = []
    doc.metadata["references"] = csl_items
    doc.metadata["citekey_aliases"] = citekey_aliases


def main():
    from manubot.command import setup_logging_and_errors, exit_if_error_handler_fired

    diagnostics = setup_logging_and_errors()
    args = parse_args()
    # Let panflute handle io to sys.stdout / sys.stdin to set utf-8 encoding.
    # args.input=None for stdin, args.output=None for stdout
    doc = pf.load(input_stream=args.input)
    log_level = doc.get_metadata("manubot-log-level", "WARNING")
    diagnostics["logger"].setLevel(getattr(logging, log_level))
    process_citations(doc)
    pf.dump(doc, output_stream=args.output)
    if doc.get_metadata("manubot-fail-on-errors", False):
        exit_if_error_handler_fired(diagnostics["error_handler"])


if __name__ == "__main__":
    main()
