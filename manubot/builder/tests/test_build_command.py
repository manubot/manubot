import pathlib
import subprocess

from manubot.util import shlex_join


def test_example_manuscript():
    """
    Test command line execution of manubot to build an example manuscript.
    """
    directory = pathlib.Path("manubot/process/tests/manuscripts/example")
    args = [
        "manubot",
        "build",
        f"--directory=.",
        "--log-level=INFO",
    ]
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        cwd=directory,
    )
    print(shlex_join(process.args))
    print(process.stderr)
    html_path = directory.joinpath("output/manuscript.html")
    print(f"## Text of {html_path}:\n{html_path.read_text()}")
    assert process.returncode == 0
