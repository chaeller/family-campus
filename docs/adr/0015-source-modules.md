# ADR-0015: Source modules – local, opt-in, own responsibility

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Families prepare tiles from what their children have to learn: exam dates,
learning goals and worksheets, often published on school platforms. Fetching
them by hand is tedious; scripts can help. But they access third-party
systems with personal credentials, handle personal data of children and
teachers, and download copyrighted material. Whether such automation is
permitted depends on the platform's terms, the school and the country, and
cannot be judged by the project.

## Decision

- Scripts that fetch material are **source modules** in `sources/<name>/`,
  part of Family Campus so that families can share and improve them.
- They are **opt-in**: a module is used only if its settings are in the
  untracked `.env` of the Family Campus folder (template `.env.example`), next to the one campus of the checkout.
- They run **only on the family's computer** during the preparation of
  content: never in the server, the image, the container or the volume; the
  server makes no outgoing requests. Downloads go to my-family's
  `material/` folder, which is never committed and never published.
- Only the reviewed result goes into my-family: exams with cleaned-up
  learning goals, tiles written by the family. Copyrighted documents are not
  copied into tiles.
- Every module documents what it accesses, how it logs in, side effects, and
  what is known about its legal status. `sources/README.md` states the rules
  for responsible use (own access only, terms of use, gentle fetching,
  personal data, copyright, credentials) and that the project gives no legal
  advice; the MIT licence excludes warranty.
- Modules that bypass protections or access data of others are not accepted.

## Consequences

+ Useful scripts are shared instead of being rewritten by every family.
+ Clear boundaries: nothing from a source reaches the server or the public.
− Each family must check the legal situation for itself; a module may have
  to be withdrawn if a platform forbids automated access.
− Modules break when platforms change; they need maintenance.

## Alternatives considered

- **Keep source scripts private in each my-family folder:** every family repeats the
  work, and nobody documents the rules.
- **Fetch at run time on the server:** credentials and personal data on the
  server, outgoing requests, a much larger attack surface.
