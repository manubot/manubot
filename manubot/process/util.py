import collections
import json
import logging
import re
import textwrap
import warnings
from typing import List, Optional

import jinja2
import pandas
import requests
import requests_cache
import yaml

from manubot.util import read_serialized_data, read_serialized_dict
from manubot.process.bibliography import load_manual_references
from manubot.process.ci import get_continuous_integration_parameters
from manubot.process.metadata import (
    get_header_includes,
    get_thumbnail_url,
    get_manuscript_urls,
)
from manubot.process.manuscript import (
    datetime_now,
    get_citekeys,
    get_manuscript_stats,
    get_text,
    update_manuscript_citekeys,
)
from manubot.cite.citekey import (
    citekey_to_csl_item,
    shorten_citekey,
    is_valid_citekey,
    standardize_citekey,
)


def check_collisions(citekeys_df):
    """
    Check for short_citekey hash collisions
    """
    collision_df = citekeys_df[["standard_citekey", "short_citekey"]].drop_duplicates()
    collision_df = collision_df[collision_df.short_citekey.duplicated(keep=False)]
    if not collision_df.empty:
        logging.error(f"OMF! Hash collision. Congratulations.\n{collision_df}")
    return collision_df


def check_multiple_citation_strings(citekeys_df):
    """
    Identify different citation strings referring the the same reference.
    """
    message = textwrap.dedent(
        f"""\
    {len(citekeys_df)} unique citations strings extracted from text
    {citekeys_df.standard_citekey.nunique()} unique standard citations\
    """
    )
    logging.info(message)
    multi_df = citekeys_df[citekeys_df.standard_citekey.duplicated(keep=False)]
    if not multi_df.empty:
        table = multi_df.to_string(
            index=False, columns=["standard_citekey", "manuscript_citekey"]
        )
        logging.warning(f"Multiple citekeys detected for the same reference:\n{table}")
    return multi_df


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


