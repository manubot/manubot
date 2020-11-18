import json
import logging
import pathlib
import subprocess
import sys

from manubot.pandoc.util import get_pandoc_info
from manubot.util import shlex_join
from manubot.cite.citations import Citations

# For manubot cite, infer --format from --output filename extensions
extension_to_format = {
    ".txt": "plain",
    ".md": "markdown",
    ".docx": "docx",
    ".html": "html",
    ".xml": "jats",
}

"""
URL or path with default CSL XML style.
<https://citation-style.manubot.org> redirects to the latest Manubot CSL Style.
"""
default_csl_style_path = "https://citation-style.manubot.org/"


def call_pandoc(metadata, path, format="plain"):
    """
    path is the path to write to.
    """
    _exit_without_pandoc()
    info = get_pandoc_info()
    _check_pandoc_version(info, metadata, format)
    metadata_block = "---\n{yaml}\n...\n".format(
        yaml=json.dumps(metadata, ensure_ascii=False, indent=2)
    )
    args = [
        "pandoc",
        "--citeproc"
        if info["pandoc version"] >= (2, 11)
        else "--filter=pandoc-citeproc",
        "--output",
        str(path) if path else "-",
    ]
    if format == "markdown":
        args.extend(["--to", "markdown_strict", "--wrap", "none"])
    elif format == "jats":
        args.extend(["--to", "jats", "--standalone"])
    elif format == "docx":
        args.extend(["--to", "docx"])
    elif format == "html":
        args.extend(["--to", "html"])
    elif format == "plain":
        args.extend(["--to", "plain", "--wrap", "none"])
        if info["pandoc version"] >= (2,):
            # Do not use ALL_CAPS for bold & underscores for italics
            # https://github.com/jgm/pandoc/issues/4834#issuecomment-412972008
            filter_path = (
                pathlib.Path(__file__)
                .joinpath("..", "plain-pandoc-filter.lua")
                .resolve()
            )
            assert filter_path.exists()
            args.extend(["--lua-filter", str(filter_path)])
    logging.info("call_pandoc subprocess args:\n" + shlex_join(args))
    process = subprocess.run(
        args=args,
        input=metadata_block.encode(),
    )
    process.check_returncode()


def _parse_cli_cite_args(args):
    arg_dict = vars(args)
    # check for implied --render
    if args.csl or args.format:
        arg_dict["render"] = True
    if not args.render:
        return
    # set --csl default
    arg_dict["csl"] = args.csl or default_csl_style_path
    # infer format from output extension
    if not args.format and args.output:
        arg_dict["format"] = extension_to_format.get(args.output.suffix)
    # default format to plain
    if not args.format:
        arg_dict["format"] = "plain"


def cli_cite(args):
    """
    Main function for the manubot cite command-line interface.

    Does not allow user to directly specify Pandoc's --to argument, due to
    inconsistent citation rendering by output format. See
    https://github.com/jgm/pandoc/issues/4834
    """
    _parse_cli_cite_args(args)
    citations = Citations(
        input_ids=args.citekeys, prune_csl_items=args.prune_csl, sort_csl_items=False
    )
    citations.load_manual_references(paths=args.bibliography)
    citations.inspect(log_level="WARNING")
    csl_items = citations.get_csl_items()

    # output CSL JSON data, if --render is False
    if not args.render:
        write_file = args.output.open("wb") if args.output else sys.stdout.buffer
        with write_file:
            write_file.write(citations.csl_json.encode())
        return

    # use Pandoc to render references
    pandoc_metadata = {"nocite": "@*", "csl": args.csl, "references": csl_items}
    call_pandoc(metadata=pandoc_metadata, path=args.output, format=args.format)


def _exit_without_pandoc() -> None:
    """
    Given info from get_pandoc_info, exit Python if Pandoc is not available.
    """
    if get_pandoc_info()["pandoc"]:
        return
    logging.critical(
        f"pandoc command not found on system. Ensure that Pandoc is installed."
    )
    raise SystemExit(1)


def _check_pandoc_version(info, metadata, format):
    """
    Given info from get_pandoc_info, check that Pandoc's version is sufficient
    to perform the citation rendering command specified by metadata and format.
    Please add additional minimum version information to this function, as its
    discovered.
    """
    issues = list()
    if format == "jats" and info["pandoc version"] < (2,):
        issues.append("--jats requires pandoc >= v2.0.")
    # --csl=URL did not work in https://travis-ci.org/greenelab/manubot/builds/417314743#L796,
    # but exact version where this fails unknown
    # if metadata.get('csl', '').startswith('http') and pandoc_version < (2,):
    #     issues.append('--csl=URL requires pandoc >= v2.0.')
    issues = "\n".join(issues)
    if issues:
        logging.critical(f"issues with pandoc version detected:\n{issues}")
