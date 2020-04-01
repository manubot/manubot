import pathlib
import logging
import subprocess
import os

from manubot.util import shlex_join


def cli_build(args):
    args_dict = vars(args)
    # args_dict["content_directory"] = args.directory / "content"
    args_dict["output_directory"] = args.directory / "output"
    args_dict["pandoc_data_dir"] = pathlib.Path(__file__).parent.joinpath("pandoc-data")
    resource_paths = os.pathsep.join([".", str(args.pandoc_data_dir.absolute()),])
    args_dict["opts_common"] = [
        # "--csl", args.csl_style_path.absolute()
        f"--data-dir={args.pandoc_data_dir.absolute()}",
        f"--resource-path={resource_paths}",
        "--defaults=common",
    ]
    # Show pandoc_data_dir contents for debugging
    logging.info("showing pandoc_data_dir contents:")
    subprocess.run(["ls", "--recursive", args.pandoc_data_dir.absolute()])
    build_html(args)
    # if os.environ.get("BUILD_PDF") != "false":
    #     build_pdf(args)
    if os.environ.get("BUILD_DOCX") == "true":
        build_docx(args)


def build_html(args):
    logging.info("Exporting HTML manuscript")
    command = [
        "pandoc",
        *args.opts_common,
        "--defaults=html",
    ]
    process = subprocess.run(command, cwd=args.directory)
    logging.info(shlex_join(process.args))


def build_pdf(args):
    """
    https://github.com/manubot/rootstock/blob/c25f8b8df29bf660f9bbd52521514eaedfa1273c/build/build.sh#L53-L83
    """
    import shutil

    if shutil.which("docker"):
        build_pdf_docker(args)
    else:
        logging.warning("Skipping building PDF because docker not available")


def build_pdf_docker(args):
    """
    TODO: handle images directory
    """
    delay = os.environ.get("MANUBOT_ATHENAPDF_DELAY")
    if not delay:
        delay = "5000" if os.environ.get("CI") == "true" else "1100"
    logging.info("Exporting PDF manuscript using Docker + Athena")
    command = [
        "docker",
        "run",
        "--rm",
        "--shm-size=1g",
        "--volume",
        f"{args.output_directory.absolute()}:/converted/",
        "--security-opt=seccomp:unconfined",
        "arachnysdocker/athenapdf:2.16.0",
        "athenapdf",
        "--delay",
        delay,
        "--pagesize=A4",
        "manuscript.html",
        "manuscript.pdf",
    ]
    process = subprocess.run(command)
    logging.info(shlex_join(process.args))


def build_docx(args):
    logging.info("Exporting DOCX manuscript")
    command = [
        "pandoc",
        *args.opts_common,
        "--defaults=docx",
        # todo add content to resource-path
    ]
    process = subprocess.run(command, cwd=args.directory)
    logging.info(shlex_join(process.args))
    logging.info(process)
