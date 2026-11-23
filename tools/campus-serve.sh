#!/usr/bin/env bash
# Runs my-family locally after tools/campus-build.sh: Family Campus's server with the built site,
# logins from <campus>/data/campus.env and the database in <campus>/data/ (both never committed).
#   tools/campus-serve.sh [campus dir] [--port 8080]
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib-campus.sh"
DIR=""; PORT=8080
while [[ $# -gt 0 ]]; do case $1 in --port) PORT=$2; shift 2 ;; *) DIR=$1; shift ;; esac; done
fc_enter_campus "$DIR"
[[ -f build/www/index.html ]] || { echo "Build first: tools/campus-build.sh" >&2; exit 1; }
[[ -f data/campus.env ]] || { echo "$(pwd)/data/campus.env with the logins is missing (see docs/getting-started.md)" >&2; exit 1; }
echo "Open http://localhost:$PORT${FC_PREFIX%/}/   (stop with Ctrl+C)"
FC_PREFIX=$FC_PREFIX exec python3 "$APP/server/server.py" --www build/www --data data --port "$PORT"
