# ADR-0012: Languages and locales

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Families use Family Campus in different languages and regions. "German" alone is
not enough: Germany writes ß, Switzerland ss; dates and numbers differ.
Learning content is written in one language and is not translated.

## Decision

- Code, identifiers, comments, logs and documentation are English.
- The UI has no hard-coded texts: every text is a key in a catalogue per
  **locale** (BCP 47) in `www/locales/`. `en` is the default and fallback;
  regional catalogues hold only their differences (`de-CH` → `de` → `en`).
  1.0 ships `en`, `de`, `de-DE` and `de-CH` (ss, never ß).
- The locale is chosen per person and stored on the server; otherwise the
  browser's languages are matched against the locales my-family offers,
  then my-family default, then `en`.
- Dates, numbers, relative times and plurals come from the browser's `Intl`
  APIs; the currency is set by my-family.
- Right-to-left is prepared (`dir` from the locale, CSS logical
  properties), not translated yet.
- Tiles keep their content language (`lang`); a tile in another language
  than the UI gets a small language badge. A small own `i18n.js`, no library.
- `tools/check_i18n.py` checks missing keys, plural forms and ß in `de-CH`.

## Consequences

+ A new language is one JSON file; regional formats are right without extra code.
− Every UI text needs a key and at least an English and a German version.

## Alternatives considered

- **One language only:** excludes most families.
- **An i18n library:** more than needed, and the pages' first dependency.
- **Locale per device only:** people would choose again on every device.
