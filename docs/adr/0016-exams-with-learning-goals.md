# ADR-0016: Exams carry cleaned-up learning goals

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Before an exam, learners want to see what will be tested. The learning
goals come from a school platform (through a source module, ADR-0015) or
from the teachers' learning-goal documents. Raw downloads and teaching
material stay in my-family's `material/` folder and are never committed or
published (ADR-0013, ADR-0015).

## Decision

Every exam in my-family's `exams.json` may carry its learning goals in the
field `goals`: one short sentence per goal in my-family's default
language, taken from the platform or the learning-goal document and
cleaned up:

- no names or initials of teachers, no names of classmates,
- no point counts, practice hints, links or references to files,
- typos fixed, bullets and formatting removed,
- if the goals are only in a dossier, one sentence saying so.

The goals are shown only after login, next to the exam on the home page.
The skill `fc-ingest` writes and updates them.

## Consequences

+ The learning goals are visible next to the exam and versioned with the
  tiles that cover them.
+ No extra storage or server logic.
− Summaries of teachers' texts are in my-family's git history and in its
  image (behind the login) – never in Family Campus.
− Cleaning up the goals is manual work for the skill; it must keep the
  rules above.

## Alternatives considered

- **Goals only in the Docker volume** (served at runtime, not in git): needs
  a server extension and a copy step for every new exam.
- **Not showing the goals:** learners would have to look them up elsewhere.
