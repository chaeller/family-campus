"""Builds the site of one campus: Family Campus's pages and tiles plus my-family's data and own tiles,
merged into an output folder (default: build/www). Family Campus's www/ stays free of family data.

usage: python3 tools/build.py [my-family dir] [--out build/www] [--content-date YYYY-MM-DD] [--commit SHA] [--dev]
       the folder defaults to $FC_CAMPUS, else example-family/ (the demo); for my-family use tools/campus-build.sh,
       which also passes the date of the content, the my-family commit and whether it is a test build (ADR-0018)

my-family folder holds:
  campus.json          name (title of the site), shortName (under the app icon), prefix, locales, defaultLocale, currency, subjects (icons), appTiles (false: without
                       Family Campus's demo tile), categories (own areas
                       are merged into Family Campus's categories by id), people (colour, area, level, focus, admin)
  exams.json           exams with learning goals
  locales/<tag>.json   own texts, e.g. names of own subjects ("subject.<id>")
  tiles.json           optional: own tiles, same fields as content/catalog.json "tiles" ("module" a+b.js,
                       "extension", "css", "cover" – paths relative to tiles/; "date" when added, optional
                       "updated" and "note" when improved – they make up "What's new?")
Output: pages, i18n, people.js (names and colours only – public for the login page), config.json (public),
exercises.json (catalogue, people without colours, exams), locales merged Family Campus + my-family, tiles built,
build.json (public: Family Campus version, date of the content, my-family commit, test build) and
release-notes.json ("What's new?": new and improved tiles plus the notes of Family Campus)."""
import argparse, datetime, html, json, os, re, shutil, subprocess, sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("campus", nargs="?", default=os.environ.get("FC_CAMPUS") or os.path.join(APP, "example-family"))
ap.add_argument("--out", default=os.path.join(APP, "build", "www"))
ap.add_argument("--content-date", default="", help="date of my-family's content (YYYY-MM-DD)")
ap.add_argument("--commit", default="", help="my-family commit the site is built from")
ap.add_argument("--dev", action="store_true", help="test build (uncommitted changes)")
a = ap.parse_args()
inst_dir, out = os.path.abspath(a.campus), os.path.abspath(a.out)
load = lambda p, default=None: json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default
inst = load(os.path.join(inst_dir, "campus.json"))
assert inst, f"no campus.json in {inst_dir}"

# ---- pages and assets of Family Campus
if os.path.exists(out): shutil.rmtree(out)
shutil.copytree(os.path.join(APP, "www"), out)

# ---- the name of the site (my-family's "name", e.g. "Our Family Campus"): titles, headings and the web-app
# manifest; the footer keeps "Family Campus <version>" (the software)
site = inst.get("name") or "Family Campus"
for page in ("login.html", "index.html", "progress.html"):
    f = os.path.join(out, page); s = open(f, encoding="utf-8").read()
    for old, new in (("<title>Family Campus</title>", f"<title>{html.escape(site)}</title>"),
                     ("<h1>Family Campus</h1>", f"<h1>{html.escape(site)}</h1>"),
                     ('content="Family Campus – ', f'content="{html.escape(site)} – '),
                     ('" – Family Campus"', json.dumps(" – " + site, ensure_ascii=False))):
        s = s.replace(old, new)
    open(f, "w", encoding="utf-8").write(s)
mf = os.path.join(out, "manifest.webmanifest"); m = json.load(open(mf, encoding="utf-8"))
m.update(name=site, short_name=inst.get("shortName") or site, lang=inst.get("defaultLocale", "en"))
open(mf, "w", encoding="utf-8").write(json.dumps(m, ensure_ascii=False, indent=2) + "\n")

# ---- categories: Family Campus's defaults, my-family adds areas (by category id) or whole categories
catalog = load(os.path.join(APP, "content", "catalog.json"))
cats = {c["id"]: dict(c, areas=list(c.get("areas", []))) for c in catalog["categories"]}
for c in inst.get("categories", []):
    base = cats.setdefault(c["id"], {"id": c["id"], "name": c.get("name", c["id"]), "areas": []})
    if c.get("name"): base["name"] = c["name"]
    known = {x["id"]: i for i, x in enumerate(base["areas"])}
    for area in c.get("areas", []):
        if area["id"] in known: base["areas"][known[area["id"]]] = area
        else: base["areas"].append(area)

# ---- tiles: Family Campus's and my-family's own, built from the engine template
engine = os.path.join(APP, "engine", "quiz.html")
# a file of a tile: in the tile's own folder, else one of Family Campus's shared helpers in content/
# (e.g. math_common.js, math.css, prim_extension.js)
def find(module_dir, name):
    own = os.path.join(module_dir, name)
    return own if os.path.exists(own) else os.path.join(APP, "content", name)
def build_tiles(tiles, module_dir):
    for t in tiles:
        mods = "+".join(find(module_dir, m) for m in t["module"].split("+"))
        ext = find(module_dir, t["extension"]) if t.get("extension") else ""
        css = find(module_dir, t["css"]) if t.get("css") else ""
        subprocess.run([sys.executable, "-I", os.path.join(APP, "tools", "build_page.py"), engine, mods,
                        os.path.join(out, "exercises", t["id"], "index.html"), t["title"], ext, css, t.get("lang", "")],
                       check=True, stdout=subprocess.DEVNULL)
        # cover: "cover" (path relative to the module folder) or <id>.cover.svg next to the modules
        cover = os.path.join(module_dir, t["cover"]) if t.get("cover") else os.path.join(module_dir, t["id"] + ".cover.svg")
        if os.path.exists(cover): shutil.copy(cover, os.path.join(out, "exercises", t["id"], "cover.svg"))
