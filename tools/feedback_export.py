"""Prints the reported questions of a Family Campus database as JSON (ADR-0019). Read-only.
Runs where the database is: tools/campus-feedback.sh pipes it into the running container
(`docker exec -i <container> python3 - /data/campus.sqlite`), or locally with a data folder.
Standard library only; it must run on the Python of the image.
usage: python3 feedback_export.py <campus.sqlite>"""
import json, sqlite3, sys

db = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
db.row_factory = sqlite3.Row
if not db.execute("SELECT 1 FROM sqlite_master WHERE name='feedback'").fetchall():
    rows = []   # a Family Campus from before ADR-0019: nothing can have been reported
else:
    rows = db.execute("""SELECT f.id, u.name AS user, f.exercise, f.set_id, f.qkey, f.reason, f.note, f.question, f.qjson,
                                f.given, f.ok, f.mode, f.build, f.ts
                         FROM feedback f JOIN users u ON u.id=f.user_id ORDER BY f.id""").fetchall()
out = []
for r in rows:
    d = dict(r)
    d["q"] = json.loads(d.pop("qjson") or "{}")
    d["ok"] = None if d["ok"] is None else bool(d["ok"])
    out.append(d)
json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
