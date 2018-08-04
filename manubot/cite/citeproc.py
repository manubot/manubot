# Valid CSL (citeproc JSON) types as per
# https://github.com/citation-style-language/schema/blob/4846e02f0a775a8272819204379a4f8d7f45c16c/csl-types.rnc#L5-L39
citeproc_types = {
    "article",
    "article-journal",
    "article-magazine",
    "article-newspaper",
    "bill",
    "book",
    "broadcast",
    "chapter",
    "dataset",
    "entry",
    "entry-dictionary",
    "entry-encyclopedia",
    "figure",
    "graphic",
    "interview",
    "legal_case",
    "legislation",
    "manuscript",
    "map",
    "motion_picture",
    "musical_score",
    "pamphlet",
    "paper-conference",
    "patent",
    "personal_communication",
    "post",
    "post-weblog",
    "report",
    "review",
    "review-book",
    "song",
    "speech",
    "thesis",
    "treaty",
    "webpage",
}

citeproc_type_fixer = {
    'journal-article': 'article-journal',
    'book-chapter': 'chapter',
    'posted-content': 'manuscript',
    'proceedings-article': 'paper-conference',
    'standard': 'entry',
    'reference-entry': 'entry',
}

# Remove citeproc keys to fix pandoc-citeproc errors
citeproc_remove_keys = [
    # Error in $[0].ISSN[0]: failed to parse field ISSN: mempty
    'ISSN',
    # Error in $[2].ISBN[0]: failed to parse field ISBN: mempty
    'ISBN',
    # pandoc-citeproc expected Object not array for archive
    'archive',
    # failed to parse field event: Could not read as string
    'event',
    # remove the references of cited papers. Not neccessary and unwieldy.
    'reference',
    # Error in $[26].categories[0][0]: failed to parse field categories: mempty
    'categories',
]


def citeproc_passthrough(csl_item, set_id=None):
    """
    Fix errors in a CSL item and optionally change its id.
    http://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html
    https://github.com/citation-style-language/schema/blob/master/csl-data.json
    """
    if set_id is not None:
        csl_item['id'] = set_id

    # Correct invalid CSL item types
    # See https://github.com/CrossRef/rest-api-doc/issues/187
    old_type = csl_item['type']
    csl_type = citeproc_type_fixer.get(old_type, old_type)
    if csl_type not in citeproc_types:
        csl_type = 'entry'
    csl_item['type'] = csl_type

    # Remove problematic objects
    for key in citeproc_remove_keys:
        csl_item.pop(key, None)

    # pandoc-citeproc error
    # failed to parse field issued: Could not read as string: Null
    try:
        value = csl_item['issued']['date-parts'][0][0]
        if value is None:
            del csl_item['issued']
    except KeyError:
        pass

    return csl_item
