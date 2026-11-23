# Changelog

All notable changes to Family Campus are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/).

## Unreleased

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
