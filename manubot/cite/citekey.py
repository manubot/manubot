"""
Utilities for representing and processing citation keys.
"""
import functools
import logging
import re
import dataclasses

try:
    from functools import cached_property
except ImportError:
    from backports.cached_property import cached_property


@dataclasses.dataclass
class CiteKey:
    input_id: str
    aliases: dict = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        self.check_input_id(self.input_id)

    @staticmethod
    def check_input_id(input_id):
        if not isinstance(input_id, str):
            raise TypeError(
                "input_id should be type 'str' not "
                f"{type(input_id).__name__!r}: {input_id!r}"
            )
        if input_id.startswith("@"):
            f"invalid citekey input_id: {input_id!r}\nstarts with '@'"

    @classmethod
    @functools.lru_cache(maxsize=None)
    def from_input_id(cls, *args, **kwargs):
        """Cached constructor"""
        return cls(*args, **kwargs)

    @cached_property
    def dealiased_id(self):
        return self.aliases.get(self.input_id, self.input_id)

    def _set_prefix_accession(self):
        try:
            prefix, accession = self.dealiased_id.split(":", 1)
        except ValueError:
            prefix, accession = None, None
        self._prefix = prefix
        self._accession = accession

    @property
    def prefix(self):
        if not hasattr(self, "_prefix"):
            self._set_prefix_accession()
        return self._prefix

    @property
    def prefix_lower(self):
        if self.prefix is None:
            return None
        return self.prefix.lower()

    @property
    def accession(self):
        if not hasattr(self, "_accession"):
            self._set_prefix_accession()
        return self._accession

    @property
    def standard_prefix(self):
        if not hasattr(self, "_standard_prefix"):
            self._standardize()
        return self._standard_prefix

    @property
    def standard_accession(self):
        if not hasattr(self, "_standard_accession"):
            self._standardize()
        return self._standard_accession

    @cached_property
    def handler(self):
        from .handlers import Handler, get_handler

        if self.is_handled_prefix:
            return get_handler(self.prefix_lower)
        return Handler(self.prefix_lower)

    @cached_property
    def is_handled_prefix(self):
        from .handlers import prefix_to_handler

        return self.prefix_lower in prefix_to_handler

    def inspect(self):
        return self.handler.inspect(self)

    def _standardize(self):
        if self.prefix_lower is None:
            self._standard_prefix = None
            self._standard_accession = None
            self._standard_id = self.dealiased_id
            return None
        (
            self._standard_prefix,
            self._standard_accession,
        ) = self.handler.standardize_prefix_accession(self.accession)
        self._standard_id = f"{self._standard_prefix}:{self._standard_accession}"

    @property
    def standard_id(self):
        if not hasattr(self, "_standard_id"):
            self._standardize()
        return self._standard_id

    @cached_property
    def short_id(self):
        return shorten_citekey(self.standard_id)

    @cached_property
    def all_ids(self):
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
        return csl_item

    def is_pandoc_xnos_prefix(self, log_case_warning=False):
        from .handlers import _pandoc_xnos_prefixes

        if self.prefix in _pandoc_xnos_prefixes:
            return True
        if log_case_warning and self.prefix_lower in _pandoc_xnos_prefixes:
            logging.warning(
                "pandoc-xnos prefixes should be all lowercase.\n"
                f'Should {self.input_id!r} use {self.prefix_lower!r} rather than "{self.prefix!r}"?'
            )
        return False


@functools.lru_cache(maxsize=5_000)
def standardize_citekey(citekey, warn_if_changed=False):
    """
    Standardize citation keys based on their source
    """
    standard_citekey = CiteKey(citekey).standard_id
    if warn_if_changed and citekey != standard_citekey:
        logging.warning(
            f"standardize_citekey expected citekey to already be standardized.\n"
            f"Instead citekey was changed from {citekey!r} to {standard_citekey!r}"
        )
    return standard_citekey


def shorten_citekey(standard_citekey):
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


def citekey_to_csl_item(citekey, prune=True):
    """
    Generate a CSL Item (Python dictionary) for the input citekey.
    """
    from manubot import __version__ as manubot_version
    from .handlers import prefix_to_handler

    citekey_obj = CiteKey(citekey)
    if citekey_obj.prefix_lower not in prefix_to_handler:
        msg = f"Unsupported citation source {citekey_obj.prefix_lower!r} in {citekey!r}"
        raise ValueError(msg)
    csl_item = citekey_obj.csl_item
    note_text = f"This CSL JSON Item was automatically generated by Manubot v{manubot_version} using citation-by-identifier."
    note_dict = {"standard_id": citekey_obj.standard_id}
    csl_item.note_append_text(note_text)
    csl_item.note_append_dict(note_dict)
    csl_item.set_id(citekey_obj.short_id)
    csl_item.clean(prune=prune)
    return csl_item


def url_to_citekey(url):
    """
    Convert a HTTP(s) URL into a citekey.
    For supported sources, convert from url citekey to an alternative source like doi.
    If citekeys fail inspection, revert alternative sources to URLs.
    """
    from urllib.parse import urlparse, unquote

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
