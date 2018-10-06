import json
import pathlib
import shutil
import subprocess

import pytest

from manubot.cite.util import (
    citation_pattern,
    citation_to_citeproc,
    get_citation_id,
    standardize_citation,
)
from manubot.cite.pubmed import (
    get_pmcid_and_pmid_for_doi,
    get_pmid_for_doi,
    get_pubmed_ids_for_doi,
)


@pytest.mark.parametrize("citation_string", [
    ('@doi:10.5061/dryad.q447c/1'),
    ('@arxiv:1407.3561v1'),
    ('@doi:10.1007/978-94-015-6859-3_4'),
    ('@tag:tag_with_underscores'),
    ('@tag:tag-with-hyphens'),
    ('@url:https://greenelab.github.io/manubot-rootstock/'),
    ('@tag:abc123'),
    ('@tag:123abc'),
])
def test_citation_pattern_match(citation_string):
    match = citation_pattern.fullmatch(citation_string)
    assert match


@pytest.mark.parametrize("citation_string", [
    ('doi:10.5061/dryad.q447c/1'),
    ('@tag:abc123-'),
    ('@tag:abc123_'),
    ('@-tag:abc123'),
    ('@_tag:abc123'),
])
def test_citation_pattern_no_match(citation_string):
    match = citation_pattern.fullmatch(citation_string)
    assert match is None


@pytest.mark.parametrize("standard_citation,expected", [
    ('doi:10.5061/dryad.q447c/1', 'kQFQ8EaO'),
    ('arxiv:1407.3561v1', '16kozZ9Ys'),
    ('pmid:24159271', '11sli93ov'),
    ('url:http://blog.dhimmel.com/irreproducible-timestamps/', 'QBWMEuxW'),
])
def test_get_citation_id(standard_citation, expected):
    citation_id = get_citation_id(standard_citation)
    assert citation_id == expected


@pytest.mark.parametrize("citation,expected", [
    ('doi:10.5061/DRYAD.q447c/1', 'doi:10.5061/dryad.q447c/1'),
    ('doi:10.5061/dryad.q447c/1', 'doi:10.5061/dryad.q447c/1'),
    ('pmid:24159271', 'pmid:24159271'),
])
def test_standardize_citation(citation, expected):
    """
    Standardize idenfiers based on their source
    """
    output = standardize_citation(citation)
    assert output == expected


@pytest.mark.xfail(reason='https://twitter.com/dhimmel/status/950443969313419264')
def test_citation_to_citeproc_doi_datacite():
    citation = 'doi:10.7287/peerj.preprints.3100v1'
    citeproc = citation_to_citeproc(citation)
    assert citeproc['id'] == '11cb5HXoY'
    assert citeproc['URL'] == 'https://doi.org/10.7287/peerj.preprints.3100v1'
    assert citeproc['DOI'] == '10.7287/peerj.preprints.3100v1'
    assert citeproc['type'] == 'report'
    assert citeproc['title'] == 'Sci-Hub provides access to nearly all scholarly literature'
    authors = citeproc['author']
    assert authors[0]['family'] == 'Himmelstein'
    assert authors[-1]['family'] == 'Greene'


def test_citation_to_citeproc_arxiv():
    citation = 'arxiv:cond-mat/0703470v2'
    citeproc = citation_to_citeproc(citation)
    assert citeproc['id'] == 'ES92tcdg'
    assert citeproc['URL'] == 'https://arxiv.org/abs/cond-mat/0703470v2'
    assert citeproc['number'] == 'cond-mat/0703470v2'
    assert citeproc['version'] == '2'
    assert citeproc['type'] == 'report'
    assert citeproc['container-title'] == 'arXiv'
    assert citeproc['title'] == 'Portraits of Complex Networks'
    authors = citeproc['author']
    assert authors[0]['literal'] == 'J. P. Bagrow'
    assert citeproc['DOI'] == '10.1209/0295-5075/81/68004'


@pytest.mark.parametrize('identifier,citation_id', [
    ('PMC3041534', 'RoOhUFKU'),
    ('21347133', '4nofiYkF'),
])
def test_citation_to_citeproc_pmc(identifier, citation_id):
    citation = f'pmcid:{identifier}'
    citeproc = citation_to_citeproc(citation)
    assert citeproc['id'] == citation_id
    assert citeproc['URL'] == 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3041534/'
    assert citeproc['container-title'] == 'Summit on Translational Bioinformatics'
    assert citeproc['title'] == 'Secondary Use of EHR: Data Quality Issues and Informatics Opportunities'
    authors = citeproc['author']
    assert authors[0]['family'] == 'Botsis'
    assert citeproc['PMID'] == '21347133'
    assert citeproc['PMCID'] == 'PMC3041534'


