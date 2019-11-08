import collections
import json
import logging
import pathlib
import re
import textwrap
import warnings

import jinja2
import pandas
import requests
import requests_cache
import yaml

from manubot.process.bibliography import load_manual_references
from manubot.process.ci import (
    add_manuscript_urls_to_ci_params,
    get_continuous_integration_parameters,
)
from manubot.process.thumbnail import get_thumbnail_url
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


def read_json(path):
    """
    Read json from a path or URL.
    """
    if re.match("^(http|ftp)s?://", path):
        response = requests.get(path)
        obj = response.json(object_pairs_hook=collections.OrderedDict)
    else:
        path = pathlib.Path(path)
        with path.open(encoding="utf-8-sig") as read_file:
            obj = json.load(read_file, object_pairs_hook=collections.OrderedDict)
    return obj


def read_jsons(paths):
    """
    Read multiple JSON files into a user_variables dictionary. Provide a list
    of paths (URLs or filepaths). Paths can optionally have a namespace
    prepended. For example:

    ```
    paths = [
        'https://git.io/vbkqm',  # update the dictionary's top-level
        'namespace_1=https://git.io/vbkqm',  # store under 'namespace_1' key
        'namespace_2=some_local_path.json',  # store under 'namespace_2' key
    ]
    ```

    If a namespace is not provided, the JSON must contain a dictionary as its
    top level. Namespaces should consist only of ASCII alphanumeric characters
    (includes underscores, first character cannot be numeric).
    """
    user_variables = collections.OrderedDict()
    for path in paths:
        logging.info(
            f"Read the following user-provided templating variables for {path}"
        )
        # Match only namespaces that are valid jinja2 variable names
        # http://jinja.pocoo.org/docs/2.10/api/#identifier-naming
        match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)=(.+)", path)
        if match:
            namespace, path = match.groups()
            logging.info(
                f'Using the "{namespace}" namespace for template variables from {path}'
            )
        try:
            obj = read_json(path)
        except Exception:
            logging.exception(f"Error reading template variables from {path}")
            continue
        if match:
            obj = {namespace: obj}
        assert isinstance(obj, dict)
        conflicts = user_variables.keys() & obj.keys()
        if conflicts:
            logging.warning(
                f"Template variables in {path} overwrite existing "
                "values for the following keys:\n" + "\n".join(conflicts)
            )
        user_variables.update(obj)
    logging.info(
        f"Reading user-provided templating variables complete:\n"
        f"{json.dumps(user_variables, indent=2, ensure_ascii=False)}"
    )
    return user_variables


def add_author_affiliations(variables):
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


def get_metadata_and_variables(args):
    """
    Process metadata.yaml and create variables available for jinja2 templating.
    """
    # Generated manuscript variables
    variables = collections.OrderedDict()

    # Read metadata which contains pandoc_yaml_metadata
    # as well as author_info.
    if args.meta_yaml_path.is_file():
        with args.meta_yaml_path.open(encoding="utf-8-sig") as read_file:
            metadata = yaml.safe_load(read_file)
            assert isinstance(metadata, dict)
    else:
        metadata = {}
        logging.warning(
            f"missing {args.meta_yaml_path} file with yaml_metadata_block for pandoc"
        )

    # Add date to metadata
    now = datetime_now()
    logging.info(
        f"Using {now:%Z} timezone.\n"
        f"Dating manuscript with the current datetime: {now.isoformat()}"
    )
    metadata["date-meta"] = now.date().isoformat()
    variables["date"] = f"{now:%B} {now.day}, {now.year}"

    # Process authors metadata
    authors = metadata.pop("author_info", [])
    if authors is None:
        authors = []
    metadata["author-meta"] = [author["name"] for author in authors]
    variables["authors"] = authors
    variables = add_author_affiliations(variables)

    # Set repository version metadata for CI builds
    ci_params = get_continuous_integration_parameters()
    if ci_params:
        variables["ci_source"] = add_manuscript_urls_to_ci_params(ci_params)

    # Add thumbnail URL if present
    thumbnail_url = get_thumbnail_url(metadata.pop("thumbnail", None))
    if thumbnail_url:
        variables["thumbnail_url"] = thumbnail_url

    # Update variables with user-provided variables here
    user_variables = read_jsons(args.template_variables_path)
    variables.update(user_variables)

    # Add header-includes metadata with <meta> information for the HTML output's <head>
    metadata["header-includes"] = get_header_includes(variables)

    return metadata, variables


def get_header_includes(variables: dict) -> str:
    """
    Render `header-includes-template.html` using information from `variables`.
    """
    path = pathlib.Path(__file__).parent.joinpath("header-includes-template.html")
    try:
        template = path.read_text(encoding="utf-8-sig")
        return template_with_jinja2(template, variables)
    except Exception:
        logging.exception(f"Error generating header-includes.")
        return ""


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
        comment_start_string="{##",
        comment_end_string="##}",
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

    metadata, variables = get_metadata_and_variables(args)
    variables["manuscript_stats"] = get_manuscript_stats(text, citekeys_df)
    with args.variables_path.open("w", encoding="utf-8") as write_file:
        json.dump(variables, write_file, ensure_ascii=False, indent=2)
        write_file.write("\n")

    text = template_with_jinja2(text, variables)

    # Write manuscript for pandoc
    with args.manuscript_path.open("w", encoding="utf-8") as write_file:
        yaml.dump(
            metadata,
            write_file,
            default_flow_style=False,
            explicit_start=True,
            explicit_end=True,
        )
        write_file.write("\n")
        write_file.write(text)
