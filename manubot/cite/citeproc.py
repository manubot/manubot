import copy
import functools
import logging
import re

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
    logging.debug(f"Starting citeproc_passthrough with{'' if prune else 'out'} CSL pruning for id: {csl_item.get('id', 'id not specified')}")

    # Correct invalid CSL item types
    # See https://github.com/CrossRef/rest-api-doc/issues/187
    if 'type' in csl_item:
        csl_item['type'] = citeproc_type_fixer.get(csl_item['type'], csl_item['type'])

    if prune:
        # Remove fields that violate the CSL Item JSON Schema
        csl_item, = remove_jsonschema_errors([csl_item])

    # Default CSL type to entry
    csl_item['type'] = csl_item.get('type', 'entry')

    if prune:
        # Confirm that corrected CSL validates
        validator = get_jsonschema_csl_validator()
        validator.validate([csl_item])
    return csl_item


def append_to_csl_item_note(csl_item, text='', dictionary={}):
    """
    Add information to the note field of a CSL Item.
    In addition to accepting arbitrary text, the note field can be used to encode
    additional values not defined by the CSL JSON schema, as per
    https://github.com/Juris-M/citeproc-js-docs/blob/93d7991d42b4a96b74b7281f38e168e365847e40/csl-json/markup.rst#cheater-syntax-for-odd-fields
    Use dictionary to specify variable-value pairs.
    """
    if not isinstance(csl_item, dict):
        raise ValueError(f'append_to_csl_item_note: csl_item must be a dict but was of type {type(csl_item)}')
    if not isinstance(dictionary, dict):
        raise ValueError(f'append_to_csl_item_note: dictionary must be a dict but was of type {type(dictionary)}')
    if not isinstance(text, str):
        raise ValueError(f'append_to_csl_item_note: text must be a str but was of type {type(text)}')
    note = str(csl_item.get('note', ''))
    if text:
        if note and not note.endswith('\n'):
            note += '\n'
        note += text
    for key, value in dictionary.items():
        if not re.fullmatch(r'[A-Z]+|[-_a-z]+', key):
            logging.warning(f'append_to_csl_item_note: skipping adding "{key}" because it does not conform to the variable_name syntax as per https://git.io/fjTzW.')
            continue
        if '\n' in value:
            logging.warning(f'append_to_csl_item_note: skipping adding "{key}" because the value contains a newline: "{value}"')
            continue
        if note and not note.endswith('\n'):
            note += '\n'
        note += f'{key}: {value}'
    if note:
        csl_item['note'] = note
    return csl_item


def parse_csl_item_note(note):
    """
    Return the dictionary of key-value pairs encoded in a CSL JSON note.
    Extracts both forms (line-entry and braced-entry) of key-value pairs from "cheater syntax"
    https://github.com/Juris-M/citeproc-js-docs/blob/93d7991d42b4a96b74b7281f38e168e365847e40/csl-json/markup.rst#cheater-syntax-for-odd-fields
    """
    note = str(note)
    line_matches = re.findall(
        r'^(?P<key>[A-Z]+|[-_a-z]+): *(?P<value>.+?) *$', note, re.MULTILINE)
    braced_matches = re.findall(
        r'{:(?P<key>[A-Z]+|[-_a-z]+): *(?P<value>.+?) *}', note)
    return dict(line_matches + braced_matches)


@functools.lru_cache()
def get_jsonschema_csl_validator():
    """
    Return a jsonschema validator for the CSL Item JSON Schema
    """
    import jsonref
    import jsonschema

    url = 'https://github.com/dhimmel/schema/raw/manubot/csl-data.json'
    # Use jsonref to workaround https://github.com/Julian/jsonschema/issues/447
    schema = jsonref.load_uri(url, jsonschema=True)
    Validator = jsonschema.validators.validator_for(schema)
    Validator.check_schema(schema)
    return Validator(schema)


def remove_jsonschema_errors(instance, recurse_depth=5):
    """
    Remove fields in CSL Items that produce JSON Schema errors. Should errors
    be removed, but the JSON instance still fails to validate, recursively call
    remove_jsonschema_errors until the instance validates or the recursion
    depth limit is reached.

    Note that this method may not be work for all types of JSON Schema errors
    and users looking to adapt it for other applications should write
    task-specific tests to provide empirical evaluate that it works as
    intended.

    See also:
    https://github.com/Julian/jsonschema/issues/448
    https://stackoverflow.com/questions/44694835
    """
    validator = get_jsonschema_csl_validator()
    errors = list(validator.iter_errors(instance))
    instance = copy.deepcopy(instance)
    errors = sorted(errors, key=lambda e: e.path, reverse=True)
    for error in errors:
        _remove_error(instance, error)
    if validator.is_valid(instance) or recurse_depth < 1:
        return instance
    return remove_jsonschema_errors(instance, recurse_depth - 1)


def _delete_elem(instance, path, absolute_path=None, message=''):
    """
    Helper function for remove_jsonschema_errors that deletes an element in the
    JSON-like input instance at the specified path. absolute_path is relative
    to the original validated instance for logging purposes. Defaults to path,
    if not specified. message is an optional string with additional error
    information to log.
    """
    if absolute_path is None:
        absolute_path = path
    logging.debug(
        (f'{message}\n' if message else message) +
        '_delete_elem deleting CSL element at: ' +
        '/'.join(map(str, absolute_path))
    )
    *head, tail = path
    try:
        del _deep_get(instance, head)[tail]
    except KeyError:
        pass


def _deep_get(instance, path):
    """
    Descend path to return a deep element in the JSON object instance.
    """
    for key in path:
        instance = instance[key]
    return instance


def _remove_error(instance, error):
    """
    Remove a jsonschema ValidationError from the JSON-like instance.

    See ValidationError documentation at
    http://python-jsonschema.readthedocs.io/en/latest/errors/#jsonschema.exceptions.ValidationError
    """
    sub_errors = error.context
    if sub_errors:
        # already_removed_additional was neccessary to workaround https://github.com/citation-style-language/schema/issues/154
        already_removed_additional = False
        for sub_error in sub_errors:
            if sub_error.validator == 'additionalProperties':
                if already_removed_additional:
                    continue
                already_removed_additional = True
            sub_instance = _deep_get(instance, error.path)
            _remove_error(sub_instance, sub_error)
    elif error.validator == 'additionalProperties':
        extras = set(error.instance) - set(error.schema['properties'])
        logging.debug(
            error.message +
            f'\nWill now remove these {len(extras)} additional properties.'
        )
        for key in extras:
            _delete_elem(
                instance=instance,
                path=list(error.path) + [key],
                absolute_path=list(error.absolute_path) + [key]
            )
    elif error.validator in {'enum', 'type', 'minItems', 'maxItems'}:
        _delete_elem(instance, error.path, error.absolute_path, error.message)
    elif error.validator == 'required':
        logging.warning(
            (f'{error.message}\n' if error.message else error.message) +
            'requried element missing at: ' +
            '/'.join(map(str, error.absolute_path))
        )
    else:
        raise NotImplementedError(f'{error.validator} is not yet supported')
