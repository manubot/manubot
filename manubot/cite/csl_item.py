from manubot.cite.citekey import standardize_citekey, infer_citekey_prefix, is_valid_citekey


csl_item_type_fixer = {
    'journal-article': 'article-journal',
    'book-chapter': 'chapter',
    'posted-content': 'manuscript',
    'proceedings-article': 'paper-conference',
    'standard': 'entry',
    'reference-entry': 'entry',
}

class CSL_Item(dict):
    """
    CSL_Item represents bibliographic information for a single publication.

    On a technical side CSL_Item is a Python dictionary with extra methods
    that help cleaning and manipulating it.

    These methods relate to:
    - adding an `id` key and value for CSL item
    - correcting bibliographic information   
    - adding and reading a custom note to CSL item

    """
    # The ideas for CSL_Item methods come from the following parts of code:
    #  - citekey_to_csl_item(citekey, prune=True)
    #  - csl_item_passthrough
    #  - append_to_csl_item_note
    # The methods provide primitives to reconstruct these fucntions.

    def __init__(self, incoming_dict: dict = {}):        
        super().__init__(incoming_dict)

    # def csl_item_passthrough(csl_item, set_id=None, prune=True):
    #     """
    #     Fix errors in a CSL item, according to the CSL JSON schema, and optionally
    #     change its id.

    #     http://docs.citationstyles.org/en/1.0.1/specification.html
    #     http://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html
    #     https://github.com/citation-style-language/schema/blob/master/csl-data.json
    #     """
    #     if set_id is not None:
    #         csl_item['id'] = set_id
    #     logging.debug(f"Starting csl_item_passthrough with{'' if prune else 'out'} CSL pruning for id: {csl_item.get('id', 'id not specified')}")

    def set_id(self, x):
        self['id'] = x
        return self

    #     # Correct invalid CSL item types
    #     # See https://github.com/CrossRef/rest-api-doc/issues/187
    #     if 'type' in csl_item:
    #         csl_item['type'] = csl_item_type_fixer.get(csl_item['type'], csl_item['type'])
    
    def fix_type(self):
        # Correct invalid CSL item types
        # See https://github.com/CrossRef/rest-api-doc/issues/187
        try:
            self['type'] = csl_item_type_fixer[self['type']]
        except KeyError:
            pass
        return self


def csl_item_set_standard_id(csl_item):
    """
    Extract the standard_id (standard citation key) for a csl_item and modify the csl_item in-place to set its "id" field.
    The standard_id is extracted from a "standard_citation" field, the "note" field, or the "id" field.
    If extracting the citation from the "id" field, uses the infer_citekey_prefix function to set the prefix.
    For example, if the extracted standard_id does not begin with a supported prefix (e.g. "doi:", "pmid:"
    or "raw:"), the citation is assumed to be raw and given a "raw:" prefix. The extracted citation
    (referred to as "original_standard_id") is checked for validity and standardized, after which it is
    the final "standard_id".

    Regarding csl_item modification, the csl_item "id" field is set to the standard_citation and the note field
    is created or updated with key-value pairs for standard_id, original_standard_id, and original_id.

    Note that the Manubot software generally refers to the "id" of a CSL Item as a citekey.
    However, in this context, we use "id" rather than "citekey" for consistency with CSL's "id" field.
    """
    if not isinstance(csl_item, dict):
        raise ValueError(
            "csl_item must be a CSL Data Item represented as a Python dictionary")

    from manubot.cite.citeproc import (
        append_to_csl_item_note,
        parse_csl_item_note,
    )
    note_dict = parse_csl_item_note(csl_item.get('note', ''))

    original_id = None
    original_standard_id = None
    if 'id' in csl_item:
        original_id = csl_item['id']
        original_standard_id = infer_citekey_prefix(original_id)
    if 'standard_id' in note_dict:
        original_standard_id = note_dict['standard_id']
    if 'standard_citation' in csl_item:
        original_standard_id = csl_item.pop('standard_citation')
    if original_standard_id is None:
        raise ValueError(
            'csl_item_set_standard_id could not detect a field with a citation / standard_citation. '
            'Consider setting the CSL Item "id" field.')
    assert is_valid_citekey(original_standard_id, allow_raw=True)
    standard_id = standardize_citekey(
        original_standard_id, warn_if_changed=False)
    add_to_note = {}
    if original_id and original_id != standard_id:
        if original_id != note_dict.get('original_id'):
            add_to_note['original_id'] = original_id
    if original_standard_id and original_standard_id != standard_id:
        if original_standard_id != note_dict.get('original_standard_id'):
            add_to_note['original_standard_id'] = original_standard_id
    if standard_id != note_dict.get('standard_id'):
        add_to_note['standard_id'] = standard_id
    append_to_csl_item_note(csl_item, dictionary=add_to_note)
    csl_item['id'] = standard_id
    return csl_item
