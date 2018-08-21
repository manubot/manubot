"""
Manubot's command line interface
"""
import argparse
import logging
import sys
import warnings

import errorhandler

import manubot
from manubot.cite.cite_command import add_subparser_cite
from manubot.process import add_subparser_process


def parse_arguments():
    """
    Read and process command line arguments.
    """
    parser = argparse.ArgumentParser(description='Manubot: the manuscript bot for scholarly writing')
    parser.add_argument('--version', action='version', version=f'v{manubot.__version__}')
    subparsers = parser.add_subparsers(
        title='subcommands',
        description='All operations are done through subcommands:',
    )
    # Require specifying a sub-command
    subparsers.required = True  # https://bugs.python.org/issue26510
    subparsers.dest = 'subcommand'  # https://bugs.python.org/msg186387
    add_subparser_process(subparsers)
    add_subparser_cite(subparsers)
    for subparser in subparsers.choices.values():
        subparser.add_argument(
            '--log-level',
            default='WARNING',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Set the logging level for stderr logging',
        )
    args = parser.parse_args()
    return args


def main():
    """
    Called as a console_scripts entry point in setup.py. This function defines
    the manubot command line script.
    """
    # Track if message gets logged with severity of error or greater
    # See https://stackoverflow.com/a/45446664/4651668
    error_handler = errorhandler.ErrorHandler()

    # Log DeprecationWarnings
    warnings.simplefilter('always', DeprecationWarning)
    logging.captureWarnings(True)

    # Log to stderr
    logger = logging.getLogger()
    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setFormatter(logging.Formatter('## {levelname}\n{message}', style='{'))
    logger.addHandler(stream_handler)

    args = parse_arguments()
    logger.setLevel(getattr(logging, args.log_level))

    args.function(args)

    if error_handler.fired:
        logging.critical('Failure: exiting with code 1 due to logged errors')
        raise SystemExit(1)
