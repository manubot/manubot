import functools
import json
import logging
import os
import warnings
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from xml.etree import ElementTree

import requests

from manubot.util import get_manubot_user_agent

from .citekey import CiteKey
from .handlers import Handler


class Handler_PubMed(Handler):

    standard_prefix = "pubmed"

    prefixes = [
        "pubmed",
        "pmid",
    ]
    accession_pattern = r"[1-9][0-9]{0,7}"

    def inspect(self, citekey: CiteKey) -> Optional[str]:
        identifier = citekey.accession
        # https://www.nlm.nih.gov/bsd/mms/medlineelements.html#pmid
        if identifier.startswith("PMC"):
            return (
                "PubMed Identifiers should start with digits rather than PMC. "
                f"Should {citekey.dealiased_id!r} switch the citation source to 'pmc'?"
            )
        elif not self._get_pattern().fullmatch(identifier):
            return "PubMed Identifiers should be 1-8 digits with no leading zeros."

    def get_csl_item(self, citekey: CiteKey) -> Dict[str, Any]:
        return get_pubmed_csl_item(citekey.standard_accession)


class Handler_PMC(Handler):

    standard_prefix = "pmc"
    prefixes = [
        "pmc",
        "pmcid",
    ]
    accession_pattern = r"PMC[0-9]+"

    def inspect(self, citekey: CiteKey) -> Optional[str]:
        identifier = citekey.accession
        # https://www.nlm.nih.gov/bsd/mms/medlineelements.html#pmc
        if not identifier.startswith("PMC"):
            return "PubMed Central Identifiers must start with 'PMC'."
        elif not self._get_pattern().fullmatch(identifier):
            return (
                "Identifier does not conform to the PMCID regex. "
                "Double check the PMCID."
            )

    def get_csl_item(self, citekey: CiteKey):
        return get_pmc_csl_item(citekey.standard_accession)


def get_pmc_csl_item(pmcid: str) -> Dict[str, Any]:
    """
    Get the CSL Item for a PubMed Central record by its PMID, PMCID, or
    DOI, using the NCBI Citation Exporter API.

    https://api.ncbi.nlm.nih.gov/lit/ctxp
    https://github.com/manubot/manubot/issues/21
    https://twitter.com/dhimmel/status/1061787168820092929
    """
    assert pmcid.startswith("PMC")
    csl_item = _get_literature_citation_exporter_csl_item("pmc", pmcid[3:])
    if "URL" not in csl_item:
        csl_item[
            "URL"
        ] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{csl_item.get('PMCID', pmcid)}/"
    return csl_item


def _get_literature_citation_exporter_csl_item(
    database: str, identifier: str
) -> Dict[str, Any]:
    """
    https://api.ncbi.nlm.nih.gov/lit/ctxp
    """
    if database not in {"pubmed", "pmc"}:
        logging.error(
            f"Error calling _get_literature_citation_exporter_csl_item.\n"
            f'database must be either "pubmed" or "pmc", not {database}'
        )
        assert False
    if not identifier:
        logging.error(
            f"Error calling _get_literature_citation_exporter_csl_item.\n"
            f"identifier cannot be blank"
        )
        assert False
    params = {"format": "csl", "id": identifier}
    headers = {"User-Agent": get_manubot_user_agent()}
    url = f"https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/{database}/"
    response = requests.get(url, params, headers=headers)
    try:
        csl_item = response.json()
    except Exception as error:
        logging.error(
            f"Error fetching {database} metadata for {identifier}.\n"
            f"Invalid JSON response from {response.url}:\n{response.text}"
        )
        raise error
    assert isinstance(csl_item, dict)
    if csl_item.get("status", "okay") == "error":
        logging.error(
            f"Error fetching {database} metadata for {identifier}.\n"
            f"Literature Citation Exporter returned JSON indicating an error for {response.url}\n"
            f"{json.dumps(csl_item, indent=2)}"
        )
        assert False
    return csl_item


