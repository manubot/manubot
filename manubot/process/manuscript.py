import collections
import datetime
import json
import logging
import pathlib
import re

from manubot.cite.util import (
    citation_pattern,
    is_valid_citation_string,
)


def get_citation_strings(text):
    """
    Extract the deduplicated list of citations in a text. Citations that are
    clearly invalid such as `doi:/453` are not returned.
    """
    citations_strings = set(citation_pattern.findall(text))
    citations_strings = filter(
        lambda x: is_valid_citation_string(x, allow_tag=True, allow_raw=True, allow_pandoc_xnos=True),
        citations_strings,
    )
    return sorted(citations_strings)


def get_text(directory):
    """
    Return a concatenated string of section texts from the specified directory.
    """
    section_dir = pathlib.Path(directory)
    paths = sorted(section_dir.glob('[0-9]*.md'))
    name_to_text = collections.OrderedDict()
    for path in paths:
        name_to_text[path.stem] = path.read_text()
    logging.info('Manuscript content parts:\n' + '\n'.join(name_to_text))
    return '\n\n'.join(name_to_text.values()) + '\n'


def replace_citations_strings_with_ids(text, string_to_id):
    """
    Convert citations to their IDs for pandoc.

    `text` is markdown source text

    `string_to_id` is a dictionary like:
    @10.7287/peerj.preprints.3100v1 → 11cb5HXoY
    """
    for old, new in string_to_id.items():
        text = re.sub(
            pattern=re.escape(old) + r'(?![\w:.#$%&\-+?<>~/]*[a-zA-Z0-9/])',
            repl='@' + new,
            string=text,
        )
    return text


def get_manuscript_stats(text, citation_df):
    """
    Compute manuscript statistics.
    """
    stats = collections.OrderedDict()

    # Number of distinct references by type
    ref_counts = (
        citation_df
        .standard_citation
        .drop_duplicates()
        .map(lambda x: x.split(':')[0])
        .pipe(collections.Counter)
    )
    ref_counts['total'] = sum(ref_counts.values())
    stats['reference_counts'] = ref_counts
    stats['word_count'] = len(text.split())
    logging.info(f"Generated manscript stats:\n{json.dumps(stats, indent=2)}")
    return stats


def datetime_now():
    """
    Return the current datetime, with timezone awareness
    https://stackoverflow.com/a/39079819/4651668
    """
    tzinfo = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    return datetime.datetime.now(tzinfo)
