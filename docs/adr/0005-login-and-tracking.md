# ADR-0005: Login per person, tracking, logins in the volume

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Progress, repetition and exams are personal. Children should not need e-mail
addresses, and parents want to see everyone's progress.

## Decision

- The whole site is available only after login; every person has a name and
  a password, parents are marked as admin and may see everybody's progress.
- Logins are defined in `campus.env` in the data volume (`CAMPUS_USERS`,
  `CAMPUS_PASSWORD_<NAME>`); at start the server creates missing people and
  applies changed passwords. The database stores only scrypt hashes; a
  changed password ends the person's sessions.
- Every answer and every finished set is stored per person, exercise and set id.
- The login page lists the names (public: names and colours only).

## Consequences

+ No e-mail, no accounts to manage in a UI; one file to edit.
+ Set ids must never change, or progress is lost; they are unique across tiles.
− Changing a password means editing a file in the volume.

## Alternatives considered

- **No login, progress in the browser:** lost on another device, no view for parents.
- **Accounts with e-mail and self-service:** too much for a family.
