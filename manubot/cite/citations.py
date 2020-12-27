import dataclasses
import json
import logging
import os
import pathlib
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
    # infer prefixes for citekeys (e.g. support DOIs without a "doi:" prefix)
    infer_citekey_prefixes: bool = True
    # manual references dictionary of standard_id to CSL_Item.
    manual_refs: dict = dataclasses.field(default_factory=dict)
    # level to log failures related to CSL Item generation
    csl_item_failure_log_level: tp.Union[str, int] = "WARNING"
    # whether to prune csl items according to the JSON Schema
    prune_csl_items: bool = True
    # whether to sort csl items by standard_id
    # `sort_csl_items=False` retains order of input_ids in get_csl_items.
    # (input_ids with the same standard_id will still be deduplicated).
    sort_csl_items: bool = True

    def __post_init__(self):
        input_ids = list(dict.fromkeys(self.input_ids))  # deduplicate
        self.citekeys = [
            CiteKey(x, aliases=self.aliases, infer_prefix=self.infer_citekey_prefixes)
            for x in input_ids
        ]

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
        self,
        attribute: str = "standard_id",
        sort: bool = True,
    ) -> tp.List[tp.Tuple[str, list]]:
        """
        Group `self.citekeys` by `attribute`.
        """

        def get_key(x):
            return getattr(x, attribute)

        key_to_indices = dict()
        for i, citekey in enumerate(self.citekeys):
            key = get_key(citekey)
            key_to_indices.setdefault(key, list()).append(i)
        items = list(key_to_indices.items())
        if sort:
            items.sort(key=lambda item: item[0])
        return [(key, [self.citekeys[i] for i in indices]) for key, indices in items]

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
        Identify different input_ids referring to the same reference.
        """
        for standard_id, citekeys in self.group_citekeys_by("standard_id"):
            input_ids = [x.input_id for x in citekeys]
            if len(input_ids) < 2:
                continue
            logging.warning(
                f"Multiple citekey input_ids refer to the same standard_id {standard_id}:\n{input_ids}"
            )

    def inspect(self, log_level=None):
        """
        If log_level is not None, log combined inspection report at this level.
        """
        citekeys = self.unique_citekeys_by("dealiased_id")
        reports = []
        for citekey in citekeys:
            report = citekey.inspect()
            if not report:
                continue
            reports.append(f"{citekey.dealiased_id} -- {report}")
        report = "\n".join(reports)
        if reports and log_level is not None:
            log_level = logging._checkLevel(log_level)
            msg = f"Inspection of dealiased citekeys revealed potential problems:\n{report}"
            logging.log(log_level, msg)
        return report

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
        # dictionary of input_id to CSL_Item ID (i.e. short_id),
        # excludes standard_ids for which CSL Items could not be generated.
        self.input_to_csl_id = {}
        self.csl_items = []
        for _standard_id, citekeys in self.group_citekeys_by(
            "standard_id", sort=self.sort_csl_items
        ):
            csl_item = citekey_to_csl_item(
                citekey=citekeys[0],
                prune=self.prune_csl_items,
                log_level=self.csl_item_failure_log_level,
                manual_refs=self.manual_refs,
            )
            if csl_item:
                for ck in citekeys:
                    self.input_to_csl_id[ck.input_id] = csl_item["id"]
                self.csl_items.append(csl_item)
        return self.csl_items

    @property
    def citekeys_tsv(self) -> str:
        import csv
        import io

        fields = ["input_id", "dealiased_id", "standard_id", "short_id"]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for citekey in self.citekeys:
            row = {x: getattr(citekey, x) for x in fields}
            writer.writerow(row)
        return output.getvalue()

    @property
    def csl_json(self) -> str:
        assert hasattr(self, "csl_items")
        json_str = json.dumps(self.csl_items, indent=2, ensure_ascii=False)
        json_str += "\n"
        return json_str

    @property
    def csl_yaml(self) -> str:
        from manubot.util import get_configured_yaml

        yaml = get_configured_yaml()
        assert hasattr(self, "csl_items")
        # dump rather than safe_dump is required for
        # pyyaml to use custom representers.
        return yaml.dump(
            data=self.csl_items,
            default_flow_style=False,
            width=float("inf"),
            allow_unicode=True,
            sort_keys=False,
        )

    def write_csl_items(self, path: tp.Union[os.PathLike, str, None]) -> None:
        """
        Write CSL Items to a JSON or YAML file at `path`.
        If path ends with a .yml or .yaml extension, write as CSL YAML.
        Otherwise write CSL JSON.
        If `path` evaluates as False, do nothing.
        """
        if not path:
            return
        path = pathlib.Path(path)
        text = self.csl_yaml if path.suffix in [".yaml", ".yml"] else self.csl_json
        path.write_text(text, encoding="utf-8")

    def write_citekeys_tsv(self, path: tp.Union[os.PathLike, str, None]):
        """
        Write `self.citekeys_tsv` to a file.
        If `path` evaluates as False, do nothing.
        """
        if not path:
            return
        path = pathlib.Path(path)
        path.write_text(self.citekeys_tsv, encoding="utf-8")
