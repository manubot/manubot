import logging
import pathlib
import shutil
import subprocess

from manubot.util import shlex_join


def cli_webpage(args):
    """
    Execute manubot webpage commands.
    args should be an argparse.Namespace object created by parser.parse_args.
    """
    configure_args(args)
    logging.debug(f"Running `manubot webpage` with the following args:\n{args}")
    if args.timestamp:
        ots_upgrade(args)
    create_version(args)


def configure_args(args):
    """
    Perform additional processing of arguments that is not handled by argparse.
    Derive additional variables and add them to args.
    For example, add directories to args and create them if neccessary.
    Note that versions_directory is the parent of version_directory.
    """
    args_dict = vars(args)

    # If --timestamp specified, check that opentimestamps-client is installed
    if args.timestamp:
        ots_executable_path = shutil.which("ots")
        if not ots_executable_path:
            logging.error(
                "manubot webpage --timestamp was specified but opentimestamps-client not found on system. "
                "Setting --timestamp=False. "
                "Fix this by installing https://pypi.org/project/opentimestamps-client/"
            )
            args_dict["timestamp"] = False

    # Directory where Manubot outputs reside
    args_dict["output_directory"] = pathlib.Path("output")

    # Set webpage directory
    args_dict["webpage_directory"] = pathlib.Path("webpage")
    args.webpage_directory.mkdir(exist_ok=True)

    # Create webpage/v directory (if it doesn't already exist)
    args_dict["versions_directory"] = args.webpage_directory.joinpath("v")
    args.versions_directory.mkdir(exist_ok=True)

    # Checkout existing version directories
    checkout_existing_versions(args)

    # Apply --version argument defaults
    if args.version is None:
        from manubot.process.ci import get_continuous_integration_parameters

        ci_params = get_continuous_integration_parameters()
        if ci_params:
            args_dict["version"] = ci_params.get("commit", "local")
        else:
            args_dict["version"] = "local"

    # Create empty webpage/v/version directory
    version_directory = args.versions_directory.joinpath(args.version)
    if version_directory.is_dir():
        logging.warning(
            f"{version_directory} exists: replacing it with an empty directory"
        )
        shutil.rmtree(version_directory)
    version_directory.mkdir()
    args_dict["version_directory"] = version_directory

    # Symlink webpage/v/latest to point to webpage/v/commit
    latest_directory = args.versions_directory.joinpath("latest")
    if latest_directory.is_symlink() or latest_directory.is_file():
        latest_directory.unlink()
    elif latest_directory.is_dir():
        shutil.rmtree(latest_directory)
    latest_directory.symlink_to(args.version, target_is_directory=True)
    args_dict["latest_directory"] = latest_directory

    # Create freeze directory
    freeze_directory = args.versions_directory.joinpath("freeze")
    freeze_directory.mkdir(exist_ok=True)
    args_dict["freeze_directory"] = freeze_directory

    return args


def checkout_existing_versions(args):
    """
    Must populate webpage/v from the gh-pages branch to get history
    References:
    http://clubmate.fi/git-checkout-file-or-directories-from-another-branch/
    https://stackoverflow.com/a/2668947/4651668
    https://stackoverflow.com/a/16493707/4651668
    Command modeled after:
    git --work-tree=webpage checkout upstream/gh-pages -- v
    """
    if not args.checkout:
        return
    command = [
        "git",
        f"--work-tree={args.webpage_directory}",
        "checkout",
        args.checkout,
        "--",
        "v",
    ]
    logging.info(
        f"Attempting checkout with the following command:\n{shlex_join(command)}"
    )
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if process.returncode == 0:
        # Addresses an odd behavior where git checkout stages v/* files that don't actually exist
        subprocess.run(["git", "add", "v"], stdout=subprocess.PIPE)
    else:
        output = process.stdout.decode()
        message = (
            f"Checkout returned a nonzero exit status. See output:\n{output.rstrip()}"
        )
        if "pathspec" in output:
            message += (
                "\nManubot note: if there are no preexisting webpage versions (like for a newly created manuscript), "
                "the pathspec error above is expected and can be safely ignored."
            )  # see https://github.com/manubot/rootstock/issues/183
        logging.warning(message)


def create_version(args):
    """
    Populate the version directory for a new version.
    """
    # Copy content/images to webpage/v/commit/images
    images_src = pathlib.Path("content/images")
    if images_src.exists():
        shutil.copytree(src=images_src, dst=args.version_directory.joinpath("images"))

    # Copy output files to to webpage/v/version/
    renamer = {"manuscript.html": "index.html", "manuscript.pdf": "manuscript.pdf"}
    for src, dst in renamer.items():
        src_path = args.output_directory.joinpath(src)
        if not src_path.exists():
            continue
        dst_path = args.version_directory.joinpath(dst)
        shutil.copy2(src=src_path, dst=dst_path)
        if args.timestamp:
            ots_stamp(dst_path)

    # Create v/freeze to redirect to v/commit
    path = pathlib.Path(__file__).with_name("redirect-template.html")
    redirect_html = path.read_text()
    redirect_html = redirect_html.format(url=f"../{args.version}/")
    args.freeze_directory.joinpath("index.html").write_text(redirect_html)


def get_versions(args):
    """
    Extract versions from the webpage/v directory, which should each contain
    a manuscript.
    """
    versions = {x.name for x in args.versions_directory.iterdir() if x.is_dir()}
    versions -= {"freeze", "latest"}
    versions = sorted(versions)
    return versions


def ots_upgrade(args):
    """
    Upgrade OpenTimestamps .ots files in versioned commit directory trees.
    Upgrades each .ots file with a separate ots upgrade subprocess call due to
    https://github.com/opentimestamps/opentimestamps-client/issues/71
    """
    ots_paths = list()
    for version in get_versions(args):
        ots_paths.extend(args.versions_directory.joinpath(version).glob("**/*.ots"))
    ots_paths.sort()
    for ots_path in ots_paths:
        process_args = ["ots"]
        if args.no_ots_cache:
            process_args.append("--no-cache")
        else:
            process_args.extend(["--cache", str(args.ots_cache)])
        process_args.extend(["upgrade", str(ots_path)])
        process = subprocess.run(
            process_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        message = f">>> {shlex_join(process.args)}\n{process.stdout}"
        if process.returncode != 0:
            logging.warning(
                f"OpenTimestamp upgrade failed with exit code {process.returncode}.\n{message}"
            )
        elif not process.stdout.strip() == "Success! Timestamp complete":
            logging.info(message)
        backup_path = ots_path.with_suffix(".ots.bak")
        if backup_path.exists():
            if process.returncode == 0:
                backup_path.unlink()
            else:
                # Restore original timestamp if failure
                backup_path.rename(ots_path)


def ots_stamp(path):
    """
    Timestamp a file using OpenTimestamps.
    This function calls `ots stamp path`.
    If `path` does not exist, this function does nothing.
    """
    process_args = ["ots", "stamp", str(path)]
    process = subprocess.run(
        process_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    if process.returncode != 0:
        logging.warning(
            f"OpenTimestamp command returned nonzero code ({process.returncode}).\n"
            f">>> {shlex_join(process.args)}\n"
            f"{process.stdout}"
        )
