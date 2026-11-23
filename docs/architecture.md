# Architecture

## Overview

```
 Family Campus (this repo)                 my-family/ (ignored by Family Campus's git)
   www/      pages, i18n.js, locales/,        campus.json, exams.json
             campus.js, subjects.js           tiles.json, tiles/, locales/
   engine/   quiz engine template             curricula.md, deploy.env
   content/  demo tile, default categories            │
   tools/    build.py, campus-*.sh ──────────────────┴──▶ my-family/build/www (one static site with data files)
                                          │
 Browser ──HTTPS──▶ reverse proxy ──▶ container: server/server.py (login, API, static files)
                                          │
                                          ▼
                                   volume /data: campus.env (logins), campus.sqlite (progress)
```

## Components

| Part | Purpose |
| --- | --- |
| `server/server.py` | One Python process, standard library only (ADR-0003): login, API, serves the built site under `FC_PREFIX` only after login (except the public files below), health check `/healthz` |
| `www/index.html` | Home page: filters (for · category · field · level · subject), upcoming exams, revision, focus, tiles with status |
| `www/login.html` | Login: tap your name, enter password; language switcher |
| `www/progress.html` | Progress of one person (parents choose the person): today, totals, activity, sets, recent runs, recent mistakes |
| `www/i18n.js`, `www/locales/` | Languages and locales ([languages.md](languages.md)) |
| `www/campus.js` | Connects tile pages to the server: progress, answers, results, revision box |
| `www/version.js` | Version in the footer and header, "What's new?" dialog |
| `www/subjects.js` | Picture (flag or icon) and name per subject |
| `www/people.template.js` | Becomes `people.js` (names and colours, public for the login page) |
| `engine/quiz.html` | Quiz engine template: views (tile, summary sheet, quiz, result), question types, typo tolerance |
| `tools/build.py` | Builds my-family: copies `www/`, builds the tiles, writes `exercises.json`, `people.js`, `config.json`, `build.json` (version, content date), `release-notes.json` (new and improved tiles + notes of Family Campus), merges locales |
| `tools/build_page.py` | Builds one tile page from the engine, modules, extension, CSS and content language |
| `tools/selftest.py` | Renders every question of every set in headless Chromium and checks content consistency |
| `tools/campus-*.sh`, `check_de_ch.py`, `check_i18n.py` | Build, image and release of my-family; checks |
| `sources/<name>/` | Source modules: fetch material on the family's computer, never part of the image (ADR-0015) |

Public without login: `login.html`, `favicon.svg`, `version.js`, `people.js`,
`i18n.js`, `config.json`, `locales/*.json`, the web app manifest and its
icons, `/api/version`, `/healthz`.

## Data model (built `exercises.json`)

```json
{
 "categories": [ { "id": "school", "name": {"en": "School"}, "areas": [
   { "id": "school", "name": {"en": "School"}, "levelOnly": true, "levels": [ {"id": "year6", "name": {"en": "Year 6"}} ] } ] } ],
 "people": { "Anna": { "area": "school", "level": "year6", "focus": [ … ] } },
 "exercises": [ { "id": "…", "title": "…", "lang": "en", "area": "…", "level": "…", "subjects": ["math"],
                  "topics": [], "date": "2026-11-20", "path": "exercises/<id>/", "image": "exercises/<id>/cover.svg",
                  "sets": [ {"id": "fr1", "title": "…"} ] } ],
 "exams": [ { "date": "…", "people": ["Anna"], "subject": "math", "topic": "…", "exercise": "…", "goals": [] } ]
}
```

- Content belongs to category → area → level (ADR-0004); a selected person
  sees their area up to their level; `levelOnly` areas start on exactly the
  level; `forAll` areas appear with "All" or their own category.
- Learners receive only their own exams (the server filters
  `exercises.json`); parents receive all.
- `config.json`: `name`, `locales`, `defaultLocale`, `currency`, `subjects`.

## Server API

All endpoints are under `FC_PREFIX`. JSON in and out; errors are
`{"error": "<code>"}`. Parents (admin) may add `?user=<name>` to the read
endpoints to look at another person.

| Method and path | Purpose |
| --- | --- |
| `POST /api/login` `{name, password, locale?}` | Session cookie (120 days); 5 failures per minute and IP lock for a minute (`too_many_attempts`); a hand-chosen `locale` becomes the person's if they have none |
| `POST /api/logout` | Ends the session |
| `GET /api/me` | Name, admin, `locale`, the people the user may see |
| `POST /api/me/locale` `{locale}` | Stores the person's language (one of my-family's locales) |
| `GET /api/progress?ex=<id>` | Best result and runs per set of one tile, due revision questions |
| `GET /api/summary` | Per tile and set: runs, best, last; due and boxed questions; totals; mastered |
| `GET /api/history?tz=<offset>` | Recent runs, recent wrong answers, answers per local day (30 days), today's answers |
| `GET /api/repeat?ex=<id>` | Up to 15 due revision questions of a tile |
| `POST /api/answer` `{ex, set, key, ok, mode, q, text}` | Stores one answer; wrong answers go into the revision box, right ones move up |
| `POST /api/result` `{ex, set, total, correct, mode}` | Stores a finished set (modes `normal`, `retry`, `repeat`) |
| `GET /api/version` | Family Campus version and date, date of my-family's content, test build (public; from `build.json`, ADR-0018) |
| `GET /healthz` | `ok` (public) |

## Database (SQLite, `/data/campus.sqlite`)

| Table | Content |
| --- | --- |
| `users` | name, scrypt hash, admin, locale |
| `sessions` | token, user, expiry |
| `attempts` | finished sets: tile, set, mode, total, correct, time |
| `answers` | every answer: tile, set, question key, question text, correct, mode, time |
| `review` | revision box: question (JSON), box 1–5, due date (ADR-0006) |
| `mastered` | questions that left the box |

The schema is created and migrated at start (new columns are added in
place). Logins come from `/data/campus.env` at every start (ADR-0005).

## Quiz flow

Tile → "learn first" (summary sheet) → set → questions one by one with
feedback → result with "practise mistakes again". Every answer goes to
`/api/answer`, every finished set to `/api/result` (ADR-0007). Revision
questions are stored with their full content, because generated questions
differ on every run.
