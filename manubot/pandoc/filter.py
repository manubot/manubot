"""
Utilities for pandoc filters
"""
import argparse
import logging

import panflute as pf


def parse_args(description=None):
    """
    Read command line arguments
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "target_format",
        help="output format of the pandoc command, as per Pandoc's --to option",
    )
    parser.add_argument(
        "--input",
        nargs="?",
        type=argparse.FileType("r", encoding="utf-8"),
        help="path read JSON input (defaults to stdin)",
    )
    parser.add_argument(
        "--output",
        nargs="?",
        type=argparse.FileType("w", encoding="utf-8"),
        help="path to write JSON output (defaults to stdout)",
    )
    args = parser.parse_args()
    return args


def filter_main(processor, description=""):
    from .filter import parse_args
    from manubot.command import setup_logging_and_errors, exit_if_error_handler_fired

    diagnostics = setup_logging_and_errors()
    description += (
        "Filters are command-line programs that read and write a JSON-encoded abstract syntax tree for Pandoc. "
        "Unless you are debugging, run this filter as part of a pandoc command by specifying --filter=pandoc-manubot-cite."
    )
    args = parse_args(description=description)
    # Let panflute handle io to sys.stdout / sys.stdin to set utf-8 encoding.
    # args.input=None for stdin, args.output=None for stdout
    doc = pf.load(input_stream=args.input)
    log_level = doc.get_metadata("manubot-log-level", "WARNING")
    diagnostics["logger"].setLevel(getattr(logging, log_level))
    processor(doc, args)
    pf.dump(doc, output_stream=args.output)
    if doc.get_metadata("manubot-fail-on-errors", False):
        exit_if_error_handler_fired(diagnostics["error_handler"])
