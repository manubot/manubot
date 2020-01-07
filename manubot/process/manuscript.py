import collections
import datetime
import json
import logging
import pathlib
import re

from manubot.cite.citekey import citekey_pattern, is_valid_citekey


def get_citekeys(text):
    """
    Extract the deduplicated list of citations in a text. Citations that are
    clearly invalid such as `doi:/453` are not returned.
    """
    citekeys = set(citekey_pattern.findall(text))
    citekeys = filter(
        lambda x: is_valid_citekey(
            x, allow_tag=True, allow_raw=True, allow_pandoc_xnos=True
        ),
        citekeys,
    )
    return sorted(citekeys)


def get_text(directory):
    """
    Return a concatenated string of section texts from the specified directory.
    Text files should be UTF-8 encoded.
    """
    section_dir = pathlib.Path(directory)
    paths = sorted(section_dir.glob("[0-9]*.md"))
    name_to_text = collections.OrderedDict()
    for path in paths:
        name_to_text[path.stem] = path.read_text(encoding="utf-8-sig")
    logging.info("Manuscript content parts:\n" + "\n".join(name_to_text))
    return "\n\n".join(name_to_text.values()) + "\n"


def update_manuscript_citekeys(text, old_to_new):
    """
    Replace citation keys according to the old_to_new dictionary.
    Useful for converting citation keys to shortened versions
    that are appropriate for pandoc.

    `text` is markdown source text

    `old_to_new` is a dictionary like:
    doi:10.7287/peerj.preprints.3100v1 → 11cb5HXoY
    """
    for old, new in old_to_new.items():
        text = re.sub(
            pattern=re.escape("@" + old) + r"(?![\w:.#$%&\-+?<>~/]*[a-zA-Z0-9/])",
            repl="@" + new,
            string=text,
        )
    return text


def get_manuscript_stats(text, citekeys_df=None):
    """
    Compute manuscript statistics.
    """
    stats = collections.OrderedDict()

    if citekeys_df is not None:
        # Number of distinct references by type
        ref_counts = (
            citekeys_df.standard_citekey.drop_duplicates()
            .map(lambda x: x.split(":")[0])
            .pipe(collections.Counter)
        )
        ref_counts["total"] = sum(ref_counts.values())
        stats["reference_counts"] = ref_counts
    stats["word_count"] = len(text.split())
    logging.info(f"Generated manscript stats:\n{json.dumps(stats, indent=2)}")
    return stats


def datetime_now():
    """
    Return the current datetime, with timezone awareness
    https://stackoverflow.com/a/39079819/4651668
    """
    tzinfo = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    return datetime.datetime.now(tzinfo)
