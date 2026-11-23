---
name: fc-ingest
argument-hint: "[person|area] [topic] [--from fotos|web|<source>] [--level <level>]"
description: Family Campus – take in new material for my-family – exams with learning goals and new tiles. Uses photos or documents the user provides, official sources on the web for topics without a teacher, or a source module set up in Family Campus's .env (e.g. a school platform); compares with the existing exams and tiles, adds exams and learning goals, and – after approval – builds new tiles. Use when the user wants new learning goals or exams, or a new tile for a topic that has none yet. To improve an existing tile use fc-improve.
---

# fc-ingest – new material → exams, learning goals, new tiles

**Where:** Claude Code runs in the Family Campus folder. my-family is `my-family/` (or
`$FC_CAMPUS`, or the folder the user names); paths below such as `campus.json`,
`tiles/`, `tiles.json`, `deploy.env`, `material/` are relative to
it, `tools/…` and `sources/…` are Family Campus's. Git commands about my-family run
in my-family (`git -C my-family …`) and only if it is its own repository –
never put family data into Family Campus's git.

Read my-family's `campus.json` (languages, categories, people) and check which source modules are set up in Family Campus's `.env` (keys only, e.g. `grep -o '^[A-Z_]*=' .env` – never print values), Family Campus's `CLAUDE.md` ("Working on my-family's
content") and Family Campus's ADRs on content (ADR-0004 areas and levels, ADR-0008
typo tolerance, ADR-0012 languages, ADR-0013 content sources).

**Arguments:** `$ARGUMENTS` – all optional, in any order:

- **Target:** a person (a name from `campus.json` `people`) → their
  `area` and `level`; or an area id from the categories. Without a target:
  every source module set up in `.env` (Escola: `ESCOLA_URL` for the people
  in `ESCOLA_CHILDREN`; Moodle: the people in `MOODLE_PEOPLE`), else ask. With
  a person: the modules that list that person.
- **Topic:** an idea in free text, not the tile title, e.g. "Internet:
  addresses and routers" or "Swiss law: sales contract". Derive the area if
  none is given (ask if unclear) and propose the rest (see 2).
- **`--from`:** `fotos` (newest files in my-family's material folders),
  `web` (official sources, see 1), or a source module (`escola`,
  `moodle`). With a topic and no material: ask whether there is material,
  otherwise `web`.
- **`--level`:** the level of the content when it is not the person's own.

The person's language is my-family's `defaultLocale` unless said
otherwise; talk to the user in that language. Never commit, release or
deploy.

## 1. Get the material

**Source modules** – `sources/<name>/` (ADR-0015), e.g. `escola`, `moodle`.
Use one only if it is set up in `.env`; follow its README (setup, side
effects such as notification e-mails – reuse sessions, avoid extra logins –
legal notes) and `sources/README.md` ("Legal and responsible use"): own
access only, fetch rarely, downloads stay in my-family's `material/`
folder. Credentials are never printed, logged or committed; if settings are
missing, ask the user to fill them into `.env` themselves. An account that
belongs to a learner (Moodle): only the learner runs `token` and types the
password – never ask for, type or store it.

**Photos or documents** – the user puts them into my-family's material
folders (never committed, see its `.gitignore`). Look at the newest files,
scale photos down in the scratchpad before reading them. Never copy them
into `tiles/` or `build/`. Teaching material is copyrighted: build own
exercises from what it teaches, do not copy its text.

**Web** (topics without a teacher): first propose an outline with learning
goals and sources and wait for approval.

- Use **official or primary sources**: laws (with article numbers), public
  authorities, standards (RFCs, ISO), original papers, vendor
  documentation. Secondary sites only to find primary ones.
- Search queries contain only the topic – never names of people, the site
  or anything personal.
- The summary sheet lists the sources with links and the date they were
  checked; legal content says it is a simplified overview, not legal advice,
  and states the legal status. Prefer examples of my-family's country.

## 2. Compare and propose

- Exams (from a source): compare with `exams.json` (date + subject +
  person). Missing upcoming exams → add them with `subject` id, `topic`,
  `exercise` (the matching tile id, or a list when several tiles fit) and `goals`: one short sentence per
  learning goal in my-family's `defaultLocale`, from the platform or the
  attached learning-goals document; clean up bullets and typos, drop point
  counts, practice hints and teachers' names; if the goals are only in a
  dossier, write one entry saying so. Do not add past exams.
- Is there a tile covering the goals (`tiles.json`)? A gap in an
  **existing** tile is work for `fc-improve`.
- New topic: propose as a short table and wait for approval –
  - **narrow tiles** (one topic per tile): a broad idea becomes one tile now
    plus named follow-ups;
  - place the tile by my-family's `curricula.md` if it has one (level and
    subject of the area's official curriculum; say which section you used),
    otherwise ask for the level;
  - per tile: **title**, area, level, **subject** (a subject id of Family Campus such as
    `math`, or a new subject of my-family with icon and names), **id**
    (English, `<level>-<subject>-<topic>` or `<area>-<subject>-<topic>`),
    learning goals, planned sets, sources.
- Show the result as a table (date · person · subject · topic · covered by ·
  still missing) and ask for missing material specifically.

## 3. Build new tiles (after approval)

- Content strictly from the learning goals and the material or the approved
  sources. If the expected answer depends on material you do not have
  (dossier, word list), ask for it; if you build anyway, say so and mark it
  in the summary sheet ("compare with the dossier"). Fix errors in source
  material, never copy them, and mention them.
- Learner-facing text in the tile's content language (`lang`, usually the
  my-family's `defaultLocale`; `de-CH`: ss, never ß – also not in accepted
  answers – and Swiss terms); ids, keys and comments in English. No names,
  classes, schools or photos of people in tiles.
- Files of my-family: module `tiles/<subject>_<topic>.js` (shared helpers
  first, e.g. `math_common.js+…`), extension for extra question types
  (`EXTRA_TYPES`, `LEARN_HOOKS`, see ADR-0002), 16:10 cover
  `tiles/covers/<id>.svg`, entry in `tiles.json` (`id`, `module`,
  `extension`, `css`, `title`, `lang`, `description`, `date`, `area`,
  `level`, `subjects`, `topics`, `cover`), new subjects in `campus.json`
  `subjects` (icon) and `locales/<tag>.json` (`subject.<id>` names), exam
  link in `exams.json`.
- Set ids unique across all tiles; the set line must read
  `{id:"xx1", title:"…"` (parsed by the build). Mark `strict:true` where
  spelling is the learning goal (ADR-0008); `num:true` for numbers,
  `nospace:true` for terms; all accepted spellings in `a`.
- Build and check: `tools/campus-build.sh` – self test of every tile and the de-CH check must pass. Take a
  headless Chromium screenshot of the new page at phone width; validate
  generated maths independently.

## 4. Wrap up

- Focus lists (`campus.json` `people[].focus`, tile ids in recommended order
  with a `reason`): suggest an update when new exams come in; keep them short.
- "What's new?" comes from `tiles.json` (ADR-0018): a new tile gets `date`
  (today); an existing tile that was extended gets `updated` (today) and a
  short `note` for learners in its language (no names, no technical terms).
  New exams alone need nothing.
- Report briefly: new or updated exams and learning goals, new tiles, what
  stays open. Next steps are `fc-release` and `fc-deploy`, started by the user.
