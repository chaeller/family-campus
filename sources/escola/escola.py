#!/usr/bin/env python3
"""Source module "escola" of Family Campus: fetch exams (Lernzielkontrollen) and their documents from
Escola, a school platform used by schools in Switzerland – with the parent account of your own family.
Read sources/README.md and sources/escola/README.md (legal notes) before using it.

Run it in the Family Campus folder (it uses my-family/), in the my-family folder, or pass --campus <dir>. Credentials come from Family Campus's .env
(next to .env.example; ESCOLA_URL = your school's Escola address, ESCOLA_USERNAME, ESCOLA_PASSWORD, ESCOLA_CHILDREN = first
names as shown in Escola). Everything downloaded goes to <campus>/material/escola/ (never committed,
never in the Docker image).

  python3 sources/escola/escola.py check [--new]
      Check the session. Logs in only if the saved session has expired -
      every Escola login sends a security e-mail to the parents.
  python3 sources/escola/escola.py fetch [--months N | --all-months] [--all-types] [--no-documents]
      Per child: exams of the future and the current month (or the last N months)
      into material/escola/<child>/exams.json, attached documents into
      material/escola/<child>/documents/.
  python3 sources/escola/escola.py discover [--headed] [--minutes 5]
      Troubleshooting only, if Escola changes: logs in with a browser, opens the
      homework page and records the requests (calls.json, JSON responses,
      screenshots - no passwords). With --headed a visible window opens: choose
      a child, homework, "nur Lernzielkontrollen", a month - everything is recorded.

Requires Python 3.10+ (check/fetch: standard library only); discover also needs
Playwright (pip install playwright; a system Chromium is enough, see CHROMIUM).
"""
import argparse, datetime as dt, html, http.cookiejar, json, mimetypes, os, re, sys, time, urllib.error, urllib.parse, urllib.request, uuid
from http.cookiejar import MozillaCookieJar

# my-family folder: --campus <dir>, else the current folder if it has campus.json, else my-family/ of Family Campus
APP = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if "--campus" in sys.argv[:-1]:   # read before argparse, so that the paths below know it
    i = sys.argv.index("--campus"); ROOT = os.path.abspath(sys.argv[i + 1]); del sys.argv[i:i + 2]
else:
    ROOT = os.getcwd() if os.path.exists("campus.json") else os.path.join(APP, "my-family")
if not os.path.exists(os.path.join(ROOT, "campus.json")):
    sys.exit(f"No my-family in {ROOT} (campus.json missing) - create it with tools/new-campus.sh or pass --campus <dir>")
OUT = os.path.join(ROOT, "material", "escola")   # downloads of this module (never committed)
CHROMIUM = os.environ.get("CHROMIUM", "/usr/bin/chromium")

# Every Escola login triggers a security e-mail ("Web-Login von einem bislang unbekannten
# Gerät"). Therefore the whole session (all cookies incl. PHPSESSID) is kept and reused;
# a new login only happens when it has expired.
COOKIES = os.path.join(OUT, ".escola-session.txt")
LOGIN_HOURS = os.environ.get("ESCOLA_LOGIN_HOURS", "720")   # "stay logged in" (30 days)

# Escola shows dates with German month names
GERMAN_MONTHS = {m: i + 1 for i, m in enumerate(["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
                                                  "August", "September", "Oktober", "November", "Dezember"])}


def load_env():
    path = os.path.join(APP, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    cfg = {k: os.environ.get(k, "").strip() for k in ("ESCOLA_URL", "ESCOLA_USERNAME", "ESCOLA_PASSWORD", "ESCOLA_CHILDREN")}
    cfg["ESCOLA_URL"] = cfg["ESCOLA_URL"].rstrip("/")
    missing = [k for k in ("ESCOLA_URL", "ESCOLA_USERNAME", "ESCOLA_PASSWORD") if not cfg[k]]
    if missing:
        sys.exit(f"Please fill in Family Campus's .env ({os.path.join(APP, '.env')}, template .env.example): {', '.join(missing)}")
    cfg["children"] = [k.strip() for k in cfg["ESCOLA_CHILDREN"].split(",") if k.strip()]
    return cfg


def multipart(fields):
    b = "----campus" + uuid.uuid4().hex
    body = b"".join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items())
    return body + f"--{b}--\r\n".encode(), f"multipart/form-data; boundary={b}"