def test_citation_to_citeproc_pubmed_1():
    """
    Generated from XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=21347133&rettype=full
    """
    citation = 'pmid:21347133'
    citeproc = citation_to_citeproc(citation)
    assert citeproc['id'] == 'y9ONtSZ9'
    assert citeproc['type'] == 'article-journal'
    assert citeproc['URL'] == 'https://www.ncbi.nlm.nih.gov/pubmed/21347133'
    assert citeproc['container-title'] == 'AMIA Joint Summits on Translational Science proceedings. AMIA Joint Summits on Translational Science'
    assert citeproc['title'] == 'Secondary Use of EHR: Data Quality Issues and Informatics Opportunities.'
    assert citeproc['issued']['date-parts'] == [[2010, 3, 1]]
    authors = citeproc['author']
    assert authors[0]['given'] == 'Taxiarchis'
    assert authors[0]['family'] == 'Botsis'
    assert citeproc['PMID'] == '21347133'
    assert citeproc['PMCID'] == 'PMC3041534'


def test_citation_to_citeproc_pubmed_2():
    """
    Generated from XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=27094199&rettype=full
    """
    citation = 'pmid:27094199'
    citeproc = citation_to_citeproc(citation)
    print(citeproc)
    assert citeproc['id'] == 'alaFV9OY'
    assert citeproc['type'] == 'article-journal'
    assert citeproc['URL'] == 'https://www.ncbi.nlm.nih.gov/pubmed/27094199'
    assert citeproc['container-title'] == 'Circulation. Cardiovascular genetics'
    assert citeproc['container-title-short'] == 'Circ Cardiovasc Genet'
    assert citeproc['page'] == '179-84'
    assert citeproc['title'] == 'Genetic Association-Guided Analysis of Gene Networks for the Study of Complex Traits.'
    assert citeproc['issued']['date-parts'] == [[2016, 4]]
    authors = citeproc['author']
    assert authors[0]['given'] == 'Casey S'
    assert authors[0]['family'] == 'Greene'
    assert citeproc['PMID'] == '27094199'
    assert citeproc['DOI'] == '10.1161/circgenetics.115.001181'


@pytest.mark.parametrize(('doi', 'pmid'), [
    ('10.1098/rsif.2017.0387', '29618526'),  # in PubMed and PMC
    ('10.1161/CIRCGENETICS.115.001181', '27094199'),  # in PubMed but not PMC
    ('10.7717/peerj-cs.134', None),  # DOI in journal not indexed by PubMed
    ('10.1161/CIRC', None),  # invalid DOI
])
def test_get_pmid_for_doi(doi, pmid):
    output = get_pmid_for_doi(doi)
    assert pmid == output


@pytest.mark.parametrize(('doi', 'id_dict'), [
    ('10.1098/rsif.2017.0387', {'PMCID': 'PMC5938574', 'PMID': '29618526'}),
    ('10.7554/ELIFE.32822', {'PMCID': 'PMC5832410', 'PMID': '29424689'}),
    ('10.1161/CIRCGENETICS.115.001181', {}),  # only in PubMed, not in PMC
    ('10.7717/peerj.000', {}),  # Non-existent DOI
    ('10.peerj.000', {}),  # malformed DOI
])
def test_get_pmcid_and_pmid_for_doi(doi, id_dict):
    output = get_pmcid_and_pmid_for_doi(doi)
    assert id_dict == output


@pytest.mark.parametrize(('doi', 'id_dict'), [
    ('10.1098/rsif.2017.0387', {'PMCID': 'PMC5938574', 'PMID': '29618526'}),
    ('10.7554/ELIFE.32822', {'PMCID': 'PMC5832410', 'PMID': '29424689'}),
    ('10.1161/CIRCGENETICS.115.001181', {'PMID': '27094199'}),  # only in PubMed, not in PMC
    ('10.7717/peerj.000', {}),  # Non-existent DOI
])
def test_get_pubmed_ids_for_doi(doi, id_dict):
    output = get_pubmed_ids_for_doi(doi)
    assert id_dict == output


