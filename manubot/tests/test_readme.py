import pathlib
import re
import shlex
import subprocess

import pytest

readme_path = pathlib.Path(__file__).parent.parent.parent / 'README.md'
readme = readme_path.read_text()

template = r'''
<!-- test codeblock contains output of `{command}` -->
```
{output}```
'''
pattern = template.format(
    command=r"(?P<command>.+?)",
    output=r"(?P<output>.+?)",
)
pattern = re.compile(pattern, re.DOTALL)
matches = list(pattern.finditer(readme))


@pytest.mark.parametrize(
    argnames=['command', 'expected'],
    argvalues=[match.groups() for match in matches],
    ids=[match.group('command') for match in matches],
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
    output = _get_output_from(command)
    assert output == expected


def _get_output_from(command):
    return subprocess.check_output(shlex.split(command), universal_newlines=True)


def _match_to_repl(match):
    template_dict = match.groupdict()
    template_dict['output'] = _get_output_from(template_dict['command'])
    return template.format(**template_dict)


if __name__ == '__main__':
    """
    Run `python tests/test_readme.py` to populate README codeblocks with
    output from the specified commands.
    """
    repl_readme = pattern.sub(repl=_match_to_repl, string=readme)
    readme_path.write_text(repl_readme)
