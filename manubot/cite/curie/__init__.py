"""
Compact Uniform Resource Identifiers

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

"""
import functools
import json
import logging
import pathlib
import re
from typing import List, Tuple

import requests

_keep_namespace_fields = {
    "prefix",
    "mirId",  # MIRIAM Registry identifier
    "name",
    "pattern",  # regex pattern
    "description",
    "sampleId",  # example identifier
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
def get_prefixes() -> Tuple[str]:
    return tuple(namespace["prefix"] for namespace in get_namespaces())


if __name__ == "__main__":
    _download_namespaces()
    namespaces = get_namespaces()
