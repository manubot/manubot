import logging
import re
import xml.etree.ElementTree

import requests

from .csl_item import CSL_Item
from manubot.util import get_manubot_user_agent


def get_arxiv_csl_item(arxiv_id):
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
    url = "https://export.arxiv.org/api/query"
    params = {"id_list": arxiv_id, "max_results": 1}
    headers = {"User-Agent": get_manubot_user_agent()}
    response = requests.get(url, params, headers=headers)

    # XML namespace prefixes
    prefix = "{http://www.w3.org/2005/Atom}"
    alt_prefix = "{http://arxiv.org/schemas/atom}"

    # Parse XML
    xml_tree = xml.etree.ElementTree.fromstring(response.text)
    (entry,) = xml_tree.findall(prefix + "entry")

    # Create dictionary for CSL Item
    csl_item = CSL_Item()

    # Extract versioned arXiv ID
    url = entry.findtext(prefix + "id")
    pattern = re.compile(r"arxiv.org/abs/(.+)")
    match = pattern.search(url)
    versioned_id = match.group(1)
    csl_item["number"] = versioned_id
    _, csl_item["version"] = versioned_id.rsplit("v", 1)
    csl_item["URL"] = "https://arxiv.org/abs/" + versioned_id

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

    # Set publisher to arXiv
    csl_item["container-title"] = "arXiv"
    csl_item["publisher"] = "arXiv"

    # Extract abstract
    abstract = entry.findtext(prefix + "summary").strip()
    if abstract:
        # remove newlines that were added to wrap abstract
        abstract = remove_newlines(abstract)
        csl_item["abstract"] = abstract

    # Check if the article has been published with a DOI
    DOI = entry.findtext("{http://arxiv.org/schemas/atom}doi")
    if DOI:
        csl_item["DOI"] = DOI
        journal_ref = entry.findtext(alt_prefix + "journal_ref")
        msg = f"arXiv article {arxiv_id} published at https://doi.org/{DOI}"
        if journal_ref:
            msg += f" — {journal_ref}"
        logging.warning(msg)
    # Set CSL type to report for preprint
    csl_item["type"] = "report"
    return csl_item


def remove_newlines(text):
    return re.sub(pattern=r"\n(?!\s)", repl=" ", string=text)


def get_arxiv_csl_item_oai(arxiv_id):
    """
    Must be unversioned ID.
    """
    # XML namespace prefixes
    ns_oai = "{http://www.openarchives.org/OAI/2.0/}"
    ns_arxiv = "{http://arxiv.org/OAI/arXiv/}"

    url = "https://export.arxiv.org/oai2"
    params = {
        "verb": "GetRecord",
        "metadataPrefix": "arXiv",
        "identifier": f"oai:arXiv.org:{arxiv_id}",
    }
    headers = {"User-Agent": get_manubot_user_agent()}
    response = requests.get(url, params, headers=headers)

    # Create dictionary for CSL Item
    csl_item = CSL_Item()

    xml_tree = xml.etree.ElementTree.fromstring(response.text)
    header_elem, = xml_tree.findall(f"{ns_oai}GetRecord/{ns_oai}record/{ns_oai}header")
    metadata_elem, = xml_tree.findall(f"{ns_oai}GetRecord/{ns_oai}record/{ns_oai}metadata")
    arxiv_elem, = metadata_elem.findall(f"{ns_arxiv}arXiv")
    title = arxiv_elem.findtext(f"{ns_arxiv}title")
    if title:
        csl_item["title"] = ' '.join(title.split())
    datestamp = header_elem.findtext(f"{ns_oai}datestamp")
    csl_item.set_date(datestamp, "issued")

    # Set publisher to arXiv
    csl_item["container-title"] = "arXiv"
    csl_item["publisher"] = "arXiv"

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

    abstract = arxiv_elem.findtext(f"{ns_arxiv}abstract")
    if abstract:
        csl_item["abstract"] = remove_newlines(abstract)

    license = arxiv_elem.findtext(f"{ns_arxiv}license")
    if license:
        csl_item.note_append_dict({"license": license})

    #import pdb; pdb.set_trace()
    return csl_item

