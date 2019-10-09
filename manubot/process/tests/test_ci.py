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


@pytest.mark.skipif(
    'CI' not in os.environ,
    reason='These tests do not apply outside continious integration system (CI)')
class Test_get_continuous_integration_parameters():

    def test_not_empty(self, info):
        assert info is not None

    def test_repo_name(self, info):
        """
        We assume 'manubot' repo name stays the same in repo forks.
        """
        assert info['repo_name'] == 'manubot'
        assert info['repo_slug'].endswith('manubot')

    @pytest.mark.skipif('TRAVIS' not in os.environ,
                        reason="Test parameters are specific to Travis")    
    def test_repo_slug_on_travis(self, info):
        # TRAVIS_REPO_SLUG: The slug (in form: owner_name/repo_name) of the repository 
        # currently being built. https://docs.travis-ci.com/user/environment-variables/
        assert info['repo_slug'] == os.environ['TRAVIS_REPO_SLUG']
        

    @pytest.mark.skipif('APPVEYOR' not in os.environ,
                        reason="Test parameters are specific to APPVEYOR")    
    def test_repo_slug_on_travis(self, info):
        # APPVEYOR_PROJECT_NAME - project name
        # APPVEYOR_PROJECT_SLUG - project slug (as seen in project details URL)
        # https://www.appveyor.com/docs/environment-variables/
        assert info['repo_slug'] == os.environ['APPVEYOR_PROJECT_SLUG']

    @pytest.mark.skipif('TRAVIS' not in os.environ or 'APPVEYOR' not in os.environ,
                        reason="Behaviour not guaranteed outside Travis or Appveyor CI"")
    def test_commits_are_not_empty(self, info):
        assert info['commit']
        assert info['triggering_commit']

    @pytest.mark.skipif('TRAVIS' not in os.environ,
                        reason="This test is specific to Travis CI")
    def test_parameters_travis(self, info):
        assert info['provider'] == 'travis'
        assert info['build_url'].startswith('https://travis-ci.com')
        assert '/manubot/builds/' in info['build_url']
        assert info['job_url'].startswith('https://travis-ci.com')
        assert '/manubot/jobs/' in info['job_url']

    @pytest.mark.skipif('APPVEYOR' not in os.environ,
                        reason="This test is specific to Appveyor")
    def test_parameters_appveyor(self, info):
        assert info['provider'] == 'appveyor'
        # assert info['provider_account'] == 'manubot' # FIXME
        assert info['build_url'].startswith('https://ci.appveyor.com/project/')
        assert '/manubot/builds/' in info['build_url']
        assert info['job_url'].startswith('https://ci.appveyor.com/project/')
        assert '/manubot/build/job/' in info['job_url']


class Test_add_manuscript_urls_to_ci_params:

    @pytest.mark.skipif('TRAVIS' not in os.environ
                        or os.environ['TRAVIS_REPO_SLUG'] != 'manubot/manubot',
                        reason="This test is specific to Travis CI")
    def test_on_travis(self, info):
        info_updated = add_manuscript_urls_to_ci_params(info)
        assert info is info_updated
        assert re.fullmatch(
            pattern=r"https://manubot\.github\.io/manubot/v/[0-9a-f]{40}/",
            string=info['manuscript_url'],
        )

    @pytest.mark.skipif('APPVEYOR' not in os.environ
                        or os.environ['APPVEYOR_PROJECT_SLUG'] != 'manubot/manubot',
                        reason="This test is specific to Appveyor")
    def test_on_appveyor(self, info):
        info_updated = add_manuscript_urls_to_ci_params(info)
        assert info is info_updated
        assert re.fullmatch(
            pattern=r"https://ci\.appveyor\.com/project/manubot/manubot/builds/[0-9]+/artifacts",
            string=info['manuscript_url'],
        )


@pytest.mark.skipif(
    'CI' in os.environ,
    reason='tests functions when run outside of a CI build')
def test_get_continuous_integration_parameters_no_ci():
    info = get_continuous_integration_parameters()
    assert info is None
    # test add_manuscript_urls_to_ci_params
    info_updated = add_manuscript_urls_to_ci_params(info)
    assert info_updated is None
