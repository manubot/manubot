import os
import re

import pytest

from ..ci import get_continuous_integration_parameters


@pytest.mark.skipif(
    "GITHUB_ACTION" not in os.environ,
    reason="tests environment variables set by GitHub Actions only",
)
@pytest.mark.skipif(
    os.getenv("GITHUB_REPOSITORY") != "manubot/manubot", reason="test fails on forks"
)
def test_get_continuous_integration_parameters_github():
    info = get_continuous_integration_parameters()
    assert info is not None
    assert info["provider"] == "github"
    assert info["repo_slug"] == "manubot/manubot"
    assert info["repo_owner"] == "manubot"
    assert info["repo_name"] == "manubot"
    assert info["commit"]
    assert info["triggering_commit"]
    assert info["build_url"].startswith("https://github.com/manubot/manubot/commit/")
    assert info["job_url"].startswith("https://github.com/manubot/manubot/runs/")


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
    assert re.fullmatch(
        pattern=r"https://ci\.appveyor\.com/project/manubot/manubot/builds/[0-9]+/artifacts",
        string=info["artifact_url"],
    )
