from ..unpaywall import Unpaywall_DOI, Unpaywall_arXiv


def test_unpaywall_doi():
    doi = "10.1371/journal.pcbi.1007250"
    unpaywall = Unpaywall_DOI(doi)
    assert isinstance(unpaywall.locations, list)
    assert unpaywall.best_pdf.has_creative_commons_license


def test_unpaywall_arxiv():
    arxiv_id = "1912.04616"
    unpaywall = Unpaywall_arXiv(arxiv_id, use_doi=False)
    assert isinstance(unpaywall.locations, list)
    best_pdf = unpaywall.best_pdf
    assert isinstance(best_pdf, dict)
    assert best_pdf["url"] == "https://arxiv.org/pdf/1912.04616.pdf"
    assert best_pdf["url_for_landing_page"] == "https://arxiv.org/abs/1912.04616"
    assert best_pdf["license"] == "cc-by-sa"
