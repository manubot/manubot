import json
import logging
import re

import requests


def get_url_citeproc(url):
    """
    Get citeproc for a URL trying a sequence of strategies.
    """
    functions = [
        get_url_citeproc_zotero,
        get_url_citeproc_greycite,
        get_url_citeproc_manual,
    ]
    for function in functions:
        try:
            return function(url)
        except Exception as error:
            logging.warning(
                f'Error in {function.__name__} for {url} '
                f'due to a {error.__class__.__name__}:\n{error}'
            )
            logging.info(error, exc_info=True)


def get_url_citeproc_zotero(url):
    """
    Use Zotero's translation-server to generate a CSL Item for the specified URL.
    """
    from manubot.cite.zotero import (
        export_as_csl,
        web_query,
    )
    zotero_json = web_query(url)
    csl_json = export_as_csl(zotero_json)
    csl_item, = csl_json
    return csl_item


def get_url_citeproc_greycite(url):
    """
    Uses Greycite which has experiened uptime problems in the past.
    API calls seem to take at least 15 seconds. Browser requests are much
    faster. Setting header did not have an effect. Consider mimicking browser
    using selenium.

    More information on Greycite at:
    http://greycite.knowledgeblog.org/
    http://knowledgeblog.org/greycite
    https://arxiv.org/abs/1304.7151
    https://git.io/v9N2C
    """
    from manubot.util import get_manubot_user_agent
    headers = {
        'Connection': 'close',  # https://github.com/kennethreitz/requests/issues/4023
        'User-Agent': get_manubot_user_agent(),
    }
    response = requests.get(
        'http://greycite.knowledgeblog.org/json',
        params={'uri': url},
        headers=headers,
    )
    # Some Greycite responses were valid JSON besides for an error appended
    # like "<p>*** Date set from uri<p>" or "<p>*** fetch error : 404<p>".
    pattern = re.compile(r"<p>\*\*\*.*<p>")
    text = pattern.sub('', response.text)
    csl_item = json.loads(text)
    csl_item['type'] = 'webpage'
    return csl_item


def get_url_citeproc_manual(url):
    """
    Manually create citeproc for a URL.
    """
    return {
        'URL': url,
        'type': 'webpage',
    }
