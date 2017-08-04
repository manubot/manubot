import pathlib
import subprocess

import pytest

directory = pathlib.Path(__file__).parent.resolve()


@pytest.mark.parametrize("manuscript_directory", [
    ('example-manuscript'),
    ('example-manuscript-empty'),
])
def test_example_manuscript(manuscript_directory):
    """
    Test command line execution of manubot to build an example manuscript.
    """
    manuscript_dir = directory.joinpath(manuscript_directory)
    args = [
        'manubot',
        '--log-level', 'INFO',
        '--content-directory', manuscript_dir.joinpath('content'),
        '--output-directory', manuscript_dir.joinpath('output'),
    ]
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(process.args)
    print(process.stderr.decode())
    assert process.returncode == 0
