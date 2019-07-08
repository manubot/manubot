import json
import logging
import pathlib

from manubot import __version__ as manubot_version
from manubot.cite.citeproc import (
    append_to_csl_item_note,
    citeproc_passthrough,
)
from manubot.cite.util import (
    csl_item_set_standard_id,
    get_citation_short_id,
)


def load_bibliography(path):
    """
    Load a bibliography as CSL Items (a CSL JSON Python object).
    For paths that already contain CSL Items (inferred from a .json or .yaml extension),
    parse these files directly. Otherwise, delegate conversion to CSL Items to pandoc-citeproc.
    """
    path = pathlib.Path(path)
    use_pandoc_citeproc = True
    try:
        if path.suffix == '.json':
            use_pandoc_citeproc = False
            with path.open(encoding='utf-8-sig') as read_file:
                csl_items = json.load(read_file)
        if path.suffix == '.yaml':
            use_pandoc_citeproc = False
            import yaml
            with path.open(encoding='utf-8-sig') as read_file:
                csl_items = yaml.safe_load(read_file)
    except Exception:
        logging.exception(f'process.load_bibliography: error parsing {path}.\n')
        csl_items = []
    if use_pandoc_citeproc:
        from manubot.pandoc.bibliography import (
            load_bibliography as load_bibliography_pandoc,
        )
        csl_items = load_bibliography_pandoc(path)
    if not isinstance(csl_items, list):
        logging.error(
            f'process.load_bibliography: csl_items read from {path} are of type {type(csl_items)}. '
            'Setting csl_items to an empty list.'
        )
        csl_items = []
    return csl_items


def load_manual_references(paths=[], extra_csl_items=[]):
    """
    Read manual references (overrides) from files specified by a list of paths.
    Returns a standard_citation to CSL Item dictionary. extra_csl_items specifies
    JSON CSL stored as a Python object, to be used in addition to the CSL JSON
    stored as text in the file specified by path. Set paths=[] to only use extra_csl_items.
    """
    csl_items = []
    for path in paths:
        path = pathlib.Path(path)
        if not path.is_file():
            logging.warning(f'process.load_bibliographies is skipping a non-existent path: {path}')
            continue
        for csl_item in load_bibliography(path):
            append_to_csl_item_note(
                csl_item,
                text=f'This CSL JSON Item was loaded by Manubot v{manubot_version} from a manual reference file.',
                dictionary={'manual_reference_filename': path.name},
            )
            csl_items.append(csl_item)
    csl_items.extend(extra_csl_items)
    manual_refs = dict()
    for csl_item in csl_items:
        try:
            csl_item_set_standard_id(csl_item)
        except Exception:
            csl_item_str = json.dumps(csl_item, indent=2)
            logging.info(f'Skipping csl_item where setting standard_id failed:\n{csl_item_str}', exc_info=True)
            continue
        standard_id = csl_item['id']
        csl_item = citeproc_passthrough(csl_item, set_id=get_citation_short_id(standard_id))
        manual_refs[standard_id] = csl_item
    return manual_refs
