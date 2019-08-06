import os

import pytest

from ..ci import get_continuous_integration_parameters


@pytest.mark.skipif('TRAVIS' not in os.environ, reason='tests environment variables set by Travis builds only')
def test_get_continuous_integration_parameters_travis():
    info = get_continuous_integration_parameters()
    assert info is not None
    assert info['provider'] == 'travis'
    assert info['repo_slug'] == 'manubot/manubot'
    assert info['repo_owner'] == 'manubot'
    assert info['repo_name'] == 'manubot'
    assert info['commit']
    assert info['triggering_commit']
    assert info['build_url'].startswith('https://travis-ci.com/manubot/manubot/builds/')
    assert info['job_url'].startswith('https://travis-ci.com/manubot/manubot/jobs/')


@pytest.mark.skipif('APPVEYOR' not in os.environ, reason='tests environment variables set by AppVeyor builds only')
def test_get_continuous_integration_parameters_appveyor():
    info = get_continuous_integration_parameters()
    assert info is not None
    assert info['provider'] == 'appveyor'
    assert info['provider_account'] == 'manubot'
    assert info['repo_slug'] == 'manubot/manubot'
    assert info['repo_owner'] == 'manubot'
    assert info['repo_name'] == 'manubot'
    assert info['commit']
    assert info['triggering_commit']
    assert info['build_url'].startswith('https://ci.appveyor.com/project/manubot/manubot/builds/')
    assert info['job_url'].startswith('https://ci.appveyor.com/project/manubot/manubot/build/job/')


@pytest.mark.skipif('CI' in os.environ, reason='tests function when run outside of a CI build')
def test_get_continuous_integration_parameters_no_ci():
    info = get_continuous_integration_parameters()
    assert info is None
