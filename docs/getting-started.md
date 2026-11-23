# Getting started

Family Campus is the software. **my-family** is a folder with your family's
people, exams, tiles and deployment values: `my-family/` in your clone of Family
Campus. Family Campus's git ignores that folder, so you work in one place, get updates
of Family Campus with `git pull`, and your family's data never ends up in the Family Campus
repository.

```text
family-campus/              Family Campus (git clone) – you work here, Claude Code starts here
  my-family/                my-family (ignored by Family Campus's git)
    campus.json             name, URL path, languages, categories, areas, levels, people
    exams.json              upcoming exams with learning goals
    tiles.json, tiles/      your tiles and their content modules ("date", "updated", "note" → "What's new?")
    locales/                your own texts (e.g. names of your own subjects)
    curricula.md            optional: official curricula of your areas (where tiles belong)
    deploy.env              Family Campus version, image, container, volume, server, URL path (no secrets)
    data/                   logins (campus.env) and the local database – never committed
    material/               photos and documents for new tiles – never committed
```

Requirements: Python 3.11 or newer; for the self test of tiles
`pip install playwright && playwright install chromium`; Docker for images.

## 1. Look at the demo

```bash
git clone https://github.com/chaeller/family-campus.git && cd family-campus
python3 tools/build.py                       # Family Campus + example family → build/www
mkdir -p data && cp example-family/campus.env.example data/campus.env
python3 server/server.py --www build/www --data data --port 8080
```

Open <http://localhost:8080/>. Logins of the invented example family:
Anna / `anna` (school, year 6), Ben / `ben` (carpenter, 2nd year), Mia / `mia`
(parent, sees everyone).

## 2. Create my-family

```bash
tools/new-campus.sh            # → my-family/, started from the example family, built and tested
```

From now on you change only `my-family/`. Leave `example-family/` as it is: it is
Family Campus's demo, and `git pull` updates it.

Then:

1. Edit `my-family/campus.json` – see [my-family.md](my-family.md):
   - `name`, `prefix` (URL path, e.g. `/campus` behind a reverse proxy, or `/`),
     `locales` and `defaultLocale` (e.g. `["en"]` / `"en"`), `currency`;
   - `categories`: the areas and levels your family needs (a school with its
     years, an apprenticeship with its years, …);
   - `people`: everybody with a colour, current `area` and `level`.
2. Logins in `my-family/data/campus.env` (never committed):

   ```text
   CAMPUS_USERS=Anna,Ben,Mia:admin
   CAMPUS_PASSWORD_ANNA=…
   CAMPUS_PASSWORD_BEN=…
   CAMPUS_PASSWORD_MIA=…
   ```

   `Name[:admin]`; `admin` (parents) may see everybody's progress.
3. `my-family/curricula.md`: replace the invented example with the official
   curricula of your areas (where tiles belong), or delete it – see
   [my-family.md](my-family.md#curriculamd-optional).
4. Optional: `.env` in the Family Campus folder (copy `.env.example`) for the source
   modules you use (`sources/README.md`). Claude Code needs no other rules
   from you; it takes languages and people from `campus.json`.

## 3. Build and run locally

```bash
tools/campus-build.sh          # → my-family/build/www, self test of every tile
tools/campus-serve.sh          # preview; prints the address: http://localhost:8080/ plus your URL path (prefix)
```

Leave out Family Campus's demo tile with `"appTiles": false` in `campus.json`.

## 4. Add tiles

Write a content module in `my-family/tiles/`, register it in
`my-family/tiles.json`, build again – see [tiles.md](tiles.md). With Claude
Code (started in the Family Campus folder): `/fc-ingest "<topic idea>" --from web` or
`/fc-ingest fotos`.

## 5. Back up my-family (optional)

Make `my-family/` its own git repository and push it to a private server of
yours (Gitea, GitLab, …). Family Campus's git still ignores the folder; the two
repositories are independent, and `git clean -fdx` in Family Campus leaves a
folder with its own repository alone.

```bash
cd my-family && git init && git add -A && git commit -m "Our my-family"
git remote add origin <your private repository> && git push -u origin main
```

`tools/new-campus.sh --git` does the `git init` right away. With a
repository of its own, the date of your content is the date of your last
commit, and the image build checks that everything is committed.

## 6. Release and deploy

my-family has no version of its own: the footer shows the Family Campus
version and the date of your content, and "What's new?" lists your new and
improved tiles (ADR-0018). When you improve a tile, set `updated` and a short
`note` in `tiles.json`.

```bash
git -C my-family add -A && git -C my-family commit -m "…"   # with a repository of its own
tools/campus-image.sh          # image $FC_IMAGE:<version>-<date> and :latest (values from deploy.env)
```

First start on the server and updates: [operations.md](operations.md). With
Claude Code: `/fc-release`, then `/fc-deploy`.

## 7. Update Family Campus

```bash
git pull                       # in the Family Campus folder; my-family/ stays as it is
```

Then set `FC_APP_VERSION` in `my-family/deploy.env` to Family Campus's new
`VERSION` (the build stops until you do), build and test. Its notes for
learners come with it; its `CHANGELOG.md` says whether a new version needs
something from my-family.

## Another folder

The scripts and source modules use `my-family/` of Family Campus by default. It
can live elsewhere too: pass its folder (`tools/campus-build.sh
../other-folder`), set `FC_CAMPUS=<folder>`, or run the scripts inside that
folder.
