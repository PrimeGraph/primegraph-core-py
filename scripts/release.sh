#!/bin/sh
# Release the primegraph-core distribution.
#
# Usage: sh scripts/release.sh <semver>       e.g. sh scripts/release.sh 1.4.0
#
# The argument is a bare semver with no leading "v"; the git tag gets the "v".
# This pipeline has no PyPI: consumers install straight from the git tag, e.g.
#   primegraph-core = { git = "https://github.com/PrimeGraph/primegraph-core-py.git", tag = "v1.4.0" }
# so the release bumps pyproject.toml and tags — there is no upload step. Every
# check that can fail runs before anything is mutated.

set -eu

usage() {
  echo "Usage: sh scripts/release.sh <semver>   (bare semver, no leading 'v')" >&2
  exit 1
}

[ "$#" -eq 1 ] || usage
VERSION="$1"

SEMVER_RE='^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$'
if ! printf '%s' "$VERSION" | grep -Eq "$SEMVER_RE"; then
  echo "release: '$VERSION' is not a bare semver (expected 1.4.0, not v1.4.0)" >&2
  exit 1
fi
TAG="v$VERSION"

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO_ROOT"

# --- preflight --------------------------------------------------------------

DEFAULT_BRANCH=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)
[ -n "$DEFAULT_BRANCH" ] || DEFAULT_BRANCH=main

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "$DEFAULT_BRANCH" ]; then
  echo "release: on branch '$CURRENT_BRANCH', releases are cut from '$DEFAULT_BRANCH' only" >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "release: the working tree is dirty, commit or stash first" >&2
  git status --short >&2
  exit 1
fi

if git rev-parse --verify --quiet "refs/tags/$TAG" >/dev/null; then
  echo "release: tag $TAG already exists locally, nothing was changed" >&2
  exit 1
fi

if [ -n "$(git ls-remote --tags origin "refs/tags/$TAG")" ]; then
  echo "release: tag $TAG already exists on origin, nothing was changed" >&2
  exit 1
fi

git fetch --quiet origin "$DEFAULT_BRANCH"
if [ "$(git rev-parse HEAD)" != "$(git rev-parse "origin/$DEFAULT_BRANCH")" ]; then
  echo "release: HEAD and origin/$DEFAULT_BRANCH differ, pull or push first" >&2
  exit 1
fi

if ! command -v poetry >/dev/null 2>&1; then
  echo "release: poetry is not on PATH" >&2
  exit 1
fi

# --- version, build ---------------------------------------------------------

echo "release: preparing $TAG"
poetry version "$VERSION"
poetry check
poetry build

# --- commit, tag, push ------------------------------------------------------

git add pyproject.toml
git commit -m "chore(release): $TAG"
git tag -a "$TAG" -m "$TAG"
git push origin "$DEFAULT_BRANCH"
git push origin "$TAG"

echo "release: tagged $TAG; consumers pin it with"
echo "  primegraph-core = { git = \"https://github.com/PrimeGraph/primegraph-core-py.git\", tag = \"$TAG\" }"
