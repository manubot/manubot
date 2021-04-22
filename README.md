# Python utilities for Manubot: Manuscripts, open and automated

[![documentation](https://img.shields.io/badge/-Documentation-purple?logo=read-the-docs&logoColor=white&style=for-the-badge)](https://manubot.github.io/manubot/)
[![PyPI](https://img.shields.io/pypi/v/manubot.svg?logo=PyPI&logoColor=white&style=for-the-badge)](https://pypi.org/project/manubot/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge&logo=Python&logoColor=white)](https://github.com/psf/black)

[![GitHub Actions CI Tests Status](https://img.shields.io/github/workflow/status/manubot/manubot/Tests?label=actions&logo=github&style=for-the-badge)](https://github.com/manubot/manubot/actions)
[![Travis Linux Build Status](https://img.shields.io/travis/com/manubot/manubot/main?style=for-the-badge&logo=travis&label=Travis)](https://travis-ci.com/manubot/manubot)
[![AppVeyor Windows Build Status](https://img.shields.io/appveyor/build/manubot/manubot/main?style=for-the-badge&logo=appveyor&logoColor=white&label=AppVeyor)](https://ci.appveyor.com/project/manubot/manubot/branch/main)


[Manubot](https://manubot.org/ "Manubot homepage") is a workflow and set of tools for the next generation of scholarly publishing.
This repository contains a Python package with several Manubot-related utilities, as described in the [usage section](#usage) below.
Package documentation is available at <https://manubot.github.io/manubot> (auto-generated from the Python source code).

The `manubot cite` command-line interface retrieves and formats bibliographic metadata for user-supplied persistent identifiers like DOIs or PubMed IDs.
The `manubot process` command-line interface prepares scholarly manuscripts for Pandoc consumption.
The `manubot process` command is used by Manubot manuscripts, which are based off the [Rootstock template](https://github.com/manubot/rootstock), to automate several aspects of manuscript generation.
See Rootstock's [manuscript usage guide](https://github.com/manubot/rootstock/blob/main/USAGE.md) for more information.

**Note:**
If you want to experience Manubot by editing an existing manuscript, see <https://github.com/manubot/try-manubot>.
If you want to create a new manuscript, see <https://github.com/manubot/rootstock>.

To cite the Manubot project or for more information on its design and history, see:

> **Open collaborative writing with Manubot**<br>
Daniel S. Himmelstein, Vincent Rubinetti, David R. Slochower, Dongbo Hu, Venkat S. Malladi, Casey S. Greene, Anthony Gitter<br>
*PLOS Computational Biology* (2019-06-24) <https://doi.org/c7np><br>
DOI: [10.1371/journal.pcbi.1007128](https://doi.org/10.1371/journal.pcbi.1007128) · PMID: [31233491](https://www.ncbi.nlm.nih.gov/pubmed/31233491) · PMCID: [PMC6611653](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6611653)

The Manubot version of this manuscript is available at <https://greenelab.github.io/meta-review/>.

## Installation

If you are using the `manubot` Python package as part of a manuscript repository, installation of this package is handled though the Rootstock's [environment specification](https://github.com/manubot/rootstock/blob/main/build/environment.yml).
For other use cases, this package can be installed via `pip`.

Install the latest release version [from PyPI](https://pypi.org/project/manubot/):

```sh
pip install --upgrade manubot
```

Or install from the source code on [GitHub](https://github.com/manubot/manubot), using the version specified by a commit hash:

```sh
COMMIT=d2160151e52750895571079a6e257beb6e0b1278
pip install --upgrade git+https://github.com/manubot/manubot@$COMMIT
```

The `--upgrade` argument ensures `pip` updates an existing `manubot` installation if present.

Some functions in this package require [Pandoc](https://pandoc.org/),
which must be [installed](https://pandoc.org/installing.html) separately on the system.
The pandoc-manubot-cite filter depends on Pandoc as well as panflute (a Python package).
Users must install a [compatible version of panflute](https://github.com/sergiocorreia/panflute#supported-pandoc-versions) based on their Pandoc version.
For example, on a system with Pandoc 2.9,
install the appropriate panflute like `pip install panflute==1.12.5`.

## Usage

Installing the python package creates the `manubot` command line program.
Here is the usage information as per `manubot --help`:

<!-- test codeblock contains output of `manubot --help` -->
```
usage: manubot [-h] [--version] {process,cite,webpage} ...

Manubot: the manuscript bot for scholarly writing

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

subcommands:
  All operations are done through subcommands:

  {process,cite,webpage}
    process             process manuscript content
    cite                citekey to CSL JSON command line utility
    webpage             deploy Manubot outputs to a webpage directory tree
```

Note that all operations are done through the following sub-commands.

### Process

The `manubot process` program is the primary interface to using Manubot.
There are two required arguments: `--content-directory` and `--output-directory`, which specify the respective paths to the content and output directories.
The content directory stores the manuscript source files.
Files generated by Manubot are saved to the output directory.

One common setup is to create a directory for a manuscript that contains both the `content` and `output` directory.
Under this setup, you can run the Manubot using:

```sh
manubot process \
  --skip-citations \
  --content-directory=content \
  --output-directory=output
```

See `manubot process --help` for documentation of all command line arguments:

<!-- test codeblock contains output of `manubot process --help` -->
```
usage: manubot process [-h] --content-directory CONTENT_DIRECTORY
                       --output-directory OUTPUT_DIRECTORY
                       [--template-variables-path TEMPLATE_VARIABLES_PATH]
                       --skip-citations [--cache-directory CACHE_DIRECTORY]
                       [--clear-requests-cache]
                       [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Process manuscript content to create outputs for Pandoc consumption. Performs
bibliographic processing and templating.

optional arguments:
  -h, --help            show this help message and exit
  --content-directory CONTENT_DIRECTORY
                        Directory where manuscript content files are located.
  --output-directory OUTPUT_DIRECTORY
                        Directory to output files generated by this script.
  --template-variables-path TEMPLATE_VARIABLES_PATH
                        Path or URL of a file containing template variables
                        for jinja2. Serialization format is inferred from the
                        file extension, with support for JSON, YAML, and TOML.
                        If the format cannot be detected, the parser assumes
                        JSON. Specify this argument multiple times to read
                        multiple files. Variables can be applied to a
                        namespace (i.e. stored under a dictionary key) like
                        `--template-variables-path=namespace=path_or_url`.
                        Namespaces must match the regex `[a-zA-
                        Z_][a-zA-Z0-9_]*`.
  --skip-citations      Skip citation and reference processing. Support for
                        citation and reference processing has been moved from
                        `manubot process` to the pandoc-manubot-cite filter.
                        Therefore this argument is now required. If citation-
                        tags.tsv is found in content, these tags will be
                        inserted in the markdown output using the reference-
                        link syntax for citekey aliases. Appends
                        content/manual-references*.* paths to Pandoc's
                        metadata.bibliography field.
  --cache-directory CACHE_DIRECTORY
                        Custom cache directory. If not specified, caches to
                        output-directory.
  --clear-requests-cache
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level for stderr logging
```

#### Manual references

Manubot has the ability to rely on user-provided reference metadata rather than generating it.
`manubot process` searches the content directory for files containing manually-provided reference metadata that match the glob `manual-references*.*`.
These files are stored in the Pandoc metadata `bibliography` field, such that they can be loaded by `pandoc-manubot-cite`.

### Cite

`manubot cite` is a command line utility to produce bibliographic metadata for citation keys.
The utility either outputs metadata as [CSL JSON items](http://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html#items) or produces formatted references if `--render`.

Citation keys should be in the format `prefix:accession`.
For example, the following example generates Markdown-formatted references for four persistent identifiers:

```shell
manubot cite --format=markdown \
  doi:10.1098/rsif.2017.0387 pubmed:29424689 pmc:PMC5640425 arxiv:1806.05726
```

The following [terminal recording](https://asciinema.org/a/205085?speed=2) demonstrates the main features of `manubot cite` (for a slightly outdated version):

![manubot cite demonstration](media/terminal-recordings/manubot-cite-cast.gif)

Additional usage information is available from `manubot cite --help`:

<!-- test codeblock contains output of `manubot cite --help` -->
```
usage: manubot cite [-h] [--output OUTPUT]
                    [--format {csljson,cslyaml,plain,markdown,docx,html,jats} | --yml | --txt | --md]
                    [--csl CSL] [--bibliography BIBLIOGRAPHY]
                    [--no-infer-prefix] [--allow-invalid-csl-data]
                    [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                    citekeys [citekeys ...]

Generate bibliographic metadata in CSL JSON format for one or more citation
keys. Optionally, render metadata into formatted references using Pandoc. Text
outputs are UTF-8 encoded.

positional arguments:
  citekeys              One or more (space separated) citation keys to
                        generate bibliographic metadata for.

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT       Specify a file to write output, otherwise default to
                        stdout.
  --format {csljson,cslyaml,plain,markdown,docx,html,jats}
                        Format to use for output file. csljson and cslyaml
                        output the CSL data. All other choices render the
                        references using Pandoc. If not specified, attempt to
                        infer this from the --output filename extension.
                        Otherwise, default to csljson.
  --yml                 Short for --format=cslyaml.
  --txt                 Short for --format=plain.
  --md                  Short for --format=markdown.
  --csl CSL             URL or path with CSL XML style used to style
                        references (i.e. Pandoc's --csl option). Defaults to
                        Manubot's style.
  --bibliography BIBLIOGRAPHY
                        File to read manual reference metadata. Specify
                        multiple times to load multiple files. Similar to
                        pandoc --bibliography.
  --no-infer-prefix     Do not attempt to infer the prefix for citekeys
                        without a known prefix.
  --allow-invalid-csl-data
                        Allow CSL Items that do not conform to the JSON
                        Schema. Skips CSL pruning.
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level for stderr logging
```

### Pandoc filter

This package creates the `pandoc-manubot-cite` Pandoc filter,
providing access to Manubot's cite-by-ID functionality from within a Pandoc workflow.

Options are set via Pandoc metadata fields [listed in the docs](https://manubot.github.io/manubot/reference/manubot/pandoc/cite_filter/).

<!-- test codeblock contains output of `pandoc-manubot-cite --help` -->
```
usage: pandoc-manubot-cite [-h] [--input [INPUT]] [--output [OUTPUT]]
                           target_format

Pandoc filter for citation by persistent identifier. Filters are command-line
programs that read and write a JSON-encoded abstract syntax tree for Pandoc.
Unless you are debugging, run this filter as part of a pandoc command by
specifying --filter=pandoc-manubot-cite.

positional arguments:
  target_format      output format of the pandoc command, as per Pandoc's --to
                     option

optional arguments:
  -h, --help         show this help message and exit
  --input [INPUT]    path read JSON input (defaults to stdin)
  --output [OUTPUT]  path to write JSON output (defaults to stdout)
```

Other Pandoc filters exist that do something similar:
[`pandoc-url2cite`](https://github.com/phiresky/pandoc-url2cite), [pandoc-url2cite-hs](https://github.com/Aver1y/pandoc-url2cite-hs), &
[`pwcite`](https://github.com/wikicite/wcite#filter-pwcite).
Currently, `pandoc-manubot-cite` supports the most types of persistent identifiers.
We're interested in creating as much compatibility as possible between these filters and their syntaxes.

#### Manual references

Manual references are loaded from the `references` and `bibliography` Pandoc metadata fields.
If a manual reference filename ends with `.json` or `.yaml`, it's assumed to contain CSL Data (i.e. Citation Style Language JSON).
Otherwise, the format is inferred from the extension and converted to CSL JSON using the `pandoc-citeproc --bib2json` [utility](https://github.com/jgm/pandoc-citeproc/blob/master/man/pandoc-citeproc.1.md#convert-mode).
The standard citation key for manual references is inferred from the CSL JSON `id` or `note` field.
When no prefix is provided, such as `doi:`, `url:`, or `raw:`, a `raw:` prefix is automatically added.
If multiple manual reference files load metadata for the same standard citation `id`, precedence is assigned according to descending filename order.

### Webpage

The `manubot webpage` command populates a `webpage` directory with Manubot output files.

<!-- test codeblock contains output of `manubot webpage --help` -->
```
usage: manubot webpage [-h] [--checkout [CHECKOUT]] [--version VERSION]
                       [--timestamp] [--no-ots-cache | --ots-cache OTS_CACHE]
                       [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Update the webpage directory tree with Manubot output files. This command
should be run from the root directory of a Manubot manuscript that follows the
Rootstock layout, containing `output` and `webpage` directories. HTML and PDF
outputs are copied to the webpage directory, which is structured as static
source files for website hosting.

optional arguments:
  -h, --help            show this help message and exit
  --checkout [CHECKOUT]
                        branch to checkout /v directory contents from. For
                        example, --checkout=upstream/gh-pages. --checkout is
                        equivalent to --checkout=gh-pages. If --checkout is
                        ommitted, no checkout is performed.
  --version VERSION     Used to create webpage/v/{version} directory.
                        Generally a commit hash, tag, or 'local'. When
                        omitted, version defaults to the commit hash on CI
                        builds and 'local' elsewhere.
  --timestamp           timestamp versioned manuscripts in webpage/v using
                        OpenTimestamps. Specify this flag to create timestamps
                        for the current HTML and PDF outputs and upgrade any
                        timestamps from past manuscript versions.
  --no-ots-cache        disable the timestamp cache.
  --ots-cache OTS_CACHE
                        location for the timestamp cache (default:
                        ci/cache/ots).
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level for stderr logging
```

## Development

### Environment

Create a development environment using:

```shell
conda create --name manubot-dev --channel conda-forge \
  python=3.8 pandoc=2.8
conda activate manubot-dev  # assumes conda >= 4.4
pip install --editable ".[webpage,dev]"
```

### Commands

Below are some common commands used for development.
They assume the working directory is set to the repository's root,
and the conda environment is activated.

```shell
# run the test suite
pytest

# install pre-commit git hooks (once per local clone).
# The pre-commit checks declared in .pre-commit-config.yaml will now
# run on changed files during git commits.
pre-commit install

# run the pre-commit checks (required to pass CI)
pre-commit run --all-files

# commit despite failing pre-commit checks (will fail CI)
git commit --no-verify

# regenerate the README codeblocks for --help messages
python manubot/tests/test_readme.py

# generate the docs
portray as_html --overwrite --output_dir=docs

# process the example testing manuscript
manubot process \
  --content-directory=manubot/process/tests/manuscripts/example/content \
  --output-directory=manubot/process/tests/manuscripts/example/output \
  --skip-citations \
  --log-level=INFO
```

### Release instructions

[![PyPI](https://img.shields.io/pypi/v/manubot.svg?logo=PyPI&style=for-the-badge)](https://pypi.org/project/manubot/)

This section is only relevant for project maintainers.
GitHub Actions [deploys](.github/workflows/release.yml) releases to [PyPI](https://pypi.org/project/manubot).

To create a new release, bump the `__version__` in [`manubot/__init__.py`](manubot/__init__.py).
Then, set the `TAG` and `OLD_TAG` environment variables:

```shell
TAG=v$(python setup.py --version)

# fetch tags from the upstream remote
# (assumes upstream is the manubot organization remote)
git fetch --tags upstream main

# get previous release tag, can hardcode like OLD_TAG=v0.3.1
OLD_TAG=$(git describe --tags --abbrev=0)
```

The following commands can help draft release notes:

```shell
# check out a branch for a pull request as needed
git checkout -b "release-$TAG"

# create release notes file if it doesn't exist
touch "release-notes/$TAG.md"

# commit list since previous tag
echo $'\n\nCommits\n-------\n' >> "release-notes/$TAG.md"
git log --oneline --decorate=no --reverse $OLD_TAG..HEAD >> "release-notes/$TAG.md"

# commit authors since previous tag
echo $'\n\nCode authors\n------------\n' >> "release-notes/$TAG.md"
git log $OLD_TAG..HEAD --format='%aN <%aE>' | sort --unique >> "release-notes/$TAG.md"
```

After a commit with the above updates is part of `upstream:main`,
for example after a PR is merged,
use the [GitHub interface](https://github.com/manubot/manubot/releases/new) to create a release with the new "Tag version".
Monitor [GitHub Actions](https://github.com/manubot/manubot/actions?query=workflow%3ARelease) and [PyPI](https://pypi.org/project/manubot/#history) for successful deployment of the release.

## Goals & Acknowledgments

Our goal is to create scholarly infrastructure that encourages open science and assists reproducibility.
Accordingly, we hope for the Manubot software and philosophy to be adopted widely, by both academic and commercial entities.
As such, Manubot is free/libre and open source software (see [`LICENSE.md`](LICENSE.md)).

We would like to thank the contributors and funders whose support makes this project possible.
Specifically, Manubot development has been financially supported by:

- the **Alfred P. Sloan Foundation** in [Grant G-2018-11163](https://sloan.org/grant-detail/8501) to [**@dhimmel**](https://github.com/dhimmel).
- the **Gordon & Betty Moore Foundation** ([**@DDD-Moore**](https://github.com/DDD-Moore)) in [Grant GBMF4552](https://www.moore.org/grant-detail?grantId=GBMF4552) to [**@cgreene**](https://github.com/cgreene).
