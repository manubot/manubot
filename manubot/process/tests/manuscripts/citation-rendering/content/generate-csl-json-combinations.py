"""
Create CSL JSON metadata with combinations of fields for testing
"""

import pathlib
import json

content_dir = pathlib.Path(__file__).parent

csl_item_complete = {
    "id": "test-csl-item-complete",
    "type": "article-journal",
    "title": "This is the title",
    "author": [
        {"given": "Given-1", "family": "Family-1"},
        {"given": "Given-2", "family": "Family-2"},
        {"given": "Given-3 I.", "family": "Family-3"},
    ],
    "editor": [
        {"given": "Given-1", "family": "Editor Family-1"},
        {"given": "Given-2", "family": "Editor Family-2"},
    ],
    "container-title": "Container Title",
    "container-title-short": "Cont Titl",
    "volume": "Volume",
    "issue": "Issue",
    "page": "page-number",
    "publisher": "Publisher",
    "issued": {"date-parts": [[2019, 1, 1]]},
    "language": "en",
    "DOI": "10.0000/fake-doi",
    "PMCID": "PMC0000000",
    "PMID": "00000000",
    "URL": "https://manubot.org",
}


def powerset(iterable):
    """
    powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    from itertools import chain, combinations

    s = list(iterable)  # allows duplicate elements
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


csl_key_subset = [
    "title",
    "author",
    "editor",
    "container-title",
    #     'container-title-short',
    "publisher",
    "issued",
    "URL",
    "DOI",
]
combinations = list(powerset(csl_key_subset))
print(f"generated {len(combinations)} combinations of CSL JSON keys")

csl_data = list()
citation_list_md = ""
for i, keys in enumerate(combinations):
    citation_id = "raw:" + "_".join(keys) if keys else "raw:blank"
    csl_item_subset = {
        "id": citation_id,
        "type": "entry",
    }
    for key in keys:
        csl_item_subset[key] = csl_item_complete[key]
    citation_list_md += f"{i + 1}. Citation whose CSL JSON contains: {', '.join(keys)} [@{citation_id}].\n"
    csl_data.append(csl_item_subset)

csl_item_ids = [csl_item["id"] for csl_item in csl_data]
newline = "\n"
text = f"""\
---
title: 'Testing manuscript for CSL JSON field combinations'
...

This file was created by `generate-csl-json-combinations.py`.

The complete CSL Item this is based on is:

```json
{json.dumps(csl_item_complete, indent=2, ensure_ascii=False)}
```

All possible combinations of the following fields were created:

{newline.join('- ' + x for x in csl_key_subset)}

The list of citations follows:

{citation_list_md}
"""

# Write markdown document
content_dir.joinpath("01.main-text.md").write_text(text)

# Write CSL JSON
with content_dir.joinpath("manual-references.json").open("w") as write_file:
    json.dump(csl_data, write_file, indent=2, ensure_ascii=False)

print("writing output files complete")
