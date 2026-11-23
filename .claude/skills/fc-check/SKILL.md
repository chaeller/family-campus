---
name: fc-check
argument-hint: "[focus: all|content|exams|release]"
description: Family Campus – health check of my-family (and the Family Campus it uses) without changing anything. Builds and self-tests the site, checks de-CH spelling, set ids, catalogue, exams, focus lists, privacy, "What's new?" (date / updated / note of the tiles) and what is not yet live; reports findings with suggested fixes. Use when the user asks to check, lint or review the state, or before fc-release.
---

# fc-check – is everything consistent?

**Where:** Claude Code runs in the Family Campus folder. my-family is `my-family/` (or
`$FC_CAMPUS`, or the folder the user names); paths below such as `campus.json`,
`tiles/`, `tiles.json`, `deploy.env`, `material/` are relative to
it, `tools/…` and `sources/…` are Family Campus's. Git commands about my-family run
in my-family (`git -C my-family …`) and only if it is its own repository –
never put family data into Family Campus's git.

Report only; change nothing unless the user
asks afterwards. Read my-family's `campus.json` and `deploy.env` first.

**Arguments:** `$ARGUMENTS` – optional focus: "content" (checks 1–7),
"exams" (5), "release" (1–2, 8–9). Without arguments run all checks.

## Checks

1. **Build and self test:** `tools/campus-build.sh` – Family Campus's
   `VERSION` equals `FC_APP_VERSION` from `deploy.env`; every tile "no
   problems"; set ids unique (the build stops otherwise); no ß in de-CH
   content.
2. **App:** the Family Campus checkout (this folder) is clean and committed (on its tag
   `v<FC_APP_VERSION>` if it has one); `python3 tools/check_i18n.py`
   has no problems.
3. **Catalogue** (`tiles.json`, `campus.json`): every tile has an `area`
   from the categories and, if that area has levels, a `level` from them; a
   `module` (and `extension`, `css`, `cover`) that exists in `tiles/`;
   subjects that are subjects of Family Campus or defined in `campus.json` with names in
   `locales/`; every person has a valid `area` (and `level`) and a colour;
   ids in English.
4. **Locales:** `campus.json` `locales` and `defaultLocale` exist in the
   catalogues of Family Campus; every own key in `locales/` exists for every offered
   locale (or its fallback).
5. **Exams** (`exams.json`): `people` exist, `subject` is a known id,
   every id in `exercise` (one id or a list) exists (an exam without a tile:
   mention it – the home page says "No tiles yet"); upcoming exams
   have `goals`; past exams can be removed (list them, today's date in the
   my-family's time zone).
6. **Focus lists:** every `focus[].exercise` exists.
7. **Privacy:** no person names in `tiles/`; nothing from the material
   folders in `tiles/` or in git; no secrets tracked (`.env`, `campus.env`).
8. **What's new? (ADR-0018):** every tile has `date`; tiles changed since the
   running image (`git -C my-family diff <label family-campus.commit> -- tiles tiles.json`)
   whose change learners notice have `updated` and a short `note` (no names, no
   technical terms); `updated` is not before `date`.
9. **Not yet live:** uncommitted or unpushed changes in my-family, and commits
   since the commit of the running image (label `family-campus.commit`, read-only
   on the server if reachable).

## Report (in the user's language)

A short table: check · status (✅ / ⚠️ / ❌) · finding · suggested fix.
Then name the next step if useful: `fc-improve`, `fc-ingest`, `fc-release`.
