import copy
import datetime

import pytest

from ..csl_item import (
    CSL_Item,
    assert_csl_item_type,
    date_to_date_parts,
    date_parts_to_string,
)


class Test_CSL_Item:
    def test_constuctor_empty(self):
        assert CSL_Item() == {}

    def test_constuctor_by_dict(self):
        d = {"title": "My book"}
        assert CSL_Item(d) == d

    def test_constuctor_by_keyword(self):
        assert CSL_Item(type="journal-article") == {"type": "journal-article"}

    def test_constuctor_by_dict_keyword_combination(self):
        assert CSL_Item({"title": "My journal article"}, type="journal-article") == {
            "title": "My journal article",
            "type": "journal-article",
        }

    def test_recursive_constructor(self):
        assert CSL_Item(CSL_Item()) == {}
        assert CSL_Item(CSL_Item(abc=1)) == {"abc": 1}

    def test_constructor_leaves_no_inplace_effects(self):
        dict1 = {"a": 1}
        ci = CSL_Item(dict1, b=2)
        assert ci == {"a": 1, "b": 2}
        assert dict1 == {"a": 1}

    def test_correct_invalid_type(self):
        assert CSL_Item(type="journal-article").correct_invalid_type() == {
            "type": "article-journal"
        }

    def test_set_default_type(self):
        assert CSL_Item().set_default_type() == {"type": "entry"}

    def test_no_change_of_type(self):
        assert CSL_Item(type="book").correct_invalid_type() == {"type": "book"}
        assert CSL_Item(type="book").set_default_type() == {"type": "book"}

    def test_clean(self):
        csl_item = CSL_Item(type="chapter", id="abc")
        csl_item.clean(prune=True)
        assert csl_item == {"type": "chapter", "id": "abc"}

    def test_clean_set_id(self):
        csl_item = CSL_Item(type="chapter")
        csl_item.set_id("abc")
        csl_item.clean(prune=True)
        assert csl_item == {"type": "chapter", "id": "abc"}


def test_assert_csl_item_type_passes():
    assert_csl_item_type(CSL_Item())


def test_assert_csl_item_type_raises_error_on_dict():
    with pytest.raises(TypeError):
        assert_csl_item_type({})


@pytest.mark.parametrize(
    ["csl_item", "standard_citation"],
    [
        (
            {"id": "my-id", "standard_citation": "doi:10.7554/elife.32822"},
            "doi:10.7554/elife.32822",
        ),
        ({"id": "doi:10.7554/elife.32822"}, "doi:10.7554/elife.32822"),
        ({"id": "doi:10.7554/ELIFE.32822"}, "doi:10.7554/elife.32822"),
        ({"id": "my-id"}, "raw:my-id"),
    ],
    ids=[
        "from_standard_citation",
        "from_doi_id",
        "from_doi_id_standardize",
        "from_raw_id",
    ],
)
def test_csl_item_standardize_id(csl_item, standard_citation):
    csl_item = CSL_Item(csl_item)
    output = csl_item.standardize_id()
    assert output is csl_item
    assert output["id"] == standard_citation


def test_csl_item_standardize_id_repeated():
    csl_item = CSL_Item(id="pmid:1", type="article-journal")
    csl_item_1 = copy.deepcopy(csl_item.standardize_id())
    assert "standard_citation" not in "csl_item"
    csl_item_2 = copy.deepcopy(csl_item.standardize_id())
    assert csl_item_1 == csl_item_2


def test_csl_item_standardize_id_note():
    """
    Test extracting standard_id from a note and setting additional
    note fields.
    """
    csl_item = CSL_Item(
        {
            "id": "original-id",
            "type": "article-journal",
            "note": "standard_id: doi:10.1371/journal.PPAT.1006256",
        }
    )
    csl_item.standardize_id()
    assert csl_item["id"] == "doi:10.1371/journal.ppat.1006256"
    note_dict = csl_item.note_dict
    assert note_dict["original_id"] == "original-id"
    assert note_dict["original_standard_id"] == "doi:10.1371/journal.PPAT.1006256"