def load_cookies(jar):
    if os.path.exists(COOKIES):
        try:
            jar.load(COOKIES, ignore_discard=True, ignore_expires=False)
        except Exception:
            pass


def save_cookies(jar):
    os.makedirs(OUT, exist_ok=True)
    jar.save(COOKIES, ignore_discard=True, ignore_expires=False)
    os.chmod(COOKIES, 0o600)


def _opener(jar):
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"),
                     ("Accept", "text/html, application/json, */*"), ("Accept-Language", "de-CH,de;q=0.9")]
    return op


def start_page(op, cfg):
    """Start page after login; contains the list of children (guardianMode) if the session is valid."""
    try:
        page = op.open(cfg["ESCOLA_URL"] + "/admin.php?page_request=5").read().decode("utf-8", "replace")
    except urllib.error.HTTPError:
        return None
    return page if "guardianMode" in html.unescape(page) else None


def session(cfg, force=False):
    """Valid Escola session: reuse the saved one, otherwise log in.
    Returns (opener, jar, info, start page); info["reused"] tells whether a login was needed."""
    jar = MozillaCookieJar()
    load_cookies(jar)
    op = _opener(jar)
    if not force and len(jar):
        page = start_page(op, cfg)
        if page:
            save_cookies(jar)
            return op, jar, {"success": True, "reused": True}, page
    op, jar, data = login_http(cfg, jar)
    page = start_page(op, cfg) if data.get("success") else None
    if data.get("success"):
        save_cookies(jar)
    data["reused"] = False
    return op, jar, data, page


def login_http(cfg, jar):
    """Log in like the Escola web page: POST login.php (FormData username/password)."""
    op = _opener(jar)
    op.open(cfg["ESCOLA_URL"] + "/").read()          # get a session cookie first
    body, ctype = multipart({"loginDurationInHours": LOGIN_HOURS, "username": cfg["ESCOLA_USERNAME"], "password": cfg["ESCOLA_PASSWORD"]})
    headers = {"Content-Type": ctype, "Origin": cfg["ESCOLA_URL"], "Referer": cfg["ESCOLA_URL"] + "/"}
    xsrf = next((urllib.parse.unquote(c.value) for c in jar if c.name == "XSRF-TOKEN"), None)
    if xsrf:
        headers["X-XSRF-TOKEN"] = xsrf
    req = urllib.request.Request(cfg["ESCOLA_URL"] + "/login.php", data=body, headers=headers)
    try:
        raw = op.open(req).read()
    except urllib.error.HTTPError as e:
        return op, jar, {"success": False, "errorMessage": f"HTTP {e.code} {e.reason}"}
    try:
        data = json.loads(raw)
    except ValueError:
        data = {"success": False, "errorMessage": "unexpected response (not JSON)"}
    return op, jar, data


def cmd_check(cfg, a):
    _, jar, data, page = session(cfg, force=a.new)
    if data.get("reused"):
        print("✅ Saved Escola session is valid - no new login (no e-mail).")
        return
    safe = {k: v for k, v in data.items() if k not in ("token", "sessionId", "userId")}
    print("Response:", json.dumps(safe, ensure_ascii=False)[:600])
    print("Cookies:", ", ".join(f"{c.name} ({'until ' + dt.date.fromtimestamp(c.expires).isoformat() if c.expires else 'session'})" for c in jar))
    if data.get("success") and page:
        print("✅ Logged in, session saved.")
    else:
        print("❌ Login failed - check username/password (or two-factor authentication is active).")


