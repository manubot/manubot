import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

from manubot.pandoc.util import get_pandoc_info
from manubot.util import shlex_join


def load_bibliography(
    path: Optional[str] = None,
    text: Optional[str] = None,
    input_format: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convert a bibliography to CSL JSON using either `pandoc-citeproc --bib2json`
    or `pandoc --to=csljson`, depending on availability of pandoc commands on the system.
    Accepts either a bibliography path or text (string). If supplying text,
    pandoc-citeproc will likely require input_format be specified.
    The CSL JSON is returned as Python objects.
    If loading fails, log an error and return an empty list.

    Parameters
    ----------
    path : str, pathlike, or None
        Path to a bibliography file. Extension is used by pandoc-citeproc to infer the
        format of the input.
    text : str or None
        Text representation of the bibliography, such as a JSON-formatted string.
        `input_format` should be specified if providing text input.
    input_format : str or None
        Manually specified input formatted that is supported by pandoc-citeproc:
        https://github.com/jgm/pandoc-citeproc/blob/master/man/pandoc-citeproc.1.md#options
        Use 'bib' for BibLaTeX. Use 'json' for CSL JSON.

    Returns
    -------
    csl_json : JSON-like object
        CSL JSON Data for the references encoded by the input bibliography.
    """
    use_text = path is None
    use_path = text is None
    if use_path:
        path = os.fspath(path)
    if not (use_text ^ use_path):
        raise ValueError("load_bibliography: specify either path or text but not both.")
    pdoc_info = get_pandoc_info()
    if pdoc_info["pandoc-citeproc"]:
        return _load_bibliography_pandoc_citeproc(path, text, input_format)
    if input_format == "bib" or (use_path and path.endswith(".bib")):
        return _load_bibliography_pandoc(path, text)
    logging.error(
        "pandoc-citeproc not found on system, but is required to convert any format besides 'bib': "
        "manubot.pandoc.bibliography.load_bibliography returning empty CSL JSON"
    )
    return []


def _load_bibliography_pandoc_citeproc(
    path: Optional[str] = None,
    text: Optional[str] = None,
    input_format: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convert a bibliography to CSL JSON using `pandoc-citeproc --bib2json`.
    Accepts either a bibliography path or text (string). If supplying text,
    pandoc-citeproc will likely require input_format be specified.
    The CSL JSON is returned as Python objects.
    If loading fails, log an error and return an empty list.

    Parameters
    ----------
    path : str, pathlike, or None
        Path to a bibliography file. Extension is used by pandoc-citeproc to infer the
        format of the input.
    text : str or None
        Text representation of the bibliography, such as a JSON-formatted string.
        `input_format` should be specified if providing text input.
    input_format : str or None
        Manually specified input formatted that is supported by pandoc-citeproc:
        https://github.com/jgm/pandoc-citeproc/blob/master/man/pandoc-citeproc.1.md#options

    Returns
    -------
    csl_json : JSON-like object
        CSL JSON Data for the references encoded by the input bibliography.
    """
    command_args = ["pandoc-citeproc", "--bib2json"]
    if input_format:
        command_args.extend(["--format", input_format])
    return _pandoc_system_call(command_args, path, text)


def _load_bibliography_pandoc(
    path: Optional[str] = None,
    text: Optional[str] = None,
) -> List[Dict[str, Any]]:

    """
    Convert a biblatex (.bib) bibliography to CSL JSON data using pandoc directly.
    Pandoc support for csljson output requires pandoc >= 2.11.
    """
    pdoc_info = get_pandoc_info()
    if not pdoc_info["pandoc"]:
        logging.error(
            "pandoc not found on system: "
            "manubot.pandoc.bibliography.load_bibliography returning empty CSL JSON"
        )
        return []
    if pdoc_info["pandoc version"] < (2, 11):
        logging.error(
            "pandoc >= version 2.11 required for biblatex to csljson conversion. "
            "manubot.pandoc.bibliography.load_bibliography returning empty CSL JSON"
        )
        return []
    command_args = "pandoc --from=biblatex --to=csljson".split()
    return _pandoc_system_call(command_args, path, text)


def _pandoc_system_call(
    command_args: List[str], path: Optional[str], text: Optional[str]
) -> List[Dict[str, Any]]:
    """
    Call "pandoc citeproc" or "pandoc" using input from a path or text.
    Return dict representing CSL JSON.
    """
    assert command_args[0].startswith("pandoc")
    run_kwargs = {}
    if path:
        command_args.append(os.fspath(path))
    else:
        run_kwargs["input"] = text
    logging.info("load_bibliography subprocess args:\n>>> " + shlex_join(command_args))
    process = subprocess.run(
        command_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        **run_kwargs,
    )
    logging.info(f"captured stderr:\n{process.stderr}")
    if process.returncode:
        logging.error(
            f"Pandoc call returned nonzero exit code.\n"
            f"{shlex_join(process.args)}\n{process.stderr}"
        )
        return []
    try:
        csl_json = json.loads(process.stdout)
    except (TypeError, json.decoder.JSONDecodeError):
        logging.error(f"Error parsing bib2json output as JSON:\n{process.stdout}")
        csl_json = []
    return csl_json
