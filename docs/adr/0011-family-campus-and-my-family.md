# ADR-0011: Family Campus and my-family

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Family Campus is open source; each family has its own people, exams, own
tiles and server. Their data must never end up in the public repository,
and families must be able to update Family Campus without losing their
content.

## Decision

- This repository is **Family Campus**: server, pages, quiz engine, build
  and release tools, skills, source modules, documentation, a demo tile and
  an invented example family (`example-family/`).
- Each family keeps everything of its own in the folder **`my-family/`** of
  its Family Campus checkout: `campus.json` (name, URL path, locales,
  currency, categories, areas, levels, people with colours, subjects),
  `exams.json`, own tiles (`tiles.json`, `tiles/`), own texts (`locales/`),
  release notes and deployment values. The `.gitignore` of Family Campus
  excludes the folder; families work in one place and update Family Campus
  with `git pull`.
- A family that wants a backup or history makes `my-family/` **its own git
  repository** with its own private remote; it stays independent of the
  the Family Campus repository. Release tags and the "committed" checks apply
  only then. (The folder may also live elsewhere: `--campus`/`FC_CAMPUS`.)
- The tools find `my-family/` by themselves (`tools/lib-campus.sh`); the
  skills run in the Family Campus folder. `my-family/` has no rules of its
  own (no `CLAUDE.md`): its values are `campus.json` and `deploy.env`, the
  rules are those of Family Campus.
- `tools/build.py <folder>` merges Family Campus and `my-family/` into one
  site at build time; the image contains both. `my-family/` names the
  the Family Campus version it is built with (`FC_APP_VERSION`).
- `my-family/` may leave out the demo tile of Family Campus (`appTiles: false`).

## Consequences

+ Family Campus can be published and updated independently of any family's data.
+ A new exam or tile needs a new build of `my-family/`, not of Family Campus.
+ One place to work; no paths between repositories, no links for the skills.
− my-family names the Family Campus version it is built with (`FC_APP_VERSION` in
  `deploy.env`) and must follow updates (ADR-0018: one version, dated content).
− The family's data sits inside the Family Campus checkout: only the
  `.gitignore` keeps it out of the Family Campus repository
  (`tools/publish_check.sh` checks it before publishing).

## Alternatives considered

- **Family data in the Family Campus repository:** cannot be published.
- **`my-family/` as a separate repository next to Family Campus:** two
  places to work, a path to Family Campus in `deploy.env` and a link for the
  skills; harder to start with (tried before 1.0.0 and dropped).
- **Family data loaded at run time from the volume:** fewer images, but a
  second way to deploy data; possible later.
