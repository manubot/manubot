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

    from manubot_ai_editor.editor import ManuscriptEditor
    from manubot_ai_editor.models import GPT3CompletionModel

    # create a manuscript editor and model to revise
    me = ManuscriptEditor(
        content_dir=content_dir,
    )

    model = GPT3CompletionModel(
        title=me.title,
        keywords=me.keywords,
    )

    me.revise_manuscript(tmp_dir, model, debug=True)

    # move the revised manuscript back to the content folder
    for f in tmp_dir.glob("*"):
        shutil.move(f, content_dir / f.name)
