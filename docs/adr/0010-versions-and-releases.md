# ADR-0010: Versions and releases

- **Status:** Superseded by [ADR-0018](0018-one-version-dated-content.md)
- **Date:** 2026-11-22

## Context

Family Campus and every my-family folder change often. Learners should see what is new,
and an installed image must be traceable to its source.

## Decision

- Semantic versioning; `VERSION` holds version and date, `CHANGELOG.md`
  collects changes under "Unreleased" (Keep a Changelog).
- Learners see the version in the footer and "What's new?" from
  `release-notes.json` (notes per locale).
- A release image is built only from a clean, tagged state; test builds are
  marked `+dev.<commit>` and never tagged `latest`.
- Family Campus and each my-family folder have their own version (see ADR-0011).

## Consequences

+ Every running image can be traced to a tag; test builds cannot be confused with releases.
− A release needs a few steps (scripts and skills guide them).

## Alternatives considered

- **Deploy from the working tree:** fast, but nobody knows what is running.
