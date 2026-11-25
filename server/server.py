#!/usr/bin/env python3
"""Family Campus server: serves the static site, handles login per person and
stores learning progress (answers, attempts, repetition box) in SQLite.

Standard library only. The data directory (SQLite database + campus.env with the
logins) is the Docker volume, so updates of the image keep all data.

  python3 server.py [--www DIR] [--data DIR] [--port 8080]
Logins come from <data>/campus.env (CAMPUS_USERS, CAMPUS_PASSWORD_<NAME>, see
data/campus.env.example); in Docker <data> is the volume /data. Environment variables
with the same names take precedence.
"""
import argparse, datetime as dt, hashlib, hmac, json, mimetypes, os, re, secrets, sqlite3, sys, threading, time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs, quote

# Family Campus's VERSION next to this script (container) or in the repository root:
# line 1 = version, line 2 = release date (YYYY-MM-DD). The built site's build.json adds the date of
# my-family's content (ADR-0018); /api/version returns both.
_here = os.path.dirname(os.path.abspath(__file__))
_vf = [p for p in (os.path.join(_here, "VERSION"), os.path.join(_here, "..", "VERSION")) if os.path.isfile(p)]
_vl = open(_vf[0]).read().split() if _vf else []
VERSION = _vl[0] if _vl else "dev"
RELEASE_DATE = _vl[1] if len(_vl) > 1 else ""

# URL path the site is served under (e.g. "/campus" behind a reverse proxy); "" = the root
PREFIX = "/" + os.environ.get("FC_PREFIX", "").strip("/") if os.environ.get("FC_PREFIX", "").strip("/") else ""
SESSION_DAYS = 120
BOX_DAYS = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}   # repetition box (Lernkartei): days until due after a right answer in box n
# reasons a learner can pick when reporting a question (ADR-0019); the texts are in the locales (report.<reason>)
REPORT_REASONS = ("wrongSolution", "rightAnswer", "unclear", "typo", "other")
# Reachable without login. The web app manifest and its icons must be public: Chrome loads them
# without cookies when it checks whether the site can be installed as an app.
PUBLIC = {"/login.html", "/login.css", "/favicon.svg", "/version.js", "/people.js", "/manifest.webmanifest",
          "/i18n.js", "/config.json",   # languages (ADR-0012): the login page needs them before anybody is logged in
          "/icons/icon-192.png", "/icons/icon-512.png", "/icons/icon-maskable-512.png", "/icons/apple-touch-icon.png"}
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
}

