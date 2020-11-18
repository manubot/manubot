import pathlib
import shutil

import pytest

from manubot.pandoc.bibliography import load_bibliography

directory = pathlib.Path(__file__).parent


skipif_no_pandoc_citeproc = pytest.mark.skipif(
    not shutil.which("pandoc-citeproc"),
    reason="pandoc-citeproc required to load this format.",
)
skipif_no_pandoc = pytest.mark.skipif(
    not shutil.which("pandoc"), reason="pandoc required to load this format."
)
bibliographies = [
    pytest.param("bib", marks=skipif_no_pandoc),
    pytest.param("json", marks=skipif_no_pandoc_citeproc),
    pytest.param("nbib", marks=skipif_no_pandoc_citeproc),
    pytest.param("ris", marks=skipif_no_pandoc_citeproc),
]


@pytest.fixture(params=bibliographies)
def bibliography_path(request):
    return directory.joinpath(f"bibliographies/bibliography.{request.param}")


def test_load_bibliography_from_path(bibliography_path: pathlib.Path):
    """
    Some of the bibliographies for this test were generated at
    https://zbib.org/c7f95cdef6d6409c92ffde24d519435d
    """
    csl_json = load_bibliography(path=bibliography_path)
    assert len(csl_json) == 2
    assert (
        csl_json[0]["title"].rstrip(".")
        == "Sci-Hub provides access to nearly all scholarly literature"
    )


def test_load_bibliography_from_text(bibliography_path):
    """
    https://zbib.org/c7f95cdef6d6409c92ffde24d519435d
    """
    text = bibliography_path.read_text(encoding="utf-8-sig")
    input_format = bibliography_path.suffix[1:]
    csl_json = load_bibliography(text=text, input_format=input_format)
    assert len(csl_json) == 2
    assert (
        csl_json[0]["title"].rstrip(".")
        == "Sci-Hub provides access to nearly all scholarly literature"
    )
    if input_format in {"json", "bib"}:
        assert csl_json[0].get("id") == "doi:10.7554/elife.32822"
