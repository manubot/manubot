"""Functions importable from manubot.cite submodule (submodule API):

  standardize_citekey()
  citekey_to_csl_item()

Helpers:

  inspect_citekey()
  is_valid_citekey() - also used in manubot.process
  shorten_citekey() - used solely in manubot.process
  infer_citekey_prefix()

"""
import functools
import logging
import re

from manubot.util import import_function

citeproc_retrievers = {
    "doi": "manubot.cite.doi.get_doi_csl_item",
    "pmid": "manubot.cite.pubmed.get_pubmed_csl_item",
    "pmcid": "manubot.cite.pubmed.get_pmc_csl_item",
    "arxiv": "manubot.cite.arxiv.get_arxiv_csl_item",
    "isbn": "manubot.cite.isbn.get_isbn_csl_item",
    "wikidata": "manubot.cite.wikidata.get_wikidata_csl_item",
    "url": "manubot.cite.url.get_url_csl_item",
}

"""
Regex to extract citation keys.
The leading '@' is omitted from the single match group.

Same rules as pandoc, except more permissive in the following ways:

1. the final character can be a slash because many URLs end in a slash.
2. underscores are allowed in internal characters because URLs, DOIs, and
   citation tags often contain underscores.

If a citekey does not match this regex, it can be substituted for a
tag that does, as defined in citation-tags.tsv.

https://github.com/greenelab/manubot-rootstock/issues/2#issuecomment-312153192

Prototyped at https://regex101.com/r/s3Asz3/4
"""
citekey_pattern = re.compile(r"(?<!\w)@([a-zA-Z0-9][\w:.#$%&\-+?<>~/]*[a-zA-Z0-9/])")


@functools.lru_cache(maxsize=5_000)
def standardize_citekey(citekey, warn_if_changed=False):
    """
    Standardize citation keys based on their source
    """
    source, identifier = citekey.split(":", 1)

    if source == "doi":
        if identifier.startswith("10/"):
            from manubot.cite.doi import expand_short_doi

            try:
                identifier = expand_short_doi(identifier)
            except Exception as error:
                # If DOI shortening fails, return the unshortened DOI.
                # DOI metadata lookup will eventually fail somewhere with
                # appropriate error handling, as opposed to here.
                logging.error(
                    f"Error in expand_short_doi for {identifier} "
                    f"due to a {error.__class__.__name__}:\n{error}"
                )
                logging.info(error, exc_info=True)
        identifier = identifier.lower()

    if source == "isbn":
        from isbnlib import to_isbn13

        identifier = to_isbn13(identifier)

    standard_citekey = f"{source}:{identifier}"
    if warn_if_changed and citekey != standard_citekey:
        logging.warning(
            f"standardize_citekey expected citekey to already be standardized.\n"
            f"Instead citekey was changed from {citekey!r} to {standard_citekey!r}"
        )
    return standard_citekey


regexes = {
    "arxiv": re.compile(
        r"(?P<versionless_id>[0-9]{4}\.[0-9]{4,5}|[a-z\-]+(\.[A-Z]{2})?/[0-9]{7})(?P<version>v[0-9]+)?"
    ),
    "pmid": re.compile(r"[1-9][0-9]{0,7}"),
    "pmcid": re.compile(r"PMC[0-9]+"),
    "doi": re.compile(r"10\.[0-9]{4,9}/\S+"),
    "shortdoi": re.compile(r"10/[a-zA-Z0-9]+"),
    "wikidata": re.compile(r"Q[0-9]+"),
}


def inspect_citekey(citekey):
    """
    Check citekeys adhere to expected formats. If an issue is detected a
    string describing the issue is returned. Otherwise returns None.
    """
    source, identifier = citekey.split(":", 1)

    if source == "arxiv":
        # https://arxiv.org/help/arxiv_identifier
        if not regexes["arxiv"].fullmatch(identifier):
            return "arXiv identifiers must conform to syntax described at https://arxiv.org/help/arxiv_identifier."

    if source == "pmid":
        # https://www.nlm.nih.gov/bsd/mms/medlineelements.html#pmid
        if identifier.startswith("PMC"):
            return (
                "PubMed Identifiers should start with digits rather than PMC. "
                f"Should {citekey!r} switch the citation source to 'pmcid'?"
            )
        elif not regexes["pmid"].fullmatch(identifier):
            return "PubMed Identifiers should be 1-8 digits with no leading zeros."

    if source == "pmcid":
        # https://www.nlm.nih.gov/bsd/mms/medlineelements.html#pmc
        if not identifier.startswith("PMC"):
            return "PubMed Central Identifiers must start with 'PMC'."
        elif not regexes["pmcid"].fullmatch(identifier):
            return (
                "Identifier does not conform to the PMCID regex. "
                "Double check the PMCID."
            )

    if source == "doi":
        if identifier.startswith("10."):
            # https://www.crossref.org/blog/dois-and-matching-regular-expressions/
            if not regexes["doi"].fullmatch(identifier):
                return (
                    "Identifier does not conform to the DOI regex. "
                    "Double check the DOI."
                )
        elif identifier.startswith("10/"):
            # shortDOI, see http://shortdoi.org
            if not regexes["shortdoi"].fullmatch(identifier):
                return (
                    "Identifier does not conform to the shortDOI regex. "
                    "Double check the shortDOI."
                )
        else:
            return "DOIs must start with '10.' (or '10/' for shortDOIs)."

    if source == "isbn":
        import isbnlib

        fail = isbnlib.notisbn(identifier, level="strict")
        if fail:
            return f"identifier violates the ISBN syntax according to isbnlib v{isbnlib.__version__}"

    if source == "wikidata":
        # https://www.wikidata.org/wiki/Wikidata:Identifiers
        if not identifier.startswith("Q"):
            return "Wikidata item IDs must start with 'Q'."
        elif not regexes["wikidata"].fullmatch(identifier):
            return (
                "Identifier does not conform to the Wikidata regex. "
                "Double check the entity ID."
            )

    return None


