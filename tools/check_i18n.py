"""Checks the locale catalogues (ADR-0012, spec B-17). Exit code 1 on problems.

- every key of en exists in de and the other way round (de is the base of de-DE and de-CH);
- regional catalogues (de-CH, de-DE) only hold keys that exist in de;
- every key used in the pages, i18n.js users and the quiz engine exists in en; unused keys are listed;
- de-CH (merged: de + de-CH) contains no ß – Swiss German writes ss;
- plural objects have at least "one" and "other".
usage: python3 tools/check_i18n.py"""
import glob, json, os, re, sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = lambda tag: json.load(open(os.path.join(APP, "www", "locales", tag + ".json"), encoding="utf-8"))
en, de = L("en"), L("de")
problems, notes = [], []
for a, b, an, bn in ((en, de, "en", "de"), (de, en, "de", "en")):
    problems += [f"{k}: in {an}, missing in {bn}" for k in sorted(set(a) - set(b))]
for tag in ("de-CH", "de-DE"):
    problems += [f"{k}: in {tag}, but not in de" for k in sorted(set(L(tag)) - set(de))]
for tag, cat in (("en", en), ("de", de)):
    for k, v in cat.items():
        if isinstance(v, dict) and not {"one", "other"} <= set(v):
            problems.append(f"{k}: plural in {tag} needs 'one' and 'other'")
merged_ch = {**de, **L("de-CH")}
problems += [f"{k}: ß in de-CH" for k, v in merged_ch.items() if "ß" in json.dumps(v, ensure_ascii=False)]

# keys used in the code: t("…"), T("…"), tr("…"), I18n.t("…"), data-i18n="…", data-i18n-attr="attr:…"
used = set()
for f in glob.glob(os.path.join(APP, "www", "*.html")) + [x for x in glob.glob(os.path.join(APP, "www", "*.js")) if not x.endswith("i18n.js")] + [os.path.join(APP, "engine", "quiz.html")]:
    s = open(f, encoding="utf-8").read()
    used |= set(re.findall(r'\b(?:t|T|tr|I18n\.t)\("([a-zA-Z][\w.-]*)"', s))
    used |= set(re.findall(r'data-i18n="([\w.-]+)"', s))
    used |= {k for attr in re.findall(r'data-i18n-attr="([^"]+)"', s) for k in re.findall(r':([\w.-]+)', attr)}
    used |= {"error." + c for c in re.findall(r'"error":\s*"(\w+)"', s)}
server = open(os.path.join(APP, "server", "server.py"), encoding="utf-8").read()
used |= {"error." + c for c in re.findall(r'"error": "([a-z_]+)"', server) if c not in ("bad request", "not found")}
used.add("locale.name")   # read by tools/build.py (names in the language dropdowns)
used = {k for k in used if not k.endswith(".")}   # prefixes of keys built at run time ("error." + code)
problems += [f"{k}: used in the code, missing in en" for k in sorted(used - set(en))]
dynamic = ("subject.", "error.")   # keys built at run time
notes += [f"{k}: not used" for k in sorted(set(en) - used) if not k.startswith(dynamic)]

for n in notes: print("note:", n)
for p in problems: print("PROBLEM:", p)
print(f"{len(en)} keys, {len(used)} used, {len(problems)} problems")
sys.exit(1 if problems else 0)
