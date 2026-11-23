# ADR-0008: Typo tolerance – one more try instead of a mistake

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

On phones, learners often mistype answers they know. Counting a slip as a
mistake is frustrating and sends known content into the revision box.

## Decision

A typed answer that differs from an accepted one by exactly one character
(wrong, missing, extra or two swapped) gets one more try with a hint. It is
not applied to numbers, terms, answers shorter than three characters, and
questions marked `strict` – where the exact spelling is the learning goal.

## Consequences

+ Fewer false mistakes; learners still have to correct the answer themselves.
− Content authors must mark spelling exercises `strict`.

## Alternatives considered

- **Accept near misses silently:** learners would never notice their spelling.
