import logging


def cli_process(args):
    # set paths for content
    content_dir = args.content_directory
    if not content_dir.is_dir():
        logging.warning(f"content directory does not exist: {content_dir}")

    # set paths for temporary output
    tmp_dir = args.temporary_directory
    if tmp_dir is None:
        # if temporary directory is not given, generate one
        import tempfile
        from pathlib import Path

        tmp_dir = tempfile.TemporaryDirectory()
        tmp_dir = Path(tmp_dir.name)
        logging.warning(f"output directory not specified, using: {tmp_dir}")

    tmp_dir.mkdir(parents=True, exist_ok=True)

    import shutil

    from manubot_ai_editor import models
    from manubot_ai_editor.editor import ManuscriptEditor

    # create a manuscript editor and model to revise
    me = ManuscriptEditor(
        content_dir=content_dir,
    )

    # instantiate a model
    module_class = getattr(models, args.model_type)

    if module_class == models.GPT3CompletionModel:
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

    # move the revised manuscript back to the content folder
    for f in tmp_dir.glob("*"):
        shutil.move(f, content_dir / f.name)


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
