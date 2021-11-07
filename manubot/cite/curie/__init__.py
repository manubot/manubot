"""
Compact Uniform Resource Identifiers

Manubot keeps a local versions of the Bioregistry.
Repository developers can run the following commands to update the Manubot version.

```shell
# regenerate manubot/cite/curie/bioregistry.json
python manubot/cite/curie/__init__.py
# if bioregistry.json has changed, the following test will likely fail:
pytest manubot/cite/tests/test_handlers.py::test_prefix_to_handler
# copy captured stdout from failed test_prefix_to_handler to
# manubot.cite.handlers.prefix_to_handler. Pre-commit hook will reformat file.
```

References:

- https://bioregistry.io/
- https://github.com/biopragmatics/bioregistry
- https://en.wikipedia.org/wiki/CURIE
- https://cthoyt.com/2021/10/07/biopragmatics-glossary.html
- https://github.com/manubot/manubot/issues/305
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
import pathlib
import re
import typing

from manubot.cite.citekey import CiteKey
from manubot.cite.handlers import Handler

_keep_bioregistry_fields = {
    "deprecated",
    "example",
    "uri_format",
    "name",
    "pattern",
    "preferred_prefix",
    "synonyms",
}


bioregistry_path = pathlib.Path(__file__).parent.joinpath("bioregistry.json")


valid_prefix_pattern = re.compile(r"^[a-z0-9][a-z0-9._-]+?$")
"""
Ignore Bioregistry prefixes/synonyms that do not adhere to this pattern.
More permissive than the pattern at <https://github.com/biopragmatics/bioregistry/issues/158>,
because there are existing Bioregistry prefixes, even preferred prefixes, that are bad.
For example, starting with a number. We primarily care whether the prefix will work as part
of a pandoc citation key without requiring escaping.
"""


@dataclasses.dataclass
class Handler_CURIE(Handler):
    def __post_init__(self):
        try:
            self.resource = get_prefix_to_resource()[self.prefix_lower]
        except KeyError:
            raise ValueError(f"Unrecognized CURIE prefix {self.prefix_lower}")
        self.standard_prefix = (
            self.resource.get("preferred_prefix") or self.resource["prefix"]
        )
        self.prefixes = self.resource["all_prefixes"]
        if "pattern" in self.resource:
            self.accession_pattern = self.resource["pattern"]

    def get_csl_item(self, citekey: CiteKey):
        from ..url import get_url_csl_item

        url = self.get_url(accession=citekey.standard_accession)
        return get_url_csl_item(url)

    def inspect(self, citekey: CiteKey) -> typing.Optional[str]:
        pattern = self._get_pattern("accession_pattern")
        if pattern and not pattern.fullmatch(citekey.accession):
            return f"{citekey.accession} does not match regex {pattern.pattern}"

    def get_url(self, accession: str) -> str:
        if "uri_format" in self.resource:
            return self.resource["uri_format"].replace("$1", accession)
        return f"https://bioregistry.io/{self.standard_prefix}:{accession}"


def get_curie_handlers():
    """Get all possible CURIE handlers"""
    registries = get_bioregistry(compile_patterns=True)
    handlers = [Handler_CURIE(reg["prefix"]) for reg in registries]
    return handlers


def _download_bioregistry() -> None:
    """
    Download the Bioregistry consensus registry adding the following fields for each registry:
    - prefix: the standard lowercase registry prefix
    - all_prefixes: all distinct valid lowercase prefixes including synonyms
    """
    import requests

    url = "https://github.com/biopragmatics/bioregistry/raw/main/exports/registry/registry.json"
    response = requests.get(url)
    response.raise_for_status()
    results = response.json()
    assert isinstance(results, dict)
    registry = list()
    for prefix, resource in results.items():
        assert isinstance(resource, dict)
        if not resource.get("uri_format"):
            # discard unresolvable prefixes
            continue
        for field in set(resource) - _keep_bioregistry_fields:
            del resource[field]
        resource["prefix"] = prefix
        all_prefixes = {
            prefix,
            *(x.lower() for x in resource.pop("synonyms", [])),
        }
        # remove invalid prefixes as per https://github.com/manubot/manubot/pull/306#discussion_r744125504
        resource["all_prefixes"] = sorted(
            filter(valid_prefix_pattern.fullmatch, all_prefixes)
        )
        registry.append(resource)
    json_text = json.dumps(registry, indent=2, ensure_ascii=False)
    bioregistry_path.write_text(json_text + "\n", encoding="utf-8")


def get_bioregistry(compile_patterns=False) -> dict:
    with bioregistry_path.open(encoding="utf-8-sig") as read_file:
        registry = json.load(read_file)
    assert isinstance(registry, list)
    if compile_patterns:
        for resource in registry:
            if "pattern" in resource:
                resource["compiled_pattern"] = re.compile(resource["pattern"])
    return registry


@functools.lru_cache()
def get_prefix_to_resource() -> typing.Dict[str, typing.Dict]:
    prefix_to_resource = dict()
    for resource in get_bioregistry():
        for prefix in resource["all_prefixes"]:
            prefix_to_resource[prefix] = resource
    return prefix_to_resource


def standardize_curie(curie: str) -> str:
    """
    Return CURIE with Bioregistry preferred prefix capitalization.
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
    handler = Handler_CURIE(prefix.lower())
    return f"{handler.standard_prefix}:{accession}"


def curie_to_url(curie: str) -> str:
    """
    `curie` should be in `prefix:accession` format
    """
    curie = standardize_curie(curie)
    prefix, accession = curie.split(":", 1)
    handler = Handler_CURIE(prefix.lower())
    return handler.get_url(accession)


if __name__ == "__main__":
    _download_bioregistry()
    bioregistry = get_bioregistry()
