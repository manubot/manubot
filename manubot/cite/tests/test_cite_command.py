import json
import pathlib
import shutil
import subprocess

import pytest

from manubot.util import shlex_join
from manubot.pandoc.util import get_pandoc_version


def test_cite_command_empty():
    process = subprocess.run(
        ["manubot", "cite"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(process.stderr)
    assert process.returncode == 2
    assert "the following arguments are required: citekeys" in process.stderr


def test_cite_command_stdout():
    process = subprocess.run(
        ["manubot", "cite", "arxiv:1806.05726v1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(process.stderr)
    assert process.returncode == 0
    (csl,) = json.loads(process.stdout)
    assert csl["URL"] == "https://arxiv.org/abs/1806.05726v1"


def test_cite_command_file(tmpdir):
    path = pathlib.Path(tmpdir) / "csl-items.json"
    process = subprocess.run(
        ["manubot", "cite", "--output", str(path), "arxiv:1806.05726v1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(process.stderr.decode())
    assert process.returncode == 0
    with path.open() as read_file:
        (csl,) = json.load(read_file)
    assert csl["URL"] == "https://arxiv.org/abs/1806.05726v1"


pandoc_version = get_pandoc_version()


@pytest.mark.skipif(
    not shutil.which("pandoc"), reason="pandoc installation not found on system"
)
@pytest.mark.skipif(
    not shutil.which("pandoc-citeproc"),
    reason="pandoc-citeproc installation not found on system",
)
class Base_cite_command_render_stdout:
    """
    Expecting reference values for test to be at files on path:
    cite-command-rendered/references-{format}-{pandoc_stamp}.{extension}

    Examples:
    - references-html-2.7.2.html
    - references-plain-2.7.2.txt
    - references-jats-2.7.2.xml
    - references-jats-2.7.3.xml
    - references-markdown-2.7.2.md

    2.7.2 was the current pandoc version on CI builds for these builds,
    but a newer version 2.7.3 was available too and giving a different output
    for xml (jats) output.

    Filenames must be adjusted accodingly when current pandoc version changes.

    Run tests locally skipping this test suit (makes sense if your local pandoc
    version is different from pandoc version used by Travis and Appveyor):

        pytest -v -m "not pandoc_version_sensitive"

    See .travis.yml and .appveyor.yml to find out current pandoc version used
    for testing.
    """

    pandoc_stamp = ".".join(map(str, pandoc_version))

    @classmethod
    def expected_output(cls, format, extension):
        return (
            pathlib.Path(__file__)
            .parent.joinpath("cite-command-rendered")
            .joinpath(f"references-{format}-{cls.pandoc_stamp}.{extension}")
            .read_text()
        )

    @staticmethod
    def render(format_args):
        args = [
            "manubot",
            "cite",
            "--render",
            "--csl",
            "https://github.com/greenelab/manubot-rootstock/raw/e83e51dcd89256403bb787c3d9a46e4ee8d04a9e/build/assets/style.csl",
            "arxiv:1806.05726v1",
            "doi:10.7717/peerj.338",
            "pmid:29618526",
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


@pytest.mark.pandoc_version_sensitive
@pytest.mark.skipif(
    pandoc_version < (2, 0),
    reason="Test requires pandoc >= 2.0 to support --lua-filter and --csl=URL",
)
class Test_cite_command_render_stdout_above_pandoc_v2(Base_cite_command_render_stdout):
    def test_no_arg(self):
        assert self.render([]) == self.expected_output("plain", "txt")

    def test_plain(self):
        assert self.render(["--format", "plain"]) == self.expected_output(
            "plain", "txt"
        )


@pytest.mark.pandoc_version_sensitive
@pytest.mark.skipif(
    pandoc_version < (2, 5),
    reason=("Testing markdown, html or jats formats assumes pandoc >= 2.5"),
)
class Test_cite_command_render_stdout_above_pandoc_v2_5(
    Base_cite_command_render_stdout
):
    def test_markdown(self):
        assert self.render(["--format", "markdown"]) == self.expected_output(
            "markdown", "md"
        )

    def test_html(self):
        assert self.render(["--format", "html"]) == self.expected_output("html", "html")

    def test_jats(self):
        assert self.render(["--format", "jats"]) == self.expected_output("jats", "xml")


def teardown_module(module):
    """
    Avoid too many requests to NCBI E-Utils in the test_pubmed.py,
    which is executed following this module. E-Utility requests are
    capped at 3 per second, which is usually controled by _get_eutils_rate_limiter,
    but this does not seem to work across test modules.
    """
    import time

    time.sleep(1)
