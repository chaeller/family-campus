# Languages and locales

Family Campus separates **language** and **region** (ADR-0012). The UI uses
locales (BCP 47): `en` (default and fallback), `de` (German, spelling of
Germany with ß), `de-DE` and `de-CH` (Swiss German: ss instead of ß, the
usual Swiss quotes «…» – „…“ would be correct too –, Swiss terms).

## Which locale applies

1. The person's choice (account menu → language), stored on the server and
   valid on all their devices.
2. Before login, or without a choice: the browser's languages, matched
   against the locales my-family offers (`de-AT` → a `de` locale).
3. my-family's `defaultLocale`, then `en`.

A choice on the login page's switcher becomes the person's choice at the
first login if they have none yet.

## Catalogues

`www/locales/<tag>.json` holds flat keys:

```json
{ "filter.reset": "Reset",
  "repeat.due": { "one": "{count} question is due", "other": "{count} questions are due" } }
```

- `{name}` placeholders; numbers are formatted for the locale.
- Plurals: an object with the forms of `Intl.PluralRules` (`one`, `other`,
  and for other languages `few`, `many`, …).
- Fallback chain: `de-CH` → `de` → `en`. A regional catalogue holds only its
  differences (`de-CH.json` is small). A missing key falls back to English.
- my-family adds or overrides keys in its own `locales/<tag>.json` (e.g.
  `subject.<id>` for its own subjects).

Dates, times, numbers, percentages and relative days come from the browser's
`Intl` APIs (`I18n.date`, `I18n.number`, `I18n.percent`, `I18n.days`), never
from hand-written formats. Amounts use my-family's `currency`.

## In pages

```html
<button data-i18n="filter.reset"></button>
<input data-i18n-attr="placeholder:quiz.yourAnswer">
```

```js
await I18n.ready;
I18n.t("repeat.due", { count: 3 });
I18n.date("2026-11-24", { weekday: "short", day: "numeric", month: "short" });
```

The quiz engine uses `T(key, params)`. Server errors are codes
(`{"error": "bad_login"}`), shown as `error.<code>`.

## Right-to-left

`<html dir>` follows the locale (`ar`, `he`, `fa`, `ur` → `rtl`), and the CSS
uses logical properties (`margin-inline-start`, `text-align: start`,
`inset-inline-end`). Use them in new code too.

## Tiles

Tiles are content and are not translated. Each has a content language
(`lang`); all tiles are shown whatever the UI language, and a tile in another
language than the UI gets a small badge ("DE").

## Adding a language

1. Copy `www/locales/en.json` to `www/locales/<tag>.json` and translate every
   value (keep keys and placeholders). `locale.name` is the name of the
   language in itself, shown in the language dropdowns (e.g. "Deutsch
   (Schweiz)"). For a regional variant of an existing language, add only the
   differences – always including its own `locale.name`.
2. Add the plural forms your language needs.
3. `python3 tools/check_i18n.py` – checks missing keys, plural objects and ß
   in `de-CH`. (For a new base language, extend the check's list.)
4. Look at the pages in the new locale (and with `dir="rtl"` for an RTL
   language) at phone and desktop width.
5. Offer it in my-family (`campus.json` `locales`).
