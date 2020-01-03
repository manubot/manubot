import logging


def cli_process(args):
    args_dict = vars(args)

    # Set paths for content
    content_dir = args.content_directory
    if not content_dir.is_dir():
        logging.warning(f"content directory does not exist: {content_dir}")
    args_dict["citation_tags_path"] = content_dir.joinpath("citation-tags.tsv")
    args_dict["meta_yaml_path"] = content_dir.joinpath("metadata.yaml")
    args_dict["manual_references_paths"] = sorted(
        content_dir.rglob("manual-references*.*")
    )

    # Set paths for output
    output_dir = args.output_directory
    output_dir.mkdir(parents=True, exist_ok=True)
    args_dict["manuscript_path"] = output_dir.joinpath("manuscript.md")
    args_dict["citations_path"] = output_dir.joinpath("citations.tsv")
    args_dict["references_path"] = output_dir.joinpath("references.json")
    args_dict["variables_path"] = output_dir.joinpath("variables.json")

    # Set paths for caching
    args_dict["cache_directory"] = args.cache_directory or output_dir
    args.cache_directory.mkdir(parents=True, exist_ok=True)
    args_dict["requests_cache_path"] = str(
        args.cache_directory.joinpath("requests-cache")
    )

    from manubot.process.util import prepare_manuscript

    prepare_manuscript(args)