def cmd_discover(cfg, a):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright is missing: pip install playwright")
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    out = os.path.join(OUT, "discover-" + stamp)
    os.makedirs(os.path.join(out, "json"), exist_ok=True)
    calls = []
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROMIUM if os.path.exists(CHROMIUM) else None, headless=not a.headed)
        # no HAR recording: it would store the login request including the password
        ctx = br.new_context(viewport={"width": 1280, "height": 900}, locale="de-CH")
        jar = MozillaCookieJar(); load_cookies(jar)
        ctx.add_cookies([{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path or "/",
                          "expires": c.expires or -1, "secure": bool(c.secure)} for c in jar])
        page = ctx.new_page()

        def on_response(r):
            u = r.url
            if not u.startswith(cfg["ESCOLA_URL"]) or any(u.endswith(x) for x in (".js", ".css", ".png", ".svg", ".woff2", ".ico")):
                return
            ct = r.headers.get("content-type", "")
            calls.append({"method": r.request.method, "url": u, "status": r.status, "type": ct.split(";")[0],
                          "post": (r.request.post_data or "")[:500] if "password" not in (r.request.post_data or "") else "<login>"})
            if "json" in ct:
                try:
                    name = re.sub(r"[^a-zA-Z0-9]+", "_", urllib.parse.urlsplit(u).path)[-80:] + f"_{len(calls)}.json"
                    open(os.path.join(out, "json", name), "w", encoding="utf-8").write(json.dumps(r.json(), ensure_ascii=False, indent=1))
                except Exception:
                    pass
        page.on("response", on_response)

        page.goto(cfg["ESCOLA_URL"] + "/", wait_until="networkidle")
        res = page.evaluate("""async ([u, p]) => { const f = new FormData(); f.append('username', u); f.append('password', p);
                               const r = await fetch('login.php', {method: 'POST', body: f}); return r.json(); }""",
                            [cfg["ESCOLA_USERNAME"], cfg["ESCOLA_PASSWORD"]])
        print("Login:", "ok" if res.get("success") else res.get("errorMessage", res))
        if not res.get("success"):
            br.close(); sys.exit(1)
        jar = MozillaCookieJar()
        for c in ctx.cookies():
            jar.set_cookie(http.cookiejar.Cookie(0, c["name"], c["value"], None, False, c["domain"], True, c["domain"].startswith("."),
                                                 c["path"], True, c["secure"], int(c["expires"]) if c["expires"] and c["expires"] > 0 else None,
                                                 not (c["expires"] and c["expires"] > 0), None, None, {}))
        save_cookies(jar)
        page.goto(urllib.parse.urljoin(cfg["ESCOLA_URL"] + "/", res.get("redirectUrl") or "/"), wait_until="networkidle")
        page.screenshot(path=os.path.join(out, "01-start.png"), full_page=True)

        # record the navigation: all links and menu items
        links = page.evaluate("""() => [...document.querySelectorAll('a,button,[role=menuitem]')]
             .map(e => ({text: (e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,80), href: e.getAttribute('href')||''}))
             .filter(x => x.text)""")
        json.dump(links, open(os.path.join(out, "links.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

        # try automatically: open the homework page (labels as shown by Escola)
        for label in ("Hausaufgaben", "Aufgaben"):
            loc = page.get_by_text(label, exact=False)
            if loc.count():
                try:
                    loc.first.click(); page.wait_for_load_state("networkidle"); time.sleep(2)
                    page.screenshot(path=os.path.join(out, "02-homework.png"), full_page=True)
                    open(os.path.join(out, "02-homework.html"), "w", encoding="utf-8").write(page.content())
                    break
                except Exception as e:
                    print("Click on", label, "failed:", e)
        if a.headed:
            print(f"Browser is open: choose a child → Hausaufgaben → «nur Lernzielkontrollen» → month/future. "
                  f"Recording for {a.minutes} minutes (or close the window).")
            end = time.time() + a.minutes * 60
            while time.time() < end and not page.is_closed():
                time.sleep(1)
        if not page.is_closed():
            page.screenshot(path=os.path.join(out, "03-end.png"), full_page=True)
            open(os.path.join(out, "03-end.html"), "w", encoding="utf-8").write(page.content())
        ctx.close(); br.close()
    json.dump(calls, open(os.path.join(out, "calls.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    api = [c for c in calls if "/api/" in c["url"] or c["type"] == "application/json"]
    print(f"Recorded {len(calls)} requests, {len(api)} of them API/JSON → {out}")
    for c in api[:40]:
        print(f"  {c['status']} {c['method']:5} {c['url'][len(cfg['ESCOLA_URL']):][:110]}")


def _post(op, cfg, path, data):
    req = urllib.request.Request(cfg["ESCOLA_URL"] + "/" + path, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                          "X-Requested-With": "XMLHttpRequest", "Origin": cfg["ESCOLA_URL"],
                                          "Referer": cfg["ESCOLA_URL"] + "/admin.php"})
    return op.open(req).read().decode("utf-8", "replace")


def _text(fragment):
    """HTML → readable text with line breaks."""
    t = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</tr>", "\n", fragment, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return "\n".join(l.strip() for l in t.splitlines() if l.strip())


def parse_entries(page):
    """Parse the HTML of show_entries.php into entries (one per homework/exam)."""
    out = []
    for sec in re.split(r'<tr class="head_2">', page)[1:]:
        m = re.search(r'homework-dates[^>]*>([^<]+)<', sec)
        date = None
        if m:
            d = re.search(r"(\d{1,2})\.\s+(\w+)\s+(\d{4})", m.group(1))
            if d and d.group(2) in GERMAN_MONTHS:
                date = f"{d.group(3)}-{GERMAN_MONTHS[d.group(2)]:02d}-{int(d.group(1)):02d}"
        for e in re.split(r'(?=<tr\b[^>]*\bid="homework_tr_)', sec)[1:]:
            eid = re.search(r'homework_tr_(\d+)', e).group(1)
            tip = html.unescape((re.search(r'title="([^"]*)"', e) or [None, ""])[1])
            kind = (re.search(r"<strong>([^<]+)</strong>", tip) or [None, ""])[1].strip()     # e.g. "Lernzielkontrolle"
            subject = html.unescape((re.search(r"<strong>([^<]+)</strong>", e) or [None, ""])[1]).strip()
            title = _text((re.search(r"<h3[^>]*>(.*?)</h3>", e, re.S) or [None, ""])[1])
            school_class = _text((re.search(r'grid-column:2 / 3;">(.*?)</div>', e, re.S) or [None, ""])[1])
            body = e.split("</h3>", 1)[-1]
            body = body.split('<div style="padding-top: 24px">', 1)[0]
            docs = [{"url": html.unescape(u), "name": _text(n)} for u, n in re.findall(r'<a\s[^>]*?href="(/download\.php[^"]+)"[^>]*>(.*?)</a>', body, re.S)]
            links = [{"url": html.unescape(u), "text": _text(n)} for u, n in re.findall(r'<a\s[^>]*?href="(https?://[^"]+)"[^>]*>(.*?)</a>', body, re.S)]
            goals = _text(re.split(r"<strong>Dokumente:</strong>", body)[0].split("</div></div></div></div>", 1)[-1])
            out.append({"id": eid, "date": date, "subject": subject, "type": kind, "title": title, "class": school_class,
                        "goals": goals, "links": links, "documents": docs})
    return out


def _download(op, cfg, doc, folder, prefix):
    os.makedirs(folder, exist_ok=True)
    with op.open(cfg["ESCOLA_URL"] + doc["url"]) as r:
        cd = r.headers.get("Content-Disposition", "")
        m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="?([^";]+)"?', cd)
        name = urllib.parse.unquote(m.group(1)) if m else doc["name"]
        if "." not in name:
            name += mimetypes.guess_extension((r.headers.get("Content-Type") or "").split(";")[0]) or ""
        name = re.sub(r'[\\/:*?"<>|]+', "_", f"{prefix}_{name}").strip()
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            open(path, "wb").write(r.read())
        return os.path.relpath(path, ROOT)


def cmd_fetch(cfg, a):
    op, jar, res, start = session(cfg)
    if not res.get("success") or not start:
        sys.exit("Login failed: " + str(res.get("errorMessage")))
    print("Escola:", "saved session reused (no login, no e-mail)" if res.get("reused") else "logged in")
    children = {n: (int(i), html.unescape(c)) for i, n, c in
                re.findall(r'"id":(\d+),"displayName":"([^"]+)","portrait":"[^"]*","classLabel":"([^"]*)"', html.unescape(start))}
    if not children:
        sys.exit("No children found - has the Escola page changed? Run «discover».")
    wanted = cfg["children"] or list(children)
    result = {}
    for name in wanted:
        if name not in children:
            print(f"⚠️  {name} not found (available: {', '.join(children)})"); continue
        kid, school_class = children[name]
        op.open(f"{cfg['ESCOLA_URL']}/inc/ajax/eltern/loadEducatorGui.php?kid={kid}").read()
        app = _post(op, cfg, "inc/ajax/homework/application.php", {"contentWidth": 800, "administrationView": 0, "preselectedStudentId": kid, "fromPublicPage": 0})
        class_id = re.search(r"classId:\s*(\d+)", app).group(1)
        sel = re.search(r'<select[^>]*id="homeworkDate".*?</select>', app, re.S)
        months = [(v, html.unescape(t).strip()) for v, t in re.findall(r'<option value="(\d+)"[^>]*>([^<]+)</option>', sel.group(0) if sel else "") if v != "0"]
        dates = [("0", "future entries")] + (months if a.all_months else months[:a.months])
        entries = {}
        for val, label in dates:
            page = _post(op, cfg, "inc/ajax/homework/show_entries.php", {"classId": class_id, "preselectedStudentId": kid, "sne": 0, "date": val})
            for e in parse_entries(page):
                entries[e["id"]] = e
        selected = [e for e in entries.values() if a.all_types or e["type"].lower().startswith("lernziel")]
        folder = os.path.join(OUT, name.lower())
        os.makedirs(folder, exist_ok=True)
        for e in selected:
            prefix = f"{e['date'] or 'no-date'}_{re.sub(r'[^A-Za-zÄÖÜäöü0-9]+', '-', e['subject'])[:30]}"
            for d in e["documents"]:
                if not a.no_documents:
                    try:
                        d["file"] = _download(op, cfg, d, os.path.join(folder, "documents"), prefix)
                    except Exception as ex:
                        d["error"] = str(ex)
            e["child"] = name
        selected.sort(key=lambda e: (e["date"] or "", e["subject"]))
        # merge with earlier runs (Escola hides old entries after a while)
        path = os.path.join(folder, "exams.json")
        old = {e["id"]: e for e in json.load(open(path, encoding="utf-8"))} if os.path.exists(path) else {}
        old.update({e["id"]: e for e in selected})
        merged = sorted(old.values(), key=lambda e: (e["date"] or "", e["subject"]))
        json.dump(merged, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n{name} ({school_class}): {len(selected)} entries from {', '.join(l for _, l in dates)} → {os.path.relpath(path, ROOT)}")
        for e in selected:
            extra = (f" · {len(e['documents'])} doc(s)" if e["documents"] else "") + (f" · {len(e['links'])} link(s)" if e["links"] else "")
            print(f"  {e['date']}  {e['subject'][:28]:28}  {e['title'][:60]}{extra}")
        result[name] = merged
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check the session (logs in only if needed)")
    c.add_argument("--new", action="store_true", help="force a new login (sends an Escola e-mail)")
    d = sub.add_parser("discover", help="troubleshooting: record Escola requests")
    d.add_argument("--headed", action="store_true"); d.add_argument("--minutes", type=float, default=5)
    f = sub.add_parser("fetch", help="fetch exams and documents")
    f.add_argument("--months", type=int, default=1, help="also the last N months (default 1 = current month)")
    f.add_argument("--all-months", action="store_true", help="all months Escola still offers")
    f.add_argument("--all-types", action="store_true", help="also homework/tasks, not only exams")
    f.add_argument("--no-documents", action="store_true", help="do not download documents")
    a = ap.parse_args()
    cfg = load_env()
    {"check": cmd_check, "discover": cmd_discover, "fetch": cmd_fetch}[a.cmd](cfg, a)


if __name__ == "__main__":
    main()
