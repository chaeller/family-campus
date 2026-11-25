# ADR-0020: Sets have a difficulty; harder sets open at 80 %

- **Status:** Accepted
- **Date:** 2026-11-25

## Context

A learner asked for harder questions (a report, ADR-0019). Tiles mostly ask terms and facts;
harder sets (cases, decisions, sequences) are useful once the basics sit, and frustrating
before. The word "level" is taken: it is the school level or year of apprenticeship of a tile
(ADR-0004). Nothing in Family Campus so far made one set depend on another.

## Decision

- A set may carry a **difficulty** `tier` – a whole number from 1, without an upper limit;
  without it a set has tier 1. In the module the field follows the title:
  `{id:"hj6", title:"Fallbeispiele", tier: 2, qs: …}` (the build reads id and title).
- A set of tier *n* > 1 is **locked** until every set of the next lower tier present in the
  tile has a best result of at least **80 % in a whole run**. Retry rounds of the mistakes and
  the repetition box do not count (they are short and would open it too easily, ADR-0007).
  The chain is enforced: tier 3 needs tier 2, which needs tier 1.
- The set list shows the difficulty as a badge (◆◆ for tier 2, ◆◆◆ for tier 3 …). A locked
  set is greyed out with 🔒. Its conditions are in the badge's tooltip and, because phones
  have no hover, appear below the set when it is tapped. The result of a run says which sets
  it opened.
- The server returns the best result of whole runs per set (`full` in `GET /api/progress`
  and `POST /api/result`); the check is done in the engine. It is a learning aid, not access
  control: anybody who wants can still read the module.

## Consequences

- Harder sets can be added to any tile without changing the others; tiles without `tier`
  behave as before.
- A learner cannot start a hard set "to have a look" before the basics sit – that is the
  intent. Parents are locked out the same way.
- Sets of a tier must each reach 80 %; a very long or hard basic set can hold back the next
  tier – keep basic sets short.

## Alternatives considered

- **Badge only, no lock:** simpler, but the dependency the family wants would not exist.
- **Two fixed levels (basic / exam):** too narrow; tiles may need three or more.
- **Average of the lower tier instead of every set:** one strong set could hide a weak one.
