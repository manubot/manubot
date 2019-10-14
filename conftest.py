import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--use-requests-cache",
        action="store_true",
        help="Use requests_cache for caching web API calls"
    )


import pytest
@pytest.fixture(scope='session', autouse=True)
def use_requests_cache(request):
    """Use requests_cache for caching web API calls. 
       Enabled with --use-requests-cache flag:

          pytest --use-requests-cache

       Notes:
       - The cache persists for 12 hours.
       - Cache does not working for invocations of manubot commands as subprocess.
    """
    if request.config.getoption("--use-requests-cache"): 
        start_caching(hours=12)


def start_caching(**kwargs):
    from datetime import timedelta
    from requests_cache import install_cache
    if not kwargs:
        kwargs = dict(hours=1)
    install_cache(cache_name='test_cache', # extension .sqlite always added by requests_cache
                  expire_after=timedelta(**kwargs))
