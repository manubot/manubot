import importlib


def import_function(name):
    """
    Import a function in a module specified by name. For example, if name were
    'manubot.cite.cite_command.cli_cite', the cli_cite function would be
    returned as an object. See https://stackoverflow.com/a/8790232/4651668.
    """
    module_name, function_name = name.rsplit('.', 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)
