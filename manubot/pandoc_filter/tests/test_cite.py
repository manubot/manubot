import pathlib
import shutil
import subprocess

import pytest

from manubot.cite.cite_command import (
    _get_pandoc_info,
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
    """
    pandoc_version = _get_pandoc_info()['pandoc version']
    if pandoc_version < (1, 12):
        pytest.skip("Test requires pandoc >= 1.12 to support --filter")
    input_md = directory.joinpath('input-with-cites.md').read_text()
    expected = directory.joinpath('output-with-cites.md').read_text()
    args = [
        'pandoc',
        '--filter', 'pandoc-manubot-cite',
        '--to', 'markdown',
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
