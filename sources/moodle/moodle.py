#!/usr/bin/env python3
"""Source module "moodle" of Family Campus: fetch upcoming exams, assignments and their attachments from
Moodle, the learning platform used by many (vocational) schools - with the learner's own account.
Read sources/README.md and sources/moodle/README.md (legal notes) before using it.

STATUS: tested with one school (Moodle 4.5); other schools may enter exams differently.

The Moodle account belongs to the learner (e.g. an apprentice), not to the parents: the learner runs
`token` and types the password; the password is never stored. Run it in the Family Campus folder (it uses my-family/)
or pass --campus <dir>. Settings come from Family Campus's .env (next to .env.example), per learner (first name in capitals):

  MOODLE_PEOPLE=Ben                      learners with a Moodle account (names as in campus.json)
  MOODLE_BEN_URL=https://moodle.school.ch
  MOODLE_BEN_ICAL=https://…/calendar/export_execute.php?…   optional: calendar export link (a secret)
  MOODLE_BEN_TOKEN=…                     optional: security key from Moodle's preferences (SSO sites)

Everything goes to <campus>/material/moodle/<person>/ (never committed, never in the Docker image).

  python3 sources/moodle/moodle.py token --person Ben
      The learner logs in once (username and password typed, not stored); the token of the
      Moodle app service is saved in material/moodle/ben/.token (mode 600).
  python3 sources/moodle/moodle.py check [--person Ben]
      Is the token (or the calendar link) valid, which functions does the site allow?
  python3 sources/moodle/moodle.py fetch [--person Ben] [--days 120] [--past-days 0] [--all] [--no-documents]
      Exams (by keywords and quizzes) of the next --days into material/moodle/<person>/exams.json,
      attachments of assignments into material/moodle/<person>/documents/. --all keeps every event.

Without a token, fetch uses the calendar link (dates and descriptions only, no documents).
Requires Python 3.10+, standard library only.
"""
import argparse, datetime as dt, getpass, html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

# my-family folder: --campus <dir>, else the current folder if it has campus.json, else my-family/ of Family Campus
APP = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if "--campus" in sys.argv[:-1]:   # read before argparse, so that the paths below know it
    i = sys.argv.index("--campus"); ROOT = os.path.abspath(sys.argv[i + 1]); del sys.argv[i:i + 2]
else:
    ROOT = os.getcwd() if os.path.exists("campus.json") else os.path.join(APP, "my-family")
if not os.path.exists(os.path.join(ROOT, "campus.json")):
    sys.exit(f"No my-family in {ROOT} (campus.json missing) - create it with tools/new-campus.sh or pass --campus <dir>")
OUT = os.path.join(ROOT, "material", "moodle")   # downloads of this module (never committed)

SERVICE = "moodle_mobile_app"   # the service of the official Moodle app, enabled by default on https sites
PAUSE = 0.5                     # seconds between requests - be gentle
UA = "FamilyCampus-SourceModule/1.0 (personal use; +https://github.com/chaeller/family-campus)"
# words that mark an exam in titles and descriptions (Moodle has no exam type); quizzes count as exams too
EXAM_WORDS = re.compile(r"prüfung|pruefung|\btest\b|lernkontrolle|lernzielkontrolle|\blzk\b|klausur|examen|\bexam\b|"
                        r"leistungsbeurteilung|leistungsnachweis|probe|épreuve|epreuve|contrôle|verifica|assessment", re.I)
NEEDED = ["core_webservice_get_site_info", "core_enrol_get_users_courses", "core_calendar_get_action_events_by_timesort",
          "core_calendar_get_calendar_events", "mod_assign_get_assignments"]


