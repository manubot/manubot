import importlib
import platform
import sys

# Email address that forwards to Manubot maintainers
contact_email = 'contact@manubot.org'


def import_function(name):
    """
    Import a function in a module specified by name. For example, if name were
    'manubot.cite.cite_command.cli_cite', the cli_cite function would be
    returned as an object. See https://stackoverflow.com/a/8790232/4651668.
    """
    module_name, function_name = name.rsplit('.', 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def get_manubot_user_agent():
    """
    Return a User-Agent string for web request headers to help services
    identify requests as coming from Manubot.
    """
    try:
        from manubot import __version__ as manubot_version
    except ImportError:
        manubot_version = ''
    return (
        f'manubot/{manubot_version} '
        f'({platform.system()}; Python/{sys.version_info.major}.{sys.version_info.minor}) '
        f'<{contact_email}>'
    )
