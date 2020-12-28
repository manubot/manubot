import logging
import re
import xml.etree.ElementTree

import requests

from manubot.util import get_manubot_user_agent

from .csl_item import CSL_Item
from .handlers import Handler


class Handler_arXiv(Handler):

    standard_prefix = "arxiv"

    prefixes = [
        "arxiv",
    ]
    accession_pattern = re.compile(
        r"(?P<versionless_id>[0-9]{4}\.[0-9]{4,5}|[a-z\-]+(\.[A-Z]{2})?/[0-9]{7})(?P<version>v[0-9]+)?"
    )

    def inspect(self, citekey):
        # https://arxiv.org/help/arxiv_identifier
        if not self._get_pattern().fullmatch(citekey.accession):
            return "arXiv identifiers must conform to syntax described at https://arxiv.org/help/arxiv_identifier."

    def get_csl_item(self, citekey):
        return get_arxiv_csl_item(citekey.standard_accession)


class CSL_Item_arXiv(CSL_Item):
    def _set_invariant_fields(self):
        # Set journal/publisher to arXiv
        self["container-title"] = "arXiv"
        self["publisher"] = "arXiv"
        # Set CSL type to report for preprint
        self["type"] = "report"
        return self

    def log_journal_doi(self, arxiv_id, journal_ref=None):
        if "DOI" not in self:
            return
        msg = f"arXiv article {arxiv_id} published at https://doi.org/{self['DOI']}"
        if journal_ref:
            msg += f" — {journal_ref}"
        logging.info(msg)

    def set_identifier_fields(self, arxiv_id):
        self.set_id(f"arxiv:{arxiv_id}")
        self["URL"] = f"https://arxiv.org/abs/{arxiv_id}"
        self["number"] = arxiv_id
        _, version = split_arxiv_id_version(arxiv_id)
        if version:
            self["version"] = version


def split_arxiv_id_version(arxiv_id: str):
    """
    Return (versionless_id, version) tuple.
    Version refers to the verion suffix like 'v2' or None.
    """
    match = re.match(Handler_arXiv.accession_pattern, arxiv_id)
    return match.group("versionless_id"), match.group("version")


def get_arxiv_csl_item(arxiv_id: str):
    """
    Return csl_item item for an arXiv identifier.
    Chooses which arXiv API to use based on whether arxiv_id
    is versioned, since only one endpoint supports versioning.
    """
    _, version = split_arxiv_id_version(arxiv_id)
    if version:
        return get_arxiv_csl_item_export_api(arxiv_id)
    return get_arxiv_csl_item_oai(arxiv_id)


def query_arxiv_api(url, params):
    headers = {"User-Agent": get_manubot_user_agent()}
    response = requests.get(url, params, headers=headers)
    response.raise_for_status()
    xml_tree = xml.etree.ElementTree.fromstring(response.text)
    return xml_tree


def get_arxiv_csl_item_export_api(arxiv_id):
    """
    Return csl_item item for an arXiv record.

    arxiv_id can be versioned, like `1512.00567v2`, or versionless, like
    `1512.00567`. If versionless, the arXiv API will return metadata for the
    latest version. Legacy IDs, such as `cond-mat/0703470v2`, are also
    supported.

    If arXiv has an associated DOI for the record, a warning is logged to
    alert the user that an alternative version of record exists.

    References:
    - https://arxiv.org/help/api/index
    - http://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html
    - https://github.com/citation-style-language/schema/blob/master/csl-data.json
    """
    xml_tree = query_arxiv_api(
        url="https://export.arxiv.org/api/query",
        params={"id_list": arxiv_id, "max_results": 1},
    )

    # XML namespace prefixes
    prefix = "{http://www.w3.org/2005/Atom}"
    alt_prefix = "{http://arxiv.org/schemas/atom}"

    # Parse XML
    (entry,) = xml_tree.findall(prefix + "entry")

    # Create dictionary for CSL Item
    csl_item = CSL_Item_arXiv()

    # Extract versioned arXiv ID
    url = entry.findtext(prefix + "id")
    pattern = re.compile(r"arxiv.org/abs/(.+)")
    match = pattern.search(url)
    versioned_id = match.group(1)
    csl_item.set_identifier_fields(versioned_id)

    # Extrat CSL title field
    csl_item["title"] = entry.findtext(prefix + "title")

    # Extract CSL date field
    published = entry.findtext(prefix + "published")
    csl_item.set_date(published, variable="issued")

    # Extract authors
    authors = list()
    for elem in entry.findall(prefix + "author"):
        name = elem.findtext(prefix + "name")
        author = {"literal": name}
        authors.append(author)
    csl_item["author"] = authors

    csl_item._set_invariant_fields()

    # Extract abstract
    abstract = entry.findtext(prefix + "summary").strip()
    if abstract:
        # remove newlines that were added to wrap abstract
        abstract = remove_newlines(abstract)
        csl_item["abstract"] = abstract

    # Check if the article has been published with a DOI
    doi = entry.findtext(f"{alt_prefix}doi")
    if doi:
        csl_item["DOI"] = doi
        journal_ref = entry.findtext(alt_prefix + "journal_ref")
        csl_item.log_journal_doi(arxiv_id, journal_ref)
    return csl_item


