import manubot.util


def test_shlex_join():
    import pathlib
    args = [
        'command',
        'positional arg',
        'path_arg',
        pathlib.Path('path'),
    ]
    output = manubot.util.shlex_join(args)
    assert output == "command 'positional arg' path_arg path"
