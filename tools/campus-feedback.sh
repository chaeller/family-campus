#!/usr/bin/env bash
# Fetches the reported questions (ADR-0019) of my-family's live instance into <campus>/feedback.json,
# read-only: the export runs inside the running container ($FC_CONTAINER on $FC_HOST, from deploy.env).
# New reports are added; reports already in the file keep what fc-feedback recorded ("handled").
#   tools/campus-feedback.sh [campus dir] [--local <data dir>]   (--local: a local database, e.g. data/)
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib-campus.sh"
DIR=""; LOCAL=""
while [[ $# -gt 0 ]]; do case $1 in --local) LOCAL=$2; shift 2 ;; *) DIR=$1; shift ;; esac; done
[[ -n $LOCAL ]] && LOCAL=$(cd "$LOCAL" && pwd -P)
fc_enter_campus "$DIR"
TMP=$(mktemp); trap 'rm -f "$TMP"' EXIT
if [[ -n $LOCAL ]]; then
  python3 "$APP/tools/feedback_export.py" "$LOCAL/campus.sqlite" > "$TMP"
else
  : "${FC_HOST:?FC_HOST missing in deploy.env}" "${FC_CONTAINER:?FC_CONTAINER missing in deploy.env}"
  ssh -o BatchMode=yes "$FC_HOST" "sudo -n docker exec -i $FC_CONTAINER python3 - /data/campus.sqlite" \
    < "$APP/tools/feedback_export.py" > "$TMP"
fi
python3 - "$TMP" feedback.json <<'PY'
import json, os, sys, datetime as dt
new = json.load(open(sys.argv[1], encoding="utf-8"))
path = sys.argv[2]
old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"reports": []}
known = {(r["id"], r["ts"]): r for r in old["reports"]}
added = 0
for r in new:
    k = (r["id"], r["ts"])
    if k in known: r["handled"] = known[k].get("handled")
    else: r["handled"] = None; added += 1
    known[k] = r
reports = sorted(known.values(), key=lambda r: r["ts"])
out = {"fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "reports": reports}
with open(path, "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False, indent=1); f.write("\n")
todo = sum(1 for r in reports if not r.get("handled"))
print(f"{os.path.abspath(path)}: {len(reports)} reports, {added} new, {todo} not handled yet")
PY
