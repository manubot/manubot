import json
import logging
import subprocess

from manubot.pandoc.util import get_pandoc_info
from manubot.util import shlex_join


def load_bibliography(path=None, text=None, input_format=None):
    """
    Convert a bibliography to CSL JSON using `pandoc-citeproc --bib2json`.
    Accepts either a bibliography path or text (string). If supplying text,
    pandoc-citeproc will likely require input_format be specified.
    The CSL JSON is returned as Python objects.

    Parameters
    ----------
    path : str, pathlike, or None
        Path to a bibliography file. Extension is used by pandoc-citeproc to infer the
        format of the input.
    text : str or None
        Text representation of the bibligriophy, such as a JSON-formatted string.
        `input_format` should be specified if providing text input.
    input_format : str or None
        Manually specified input formatted that is supported by pandoc-citeproc:
        https://github.com/jgm/pandoc-citeproc/blob/master/man/pandoc-citeproc.1.md#options

    Returns
    -------
    csl_json : JSON-like object
        CSL JSON Data for the references encoded by the input bibliography.
    """
    use_text = path is None
    use_path = text is None
    if not (use_text ^ use_path):
        raise ValueError("load_bibliography: specify either path or text but not both.")
    if not get_pandoc_info()["pandoc-citeproc"]:
        logging.error(
            "pandoc-citeproc not found on system: manubot.pandoc.bibliography.load_bibliography returning empty CSL JSON"
        )
        return []
    args = ["pandoc-citeproc", "--bib2json"]
    if input_format:
        args.extend(["--format", input_format])
    run_kwargs = {}
    if use_path:
        args.append(str(path))
    if use_text:
        run_kwargs["input"] = text
    logging.info("call_pandoc subprocess args:\n>>> " + shlex_join(args))
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        **run_kwargs,
    )
    logging.info(f"captured stderr:\n{process.stderr}")
    process.check_returncode()
    try:
        csl_json = json.loads(process.stdout)
    except Exception:
        logging.exception(f"Error parsing bib2json output as JSON:\n{process.stdout}")
        csl_json = []
    return csl_json
