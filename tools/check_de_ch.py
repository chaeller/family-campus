"""Swiss German writes ss, never ß (ADR-0012). Checks the de-CH content of my-family:
tiles with lang de-CH (their modules and catalogue texts), my-family's locales de and de-CH
(they end up in the de-CH UI), and – if my-family's default locale is de-CH – exams,
release notes and campus.json. Exit code 1 if a ß is found.
usage: python3 check_de_ch.py [my-family dir]"""
import json, os, sys

inst = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
load = lambda name, default=None: json.load(open(os.path.join(inst, name), encoding="utf-8")) if os.path.exists(os.path.join(inst, name)) else default
cfg = load("campus.json", {})
found = []
def check_text(where, text):
    if "ß" in text: found.append(where)
for t in load("tiles.json", []):
    if not str(t.get("lang") or cfg.get("defaultLocale", "")).startswith("de-CH"): continue
    check_text(f"tiles.json: {t['id']}", json.dumps(t, ensure_ascii=False))
    for m in t["module"].split("+") + [t.get("extension")]:
        if m and os.path.exists(os.path.join(inst, "tiles", m)):
            check_text(f"tiles/{m}", open(os.path.join(inst, "tiles", m), encoding="utf-8").read())
if "de-CH" in cfg.get("locales", []):
    for loc in ("de", "de-CH"):
        check_text(f"locales/{loc}.json", json.dumps(load(f"locales/{loc}.json", {}), ensure_ascii=False))
if cfg.get("defaultLocale") == "de-CH":
    for name in ("exams.json", "campus.json"):   # tile notes ("What's new?") are checked with tiles.json above
        check_text(name, json.dumps(load(name, {}), ensure_ascii=False))
for f in sorted(set(found)): print("ß in de-CH content (use ss):", f)
sys.exit(1 if found else 0)
