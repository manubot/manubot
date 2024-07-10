import logging
import shutil
import tempfile
from pathlib import Path


def cli_process(args):
    try:
        from manubot_ai_editor import models
        from manubot_ai_editor.editor import ManuscriptEditor
    except ImportError as err:
        raise ModuleNotFoundError(
            "Install manubot with: pip install manubot[ai-rev]"
        ) from err

    # set paths for content
    content_dir = args.content_directory
    if not content_dir.is_dir():
        raise SystemExit(
            f"content directory is not a directory or does not exist: {content_dir}"
        )
    
    # set paths for config
    # (the config directory is optional, but if it is provided, it must be a directory)
    config_dir = args.config_directory
    if config_dir is not None and not config_dir.is_dir():
        raise SystemExit(
            f"config directory is not a directory or does not exist: {config_dir}"
        )

    # set paths for temporary output
    tmp_dir = Path(tempfile.mkdtemp(suffix="_manubot_ai_revision"))
    logging.info(f"using temporary directory: {tmp_dir}")

    # create a manuscript editor and model to revise
    me = ManuscriptEditor(
        content_dir=content_dir,
        config_dir=config_dir,
    )

    # instantiate a model
    module_class = getattr(models, args.model_type)

    if issubclass(module_class, models.GPT3CompletionModel):
        model = module_class(
            title=me.title,
            keywords=me.keywords,
        )
    else:
        model_kwargs = parse_kwargs(args.model_kwargs)

        model = module_class(
            **model_kwargs,
        )

    # revise
    me.revise_manuscript(tmp_dir, model, debug=True)

    # copy the revised manuscript back to the content folder
    for f in tmp_dir.glob("*"):
        shutil.copyfile(f, content_dir / f.name)


def parse_kwargs(kwargs: list[str]) -> dict[str, object]:
    """
    Parse a list of keyword arguments into a dictionary. Values are converted to int or bool if possible.

    Args:
        kwargs: A list of keyword arguments with format "key=value".

    Returns:
        A dictionary of keyword arguments. Returns an empty dictionary if kwargs is None.
    """
    out = {}

    if kwargs is None:
        return out

    for kwarg in kwargs:
        if "=" not in kwarg:
            raise ValueError(f"Invalid keyword argument: {kwarg}")

        key, value = kwarg.split("=", maxsplit=1)

        # try to convert values to int or bool if possible
        if value.isdigit():
            value = int(value)
        elif value.lower() in ["true", "false"]:
            value = value.lower() == "true"

        out[key] = value

    return out
