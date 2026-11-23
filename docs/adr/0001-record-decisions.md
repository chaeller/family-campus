# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Family Campus is small and maintained by few people, often with the help of
coding agents. Decisions about structure, data and operations are easy to
forget or to undo by accident.

## Decision

We record every fundamental decision as an Architecture Decision Record in
`docs/adr/`, numbered, in English, with context, decision, consequences and
alternatives (template `0000-template.md`). Accepted ADRs are not rewritten;
a new decision supersedes an old one and the old one is marked.

## Consequences

+ Contributors and agents can see why things are as they are.
− Each fundamental change needs a short write-up first.

## Alternatives considered

- **Decisions only in commit messages or issues:** hard to find later.
