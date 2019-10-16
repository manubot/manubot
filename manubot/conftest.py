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
    from requests_cache import install_cache
    if not kwargs:
        kwargs = dict(hours=1)
    install_cache(cache_name='test_cache', # requests_cache always adds 
                                           # extension .sqlite
                  expire_after=timedelta(**kwargs))
