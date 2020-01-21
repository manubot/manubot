"""
Must set --standalone
https://github.com/manubot/rootstock/blob/f6b623157304c46f5f77578a15d1f353674e814e/build/pandoc-defaults/html.yaml#L5-L17
https://github.com/tomduck/pandoc-xnos/blob/8f5ef7d0087ab1fc3f48943d266d2196d9d414d1/pandocxnos/core.py#L318-L374
https://github.com/jgm/pandoc/issues/3139
"""
import logging

import requests
# import panflute as pf

theme = "default"
plugins = [
    "anchors",
    "accordion",
    "tooltips",
    "jump-to-first",
    "link-highlight",
    "table-of-contents",
    "lightbox",
    "attributes",
    "math",
    "hypothesis",
    "analytics",
]


rootstock_raw_base_url = "https://github.com/manubot/rootstock/raw/f6b623157304c46f5f77578a15d1f353674e814e"


def get_text_at_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def processer(doc, args):
    if not args.target_format.startswith("html") or args.target_format == "json":
        logging.warning(
            "pandoc-manubot-html is designed for HTML outputs. "
            f"Filter received a target format of {args.target_format}. "
            "Skipping filter.")
        return
    include_after = doc.get_metadata("include-after", default="")
    include_after += "\n\n```\n"
    include_after_urls = [f"{rootstock_raw_base_url}/build/themes/{theme}.html"]
    for plugin in plugins:
        url = f"{rootstock_raw_base_url}/build/plugins/{plugin}.html"
        include_after_urls.append(url)
    for url in include_after_urls:
        include_after += get_text_at_url(url)
    include_after += "\n```\n"
    # does not currently work because include-after text is getting processed rather than treated as raw
    doc.metadata["include-after"] = include_after


def main():
    from .filter import filter_main

    description = "Pandoc filter for HMTL output theme and plugins. "
    filter_main(processer, description)
