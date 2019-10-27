#!/usr/bin/env bash

## deploy-docs.sh: run during a Travis CI build to deploy docs directory to the gh-pages branch on GitHub.
## References
## - https://github.com/hetio/xswap/blob/ffbb933d1731c2ce4e4e24f00a9a909b53ddf75c/ci/deploy.sh
## - https://github.com/manubot/rootstock/blob/6859ada7a28a72cd0ed728e085955f23fadc2b9a/ci/deploy.sh
## - https://github.com/wp-cli/wp-cli/issues/3798
## - https://github.com/manubot/catalog/blob/fd0ef6a999cca38890023eb65f19d1b87e96e83c/deploy.sh#L1-L45

# Set options for extra caution & debugging
set -o errexit \
    -o nounset \
    -o pipefail

# Decrypt and add SSH key
eval "$(ssh-agent -s)"
(
  set +o xtrace  # disable xtrace in subshell for private key operations
  base64 --decode <<< "$GITHUB_PRIVATE_DEPLOY_KEY" | ssh-add -
)

# Configure git
git config --global push.default simple
git config --global user.name "Travis CI"
git config --global user.email "deploy@travis-ci.com"
git checkout "$TRAVIS_BRANCH"
git remote set-url origin "git@github.com:$TRAVIS_REPO_SLUG.git"

# Fetch and create gh-pages branch
# Travis does a shallow and single branch git clone
git remote set-branches --add origin gh-pages
git fetch origin gh-pages:gh-pages

commit_message="\
Generate docs on $(date --iso --utc)
[skip ci]

built by $TRAVIS_JOB_WEB_URL
based on https://github.com/$TRAVIS_REPO_SLUG/commit/$TRAVIS_COMMIT
"
# echo >&2 "$commit_message"

ghp-import \
  --push --no-jekyll \
  --message="$commit_message" \
  docs
