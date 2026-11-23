# ADR-0003: Server with the Python standard library and SQLite

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Families host the site themselves, often on a small home server. The server
must be easy to run, to update and to keep secure for years.

## Decision

The server is one Python file using only the standard library
(`http.server`, `sqlite3`, `hashlib.scrypt`). It serves the built site,
handles login, stores answers, runs and the spaced repetition box in SQLite
under `/data`, and runs in a small container with a read-only file system.

## Consequences

+ No dependencies to update, no supply-chain risk from packages.
+ One process, one database file, easy to back up.
− Features a web framework would bring (routing, templating) are written by hand.
− SQLite limits writes to one process – enough for a family.

## Alternatives considered

- **A web framework (Flask, FastAPI):** more convenience, but dependencies.
- **PostgreSQL:** a second service to run and back up, not needed at this scale.
