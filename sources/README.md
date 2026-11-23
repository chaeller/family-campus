# Source modules

A source module fetches material that a family is entitled to see – for
example the upcoming exams and learning goals of their own children from a
school platform – so that tiles and exams can be prepared from it
(`/fc-ingest --from <source>`). Source modules are part of Family Campus, but they
are **opt-in, run only on your own computer and are used at your own
responsibility** (ADR-0015).

| Module | Fetches | Status |
| --- | --- | --- |
| [`escola/`](escola/README.md) | Exams (Lernzielkontrollen), learning goals and attached documents from Escola, a school platform used by schools in Switzerland | works with the parent account of a family; legal status: see its README |
| [`moodle/`](moodle/README.md) | Upcoming exams, assignments and attachments from Moodle (used by many vocational schools), through its official web service or the calendar export | tested with one school; uses the learner's own account |

## How a source module works

- It lives in `sources/<name>/` with a script and a `README.md`.
- It runs in the folder of an **campus** (or with `--campus <dir>`), reads
  its credentials from Family Campus's `.env` (template `.env.example`, never
  committed) and writes
  only into `<campus>/material/<name>/` (never committed, never copied into
  tiles or the image).
- It never runs on the server: no source code, credentials, sessions or raw
  data in the image, the container or the volume, and the server makes no
  outgoing requests.
- Output for exams: `material/<name>/<person>/exams.json`, a list of
  `{date, subject, type, title, goals, links, documents}` (documents: files
  next to it). `/fc-ingest` compares it with my-family's `exams.json` and
  tiles; only the reviewed result (exams with cleaned-up learning goals,
  tiles written for the family) goes into my-family.
- A source is enabled by its settings in Family Campus's `.env` (which source,
  which people); there are no other switches.

## Legal and responsible use

**This is not legal advice.** The authors of Family Campus cannot judge
whether using a module is permitted in your situation; that depends on your
country, the platform's terms and your school's rules. The software is
provided "as is", without warranty (see [LICENSE](../LICENSE)). Before using
a module, check at least:

1. **Your own access only.** Use only your own account and only data you are
   entitled to see (e.g. your own children's). If the account belongs to a
   learner (e.g. an apprentice in Moodle), the learner runs the module or
   agrees to it and types the password. Never use other people's
   credentials, never try to see data of others, never bypass access controls,
   captchas or two-factor authentication.
2. **Terms of use.** Read the platform's terms of use and your school's rules.
   If they forbid automated access, or the operator or the school objects, do
   not use the module. When in doubt, ask the school or the platform operator.
3. **Be gentle.** Fetch rarely (e.g. once a week), only what you need, reuse
   sessions; the modules avoid repeated logins and do not crawl links.
4. **Personal data.** The fetched data is personal data of your family and
   possibly of teachers and classmates. Keep it on your own computer, do not
   share or publish it, delete it when it is no longer needed; teachers'
   names are not stored. Data protection law (e.g. the Swiss FADP, the EU
   GDPR) may apply to you.
5. **Copyright.** Attached documents (worksheets, dossiers) are protected.
   Use them privately to prepare your own exercises; never copy their text
   into tiles that you publish, never put them into the image or a public
   repository (ADR-0013).
6. **Credentials.** Keep them in Family Campus's `.env`, never in code, logs,
   commits or chats.

Every module README states what it accesses, how it logs in, side effects
(e.g. notification e-mails), what is known about its legal status, and what
to do if the platform changes.

## Writing a new source module

Open an issue first. A new module needs a README with the points above,
must follow the rules of this page (local only, own access, no crawling,
output format) and must work without third-party packages for its normal use
(a troubleshooting mode may need Playwright). Modules that need to bypass
protections or access data of others are not accepted.
