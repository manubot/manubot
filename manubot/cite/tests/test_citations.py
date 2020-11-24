import pathlib
import pytest

from manubot.cite.citations import Citations


def test_citations_filter_pandoc_xnos():
    input_ids = [
        "fig:pandoc-fignos-key",  # should filter
        "eq:pandoc-eqnos-key",  # should filter
        "tbl:pandoc-tablenos-key",  # should filter
        "not-pandoc-xnos-key",  # should keep
    ]
    citations = Citations(input_ids)
    citations.filter_pandoc_xnos()
    assert len(citations.citekeys) == 1
    assert citations.citekeys[0].input_id == "not-pandoc-xnos-key"


def test_citations_filter_unhandled():
    input_ids = [
        "citekey-with-no-prefix",
        "bad-prefix:citekey",
        ":empty-prefix",
        "doi:handled-prefix",
    ]
    citations = Citations(input_ids)
    citations.filter_unhandled()
    assert len(citations.citekeys) == 1
    assert citations.citekeys[0].input_id == "doi:handled-prefix"


def test_citations_check_collisions(caplog):
    input_ids = [
        "citekey-1",
        "citekey-1",
        "citekey-2",
        "Citekey-2",
    ]
    citations = Citations(input_ids)
    citations.check_collisions()
    assert not caplog.records


def test_citations_check_multiple_input_ids(caplog):
    input_ids = [
        "doi:10/b6vnmd",
        "DOI:10/B6VNMD",
        "doi:10.1016/s0933-3657(96)00367-3",
        "ugly-doi-alias",
        "other-citekey",
    ]
    citekey_aliases = {"ugly-doi-alias": "DOI:10.1016/s0933-3657(96)00367-3"}
    citations = Citations(input_ids, citekey_aliases)
    citations.check_multiple_input_ids()
    expected = "Multiple citekey input_ids refer to the same standard_id doi:10.1016/s0933-3657(96)00367-3:"
    "['doi:10/b6vnmd', 'DOI:10/B6VNMD', 'doi:10.1016/s0933-3657(96)00367-3', 'ugly-doi-alias']"
    assert expected in caplog.text


def test_citations_citekeys_tsv():
    input_ids = [
        "citekey-1",
        "arXiv:1806.05726v1",
        "DOI:10.7717/peerj.338",
        "pmid:29618526",
    ]
    citations = Citations(input_ids)
    citekeys_tsv = citations.citekeys_tsv
    assert isinstance(citekeys_tsv, str)
    assert "arxiv:1806.05726v1" in citekeys_tsv.splitlines()[2].split("\t")


def test_citations_inspect():
    input_ids = [
        "citekey-1",  # passes inspection
        "arXiv:1806.05726v1",  # passes inspection
        "arXiv:bad-id",
        "DOI:bad-id",
        "pmid:bad-id",
        "DOID:not-disease-ontology-id",
    ]
    citations = Citations(input_ids)
    report = citations.inspect(log_level="INFO")
    print(report)
    assert len(report.splitlines()) == 4
    assert "pmid:bad-id -- PubMed Identifiers should be 1-8 digits" in report


@pytest.mark.parametrize("csl_format", ["json", "yaml"])
def test_citations_csl_serialization(csl_format):
    ccr_dir = pathlib.Path(__file__).parent.joinpath("cite-command-rendered")
    citations = Citations(
        ["arxiv:1806.05726v1", "doi:10.7717/peerj.338", "pubmed:29618526"]
    )
    citations.load_manual_references(
        paths=[ccr_dir.joinpath("input-bibliography.json")]
    )
    citations.get_csl_items()
    path_out = ccr_dir.joinpath(f"output-bibliography.{csl_format}")
    # uncomment the following line to regenerate test output
    # citations.write_csl_items(path_out)
    csl_out = getattr(citations, f"csl_{csl_format}")
    assert csl_out == path_out.read_text()
