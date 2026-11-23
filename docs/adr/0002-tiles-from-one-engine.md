# ADR-0002: Tiles are static pages built from one quiz engine

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

A learning site for families needs many small exercise units ("tiles") on
very different topics. They must load fast on phones, work without a build
step on the server and be easy to write for one person.

## Decision

- Every tile is one static HTML page, built from the quiz engine template
  (`engine/quiz.html`) and one or more **content modules** (JavaScript that
  defines `MODULES`: a summary sheet and short sets of questions).
- The engine provides the question types (multiple choice, typed answers,
  tables, matching, ordering, tapping, sorting, figures) and the flow
  (learn → practise → result → repeat mistakes).
- A tile can bring an **extension**: extra question types (`EXTRA_TYPES`)
  and widgets for its summary sheet (`LEARN_HOOKS`), inserted by
  `tools/build_page.py`. Content-specific code never goes into the engine.
- Questions can be generated anew on every run, so learners practise the
  skill and not the answer.

## Consequences

+ No framework, no client build; tiles are plain files any static server can deliver.
+ One engine improvement reaches every tile at the next build.
− Every tile page contains a copy of the engine (a few tens of kilobytes).

## Alternatives considered

- **A single-page app with content as JSON:** generated questions and
  special question types are harder to express as data.
- **An existing quiz framework:** heavier, and its question types do not fit
  summary sheets and generated tasks.
