from manubot.pandoc.tests.test_bibliography import (
    directory,
    skipif_no_pandoc,
    skipif_no_pandoc_citeproc,
)
from manubot.process.bibliography import load_manual_references


class Test_load_manual_references:
    """
    Tests loading multiple bibliography paths
    """

    def setup_method(self):
        bibliography_paths = sorted(
            directory / x for x in directory.glob("bibliographies/bibliography.*")
        )
        self.citation_to_csl_item = load_manual_references(bibliography_paths)
        print(list(self.citation_to_csl_item))

    def test_csl_item_1(self):
        assert "doi:10.7554/elife.32822" in self.citation_to_csl_item
        csl_item_1 = self.citation_to_csl_item["doi:10.7554/elife.32822"]
        assert csl_item_1["title"].startswith("Sci-Hub")
        assert "CSL JSON Item was loaded by Manubot" in csl_item_1["note"]
        assert "manual_reference_filename: bibliography.json" in csl_item_1["note"]
        assert "standard_id: doi:10.7554/elife.32822" in csl_item_1["note"]

    @skipif_no_pandoc
    def test_csl_item_2(self):
        # raw id corresponding to bibliography.bib
        assert "noauthor_techblog:_nodate" in self.citation_to_csl_item
        csl_item_2 = self.citation_to_csl_item["noauthor_techblog:_nodate"]
        assert csl_item_2["title"].startswith("TechBlog")
        assert "manual_reference_filename: bibliography.bib" in csl_item_2["note"]
        assert "standard_id: noauthor_techblog:_nodate" in csl_item_2["note"]

    @skipif_no_pandoc_citeproc
    def test_csl_item_3(self):
        assert "Beaulieu-Jones2017" in self.citation_to_csl_item
        csl_item_3 = self.citation_to_csl_item["Beaulieu-Jones2017"]
        assert csl_item_3["author"][0]["family"] == "Beaulieu-Jones"
        assert "manual_reference_filename: bibliography.nbib" in csl_item_3["note"]
        assert "standard_id: Beaulieu-Jones2017" in csl_item_3["note"]
