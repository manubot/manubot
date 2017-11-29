import pathlib
import subprocess

import pytest

from manubot.manubot import read_jsons

directory = pathlib.Path(__file__).parent.resolve()

# List of manuscripts for testing. All subdirectories of ./manuscripts
manuscripts = [path.name for path in
               directory.joinpath('manuscripts').iterdir() if path.is_dir()]


@pytest.mark.parametrize("manuscript", manuscripts)
def test_example_manuscript(manuscript):
    """
    Test command line execution of manubot to build an example manuscript.
    """
    manuscript_dir = directory.joinpath('manuscripts', manuscript)
    args = [
        'manubot',
        '--log-level', 'INFO',
        '--content-directory', manuscript_dir.joinpath('content'),
        '--output-directory', manuscript_dir.joinpath('output'),
    ]
    if manuscript == 'variables':
        args.extend([
            '--template-variables-path',
            manuscript_dir.joinpath('content/template-variables.json'),
        ])
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(process.args)
    print(process.stderr.decode())
    assert process.returncode == 0


def test_read_jsons():
    """
    Test reading multiple JSON files, from both local paths and URLs.
    """
    local_path = 'manuscripts/variables/content/template-variables.json'
    local_path = directory.joinpath(local_path)
    paths = [
        'https://git.io/vbkqm',
        'https://git.io/vbkqm',
        'namespace_1=https://git.io/vbkqm',
        'namespace_2=https://git.io/vbkqm',
        f'namespace_2={local_path}',
        f'namespace_3={local_path}',
    ]
    user_variables = read_jsons(paths)
    assert 'namespace_1' in user_variables
    assert 'namespace_2' in user_variables
    assert 'namespace_3' in user_variables
    assert user_variables['generated_by'] == 'Manubot'
    assert 'violet' in user_variables['namespace_1']['rainbow']
    assert 'yellow' in user_variables['namespace_2']['rainbow']
    assert 'orange' in user_variables['namespace_3']['rainbow']
