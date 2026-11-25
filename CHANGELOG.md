# Changelog

All notable changes to Family Campus are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- Difficulty of sets (ADR-0020): a set may carry `tier: 2, 3, …`; it is shown with a ◆◆ badge
  and stays locked (🔒, greyed out) until every set of the next lower tier of the tile reached
  80 % in a whole run – retry rounds and the repetition box do not count. The conditions are in
  the badge's tooltip and appear below the set when it is tapped; the result of a run names the
  sets it opened. `GET /api/progress` and `POST /api/result` return `full` (best result of whole
  runs) per set; the self test checks `tier`; `fc-improve` and `fc-feedback` use it for harder sets.

### Changed

- A 🚩 flag now ends with the release in which its report was handled, not with any next
  release (ADR-0019): `tools/build.py` writes the handled reports of my-family's
  `feedback.json` (`id@time` only) into `build.json`, the server flags every other report.
  Reports not processed yet – or made after the last fetch – stay flagged across releases. The
  parents' list shows the open reports and folds the handled ones away. The build prints a
  note with the number of reports not handled yet; `fc-release` reports them without blocking; `fc-feedback`, ADR-0019 and the docs follow.
- Reporting a question: typing a comment without picking a reason selects "Something else", so the
  report can be sent; the reason can still be changed.

## 1.1.0 – 2026-11-24

### Added

- Learners can report a question (ADR-0019): "🚩 Something wrong with this question?" before
  answering or in the feedback box, with a quick reason (wrong solution, my answer was right,
  unclear, typo, something else) and an optional comment. A reported question counts neither as
  right nor as wrong and does not go into the repetition box; while the same release runs it is
  flagged for everybody and can be skipped. New table `feedback`, `POST /api/report`,
  `GET /api/reports` (parents only), `flags` in `GET /api/progress`; the engine sends an answer
  when the learner goes on instead of at once. Parents see the reports on the progress page.
- `tools/campus-feedback.sh` fetches the reports read-only from the running container (or a local
  database) into my-family's `feedback.json` (`tools/feedback_export.py`); the skill `fc-feedback`
  analyses and fixes them and records how each was handled.
- GitHub Actions workflow `checks` (`.github/workflows/checks.yml`): on every push and pull request
  the server compiles, the i18n and de-CH checks run, the example family is built and every tile
  passes the self test in headless Chromium (Google Chrome on the runner – its chromium snap
  cannot read the test page in /tmp). The private word check stays local (`publish_check.sh`).
- Dependabot (`.github/dependabot.yml`): monthly updates of the Docker base image and of the GitHub
  Actions; Family Campus has no package dependencies.
- CI: `actions/checkout` and `actions/setup-python` updated to v7 (Dependabot #1, #2).

### Changed

- `fc-release` detects changes in Family Campus (uncommitted, or commits after its tag) and prepares
  the next version before the my-family release; it hands over the commands in the order the image
  needs (Family Campus commit, tag and push, then my-family, then the image), warns when a release
  name would repeat and asks before creating a GitHub release. `docs/operations.md` describes the
  order for changes in both.
- `tools/publish_check.sh` has two modes: without options it checks a push (private words, secrets,
  build, tests – entries under "Unreleased" are allowed); `--release` additionally refuses unreleased
  entries in `CHANGELOG.md` and `release-notes.json`. `fc-release` and `docs/operations.md` use
  `--release`.
- `tools/campus-image.sh` builds with `docker build --pull`: every image gets the current patch level
  of the base image instead of a cached one.
- Base image `python:3.13-alpine` → `python:3.15-alpine` (Dependabot #3); the CI checks run on Python
  3.15 as well. Tested: the example family builds, the server starts and answers `healthz`.

### Fixed

- `tools/publish_check.sh` ran the self test only when Playwright was installed, although
  `tools/selftest.py` needs only the `chromium` command – the self test was skipped. It now runs
  whenever `chromium` is found.
- Sort questions (`t:"sort"`, tap a category per item) showed the items in the order the set listed
  them – most sets list them per category, so the answers were always e.g. left, left, right, right.
  The engine now shuffles the items every time the question is shown.

## 1.0.1 – 2026-11-23

### Fixed

- Language before login: the browser's languages are matched in their order – per language the exact
  tag, then the same language. `de-DE, de, en` on a `de-CH`/`en` campus now gives `de-CH`, not `en`.
- Built pages start with `<html lang>` set to the campus default and list the offered locales;
  `i18n.js` sets the page language before anything is loaded, so browsers no longer offer to
  translate a page that is already in the reader's language.

## 1.0.0 – 2026-11-22

First public release.

- Tiles built from one quiz engine and content modules: summary sheet, short sets, question types
  multiple choice, typed answers (with typo tolerance), tables, matching, ordering, tapping words,
  sorting; generated questions; extensions for extra question types and summary-sheet widgets
- Login per person (logins in the data volume), parents see everyone's progress
- Spaced repetition (Leitner box: 1, 3, 7, 14, 30 days), progress page with activity, sets, recent
  runs and mistakes
- Home page with filters (person, category, field, level, subject), upcoming exams with learning
  goals, revision and a focus list per person
- Content by category → area → level, with "up to my level" and level-only areas
- Languages and locales: English (default), German (Germany) and Swiss German; per-person choice;
  dates, numbers and plurals via `Intl`; right-to-left prepared; content language badge on tiles
- Family Campus and my-family: `tools/build.py` merges a family's private folder `my-family/` into
  one site; an invented example family (`example-family/`); build, image and release scripts for my-family
- One version (Family Campus); the content of my-family is dated: the footer shows "Family Campus
  <version> · content of <date>", "What's new?" lists new and improved tiles (`date`, `updated`,
  `note` in `tiles.json`) and the notes of Family Campus for learners; images are tagged
  `<version>-<date>`
- Demo tile "Internet basics" with an interactive Prim's algorithm question
- Source modules (opt-in, local only): `sources/escola` fetches exams, learning goals and documents
  from the Swiss school platform Escola with a family's own parent account; `sources/moodle`
  fetches upcoming exams and assignments from Moodle with the learner's
  own account; rules for legal and responsible use
- my-family lives in `my-family/` of the Family Campus checkout (ignored by Family Campus's git; optionally its
  own git repository with its own remote): `tools/new-campus.sh` creates it from the example family,
  `campus-build.sh`, `campus-serve.sh` and `campus-image.sh` find it by
  themselves, the source modules too (`--campus <dir>` for another folder)
- Server with the Python standard library and SQLite; Docker image with a read-only root file
  system; installable as a web app
- Checks: self test of every tile, i18n catalogue check, ß check for de-CH content
- Skills for coding agents (`fc-ingest`, `fc-improve`, `fc-check`, `fc-release`, `fc-deploy`)
- Documentation: README, getting started, my-family reference, writing tiles, languages,
  architecture, operations, architecture decision records, contributing guide
