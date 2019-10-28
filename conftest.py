import pytest


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "pandoc_version_sensitive: marks tests that require a specific version of pandoc to pass"
    )


def pytest_addoption(parser):
    parser.addoption(
        '--use-requests-cache',
        action='store_true',
        help="Use requests_cache for caching web API calls"
    )
    parser.addoption(
        '--requests-cache-hours',
        action='store',
        default='12',
        help='Set time to live for requests cache. To be used with --use-requests-cache.'
    )


@pytest.fixture(scope='session', autouse=True)
def use_requests_cache(request):
    """Use requests_cache for caching web API calls.
       Enabled with --use-requests-cache flag:

          pytest --use-requests-cache
          pytest --use-requests-cache --requests-cache-hours=3
          pytest --use-requests-cache --requests-cache-hours=8760

       Notes:
       - By default the cache persists for 12 hours. Default can be overrriden
         with --requests-cache-hours option.
       - Cache does not work for invocations of manubot commands as subprocess.

       Cache file location: ./.cache/requests-cache.sqlite
    """

    if request.config.getoption('--use-requests-cache'):
        hours = int(request.config.getoption('--requests-cache-hours'))
        start_caching(hours)


def cache_path():
    from pathlib import Path
    folder = Path(__file__).resolve().parent / '.cache'
    if not folder.exists():
        folder.mkdir()
    # requests_cache itself always adds extension .sqlite
    return str(folder / 'requests-cache')


def start_caching(hours: int):
    from datetime import timedelta
    import logging
    from requests_cache import install_cache
    ttl = timedelta(hours=hours)
    install_cache(cache_name=cache_path(), expire_after=ttl)
    logging.info('Using requests_cache to speed up local tests execution.')
    logging.info(f"Cache location is {cache_path() + '.sqlite'}")
    logging.info(f'Cache expiration time is set to {ttl}')
