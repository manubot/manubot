def test_imports():
    import manubot.cite
    import manubot.cite.arxiv
    import manubot.cite.doi
    import manubot.cite.pubmed
    import manubot.cite.url
    import manubot.process.manuscript

    manubot


def assert_instance_type():
    from manubot.cite.citekey import citeproc_retrievers

    assert isinstance(citeproc_retrievers, dict)
