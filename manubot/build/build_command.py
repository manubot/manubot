import pathlib
import logging
import subprocess

from manubot.util import shlex_join


def cli_build(args):
    args_dict = vars(args)
    # args_dict["content_directory"] = args.directory / "content"
    # args_dict["output_directory"] = args.directory / "output"
    args_dict["pandoc_data_dir"] = pathlib.Path(__file__).parent.joinpath("pandoc-data")
    args_dict["csl_style_path"] = args.pandoc_data_dir.joinpath("style.csl")
    # Would be better to have these opts in defaults files, but see
    # https://github.com/jgm/pandoc/issues/5982#issuecomment-588410073
    args_dict['opts_common'] = ["--csl", args.csl_style_path.absolute()]
    build_html(args)
    build_docx(args)


def build_html(args):
    opts_html = []
    include_after_body = [
        'themes/default.html',
        "plugins/anchors.html",
        "plugins/accordion.html",
        "plugins/tooltips.html",
        "plugins/jump-to-first.html",
        "plugins/link-highlight.html",
        "plugins/table-of-contents.html",
        "plugins/lightbox.html",
        "plugins/attributes.html",
        "plugins/math.html",
        "plugins/hypothesis.html",
        "plugins/analytics.html",
    ]
    for path in include_after_body:
        opts_html.append("--include-after-body")
        opts_html.append(args.pandoc_data_dir.joinpath(path))
    logging.info("Exporting HTML manuscript")
    # logging.info(args.pandoc_data_dir.absolute())
    # logging.info(list(args.pandoc_data_dir.iterdir()))
    command = [
        "pandoc",
        *args.opts_common, *opts_html,
        "--data-dir", args.pandoc_data_dir.absolute(),
        "--resource-path", f".:{args.pandoc_data_dir.absolute()}",
        "--defaults=common", "--defaults=html",
    ]
    process = subprocess.run(command, cwd=args.directory)
    logging.info(shlex_join(process.args))


def build_docx(args):
    opts_docx = ["--reference-doc", args.pandoc_data_dir.joinpath("themes/default.docx").absolute()]
    logging.info("Exporting DOCX manuscript")
    command = [
        "pandoc",
        *args.opts_common, *opts_docx,
        "--data-dir", args.pandoc_data_dir.absolute(),
        "--resource-path", f".:{args.pandoc_data_dir.absolute()}",
        "--defaults=common", "--defaults=docx",
    ]
    process = subprocess.run(command, cwd=args.directory)
    logging.info(shlex_join(process.args))
    logging.info(process)
