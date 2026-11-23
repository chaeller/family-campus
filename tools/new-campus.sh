#!/usr/bin/env bash
# Creates my-family: the folder with your family's people, exams, tiles and deployment values,
# started from the example family. Never overwrites anything.
#   tools/new-campus.sh [folder] [--git]
#     folder   default: my-family/ in the Family Campus checkout (ignored by its git – updates with
#              'git pull' leave it alone)
#     --git    also make the folder its own git repository (for a backup on your own git server and
#              for releases with tags); you can also do that later with 'git init' in the folder
set -euo pipefail
APP=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DIR=""; GIT=0
for a in "$@"; do case $a in --git) GIT=1 ;; -h|--help) sed -n '2,9p' "$0"; exit 0 ;; *) DIR=$a ;; esac; done
DIR=${DIR:-$APP/my-family}
[[ ! -e $DIR ]] || { echo "$DIR already exists – nothing changed." >&2; exit 1; }
APPV=$(sed -n 1p "$APP/VERSION")

mkdir -p "$DIR"
cp -r "$APP/example-family/." "$DIR/"
cd "$DIR"
mkdir -p tiles data
mv campus.env.example data/campus.env && chmod 600 data/campus.env
printf '[]\n' > tiles.json
cat > deploy.env <<EOF
# Deployment values of this my-family (no secrets). See docs/operations.md.
FC_APP_VERSION=$APPV                       # the Family Campus version my-family is built with
FC_IMAGE=registry.example.org/family-campus  # Docker image (your registry)
FC_CONTAINER=family-campus
FC_VOLUME=family-campus
FC_HOST=server.example.org                 # ssh host for deployments
FC_PORT=8083
FC_PREFIX=/                                # URL path, e.g. /campus behind a reverse proxy
FC_PUBLIC_URL=https://campus.example.org/
EOF
cat > .gitignore <<'EOF'
# only relevant if this folder is its own git repository
build/
data/
*.env
!deploy.env
material*/
fotos/
EOF
mkdir -p material
cat > README.md <<'EOF'
# my-family – our part of Family Campus

The content and settings of our family's learning site. This folder is
`my-family/` in a clone of [Family Campus](https://github.com/chaeller/family-campus)
and is ignored by its git; as its own git repository it can be backed up on
our own git server. Everything else – server, pages, quiz engine, tools,
skills, source modules, documentation – belongs to Family Campus; all
commands run in the Family Campus folder.

| Path | Content |
| --- | --- |
| `campus.json` | People (colour, area, level, focus), categories, areas, levels, own subjects, languages |
| `exams.json` | Upcoming exams with learning goals |
| `tiles.json`, `tiles/` | Our tiles: catalogue entries (with `date`, and `updated`/`note` when improved – they make up "What's new?"), content modules, extensions, covers |
| `locales/` | Optional: our own texts per language (e.g. names of own subjects) |
| `curricula.md` | Optional: official curricula of our areas (where tiles belong) |
| `deploy.env` | App version, image, container, volume, server, port, URL path (no secrets) |
| `data/` | Logins (`campus.env`) and the local database – not in git |
| `material/` | Photos and documents for new tiles – not in git, never published |

How-to: `README.md` and `docs/` of Family Campus (start with `docs/getting-started.md`).
EOF
[[ $GIT == 1 ]] && git init -q && echo "git repository created in $(pwd)"

echo "my-family created in $(pwd) (from the example family, Family Campus $APPV)."
"$APP/tools/campus-build.sh" . >/dev/null && echo "Built and tested."
cat <<EOF

Next steps:
  Change only this folder from now on – example-family/ in Family Campus stays the demo.
  1. Edit campus.json: name, URL path, languages, categories, people (docs/my-family.md).
  2. Set the logins and passwords in data/campus.env (CAMPUS_USERS, CAMPUS_PASSWORD_<NAME>).
  3. curricula.md: replace the invented example with your areas' curricula, or delete it.
  4. Build and look at it:  tools/campus-build.sh && tools/campus-serve.sh
  5. Add tiles (docs/tiles.md) – or with Claude Code: /fc-ingest
  6. Deployment values in deploy.env, then docs/operations.md.
EOF
