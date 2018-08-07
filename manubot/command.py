"""
Manubot's command line interface
"""
import argparse
import logging
import sys
import warnings

import errorhandler

import manubot
from manubot.cite import (
    cli_cite,
    configure_cite_argparser,
)
from manubot.process import (
    cli_process,
    configure_process_argparser,
)


def parse_arguments():
    """
    Read and process command line arguments.
    """
    parser = argparse.ArgumentParser(description='Manubot: the manuscript bot for scholarly writing')
    parser.add_argument('--version', action='version', version=f'v{manubot.__version__}')
    parser.add_argument('--log-level', default='WARNING',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level for stderr logging')
    subparsers = parser.add_subparsers(
        title='subcommands',
        description='All operations are done through subcommands:',
    )
    # Require specifying a sub-command
    subparsers.required = True  # https://bugs.python.org/issue26510
    subparsers.dest = 'subcommand'  # https://bugs.python.org/msg186387
    # manubot parse
    parser_process = subparsers.add_parser('process', help='process manuscript content')
    configure_process_argparser(parser_process)
    parser_process.set_defaults(function=cli_process)
    # manubot cite
    parser_cite = subparsers.add_parser('cite', help='citation to CSL command line utility')
    configure_cite_argparser(parser_cite)
    parser_cite.set_defaults(function=cli_cite)
    # Parse args
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
