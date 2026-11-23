---
name: fc-release
argument-hint: "[--run]"
description: Family Campus – prepare a release of my-family. my-family has no version of its own (ADR-0018) – the site shows the Family Campus version and the date of the content. Checks what changed since the image that runs, makes sure every new or improved tile carries date / updated / note in tiles.json (that is "What's new?"), checks the Family Campus version in deploy.env and runs the checks. Without --run it hands over the exact commands (commit, push, image build, image push); with --run (explicit request) it asks for confirmation in the chat and then carries them out. Use when the user wants to release, prepare a release or asks what goes into the next one.
---

# fc-release – prepare (and with --run: carry out) a release of my-family

**Where:** Claude Code runs in the Family Campus folder. my-family is `my-family/` (or
`$FC_CAMPUS`, or the folder the user names); paths below such as `campus.json`,
`tiles/`, `tiles.json`, `deploy.env`, `material/` are relative to it, `tools/…` and
`sources/…` are Family Campus's. Git commands about my-family run in my-family
(`git -C my-family …`) and only if it is its own repository – never put family
data into Family Campus's git.

Read ADR-0018 (one version, dated content) and ADR-0011 (Family Campus and
my-family). Values come from `deploy.env` (`set -a; . my-family/deploy.env; set +a`).

**Arguments:** `$ARGUMENTS` – optionally `--run`: the user's explicit request to
carry out the release (step 4); without it only hand over the commands (step 3).

## 1. What has changed?

- The image that runs: its labels `family-campus.commit` (my-family commit) and
  `family-campus.app-version` – from `docker image inspect` on the server
  (`FC_HOST`, read-only) or locally; otherwise ask.
- Changes that reach the site since that commit:
  `git -C my-family diff --name-only <commit> -- tiles tiles.json campus.json exams.json locales curricula.md deploy.env`
  plus uncommitted and untracked files there (without a repository of its own:
  ask the user what changed). Read the diffs, not only the file names.
- **Family Campus:** `FC_APP_VERSION` in `deploy.env` and the Family Campus
  checkout (this folder): its `VERSION` must match, its working tree must be clean
  and committed, and if the tag `v<VERSION>` exists, `HEAD` must be on it
  (`campus-image.sh` refuses otherwise). Its notes for learners come with the
  version – nothing to copy. Check all of it now (`git status --porcelain`,
  `git describe --tags --exact-match`, `git log v<VERSION>..HEAD`):
  - all clean and `HEAD` on `v<FC_APP_VERSION>` → nothing to do;
  - **changes in Family Campus** (uncommitted, or commits after its tag) → a
    **Family Campus version comes first** (step 1b); the my-family release waits
    for it.
- **Same name twice:** the release is named `<FC_APP_VERSION>-<content date>`. If
  the running image already has that name (same Family Campus version, my-family
  committed on the same day), the new image would overwrite its tag – only with a
  new Family Campus version or on another day the name is new. Say so.

## 1b. Family Campus has changes: its version first

Propose the next version (patch for fixes, minor for new features, per
`CHANGELOG.md`) and **prepare** – only files, no git – following
`docs/operations.md` ("Releasing Family Campus"):

- `VERSION`: new version and today's date (two lines);
- `CHANGELOG.md`: a section `## <version> – <date>` below "Unreleased" with the
  changes (for developers, English);
- `release-notes.json`: a new first entry of `"versions"` with short notes for
  learners in `en` and `de` (what they notice; empty `"unreleased"` afterwards);
- `my-family/deploy.env`: `FC_APP_VERSION=<version>`;
- run `python3 tools/check_i18n.py`, `python3 tools/build.py` (example family) and
  `tools/campus-build.sh`.

The order of the commands matters – hand them over exactly so (Family Campus
before my-family, because the image needs both committed):

```bash
# 1. Family Campus (this folder) – version files are part of the same commit
tools/publish_check.sh --deny <private word list outside the repo>
git add -A && git commit -m "Family Campus <version>: <what changed>"
git tag -a v<version> -m "Family Campus <version>"
git push && git push origin v<version>
# 2. my-family – content and FC_APP_VERSION in one commit
git -C my-family add -A && git -C my-family commit -m "<what changed>; Family Campus <version>" && git -C my-family push
# 3. image
tools/campus-image.sh
docker push $FC_IMAGE:<version>-<date> && docker push $FC_IMAGE:latest
```

Then ask whether a **GitHub release** should be created for `v<version>` (not
every version gets one; command in `docs/operations.md`). Only after a yes.

## 2. Fill the gaps and check

- Every **new** tile has `date` (the day it was added). Every **improved** tile
  whose change learners notice has `updated` (today) and a short `note` in the
  tile's language or per locale ("Mehr Bilder", "Lösung in Set 3 korrigiert"; no
  names, no technical terms). Add what is missing; corrections nobody notices need
  no note. New exams alone need nothing.
- Run `tools/campus-build.sh` and the checks of `fc-check` that matter for a
  release. Stop on a failing check.
- The release will be named `<FC_APP_VERSION>-<date of the content>`; the date is
  the date of my-family's commit (with a repository of its own), else today.

## 3. Without --run: hand over

Show the new and improved tiles ("What's new?"), the name of the release and
these commands:

```bash
# if my-family/ is its own git repository:
git -C my-family add -A && git -C my-family commit -m "<what changed>" && git -C my-family push
tools/campus-image.sh                         # → $FC_IMAGE:<version>-<date> and :latest
docker push $FC_IMAGE:<version>-<date> && docker push $FC_IMAGE:latest
```

Then: "Install with `/fc-deploy <version>-<date>`."

## 4. With --run: carry out the release

1. **Confirm in the chat** with AskUserQuestion, standing on its own: the name of
   the release, the new and improved tiles with their notes, the files that reach
   the site, and every other uncommitted file that `git -C my-family add -A` would
   include (`git -C my-family status --porcelain`). With a Family Campus version
   (step 1b) also: its version, its changed files and that it will be committed,
   tagged and pushed to its public remote. Options: carry out the release /
   cancel. Anything but the first option: stop.
2. Only with a Family Campus version (1b): `tools/publish_check.sh --deny <list>`
   (ask the user for the path of the private word list if it is not known; stop on
   any finding), then commit, `git tag -a v<version>`, push the branch and the tag
   – in that order, before my-family.
3. If my-family is its own repository: `git -C my-family add -A && git -C my-family commit -m "<what changed>"`
   – with the attribution lines the session asks for; check first that
   `git -C my-family status` lists nothing from material folders, `data/` or secrets
   (`.env`, `campus.env`). Then `git -C my-family push` (if it has a remote).
4. `tools/campus-image.sh`, then push `$FC_IMAGE:<version>-<date>` and `:latest`.
5. Report what was done (commits, tag, image tag and digest), ask about a GitHub
   release if a Family Campus version was tagged, and ask whether to install
   now (`/fc-deploy <version>-<date>`); do not deploy without that answer.

If a step fails, stop and report the exact error. Never force-push, never
`git reset`, never rewrite history – ask the user.

Without `--run`, never commit, push or build the release image unless the user
explicitly asks for that step.