def get_arxiv_csl_item_oai(arxiv_id):
    """
    Generate a CSL Item for an unversioned arXiv identifier
    using arXiv's OAI_PMH v2.0 API <https://arxiv.org/help/oa>.
    This endpoint does not support versioned `arxiv_id`.
    """
    # XML namespace prefixes
    ns_oai = "{http://www.openarchives.org/OAI/2.0/}"
    ns_arxiv = "{http://arxiv.org/OAI/arXiv/}"

    xml_tree = query_arxiv_api(
        url="https://export.arxiv.org/oai2",
        params={
            "verb": "GetRecord",
            "metadataPrefix": "arXiv",
            "identifier": f"oai:arXiv.org:{arxiv_id}",
        },
    )

    # Create dictionary for CSL Item
    csl_item = CSL_Item_arXiv()
    # Extract parent XML elements
    (header_elem,) = xml_tree.findall(
        f"{ns_oai}GetRecord/{ns_oai}record/{ns_oai}header"
    )
    (metadata_elem,) = xml_tree.findall(
        f"{ns_oai}GetRecord/{ns_oai}record/{ns_oai}metadata"
    )
    (arxiv_elem,) = metadata_elem.findall(f"{ns_arxiv}arXiv")
    # Set identifier fields
    response_arxiv_id = arxiv_elem.findtext(f"{ns_arxiv}id")
    if arxiv_id != response_arxiv_id:
        logging.warning(
            "arXiv oai2 query returned a different arxiv_id:"
            f" {arxiv_id} became {response_arxiv_id}"
        )
    csl_item.set_identifier_fields(response_arxiv_id)
    # Set title and date
    title = arxiv_elem.findtext(f"{ns_arxiv}title")
    if title:
        csl_item["title"] = " ".join(title.split())
    datestamp = header_elem.findtext(f"{ns_oai}datestamp")
    csl_item.set_date(datestamp, "issued")

    # Extract authors
    author_elems = arxiv_elem.findall(f"{ns_arxiv}authors/{ns_arxiv}author")
    authors = list()
    for author_elem in author_elems:
        author = {}
        given = author_elem.findtext(f"{ns_arxiv}forenames")
        family = author_elem.findtext(f"{ns_arxiv}keyname")
        if given:
            author["given"] = given
        if family:
            author["family"] = family
        authors.append(author)
    csl_item["author"] = authors

    csl_item._set_invariant_fields()

    abstract = arxiv_elem.findtext(f"{ns_arxiv}abstract")
    if abstract:
        csl_item["abstract"] = remove_newlines(abstract)

    license = arxiv_elem.findtext(f"{ns_arxiv}license")
    if license:
        csl_item.note_append_dict({"license": license})

    doi = arxiv_elem.findtext(f"{ns_arxiv}doi")
    if doi:
        csl_item["DOI"] = doi
        journal_ref = arxiv_elem.findtext(f"{ns_arxiv}journal-ref")
        csl_item.log_journal_doi(arxiv_id, journal_ref)
    return csl_item


def remove_newlines(text):
    return re.sub(pattern=r"\n(?!\s)", repl=" ", string=text)


def get_arxiv_csl_item_zotero(arxiv_id):
    """
    Generate CSL JSON Data for an arXiv ID using Zotero's translation-server.
    """
    from manubot.cite.zotero import get_csl_item

    return get_csl_item(f"arxiv:{arxiv_id}")
