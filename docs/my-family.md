# my-family reference

my-family holds everything that belongs to one family (ADR-0011): usually the
folder `my-family/` in the Family Campus checkout, created by `tools/new-campus.sh` and
ignored by Family Campus's git. `tools/campus-build.sh` merges it with Family Campus into
`my-family/build/www`. `example-family/` is a complete small family: Family Campus's demo
and the starting point that `tools/new-campus.sh` copies – change your copy,
never `example-family/` itself.

## campus.json

```json
{
 "name": "Family Campus",
 "prefix": "/campus",
 "locales": ["en", "de-CH"],
 "defaultLocale": "en",
 "currency": "EUR",
 "appTiles": true,
 "subjects": { "carpentry": { "icon": "🪚" } },
 "categories": [
  { "id": "school", "areas": [
    { "id": "school", "name": {"en": "School", "de": "Schule"}, "levelOnly": true,
      "levels": [ {"id": "year5", "name": {"en": "Year 5", "de": "Klasse 5"}}, {"id": "year6", "name": {"en": "Year 6", "de": "Klasse 6"}} ] } ] },
  { "id": "vocational", "areas": [
    { "id": "carpenter", "name": {"en": "Carpenter"}, "short": {"en": "Carpenter"},
      "levels": [ {"id": "y1", "name": {"en": "1st year"}}, {"id": "y2", "name": {"en": "2nd year"}} ] } ] }
 ],
 "people": {
  "Anna": { "color": "#e64980", "area": "school", "level": "year6",
            "focus": [ {"exercise": "demo-internet-basics", "reason": {"en": "Basics for the next test"}} ] },
  "Ben":  { "color": "#2f9e44", "area": "carpenter", "level": "y2" }
 }
}
```

