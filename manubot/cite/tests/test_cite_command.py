import json
import pathlib
import shutil
import subprocess

import pytest

from manubot.util import shlex_join
from manubot.pandoc.util import (
    get_pandoc_version,
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
    assert 'the following arguments are required: citekeys' in process.stderr


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


pandoc_version = get_pandoc_version()


@pytest.mark.skipif(
    not shutil.which('pandoc'),
    reason='pandoc installation not found on system'
)
@pytest.mark.skipif(
    not shutil.which('pandoc-citeproc'),
    reason='pandoc-citeproc installation not found on system'
)
class Base_cite_command_render_stdout():
    @classmethod
    def expected_output(cls, filename):
        return (
            pathlib.Path(__file__).parent
            .joinpath('cite-command-rendered', filename)
            # We need to enforce that files are read with 
            # encoding='utf-8-sig', otherwise ther maybe fasle test failures.
            # File reader can be helper function in conftest.py
            .read_text(encoding='utf-8-sig')
        )

    @classmethod
    def render(self, format_args):
        args = [
            'manubot',
            'cite',
            '--render',
            '--csl',
            'https://github.com/greenelab/manubot-rootstock/raw/e83e51dcd89256403bb787c3d9a46e4ee8d04a9e/build/assets/style.csl',
            'arxiv:1806.05726v1',
            'doi:10.7717/peerj.338',
            'pmid:29618526',
        ] + format_args
        process = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        print(shlex_join(process.args))
        print(process.stdout)
        print(process.stderr)
        return process.stdout


@pytest.mark.skipif(
    pandoc_version < (2, 0),
    reason="Test requires pandoc >= 2.0 to support --lua-filter and --csl=URL")
class Test_cite_command_render_stdout_above_pandoc_v2(
        Base_cite_command_render_stdout):
    def test_no_arg(self):
        assert self.render([]) == \
            self.expected_output('references-plain.txt')

    def test_plain(self):
        assert self.render(['--format', 'plain']) == \
            self.expected_output('references-plain.txt')


@pytest.mark.skipif(
    pandoc_version < (2, 5),
    reason=("Testing markdown, html or jats formats "
            "assumes pandoc >= 2.5")
)
class Test_cite_command_render_stdout_above_pandoc_v2_5(
        Base_cite_command_render_stdout):
    def test_markdown(self):
        assert self.render(['--format', 'markdown']) == \
            self.expected_output('references-markdown.md')

    def test_html(self):
        assert self.render(['--format', 'html']) == \
            self.expected_output('references-html.html')

    def test_jats(self):
        if pandoc_version >= (2, 7, 3):
            filename = 'references-jats-2.7.3.xml'
        else:
            filename = 'references-jats.xml'
        assert self.render(['--format', 'jats']) == \
            self.expected_output(filename)


def teardown_module(module):
    """
    Avoid too many requests to NCBI E-Utils in the test_pubmed.py,
    which is executed following this module. E-Utility requests are
    capped at 3 per second, which is usually controled by _get_eutils_rate_limiter,
    but this does not seem to work across test modules.
    """
    import time
    time.sleep(1)