def get_pubmed_csl_item(pmid: Union[str, int]) -> Dict[str, Any]:
    """
    Query NCBI E-Utilities to create CSL Items for PubMed IDs.

    https://github.com/manubot/manubot/issues/21
    https://github.com/ncbi/citation-exporter/issues/3#issuecomment-355313143
    """
    pmid = str(pmid)
    params = {"db": "pubmed", "id": pmid, "rettype": "full"}
    headers = {"User-Agent": get_manubot_user_agent()}
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    with _get_eutils_rate_limiter():
        response = requests.get(url, params, headers=headers)
    try:
        xml_article_set = ElementTree.fromstring(response.text)
        assert isinstance(xml_article_set, ElementTree.Element)
        assert xml_article_set.tag == "PubmedArticleSet"
        (xml_article,) = list(xml_article_set)
        assert xml_article.tag in ["PubmedArticle", "PubmedBookArticle"]
    except Exception as error:
        logging.error(
            f"Error fetching PubMed metadata for {pmid}.\n"
            f"Unsupported XML response from {response.url}:\n{response.text}"
        )
        raise error
    try:
        csl_item = csl_item_from_pubmed_article(xml_article)
    except Exception as error:
        msg = f"Error parsing the following PubMed metadata for PMID {pmid}:\n{response.text}"
        logging.error(msg)
        raise error
    return csl_item


def csl_item_from_pubmed_article(article: ElementTree.Element) -> Dict[str, Any]:
    """
    Extract a CSL Item dictionary from a PubmedArticle XML element.
    https://github.com/citation-style-language/schema/blob/master/csl-data.json
    """
    if not article.tag == "PubmedArticle":
        raise ValueError(
            f"Expected article to be an XML element with tag PubmedArticle, received tag {article.tag!r}"
        )

    csl_item = dict()

    if not article.find("MedlineCitation/Article"):
        raise NotImplementedError("Unsupported PubMed record: no <Article> element")

    title = article.findtext("MedlineCitation/Article/ArticleTitle")
    if title:
        csl_item["title"] = title

    volume = article.findtext("MedlineCitation/Article/Journal/JournalIssue/Volume")
    if volume:
        csl_item["volume"] = volume

    issue = article.findtext("MedlineCitation/Article/Journal/JournalIssue/Issue")
    if issue:
        csl_item["issue"] = issue

    page = article.findtext("MedlineCitation/Article/Pagination/MedlinePgn")
    if page:
        csl_item["page"] = page

    journal = article.findtext("MedlineCitation/Article/Journal/Title")
    if journal:
        csl_item["container-title"] = journal

    journal_short = article.findtext("MedlineCitation/Article/Journal/ISOAbbreviation")
    if journal_short:
        csl_item["container-title-short"] = journal_short

    issn = article.findtext("MedlineCitation/Article/Journal/ISSN")
    if issn:
        csl_item["ISSN"] = issn

    date_parts = extract_publication_date_parts(article)
    if date_parts:
        csl_item["issued"] = {"date-parts": [date_parts]}

    authors_csl = list()
    authors = article.findall("MedlineCitation/Article/AuthorList/Author")
    for author in authors:
        author_csl = dict()
        given = author.findtext("ForeName")
        if given:
            author_csl["given"] = given
        family = author.findtext("LastName")
        if family:
            author_csl["family"] = family
        authors_csl.append(author_csl)
    if authors_csl:
        csl_item["author"] = authors_csl

    for id_type, key in ("pubmed", "PMID"), ("pmc", "PMCID"), ("doi", "DOI"):
        xpath = f"PubmedData/ArticleIdList/ArticleId[@IdType='{id_type}']"
        value = article.findtext(xpath)
        if value:
            csl_item[key] = value.lower() if key == "DOI" else value

    abstract = article.findtext("MedlineCitation/Article/Abstract/AbstractText")
    if abstract:
        csl_item["abstract"] = abstract

    csl_item["URL"] = f"https://www.ncbi.nlm.nih.gov/pubmed/{csl_item['PMID']}"
    csl_item["type"] = "article-journal"

    return csl_item


month_abbrev_to_int: Dict[str, int] = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def extract_publication_date_parts(article: ElementTree.Element) -> List[int]:
    """
    Extract date published from a PubmedArticle XML element.
    """
    date_parts = []

    # Electronic articles
    date = article.find("MedlineCitation/Article/ArticleDate")
    if date:
        for part in "Year", "Month", "Day":
            part = date.findtext(part)
            if not part:
                break
            date_parts.append(int(part))
        return date_parts

    # Print articles
    date = article.find("MedlineCitation/Article/Journal/JournalIssue/PubDate")
    year = date.findtext("Year")
    if year:
        date_parts.append(int(year))
    month = date.findtext("Month")
    if month:
        try:
            date_parts.append(month_abbrev_to_int[month])
        except KeyError:
            date_parts.append(int(month))
    day = date.findtext("Day")
    if day:
        date_parts.append(int(day))
    return date_parts


