import dataclasses
import itertools
import logging
import typing as tp

from manubot.cite.citekey import CiteKey, citekey_to_csl_item


@dataclasses.dataclass
class Citations:
    """
    Class for operating on a set of citations provided by
    their citekey input_ids.
    """

    # Input citekey IDs as strings
    input_ids: list
    # Citation key aliases
    aliases: dict = dataclasses.field(default_factory=dict)
    # manual references dictionary of standard_id to CSL_Item.
    manual_refs: dict = dataclasses.field(default_factory=dict)
    # level to log failures related to CSL Item generation
    csl_item_failure_log_level: tp.Union[str, int] = "WARNING"
    # whether to prune csl items according to the JSON Schema
    prune_csl_items: bool = True

    def __post_init__(self):
        input_ids = list(dict.fromkeys(self.input_ids))  # deduplicate
        self.citekeys = [CiteKey(x, self.aliases) for x in input_ids]

    def filter_pandoc_xnos(self) -> list:
        """
        Filter self.citekeys to remove pandoc-xnos style citekeys.
        Return removed citekeys.
        """
        keep, remove = [], []
        for citekey in self.citekeys:
            remove_ = citekey.is_pandoc_xnos_prefix(log_case_warning=True)
            (keep, remove)[remove_].append(citekey)
        self.citekeys = keep
        return remove

    def filter_unhandled(self) -> list:
        """
        Filter self.citekeys to remove unhandled citekeys.
        Return removed citekeys.
        """
        keep, remove = [], []
        for citekey in self.citekeys:
            (remove, keep)[citekey.is_handled_prefix].append(citekey)
        self.citekeys = keep
        return remove

    def group_citekeys_by(
        self, attribute: str = "standard_id"
    ) -> tp.List[tp.Tuple[str, list]]:
        """
        Group `self.citekeys` by `attribute`.
        """
        get_key = lambda x: getattr(x, attribute)
        citekeys = sorted(self.citekeys, key=get_key)
        groups = itertools.groupby(citekeys, get_key)
        return [(key, list(group)) for key, group in groups]

    def unique_citekeys_by(self, attribute: str = "standard_id") -> list:
        return [citekeys[0] for key, citekeys in self.group_citekeys_by(attribute)]

    def check_collisions(self):
        """
        Check for short_id hash collisions
        """
        for short_id, citekeys in self.group_citekeys_by("short_id"):
            standard_ids = sorted(set(x.standard_id for x in citekeys))
            if len(standard_ids) == 1:
                continue
            logging.error(
                "Congratulations! Hash collision. Please report to https://git.io/JfuhH.\n"
                f"Multiple standard_ids hashed to {short_id}: {standard_ids}"
            )

    def check_multiple_input_ids(self):
        """
        Identify different input_ids referring the the same reference.
        """
        for standard_id, citekeys in self.group_citekeys_by("standard_id"):
            input_ids = [x.input_id for x in citekeys]
            logging.warning(
                f"Multiple citekey input_ids refer to the same standard_id {standard_id}:\n{input_ids}"
            )

    def load_manual_references(self, *args, **kwargs):
        """
        Load manual references
        """
        from manubot.process.bibliography import load_manual_references

        manual_refs = load_manual_references(*args, **kwargs)
        self.manual_refs.update(manual_refs)

    def get_csl_items(self) -> tp.List:
        """
        Produce a list of CSL_Items. I.e. a references list / bibliography
        for `self.citekeys`.
        """
        # dictionary of standard_id to CSL_Item ID (i.e. short_id),
        # excludes standard_ids for which CSL Items could not be generated.
        self.standard_to_csl_id = {}
        self.csl_items = []
        citekeys = self.unique_citekeys_by("standard_id")
        for citekey in citekeys:
            csl_item = citekey_to_csl_item(
                citekey=citekey,
                prune=self.prune_csl_items,
                log_level=self.csl_item_failure_log_level,
                manual_refs=self.manual_refs,
            )
            if csl_item:
                self.standard_to_csl_id[citekey.standard_id] = csl_item["id"]
                self.csl_items.append(csl_item)
        return self.csl_items
