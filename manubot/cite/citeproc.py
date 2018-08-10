import copy
import functools
import logging

import jsonref
import jsonschema

citeproc_type_fixer = {
    'journal-article': 'article-journal',
    'book-chapter': 'chapter',
    'posted-content': 'manuscript',
    'proceedings-article': 'paper-conference',
    'standard': 'entry',
    'reference-entry': 'entry',
}


def citeproc_passthrough(csl_item, set_id=None, prune=True):
    """
    Fix errors in a CSL item, according to the CSL JSON schema, and optionally
    change its id.

    http://docs.citationstyles.org/en/1.0.1/specification.html
    http://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html
    https://github.com/citation-style-language/schema/blob/master/csl-data.json
    """
    if set_id is not None:
        csl_item['id'] = set_id

    # Correct invalid CSL item types
    # See https://github.com/CrossRef/rest-api-doc/issues/187
    csl_item['type'] = citeproc_type_fixer.get(csl_item['type'], csl_item['type'])

    if prune:
        # Remove fields that violate the CSL Item JSON Schema
        csl_item, = remove_jsonschema_errors([csl_item])

    # Default CSL type to entry
    csl_item['type'] = csl_item.get('type', 'entry')

    if prune:
        # Confirm that corrected CSL validates
        # validator.validate([csl_item])
        pass
    return csl_item


@functools.lru_cache()
def get_jsonschema_csl_validator():
    """
    Return a jsonschema validator for the CSL Item JSON Schema
    """
    url = 'https://github.com/dhimmel/schema/raw/manubot/csl-data.json'
    # Use jsonref to workaround https://github.com/Julian/jsonschema/issues/447
    schema = jsonref.load_uri(url, jsonschema=True)
    Validator = jsonschema.validators.validator_for(schema)
    Validator.check_schema(schema)
    return Validator(schema)


def remove_jsonschema_errors(instance):
    """
    Remove fields that produced JSON Schema errors.
    https://github.com/Julian/jsonschema/issues/448
    """
    validator = get_jsonschema_csl_validator()
    errors = list(validator.iter_errors(instance))
    instance = copy.deepcopy(instance)
    errors = sorted(errors, key=lambda e: e.path, reverse=True)
    for error in errors:
        _remove_error(instance, error)
    return instance


def _delete_elem(instance, path):
    """
    Helper function for remove_jsonschema_errors
    """
    logging.info(f'_delete_elem deleting CSL element at: ' + '/'.join(map(str, path)))
    *head, tail = path
    try:
        del _deep_get(instance, head)[tail]
    except KeyError:
        pass


def _deep_get(instance, path):
    for key in path:
        instance = instance[key]
    return instance


def _remove_error(instance, error):
    """
    Helper function for remove_jsonschema_errors
    """
    sub_errors = error.context
    if sub_errors:
        already_removed_additional = False
        for sub_error in sub_errors:
            if sub_error.validator == 'additionalProperties':
                if already_removed_additional:
                    continue
                already_removed_additional = True
            sub_intance = _deep_get(instance, error.path)
            _remove_error(sub_intance, sub_error)
    elif error.validator == 'additionalProperties':
        extras = set(error.instance) - set(error.schema['properties'])
        for key in extras:
            _delete_elem(instance, path=list(error.path) + [key])
    elif error.validator in {'enum', 'type'}:
        _delete_elem(instance, error.path)
    else:
        raise NotImplementedError(f'{error.validator} is not yet supported')
