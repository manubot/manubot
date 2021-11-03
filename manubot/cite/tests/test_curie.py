import pytest

from ..citekey import CiteKey
from ..curie import Handler_CURIE, curie_to_url, get_bioregistry, get_prefix_to_registry


@pytest.mark.xfail(reason="https://github.com/biopragmatics/bioregistry/issues/242")
def test_registry_patterns():
    """
    https://github.com/biopragmatics/bioregistry/issues/242
    """
    bioregistry = get_bioregistry(compile_patterns=True)
    assert isinstance(bioregistry, list)
    reports = list()
    for registry in bioregistry:
        assert registry["prefix"]  # ensure prefix field exists
        if "example" in registry and "pattern" in registry:
            prefix = registry["prefix"]
            example = registry["example"]
            handler = Handler_CURIE(prefix)
            example_curie = CiteKey(f"{prefix}:{example}")
            report = handler.inspect(example_curie)
            if report:
                reports.append(report)
    print("\n".join(reports))
    assert not reports


def test_get_prefix_to_registry():
    prefix_to_registry = get_prefix_to_registry()
    assert isinstance(prefix_to_registry, dict)
    assert "doid" in prefix_to_registry
    registry = prefix_to_registry["doid"]
    registry["preferred_prefix"] = "DOID"


@pytest.mark.parametrize(
    "curie, expected",
    [
        ("doi:10.1038/nbt1156", "https://doi.org/10.1038/nbt1156"),
        ("DOI:10.1038/nbt1156", "https://doi.org/10.1038/nbt1156"),
        ("arXiv:0807.4956v1", "https://arxiv.org/abs/0807.4956v1"),
        (
            "taxonomy:9606",
            "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=9606",
        ),
        ("CHEBI:36927", "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:36927"),
        ("ChEBI:36927", "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:36927"),
        (
            "DOID:11337",
            "https://www.ebi.ac.uk/ols/ontologies/doid/terms?obo_id=DOID:11337",
        ),
        (
            "doid:11337",
            "https://www.ebi.ac.uk/ols/ontologies/doid/terms?obo_id=DOID:11337",
        ),
        (
            "clinicaltrials:NCT00222573",
            "https://clinicaltrials.gov/ct2/show/NCT00222573",
        ),
        # formerly afflicted by https://github.com/identifiers-org/identifiers-org.github.io/issues/99#issuecomment-614690283
        pytest.param(
            "gramene.growthstage:0007133",
            "http://www.gramene.org/db/ontology/search?id=GRO:0007133",
            id="gramene.growthstage",
        ),
    ],
)
def test_curie_to_url(curie, expected):
    url = curie_to_url(curie)
    assert url == expected


def test_curie_to_url_bad_curie():
    with pytest.raises(ValueError):
        curie_to_url("this.is.not:a_curie")
