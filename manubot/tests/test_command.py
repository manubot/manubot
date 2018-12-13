import subprocess

import manubot


def test_version():
    stdout = subprocess.check_output(
        ['manubot', '--version'],
        universal_newlines=True,
    )
    version_str = f'v{manubot.__version__}'
    assert version_str == stdout.rstrip()


def test_missing_subcommand():
    process = subprocess.run(
        ['manubot'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(process.stderr)
    assert process.returncode == 2
    assert 'error: the following arguments are required: subcommand' in process.stderr
