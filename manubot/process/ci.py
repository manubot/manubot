import logging
import os

supported_providers = ["github", "travis", "appveyor"]


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
        For pull requests, CI services often build a merge commit
        with the default branch rather than the commit that was
        added to the pull request. In these cases, commit refers
        to this merge commit.
    - triggering_commit: git commit that triggered the CI build.
    - build_url: URL for the webpage with build details
    - job_url: URL for the webpage with job details

    GitHub Actions does not set an environment variable with triggering_commit
    for pull requests. Therefore, set the following environment variable in your workflow:

    ```yaml
    env:
      GITHUB_PULL_REQUEST_SHA: ${{ github.event.pull_request.head.sha }}
    ```
    """
    if os.getenv("GITHUB_ACTIONS", "false") == "true":
        # https://git.io/JvUf7
        repo_slug = os.environ["GITHUB_REPOSITORY"]
        repo_owner, repo_name = repo_slug.split("/")
        action_id = os.environ["GITHUB_ACTION"]
        # GITHUB_SHA for pull_request event: Last merge commit on the GITHUB_REF branch
        # GITHUB_SHA for push event: Commit pushed, unless deleting a branch (when it's the default branch)
        # https://git.io/JvUfd
        github_sha = os.environ["GITHUB_SHA"]
        ci_params = {
            "provider": "github",
            "repo_slug": repo_slug,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "commit": github_sha,
            "triggering_commit": os.getenv("GITHUB_PULL_REQUEST_SHA") or github_sha,
            "build_url": f"https://github.com/{repo_slug}/commit/{github_sha}/checks",
            "job_url": f"https://github.com/{repo_slug}/runs/{action_id}",
        }
        return ci_params

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

    if os.getenv("CI", "false").lower() == "true":
        logging.warning(
            "Detected CI environment variable, but get_continuous_integration_parameters "
            "did not detect environment variables for a supported CI provider. "
            "Supported providers are: {}".format(", ".join(supported_providers))
        )
    return None
