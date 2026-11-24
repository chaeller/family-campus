# ADR-0019: Learners report questions; reported questions do not count

- **Status:** Accepted
- **Date:** 2026-11-24

## Context

Tiles are written by people and agents, many questions are generated, and the
engine checks answers automatically. A wrong solution, an unclear question, a
correct answer that is not accepted or an engine fault (such as the fixed
left-left-right-right order of sort questions) shows up first for the learner. Until
now the learner could only tell a parent, the wrong result was stored anyway, and
the mistake went into the repetition box (ADR-0006).

## Decision

- Every question can be reported: before answering, and after the result in the
  feedback box ("🚩 Something wrong with this question?"). The learner picks one
  quick reason (wrong solution, my answer was right, unclear, typo, something else)
  and may add a comment.
- A reported question counts neither as right nor as wrong: its answer is not
  stored, it is not in the result of the run and not in the repetition box. To make
  this simple, the engine sends an answer only when the learner goes on (next,
  close, leaving the page), not at once.
- The server stores the report (table `feedback`): person, tile, set, question key,
  the question as shown, the answer given as read from the screen, whether it was
  rated right, reason, comment, and the running release (`version-content@commit`).
- A question reported during the running release is flagged for everybody (🚩) and
  can be skipped; skipping counts neither. The flag ends when another release is
  installed – nothing on the live server has to be changed or cleared.
- Only parents (admins) see the reports with their comments, in a section of the
  progress page (`GET /api/reports`). Learners see only the flag.
- On the development machine `tools/campus-feedback.sh` fetches the reports
  read-only from the running container into my-family's `feedback.json`; the skill
  `fc-feedback` analyses them, fixes the tile or Family Campus, and records per
  report how it was handled. The next release and deployment end the flags.

## Consequences

- A wrong question no longer harms the learner's results or repetition box.
- An answer given right before the page is closed abruptly may be lost; the engine
  sends pending answers on `pagehide` with `keepalive`, which covers the usual cases.
- Flags match a question by its key (ADR-0006). Generated questions change on every
  run, so the flag shows only if exactly the same question comes again; the report
  itself is kept regardless.
- `feedback.json` holds names and the learners' own words: it belongs to my-family.

## Alternatives considered

- **Store the answer at once and undo it on a report:** undoing a change of the
  repetition box needs the previous state; deferring is simpler and exact.
- **Flags that a parent clears by hand:** needs writes on the live server and a
  further screen; tying the flag to the release clears it exactly when the fix
  arrives.
- **Reports by e-mail or a chat message:** needs a mail setup and loses the
  question as shown.
