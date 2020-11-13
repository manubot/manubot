import pathlib
import shutil
import subprocess

import pytest

from manubot.pandoc.util import get_pandoc_info
from manubot.util import shlex_join

directory = pathlib.Path(__file__).parent


@pytest.mark.integration
@pytest.mark.pandoc_version_sensitive
@pytest.mark.skipif(
    not shutil.which("pandoc"), reason="pandoc installation not found on system"
)
@pytest.mark.skipif(
    not shutil.which("pandoc-citeproc"),
    reason="pandoc-citeproc installation not found on system",
)
def test_cite_pandoc_filter():
    """
    Test the stdout output of `manubot cite --render` with various formats.
    The output is sensitive to the version of Pandoc used, so rather than fail when
    the system's pandoc is outdated, the test is skipped.

    ```shell
    # Command to regenerate the expected output
    pandoc \
      --to=plain \
      --wrap=preserve \
      --csl=https://github.com/manubot/rootstock/raw/8b9b5ced2c7c963bf3ea5afb8f31f9a4a54ab697/build/assets/style.csl \
      --output=manubot/pandoc/tests/test_cite_filter/output.txt \
      --bibliography=manubot/pandoc/tests/test_cite_filter/bibliography.json \
      --bibliography=manubot/pandoc/tests/test_cite_filter/bibliography.bib \
      --filter=pandoc-manubot-cite \
      --filter=pandoc-citeproc \
      manubot/pandoc/tests/test_cite_filter/input.md

    # Command to generate Pandoc JSON input for pandoc-manubot-cite
    pandoc \
      --to=json \
      --wrap=preserve \
      --csl=https://github.com/manubot/rootstock/raw/8b9b5ced2c7c963bf3ea5afb8f31f9a4a54ab697/build/assets/style.csl \
      --output=manubot/pandoc/tests/test_cite_filter/filter-input.json \
      --bibliography=manubot/pandoc/tests/test_cite_filter/bibliography.json \
      --bibliography=manubot/pandoc/tests/test_cite_filter/bibliography.bib \
      manubot/pandoc/tests/test_cite_filter/input.md
    ```
    """
    data_dir = directory.joinpath("test_cite_filter")
    pandoc_version = get_pandoc_info()["pandoc version"]
    if pandoc_version < (1, 12):
        pytest.skip("Test requires pandoc >= 1.12 to support --filter")
    input_md = data_dir.joinpath("input.md").read_text(encoding="utf-8-sig")
    expected = data_dir.joinpath("output.txt").read_text(encoding="utf-8-sig")
    args = [
        "pandoc",
        "--wrap=preserve",
        "--csl=https://github.com/manubot/rootstock/raw/8b9b5ced2c7c963bf3ea5afb8f31f9a4a54ab697/build/assets/style.csl",
        "--bibliography",
        str(directory.joinpath("test_cite_filter", "bibliography.json")),
        "--bibliography",
        str(directory.joinpath("test_cite_filter", "bibliography.bib")),
        "--filter=pandoc-manubot-cite",
        "--filter=pandoc-citeproc",
        "--to=plain",
    ]
    process = subprocess.run(
        args,
        input=input_md,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    print(shlex_join(process.args))
    print(process.stdout)
    print(process.stderr)
    assert process.stdout.lower() == expected.lower()
