"""
Compact Uniform Resource Identifiers

Manubot keeps a local versions of the identifier.org registry.
Repository developers can run the following commands to update the Manubot version.

```shell
# regenerate manubot/cite/curie/namespaces.json
python manubot/cite/curie/__init__.py
# if namespaces.json has changed, the following test will likely fail:
pytest manubot/cite/tests/test_handlers.py::test_prefix_to_handler
# copy captured stdout from failed test_prefix_to_handler to
# manubot.cite.handlers.prefix_to_handler. Pre-commit hook will reformat file.
```

References:

- https://en.wikipedia.org/wiki/CURIE
- https://identifiers.org/
- https://github.com/manubot/manubot/issues/218
- https://docs.identifiers.org/articles/api.html
- https://n2t.net/e/compact_ids.html
- https://n2t.net/e/cdl_ebi_prefixes.yaml
- https://en.wikipedia.org/wiki/MIRIAM_Registry
- [Identifiers.org and MIRIAM Registry: community resources to provide persistent identification](https://doi.org/10.1093/nar/gkr1097)
- [On the road to robust data citation](https://doi.org/10.1038/sdata.2018.95)
- [Uniform Resolution of Compact Identifiers for Biomedical Data](https://doi.org/10.1038/sdata.2018.29)
"""
import dataclasses
import functools
import json
import logging
import pathlib
import re
import typing

from manubot.cite.handlers import Handler

_keep_namespace_fields = {
    "prefix",
    "mirId",  # MIRIAM Registry identifier
    "name",
    "pattern",  # regex pattern
    "description",
    "sampleId",  # example identifier
    "namespaceEmbeddedInLui",  # whether prefix is included in the local unique identifier
    "curiePrefix",  # a computed field for the actual prefix used by CURIEs including required capitalization
}


namespace_path = pathlib.Path(__file__).parent.joinpath("namespaces.json")


@dataclasses.dataclass
class Handler_CURIE(Handler):
    def __post_init__(self):
        prefix_to_namespace = get_prefix_to_namespace()
        self.namespace = prefix_to_namespace[self.prefix_lower]
        self.standard_prefix = self.namespace["prefix"]
        self.prefixes = sorted(
            {self.namespace["prefix"], self.namespace["curiePrefix"].lower()}
        )
        self.accession_pattern = self.namespace["pattern"]

    def get_csl_item(self, citekey):
        from ..url import get_url_csl_item

        url = curie_to_url(citekey.standard_id)
        return get_url_csl_item(url)

    def _get_lui(self, citekey) -> str:
        """
        When namespaceEmbeddedInLui is true, some identifiers.org namespace
        metadata, such as pattern, include curiePrefix. This function
        returns the local unique identifier (lui / accession) based on this
        caveat.
        """
        lui = citekey.accession
        if self.namespace.get("namespaceEmbeddedInLui", False):
            lui = f"{self.namespace['curiePrefix']}:{lui}"
        return lui

    def inspect(self, citekey):
        pattern = self._get_pattern("accession_pattern")
        lui = self._get_lui(citekey)
        if not pattern.fullmatch(lui):
            return f"{lui} does not match regex {pattern.pattern}"


def get_curie_handlers():
    """Get all possible CURIE handlers"""
    namespaces = get_namespaces(compile_patterns=True)
    handlers = [Handler_CURIE(ns["prefix"]) for ns in namespaces]
    return handlers


def _download_namespaces():
    """
    Download all namespaces from the Identifiers.org Central Registry.

    Example of a single namespace JSON data at
    <https://registry.api.identifiers.org/restApi/namespaces/230>
    """
    import requests

    params = dict(size=5000, sort="prefix")
    url = "https://registry.api.identifiers.org/restApi/namespaces"
    response = requests.get(url, params)
    response.raise_for_status()
    results = response.json()
    if results["page"]["totalPages"] > 1:
        logging.warning(
            "_download_curie_registry does not support multi-page results\n"
            f"{response.url}\n{json.dumps(results['page'])}"
        )
    namespaces = results["_embedded"]["namespaces"]
    # filter namespace fields to reduce diskspace
    for namespace in namespaces:
        namespace["curiePrefix"] = get_curie_prefix(namespace)
        for field in set(namespace) - _keep_namespace_fields:
            del namespace[field]
    json_text = json.dumps(namespaces, indent=2, ensure_ascii=False)
    namespace_path.write_text(json_text + "\n", encoding="utf-8")


def get_curie_prefix(namespace):
    """
    The prefix portion of a CURIE is not always the same as the identifiers.org namespace prefix.
    This occurs when namespaceEmbeddedInLui is true.
    When namespaceEmbeddedInLui, CURIEs require a specific prefix capitalization.
    The actual prefix and capitalization is reverse engineered from the regex pattern.

    References:
    https://github.com/identifiers-org/identifiers-org.github.io/issues/100#issuecomment-614679142

    """
    if not namespace["namespaceEmbeddedInLui"]:
        return namespace["prefix"]
    import exrex

    example_curie = exrex.getone(namespace["pattern"])
    curie_prefix, _ = example_curie.split(":", 1)
    return curie_prefix


def get_namespaces(compile_patterns=False) -> typing.List[dict]:
    with namespace_path.open(encoding="utf-8-sig") as read_file:
        namespaces = json.load(read_file)
    if compile_patterns:
        for namespace in namespaces:
            namespace["compiled_pattern"] = re.compile(namespace["pattern"])
    return namespaces


@functools.lru_cache()
def get_prefix_to_namespace() -> typing.Dict[str, typing.Dict]:
    prefix_to_namespace = dict()
    for ns in get_namespaces():
        for key in "prefix", "curiePrefix":
            prefix_to_namespace[ns[key].lower()] = ns
    return prefix_to_namespace


def standardize_curie(curie):
    """
    Return CURIE with identifiers.org expected capitalization.
    `curie` should be in `prefix:accession` format.
    If `curie` is malformed or uses an unrecognized prefix, raise ValueError.
    """
    if not isinstance(curie, str):
        raise TypeError(
            f"curie parameter should be string. Received {curie.__class__.__name__} instead for {curie}"
        )
    try:
        prefix, accession = curie.split(":", 1)
    except ValueError:
        raise ValueError(
            f"curie must be splittable by `:` and formatted like `prefix:accession`. Received {curie}"
        )
    # do not yet understand capitalization
    # https://github.com/identifiers-org/identifiers-org.github.io/issues/100
    prefix_lower = prefix.lower()
    prefix_to_namespaces = get_prefix_to_namespace()
    try:
        namespace = prefix_to_namespaces[prefix_lower]
    except KeyError:
        raise ValueError(
            f"prefix {prefix_lower} for {curie} is not a recognized prefix"
        )
    return f"{namespace['curiePrefix']}:{accession}"


def curie_to_url(curie):
    """
    `curie` should be in `prefix:accession` format
    """
    curie = standardize_curie(curie)
    resolver_url = "https://identifiers.org"
    return f"{resolver_url}/{curie}"


if __name__ == "__main__":
    _download_namespaces()
    namespaces = get_namespaces()