app_tiles = catalog["tiles"] if inst.get("appTiles", True) else []   # my-family may leave out Family Campus's demo tile
own_tiles = load(os.path.join(inst_dir, "tiles.json"), [])
build_tiles(app_tiles, os.path.join(APP, "content"))
build_tiles(own_tiles, os.path.join(inst_dir, "tiles"))

exercises = []
for t in app_tiles + own_tiles:
    ex = {k: v for k, v in t.items() if k not in ("module", "extension", "css", "cover")}
    ex["path"] = f"exercises/{t['id']}/"
    if os.path.exists(os.path.join(out, "exercises", t["id"], "cover.svg")): ex["image"] = ex["path"] + "cover.svg"
    page = open(os.path.join(out, ex["path"], "index.html"), encoding="utf-8").read()
    mods = page[page.index("/* ============================ Modules & content"):page.index("/* ============================ Navigation")]
    ex["sets"] = [{"id": i, "title": html.unescape(s)} for i, s in re.findall(r'\{id:"([a-z0-9]+)", title:"([^"]+)"', mods)]
    assert ex["sets"], f"{t['id']}: no sets found"
    exercises.append(ex)
seen = {}
for ex in exercises:   # progress is stored per person, exercise and set id
    for st in ex["sets"]:
        assert st["id"] not in seen, f'set id "{st["id"]}" used in {seen.get(st["id"])} and {ex["id"]}'
        seen[st["id"]] = ex["id"]

# ---- data files
people = inst.get("people", {})
dump = lambda name, obj: open(os.path.join(out, name), "w", encoding="utf-8").write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
dump("exercises.json", {
    "categories": list(cats.values()),
    "people": {n: {k: v for k, v in p.items() if k not in ("color", "admin")} for n, p in people.items()},
    "exercises": exercises,
    "exams": load(os.path.join(inst_dir, "exams.json"), [])})
config = {k: inst[k] for k in ("name", "locales", "defaultLocale", "currency", "subjects") if k in inst}
def catalog_of(tag):   # merged catalogue of a locale: en, then de, then de-CH (my-family's own keys last)
    parts = tag.split("-"); chain = ["en"] + ["-".join(parts[:i]) for i in range(1, len(parts) + 1) if "-".join(parts[:i]) != "en"]
    merged = {}
    for c in chain:
        merged.update(load(os.path.join(APP, "www", "locales", c + ".json"), {}))
        merged.update(load(os.path.join(inst_dir, "locales", c + ".json"), {}))
    return merged
# the name of each offered locale in its own language ("Deutsch (Schweiz)"), for the language dropdowns
config["localeNames"] = {tag: catalog_of(tag).get("locale.name", tag) for tag in inst.get("locales", ["en"])}
dump("config.json", config)
# ---- version and "What's new?" (ADR-0018): one version – Family Campus's; my-family's content is dated
vl = (open(os.path.join(APP, "VERSION"), encoding="utf-8").read().split() + ["", ""])[:2]
dump("build.json", {"version": vl[0] or "dev", "date": vl[1], "content": a.content_date, "commit": a.commit, "dev": a.dev})
NEWS_DAYS, NEWS_MAX = 60, 12
since = (datetime.date.fromisoformat(a.content_date) if a.content_date else datetime.date.today()) - datetime.timedelta(days=NEWS_DAYS)
news = []
for t in app_tiles + own_tiles:
    for kind, day in (("updated", t.get("updated")), ("new", t.get("date"))):
        if day and datetime.date.fromisoformat(day) >= since:
            news.append({"date": day, "kind": kind, "id": t["id"], "title": t["title"], "path": f"exercises/{t['id']}/",
                         **({"note": t["note"]} if kind == "updated" and t.get("note") else {})})
            break   # one line per tile: the latest change
news.sort(key=lambda n: n["date"], reverse=True)
dump("release-notes.json", {"content": news[:NEWS_MAX],
                            "app": load(os.path.join(APP, "release-notes.json"), {"unreleased": {}, "versions": []})})
people_js = open(os.path.join(APP, "www", "people.template.js"), encoding="utf-8").read()
open(os.path.join(out, "people.js"), "w", encoding="utf-8").write(people_js.replace(
    "/* LIST */[]", json.dumps([{"name": n, "color": p.get("color", "#6c6886")} for n, p in people.items()], ensure_ascii=False)))
os.remove(os.path.join(out, "people.template.js"))

# ---- locales: app catalogue plus my-family's own keys (my-family wins)
for f in sorted(os.listdir(os.path.join(inst_dir, "locales"))) if os.path.isdir(os.path.join(inst_dir, "locales")) else []:
    if f.endswith(".json"):
        merged = load(os.path.join(out, "locales", f), {})
        merged.update(load(os.path.join(inst_dir, "locales", f)))
        dump(os.path.join("locales", f), merged)

print(f"built {out}: {len(exercises)} tiles ({len(own_tiles)} own), {sum(len(e['sets']) for e in exercises)} sets, "
      f"{len(people)} people, locales {', '.join(inst.get('locales', ['en']))}")
