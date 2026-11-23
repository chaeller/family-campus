# Shared by the campus-*.sh scripts (sourced, not run): finds the my-family folder and loads its deploy.env.
# my-family is a folder with campus.json – usually my-family/ in the Family Campus checkout (ignored by Family Campus's git).
# Order: the folder given as argument, $FC_CAMPUS, the current folder (if it has campus.json), <Family Campus>/my-family.
APP=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

fc_campus_dir() {
  local d=${1:-${FC_CAMPUS:-}}
  if [[ -z $d ]]; then
    if [[ -f campus.json ]]; then d=.
    elif [[ -f $APP/my-family/campus.json ]]; then d=$APP/my-family
    fi
  fi
  [[ -n $d && -f $d/campus.json ]] || {
    echo "No my-family found (a folder with campus.json). Create it with tools/new-campus.sh, or pass its folder." >&2; exit 1; }
  (cd "$d" && pwd -P)
}

# enter my-family folder and load deploy.env (no secrets in it)
fc_enter_campus() {
  cd "$(fc_campus_dir "${1:-}")"
  [[ -f deploy.env ]] || { echo "$(pwd)/deploy.env is missing (see docs/getting-started.md)" >&2; exit 1; }
  set -a; . ./deploy.env; set +a
}

# true if my-family folder is the top of its own git repository; inside the Family Campus checkout git would
# otherwise answer with Family Campus's history, tags and status
fc_own_git() { [[ "$(git rev-parse --show-toplevel 2>/dev/null)" == "$(pwd -P)" ]]; }
