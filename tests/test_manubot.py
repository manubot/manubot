import pathlib
import subprocess

directory = pathlib.Path(__file__).parent.resolve()


def test_example_manuscript():
    """
    Test command line execution of manubot to build the example-manuscript.
    """
    manuscript_dir = directory.joinpath('example-manuscript')
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
