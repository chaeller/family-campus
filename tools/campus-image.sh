#!/usr/bin/env bash
# Builds the Docker image of my-family: the server of Family Campus, its VERSION and the site built by
# campus-build.sh. Image name and URL path from my-family's deploy.env. One version (ADR-0018): the image
# is tagged <FC_APP_VERSION>-<date of the content>, e.g. 1.0.0-2026.11.22, and :latest.
#   tools/campus-image.sh [--dev] [my-family dir]   (default: my-family/, see lib-campus.sh)
#   release build: a clean Family Campus checkout at FC_APP_VERSION (on its tag once it has one); if
#                  my-family is its own git repository, everything committed – the content date is the
#                  date of its last commit, the commit is recorded in a label
#   --dev        test build of the working trees, tagged :dev only; the footer says "test version"
# Never pushes; prints the push commands.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib-campus.sh"
DEV=0; [[ "${1:-}" == "--dev" ]] && { DEV=1; shift; }
fc_enter_campus "${1:-}"
REPO=$FC_IMAGE
fail() { echo "campus-image: $*" >&2; echo "Commit first, or use --dev for a test build." >&2; exit 1; }

if [[ $DEV == 0 ]]; then
  if fc_own_git; then   # with its own git repository: everything committed
    git rev-parse -q --verify HEAD >/dev/null || fail "my-family has no commit yet"
    [[ -z $(git status --porcelain) ]] || fail "my-family has uncommitted changes"
  fi
  # Family Campus must be exactly the version named in deploy.env, committed (tagged once it is published)
  [[ -z $(git -C "$APP" status --porcelain) ]] || fail "Family Campus in $APP has uncommitted changes"
  git -C "$APP" rev-parse -q --verify HEAD >/dev/null || fail "Family Campus in $APP has no commit yet"
  if git -C "$APP" rev-parse -q --verify "refs/tags/v$FC_APP_VERSION" >/dev/null; then
    [[ $(git -C "$APP" rev-parse "v$FC_APP_VERSION^{commit}") == $(git -C "$APP" rev-parse HEAD) ]] || fail "Family Campus is not on its tag v$FC_APP_VERSION"
  fi
fi

FC_DEV=$DEV "$APP/tools/campus-build.sh" .
read -r CONTENT COMMIT < <(python3 -I -c 'import json; b=json.load(open("build/www/build.json")); print(b["content"], b["commit"] or "-")')
TAG="$FC_APP_VERSION-${CONTENT//-/.}"
# build context: the server and VERSION of Family Campus, the built site
CTX=build/image
rm -rf "$CTX"; mkdir -p "$CTX/server"
cp "$APP/server/server.py" "$CTX/server/"
cp "$APP/VERSION" "$CTX/VERSION"
cp -r build/www "$CTX/www"
APPREF="$FC_APP_VERSION ($(git -C "$APP" rev-parse --short HEAD 2>/dev/null || echo uncommitted))"
ARGS=(--build-arg FC_PREFIX="$FC_PREFIX" --build-arg APP_VERSION="$APPREF" --build-arg CONTENT_DATE="$CONTENT" --build-arg COMMIT="$COMMIT")
if [[ $DEV == 1 ]]; then
  docker build -f "$APP/Dockerfile" "${ARGS[@]}" --tag "$REPO:dev" "$CTX"
  echo; echo "Built $REPO:dev (Family Campus $APPREF, content $CONTENT, test version). Not for release."
  echo "Push:  docker push $REPO:dev"
else
  docker build -f "$APP/Dockerfile" "${ARGS[@]}" --tag "$REPO:$TAG" --tag "$REPO:latest" "$CTX"
  echo; echo "Built $REPO:$TAG and :latest (Family Campus $APPREF, content $CONTENT, my-family commit $COMMIT)."
  echo "Push:  docker push $REPO:$TAG && docker push $REPO:latest"
  echo "Then deploy with /fc-deploy $TAG."
fi
