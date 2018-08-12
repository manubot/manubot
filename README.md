# The manuscript bot for automated scholarly publishing

[![Travis Linux Build Status](https://travis-ci.org/greenelab/manubot.svg?branch=master)](https://travis-ci.org/greenelab/manubot)
[![AppVeyor Windows Build Status](https://ci.appveyor.com/api/projects/status/u51tva6rmuk39xsc/branch/master?svg=true)](https://ci.appveyor.com/project/greenelab/manubot/branch/master)

The Manubot Python package prepares scholarly manuscripts for Pandoc consumption.
It automates and scripts several aspects of manuscript creation, including fetching bibliographic metadata for citations.

This program is designed to be used with clones of [Manubot Rootstock](https://github.com/greenelab/manubot-rootstock), which perform Pandoc conversion and continuous deployment.
See the Manubot Rootstock [usage guide](https://github.com/greenelab/manubot-rootstock/blob/master/USAGE.md) for more information.

## Usage

Installing the python package creates the `manubot` command line program.
Here is the usage information as per `manubot --help`:

```
usage: manubot [-h] [--version]
               [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
               {process,cite} ...

Manubot: the manuscript bot for scholarly writing

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level for stderr logging

subcommands:
  All operations are done through subcommands:

  {process,cite}
    process             process manuscript content
    cite                citation to CSL command line utility
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
  --content-directory=content \
  --output-directory=output
```

See `manubot process --help` for documentation of all command line arguments:

```
usage: manubot process [-h] --content-directory CONTENT_DIRECTORY
                       --output-directory OUTPUT_DIRECTORY
                       [--template-variables-path TEMPLATE_VARIABLES_PATH]
                       [--cache-directory CACHE_DIRECTORY]
                       [--clear-requests-cache]

Process manuscript content to create outputs for Pandoc consumption. Performs
bibliographic processing and templating.

optional arguments:
  -h, --help            show this help message and exit
  --content-directory CONTENT_DIRECTORY
                        directory where manuscript content files are located
  --output-directory OUTPUT_DIRECTORY
                        directory to output files generated by this script
  --template-variables-path TEMPLATE_VARIABLES_PATH
                        path or URL of a JSON file containing template
                        variables for jinja2. Specify this argument multiple
                        times to read multiple files. Variables can be applied
                        to a namespace (i.e. stored under a dictionary key)
                        like `--template-variables-
                        path=namespace=path_or_url`. Namespaces must match the
                        regex `[a-zA-Z_][a-zA-Z0-9_]*`.
  --cache-directory CACHE_DIRECTORY
                        Custom cache directory. If not specified, caches to
                        output-directory
  --clear-requests-cache
```

### Cite

`manubot cite` is a command line utility to create [CSL JSON items](http://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html#items) for one or more citations.
Citations should be in the format `source:identifier`.
For example, the following example generates CSL JSON for four references:

```sh
manubot cite doi:10.1098/rsif.2017.0387 pmid:29424689 pmcid:PMC5640425 arxiv:1806.05726
```

Additional usage information is available from `manubot cite --help`:

```
usage: manubot cite [-h] [--file FILE] [--bad-csl] citations [citations ...]

Retrieve bibliographic metadata for one or more citation identifiers.

positional arguments:
  citations    one or more (space separated) citations to produce CSL for

optional arguments:
  -h, --help   show this help message and exit
  --file FILE  specify a file to write CSL output, otherwise default to stdout
  --bad-csl    allow CSL Items that do not conform to the JSON Schema. Skips
               CSL pruning.
```

## Installation

Install the version specified by a git commit hash using:

```sh
COMMIT=33e512d21218263423de5f0d127aac4f8635468f
pip install git+https://github.com/greenelab/manubot@$COMMIT
```

Use the `--upgrade` argument to reinstall `manubot` with a different commit hash.

## Development

Create a development environment using:

```sh
conda create --name=manubot-dev python=3.6 jinja2 pandas pytest
conda activate manubot-dev  # assumes conda >= 4.4
pip install --editable .
```

Inside this environment, use `pytest` to run the test suite.
You can also use the `manubot` CLI to build manuscripts.
For example:

```sh
manubot process \
  --content-directory=tests/manuscripts/example/content \
  --output-directory=tests/manuscripts/example/output \
  --log-level=DEBUG
```

## Release instructions

[![PyPI](https://img.shields.io/pypi/v/manubot.svg)](https://pypi.org/project/manubot/)

This section is only relevant for project maintainers.
Travis CI deployments are used to upload releases to [PyPI](https://pypi.org/project/manubot).
To create a new release, bump the `__version__` in [`manubot/__init__.py`](manubot/__init__.py).
Then run the following commands:

```sh
TAG=v`python setup.py --version`
# Commit updated __version__ info
git add manubot/__init__.py
git commit --message="Set __version__ to $TAG"
git push
# Create & push tag (assuming upstream is greenelab remote)
git tag --annotate $TAG --message="Upgrade to $TAG"
git push upstream $TAG
```
