# ADR-0009: Installable web app without a service worker

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Learners use the site mostly on phones and want it on the home screen.
Practising offline is rare; progress is stored on the server.

## Decision

The site has a web app manifest and icons (public, so that browsers can
check them before login) and can be installed as an app. It has no service
worker and no offline mode.

## Consequences

+ An app icon on the phone without app stores; updates are immediate.
− No practice without a connection.

## Alternatives considered

- **A service worker with offline sync:** complex (conflicts, caching of
  pages and progress) for little benefit.