def load_env():
    path = os.path.join(APP, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    people = [p.strip() for p in os.environ.get("MOODLE_PEOPLE", "").split(",") if p.strip()]
    if not people:
        sys.exit(f"Please fill in Family Campus's .env ({path}, template .env.example): MOODLE_PEOPLE and MOODLE_<NAME>_URL")
    cfg = {}
    for p in people:
        key = re.sub(r"[^A-Z0-9]", "_", p.upper())
        c = {k: os.environ.get(f"MOODLE_{key}_{k}", "").strip() for k in ("URL", "ICAL", "TOKEN")}
        c["URL"] = c["URL"].rstrip("/")
        if not c["URL"] and not c["ICAL"]:
            sys.exit(f"Please fill in Family Campus's .env: MOODLE_{key}_URL (or MOODLE_{key}_ICAL)")
        c["folder"] = os.path.join(OUT, p.lower())
        cfg[p] = c
    return cfg


def pick(cfg, person):
    if not person:
        return list(cfg.items())
    if person not in cfg:
        sys.exit(f"{person} is not in MOODLE_PEOPLE ({', '.join(cfg)})")
    return [(person, cfg[person])]


def _open(url, data=None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data is not None else None,
                                 headers={"User-Agent": UA, "Accept": "application/json, text/calendar, */*"})
    time.sleep(PAUSE)
    return urllib.request.urlopen(req, timeout=60)


def token_file(c):
    return os.path.join(c["folder"], ".token")


def get_token(c):
    if c["TOKEN"]:
        return c["TOKEN"]
    path = token_file(c)
    return open(path, encoding="utf-8").read().strip() if os.path.exists(path) else ""


def call(c, token, function, **params):
    """One web service call (REST, JSON). Array parameters as lists or dicts, e.g. courseids=[5, 7]."""
    data = {"wstoken": token, "wsfunction": function, "moodlewsrestformat": "json"}
    def flat(prefix, v):
        if isinstance(v, (list, tuple)):
            for i, x in enumerate(v):
                flat(f"{prefix}[{i}]", x)
        elif isinstance(v, dict):
            for k, x in v.items():
                flat(f"{prefix}[{k}]", x)
        else:
            data[prefix] = int(v) if isinstance(v, bool) else v
    for k, v in params.items():
        flat(k, v)
    res = json.loads(_open(c["URL"] + "/webservice/rest/server.php", data).read().decode("utf-8", "replace"))
    if isinstance(res, dict) and "exception" in res:
        raise RuntimeError(f"{function}: {res.get('errorcode')} - {res.get('message')}")
    return res


def _text(fragment):
    """HTML → readable text with line breaks."""
    t = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</tr>|</h\d>", "\n", fragment or "", flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return "\n".join(l.strip() for l in t.splitlines() if l.strip())


def _links(fragment):
    return [{"url": html.unescape(u), "text": _text(n)} for u, n in
            re.findall(r'<a\s[^>]*?href="(https?://[^"]+)"[^>]*>(.*?)</a>', fragment or "", re.S)
            if "/pluginfile.php" not in u]


def _date(ts):
    return dt.datetime.fromtimestamp(int(ts)).date().isoformat() if ts else None


def _kind(title, text, module):
    if module == "quiz" or EXAM_WORDS.search(title or "") or EXAM_WORDS.search((text or "")[:300]):
        return "exam"
    return module or "event"


# ---------- commands ----------

def cmd_token(cfg, a):
    for person, c in pick(cfg, a.person):
        if not c["URL"]:
            sys.exit(f"MOODLE_{person.upper()}_URL is missing")
        print(f"{person}: log in to {c['URL']} - only {person} should type the password (it is not stored).")
        user = input("Moodle username: ").strip()
        pw = getpass.getpass("Moodle password: ")
        try:
            res = json.loads(_open(c["URL"] + "/login/token.php", {"username": user, "password": pw, "service": SERVICE}).read())
        finally:
            pw = None
        if not res.get("token"):
            print(f"❌ No token: {res.get('errorcode') or res.get('error')}. If the school logs in with Microsoft, "
                  "edu-ID or another single sign-on, use a security key instead (see README).")
            continue
        os.makedirs(c["folder"], exist_ok=True)
        with open(token_file(c), "w", encoding="utf-8") as f:
            f.write(res["token"])
        os.chmod(token_file(c), 0o600)
        print(f"✅ Token saved in {os.path.relpath(token_file(c), ROOT)}.")


def public_config(c):
    """The site's public settings for the Moodle app (no login): is the web service on, how do users log in?"""
    req = urllib.request.Request(c["URL"] + "/lib/ajax/service-nologin.php?info=tool_mobile_get_public_config",
                                 data=json.dumps([{"index": 0, "methodname": "tool_mobile_get_public_config", "args": {}}]).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    res = json.loads(urllib.request.urlopen(req, timeout=60).read())[0]
    if res.get("error"):
        raise RuntimeError(f"public config: {(res.get('exception') or {}).get('errorcode')}")
    return res["data"]


def cmd_check(cfg, a):
    for person, c in pick(cfg, a.person):
        print(f"\n{person}:")
        if c["URL"]:
            try:
                p = public_config(c)
                login = {1: "username and password (token works)", 2: "in the browser (single sign-on: use a security key)",
                         3: "embedded browser (single sign-on: use a security key)"}.get(p.get("typeoflogin"), "unknown")
                print(f"  site: {p.get('sitename')} · web service for Family Campus: {'on' if p.get('enablemobilewebservice') else 'OFF'}"
                      f" · login: {login}")
            except (RuntimeError, ValueError, KeyError, urllib.error.URLError) as ex:
                print(f"  ⚠️  public config not readable ({ex}) - is MOODLE_..._URL the Moodle start address?")
        token = get_token(c)
        if token and c["URL"]:
            try:
                info = call(c, token, "core_webservice_get_site_info")
                allowed = {f["name"] for f in info.get("functions", [])}
                courses = call(c, token, "core_enrol_get_users_courses", userid=info["userid"])
                print(f"  ✅ token valid: {info.get('sitename')} (Moodle {info.get('release')}), {len(courses)} course(s)")
                missing = [f for f in NEEDED if allowed and f not in allowed]
                print("  ⚠️  not allowed on this site: " + ", ".join(missing) if missing else "  ✅ all needed functions allowed")
                print("  files download: " + ("allowed" if info.get("downloadfiles") else "not allowed (no documents)"))
            except (RuntimeError, urllib.error.URLError) as ex:
                print(f"  ❌ token: {ex}")
                if "invalidtoken" in str(ex):
                    print("     The key must be the one of the service «Moodle mobile web service» (preferences → security keys),\n"
                          "     not the RSS key - or leave MOODLE_..._TOKEN empty and run «token».")
        else:
            print("  no token (run «token», or set MOODLE_<NAME>_TOKEN)")
        if c["ICAL"]:
            try:
                events = parse_ical(_open(c["ICAL"]).read().decode("utf-8", "replace"))
                print(f"  ✅ calendar link: {len(events)} event(s)")
            except urllib.error.URLError as ex:
                print(f"  ❌ calendar link: {getattr(ex, 'code', '') or ex.reason}")


# calendar titles carry a suffix ("Prüfung X beginnt", "Übung 7 ist fällig.") - the activity name is enough
SUFFIX = re.compile(r"\s+(beginnt|endet|ist fällig\.?|ist zu erledigen\.?|opens|closes|is due\.?|should be completed\.?|"
                    r"s'ouvre|se ferme|est à remettre\.?)\s*$", re.I)


def fetch_ws(c, token, a):
    """Events and assignments through the web service; one entry per activity (a quiz's open and close
    events, an assignment's due event and the assignment itself are merged; the earliest date is kept)."""
    now = int(time.time())
    start, end = now - a.past_days * 86400, now + a.days * 86400
    info = call(c, token, "core_webservice_get_site_info")
    courses = {x["id"]: x.get("fullname") or x.get("shortname") for x in call(c, token, "core_enrol_get_users_courses", userid=info["userid"])}
    entries = {}

    def add(key, date, subject, title, desc, module):
        title = SUFFIX.sub("", html.unescape(title or ""))
        e = {"id": key, "date": date, "subject": subject, "type": _kind(title, _text(desc), module), "title": title,
             "goals": _text(desc), "links": _links(desc), "documents": []}
        old = entries.get(key)
        if old:   # same activity: keep the earliest date and whatever text is there
            e["date"] = min(filter(None, [old["date"], date]), default=None)
            for k in ("goals", "links", "documents"):
                e[k] = old[k] or e[k]
        entries[key] = e
        return e

    seen = {}   # event id → key: the two calendar functions give "instance" differently (instance id vs. cmid)

    def key_of(e):
        if e["id"] not in seen:
            seen[e["id"]] = f"{e['modulename']}-{e['instance']}" if e.get("modulename") and e.get("instance") else f"event-{e['id']}"
        return seen[e["id"]]

    # course, site and own events (exams are often quizzes or course events) ...
    res = call(c, token, "core_calendar_get_calendar_events", events={"courseids": list(courses)},
               options={"timestart": start, "timeend": end, "userevents": 1, "siteevents": 1})
    for e in res.get("events", []):
        add(key_of(e), _date(e.get("timestart")), courses.get(e.get("courseid"), ""), e.get("name"), e.get("description", ""),
            e.get("modulename") or e.get("eventtype"))
    # ... and due dates of activities (assignments, quizzes)
    res = call(c, token, "core_calendar_get_action_events_by_timesort", timesortfrom=start, timesortto=end, limitnum=50)
    for e in res.get("events", []):
        add(key_of(e), _date(e.get("timesort") or e.get("timestart")),
            (e.get("course") or {}).get("fullname") or courses.get(e.get("courseid"), ""), e.get("name"), e.get("description", ""),
            e.get("modulename"))
    # assignment texts and attachments
    if courses:
        res = call(c, token, "mod_assign_get_assignments", courseids=list(courses))
        for course in res.get("courses", []):
            for asg in course.get("assignments", []):
                if not (start <= (asg.get("duedate") or 0) <= end):
                    continue
                # calendar events give the assignment id, action events the course module id (cmid) - match both
                key = next((k for k in (f"assign-{asg.get('cmid')}", f"assign-{asg['id']}") if k in entries), f"assign-{asg['id']}")
                e = add(key, _date(asg["duedate"]), course.get("fullname", ""), asg.get("name"),
                        asg.get("intro", ""), "assign")
                e["title"] = html.unescape(asg.get("name", ""))
                e["documents"] = [{"name": f["filename"], "url": f["fileurl"]} for f in asg.get("introattachments", [])]
    return list(entries.values()), info.get("downloadfiles", 1)


def parse_ical(text):
    """Events of an iCalendar file (Moodle's calendar export)."""
    text = re.sub(r"\r?\n[ \t]", "", text)   # unfold lines
    unesc = lambda v: v.replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")
    out = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        f = {}
        for line in block.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                f[k.split(";")[0].upper()] = unesc(v.strip())
        start = f.get("DTSTART", "")
        if re.fullmatch(r"\d{8}T\d{6}Z", start):
            d = dt.datetime.strptime(start, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc).astimezone().date()
        elif re.match(r"\d{8}", start):
            d = dt.date(int(start[:4]), int(start[4:6]), int(start[6:8]))
        else:
            continue
        out.append({"uid": f.get("UID", ""), "date": d, "title": f.get("SUMMARY", ""), "text": f.get("DESCRIPTION", ""),
                    "course": f.get("CATEGORIES", "")})
    return out


def fetch_ical(c, a):
    today = dt.date.today()
    lo, hi = today - dt.timedelta(days=a.past_days), today + dt.timedelta(days=a.days)
    entries = []
    for e in parse_ical(_open(c["ICAL"]).read().decode("utf-8", "replace")):
        if lo <= e["date"] <= hi:
            entries.append({"id": "ical-" + re.sub(r"[^A-Za-z0-9]+", "-", e["uid"] or f"{e['date']}-{e['title']}")[:80],
                            "date": e["date"].isoformat(), "subject": e["course"], "type": _kind(e["title"], e["text"], None),
                            "title": e["title"], "goals": e["text"].strip(),
                            "links": [{"url": u, "text": u} for u in re.findall(r"https?://\S+", e["text"])], "documents": []})
    return entries


def _download(c, token, doc, folder, prefix):
    os.makedirs(folder, exist_ok=True)
    name = re.sub(r'[\\/:*?"<>|]+', "_", f"{prefix}_{doc['name']}").strip()
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        url = doc["url"] + ("&" if "?" in doc["url"] else "?") + "token=" + urllib.parse.quote(token)
        with _open(url) as r:
            open(path, "wb").write(r.read())
    return os.path.relpath(path, ROOT)


def cmd_fetch(cfg, a):
    for person, c in pick(cfg, a.person):
        token = get_token(c)
        try:
            if token and c["URL"]:
                entries, can_download = fetch_ws(c, token, a)
                how = "web service"
            elif c["ICAL"]:
                entries, can_download, how = fetch_ical(c, a), False, "calendar link"
            else:
                print(f"⚠️  {person}: no token and no calendar link - run «token» first"); continue
        except (RuntimeError, urllib.error.URLError) as ex:
            print(f"❌ {person}: {ex if isinstance(ex, RuntimeError) else getattr(ex, 'code', '') or ex.reason}"); continue
        selected = [e for e in entries if a.all or e["type"] == "exam"]
        for e in selected:
            prefix = f"{e['date'] or 'no-date'}_{re.sub(r'[^A-Za-zÄÖÜäöü0-9]+', '-', e['subject'])[:30]}"
            for d in e["documents"]:
                if not a.no_documents and can_download:
                    try:
                        d["file"] = _download(c, token, d, os.path.join(c["folder"], "documents"), prefix)
                    except (OSError, urllib.error.URLError) as ex:
                        d["error"] = str(getattr(ex, "code", "") or type(ex).__name__)
                d.pop("url", None)   # the file url only works with the token - not kept
            e["person"] = person
        # merge with earlier runs (Moodle hides past events after a while)
        os.makedirs(c["folder"], exist_ok=True)
        path = os.path.join(c["folder"], "exams.json")
        old = {e["id"]: e for e in json.load(open(path, encoding="utf-8"))} if os.path.exists(path) else {}
        old.update({e["id"]: e for e in selected})
        merged = sorted(old.values(), key=lambda e: (e["date"] or "", e["subject"]))
        json.dump(merged, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n{person} ({how}): {len(selected)} of {len(entries)} entries → {os.path.relpath(path, ROOT)}")
        for e in sorted(selected, key=lambda e: e["date"] or ""):
            extra = f" · {len(e['documents'])} doc(s)" if e["documents"] else ""
            print(f"  {e['date']}  {e['type'][:6]:6}  {e['subject'][:28]:28}  {e['title'][:50]}{extra}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("token", help="the learner logs in once; saves the token (not the password)")
    t.add_argument("--person", required=True)
    c = sub.add_parser("check", help="check token and calendar link")
    c.add_argument("--person")
    f = sub.add_parser("fetch", help="fetch exams and attachments")
    f.add_argument("--person")
    f.add_argument("--days", type=int, default=120, help="how far ahead (default 120 days)")
    f.add_argument("--past-days", type=int, default=0, help="also the last N days")
    f.add_argument("--all", action="store_true", help="keep every event, not only exams")
    f.add_argument("--no-documents", action="store_true", help="do not download attachments")
    a = ap.parse_args()
    cfg = load_env()
    {"token": cmd_token, "check": cmd_check, "fetch": cmd_fetch}[a.cmd](cfg, a)


if __name__ == "__main__":
    main()
