---
name: fc-improve
argument-hint: "<tile id, title or topic> [what to improve]"
description: Family Campus – improve an existing tile of my-family. Extend or correct the summary sheet and sets from photos, worksheets, learning goals, official sources or feedback (wrong solution, missing topic, too few images, spelling to be strict), add sketches, then rebuild, test and record the change. Use when the user wants to change, extend or fix an existing tile. For a topic without a tile use fc-ingest.
---

# fc-improve – make an existing tile better

**Where:** Claude Code runs in the Family Campus folder. my-family is `my-family/` (or
`$FC_CAMPUS`, or the folder the user names); paths below such as `campus.json`,
`tiles/`, `tiles.json`, `deploy.env`, `material/` are relative to
it, `tools/…` and `sources/…` are Family Campus's. Git commands about my-family run
in my-family (`git -C my-family …`) and only if it is its own repository –
never put family data into Family Campus's git.

Read my-family's `campus.json` (languages, categories, people), Family Campus's
`CLAUDE.md` ("Working on my-family's content") and ADR-0002, ADR-0008,
ADR-0012 and ADR-0013 of Family Campus.

**Arguments:** `$ARGUMENTS` – the tile (id, title or topic) and optionally
what to improve ("more images", "photos in the material folder", "solution in
set ab3 is wrong"). Without arguments ask which tile.

## 1. Understand the request

- Find the tile in `tiles.json` (id, title, level, `module`, `extension`)
  and its exams in `exams.json`; read the module in `tiles/`: summary sheet
  (`learn`), sets, question types.
- New material: my-family's material folders (newest files; scale photos
  down in the scratchpad). Never copy them into `tiles/` or `build/` and
  never commit them.
- Check the learning goals of the linked exam (`goals`) – what will be
  tested, and when? Prioritise accordingly. For a tile of an area with a
  curriculum (`curricula.md` of my-family), keep it within its level's
  topics.
- If the expected answer depends on material you do not have, ask for it;
  otherwise say what you base it on and mark it in the summary sheet.

## 2. Change the content

- Follow the material exactly where it says what will be tested; keep the
  class's terms. Fix errors in material and mention them; leave ambiguous
  solutions out or ask.
- Images: inline SVG with numbered parts, readable on phones (legend below
  the sketch); reusable sketches as a separate module loaded before the
  content module (`"module": "a.js+b.js"`).
- New sets: ids unique across all tiles; the set line must read
  `{id:"xx1", title:"…"`. **Existing set ids must not change** – progress is
  stored per set id (ADR-0005).
- Content language of the tile (`de-CH`: ss, never ß, also not in accepted
  answers, Swiss terms); `strict:true` where spelling is the learning goal.
  No names, classes, schools or photos of people in tiles.

## 3. Verify

- `tools/campus-build.sh` – self test
  and de-CH check pass.
- Headless Chromium screenshot of the changed summary sheet and of a new
  question at phone width (about 400 px); fix overlapping or clipped labels.
- Validate generated maths independently.

## 4. Wrap up

- If learners notice the change, set `updated` (today) and a short `note` on the
  tile in `tiles.json`, in the tile's language ("Mehr Bilder", "Lösung in Set 3
  korrigiert"; no names, no technical terms) – that is "What's new?" (ADR-0018).
- Report briefly: what changed, on which material it is based, what is
  uncertain or still missing. Do not commit, release or deploy.
