# ADR-0017: Hand-made focus lists per person

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

my-family quickly has many tiles. Before an exam a learner needs a clear
order – what to practise first, what next – not just a long list filtered
by level and subject. Tiles belong to areas and levels, not to people
(ADR-0004), so the order cannot come from the tiles themselves.

## Decision

- Every person in `campus.json` may have a short **focus list**
  (`people[].focus`): tile ids in the recommended order, each with a
  `reason` per locale.
- The home page shows the list of the selected person (on their own area
  and level, without a subject filter) and marks the first tile that is not
  finished yet with "next".
- The list is made by hand – by the parents or with `fc-ingest` when new
  exams come in – and kept short; tiles that are mastered or no longer
  needed are removed.

## Consequences

+ A clear, explainable order that can follow the next exams and known
  weaknesses.
+ No logic on the server; the list is part of my-family and versioned with it.
− The list must be maintained; it gets outdated if nobody updates it.

## Alternatives considered

- **Automatic suggestions** from error rates and the next exams: no
  reasons that make sense to the learner, and harder to build; a possible
  addition to the lists later.
- **A fixed order in the catalogue:** does not fit people with different
  exams and levels.
