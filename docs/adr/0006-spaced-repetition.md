# ADR-0006: Spaced repetition with a Leitner box

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Learners repeat what they already know and avoid their mistakes. Mistakes
should come back at the right time until they stick.

## Decision

A wrongly answered question goes into a personal revision box (Leitner
system) with five compartments: it is due again after 1, 3, 7, 14 and 30
days; a right answer moves it up, a wrong one back to the start; after the
last compartment it counts as mastered. Due questions are shown on the home
page and in each tile, and are answered in their own round.

## Consequences

+ Practice focuses on weaknesses without planning by the learner.
− The question itself (not only an id) is stored, because generated
  questions differ on every run.

## Alternatives considered

- **SM-2 or similar algorithms:** finer, but harder to explain to children.