| Field | Meaning |
| --- | --- |
| `name` | Title of the site: browser tab, headings of the login and home page, name of the installed app (default "Family Campus"; the footer always says "Family Campus <version>", the software) |
| `shortName` | Optional: short name under the app icon on phones (default: `name`) |
| `prefix` | URL path of the site, e.g. `/campus` behind a reverse proxy; `/` for the root. Built into the image (`FC_PREFIX`) |
| `locales`, `defaultLocale` | Languages offered and the default ([languages.md](languages.md)) |
| `currency` | ISO code for amounts in my-family's content |
| `appTiles` | `false` leaves out Family Campus's demo tile |
| `subjects` | Own subjects: id → `{ "icon": "…" }`; their names go into `locales/<tag>.json` as `subject.<id>`. Family Campus knows common subjects (`math`, `german`, `english`, `french`, `history`, `science`, `media-it`, `law`, …) |
| `categories` | Merged by `id` into Family Campus's categories `school`, `vocational`, `studies`, `further`, `general`; an area with the same id replaces Family Campus's, new areas are added. Categories without areas are hidden |
| area `levels` | Ordered `{id, name}`; empty for areas without levels |
| area `levelOnly` | A person of this area starts on exactly their level (e.g. "4th year"); otherwise on everything up to their level ("up to 2nd year" – e.g. for a shortened training). They can always choose another level |
| area `short` | Short name in badges: "Carpenter · 1st year"; without it badges show the level alone ("Year 6") |
| area `forAll` | Content for everybody (Family Campus's `general` area): shown with "All" or its own category |
| area `short` | Short name for filters and badges |
| `people` | Name → `color` (hex), current `area` and `level` (ids), optional `focus` (tiles in recommended order with a `reason`) |

Names (`name`, `short`, level names, `reason`) are a plain string or an
object per locale (`{"en": …, "de": …}`; the fallback chain applies).

Logins are **not** here: `data/campus.env` locally and `/data/campus.env` in
the volume (`CAMPUS_USERS=Name[:admin],…`,
`CAMPUS_PASSWORD_<NAME>=…`). Every person in `people` needs a login and the
other way round.

## exams.json

```json
[ { "date": "2026-12-08", "people": ["Anna"], "subject": "media-it", "topic": "Internet basics",
    "exercise": "demo-internet-basics",
    "goals": ["I can explain what a router, a server and a provider do."] } ]
```

`exercise`: the tile to practise with – one id, or a list of ids
(`["demo-internet-basics", "…"]`), or left out while there is none yet.

Upcoming exams appear at the top of the home page (the next 14 days first)
with their learning goals and every linked tile with the progress of the
person whose exam it is ("3/5 sets · Ø 72 %"; parents looking at "everyone"
see it per person). An exam without a tile says "No tiles yet". Learners only
receive their own exams; parents see everyone's. Past exams can be removed.

## tiles.json and tiles/

Own tiles, same fields as Family Campus's `content/catalog.json` – see
[tiles.md](tiles.md):

```json
[ { "id": "year6-math-fractions", "module": "math_common.js+math_fractions.js", "css": "math.css",
    "title": "Fractions", "lang": "en", "description": "…", "date": "2026-11-20",
    "area": "school", "level": "year6", "subjects": ["math"], "topics": ["Fractions"],
    "cover": "covers/year6-math-fractions.svg" } ]
```

Paths (`module`, `extension`, `css`, `cover`) are relative to `tiles/`. Tile
ids and set ids never change once used: progress is stored by them.

## locales/

Own texts per locale, merged over Family Campus's catalogues: names of own subjects
(`"subject.carpentry": "Carpentry"`) or a different wording of a Family Campus text.

## deploy.env

No secrets – committed if my-family is its own git repository.

| Variable | Meaning |
| --- | --- |
| `FC_APP_VERSION` | the Family Campus version this campus is built with (the build stops on a mismatch – after `git pull` of Family Campus, set it to Family Campus's new `VERSION`) |
| `FC_IMAGE` | Image name, e.g. `registry.example.org/family-campus` |
| `FC_CONTAINER`, `FC_VOLUME` | Container and volume on the server |
| `FC_HOST`, `FC_PORT` | ssh host for deployments, port on the host |
| `FC_PREFIX`, `FC_PUBLIC_URL` | URL path (as `prefix`), public address for checks |
| `FC_MIGRATE_FROM_VOLUME`, `FC_MIGRATE_FROM_CONTAINER` | Optional: copy an old volume once into `FC_VOLUME` and replace the old container (`/fc-deploy`) |

## curricula.md (optional)

A summary of the official curricula of my-family's areas, so that tiles
land in the right level and subject. `fc-ingest` and `fc-improve` read it
when it exists; without it they ask. Plain Markdown, one section per area
(the area id from `campus.json` in the heading):

- **Source:** the official documents with links and the date they were
  checked (training ordinance, training plan, school curriculum). Keep
  downloaded PDFs in `material/` – never committed.
- **Duration and levels:** how the official years map onto the area's
  `levels` (e.g. a shortened training).
- **Topics per level:** what is taught in which year or semester, and the
  subjects my-family uses for them.

See `example-family/curricula.md`.

## feedback.json

Written by `tools/campus-feedback.sh`: the questions learners reported on the
live site (ADR-0019), with names and their comments – it stays in my-family.
`/fc-feedback` adds `handled` (date, outcome, what was done) to each report it
processed; the script keeps that field when it fetches again.

## What's new? and the version

my-family has no version, changelog or release notes of its own (ADR-0018).
The footer shows "Family Campus <version> · content of <date>":

- **The date of the content** is the date of my-family's last commit (if it
  is its own git repository; otherwise the day of the build). With
  uncommitted changes the local preview shows today's date; only a test image
  (`campus-image.sh --dev`) says "test version" in the footer.
- **"What's new?"** lists the new and improved tiles of the last 60 days from
  `tiles.json` – a tile's `date` when it was added, its `updated` and `note`
  when it was improved ([tiles.md](tiles.md#catalogue-entry)) – followed by
  the notes of Family Campus for learners.
- After an update of Family Campus set `FC_APP_VERSION` in `deploy.env`; its
  news come with it.
