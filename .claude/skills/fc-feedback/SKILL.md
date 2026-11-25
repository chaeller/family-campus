---
name: fc-feedback
argument-hint: "[--local <data dir>]"
description: Family Campus – work through the questions learners reported on my-family's live site (🚩 "Something wrong with this question?"). Fetches the reports read-only from the running container into my-family's feedback.json, analyses each one against the tile and the engine, fixes the tile (with fc-improve's rules) or Family Campus's engine, or records why no change is needed, and marks every report as handled. Use when the user asks to look at, fetch or process reports, complaints or feedback on questions, or starts /fc-feedback. Never commits, releases or deploys.
---

# fc-feedback – process reported questions

**Where:** Claude Code runs in the Family Campus folder. my-family is `my-family/` (or
`$FC_CAMPUS`, or the folder the user names); paths below such as `campus.json`,
`tiles/`, `tiles.json`, `deploy.env`, `feedback.json` are relative to it, `tools/…`
are Family Campus's. Git commands about my-family run in my-family
(`git -C my-family …`) and only if it is its own repository – never put family data
into Family Campus's git.

Read ADR-0019 (reporting questions) and ADR-0005 of Family Campus, my-family's
`campus.json` and Family Campus's `CLAUDE.md` ("Working on my-family's content").
Talk to the user in the language of my-family's `defaultLocale`.

**Arguments:** `$ARGUMENTS` – optional `--local <data dir>` to read a local
database (testing) instead of the live instance.

## 1. Fetch

```bash
tools/campus-feedback.sh              # live: ssh $FC_HOST, docker exec $FC_CONTAINER, read-only
tools/campus-feedback.sh --local my-family/data   # a local database
```

The script adds new reports to `feedback.json` and keeps the `handled` field of
reports already in it. Never write to the live database; never print logins.
`feedback.json` holds names and the learners' own words: it stays in my-family,
never in Family Campus's files, issues or commit messages.

## 2. Analyse – every report with `"handled": null`

Each report has the tile (`exercise`), set (`set_id`), the question exactly as
shown (`q`, also for generated questions), the answer given (`given`, read from
the screen – may be empty), whether the engine rated it right (`ok`, `null` =
reported before answering), the reason, the learner's `note` and the release it
was made in (`build`). Group reports on the same question (`qkey`).

For each one decide, and check it yourself (solve the question, look at the
module in `tiles/`, the engine in `engine/quiz.html`, the source the summary
sheet names):

| Finding | What to do |
|---|---|
| The solution or the question in the tile is wrong or unclear, a correct answer is not accepted (`rightAnswer`: add it to `a`), a typo | Fix the tile with **fc-improve**'s rules (steps 2–4: set ids stay, content language, `updated` + `note` in `tiles.json`) |
| The engine rates or shows it wrongly (checking, typo tolerance, order, layout) | Fix Family Campus (engine, tools), with its `CHANGELOG.md` line and – if learners notice it – a note in `release-notes.json` |
| The question is right; the learner was mistaken | No change. If the summary sheet could prevent the mistake, improve it (fc-improve) |
| A wish for harder or more questions | A new set with a higher `tier` (ADR-0020) in that tile, with fc-improve's rules; ask first if it should cover more tiles |
| Unclear what is meant, or the answer depends on material you do not have | Ask the user; leave `handled` empty |

Generated questions: fix the generator, not the one instance; check a few
generated instances afterwards.

## 3. Record

Set `handled` on every processed report in `feedback.json`:

```json
"handled": {"date": "YYYY-MM-DD", "outcome": "tile | engine | no-change", "what": "short description of the fix or the reason"}
```

Then `tools/campus-build.sh` (self test, de-CH check) must pass. The build takes the
handled reports into `build.json`; the release carrying them ends their flags (ADR-0019),
so `feedback.json` is committed in my-family together with the fix. A report already
fixed by an earlier change is `no-change` with that reason.

## 4. Report

Per report: tile, question, reason, verdict and what changed. Say that the 🚩 flags
of the handled reports disappear when the next release is installed (`fc-release`, then
`fc-deploy`); reports not handled – or made after this fetch – stay flagged and can be
skipped until a later release handles them.
Do not commit, release or deploy.
