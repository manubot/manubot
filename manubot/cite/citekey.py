"""
Utilities for representing and processing citation keys.
"""
import dataclasses
import functools
import logging
import re
import typing as tp

try:
    from functools import cached_property
except ImportError:
    from backports.cached_property import cached_property


@dataclasses.dataclass
class CiteKey:
    input_id: str
    """Input identifier for the citekey"""
    aliases: dict = dataclasses.field(default_factory=dict)
    """Mapping from input identifier to aliases"""
    infer_prefix: bool = True
    """Whether to infer the citekey's prefix when a prefix is missing or unhandled"""

    def __post_init__(self):
        self.check_input_id(self.input_id)

    @staticmethod
    def check_input_id(input_id) -> None:
        if not isinstance(input_id, str):
            raise TypeError(
                "input_id should be type 'str' not "
                f"{type(input_id).__name__!r}: {input_id!r}"
            )
        if input_id.startswith("@"):
            raise ValueError(f"invalid citekey input_id: {input_id!r}\nstarts with '@'")

    @classmethod
    @functools.lru_cache(maxsize=None)
    def from_input_id(cls, *args, **kwargs) -> "CiteKey":
        """Cached constructor"""
        return cls(*args, **kwargs)

    @cached_property
    def dealiased_id(self) -> str:
        """
        If `self.input_id` is in `self.aliases`, the value specified by
        `self.aliases`. Otherwise, `self.input_id`.
        """
        return self.aliases.get(self.input_id, self.input_id)

    def _set_prefix_accession(self) -> None:
        self._prefix = None
        self._accession = None
        split_id = self.dealiased_id.split(":", 1)
        if len(split_id) == 2:
            self._prefix, self._accession = split_id
        if self.infer_prefix and not self.is_known_prefix:
            self._infer_prefix()

    def _infer_prefix(self) -> None:
        """
        Treat `self.dealiased_id` as missing a prefix.
        If the prefix can be inferred, set `self._prefix` and `self._accession`.

        Only call this function from _set_prefix_accession,
        since it is not safe after instance attributes or properties have been cached.
        """
        from .handlers import infer_prefix

        prefix = infer_prefix(self.dealiased_id)
        if not prefix:
            return
        self._prefix = prefix
        self._accession = self.dealiased_id

    @property
    def prefix(self) -> tp.Optional[str]:
        """
        If `self.input_id` contains a colon, the substring up to the first colon.
        Otherwise, None.
        """
        if not hasattr(self, "_prefix"):
            self._set_prefix_accession()
        return self._prefix

    @property
    def prefix_lower(self) -> tp.Optional[str]:
        """
        A lowercase version of `self.prefix` or None.
        """
        if self.prefix is None:
            return None
        return self.prefix.lower()

    @property
    def accession(self) -> tp.Optional[str]:
        """
        If `self.prefix`, the remainder of `self.input_id` following the first colon.
        """
        if not hasattr(self, "_accession"):
            self._set_prefix_accession()
        return self._accession

    @property
    def standard_prefix(self) -> tp.Optional[str]:
        """
        If the citekey is handled, the standard prefix specified by the handler.
        Otherwise, None.
        """
        if not hasattr(self, "_standard_prefix"):
            self._standardize()
        return self._standard_prefix

    @property
    def standard_accession(self) -> tp.Optional[str]:
        """
        If the citekey is handled, the standard accession specified by the handler.
        Otherwise, None.
        """
        if not hasattr(self, "_standard_accession"):
            self._standardize()
        return self._standard_accession

    @cached_property
    def handler(self):
        from .handlers import Handler, get_handler

        if self.is_handled_prefix:
            return get_handler(self.prefix_lower)
        return Handler(self.prefix_lower)

    @property
    def is_handled_prefix(self) -> bool:
        from .handlers import prefix_to_handler

        return self.prefix_lower in prefix_to_handler

    @property
    def is_known_prefix(self) -> bool:
        return self.is_handled_prefix or self.is_pandoc_xnos_prefix()

    def inspect(self) -> tp.Optional[str]:
        """
        Inspect citekey for potential problems.
        If no problems are found, return None.
        Otherwise, returns a string describing the problem.
        """
        return self.handler.inspect(self)

    def _standardize(self) -> None:
        """
        Set `self._standard_prefix`, `self._standard_accession`, and `self._standard_id`.
        For citekeys without a prefix or with an unhandled prefix, _standard_prefix
        and _standard_accession are set to None.
        """
        if not self.is_handled_prefix:
            self._standard_prefix = None
            self._standard_accession = None
            self._standard_id = self.dealiased_id
            return
        fxn = self.handler.standardize_prefix_accession
        self._standard_prefix, self._standard_accession = fxn(self.accession)
        self._standard_id = f"{self._standard_prefix}:{self._standard_accession}"

    @property
    def standard_id(self) -> str:
        """
        If the citekey is handled, the standard_id specified by the handler.
        Otherwise, `self.dealiased_id`.
        """
        if not hasattr(self, "_standard_id"):
            self._standardize()
        return self._standard_id

    @cached_property
    def short_id(self) -> str:
        """
        A hashed version of standard_id whose characters are
        within the ranges 0-9, a-z and A-Z.
        """
        return shorten_citekey(self.standard_id)

    @cached_property
    def all_ids(self) -> tp.List[str]:
        ids = [self.input_id, self.dealiased_id, self.standard_id, self.short_id]
        ids = [x for x in ids if x]  # remove None
        ids = list(dict.fromkeys(ids))  # deduplicate
        return ids

    def __hash__(self):
        return hash((self.input_id, self.dealiased_id))

    def __repr__(self):
        return " --> ".join(
            f"{getattr(self, key)} ({key})"
            for key in (
                "input_id",
                "dealiased_id",
                "prefix_lower",
                "accession",
                "standard_id",
                "short_id",
            )
        )

    @cached_property
    def csl_item(self):
        from .csl_item import CSL_Item

        csl_item = self.handler.get_csl_item(self)
        if not isinstance(csl_item, CSL_Item):
            csl_item = CSL_Item(csl_item)
        csl_item.set_id(self.standard_id)
        return csl_item

    def is_pandoc_xnos_prefix(self, log_case_warning: bool = False) -> bool:
        from .handlers import _pandoc_xnos_prefixes

        if self.prefix in _pandoc_xnos_prefixes:
            return True
        if log_case_warning and self.prefix_lower in _pandoc_xnos_prefixes:
            logging.warning(
                "pandoc-xnos prefixes should be all lowercase.\n"
                f'Should {self.input_id!r} use {self.prefix_lower!r} rather than "{self.prefix!r}"?'
            )
        return False


