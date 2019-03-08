"""
Preliminary testing command:

pandoc \
  --filter=manubot/pandoc_filter/cite.py \
  --to=markdown \
  README.md
"""

"""
https://github.com/jgm/pandocfilters
https://github.com/sergiocorreia/panflute
"""
import argparse
import json
import sys

import pandocfilters

def parse_args():
    """
    Read command line arguments
    """
    parser = argparse.ArgumentParser(description='Pandoc figure numbers filter.')
    parser.add_argument('target_format')
    parser.add_argument('--pandocversion', help='The pandoc version.')
    parser.add_argument('--input', nargs='?', type=argparse.FileType('r', encoding='utf-8'), default=sys.stdin)
    parser.add_argument('--output', nargs='?', type=argparse.FileType('w', encoding='utf-8'), default=sys.stdout)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    doc = json.load(args.input)
    meta = doc.get('meta', {})
    #print(json.dumps(meta, indent=2), file=sys.stderr)
    json.dump(doc, args.output, ensure_ascii=False)


if __name__ == '__main__':
    main()
