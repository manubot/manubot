import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--use-requests-cache",
        action="store_true",
        help="Use requests_cache for caching web API calls"
    )
    parser.addoption(
        "--hours",
        action="store",
        default="12",
        help="Set time to live for requests cache"
    )


@pytest.fixture(scope='session', autouse=True)
def use_requests_cache(request):
    """Use requests_cache for caching web API calls.
       Enabled with --use-requests-cache flag:

          pytest --use-requests-cache
          pytest --use-requests-cache --hours=3
          pytest --use-requests-cache --hours=8760

       Notes:
       - By default the cache persists for 12 hours. Default can be overrriden
         with --hours option.
       - Cache does not work for invocations of manubot commands as subprocess.
    """
    if request.config.getoption("--use-requests-cache"):
        start_caching(hours=int(request.config.getoption("--hours")))


def start_caching(**kwargs):
    from datetime import timedelta
    from pathlib import Path
    from requests_cache import install_cache
    if not kwargs:
        kwargs = dict(hours=1)
    folder = Path(__file__).resolve().parent / '.cache'
    if not folder.exists():
        folder.mkdir()
    # requests_cache itself always adds extension .sqlite
    path = str(folder / 'requests-cache')
    ttl = timedelta(**kwargs)
    install_cache(cache_name=path, expire_after=ttl)
    print('Using requests_cache to speed up local tests')
    print('Cache location is', path + '.sqlite')
    print('Cache expiration time is set to', ttl)
