import collections
import pathlib

from manubot.citations import citation_pattern, is_valid_citation_string


def get_citation_strings(text):
    """
    Extract the deduplicated list of citations in a text
    """
    citations_strings = set(citation_pattern.findall(text))
    citations_strings = filter(is_valid_citation_string, citations_strings)
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
    return '\n\n'.join(name_to_text.values())
