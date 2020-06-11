# Manuscript to generate CSL JSON Items for testing

Commands in this readme should be run from this directory:

```shell
cd manubot/process/tests/manuscripts/citation-rendering
```
## Generate output

To produce a rendered output file, run the following pandoc command:

```sh
mkdir -p output
pandoc \
  --to=html --output=output/manuscript.html \
  --csl=https://gist.githubusercontent.com/rmzelle/a3f1fab95a4b136962fce5b1b7cdeaf8/raw/0e2478d17476c633b080b5197e145d1e2b858a2f/manubot.csl \
  --metadata link-citations=true \
  --bibliography=content/manual-references.json \
  --include-after-body=https://github.com/manubot/rootstock/raw/master/build/themes/default.html \
  --include-after-body=https://github.com/manubot/rootstock/raw/master/build/plugins/tooltips.html \
  content/01.main-text.md
```

Evaluate `output/manuscript.html` to determine whether the references render properly.
This is useful for evaluating the effect of proposed changes to a CSL XML style

## Generate content

Use the Python script [`content/generate-csl-json-combinations.py`](content/generate-csl-json-combinations.py) to generate the content files `01.main-text.md` and `manual-references.json`:

```sh
python content/generate-csl-json-combinations.py
```
