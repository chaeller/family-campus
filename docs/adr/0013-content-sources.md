# ADR-0013: Content only from own work or official sources

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Tiles are often inspired by school material: worksheets, textbooks,
dossiers. Their text and exercises are protected; Family Campus, as open source, must
not redistribute them, and learners deserve correct content.

## Decision

Tiles that ship with Family Campus are written for Family Campus or generated, based on
general knowledge or on official and primary sources (laws, standards,
public authorities, original papers), named with links in the summary
sheet. Content derived from teaching material belongs only in a family's private
my-family. Errors in sources are corrected, not copied.

## Consequences

+ Family Campus can be published under the MIT licence without third-party content.
+ Learners can check where a statement comes from.
− Demo content is limited; families build most tiles in their my-family.

## Alternatives considered

- **Ship tiles from teaching material:** copyright problems.
