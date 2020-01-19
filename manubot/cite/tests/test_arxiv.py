from ..arxiv import get_arxiv_csl_item_export_api, get_arxiv_csl_item_oai


def test_get_arxiv_csl_item_abstract_whitespace():
    """
    Test wrapping newlines are properly removed from the abstract,
    while preserving paragraph breaks.
    From https://arxiv.org/help/prep#abstracts:

    > Carriage returns will be stripped unless they are followed by leading white spaces.
    So if you want a new paragraph or a table of contents,
    be sure to indent the lines after the carriage return.
    When the abstract is formatted for email announcement,
    it will be wrapped to 80 characters.
    """
    csl_item = get_arxiv_csl_item_export_api("1908.00936v2")
    assert csl_item["title"] == "Multi-Scale Learned Iterative Reconstruction"
    assert csl_item["URL"] == "https://arxiv.org/abs/1908.00936v2"
    assert csl_item["version"] == "v2"
    abstract = (
        "Model-based learned iterative reconstruction methods have recently been shown to outperform classical reconstruction algorithms. Applicability of these methods to large scale inverse problems is however limited by the available memory for training and extensive training times due to computationally expensive forward models. As a possible solution to these restrictions we propose a multi-scale learned iterative reconstruction scheme that computes iterates on discretisations of increasing resolution. This procedure does not only reduce memory requirements, it also considerably speeds up reconstruction and training times, but most importantly is scalable to large scale inverse problems with non-trivial forward operators, such as those that arise in many 3D tomographic applications. In particular, we propose a hybrid network that combines the multi-scale iterative approach with a particularly expressive network architecture which in combination exhibits excellent scalability in 3D."
        "\n  Applicability of the algorithm is demonstrated for 3D cone beam computed tomography from real measurement data of an organic phantom. Additionally, we examine scalability and reconstruction quality in comparison to established learned reconstruction methods in two dimensions for low dose computed tomography on human phantoms."
    )
    assert csl_item["abstract"] == abstract


def test_get_arxiv_csl_item_oai():
    """
    https://export.arxiv.org/oai2?verb=GetRecord&identifier=oai:arXiv.org:1912.04616&metadataPrefix=arXiv
    """
    csl_item = get_arxiv_csl_item_oai("1912.04616")
    assert (
        csl_item["title"]
        == "OpenBioLink: A resource and benchmarking framework for large-scale biomedical link prediction"
    )
    assert csl_item["URL"] == "https://arxiv.org/abs/1912.04616"
    assert csl_item.note_dict["license"]
    assert csl_item["author"][0]["family"] == "Breit"
