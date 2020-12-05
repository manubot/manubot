import json
import logging
import os
import re
import warnings
from typing import List, Optional

import jinja2

from manubot.process.ci import get_continuous_integration_parameters
from manubot.process.manuscript import datetime_now, get_manuscript_stats, get_text
from manubot.process.metadata import (
    get_header_includes,
    get_manuscript_urls,
    get_software_versions,
    get_thumbnail_url,
)
from manubot.util import get_configured_yaml, read_serialized_data, read_serialized_dict


def read_variable_files(paths: List[str], variables: Optional[dict] = None) -> dict:
    """
    Read multiple serialized data files into a user_variables dictionary.
    Provide `paths` (a list of URLs or local file paths).
    Paths can optionally have a namespace prepended.
    For example:

    ```python
    paths = [
        'https://git.io/vbkqm',  # update the dictionary's top-level
        'namespace_1=https://git.io/vbkqm',  # store under 'namespace_1' key
        'namespace_2=some_local_path.json',  # store under 'namespace_2' key
    ]
    ```

    If a namespace is not provided, the JSON must contain a dictionary as its
    top level. Namespaces should consist only of ASCII alphanumeric characters
    (includes underscores, first character cannot be numeric).

    Pass a dictionary to `variables` to update an existing dictionary rather
    than create a new dictionary.
    """
    if variables is None:
        variables = {}
    for path in paths:
        logging.info(f"Reading user-provided templating variables at {path!r}")
        # Match only namespaces that are valid jinja2 variable names
        # http://jinja.pocoo.org/docs/2.10/api/#identifier-naming
        match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)=(.+)", path)
        if match:
            namespace, path = match.groups()
            logging.info(
                f"Using the {namespace!r} namespace for template variables from {path!r}"
            )
        try:
            if match:
                obj = {namespace: read_serialized_data(path)}
            else:
                obj = read_serialized_dict(path)
        except Exception:
            logging.exception(f"Error reading template variables from {path!r}")
            continue
        assert isinstance(obj, dict)
        conflicts = variables.keys() & obj.keys()
        if conflicts:
            logging.warning(
                f"Template variables in {path!r} overwrite existing "
                "values for the following keys:\n" + "\n".join(conflicts)
            )
        variables.update(obj)
    logging.debug(
        f"Reading user-provided templating variables complete:\n"
        f"{json.dumps(variables, indent=2, ensure_ascii=False)}"
    )
    return variables


def _convert_field_to_list(
    dictionary, field, separator=False, deprecation_warning_key=None
):
    """
    Convert `dictionary[field]` to a list. If value is a string and
    `separator` is specified, split by `separator`. If `deprecation_warning_key`
    is provided, warn when `dictionary[field]` is a string.
    """
    if field not in dictionary:
        return dictionary
    value = dictionary[field]
    if isinstance(value, list):
        return dictionary
    if isinstance(value, str):
        if separator is False:
            dictionary[field] = [value]
        else:
            dictionary[field] = value.split(separator)
        if deprecation_warning_key:
            warnings.warn(
                f"Expected list for {dictionary.get(deprecation_warning_key)}'s {field}. "
                + (
                    f"Assuming multiple {field} are `{separator}` separated. "
                    if separator
                    else ""
                )
                + f"Please switch {field} to a list.",
                category=DeprecationWarning,
            )
        return dictionary
    raise ValueError("Unsupported value type {value.__class__.__name__}")


def add_author_affiliations(variables: dict) -> dict:
    """
    Edit variables to contain numbered author affiliations. Specifically,
    add a list of affiliation_numbers for each author and add a list of
    affiliations to the top-level of variables. If no authors have any
    affiliations, variables is left unmodified.
    """
    affiliations = list()
    for author in variables["authors"]:
        _convert_field_to_list(
            dictionary=author,
            field="affiliations",
            separator="; ",
            deprecation_warning_key="name",
        )
        _convert_field_to_list(
            dictionary=author,
            field="funders",
        )
        affiliations.extend(author.get("affiliations", []))
    if not affiliations:
        return variables
    affiliations = list(dict.fromkeys(affiliations))  # deduplicate
    affil_to_number = {affil: i for i, affil in enumerate(affiliations, start=1)}
    for author in variables["authors"]:
        numbers = [affil_to_number[affil] for affil in author.get("affiliations", [])]
        author["affiliation_numbers"] = sorted(numbers)
    variables["affiliations"] = [
        dict(affiliation=affil, affiliation_number=i)
        for affil, i in affil_to_number.items()
    ]
    return variables