def test_citation_to_citeproc_pubmed_book():
    """
    Extracting CSL metadata from books in PubMed is not supported.
    Logic not implemented to parse XML returned by
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=29227604&rettype=full
    """
    with pytest.raises(NotImplementedError):
        citation_to_citeproc('pmid:29227604')


def test_cite_command_empty():
    process = subprocess.run(
        ['manubot', 'cite'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(process.stderr)
    assert process.returncode == 2
    assert 'the following arguments are required: citations' in process.stderr


def test_cite_command_stdout():
    process = subprocess.run(
        ['manubot', 'cite', 'arxiv:1806.05726v1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(process.stderr)
    assert process.returncode == 0
    csl, = json.loads(process.stdout)
    assert csl['URL'] == 'https://arxiv.org/abs/1806.05726v1'


def test_cite_command_file(tmpdir):
    path = pathlib.Path(tmpdir) / 'csl-items.json'
    process = subprocess.run(
        ['manubot', 'cite', '--output', str(path), 'arxiv:1806.05726v1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(process.stderr.decode())
    assert process.returncode == 0
    with path.open() as read_file:
        csl, = json.load(read_file)
    assert csl['URL'] == 'https://arxiv.org/abs/1806.05726v1'


references_plain = '''\
1. Generalization of the Fermi Pseudopotential
Trang T. Le, Zach Osman, D. K. Watson, Martin Dunn, B. A. McKinney
arXiv (2018-06-14) https://arxiv.org/abs/1806.05726v1

2. Vagelos Report Summer 2017
Michael Zietz
Figshare (2017) https://doi.org/gdz6dd
DOI: 10.6084/m9.figshare.5346577.v1

3. Opportunities and obstacles for deep learning in biology and medicine.
Travers Ching, Daniel S Himmelstein, Brett K Beaulieu-Jones, Alexandr A Kalinin, Brian T Do, Gregory P Way, Enrico Ferrero, Paul-Michael Agapow, Michael Zietz, Michael M Hoffman, … Casey S Greene
Journal of the Royal Society, Interface (2018-04) https://www.ncbi.nlm.nih.gov/pubmed/29618526
DOI: 10.1098/rsif.2017.0387 · PMID: 29618526 · PMCID: PMC5938574
'''

references_markdown = '''\
1. **Generalization of the Fermi Pseudopotential**
Trang T. Le, Zach Osman, D. K. Watson, Martin Dunn, B. A. McKinney

*arXiv* (2018-06-14) <https://arxiv.org/abs/1806.05726v1>

2. **Vagelos Report Summer 2017**
Michael Zietz

*Figshare* (2017) <https://doi.org/gdz6dd>
DOI: [10.6084/m9.figshare.5346577.v1](https://doi.org/10.6084/m9.figshare.5346577.v1)

3. **Opportunities and obstacles for deep learning in biology and medicine.**
Travers Ching, Daniel S Himmelstein, Brett K Beaulieu-Jones, Alexandr A Kalinin, Brian T Do, Gregory P Way, Enrico Ferrero, Paul-Michael Agapow, Michael Zietz, Michael M Hoffman, … Casey S Greene

*Journal of the Royal Society, Interface* (2018-04) <https://www.ncbi.nlm.nih.gov/pubmed/29618526>
DOI: [10.1098/rsif.2017.0387](https://doi.org/10.1098/rsif.2017.0387) · PMID: [29618526](http://www.ncbi.nlm.nih.gov/pubmed/29618526) · PMCID: [PMC5938574](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC5938574)
'''

references_html = '''\
<div id="refs" class="references">
<div id="ref-s33GCagP">
<p>1. <strong>Generalization of the Fermi Pseudopotential</strong><br />
Trang T. Le, Zach Osman, D. K. Watson, Martin Dunn, B. A. McKinney<br />
<br />
<em>arXiv</em> (2018-06-14) <a href="https://arxiv.org/abs/1806.05726v1" class="uri">https://arxiv.org/abs/1806.05726v1</a></p>
</div>
<div id="ref-vbapKMop">
<p>2. <strong>Vagelos Report Summer 2017</strong><br />
Michael Zietz<br />
<br />
<em>Figshare</em> (2017) <a href="https://doi.org/gdz6dd" class="uri">https://doi.org/gdz6dd</a><br />
DOI: <a href="https://doi.org/10.6084/m9.figshare.5346577.v1">10.6084/m9.figshare.5346577.v1</a></p>
</div>
<div id="ref-HgEQEBcy">
<p>3. <strong>Opportunities and obstacles for deep learning in biology and medicine.</strong><br />
Travers Ching, Daniel S Himmelstein, Brett K Beaulieu-Jones, Alexandr A Kalinin, Brian T Do, Gregory P Way, Enrico Ferrero, Paul-Michael Agapow, Michael Zietz, Michael M Hoffman, … Casey S Greene<br />
<br />
<em>Journal of the Royal Society, Interface</em> (2018-04) <a href="https://www.ncbi.nlm.nih.gov/pubmed/29618526" class="uri">https://www.ncbi.nlm.nih.gov/pubmed/29618526</a><br />
DOI: <a href="https://doi.org/10.1098/rsif.2017.0387">10.1098/rsif.2017.0387</a> · PMID: <a href="http://www.ncbi.nlm.nih.gov/pubmed/29618526">29618526</a> · PMCID: <a href="http://www.ncbi.nlm.nih.gov/pmc/articles/PMC5938574">PMC5938574</a></p>
</div>
</div>
'''

references_jats = '''\
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.0 20120330//EN"
                  "JATS-journalpublishing1.dtd">
<article xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink" dtd-version="1.0" article-type="other">
<front>
<journal-meta>
<journal-title-group>
</journal-title-group>
<publisher>
<publisher-name></publisher-name>
</publisher>
</journal-meta>
<article-meta>
</article-meta>
</front>
<body>

</body>
<back>
<ref-list>
  <ref id="ref-1"><element-citation publication-type="report"><person-group person-group-type="author"><name><surname>Trang
  T. Le</surname></name>, <name><surname>Zach Osman</surname></name>,
  <name><surname>D. K. Watson</surname></name>, <name><surname>Martin
  Dunn</surname></name>, <name><surname>B. A.
  McKinney</surname></name></person-group><article-title>Generalization
  of the Fermi
  Pseudopotential</article-title><source>arXiv</source><publisher-name>arXiv</publisher-name><date><day>14</day><month>06</month><year>2018</year></date><ext-link ext-link-type="uri" xlink:href="https://arxiv.org/abs/1806.05726v1">https://arxiv.org/abs/1806.05726v1</ext-link></element-citation></ref>
  <ref id="ref-2"><element-citation publication-type="journal"><person-group person-group-type="author"><name><surname>Zietz</surname>,
  <given-names>Michael</given-names></name></person-group><article-title>Vagelos
  Report Summer
  2017</article-title><publisher-name>Figshare</publisher-name><date><year>2017</year></date><pub-id pub-id-type="doi"><ext-link ext-link-type="uri" xlink:href="https://doi.org/10.6084/m9.figshare.5346577.v1">10.6084/m9.figshare.5346577.v1</ext-link></pub-id><ext-link ext-link-type="uri" xlink:href="https://doi.org/gdz6dd">https://doi.org/gdz6dd</ext-link></element-citation></ref>
  <ref id="ref-3"><element-citation publication-type="journal"><person-group person-group-type="author"><name><surname>Ching</surname>,
  <given-names>Travers</given-names></name>,
  <name><surname>Himmelstein</surname>, <given-names>Daniel
  S</given-names></name>, <name><surname>Beaulieu-Jones</surname>,
  <given-names>Brett K</given-names></name>,
  <name><surname>Kalinin</surname>, <given-names>Alexandr
  A</given-names></name>, <name><surname>Do</surname>,
  <given-names>Brian T</given-names></name>,
  <name><surname>Way</surname>, <given-names>Gregory
  P</given-names></name>, <name><surname>Ferrero</surname>,
  <given-names>Enrico</given-names></name>,
  <name><surname>Agapow</surname>,
  <given-names>Paul-Michael</given-names></name>,
  <name><surname>Zietz</surname>,
  <given-names>Michael</given-names></name>,
  <name><surname>Hoffman</surname>, <given-names>Michael
  M</given-names></name>, <name><surname>Xie</surname>,
  <given-names>Wei</given-names></name>, <name><surname>Rosen</surname>,
  <given-names>Gail L</given-names></name>,
  <name><surname>Lengerich</surname>, <given-names>Benjamin
  J</given-names></name>, <name><surname>Israeli</surname>,
  <given-names>Johnny</given-names></name>,
  <name><surname>Lanchantin</surname>,
  <given-names>Jack</given-names></name>,
  <name><surname>Woloszynek</surname>,
  <given-names>Stephen</given-names></name>,
  <name><surname>Carpenter</surname>, <given-names>Anne
  E</given-names></name>, <name><surname>Shrikumar</surname>,
  <given-names>Avanti</given-names></name>, <name><surname>Xu</surname>,
  <given-names>Jinbo</given-names></name>,
  <name><surname>Cofer</surname>, <given-names>Evan
  M</given-names></name>, <name><surname>Lavender</surname>,
  <given-names>Christopher A</given-names></name>,
  <name><surname>Turaga</surname>, <given-names>Srinivas
  C</given-names></name>, <name><surname>Alexandari</surname>,
  <given-names>Amr M</given-names></name>, <name><surname>Lu</surname>,
  <given-names>Zhiyong</given-names></name>,
  <name><surname>Harris</surname>, <given-names>David
  J</given-names></name>, <name><surname>DeCaprio</surname>,
  <given-names>Dave</given-names></name>, <name><surname>Qi</surname>,
  <given-names>Yanjun</given-names></name>,
  <name><surname>Kundaje</surname>,
  <given-names>Anshul</given-names></name>,
  <name><surname>Peng</surname>,
  <given-names>Yifan</given-names></name>,
  <name><surname>Wiley</surname>, <given-names>Laura
  K</given-names></name>, <name><surname>Segler</surname>,
  <given-names>Marwin H S</given-names></name>,
  <name><surname>Boca</surname>, <given-names>Simina
  M</given-names></name>, <name><surname>Swamidass</surname>,
  <given-names>S Joshua</given-names></name>,
  <name><surname>Huang</surname>,
  <given-names>Austin</given-names></name>,
  <name><surname>Gitter</surname>,
  <given-names>Anthony</given-names></name>,
  <name><surname>Greene</surname>, <given-names>Casey
  S</given-names></name></person-group><article-title>Opportunities and
  obstacles for deep learning in biology and
  medicine.</article-title><source>J R Soc
  Interface</source><date><month>04</month><year>2018</year></date><volume>15</volume><issue>141</issue><pub-id pub-id-type="doi"><ext-link ext-link-type="uri" xlink:href="https://doi.org/10.1098/rsif.2017.0387">10.1098/rsif.2017.0387</ext-link></pub-id><ext-link ext-link-type="pmid" xlink:href="http://www.ncbi.nlm.nih.gov/pubmed/<ext-link ext-link-type="uri" xlink:href="http://www.ncbi.nlm.nih.gov/pubmed/29618526">29618526</ext-link>" xlink:type="simple"><ext-link ext-link-type="uri" xlink:href="http://www.ncbi.nlm.nih.gov/pubmed/29618526">29618526</ext-link></ext-link><ext-link ext-link-type="uri" xlink:href="https://www.ncbi.nlm.nih.gov/pubmed/29618526">https://www.ncbi.nlm.nih.gov/pubmed/29618526</ext-link></element-citation></ref>
</ref-list>
</back>
</article>
'''


@pytest.mark.parametrize(['args', 'expected'], [
    ([], references_plain),
    (['--format', 'plain'], references_plain),
    (['--format', 'markdown'], references_markdown),
    (['--format', 'html'], references_html),
    (['--format', 'jats'], references_jats),
], ids=['no-args', '--format=plain', '--format=markdown', '--format=html', '--format=jats'])
@pytest.mark.skipif(
    not shutil.which('pandoc'),
    reason='pandoc installation not found on system'
)
@pytest.mark.skipif(
    not shutil.which('pandoc-citeproc'),
    reason='pandoc-citeproc installation not found on system'
)
def test_cite_command_render_stdout(args, expected):
    """
    Note that this test may fail if the Pandoc version is not recent enough to
    support --lua-filter (introduced in pandoc 2.0) or URLs for --csl.
    """
    args = [
        'manubot', 'cite', '--render',
        '--csl', 'https://github.com/greenelab/manubot-rootstock/raw/e83e51dcd89256403bb787c3d9a46e4ee8d04a9e/build/assets/style.csl',
        'arxiv:1806.05726v1', 'doi:10.6084/m9.figshare.5346577.v1', 'pmid:29618526',
    ] + args
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(' '.join(process.args))
    print(process.stdout)
    print(process.stderr)
    assert process.stdout == expected
