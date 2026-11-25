# Writing tiles

A tile is one page built from the quiz engine (`engine/quiz.html`) and one or
more content modules (ADR-0002). Family Campus ships one demo tile
(`content/internet_basics.js`); a family writes its tiles in its my-family
(`tiles/`, `tiles.json`).

## A content module

A module is plain JavaScript that defines `MODULES` – usually one module per
tile – with a summary sheet and sets:

```js
const MODULES = [
{ id: "fractions", emo: "🍕", c: "#e8590c", title: "Fractions", desc: "Expand, reduce, compare.",
learn: `
<h2>🍕 Fractions</h2>
<p>A fraction <b>a/b</b> means a parts of b equal parts.</p>
<div class="key">Expand: multiply numerator and denominator by the same number.</div>
<div class="tip">Check: is the result still the same amount?</div>
`,
sets: [
 {id:"fr1", title:"Expand and reduce", qs: () => [
   { t:"in", q:"Reduce <b>6/8</b>.", a:["3/4"], sol:"3/4", nospace:true },
   { t:"mc", q:"Which fraction is bigger?", o:["3/4","2/3"], e:"3/4 = 9/12, 2/3 = 8/12." }
 ]},
 {id:"fr2", title:"Mixed", qs: () => Array.from({length: 5}, makeQuestion)}
]}
];
```

- `learn` is HTML: headings, tables (`<table class="t">` inside
  `<div class="scroll">`), boxes `class="key"` and `class="tip"`, inline SVG.
  End with a "Sources" list when content comes from sources (ADR-0013).
- `sets[].qs` is a function: it is called on every run, so questions can be
  generated (`shuffle(array)` and `pick(array, n)` are always available).
- **Set ids** are short, unique across all tiles of my-family and never
  change (progress is stored per set id). The line must read
  `{id:"fr1", title:"…"` – the build reads the set list from it.
- A set may set `noShuffle: true` to keep the order of its questions.

## Question types

| `t` | Fields | Notes |
| --- | --- | --- |
| `mc` | `q`, `o` (options, the **first** is correct), `e`, `svg` | Options are shuffled; offer no second defensible answer |
| `in` | `q`, `a` (all accepted answers), `sol` (shown), `e`, `svg`, `num`, `nospace`, `strict`, `keys` | `num: true`: number pad, a trailing unit is ignored; `nospace: true`: spaces, `·`/`*` ignored (terms, equations); typos: one more try unless `strict` (ADR-0008). Keys below the input type characters phones lack: `−` for every `num` question (the number pads of iPhones and many Android keyboards have none; always shown, so it does not give away the sign), `^`, `²`, `³` when an accepted answer contains them – or the list in `keys` (also for `table`) |
| `table` | `q`, `rows: [[label, answer], …]`, `fr` | One input per row; `fr: true` shows an accent bar for French |
| `match` | `q`, `pairs: [[left, right], …]` | Both sides must be unique |
| `order` | `q`, `steps` (in the right order) | Tap the steps in order |
| `tap` | `q`, `s` (sentence), `a` (words to tap, lower case) | Tap all words of a kind |
| `sort` | `q`, `cats`, `items: [[text, cat], …]` | Assign every item to a category; items are shuffled, so they may be listed per category |

Every question may have `e` (an explanation shown after answering). Texts
may contain HTML. Learners can report every question (🚩, ADR-0019); `/fc-feedback`
processes the reports.

**Difficulty (ADR-0020):** a set may have `tier: 2` (3, 4 …) right after its title –
`{id:"hj6", title:"Fallbeispiele", tier: 2, qs: () => […]}`. It is shown with ◆◆ and opens
when every set of the next lower tier in the tile reached 80 % in a whole run. Use it for
cases, decisions and exam-style questions; keep the basic sets (tier 1) short.

## Shared helpers of Family Campus

`content/` holds helpers any tile can use by name; the build looks for a
file in my-family's `tiles/` first, then in Family Campus's `content/`:

| File | Use |
| --- | --- |
| `math_common.js` | `"module": "math_common.js+my_tile.js"` – random numbers, evaluating and formatting expressions (`calc`, `show`), accepted spellings (`variants`), fractions and powers as HTML (`fr`, `pw`), `gcd`, `lcm`, primes, factorisation |
| `math.css` | `"css": "math.css"` – styles for fractions and figures |
| `prim_extension.js` | `"extension": "prim_extension.js"` – question type `prim` (English texts) |

## Extensions

A tile that needs more than the standard types brings an **extension**
(`"extension": "my_extension.js"` in the catalogue): code inserted at the end
of the page, defining

- `const EXTRA_TYPES = { mytype(q, card, finish) { … } }` – extra question
  types; call `finish(ok, solutionHtml)` once;
- `const LEARN_HOOKS = [card => { … }]` – widgets for the summary sheet (e.g.
  an animation for elements with a class).

`content/prim_extension.js` (question type `prim`) is an example. Helpers that
the summary sheet needs while `MODULES` is defined (constants, figures) go
into a module placed **before** the content module (`"module": "figures.js+tile.js"`).

## Catalogue entry

```json
{ "id": "year6-math-fractions", "module": "math_common.js+math_fractions.js", "css": "math.css",
  "extension": "", "title": "Fractions", "lang": "en", "description": "…", "date": "2026-11-20",
  "area": "school", "level": "year6", "subjects": ["math"], "topics": ["Fractions"],
  "cover": "covers/year6-math-fractions.svg" }
```

- `id`: English, `<level>-<subject>-<topic>` or `<area>-<subject>-<topic>`.
- `lang`: content language (BCP 47). Tiles are not translated; a tile in
  another language than the UI gets a small badge ([languages.md](languages.md)).
- `area`, `level`, `subjects`: ids from my-family (ADR-0004).
- `cover`: a 16:10 SVG (800 × 500).
- `date`: when the tile was added – it is "new" for 14 days and appears in
  "What's new?" for 60 days.
- `updated`, `note` (optional): when and how the tile was improved, e.g.
  `"updated": "2026-12-02", "note": {"en": "More pictures", "de": "Mehr Bilder"}`
  (plain text in the tile's language is fine too). They put the tile into
  "What's new?" again (ADR-0018); keep the note short and say what learners
  notice.

## Test

```bash
python3 tools/build.py <campus>                         # or tools/campus-build.sh in my-family
python3 tools/selftest.py build/www/exercises/*/index.html
```

The self test renders every question of every set several times in headless
Chromium and checks options, accepted answers, matching and sorting
consistency. Also look at new pages at phone width (about 400 px) and check
generated maths independently.

## Content rules

- Narrow tiles: one topic per tile, aimed at upcoming exams and weaknesses.
- No person names in tiles; tiles must be reusable.
- Content from own work or official sources; never copy teaching material
  (ADR-0013). Fix errors in sources and say so.
- `de-CH` content writes ss, never ß – also in accepted answers
  (`tools/check_de_ch.py`).
