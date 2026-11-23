#!/usr/bin/env bash
# Checks the Family Campus repository before it is pushed (every push) or released (--release):
# - every file that would be committed (tracked + untracked, not ignored) is free of private words,
#   secrets, databases, material folders and build output;
# - LICENSE, README.md, CHANGELOG.md with a section for VERSION; release-notes.json starts with VERSION
#   (notes for learners in en and de); with --release also nothing left under "Unreleased" in either –
#   between two versions the changes are recorded there and may be pushed;
# - the example family builds, the i18n catalogues are complete, the server compiles,
#   and the tiles pass the self test (if chromium is installed).
# Private words (names of your family, domains, servers …) come from a file that is NOT part of the
# repository, one word or phrase per line, # for comments:
#   tools/publish_check.sh [--release] [--deny <file>]   default list: $FC_PUBLISH_DENY or .publish-deny
#   --release   before tagging a version (fc-release): the version has taken over all unreleased entries
# Lines of LICENSE (the copyright holder) are not checked against the private words.
set -euo pipefail
cd "$(dirname "$0")/.."
DENY=${FC_PUBLISH_DENY:-.publish-deny}; RELEASE=0
while [[ $# -gt 0 ]]; do case $1 in
  --deny) DENY=$2; shift 2 ;;
  --release) RELEASE=1; shift ;;
  *) echo "usage: $0 [--release] [--deny <file>]" >&2; exit 2 ;;
esac; done
PROBLEMS=0
fail() { echo "PROBLEM: $*"; PROBLEMS=$((PROBLEMS+1)); }

mapfile -t FILES < <(git ls-files --cached --others --exclude-standard | sort -u)
echo "Files to publish: ${#FILES[@]}"

# 1. what must never be published
for f in "${FILES[@]}"; do
  case "$f" in
    .env.example) grep -qE '^[[:space:]]*[A-Z_]+=.+' "$f" && fail "values in the template (keep them commented): $f" ;;
    build/*|data/*|my-family/*|*.sqlite|*.sqlite-*|*campus.env|.env|.env.*) fail "must not be published: $f" ;;
    example-family/campus.env.example) ;;
  esac
done
for f in "${FILES[@]}"; do
  [[ -f $f ]] || continue
  grep -IlE -- "-----BEGIN [A-Z ]*PRIVATE KEY-----|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}" "$f" >/dev/null 2>&1 && fail "looks like a secret: $f"
done
# passwords: only the invented example family may have them
for f in "${FILES[@]}"; do
  [[ -f $f && $f != example-family/campus.env.example ]] || continue
  grep -IqE "^CAMPUS_PASSWORD_[A-Z]+=.+" "$f" 2>/dev/null && fail "password in $f"
done

# 2. private words
if [[ -f $DENY ]]; then
  mapfile -t WORDS < <(grep -vE '^\s*(#|$)' "$DENY")
  echo "Private words checked: ${#WORDS[@]} (from $DENY)"
  for w in "${WORDS[@]}"; do
    for f in "${FILES[@]}"; do
      [[ -f $f ]] || continue
      if [[ $f == LICENSE ]]; then continue; fi
      grep -IqiF -- "$w" "$f" 2>/dev/null && fail "private word \"$w\" in $f"
    done
  done
else
  fail "no list of private words ($DENY) – create it outside the repository or pass --deny <file>"
fi

# 3. version state (with --release: nothing unreleased)
[[ -f LICENSE ]] || fail "LICENSE missing"
[[ -f README.md ]] || fail "README.md missing"
V=$(sed -n 1p VERSION)
grep -q "^## $V " CHANGELOG.md || fail "CHANGELOG.md has no section for $V"
if [[ $RELEASE == 1 ]]; then
  [[ -z $(awk '/^## Unreleased/{f=1;next} /^## /{f=0} f && /^- /' CHANGELOG.md) ]] || fail "CHANGELOG.md has unreleased entries – move them into the section of $V"
fi
# release notes for learners (ADR-0018): the newest version is VERSION with en and de; --release: nothing unreleased
python3 -I -c 'import json,sys; rn=json.load(open("release-notes.json", encoding="utf-8")); v=(rn.get("versions") or [{}])[0]
sys.exit((sys.argv[2] == "1" and any(rn.get("unreleased", {}).values())) or v.get("version") != sys.argv[1] or not all(v.get("notes", {}).get(k) for k in ("en", "de")))' "$V" "$RELEASE" \
  || fail "release-notes.json: the first version must be $V with notes in en and de$([[ $RELEASE == 1 ]] && echo ', and "unreleased" must be empty')"

# 4. it works
python3 -m py_compile server/server.py || fail "server does not compile"
python3 tools/check_i18n.py >/dev/null || fail "i18n check (python3 tools/check_i18n.py)"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
python3 tools/build.py example-family --out "$TMP/www" >/dev/null || fail "the example family does not build"
if command -v chromium >/dev/null; then
  BAD=$(python3 tools/selftest.py "$TMP"/www/exercises/*/index.html | grep -v "no problems" || true)
  [[ -z $BAD ]] || fail "self test: $BAD"
else
  echo "note: chromium not found – self test skipped"
fi

MODE=push; [[ $RELEASE == 1 ]] && MODE=release
if [[ $PROBLEMS -eq 0 ]]; then echo "Publish check ($MODE): OK ($V)"; else echo "Publish check: $PROBLEMS problem(s)"; exit 1; fi
