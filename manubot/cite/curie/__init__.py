"""
Compact Uniform Resource Identifiers

```shell
# regenerate manubot/cite/curie/namespaces.json
python manubot/cite/curie/__init__.py
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
import functools
import json
import logging
import pathlib
import re
from typing import List, Set

import requests

_keep_namespace_fields = {
    "prefix",
    "mirId",  # MIRIAM Registry identifier
    "name",
    "pattern",  # regex pattern
    "description",
    "sampleId",  # example identifier
    "namespaceEmbeddedInLui",  # whether prefix is included in the local unique identifier
}


namespace_path = pathlib.Path(__file__).parent.joinpath("namespaces.json")


def _download_namespaces():
    """
    Download all namespaces from the Identifiers.org Central Registry.

    Example of a single namespace JSON data at
    <https://registry.api.identifiers.org/restApi/namespaces/230>
    """
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
        for field in set(namespace) - _keep_namespace_fields:
            del namespace[field]
    json_text = json.dumps(namespaces, indent=2, ensure_ascii=False)
    namespace_path.write_text(json_text + "\n", encoding="utf-8")


def get_namespaces(compile_patterns=False) -> List[dict]:
    with namespace_path.open(encoding="utf-8-sig") as read_file:
        namespaces = json.load(read_file)
    if compile_patterns:
        for namespace in namespaces:
            namespace["pattern"] = re.compile(namespace["pattern"])
    return namespaces


@functools.lru_cache()
def get_prefixes() -> Set[str]:
    return {namespace["prefix"] for namespace in get_namespaces()}


@functools.lru_cache()
def get_prefix_to_namespace() -> Set[str]:
    return {n["prefix"]: n for n in get_namespaces()}


def curie_to_url(curie):
    """
    `curie` should be in `prefix:accession` format
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
    if not namespace["namespaceEmbeddedInLui"]:
        curie = f"{prefix_lower}:{accession}"
    resolver_url = "https://identifiers.org"
    return f"{resolver_url}/{curie}"


if __name__ == "__main__":
    _download_namespaces()
    namespaces = get_namespaces()
