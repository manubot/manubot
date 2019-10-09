import os
import re

import pytest

from ..ci import (
    add_manuscript_urls_to_ci_params,
    get_continuous_integration_parameters,
)

@pytest.fixture
def info():
    return get_continuous_integration_parameters()


# TODO: test generic properties of `info` distionary, eg list of keys
# TODO: make class for get_continuous_integration_parameters

@pytest.mark.skipif('CI' not in os.environ)
def test_get_continuous_integration_parameters_generic(info):
    assert info is not None
    # assume fork repo name unchanged
    assert info['repo_slug'].endswith('manubot') 
    assert info['repo_name'] == 'manubot' 
    # commis are not empty
    assert info['commit']
    assert info['triggering_commit']


# TODO: need similar test for APPVEYOR, what is the slug constant name?
#       may embed in this test  
@pytest.mark.skipif('TRAVIS' not in os.environ 
                     or os.environ['TRAVIS_REPO_SLUG'] != 'manubot/manubot',
                     reason='this test runs only for ')
def test_get_continuous_integration_parameters_on_master_repo_on_travis(info):
    assert info['repo_slug'] == 'manubot/manubot'
    assert info['repo_owner'] == 'manubot'

@pytest.mark.skipif('TRAVIS' not in os.environ, reason='tests environment variables set by Travis builds only')
def test_get_continuous_integration_parameters_travis(info):
    assert info is not None
    assert info['provider'] == 'travis'
    assert info['build_url'].startswith('https://travis-ci.com/manubot/manubot/builds/')
    assert info['job_url'].startswith('https://travis-ci.com/manubot/manubot/jobs/')
    
    # TODO: must be separate test - it depends on owner name
    # test add_manuscript_urls_to_ci_params
    info_updated = add_manuscript_urls_to_ci_params(info)    
    assert info is info_updated
    assert re.fullmatch(
        pattern=r"https://manubot\.github\.io/manubot/v/[0-9a-f]{40}/",
        string=info['manuscript_url'],
    )


@pytest.mark.skipif('APPVEYOR' not in os.environ, reason='tests environment variables set by AppVeyor builds only')
def test_get_continuous_integration_parameters_appveyor(info):
    assert info is not None
    assert info['provider'] == 'appveyor'
    assert info['provider_account'] == 'manubot' # FIXME
    assert info['build_url'].startswith('https://ci.appveyor.com/project/manubot/manubot/builds/')
    assert info['job_url'].startswith('https://ci.appveyor.com/project/manubot/manubot/build/job/')
    
    # TODO: must be separate test - it depends on owner name
    # test add_manuscript_urls_to_ci_params
    info_updated = add_manuscript_urls_to_ci_params(info)
    assert info is info_updated
    assert re.fullmatch(
        pattern=r"https://ci\.appveyor\.com/project/manubot/manubot/builds/[0-9]+/artifacts",
        string=info['manuscript_url'],
    )


@pytest.mark.skipif('CI' in os.environ, reason='tests function when run outside of a CI build')
def test_get_continuous_integration_parameters_no_ci():
    info = get_continuous_integration_parameters()
    assert info is None
    # test add_manuscript_urls_to_ci_params
    info_updated = add_manuscript_urls_to_ci_params(info)
    assert info_updated is None
