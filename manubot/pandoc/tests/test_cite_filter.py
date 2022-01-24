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
      --output=manubot/pandoc/tests/test_cite_filter/output.txt \
      --filter=pandoc-manubot-cite \
      --citeproc \
      manubot/pandoc/tests/test_cite_filter/input.md

    # Command to generate Pandoc JSON input for pandoc-manubot-cite
    pandoc \
      --to=json \
      --wrap=preserve \
      --output=manubot/pandoc/tests/test_cite_filter/filter-input.json \
      manubot/pandoc/tests/test_cite_filter/input.md
    ```
    """
    data_dir = directory.joinpath("test_cite_filter")
    pandoc_version = get_pandoc_info()["pandoc version"]
    if pandoc_version < (2, 11):
        pytest.skip("Test requires pandoc >= 2.11 to support --citeproc")
    input_md = data_dir.joinpath("input.md").read_text(encoding="utf-8-sig")
    expected = data_dir.joinpath("output.txt").read_text(encoding="utf-8-sig")
    args = [
        "pandoc",
        "--wrap=preserve",
        "--filter=pandoc-manubot-cite",
        "--citeproc",
        "--to=plain",
    ]
    process = subprocess.run(
        args,
        input=input_md,
        capture_output=True,
        encoding="utf-8",
    )
    print(shlex_join(process.args))
    print(process.stdout)
    print(process.stderr)
    assert process.stdout.lower() == expected.lower()
