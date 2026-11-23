# ADR-0018: One version – Family Campus; the content of my-family is dated

- **Status:** Accepted (supersedes ADR-0010)
- **Date:** 2026-11-22

## Context

ADR-0010 gave Family Campus and each my-family a version, a changelog and
release notes of their own. That meant two version numbers on one site,
two changelogs, and learner notes that mixed both: every family had to
copy the news of Family Campus into its own notes. Most changes of a
family are content – a new or improved tile – and that is already recorded
in `tiles.json`.

## Decision

- **Family Campus has the only version**: `VERSION` and `CHANGELOG.md`
  (Semantic Versioning, Keep a Changelog) and `release-notes.json` with
  notes for learners per locale (at least `en` and `de`). Every family gets
  them with the version.
- **my-family has no version, changelog or release notes.** Its content is
  **dated**: the date of its last commit (if it is its own git repository;
  otherwise the day of the build). With uncommitted changes the local
  preview shows today's date; a release image needs a committed state.
- Tiles carry their own news: `date` when added, `updated` and a short
  `note` (per locale or plain) when improved. The build turns the tiles of
  the last weeks into "What's new?", followed by the notes of Family Campus.
- The footer shows "Family Campus <version> · content of <date>" (a test
  image adds "test version"; a local preview needs no hint). The build writes this into `build.json`; the server
  returns it at `/api/version`.
- A release image is tagged `<Family Campus version>-<content date>`, e.g.
  `1.0.0-2026.11.22`, and `latest`; labels record the Family Campus commit,
  the content date and the my-family commit. It is built only from a clean
  Family Campus checkout at `FC_APP_VERSION` and a committed my-family; test
  builds are tagged `dev` only.

## Consequences

+ One version on the site; families never copy the news of Family Campus.
+ No release bookkeeping for content: commit, build the image, deploy.
+ Every running image can be traced to a Family Campus version and a
  my-family commit.
− A small fix to a tile appears in "What's new?" only if `updated` and
  `note` are set (the skills do it).
− Two images of the same day share a tag; the label with the commit tells
  them apart.

## Alternatives considered

- **Keep a version per my-family (ADR-0010):** two versions and copied
  notes – the reason for this decision.
- **A counter instead of the date (`1.0.0+12`):** unique, but tells
  learners nothing.
