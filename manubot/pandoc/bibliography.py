

def load_bibliography(path=None, text=None, input_format=None):
    """
    Convert a bibliography to CSL JSON using `pandoc-citeproc --bib2json`.
    Accepts either a bibliography path or text (string). If supplying text,
    pandoc-citeproc will likely require input_format be specified.
    The CSL JSON is returned as Python objects.
    """
    use_text = path is None
    use_path = text is None
    if not (use_text ^ use_path):
        raise ValueError('load_bibliography: specify either path or text but not both.')
    args = [
        'pandoc-citeproc', '--bib2json',
    ]
    if input_format:
        args.extend(['--format', input_format])
    run_kwargs = {}
    if use_path:
        args.append(str(path))
    if use_text:
        run_kwargs['input'] = text
    logging.info('call_pandoc subprocess args:\n' + ' '.join(args))
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        **run_kwargs,
    )
    logging.info(f'captured stderr:\n{process.stderr}')
    process.check_returncode()
    try:
        csl_json = json.loads(process.stdout)
    except Exception:
        logging.exception(f'Error parsing bib2json output as JSON:\n{process.stdout}')
        csl_json = []
    return csl_json
