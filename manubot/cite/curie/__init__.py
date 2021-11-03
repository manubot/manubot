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

from manubot.cite.handlers import Handler

_keep_bioregistry_fields = {
    "deprecated",
    "example",
    "url",
    "name",
    "pattern",
    "preferred_prefix",
    "synonyms",
}


bioregistry_path = pathlib.Path(__file__).parent.joinpath("bioregistry.json")


@dataclasses.dataclass
class Handler_CURIE(Handler):
    def __post_init__(self):
        prefix_to_registry = get_prefix_to_registry()
        self.registry = prefix_to_registry[self.prefix_lower]
        self.standard_prefix = self.registry["prefix"]
        self.prefixes = self.registry["all_prefixes"]
        if "pattern" in self.registry:
            self.accession_pattern = self.registry["pattern"]

    def get_csl_item(self, citekey):
        from ..url import get_url_csl_item

        url = curie_to_url(citekey.standard_id)
        return get_url_csl_item(url)

    def inspect(self, citekey):
        pattern = self._get_pattern("accession_pattern")
        # FIXME: match or fullmatch?
        if pattern and not pattern.fullmatch(citekey.accession):
            return f"{citekey.accession} does not match regex {pattern.pattern}"


def get_curie_handlers():
    """Get all possible CURIE handlers"""
    registries = get_bioregistry(compile_patterns=True)
    handlers = [Handler_CURIE(reg["prefix"]) for reg in registries]
    return handlers


def _download_bioregistry():
    """
    Download the Bioregistry consensus registry adding the following fields for each registry:
    - prefix: the standard lowercase registry prefix
    - all_prefixes: all distinct lowercase prefixes including synonyms
    """
    import requests

    url = "https://github.com/biopragmatics/bioregistry/raw/main/exports/registry/registry.json"
    response = requests.get(url)
    response.raise_for_status()
    results = response.json()
    assert isinstance(results, dict)
    for prefix, metadata in results.items():
        assert isinstance(metadata, dict)
        for field in set(metadata) - _keep_bioregistry_fields:
            del metadata[field]
        metadata["prefix"] = prefix
        metadata["all_prefixes"] = sorted(
            {
                prefix,
                *(x.lower() for x in metadata.get("synonyms", [])),
            }
        )
    registries = list(results.values())
    json_text = json.dumps(registries, indent=2, ensure_ascii=False)
    bioregistry_path.write_text(json_text + "\n", encoding="utf-8")


def get_bioregistry(compile_patterns=False) -> dict:
    with bioregistry_path.open(encoding="utf-8-sig") as read_file:
        registries = json.load(read_file)
    assert isinstance(registries, list)
    if compile_patterns:
        for registry in registries:
            if "pattern" in registry:
                registry["compiled_pattern"] = re.compile(registry["pattern"])
    return registries


@functools.lru_cache()
def get_prefix_to_registry() -> typing.Dict[str, typing.Dict]:
    prefix_to_registry = dict()
    for reg in get_bioregistry():
        for prefix in reg["all_prefixes"]:
            prefix_to_registry[prefix] = reg
    return prefix_to_registry


def standardize_curie(curie):
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
    prefix_lower = prefix.lower()
    try:
        registry = get_prefix_to_registry()[prefix_lower]
    except KeyError:
        raise ValueError(
            f"Prefix {prefix_lower} for {curie} is not a recognized prefix."
        )
    standard_prefix = registry.get("preferred_prefix") or registry["prefix"]
    return f"{standard_prefix}:{accession}"


def curie_to_url(curie):
    """
    `curie` should be in `prefix:accession` format
    """
    curie = standardize_curie(curie)
    prefix, accession = curie.split(":", 1)
    registry = get_prefix_to_registry()[prefix.lower()]
    if "url" in registry:
        return registry["url"].replace("$1", accession)
    return f"https://bioregistry.io/{curie}"


if __name__ == "__main__":
    _download_bioregistry()
    bioregistry = get_bioregistry()
