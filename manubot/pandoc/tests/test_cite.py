import pathlib
import shutil
import subprocess

import pytest

from manubot.pandoc.util import (
    get_pandoc_info,
)
from manubot.pandoc.cite import (
    csl_item_set_standard_citation,
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
    pandoc_version = get_pandoc_info()['pandoc version']
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
