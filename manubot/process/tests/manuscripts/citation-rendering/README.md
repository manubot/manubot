# Manuscript to generate CSL JSON Items for testing

Use the Python script [`content/generate-csl-json-combinations.py`](content/generate-csl-json-combinations.py) to generate the content files `01.main-text.md` and `manual-references.json`:

```sh
python content/generate-csl-json-combinations.py
```

To produce a rendered output file, run the following pandoc command:

```sh
mkdir output
pandoc \
  --to=html --output=output/manuscript.html \
  --csl=https://github.com/manubot/rootstock/raw/master/build/assets/style.csl \
  --metadata link-citations=true \
  --bibliography=content/manual-references.json \
  --include-after-body=https://github.com/manubot/rootstock/raw/master/build/themes/default.html \
  --include-after-body=https://github.com/manubot/rootstock/raw/master/build/plugins/tooltips.html \
  content/01.main-text.md
```
