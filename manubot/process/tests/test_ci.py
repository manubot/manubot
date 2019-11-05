import os
import re

import pytest

from ..ci import add_manuscript_urls_to_ci_params, get_continuous_integration_parameters


@pytest.mark.skipif(
    "TRAVIS" not in os.environ,
    reason="tests environment variables set by Travis builds only",
)
@pytest.mark.skipif(
    os.getenv("TRAVIS_REPO_SLUG") != "manubot/manubot", reason="test fails on forks"
)
def test_get_continuous_integration_parameters_travis():
    info = get_continuous_integration_parameters()
    assert info is not None
    assert info["provider"] == "travis"
    assert info["repo_slug"] == "manubot/manubot"
    assert info["repo_owner"] == "manubot"
    assert info["repo_name"] == "manubot"
    assert info["commit"]
    assert info["triggering_commit"]
    assert info["build_url"].startswith("https://travis-ci.com/manubot/manubot/builds/")
    assert info["job_url"].startswith("https://travis-ci.com/manubot/manubot/jobs/")
    # test add_manuscript_urls_to_ci_params
    info_updated = add_manuscript_urls_to_ci_params(info)
    assert info is info_updated
    assert re.fullmatch(
        pattern=r"https://manubot\.github\.io/manubot/v/[0-9a-f]{40}/",
        string=info["manuscript_url"],
    )


@pytest.mark.skipif(
    "APPVEYOR" not in os.environ,
    reason="tests environment variables set by AppVeyor builds only",
)
@pytest.mark.skipif(
    os.getenv("APPVEYOR_REPO_NAME") != "manubot/manubot", reason="test fails on forks"
)
def test_get_continuous_integration_parameters_appveyor():
    info = get_continuous_integration_parameters()
    assert info is not None
    assert info["provider"] == "appveyor"
    assert info["provider_account"] == "manubot"
    assert info["repo_slug"] == "manubot/manubot"
    assert info["repo_owner"] == "manubot"
    assert info["repo_name"] == "manubot"
    assert info["commit"]
    assert info["triggering_commit"]
    assert info["build_url"].startswith(
        "https://ci.appveyor.com/project/manubot/manubot/builds/"
    )
    assert info["job_url"].startswith(
        "https://ci.appveyor.com/project/manubot/manubot/build/job/"
    )
    # test add_manuscript_urls_to_ci_params
    info_updated = add_manuscript_urls_to_ci_params(info)
    assert info is info_updated
    assert re.fullmatch(
        pattern=r"https://ci\.appveyor\.com/project/manubot/manubot/builds/[0-9]+/artifacts",
        string=info["manuscript_url"],
    )


@pytest.mark.skipif(
    "CI" in os.environ, reason="tests function when run outside of a CI build"
)
def test_get_continuous_integration_parameters_no_ci():
    info = get_continuous_integration_parameters()
    assert info is None
    # test add_manuscript_urls_to_ci_params
    info_updated = add_manuscript_urls_to_ci_params(info)
    assert info_updated is None
