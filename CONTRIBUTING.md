# Contributing

Thanks for your interest in Family Campus! Issues and pull requests are
welcome.

## Before you start

- Read the [architecture decision records](docs/adr/README.md); a change that
  contradicts an accepted ADR needs a new ADR first.
- Larger changes: open an issue to discuss the idea.
- Family Campus is small on purpose: Python standard library on the server, no
  framework and no build step for the pages, no runtime dependencies.

## Rules

- **No data of a real family**: no real names, exams, schools, domains or
  servers. Use the invented family of `example-family/`.
- **Content**: only tiles written for the project or generated, with sources
  for facts – never material copied from textbooks or worksheets (ADR-0013).
- **English** for code, identifiers, comments, logs and docs. **No
  hard-coded UI text**: add keys to `www/locales/en.json` and `de.json`
  (`de-CH` only where it differs) – see [docs/languages.md](docs/languages.md).
- CSS with logical properties (RTL-ready).
- Note changes under "Unreleased" in `CHANGELOG.md`, and what learners notice
  per locale under `"unreleased"` in `release-notes.json` (ADR-0018).
- **Source modules** (`sources/`) follow ADR-0015 and the rules in
  [sources/README.md](sources/README.md); open an issue first.

## Checks before a pull request

```bash
python3 tools/build.py                                     # example family
python3 tools/selftest.py build/www/exercises/*/index.html # needs Chromium
python3 tools/check_i18n.py
python3 tools/check_de_ch.py example-family
python3 -m py_compile server/server.py
```

The same checks run on GitHub for every push and pull request
(`.github/workflows/checks.yml`).

Look at changed pages at phone width (about 400 px) and on a desktop, in
English and German.

## Licence

By contributing you agree that your contribution is licensed under the
[MIT licence](LICENSE).