def shorten_citekey(standard_citekey: str) -> str:
    """
    Return a shortened citekey derived from the input citekey.
    The input citekey should be standardized prior to this function,
    since differences in the input citekey will result in different shortened citekeys.
    Short citekeys are generated by converting the input citekey to a 6 byte hash,
    and then converting this digest to a base62 ASCII str. Shortened
    citekeys consist of characters in the following ranges: 0-9, a-z and A-Z.
    """
    import hashlib

    import base62

    assert not standard_citekey.startswith("@")
    as_bytes = standard_citekey.encode()
    blake_hash = hashlib.blake2b(as_bytes, digest_size=6)
    digest = blake_hash.digest()
    short_citekey = base62.encodebytes(digest)
    return short_citekey


def citekey_to_csl_item(
    citekey, prune=True, manual_refs={}, log_level: tp.Union[str, int] = "WARNING"
):
    """
    Generate a CSL_Item for the input citekey.
    """
    from manubot import __version__ as manubot_version

    # https://stackoverflow.com/a/35704430/4651668
    log_level = logging._checkLevel(log_level)
    if not isinstance(citekey, CiteKey):
        citekey = CiteKey(citekey)

    if citekey.standard_id in manual_refs:
        return manual_refs[citekey.standard_id]

    try:
        csl_item = citekey.csl_item
    except Exception as error:
        logging.log(
            log_level,
            f"Generating csl_item for {citekey.standard_id!r} failed "
            f"due to a {error.__class__.__name__}:\n{error}",
        )
        logging.info(error, exc_info=True)
        return None
    # update csl_item with manubot generated metadata
    note_text = f"This CSL Item was generated by Manubot v{manubot_version} from its persistent identifier (standard_id)."
    note_dict = {"standard_id": citekey.standard_id}
    csl_item.note_append_text(note_text)
    csl_item.note_append_dict(note_dict)
    csl_item.set_id(citekey.short_id)
    csl_item.clean(prune=prune)
    return csl_item


def url_to_citekey(url: str) -> str:
    """
    Convert a HTTP(s) URL into a citekey.
    For supported sources, convert from url citekey to an alternative source like doi.
    If citekeys fail inspection, revert alternative sources to URLs.
    """
    from urllib.parse import unquote, urlparse

    citekey = None
    parsed_url = urlparse(url)
    domain_levels = parsed_url.hostname.split(".")
    if domain_levels[-2:] == ["doi", "org"]:
        # DOI URLs
        doi = unquote(parsed_url.path.lstrip("/"))
        citekey = f"doi:{doi}"
    if domain_levels[-2] == "sci-hub":
        # Sci-Hub domains
        doi = parsed_url.path.lstrip("/")
        citekey = f"doi:{doi}"
    if domain_levels[-2:] == ["biorxiv", "org"]:
        # bioRxiv URL to DOI. See https://git.io/Je9Hq
        match = re.search(
            r"/(?P<biorxiv_id>([0-9]{4}\.[0-9]{2}\.[0-9]{2}\.)?[0-9]{6,})",
            parsed_url.path,
        )
        if match:
            citekey = f"doi:10.1101/{match.group('biorxiv_id')}"
    is_ncbi_url = parsed_url.hostname.endswith("ncbi.nlm.nih.gov")
    if is_ncbi_url and parsed_url.path.startswith("/pubmed/"):
        # PubMed URLs
        try:
            pmid = parsed_url.path.split("/")[2]
            citekey = f"pmid:{pmid}"
        except IndexError:
            pass
    if is_ncbi_url and parsed_url.path.startswith("/pmc/"):
        # PubMed Central URLs
        try:
            pmcid = parsed_url.path.split("/")[3]
            citekey = f"pmcid:{pmcid}"
        except IndexError:
            pass
    if domain_levels[-2:] == ["wikidata", "org"] and parsed_url.path.startswith(
        "/wiki/"
    ):
        # Wikidata URLs
        try:
            wikidata_id = parsed_url.path.split("/")[2]
            citekey = f"wikidata:{wikidata_id}"
        except IndexError:
            pass
    if domain_levels[-2:] == ["arxiv", "org"]:
        # arXiv identifiers. See https://arxiv.org/help/arxiv_identifier
        try:
            arxiv_id = parsed_url.path.split("/", maxsplit=2)[2]
            if arxiv_id.endswith(".pdf"):
                arxiv_id = arxiv_id[:-4]
            citekey = f"arxiv:{arxiv_id}"
        except IndexError:
            pass
    if citekey is None or CiteKey(citekey).inspect() is not None:
        citekey = f"url:{url}"
    return citekey
