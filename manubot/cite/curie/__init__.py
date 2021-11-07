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
import json
import pathlib
import re
import typing

from bioregistry import Manager, Resource

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


def _get_manager() -> Manager:
    with bioregistry_path.open() as file:
        resources = json.load(file)
    return Manager({entry["prefix"]: Resource(**entry) for entry in resources})


manager = _get_manager()

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
        self.resource = manager.get_resource(self.prefix_lower)
        if self.resource is None:
            raise ValueError(f"Unrecognized CURIE prefix {self.prefix_lower}")
        self.standard_prefix = self.resource.get_preferred_prefix()

    def get_csl_item(self, citekey: CiteKey):
        from ..url import get_url_csl_item

        url = self.get_url(accession=citekey.standard_accession)
        return get_url_csl_item(url)

    def inspect(self, citekey: CiteKey) -> typing.Optional[str]:
        judgement = self.resource.is_canonical_identifier(citekey.accession)
        if judgement is None or judgement is True:
            return None
        return f"{citekey.accession} does not match regex {self.resource.get_pattern()}"

    def get_url(self, accession: str) -> str:
        return self.resource.get_default_uri(accession)


def get_curie_handlers():
    """Get all possible CURIE handlers"""
    handlers = [Handler_CURIE(prefix) for prefix in manager.registry]
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
        resource["synonyms"] = sorted(
            filter(valid_prefix_pattern.fullmatch, all_prefixes)
        )
        registry.append(resource)
    json_text = json.dumps(registry, indent=2, ensure_ascii=False)
    bioregistry_path.write_text(json_text + "\n", encoding="utf-8")


def standardize_curie(curie: str) -> str:
    """
    Return CURIE with Bioregistry preferred prefix capitalization.
    `curie` should be in `prefix:accession` format.
    If `curie` is malformed or uses an unrecognized prefix, raise ValueError.
    """
    return manager.normalize_curie(curie)


def curie_to_url(curie: str) -> str:
    """
    `curie` should be in `prefix:accession` format
    """
    prefix, accession = manager.parse_curie(curie)
    if prefix is None or accession is None:
        raise ValueError(f"Could not parse {curie}")
    handler = Handler_CURIE(prefix.lower())
    return handler.get_url(accession)


if __name__ == "__main__":
    _download_bioregistry()