@pytest.mark.parametrize(
    ["input_note", "text", "dictionary", "expected_note"],
    [
        ("", "", {}, ""),
        (None, "", {}, ""),
        ("preexisting note", "", {}, "preexisting note"),
        (
            "preexisting note",
            "",
            {"key": "the value"},
            "preexisting note\nkey: the value",
        ),
        ("", "", {"KEYOKAY": "the value"}, "KEYOKAY: the value"),
        ("preexisting note", "", {"KEY-NOT-OKAY": "the value"}, "preexisting note"),
        (
            "",
            "",
            {"standard_citation": "doi:10.7554/elife.32822"},
            "standard_citation: doi:10.7554/elife.32822",
        ),
        (
            "This CSL Item was produced using Manubot.",
            "",
            {"standard_citation": "doi:10.7554/elife.32822"},
            "This CSL Item was produced using Manubot.\nstandard_citation: doi:10.7554/elife.32822",
        ),
    ],
)
def test_csl_item_note_append(input_note, text, dictionary, expected_note):
    csl_item = CSL_Item({"id": "test_csl_item", "type": "entry", "note": input_note})
    csl_item.note_append_text(text)
    csl_item.note_append_dict(dictionary)
    assert csl_item.note == expected_note


@pytest.mark.parametrize(
    ["note", "dictionary"],
    [
        (
            "This is a note\nkey_one: value\nKEYTWO: value 2 ",
            {"key_one": "value", "KEYTWO": "value 2"},
        ),
        ("BAD_KEY: good value\ngood-key: good value", {"good-key": "good value"}),
        (
            "This is a note {:key_one: value} {:KEYTWO: value 2 } ",
            {"key_one": "value", "KEYTWO": "value 2"},
        ),
        ("{:BAD_KEY: good value}\n{:good-key: good value}", {"good-key": "good value"}),
        (
            "Mixed line-entry and braced-entry syntax\nGOODKEY: good value\n{:good-key: good value}",
            {"GOODKEY": "good value", "good-key": "good value"},
        ),
        ("Note without any key-value pairs", {}),
        (
            "Other text\nstandard_citation: doi:10/ckcj\nMore other text",
            {"standard_citation": "doi:10/ckcj"},
        ),
    ],
)
def test_csl_item_note_dict(note, dictionary):
    csl_item = CSL_Item(note=note)
    assert csl_item.note_dict == dictionary


@pytest.mark.parametrize(
    ["date", "expected"],
    [
        (None, None),
        ("", None),
        ("2019", [2019]),
        ("2019-01", [2019, 1]),
        ("2019-12", [2019, 12]),
        ("2019-12-31", [2019, 12, 31]),
        ("2019-12-99", [2019, 12]),
        ("2019-12-01", [2019, 12, 1]),
        (" 2019-12-01 ", [2019, 12, 1]),
        ("2019-12-30T23:32:16Z", [2019, 12, 30]),
        (datetime.date(2019, 12, 31), [2019, 12, 31]),
        (datetime.datetime(2019, 12, 31, 23, 32, 16), [2019, 12, 31]),
    ],
)
def test_date_to_date_parts(date, expected):
    assert date_to_date_parts(date) == expected


@pytest.mark.parametrize(
    ["expected", "date_parts", "fill"],
    [
        (None, None, False),
        (None, [], True),
        (None, [], False),
        (None, None, True),
        ("2019", [2019], False),
        ("2019-01-01", [2019], True),
        ("2019-01", [2019, 1], False),
        ("2019-12", [2019, 12], False),
        ("2019-12-01", [2019, 12], True),
        ("2019-12-31", [2019, 12, 31], False),
        ("2019-12-31", [2019, 12, 31], True),
        ("2019-12", [2019, 12, "bad day"], False),
        ("2019-12-01", [2019, 12, 1], False),
        ("2019-12-01", ["2019", "12", "01"], False),
        ("2019-02-01", ["2019", "2", "1"], False),
        ("2019-12-31", [2019, 12, 31, 23, 32, 16], False),
        ("2019-12-31", [2019, 12, 31, 23, 32, 16], True),
        ("0080-07-14", [80, 7, 14], False),
        ("0080-07-14", ["80", "07", 14], False),
    ],
)
def test_date_parts_to_string(expected, date_parts, fill):
    assert expected == date_parts_to_string(date_parts, fill=fill)
