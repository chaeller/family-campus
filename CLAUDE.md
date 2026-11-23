# Family Campus – agent steering

Family Campus is a self-hosted learning site for families (tiles with a
summary sheet and short sets, progress page, spaced repetition). This
repository is the software; it will be published on GitHub under the MIT
licence as one single initial commit, version 1.0.0. Family data and
family content live in **my-family**: the folder `my-family/`,
ignored by git (ADR-0011).
Decisions are recorded in `docs/adr/` (ADR-0001); read them before larger
changes and do not contradict an accepted ADR silently.

## Hard rules

- **No data of a real family in this repository**: no real names, colours
  per person, exams, learning goals, schools, domains, server names,
  registry hosts, logins. Examples use the invented family of `example-family/`.
  Before every push run `tools/publish_check.sh --deny <private word list
  outside the repo>`; before tagging a version add `--release`.
- **The user commits, pushes and releases himself.** Never run
  `git commit`, `git push`, `git tag` or `docker push` unless explicitly
  asked in the current request.
- **Every change to Family Campus is recorded where it is made**, before it is
  committed: a line under `## Unreleased` in `CHANGELOG.md` (English, for
  developers; also skills, docs and tools), and – if learners notice it – a
  short note in `"unreleased"` of `release-notes.json` (`en` and `de`). Check
  this before every commit of Family Campus (`git diff --cached --stat`: a
  change without a `CHANGELOG.md` line is incomplete). A new version moves the
  entries into its own section (`fc-release`, step 1b); `publish_check.sh
  --release` refuses unreleased entries, so no version is tagged without them.
- No tiles **in this repository** built from teachers' worksheets, dossiers
  or books (copyright): only generated content or content from
  official/primary sources, with the sources named in the summary sheet.
  Tiles derived from teaching material belong only in my-family (ADR-0013).

- `my-family/` is ignored by git: it holds everything of the user's **own family** (and
  may be its own git repository with its own remote). Its data belong to that folder
  only – never copy them into Family Campus files; its git repository (if any) is its
  own (`git -C my-family …`). my-family has **no rules of its own**: its
  values are `campus.json` (languages, categories, people) and `deploy.env`,
  the source modules it uses are set up in Family Campus's `.env`; everything else
  follows this file and the `fc-*` skills.

## Languages and locales (ADR-0012)

- Code, identifiers, comments, logs and all documentation: **English**.
- UI: **no hard-coded texts**; every text is a key in `locales/<tag>.json`
  (`en` is the default and fallback; `de` base with ß; `de-DE` and `de-CH`
  hold only their differences – `de-CH` writes ss, never ß). Dates, numbers,
  relative times and plurals through `Intl` (`i18n.js`), currency from
  my-family. CSS uses logical properties (RTL-ready).
- Tile content is not translated; every tile has a content language
  (`lang`).
- Talk to the user in German.

## Structure (work in progress)

User documentation: `README.md` and `docs/` (getting-started, my-family, tiles,
languages, architecture, operations) – keep them in step with the code.


- `server/server.py` – Python standard library, SQLite in `/data`; `FC_PREFIX` sets the URL path.
- `www/` – pages, `i18n.js`, `locales/`, `campus.js`, `version.js`, `subjects.js`,
  `people.template.js`; `people.js`, `exercises.json`, `config.json`, `build.json` and `release-notes.json` are
  build output; `release-notes.json` in the root holds the notes of Family Campus for learners (ADR-0018).
- `engine/quiz.html` – quiz engine template; `tools/build_page.py` inserts content modules.
- `content/` – the demo tile "Internet basics" (`catalog.json` with default categories,
  module, extension `prim_extension.js`, cover). Family content belongs in my-family.
- `example-family/` – the invented example family (the demo, and the template `tools/new-campus.sh` copies).
- `tools/build.py <folder>` → `build/www` (default: `example-family/`); `tools/selftest.py`, `tools/check_i18n.py`.
- Local test: `python3 tools/build.py && FC_PREFIX=/campus python3 server/server.py --www build/www --data <dir>`
  (logins of the example in `example-family/campus.env.example`).
- `tools/new-campus.sh`, `campus-build.sh`, `campus-serve.sh`, `campus-image.sh`,
  `check_de_ch.py` – create, build, run and image
  my-family (default `my-family/`, see `tools/lib-campus.sh`; values
  from its `deploy.env`).
- `.claude/skills/fc-*` – generic workflows for my-family (ADR-0014); Claude
  Code runs in the Family Campus folder, the skills take my-family's values from
  `campus.json`, `deploy.env` and Family Campus's `.env`.
- `.env` (untracked, template `.env.example`) – settings and credentials of
  the source modules; never print, log or commit its values.

## Working on my-family's content

- Talk to the user in the language of my-family's `defaultLocale`.
- Learner-facing text in the tile's `lang`. `de-CH`: ss, never ß (also not in
  accepted answers), Swiss terms and examples (Franken, Velo, Kantone).
- Tiles stay reusable: no names, surnames, classes, schools or photos of
  people in tiles.
- Photos and documents in my-family's `material*/` and `fotos/` are never
  committed, never copied into `tiles/` or `build/`, never published.
- A source module is used only if it is set up in `.env`; if its account
  belongs to a learner (Moodle), never ask for, type or store the password
  and never run its `token` command yourself.