# ---------------------------------------------------------------- passwords
def hash_pw(pw: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt$16384$8$1${salt.hex()}${h.hex()}"

def check_pw(pw: str, stored: str) -> bool:
    try:
        _, n, r, p, salt, h = stored.split("$")
        calc = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=len(h) // 2)
        return hmac.compare_digest(calc.hex(), h)
    except Exception:
        return False

# ---------------------------------------------------------------- database
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL COLLATE NOCASE, pw_hash TEXT NOT NULL,
  admin INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), created TEXT NOT NULL, expires TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, exercise TEXT NOT NULL, set_id TEXT NOT NULL,
  mode TEXT NOT NULL, total INTEGER NOT NULL, correct INTEGER NOT NULL, ts TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS answers (
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, exercise TEXT NOT NULL, set_id TEXT NOT NULL,
  qkey TEXT NOT NULL, question TEXT NOT NULL, correct INTEGER NOT NULL, mode TEXT NOT NULL, ts TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS review (
  user_id INTEGER NOT NULL, exercise TEXT NOT NULL, set_id TEXT NOT NULL, qkey TEXT NOT NULL,
  qjson TEXT NOT NULL, box INTEGER NOT NULL, due TEXT NOT NULL, wrong INTEGER NOT NULL DEFAULT 0, updated TEXT NOT NULL,
  PRIMARY KEY (user_id, exercise, qkey));
CREATE INDEX IF NOT EXISTS answers_user ON answers(user_id, ts);
CREATE INDEX IF NOT EXISTS attempts_user ON attempts(user_id, exercise, set_id);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, exercise TEXT NOT NULL, set_id TEXT NOT NULL, qkey TEXT NOT NULL,
  reason TEXT NOT NULL, note TEXT NOT NULL, question TEXT NOT NULL, qjson TEXT NOT NULL, given TEXT NOT NULL,
  ok INTEGER, mode TEXT NOT NULL, build TEXT NOT NULL, ts TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS feedback_build ON feedback(build, exercise);
CREATE INDEX IF NOT EXISTS feedback_ex ON feedback(exercise);
CREATE TABLE IF NOT EXISTS mastered (
  user_id INTEGER NOT NULL, exercise TEXT NOT NULL, qkey TEXT NOT NULL, ts TEXT NOT NULL,
  PRIMARY KEY (user_id, exercise, qkey));
"""

class DB:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)
        # migrations for databases created by earlier versions
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(users)")}
        if "locale" not in cols:   # language chosen by the person (ADR-0012); NULL = not chosen yet
            self.conn.execute("ALTER TABLE users ADD COLUMN locale TEXT")
        if "birth_year" in cols:   # never used; removed in 1.0.0
            self.conn.execute("ALTER TABLE users DROP COLUMN birth_year")

    def q(self, sql, args=()):
        with self.lock:
            return self.conn.execute(sql, args).fetchall()

    def x(self, sql, args=()):
        with self.lock:
            cur = self.conn.execute(sql, args)
            return cur.lastrowid

def now(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
def today(): return dt.date.today()

# ---------------------------------------------------------------- HTTP
def load_env_file(path):
    """Minimal KEY=VALUE reader (# comments). Does not override existing environment variables."""
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def env_users(db):
    """CAMPUS_USERS=Name[:admin],…  and  CAMPUS_PASSWORD_<NAME>=…
    (older entries Name:BirthYear[:admin] still work; the year is ignored)
    Creates missing users, updates admin and replaces the password hash
    when the password in the environment changed. Plain passwords are never stored."""
    spec = os.environ.get("CAMPUS_USERS", "").strip()
    for item in filter(None, (x.strip() for x in spec.split(","))):
        parts = item.split(":")
        name = parts[0].strip()
        admin = int(any(p.strip().lower() == "admin" for p in parts[1:]))
        pw = os.environ.get("CAMPUS_PASSWORD_" + name.upper(), "")
        row = db.q("SELECT id, pw_hash FROM users WHERE name=?", (name,))
        if not row:
            if not pw:
                print(f"note: no password set for {name} - user not created", flush=True)
                continue
            db.x("INSERT INTO users(name,pw_hash,admin,created) VALUES(?,?,?,?)", (name, hash_pw(pw), admin, now()))
            print(f"user created: {name}", flush=True)
        else:
            db.x("UPDATE users SET admin=? WHERE id=?", (admin, row[0]["id"]))
            if pw and not check_pw(pw, row[0]["pw_hash"]):
                db.x("UPDATE users SET pw_hash=? WHERE id=?", (hash_pw(pw), row[0]["id"]))
                db.x("DELETE FROM sessions WHERE user_id=?", (row[0]["id"],))
                print(f"password changed: {name} (existing sessions ended)", flush=True)

class App:
    def __init__(self, www, data):
        self.www = os.path.realpath(www)
        bj = os.path.join(self.www, "build.json")
        self.build = json.load(open(bj, encoding="utf-8")) if os.path.exists(bj) else {}
        self.build = {"version": VERSION, "date": RELEASE_DATE, "content": "", "dev": False, **self.build}
        # the running release, stored with every report (ADR-0019)
        self.stamp = "{}-{}{}{}".format(self.build.get("version") or VERSION, self.build.get("content") or "",
                                        "@" + self.build["commit"] if self.build.get("commit") else "", "+dev" if self.build.get("dev") else "")
        # reports handled on the development machine ("id@ts", from my-family's feedback.json): their flags end (ADR-0019)
        self.resolved = set(self.build.get("resolved") or [])
        os.makedirs(data, exist_ok=True)
        self.db = DB(os.path.join(data, "campus.sqlite"))
        # campus logins: <data>/campus.env (in the Docker volume); environment variables take precedence
        cred = os.path.join(data, "campus.env")
        if os.path.exists(cred):
            load_env_file(cred)
        elif not os.environ.get("CAMPUS_USERS"):
            print(f"note: {cred} is missing - nobody new can log in (see data/campus.env.example)", flush=True)
        env_users(self.db)
        self.fails = {}   # ip -> [count, until]

    def is_resolved(self, r):
        return f"{r['id']}@{r['ts']}" in self.resolved

    def locales(self):
        """Locales my-family offers (config.json, written by the build); English if there is none."""
        try:
            with open(os.path.join(self.www, "config.json"), encoding="utf-8") as f:
                return list(json.load(f).get("locales") or ["en"])
        except (OSError, ValueError):
            return ["en"]

class Handler(BaseHTTPRequestHandler):
    server_version = "campus"
    sys_version = ""
    app: App = None

    # ---- helpers
    def log_message(self, fmt, *args):
        if "/healthz" not in (args[0] if args else ""):
            sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))

    def path_parts(self):
        u = urlsplit(self.path)
        p = u.path
        if p == PREFIX: p = PREFIX + "/"
        if p.startswith(PREFIX + "/"): p = p[len(PREFIX):]
        return p, parse_qs(u.query), u.path.startswith(PREFIX)

    def base(self):
        return PREFIX if urlsplit(self.path).path.startswith(PREFIX) else ""

    def send(self, code, body=b"", ctype="text/plain; charset=utf-8", headers=None):
        self.send_response(code)
        for k, v in SECURITY_HEADERS.items(): self.send_header(k, v)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(body)

    def json(self, obj, code=200, headers=None):
        self.send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8", headers)

    def body(self):
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            raise ValueError("json required")
        n = int(self.headers.get("Content-Length") or 0)
        if n > 2_000_000: raise ValueError("too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def user(self):
        c = self.headers.get("Cookie") or ""
        tok = None
        for part in c.split(";"):
            k, _, v = part.strip().partition("=")
            if k == "campus_session": tok = v
        if not tok: return None
        r = self.app.db.q("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires>?", (tok, now()))
        return r[0] if r else None

    def secure(self):
        return (self.headers.get("X-Forwarded-Proto") or "").lower() == "https"

    # ---- routing
    def do_HEAD(self): self.do_GET()

    def do_GET(self):
        path, qs, _ = self.path_parts()
        if path == "/healthz": return self.send(200, b"ok\n")
        u = urlsplit(self.path)
        if u.path == PREFIX:   # "/campus" without slash: relative URLs of the page would resolve to "/"
            return self.send(301, b"", headers={"Location": PREFIX + "/" + ("?" + u.query if u.query else "")})
        if path == "/api/version": return self.json({k: self.app.build.get(k) for k in ("version", "date", "content", "dev")})
        if path.startswith("/api/"): return self.api_get(path, qs)
        if path in PUBLIC or re.fullmatch(r"/locales/[A-Za-z-]+\.json", path): return self.static(path)
        user = self.user()
        if not user:
            nxt = quote(urlsplit(self.path).path)
            return self.send(302, b"", headers={"Location": f"{self.base()}/login.html?next={nxt}"})
        return self.static(path, user)

    def do_POST(self):
        path, qs, _ = self.path_parts()
        try:
            data = self.body()
        except Exception:
            return self.json({"error": "bad request"}, 400)
        if path == "/api/login": return self.login(data)
        u = self.user()
        if not u: return self.json({"error": "login required"}, 401)
        if path == "/api/logout":
            tok = [p.strip().partition("=")[2] for p in (self.headers.get("Cookie") or "").split(";") if p.strip().startswith("campus_session=")]
            if tok: self.app.db.x("DELETE FROM sessions WHERE token=?", (tok[0],))
            return self.json({"ok": True}, headers={"Set-Cookie": f"campus_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"})
        if path == "/api/me/locale":   # the person's language, one of the locales my-family offers
            loc = str(data.get("locale") or "")
            if loc not in self.app.locales(): return self.json({"error": "bad_locale"}, 400)
            self.app.db.x("UPDATE users SET locale=? WHERE id=?", (loc, u["id"]))
            return self.json({"ok": True, "locale": loc})
        if path == "/api/answer": return self.answer(u, data)
        if path == "/api/result": return self.result(u, data)
        if path == "/api/report": return self.report(u, data)
        return self.json({"error": "not found"}, 404)

    # ---- static files
    def static(self, path, user=None):
        if path.endswith("/"): path += "index.html"
        full = os.path.realpath(os.path.join(self.app.www, path.lstrip("/")))
        if not (full == self.app.www or full.startswith(self.app.www + os.sep)):
            return self.send(404, b"not found\n")
        if os.path.isdir(full):
            return self.send(301, b"", headers={"Location": urlsplit(self.path).path + "/"})
        if not os.path.isfile(full):
            return self.send(404, b"not found\n")
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/json", "application/javascript", "image/svg+xml"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as f: data = f.read()
        if full == os.path.join(self.app.www, "exercises.json") and user and not user["admin"]:
            data = self.own_exams_only(data, user["name"])
        self.send(200, data, ctype)

    @staticmethod
    def own_exams_only(raw, name):
        """Learners get only their own exams (dates, topics, learning goals); parents get all."""
        cat = json.loads(raw)
        cat["exams"] = [x for x in cat.get("exams", []) if name in x.get("people", [])]
        return json.dumps(cat, ensure_ascii=False).encode("utf-8")

    # ---- API
    def login(self, data):
        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        cnt, until = self.app.fails.get(ip, [0, 0])
        if until > time.time():
            return self.json({"error": "too_many_attempts"}, 429)
        name, pw = str(data.get("name", "")).strip(), str(data.get("password", ""))
        r = self.app.db.q("SELECT * FROM users WHERE name=?", (name,))
        if not r or not check_pw(pw, r[0]["pw_hash"]):
            cnt += 1
            self.app.fails[ip] = [cnt, time.time() + 60 if cnt >= 5 else 0]
            time.sleep(0.8)
            return self.json({"error": "bad_login"}, 401)
        self.app.fails.pop(ip, None)
        # a language chosen on the login page becomes the person's choice if they have none yet
        loc = str(data.get("locale") or "")
        if not r[0]["locale"] and loc in self.app.locales():
            self.app.db.x("UPDATE users SET locale=? WHERE id=?", (loc, r[0]["id"]))
        tok = secrets.token_urlsafe(32)
        exp = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=SESSION_DAYS)).isoformat(timespec="seconds")
        self.app.db.x("INSERT INTO sessions(token,user_id,created,expires) VALUES(?,?,?,?)", (tok, r[0]["id"], now(), exp))
        cookie = f"campus_session={tok}; Path=/; Max-Age={SESSION_DAYS*86400}; HttpOnly; SameSite=Lax" + ("; Secure" if self.secure() else "")
        return self.json({"ok": True, "name": r[0]["name"]}, headers={"Set-Cookie": cookie})

    def target_user(self, u, qs):
        """Admins may look at other people's progress (?user=Name)."""
        name = (qs.get("user") or [None])[0]
        if name and name.lower() != u["name"].lower():
            if not u["admin"]: return None
            r = self.app.db.q("SELECT * FROM users WHERE name=?", (name,))
            return r[0] if r else None
        return u

    def api_get(self, path, qs):
        u = self.user()
        if not u: return self.json({"error": "login required"}, 401)
        db = self.app.db
        if path == "/api/me":
            users = [r["name"] for r in db.q("SELECT name FROM users ORDER BY id")] if u["admin"] else [u["name"]]
            return self.json({"name": u["name"], "admin": bool(u["admin"]), "users": users,
                              "locale": u["locale"]})
        t = self.target_user(u, qs)
        if not t: return self.json({"error": "forbidden"}, 403)
        if path == "/api/progress":
            ex = (qs.get("ex") or [""])[0]
            return self.json({"sets": self.sets_progress(t["id"], ex), "due": self.due(t["id"], ex), "flags": self.flags(ex)})
        if path == "/api/reports":   # parents only: every report with its note; active = not resolved (ADR-0019)
            if not u["admin"]: return self.json({"error": "forbidden"}, 403)
            rows = db.q("""SELECT f.id, u.name user, f.exercise, f.set_id, f.reason, f.note, f.question, f.given, f.ok, f.mode,
                                  f.build, f.ts FROM feedback f JOIN users u ON u.id=f.user_id ORDER BY f.ts DESC LIMIT 300""")
            return self.json({"build": self.app.stamp,
                              "reports": [dict(r, active=not self.app.is_resolved(r)) for r in rows]})
        if path == "/api/summary":
            rows = db.q("""SELECT exercise, set_id, COUNT(*) runs, MAX(100*correct/MAX(total,1)) best, MAX(ts) last
                           FROM attempts WHERE user_id=? AND mode!='repeat' GROUP BY exercise, set_id""", (t["id"],))
            ex = {}
            for r in rows:
                ex.setdefault(r["exercise"], {})[r["set_id"]] = {"runs": r["runs"], "best": r["best"], "last": r["last"]}
            due = {r["exercise"]: r["n"] for r in db.q("SELECT exercise, COUNT(*) n FROM review WHERE user_id=? AND due<=? GROUP BY exercise", (t["id"], today().isoformat()))}
            box = {r["exercise"]: r["n"] for r in db.q("SELECT exercise, COUNT(*) n FROM review WHERE user_id=? GROUP BY exercise", (t["id"],))}
            tot = db.q("SELECT COUNT(*) n, COALESCE(SUM(correct),0) ok FROM answers WHERE user_id=?", (t["id"],))[0]
            mastered = db.q("SELECT COUNT(*) n FROM mastered WHERE user_id=?", (t["id"],))[0]["n"]
            return self.json({"user": t["name"], "exercises": ex, "due": due, "inBox": box,
                              "answers": tot["n"], "correct": tot["ok"], "mastered": mastered})
        if path == "/api/repeat":
            ex = (qs.get("ex") or [""])[0]
            rows = db.q("SELECT qkey, set_id, qjson, box FROM review WHERE user_id=? AND exercise=? AND due<=? ORDER BY box, due LIMIT 15",
                        (t["id"], ex, today().isoformat()))
            return self.json([{"key": r["qkey"], "set": r["set_id"], "box": r["box"], "q": json.loads(r["qjson"])} for r in rows])
        if path == "/api/history":
            att = db.q("""SELECT exercise, set_id, mode, total, correct, ts FROM attempts WHERE user_id=? ORDER BY ts DESC LIMIT 200""", (t["id"],))
            wrong = db.q("""SELECT exercise, set_id, question, ts FROM answers WHERE user_id=? AND correct=0 ORDER BY ts DESC LIMIT 60""", (t["id"],))
            # timestamps are UTC; the browser sends its offset (JavaScript getTimezoneOffset, minutes) so days are local days
            try: offset = max(-840, min(840, int((qs.get("tz") or ["0"])[0])))
            except ValueError: offset = 0
            shift = f"{-offset:+d} minutes"
            days = db.q("""SELECT substr(datetime(ts, ?),1,10) d, COUNT(*) n, SUM(correct) ok FROM answers WHERE user_id=?
                           GROUP BY d ORDER BY d DESC LIMIT 30""", (shift, t["id"]))
            today_rows = db.q("""SELECT exercise, set_id, correct, mode, ts FROM answers WHERE user_id=? AND ts >= ?
                                 AND substr(datetime(ts, ?),1,10) = substr(datetime('now', ?),1,10) ORDER BY ts""",
                              (t["id"], (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).isoformat(timespec="seconds"), shift, shift))
            return self.json({"user": t["name"], "attempts": [dict(r) for r in att], "wrong": [dict(r) for r in wrong],
                              "days": [dict(r) for r in days], "today": [dict(r) for r in today_rows]})
        return self.json({"error": "not found"}, 404)

    def sets_progress(self, uid, ex):
        # full: best result of a whole run (no retry round of the mistakes) – it opens harder sets (ADR-0020)
        rows = self.app.db.q("""SELECT set_id, COUNT(*) runs, MAX(100*correct/MAX(total,1)) best, MAX(ts) last,
                                       MAX(CASE WHEN mode='normal' THEN 100*correct/MAX(total,1) END) best_full
                                FROM attempts WHERE user_id=? AND exercise=? AND mode!='repeat' GROUP BY set_id""", (uid, ex))
        return {r["set_id"]: {"runs": r["runs"], "best": r["best"], "full": r["best_full"] or 0, "last": r["last"]} for r in rows}

    def due(self, uid, ex):
        return self.app.db.q("SELECT COUNT(*) n FROM review WHERE user_id=? AND exercise=? AND due<=?", (uid, ex, today().isoformat()))[0]["n"]

    def flags(self, ex):
        """Keys of the questions of a tile with an open report – flagged for everybody until a release marks the
        report as handled (ADR-0019)."""
        return sorted({r["qkey"] for r in self.app.db.q("SELECT id, ts, qkey FROM feedback WHERE exercise=?", (ex,))
                       if not self.app.is_resolved(r)})

    def report(self, u, d):
        """A learner reports a question (ADR-0019). The answer to it is not stored, so it counts neither as right
        nor as wrong; the question is flagged for everybody until a release marks the report as handled."""
        try:
            ex, set_id, key = str(d["ex"])[:80], str(d["set"])[:40], str(d["key"])[:64]
            reason = str(d["reason"])
            if reason not in REPORT_REASONS: raise ValueError(reason)
            note = str(d.get("note") or "").strip()[:1000]
            ok = None if d.get("ok") is None else int(bool(d["ok"]))
            mode = d.get("mode") if d.get("mode") in ("normal", "retry", "repeat") else "normal"
            qjson = json.dumps(d.get("q") or {}, ensure_ascii=False)[:200_000]
            text, given = str(d.get("text", ""))[:500], str(d.get("given", ""))[:500]
        except Exception:
            return self.json({"error": "bad request"}, 400)
        self.app.db.x("""INSERT INTO feedback(user_id,exercise,set_id,qkey,reason,note,question,qjson,given,ok,mode,build,ts)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (u["id"], ex, set_id, key, reason, note, text, qjson, given, ok, mode, self.app.stamp, now()))
        return self.json({"ok": True, "flags": self.flags(ex)})

    def answer(self, u, d):
        try:
            ex, set_id, key, ok = str(d["ex"])[:80], str(d["set"])[:40], str(d["key"])[:64], bool(d["ok"])
            mode = d.get("mode") if d.get("mode") in ("normal", "retry", "repeat") else "normal"
            qjson = json.dumps(d.get("q") or {}, ensure_ascii=False)[:200_000]
            text = str(d.get("text", ""))[:500]
        except Exception:
            return self.json({"error": "bad request"}, 400)
        db, t = self.app.db, now()
        db.x("INSERT INTO answers(user_id,exercise,set_id,qkey,question,correct,mode,ts) VALUES(?,?,?,?,?,?,?,?)",
             (u["id"], ex, set_id, key, text, int(ok), mode, t))
        r = db.q("SELECT box, wrong FROM review WHERE user_id=? AND exercise=? AND qkey=?", (u["id"], ex, key))
        if not ok:
            # wrong: (back) into box 1; due tomorrow when repeating, due today after a new mistake in normal practice
            due = today() + dt.timedelta(days=1 if mode == "repeat" else 0)
            db.x("""INSERT INTO review(user_id,exercise,set_id,qkey,qjson,box,due,wrong,updated) VALUES(?,?,?,?,?,1,?,1,?)
                    ON CONFLICT(user_id,exercise,qkey) DO UPDATE SET box=1, due=excluded.due, wrong=wrong+1, qjson=excluded.qjson, updated=excluded.updated""",
                 (u["id"], ex, set_id, key, qjson, due.isoformat(), t))
        elif r:
            box = r[0]["box"]
            if mode == "repeat" or box >= 1:
                if box >= 5:
                    db.x("DELETE FROM review WHERE user_id=? AND exercise=? AND qkey=?", (u["id"], ex, key))
                    db.x("INSERT OR REPLACE INTO mastered(user_id,exercise,qkey,ts) VALUES(?,?,?,?)", (u["id"], ex, key, t))
                else:
                    due = today() + dt.timedelta(days=BOX_DAYS[box])
                    db.x("UPDATE review SET box=?, due=?, updated=? WHERE user_id=? AND exercise=? AND qkey=?",
                         (box + 1, due.isoformat(), t, u["id"], ex, key))
        return self.json({"ok": True, "due": self.due(u["id"], ex)})

    def result(self, u, d):
        try:
            ex, set_id = str(d["ex"])[:80], str(d["set"])[:40]
            total, correct = int(d["total"]), int(d["correct"])
            mode = d.get("mode") if d.get("mode") in ("normal", "retry", "repeat") else "normal"
        except Exception:
            return self.json({"error": "bad request"}, 400)
        if total <= 0 or correct < 0 or correct > total:
            return self.json({"error": "bad request"}, 400)
        self.app.db.x("INSERT INTO attempts(user_id,exercise,set_id,mode,total,correct,ts) VALUES(?,?,?,?,?,?,?)",
                      (u["id"], ex, set_id, mode, total, correct, now()))
        return self.json({"ok": True, "sets": self.sets_progress(u["id"], ex), "due": self.due(u["id"], ex)})

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--www", default=os.environ.get("CAMPUS_WWW", "/srv/www"))
    ap.add_argument("--data", default=os.environ.get("CAMPUS_DATA", "/data"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    ap.add_argument("--env", help="additionally read variables from this file")
    a = ap.parse_args()
    if a.env:
        load_env_file(a.env)
    os.umask(0o077)   # database and files in the volume only readable by my-family user
    Handler.app = App(a.www, a.data)
    mimetypes.add_type("image/svg+xml", ".svg"); mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("application/manifest+json", ".webmanifest")
    srv = ThreadingHTTPServer(("0.0.0.0", a.port), Handler)
    srv.daemon_threads = True
    print(f"Family Campus {VERSION} on :{a.port} (www={a.www}, data={a.data})", flush=True)
    srv.serve_forever()

if __name__ == "__main__":
    main()
