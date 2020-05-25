import datetime
import json
import logging
import pathlib


def get_text(directory):
    """
    Return a concatenated string of section texts from the specified directory.
    Text files should be UTF-8 encoded.
    """
    section_dir = pathlib.Path(directory)
    paths = sorted(section_dir.glob("[0-9]*.md"))
    name_to_text = dict()
    for path in paths:
        name_to_text[path.stem] = path.read_text(encoding="utf-8-sig")
    logging.info("Manuscript content parts:\n" + "\n".join(name_to_text))
    return "\n\n".join(name_to_text.values()) + "\n"


def get_manuscript_stats(text):
    """
    Compute manuscript statistics.
    """
    stats = dict()
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