def is_valid_citekey(
    citekey, allow_tag=False, allow_raw=False, allow_pandoc_xnos=False
):
    """
    Return True if citekey is a properly formatted string. Return False if
    citekey is not a citation or is an invalid citation.

    In the case citekey is invalid, an error is logged. This
    function does not catch all invalid citekeys, but instead performs cursory
    checks, such as ensuring citekeys adhere to the expected formats. No calls to
    external resources are used by these checks, so they will not detect
    citekeys to non-existent identifiers unless those identifiers violate
    their source's syntax.

    allow_tag=False, allow_raw=False, and allow_pandoc_xnos=False enable
    allowing citekey sources that are valid for Manubot manuscripts, but
    likely not elsewhere. allow_tag=True enables citekey tags (e.g.
    tag:citation-tag). allow_raw=True enables raw citekeys (e.g.
    raw:manual-reference). allow_pandoc_xnos=True still returns False for
    pandoc-xnos references (e.g. fig:figure-id), but does not log an error.
    With the default of False for these arguments, valid sources are restricted
    to those for which manubot can retrieve metadata based only on the
    standalone citekey.
    """
    if not isinstance(citekey, str):
        logging.error(
            f"citekey should be type 'str' not "
            f"{type(citekey).__name__!r}: {citekey!r}"
        )
        return False
    if citekey.startswith("@"):
        logging.error(f"invalid citekey: {citekey!r}\nstarts with '@'")
        return False
    try:
        source, identifier = citekey.split(":", 1)
    except ValueError:
        logging.error(
            f"citekey not splittable via a single colon: {citekey}. "
            "Citekeys must be in the format of `source:identifier`."
        )
        return False

    if not source or not identifier:
        msg = f"invalid citekey: {citekey!r}\nblank source or identifier"
        logging.error(msg)
        return False

    if allow_pandoc_xnos:
        # Exempted non-citation sources used for pandoc-fignos,
        # pandoc-tablenos, and pandoc-eqnos
        pandoc_xnos_keys = {"fig", "tbl", "eq"}
        if source in pandoc_xnos_keys:
            return False
        if source.lower() in pandoc_xnos_keys:
            logging.error(
                f"pandoc-xnos reference types should be all lowercase.\n"
                f'Should {citekey!r} use {source.lower()!r} rather than "{source!r}"?'
            )
            return False

    # Check supported source type
    sources = set(citeproc_retrievers)
    if allow_raw:
        sources.add("raw")
    if allow_tag:
        sources.add("tag")
    if source not in sources:
        if source.lower() in sources:
            logging.error(
                f"citekey sources should be all lowercase.\n"
                f'Should {citekey} use "{source.lower()}" rather than "{source}"?'
            )
        else:
            logging.error(
                f"invalid citekey: {citekey!r}\n"
                f"Source {source!r} is not valid.\n"
                f'Valid citation sources are {{{", ".join(sorted(sources))}}}'
            )
        return False

    inspection = inspect_citekey(citekey)
    if inspection:
        logging.error(f"invalid {source} citekey: {citekey}\n{inspection}")
        return False

    return True


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
    from manubot.cite.csl_item import CSL_Item
    from manubot import __version__ as manubot_version

    citekey == standardize_citekey(citekey, warn_if_changed=True)
    source, identifier = citekey.split(":", 1)

    if source not in citeproc_retrievers:
        msg = f"Unsupported citation source {source!r} in {citekey!r}"
        raise ValueError(msg)
    citeproc_retriever = import_function(citeproc_retrievers[source])
    csl_item = citeproc_retriever(identifier)
    csl_item = CSL_Item(csl_item)

    note_text = f"This CSL JSON Item was automatically generated by Manubot v{manubot_version} using citation-by-identifier."
    note_dict = {"standard_id": citekey}
    csl_item.note_append_text(note_text)
    csl_item.note_append_dict(note_dict)

    short_citekey = shorten_citekey(citekey)
    csl_item.set_id(short_citekey)
    csl_item.clean(prune=prune)

    return csl_item


def infer_citekey_prefix(citekey):
    """
    Passthrough citekey if it has a valid citation key prefix. Otherwise,
    if the lowercase citekey prefix is valid, convert the prefix to lowercase.
    Otherwise, assume citekey is raw and prepend "raw:".
    """
    prefixes = [f"{x}:" for x in list(citeproc_retrievers) + ["raw"]]
    for prefix in prefixes:
        if citekey.startswith(prefix):
            return citekey
        if citekey.lower().startswith(prefix):
            return prefix + citekey[len(prefix) :]
    return f"raw:{citekey}"


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
    if citekey is None or inspect_citekey(citekey) is not None:
        citekey = f"url:{url}"
    return citekey
