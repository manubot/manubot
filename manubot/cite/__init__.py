__all__ = [
    "citation_to_citeproc",
    "citekey_to_csl_item",
    "standardize_citation",
    "standardize_citekey",
]

from manubot.cite.citekey import citekey_to_csl_item, standardize_citekey


def citation_to_citeproc(*args, **kwargs):
    import warnings

    warnings.warn(
        "'citation_to_citeproc' has been renamed to 'citekey_to_csl_item'"
        " and will be removed in a future release.",
        category=FutureWarning,
    )
    return citekey_to_csl_item(*args, **kwargs)


def standardize_citation(*args, **kwargs):
    import warnings

    warnings.warn(
        "'standardize_citation' has been renamed to 'standardize_citekey'"
        " and will be removed in a future release.",
        category=FutureWarning,
    )
    return standardize_citekey(*args, **kwargs)
