# ADR-0014: Content and releases with coding-agent skills

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Writing a tile (summary sheet, sets, generated questions, cover, catalogue
entry, tests) takes many careful steps. Families are rarely developers;
coding agents can do the work if the steps are written down.

## Decision

The recurring workflows are described as skills in `.claude/skills/`
(`fc-ingest` new material and tiles, `fc-improve` change a tile, `fc-check`
health check, `fc-release` prepare a release, `fc-deploy` install it). They
are plain Markdown and also readable by people. Skills never commit, push or
deploy unless the person explicitly asks for that step. They are generic:
the values of my-family come from its `campus.json` and `deploy.env` and the
source modules set up in Family Campus's `.env`, not from rules in my-family.

## Consequences

+ Consistent tiles and releases, also with little technical knowledge.
− Skills must be kept in step with the tools.

## Alternatives considered

- **Only a written guide:** agents and people skip steps.
