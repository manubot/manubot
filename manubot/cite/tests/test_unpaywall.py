from ..unpaywall import Unpaywall_DOI


def test_Unpaywall_DOI():
    doi = "10.1371/journal.pcbi.1007250"
    unpaywall_doi = Unpaywall_DOI(doi)
    unpaywall_doi.best_openly_licensed_pdf
    assert isintance(unpaywall_doi.locations, list)
    assert unpaywall_doi.best_pdf.has_creative_commons_license
