import pathlib
import shutil
import subprocess

import pytest

from manubot.cite.cite_command import (
    _get_pandoc_info,
)
from manubot.pandoc.cite import (
    csl_item_set_standard_citation,
    load_bibliography,
)

directory = pathlib.Path(__file__).parent


@pytest.mark.skipif(
    not shutil.which('pandoc'),
    reason='pandoc installation not found on system'
)
@pytest.mark.skipif(
    not shutil.which('pandoc-citeproc'),
    reason='pandoc-citeproc installation not found on system'
)
def test_cite_pandoc_filter():
    """
    Test the stdout output of `manubot cite --render` with various formats.
    The output is sensitive to the version of Pandoc used, so rather than fail when
    the system's pandoc is outdated, the test is skipped.

    ```
    # Command to rebuild the expected output
    pandoc \
    --to=plain \
    --wrap=preserve \
    --csl=https://github.com/manubot/rootstock/raw/af1d47a0ec5f33d8fc99deab2ac23b697983b673/build/assets/style.csl \
    --output=manubot/pandoc/tests/output-with-cites.txt \
    --filter=pandoc-manubot-cite \
    --filter=pandoc-citeproc \
    manubot/pandoc/tests/input-with-cites.md
    ```
    """
    pandoc_version = _get_pandoc_info()['pandoc version']
    if pandoc_version < (1, 12):
        pytest.skip("Test requires pandoc >= 1.12 to support --filter")
    input_md = directory.joinpath('input-with-cites.md').read_text()
    expected = directory.joinpath('output-with-cites.txt').read_text()
    args = [
        'pandoc',
        '--wrap', 'preserve',
        '--csl', 'https://github.com/manubot/rootstock/raw/af1d47a0ec5f33d8fc99deab2ac23b697983b673/build/assets/style.csl',
        '--filter', 'pandoc-manubot-cite',
        '--filter', 'pandoc-citeproc',
        '--to', 'plain',
    ]
    process = subprocess.run(
        args,
        input=input_md,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(' '.join(process.args))
    print(process.stdout)
    print(process.stderr)
    assert process.stdout == expected


bibliography_paths = sorted(directory.glob('bibliographies/bibliography.*'))
bibliography_path_ids = [path.name for path in bibliography_paths]

@pytest.mark.parametrize('path', bibliography_paths, ids=bibliography_path_ids)
def test_load_bibliography_from_path(path):
    """
    Some of the bibliographies for this test were generated at
    https://zbib.org/c7f95cdef6d6409c92ffde24d519435d
    """
    path = directory / path
    csl_json = load_bibliography(path=path)
    assert len(csl_json) == 2
    assert csl_json[0]['title'] == 'Sci-Hub provides access to nearly all scholarly literature'


@pytest.mark.parametrize('path', bibliography_paths, ids=bibliography_path_ids)
def test_load_bibliography_from_text(path):
    """
    https://zbib.org/c7f95cdef6d6409c92ffde24d519435d
    """
    text = directory.joinpath(path).read_text()
    input_format = path.suffix[1:]
    csl_json = load_bibliography(text=text, input_format=input_format)
    assert len(csl_json) == 2
    assert csl_json[0]['title'] == 'Sci-Hub provides access to nearly all scholarly literature'
    if input_format in {'json', 'bib'}:
        assert csl_json[0].get('id') == 'doi:10.7554/elife.32822'
