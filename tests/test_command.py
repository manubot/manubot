import subprocess


def test_command_without_subcommand():
    process = subprocess.run(
        ['manubot'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stderr = process.stderr.decode()
    print(stderr)
    assert process.returncode == 2
    assert 'error: the following arguments are required: command' in stderr
