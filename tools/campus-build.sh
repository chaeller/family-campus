#!/usr/bin/env bash
# Builds the site of my-family from Family Campus and my-family into <campus>/build/www, then runs
# the checks: self test of every tile, no ß in de-CH content (ADR-0012).
#   tools/campus-build.sh [campus dir]     (default: my-family/ of Family Campus, or the current folder if it has campus.json)
# my-family's deploy.env names the Family Campus version it expects (FC_APP_VERSION). The footer shows that
# version and the date of my-family's content (ADR-0018).
# Local test afterwards: tools/campus-serve.sh (logins in <campus>/data/campus.env, database in <campus>/data/)
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib-campus.sh"
fc_enter_campus "${1:-}"
APPV=$(sed -n 1p "$APP/VERSION")
[[ $APPV == "$FC_APP_VERSION" ]] || { echo "build: Family Campus in $APP is $APPV, deploy.env wants $FC_APP_VERSION – after updating Family Campus set FC_APP_VERSION=$APPV in deploy.env" >&2; exit 1; }
# date of the content (ADR-0018): the date of my-family's last commit; with uncommitted changes or without a
# git repository of its own: today. "test version" in the footer only for test images (FC_DEV=1 from
# campus-image.sh --dev) – a local preview needs no hint.
DEV=""; COMMIT=""; CDATE=$(date +%F)
if fc_own_git && git rev-parse -q --verify HEAD >/dev/null; then
  COMMIT=$(git rev-parse --short HEAD)
  [[ -n $(git status --porcelain) ]] || CDATE=$(git log -1 --format=%cs)
fi
[[ ${FC_DEV:-} == 1 ]] && DEV=--dev
python3 "$APP/tools/build.py" . --out build/www --content-date "$CDATE" --commit "$COMMIT" $DEV
PROBLEMS=$(python3 "$APP/tools/selftest.py" build/www/exercises/*/index.html | grep -v "no problems" || true)
[[ -z $PROBLEMS ]] || { echo "$PROBLEMS"; echo "build: self test failed" >&2; exit 1; }
echo "Self test: all tiles OK."
# de-CH writes ss, never ß – in texts and in accepted answers (ADR-0012)
python3 "$APP/tools/check_de_ch.py" .
