import os
import logging

supported_providers = ["travis", "appveyor"]


def get_continuous_integration_parameters():
    """
    Return a dictionary with information on a continuous integration build
    inferred from environment variables.

    The following dictionary keys are set (all values are also strings):
    - provider: name of CI provider, such as "travis" or "appveyor".
    - repo_slug: owner/name of the source code repository, i.e. "manubot/rootstock"
    - repo_owner: owner from repo_slug, i.e. "manubot"
    - repo_name: name from repo_slug, i.e. "rootstock"
    - commit: git commit being evaluated by the CI build
    - triggering_commit: git commit that triggered the CI build. For pull requests,
        CI services often build a merge commit with the default branch rather than
        the commit that was added to the pull request.
    - build_url: URL for the webpage with build details
    - job_url: URL for the webpage with job details
    """
    if os.getenv("CI", "false").lower() != "true":
        # No continuous integration environment detected
        return None

    if os.getenv("TRAVIS", "false") == "true":
        # https://docs.travis-ci.com/user/environment-variables/
        repo_slug = os.environ["TRAVIS_REPO_SLUG"]
        repo_owner, repo_name = repo_slug.split("/")
        return {
            "provider": "travis",
            "repo_slug": repo_slug,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "commit": os.environ["TRAVIS_COMMIT"],
            "triggering_commit": os.getenv("TRAVIS_PULL_REQUEST_SHA")
            or os.environ["TRAVIS_COMMIT"],
            "build_url": os.environ["TRAVIS_BUILD_WEB_URL"],
            "job_url": os.environ["TRAVIS_JOB_WEB_URL"],
        }

    if os.getenv("APPVEYOR", "false").lower() == "true":
        # https://www.appveyor.com/docs/environment-variables/
        repo_slug = os.environ["APPVEYOR_REPO_NAME"]
        repo_owner, repo_name = repo_slug.split("/")
        provider_url = "{APPVEYOR_URL}/project/{APPVEYOR_ACCOUNT_NAME}/{APPVEYOR_PROJECT_SLUG}".format(
            **os.environ
        )
        build_url = f"{provider_url}/builds/{os.environ['APPVEYOR_BUILD_ID']}"
        return {
            "provider": "appveyor",
            "provider_account": os.environ["APPVEYOR_ACCOUNT_NAME"],
            "repo_slug": repo_slug,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "commit": os.environ["APPVEYOR_REPO_COMMIT"],
            "triggering_commit": os.getenv("APPVEYOR_PULL_REQUEST_HEAD_COMMIT")
            or os.environ["APPVEYOR_REPO_COMMIT"],
            "build_url": build_url,
            "job_url": f"{provider_url}/build/job/{os.environ['APPVEYOR_JOB_ID']}",
            "artifact_url": f"{build_url}/artifacts",
        }

    logging.warning(
        "Detected CI environment variable, but get_continuous_integration_parameters "
        "did not detect environment variables for a supported CI provider. "
        "Supported providers are: {}".format(", ".join(supported_providers))
    )
    return None
