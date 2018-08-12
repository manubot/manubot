import pathlib
import re
import subprocess

import pytest

readme_path = pathlib.Path(__file__).parent.parent / 'README.md'
readme = readme_path.read_text()

pattern = r'''\
<!-- test codeblock contains output of `(?P<command>.+?)` -->
```
(?P<output>.+?)
```
'''
pattern = re.compile(pattern, re.DOTALL)
matches = list(pattern.finditer(readme))
matches


@pytest.mark.parametrize(
    ['command', 'expected'],
    [match.groups() for match in matches],
)
def test_readme_codeblock_contains_output_from(command, expected):
    """
    If this test fails, ensure that codeblocks in README.md have the correct
    output. To enable this check for output in a codeblock, use the following
    construct:

    <!-- test codeblock contains output of `{command}` -->
    ```
    {expected}
    ```
    """
    output = subprocess.check_output(command, shell=True)
    output = output.decode().rstrip()
    assert output == expected
