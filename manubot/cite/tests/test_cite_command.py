import json
import pathlib
import shutil
import subprocess

import pytest

from manubot.cite.cite_command import (
    _get_pandoc_info,
)


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


@pytest.mark.parametrize(['args', 'expected'], [
    ([], 'references-plain.txt'),
    (['--format', 'plain'], 'references-plain.txt'),
    (['--format', 'markdown'], 'references-markdown.md'),
    (['--format', 'html'], 'references-html.html'),
    (['--format', 'jats'], 'references-jats.xml'),
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
    Test the stdout output of `manubot cite --render` with various formats.
    The output is sensitive to the version of Pandoc used, so rather than fail when
    the system's pandoc is outdated, the test is skipped. 
    """
    pandoc_version = _get_pandoc_info()['pandoc version']
    for output in 'markdown', 'html', 'jats':
        if output in args and pandoc_version < (2, 5):
            pytest.skip(f"Test {output} output assumes pandoc >= 2.5")
    if pandoc_version < (2, 0):
        pytest.skip("Test requires pandoc >= 2.0 to support --lua-filter and --csl=URL")
    expected = (
        pathlib.Path(__file__).parent
        .joinpath('cite-command-rendered', expected)
        .read_text()
    )
    args = [
        'manubot', 'cite', '--render',
        '--csl', 'https://github.com/greenelab/manubot-rootstock/raw/e83e51dcd89256403bb787c3d9a46e4ee8d04a9e/build/assets/style.csl',
        'arxiv:1806.05726v1', 'doi:10.7717/peerj.338', 'pmid:29618526',
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


def teardown_module(module):
    """
    Avoid too many requests to NCBI E-Utils in the test_pubmed.py,
    which is executed following this module. E-Utility requests are
    capped at 3 per second, which is usually controled by _get_eutils_rate_limiter,
    but this does not seem to work across test modules.
    """
    import time
    time.sleep(1)
