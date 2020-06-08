import pathlib
import subprocess

import pytest

from manubot.util import shlex_join

directory = pathlib.Path(__file__).parent.resolve()

# List of manuscripts for testing. All subdirectories of ./manuscripts
manuscripts = [
    path.name for path in directory.joinpath("manuscripts").iterdir() if path.is_dir()
]


@pytest.mark.integration
@pytest.mark.parametrize("manuscript", manuscripts)
def test_example_manuscript(manuscript):
    """
    Test command line execution of manubot to build an example manuscript.
    """
    manuscript_dir = directory.joinpath("manuscripts", manuscript)
    args = [
        "manubot",
        "process",
        "--log-level",
        "INFO",
        "--skip-citations",
        "--content-directory",
        str(manuscript_dir.joinpath("content")),
        "--output-directory",
        str(manuscript_dir.joinpath("output")),
    ]
    if manuscript == "variables":
        args.extend(
            [
                "--template-variables-path",
                str(manuscript_dir.joinpath("content/template-variables.json")),
            ]
        )
    process = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8"
    )
    print(shlex_join(process.args))
    print(process.stderr)
    assert process.returncode == 0
