import json
import logging
import re

import requests


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

    Uses urllib.request.urlopen rather than requests.get due to
    https://github.com/kennethreitz/requests/issues/4023
    """
    response = requests.get(
        'http://greycite.knowledgeblog.org/json',
        params={'uri': url},
        headers={'Connection': 'close'},
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


def get_url_citeproc(url):
    """
    Get citeproc for a URL trying a sequence of strategies.
    """
    try:
        return get_url_citeproc_greycite(url)
    except Exception as e:
        logging.warning(f'Error getting {url} from Greycite: {e}')
        # Fallback strategy
        return get_url_citeproc_manual(url)