def add_author_affiliations(variables: dict) -> dict:
    """
    Edit variables to contain numbered author affiliations. Specifically,
    add a list of affiliation_numbers for each author and add a list of
    affiliations to the top-level of variables. If no authors have any
    affiliations, variables is left unmodified.
    """
    rows = list()
    for author in variables["authors"]:
        if "affiliations" not in author:
            continue
        if not isinstance(author["affiliations"], list):
            warnings.warn(
                f"Expected list for {author['name']}'s affiliations. "
                f"Assuming multiple affiliations are `; ` separated. "
                f"Please switch affiliations to a list.",
                category=DeprecationWarning,
            )
            author["affiliations"] = author["affiliations"].split("; ")
        for affiliation in author["affiliations"]:
            rows.append((author["name"], affiliation))
    if not rows:
        return variables
    affil_map_df = pandas.DataFrame(rows, columns=["name", "affiliation"])
    affiliation_df = affil_map_df[["affiliation"]].drop_duplicates()
    affiliation_df["affiliation_number"] = range(1, 1 + len(affiliation_df))
    affil_map_df = affil_map_df.merge(affiliation_df)
    name_to_numbers = {
        name: sorted(df.affiliation_number) for name, df in affil_map_df.groupby("name")
    }
    for author in variables["authors"]:
        author["affiliation_numbers"] = name_to_numbers.get(author["name"], [])
    variables["affiliations"] = affiliation_df.to_dict(orient="records")
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
      `keywords`, `author_info`, `lang`, and `thumbnail`.
    - User-specified fields inserted according to the `--template-variables-path` option.
      User-specified variables take highest precedence and can overwrite values for existing
      keys like `pandoc` or `manubot` (dangerous).
    """
    # Generated manuscript variables
    variables = {"pandoc": {}, "manubot": {}}

    # Read metadata which contains pandoc_yaml_metadata
    # as well as author_info.
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
    authors = metadata.pop("author_info", [])
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

    return variables


def get_citekeys_df(args, text):
    """
    Generate citekeys_df and save it to 'citations.tsv'.
    citekeys_df is a pandas.DataFrame with the following columns:
    - manuscript_citekey: citation keys extracted from the manuscript content files.
    - detagged_citekey: manuscript_citekey but with tag citekeys dereferenced
    - standard_citekey: detagged_citekey standardized
    - short_citekey: standard_citekey hashed to create a shortened citekey
    """
    citekeys_df = pandas.DataFrame({"manuscript_citekey": get_citekeys(text)})
    if args.citation_tags_path.is_file():
        tag_df = pandas.read_csv(args.citation_tags_path, sep="\t")
        na_rows_df = tag_df[tag_df.isnull().any(axis="columns")]
        if not na_rows_df.empty:
            logging.error(
                f"{args.citation_tags_path} contains rows with missing values:\n"
                f"{na_rows_df}\n"
                "This error can be caused by using spaces rather than tabs to delimit fields.\n"
                "Proceeding to reread TSV with delim_whitespace=True."
            )
            tag_df = pandas.read_csv(args.citation_tags_path, delim_whitespace=True)
        tag_df["manuscript_citekey"] = "tag:" + tag_df.tag
        tag_df = tag_df.rename(columns={"citation": "detagged_citekey"})
        for detagged_citekey in tag_df.detagged_citekey:
            is_valid_citekey(detagged_citekey, allow_raw=True)
        citekeys_df = citekeys_df.merge(
            tag_df[["manuscript_citekey", "detagged_citekey"]], how="left"
        )
    else:
        citekeys_df["detagged_citekey"] = None
        logging.info(
            f"missing {args.citation_tags_path} file: no citation tags (citekey aliases) set"
        )
    citekeys_df.detagged_citekey.fillna(
        citekeys_df.manuscript_citekey.astype(str), inplace=True
    )
    citekeys_df["standard_citekey"] = citekeys_df.detagged_citekey.map(
        standardize_citekey
    )
    citekeys_df["short_citekey"] = citekeys_df.standard_citekey.map(shorten_citekey)
    citekeys_df = citekeys_df.sort_values(["standard_citekey", "detagged_citekey"])
    citekeys_df.to_csv(args.citations_path, sep="\t", index=False)
    check_collisions(citekeys_df)
    check_multiple_citation_strings(citekeys_df)
    return citekeys_df


def generate_csl_items(args, citekeys_df):
    """
    General CSL (citeproc) items for standard_citekeys in citekeys_df.
    Writes references.json to disk and logs warnings for potential problems.
    """
    # Read manual references (overrides) in JSON CSL
    manual_refs = load_manual_references(args.manual_references_paths)

    requests  # require `import requests` in case this is essential for monkey patching by requests_cache.
    requests_cache.install_cache(args.requests_cache_path, include_get_headers=True)
    cache = requests_cache.get_cache()
    if args.clear_requests_cache:
        logging.info("Clearing requests-cache")
        requests_cache.clear()
    logging.info(
        f"requests-cache starting with {len(cache.responses)} cached responses"
    )

    csl_items = list()
    failures = list()
    for standard_citekey in citekeys_df.standard_citekey.unique():
        if standard_citekey in manual_refs:
            csl_items.append(manual_refs[standard_citekey])
            continue
        elif standard_citekey.startswith("raw:"):
            logging.error(
                f"CSL JSON Data with a standard_citekey of {standard_citekey!r} not found in manual-references.json. "
                "Metadata must be provided for raw citekeys."
            )
            failures.append(standard_citekey)
        try:
            csl_item = citekey_to_csl_item(standard_citekey)
            csl_items.append(csl_item)
        except Exception:
            logging.exception(f"Citeproc retrieval failure for {standard_citekey!r}")
            failures.append(standard_citekey)

    logging.info(
        f"requests-cache finished with {len(cache.responses)} cached responses"
    )
    requests_cache.uninstall_cache()

    if failures:
        message = "CSL JSON Data retrieval failed for the following standardized citation keys:\n{}".format(
            "\n".join(failures)
        )
        logging.error(message)

    # Write JSON CSL bibliography for Pandoc.
    with args.references_path.open("w", encoding="utf-8") as write_file:
        json.dump(csl_items, write_file, indent=2, ensure_ascii=False)
        write_file.write("\n")
    return csl_items


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
    citekeys_df = get_citekeys_df(args, text)

    generate_csl_items(args, citekeys_df)

    citekey_mapping = collections.OrderedDict(
        zip(citekeys_df.manuscript_citekey, citekeys_df.short_citekey)
    )
    text = update_manuscript_citekeys(text, citekey_mapping)

    variables = load_variables(args)
    variables["manubot"]["manuscript_stats"] = get_manuscript_stats(text, citekeys_df)
    with args.variables_path.open("w", encoding="utf-8") as write_file:
        json.dump(variables, write_file, ensure_ascii=False, indent=2)
        write_file.write("\n")

    text = template_with_jinja2(text, variables)

    # Write manuscript for pandoc
    with args.manuscript_path.open("w", encoding="utf-8") as write_file:
        yaml.dump(
            variables["pandoc"],
            write_file,
            default_flow_style=False,
            explicit_start=True,
            explicit_end=True,
            width=float("inf"),
        )
        write_file.write("\n")
        write_file.write(text)
