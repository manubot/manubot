import json
import pathlib
import shutil
import subprocess

import pytest

from manubot.cite.csl_item import CSL_Item
from manubot.util import shlex_join
from manubot.pandoc.util import get_pandoc_version

data_dir = pathlib.Path(__file__).parent.joinpath("cite-command-rendered")


def test_cite_command_preserves_order():
    """
    https://github.com/manubot/manubot/issues/240
    """
    citekeys = [
        "pmid:29618526",
        "doi:10.7717/peerj.338",
        "arxiv:1806.05726v1",
        "pubmed:29618526",
        "DOI:10.7717/PEERJ.338",
    ]
    args = [
        "manubot",
        "cite",
        "--bibliography=input-bibliography.json",
        *citekeys,
    ]
    output = subprocess.check_output(
        args,
        encoding="utf-8",
        cwd=data_dir,
    )
    csl_items = json.loads(output)
    csl_items = [CSL_Item(x) for x in csl_items]
    standard_ids = [csl_item.note_dict.get("standard_id") for csl_item in csl_items]
    assert standard_ids == [
        "pubmed:29618526",
        "doi:10.7717/peerj.338",
        "arxiv:1806.05726v1",
    ]


def test_cite_command_empty():
    process = subprocess.run(
        ["manubot", "cite"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    print(process.stderr)
    assert process.returncode == 2
    assert "the following arguments are required: citekeys" in process.stderr


def test_cite_command_stdout():
    process = subprocess.run(
        ["manubot", "cite", "arxiv:1806.05726v1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
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


@pytest.mark.integration
@pytest.mark.parametrize(
    ["args", "filename"],
    [
        pytest.param([], "references-plain-{}.txt", id="no-args"),
        pytest.param(
            ["--format", "plain"], "references-plain-{}.txt", id="--format=plain"
        ),
        pytest.param(
            ["--format", "markdown"],
            "references-markdown-{}.md",
            id="--format=markdown",
        ),
        pytest.param(
            ["--format", "html"], "references-html-{}.html", id="--format=html"
        ),
        pytest.param(
            ["--format", "jats"], "references-jats-{}.xml", id="--format=jats"
        ),
    ],
)
@pytest.mark.skipif(
    not shutil.which("pandoc"), reason="pandoc installation not found on system"
)
@pytest.mark.pandoc_version_sensitive
def test_cite_command_render_stdout(args, filename):
    """
    Test the stdout output of `manubot cite --render` with various formats.
    The output is sensitive to the version of Pandoc used, so expected output
    files include the pandoc version stamp in their filename.
    When the expected version is missing, the test fails but writes the
    command output to that file. Therefore, subsequent runs of the same test
    will pass. Before committing the auto-generated output, do look to ensure
    its integrity.

    This test uses --bibliography to avoid slow network calls.
    Regenerate the CSL JSON using:

    ```shell
    manubot cite \
      --output=manubot/cite/tests/cite-command-rendered/input-bibliography.json \
      arxiv:1806.05726v1 doi:10.7717/peerj.338 pmid:29618526
    ```
    """
    # get pandoc version info
    pandoc_version = get_pandoc_version()
    pandoc_stamp = ".".join(map(str, pandoc_version))
    path = data_dir.joinpath(filename.format(pandoc_stamp))

    # skip test on old pandoc versions
    for output in "markdown", "html", "jats":
        if output in args and pandoc_version < (2, 5):
            pytest.skip(f"Test {output} output assumes pandoc >= 2.5")
    if pandoc_version < (2, 0):
        pytest.skip("Test requires pandoc >= 2.0 to support --lua-filter and --csl=URL")

    args = [
        "manubot",
        "cite",
        "--bibliography=input-bibliography.json",
        "--render",
        "--csl=https://github.com/greenelab/manubot-rootstock/raw/e83e51dcd89256403bb787c3d9a46e4ee8d04a9e/build/assets/style.csl",
        "arxiv:1806.05726v1",
        "doi:10.7717/peerj.338",
        "pmid:29618526",
    ] + args
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        cwd=data_dir,
    )
    print(shlex_join(process.args))
    print(process.stderr)
    assert process.returncode == 0
    print(process.stdout)
    if not path.exists():
        # https://github.com/manubot/manubot/pull/146#discussion_r333132261
        print(
            f"Missing expected output at {path}\n"
            "Writing output to file such that future tests will pass."
        )
        path.write_text(process.stdout, encoding="utf-8")
        assert False
    expected = path.read_text(encoding="utf-8-sig")
    assert process.stdout == expected


def test_cite_command_bibliography():
    bib_dir = pathlib.Path(__file__).parent.parent.parent.joinpath(
        "pandoc/tests/bibliographies"
    )
    args = [
        "manubot",
        "cite",
        "--bibliography=bibliography.json",
        "DOI:10.7554/elife.32822",
    ]
    csl_json = subprocess.check_output(args, encoding="utf-8", cwd=bib_dir)
    csl_items = json.loads(csl_json)
    assert len(csl_items) == 1
    csl_item = csl_items[0]
    assert "manual_reference_filename: bibliography.json" in csl_item["note"]


def teardown_module(module):
    """
    Avoid too many requests to NCBI E-Utils in the test_pubmed.py,
    which is executed following this module. E-Utility requests are
    capped at 3 per second, which is usually controled by _get_eutils_rate_limiter,
    but this does not seem to work across test modules.
    """
    import time

    time.sleep(1)
