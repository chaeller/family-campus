"""Builds an exercise page from the quiz engine template and one or more content modules.

usage: build_page.py <engine.html> <a.js+b.js> <output index.html> <title> [extension.js] [extra.css] [lang]

- The modules section of the engine (between the "Modules & content" and "Navigation" markers) is
  replaced by the given modules.
- extension.js (optional) holds code a tile needs beyond the standard question types: extra question
  types as properties of an object literal assigned to EXTRA_TYPES, and functions in LEARN_HOOKS that
  run on the summary sheet (e.g. a construction animation). It is inserted before Campus.start().
- lang (optional): content language of the tile (BCP 47, e.g. "de-CH"); set on the page content so
  that screen readers and hyphenation use it. The UI around it follows the person's locale."""
import os, re, sys
base, mods, out, title = sys.argv[1:5]
ext = open(sys.argv[5], encoding="utf-8").read() if len(sys.argv) > 5 and sys.argv[5] else ""
extra_css = open(sys.argv[6], encoding="utf-8").read() if len(sys.argv) > 6 and sys.argv[6] else ""
lang = sys.argv[7] if len(sys.argv) > 7 else ""
s = open(base, encoding="utf-8").read()
start = s.index("/* ============================ Modules & content ============================ */")
end = s.index("/* ============================ Navigation ============================ */")
s = s[:start] + "/* ============================ Modules & content ============================ */\n" + "\n".join(open(m, encoding="utf-8").read().rstrip() for m in mods.split("+")) + "\n\n" + s[end:]
s = re.sub(r"<title>[^<]*</title>", "<title>" + title.replace("&", "&amp;") + "</title>", s, count=1)
if ext:
    anchor = "/* extensions of a tile (extra question types, summary-sheet widgets) are inserted here by tools/build_page.py */\n"
    assert s.count(anchor) == 1
    s = s.replace(anchor, anchor + ext.rstrip() + "\nif (typeof EXTRA_TYPES === \"object\") Object.assign(TYPES, EXTRA_TYPES);\n")
if extra_css:
    s = s.replace("</style>", extra_css.rstrip() + "\n</style>", 1)
if lang:
    s = s.replace('<div id="app">', f'<div id="app" lang="{lang}">', 1)
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(s)
print("wrote", out, len(s))