def get_pmcid_and_pmid_for_doi(doi: str) -> Dict[str, str]:
    """
    Query PMC's ID Converter API to retrieve the PMCID and PMID for a DOI.
    Does not work for DOIs that are in Pubmed but not PubMed Central.
    https://www.ncbi.nlm.nih.gov/pmc/tools/id-converter-api/
    """
    assert isinstance(doi, str)
    assert doi.startswith("10.")
    params = {"ids": doi, "tool": "manubot"}
    url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    response = requests.get(url, params)
    if not response.ok:
        logging.warning(f"Status code {response.status_code} querying {response.url}\n")
        return {}
    try:
        element_tree = ElementTree.fromstring(response.text)
        assert element_tree.tag == "pmcids"
    except Exception:
        logging.warning(
            f"Error fetching PMC ID conversion for {doi}.\n"
            f"Response from {response.url}:\n{response.text}"
        )
        return {}
    records = element_tree.findall("record")
    if len(records) != 1:
        logging.warning(
            f"Expected PubMed Central ID converter to return a single XML record for {doi}.\n"
            f"Response from {response.url}:\n{response.text}"
        )
        return {}
    (record,) = records
    if record.findtext("status", default="okay") == "error":
        return {}
    id_dict = {}
    for id_type in "pmcid", "pmid":
        id_ = record.get(id_type)
        if id_:
            id_dict[id_type.upper()] = id_
    return id_dict


def get_pmid_for_doi(doi: str) -> Optional[str]:
    """
    Query NCBI's E-utilities to retrieve the PMID for a DOI.
    """
    assert isinstance(doi, str)
    assert doi.startswith("10.")
    params = {"db": "pubmed", "term": f"{doi}[DOI]"}
    headers = {"User-Agent": get_manubot_user_agent()}
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    with _get_eutils_rate_limiter():
        response = requests.get(url, params, headers=headers)
    if not response.ok:
        logging.warning(f"Status code {response.status_code} querying {response.url}\n")
        return None
    try:
        element_tree = ElementTree.fromstring(response.text)
        assert isinstance(element_tree, ElementTree.Element)
        assert element_tree.tag == "eSearchResult"
    except Exception:
        logging.warning(
            f"Error in ESearch XML for DOI: {doi}.\n"
            f"Response from {response.url}:\n{response.text}"
        )
        return None
    id_elems = element_tree.findall("IdList/Id")
    if len(id_elems) != 1:
        logging.debug(
            f"No PMIDs found for {doi}.\n"
            f"Response from {response.url}:\n{response.text}"
        )
        return None
    (id_elem,) = id_elems
    return id_elem.text


def get_pubmed_ids_for_doi(doi: str) -> Dict[str, str]:
    """
    Return a dictionary with PMCID and PMID, if they exist, for the specified
    DOI. See https://github.com/manubot/manubot/issues/45.
    """
    pubmed_ids = get_pmcid_and_pmid_for_doi(doi)
    if not pubmed_ids:
        pmid = get_pmid_for_doi(doi)
        if pmid:
            pubmed_ids["PMID"] = pmid
    return pubmed_ids


if TYPE_CHECKING:
    # support RateLimiter return type while avoiding unused runtime import
    # https://stackoverflow.com/a/39757388/4651668
    from ratelimiter import RateLimiter


@functools.lru_cache()
def _get_eutils_rate_limiter() -> "RateLimiter":
    """
    Rate limiter to cap NCBI E-utilities queries to <= 3 per second as per
    https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
    """
    with warnings.catch_warnings():
        # https://github.com/RazerM/ratelimiter/issues/10
        # https://github.com/manubot/manubot/issues/257
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        from ratelimiter import RateLimiter

    if "CI" in os.environ:
        # multiple CI jobs might be running concurrently
        return RateLimiter(max_calls=1, period=1.5)
    return RateLimiter(max_calls=2, period=1)
