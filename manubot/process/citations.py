import dataclasses
import itertools
import logging

from manubot.cite.citekey import CiteKey


@dataclasses.dataclass
class Citations:
    """Input citekey IDs as strings"""

    input_ids: list
    """Citation key aliases"""
    aliases: dict = dataclasses.field(default_factory=dict)

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

    def filter_unhandled(self):
        """
        Filter self.citekeys to remove unhandled citekeys.
        Return removed citekeys.
        """
        keep, remove = [], []
        for citekey in self.citekeys:
            (remove, keep)[citekey.is_handled_prefix].append(citekey)
        self.citekeys = keep
        return remove

    def group_citekeys_by(self, attribute="standard_id") -> list:
        get_key = lambda x: getattr(x, attribute)
        citekeys = sorted(self.citekeys, key=get_key)
        groups = itertools.groupby(citekeys, get_key)
        return [(key, list(group)) for key, group in groups]

    def unique_citekeys_by(self, attribute="standard_id") -> list:
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
                "Congratulations! Hash collision.\n"
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

    def get_csl_items(self, log_level="WARNING"):
        """
        Produce a list of CSL_Items. I.e. a references list / bibliography
        for `self.citekeys`.
        """
        # https://stackoverflow.com/a/35704430/4651668
        log_level = logging._checkLevel(log_level)
        csl_items = list()
        citekeys = self.unique_citekeys_by("standard_id")
        for citekey in citekeys:
            try:
                csl_items.append(citekey.csl_item)
            except Exception as error:
                logging.log(
                    log_level,
                    f"Generating csl_item for {citekey.standard_id!r} failed "
                    f"due to a {error.__class__.__name__}:\n{error}",
                )
                logging.info(error, exc_info=True)
        return csl_items
