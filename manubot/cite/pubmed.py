import collections
import logging
import xml.etree.ElementTree

import requests


def get_pmc_citeproc(identifier):
    """
    Get the citeproc JSON for a PubMed Central record by its PMID, PMCID, or
    DOI, using the NCBI Citation Exporter API.

    https://github.com/ncbi/citation-exporter
    https://www.ncbi.nlm.nih.gov/pmc/tools/ctxp/
    https://www.ncbi.nlm.nih.gov/pmc/utils/ctxp/samples
    https://github.com/greenelab/manubot/issues/21
    """
    params = {
        'ids': identifier,
        'report': 'citeproc',
    }
    url = 'https://www.ncbi.nlm.nih.gov/pmc/utils/ctxp'
    response = requests.get(url, params)
    try:
        citeproc = response.json()
    except Exception as error:
        logging.error(f'Error fetching PMC metadata for {identifier}.\n'
                      f'Invalid response from {response.url}:\n{response.text}')
        raise error
    citeproc['URL'] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{citeproc['PMCID']}/"
    return citeproc


def get_pubmed_citeproc(pmid):
    """
    Query NCBI E-Utilities to create CSL Items for PubMed IDs.

    https://github.com/greenelab/manubot/issues/21
    https://github.com/ncbi/citation-exporter/issues/3#issuecomment-355313143
    """
    pmid = str(pmid)
    params = {
        'db': 'pubmed',
        'id': pmid,
        'rettype': 'full',
    }
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    response = requests.get(url, params)
    try:
        element_tree = xml.etree.ElementTree.fromstring(response.text)
        element_tree, = list(element_tree)
    except Exception as error:
        logging.error(f'Error fetching PubMed metadata for {pmid}.\n'
                      f'Invalid XML response from {response.url}:\n{response.text}')
        raise error
    try:
        citeproc = citeproc_from_pubmed_article(element_tree)
    except Exception as error:
        msg = f'Error parsing the following PubMed metadata for PMID {pmid}:\n{response.text}'
        logging.error(msg)
        raise error
    return citeproc


def citeproc_from_pubmed_article(article):
    """
    article is a PubmedArticle xml element tree

    https://github.com/citation-style-language/schema/blob/master/csl-data.json
    """
    citeproc = collections.OrderedDict()

    if not article.find("MedlineCitation/Article"):
        raise NotImplementedError('Unsupported PubMed record: no <Article> element')

    title = article.findtext("MedlineCitation/Article/ArticleTitle")
    if title:
        citeproc['title'] = title

    volume = article.findtext("MedlineCitation/Article/Journal/JournalIssue/Volume")
    if volume:
        citeproc['volume'] = volume

    issue = article.findtext("MedlineCitation/Article/Journal/JournalIssue/Issue")
    if issue:
        citeproc['issue'] = issue

    page = article.findtext("MedlineCitation/Article/Pagination/MedlinePgn")
    if page:
        citeproc['page'] = page

    journal = article.findtext("MedlineCitation/Article/Journal/Title")
    if journal:
        citeproc['container-title'] = journal

    journal_short = article.findtext("MedlineCitation/Article/Journal/ISOAbbreviation")
    if journal_short:
        citeproc['container-title-short'] = journal_short

    issn = article.findtext("MedlineCitation/Article/Journal/ISSN")
    if issn:
        citeproc['ISSN'] = issn

    date_parts = extract_publication_date_parts(article)
    if date_parts:
        citeproc['issued'] = {'date-parts': [date_parts]}

    authors_csl = list()
    authors = article.findall("MedlineCitation/Article/AuthorList/Author")
    for author in authors:
        author_csl = collections.OrderedDict()
        given = author.findtext('ForeName')
        if given:
            author_csl['given'] = given
        family = author.findtext('LastName')
        if family:
            author_csl['family'] = family
        authors_csl.append(author_csl)
    if authors_csl:
        citeproc['author'] = authors_csl

    for id_type, key in ('pubmed', 'PMID'), ('pmc', 'PMCID'), ('doi', 'DOI'):
        xpath = f"PubmedData/ArticleIdList/ArticleId[@IdType='{id_type}']"
        value = article.findtext(xpath)
        if value:
            citeproc[key] = value.lower() if key == 'DOI' else value

    abstract = article.findtext("MedlineCitation/Article/Abstract/AbstractText")
    if abstract:
        citeproc['abstract'] = abstract

    citeproc['URL'] = f"https://www.ncbi.nlm.nih.gov/pubmed/{citeproc['PMID']}"
    citeproc['type'] = 'article-journal'

    return citeproc


month_abbrev_to_int = {
    'Jan': 1,
    'Feb': 2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12,
}


def extract_publication_date_parts(article):
    """
    Extract date published from a PubmedArticle xml element tree.
    """
    date_parts = []

    # Electronic articles
    date = article.find("MedlineCitation/Article/ArticleDate")
    if date:
        for part in 'Year', 'Month', 'Day':
            part = date.findtext(part)
            if not part:
                break
            date_parts.append(int(part))
        return date_parts

    # Print articles
    date = article.find("MedlineCitation/Article/Journal/JournalIssue/PubDate")
    year = date.findtext('Year')
    if year:
        date_parts.append(int(year))
    month = date.findtext('Month')
    if month:
        date_parts.append(month_abbrev_to_int[month])
    day = date.findtext('Day')
    if day:
        date_parts.append(int(day))
    return date_parts


if __name__ == '__main__':
    for pmid in 25648772, 27094199, 11234041, 14728133:
        print(pmid)
        citeproc = get_pubmed_citeproc(pmid)
        print(citeproc)
