
def test_imports():
    import manubot.cite
    import manubot.cite.util
    import manubot.cite.arxiv
    import manubot.cite.doi
    import manubot.cite.pubmed
    import manubot.cite.url
    import manubot.process.manuscript
    assert isinstance(manubot.cite.util.citeproc_retrievers, dict)