def load_variables(args) -> dict:
    """
    Read `metadata.yaml` and files specified by `--template-variables-path` to generate
    manuscript variables available for jinja2 templating.

    Returns a dictionary, refered to as `variables`, with the following keys:

    - `pandoc`: a dictionary for passing options to Pandoc via the `yaml_metadata_block`.
      Fields in `pandoc` are either generated by Manubot or hard-coded by the user if `metadata.yaml`
      includes a `pandoc` dictionary.
    - `manubot`: a dictionary for manubot-related information and metadata.
      Fields in `manubot` are either generated by Manubot or hard-coded by the user if `metadata.yaml`
      includes a `manubot` dictionary.
    - All fields from a manuscript's `metadata.yaml` that are not interpreted by Manubot are
      copied to `variables`. Interpreted fields include `pandoc`, `manubot`, `title`,
      `keywords`, `authors` (formerly `author_info`, now deprecated), `lang`, and `thumbnail`.
    - User-specified fields inserted according to the `--template-variables-path` option.
      User-specified variables take highest precedence and can overwrite values for existing
      keys like `pandoc` or `manubot` (dangerous).
    """
    # Generated manuscript variables
    variables = {"pandoc": {}, "manubot": {}}

    # Read metadata which contains pandoc_yaml_metadata
    # as well as authors information.
    if args.meta_yaml_path.is_file():
        metadata = read_serialized_dict(args.meta_yaml_path)
    else:
        metadata = {}
        logging.warning(
            f"missing {args.meta_yaml_path} file with yaml_metadata_block for pandoc"
        )

    # Interpreted keys that are intended for pandoc
    move_to_pandoc = "title", "keywords", "lang"
    for key in move_to_pandoc:
        if key in metadata:
            variables["pandoc"][key] = metadata.pop(key)

    # Add date to metadata
    now = datetime_now()
    logging.info(
        f"Using {now:%Z} timezone.\n"
        f"Dating manuscript with the current datetime: {now.isoformat()}"
    )
    variables["pandoc"]["date-meta"] = now.date().isoformat()
    variables["manubot"]["date"] = f"{now:%B} {now.day}, {now.year}"

    # Process authors metadata
    if "author_info" in metadata:
        authors = metadata.pop("author_info", [])
        warnings.warn(
            "metadata.yaml: 'author_info' is deprecated. Use 'authors' instead.",
            category=DeprecationWarning,
        )
    else:
        authors = metadata.pop("authors", [])
    if authors is None:
        authors = []
    variables["pandoc"]["author-meta"] = [author["name"] for author in authors]
    variables["manubot"]["authors"] = authors
    add_author_affiliations(variables["manubot"])

    # Set repository version metadata for CI builds
    ci_params = get_continuous_integration_parameters()
    if ci_params:
        variables["manubot"]["ci_source"] = ci_params

    # Add manuscript URLs
    variables["manubot"].update(get_manuscript_urls(metadata.pop("html_url", None)))

    # Add software versions
    variables["manubot"].update(get_software_versions())

    # Add thumbnail URL if present
    thumbnail_url = get_thumbnail_url(metadata.pop("thumbnail", None))
    if thumbnail_url:
        variables["manubot"]["thumbnail_url"] = thumbnail_url

    # Update variables with metadata.yaml pandoc/manubot dicts
    for key in "pandoc", "manubot":
        dict_ = metadata.pop(key, {})
        if not isinstance(dict_, dict):
            logging.warning(
                f"load_variables expected metadata.yaml field {key!r} to be a dict."
                f"Received a {dict_.__class__.__name__!r} instead."
            )
            continue
        variables[key].update(dict_)

    # Update variables with uninterpreted metadata.yaml fields
    variables.update(metadata)

    # Update variables with user-provided variables here
    variables = read_variable_files(args.template_variables_path, variables)

    # Add header-includes metadata with <meta> information for the HTML output's <head>
    variables["pandoc"]["header-includes"] = get_header_includes(variables)

    assert args.skip_citations
    # Extend Pandoc's metadata.bibliography field with manual references paths
    bibliographies = variables["pandoc"].get("bibliography", [])
    if isinstance(bibliographies, str):
        bibliographies = [bibliographies]
    assert isinstance(bibliographies, list)
    bibliographies.extend(args.manual_references_paths)
    bibliographies = list(map(os.fspath, bibliographies))
    variables["pandoc"]["bibliography"] = bibliographies
    # enable pandoc-manubot-cite option to write bibliography to a file
    variables["pandoc"]["manubot-output-bibliography"] = os.fspath(args.references_path)
    variables["pandoc"]["manubot-output-citekeys"] = os.fspath(args.citations_path)
    variables["pandoc"]["manubot-requests-cache-path"] = os.fspath(
        args.requests_cache_path
    )
    variables["pandoc"]["manubot-clear-requests-cache"] = args.clear_requests_cache

    return variables


def template_with_jinja2(text, variables):
    """
    Template using jinja2 with the variables dictionary unpacked as keyword
    arguments.
    """
    jinja_environment = jinja2.Environment(
        loader=jinja2.BaseLoader(),
        undefined=jinja2.make_logging_undefined(logging.getLogger()),
        autoescape=False,
        comment_start_string="{##",
        comment_end_string="##}",
        extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols"],
    )
    template = jinja_environment.from_string(text)
    return template.render(**variables)


def prepare_manuscript(args):
    """
    Compile manuscript, creating manuscript.md and references.json as inputs
    for pandoc.
    """
    text = get_text(args.content_directory)
    assert args.skip_citations

    variables = load_variables(args)
    variables["manubot"]["manuscript_stats"] = get_manuscript_stats(text)
    with args.variables_path.open("w", encoding="utf-8") as write_file:
        json.dump(variables, write_file, ensure_ascii=False, indent=2)
        write_file.write("\n")

    text = template_with_jinja2(text, variables)

    # Write manuscript for pandoc
    yaml = get_configured_yaml()
    with args.manuscript_path.open("w", encoding="utf-8") as write_file:
        yaml.dump(
            variables["pandoc"],
            write_file,
            default_flow_style=False,
            explicit_start=True,
            explicit_end=True,
            width=float("inf"),
            allow_unicode=True,
            sort_keys=False,
        )
        write_file.write("\n")
        write_file.write(text)
