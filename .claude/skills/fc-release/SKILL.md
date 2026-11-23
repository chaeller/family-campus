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
  and committed (`campus-image.sh` refuses otherwise). Its notes for learners come
  with the version – nothing to copy.

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
   include (`git -C my-family status --porcelain`). Options: carry out the release /
   cancel. Anything but the first option: stop.
2. If my-family is its own repository: `git -C my-family add -A && git -C my-family commit -m "<what changed>"`
   – with the attribution lines the session asks for; check first that
   `git -C my-family status` lists nothing from material folders, `data/` or secrets
   (`.env`, `campus.env`). Then `git -C my-family push` (if it has a remote).
3. `tools/campus-image.sh`, then push `$FC_IMAGE:<version>-<date>` and `:latest`.
4. Report what was done (commit, image tag and digest) and ask whether to install
   now (`/fc-deploy <version>-<date>`); do not deploy without that answer.

If a step fails, stop and report the exact error. Never force-push, never
`git reset`, never rewrite history – ask the user.

Without `--run`, never commit, push or build the release image unless the user
explicitly asks for that step.
