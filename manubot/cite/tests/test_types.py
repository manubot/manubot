from manubot.cite.types import split_prefixed_identifier

def test_split_prefixed_identifier():    
    assert split_prefixed_identifier("  @dOi:blah\t\t\n ") == ('doi', 'blah')