/* Family Campus – page footer with the version of Family Campus and the date of my-family's content
   (from /api/version, ADR-0018): "Family Campus 1.0.0 · Inhalte vom 22. November 2026".
   After login it opens "What's new?" (release-notes.json, built by tools/build.py): the new and improved
   tiles of the last weeks, then the notes of Family Campus (per locale with fallback; texts from i18n.js).
   A ✨ marks a state this browser has not opened yet. On the login page the footer is plain text.
   A page can show it in its header too: an element with id "app-version" gets a small button;
   window.CampusNews.open() opens "What's new?". */
(function () {
  const base = location.pathname.replace(/\/exercises\/[^/]+\/.*$/, "/").replace(/[^/]*$/, "");
  const loginPage = /\/login\.html$/.test(location.pathname);
  const SEEN = "campus-seen-version";
  const longDate = iso => iso ? I18n.date(iso) : "";
  const t = (k, p) => I18n.t(k, p);
  const store = { get() { try { return localStorage.getItem(SEEN); } catch (e) { return null; } },
                  set(v) { try { localStorage.setItem(SEEN, v); } catch (e) {} } };

  I18n.ready.then(() => fetch(base + "api/version")).then(r => r.json()).then(v => {
    const label = `Family Campus ${v.version}`
      + (v.content ? ` · ${t("footer.content", { date: longDate(v.content) })}` : v.date ? ` · ${longDate(v.date)}` : "")
      + (v.dev ? ` · ${t("footer.test")}` : "");
    const state = `${v.version}|${v.content || ""}`;
    const f = document.createElement("footer");
    f.className = "campus-version";
    f.style.cssText = "text-align:center;font-size:.8rem;color:var(--muted,#6c6886);padding:24px 16px 32px";
    document.body.append(f);
    if (loginPage) { f.textContent = label; return; }

    const unseen = store.get() !== state;
    const dots = [];
    const openNews = () => { store.set(state); dots.forEach(d => d.remove()); open(v); };
    function newsButton(text, css) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.title = t("news.title");
      btn.style.cssText = "font:inherit;color:inherit;background:none;border:0;cursor:pointer;text-decoration:underline dotted;text-underline-offset:3px;" + css;
      btn.textContent = text;
      const dot = document.createElement("span");
      dot.setAttribute("aria-label", t("news.new"));
      dot.textContent = "✨";   // unseen release notes; an icon says "new" better than a coloured dot
      dot.style.cssText = "margin-inline-start:5px;text-decoration:none;display:inline-block";
      if (unseen) { btn.append(dot); dots.push(dot); btn.title = t("news.show"); }
      btn.addEventListener("click", openNews);
      return btn;
    }
    f.append(newsButton(label, "padding:8px 10px"));
    const head = document.getElementById("app-version");
    if (head) {
      const day = v.content || v.date;
      const short = day ? I18n.date(day, { day: "numeric", month: "short", year: "numeric" }) : "";
      head.append(newsButton(t("version", { version: v.version }) + (short ? ` · ${short}` : ""), "padding:0;text-align:start"));
    }
    window.CampusNews = { open: openNews };
  }).catch(() => {});

  let dialog;
  function open(v) {
    if (!dialog) {
      dialog = document.createElement("dialog");
      dialog.setAttribute("aria-labelledby", "campus-news-title");
      dialog.style.cssText = "border:0;border-radius:18px;padding:0;max-width:min(520px,calc(100vw - 32px));width:100%;background:var(--card,#fff);color:var(--ink,#26233a);box-shadow:0 10px 40px rgba(0,0,0,.25)";
      const style = document.createElement("style");
      style.textContent = "dialog.campus-news::backdrop{background:rgba(20,16,40,.45)} dialog.campus-news h3{margin:16px 0 4px;font-size:1rem} dialog.campus-news ul{margin:0;padding-inline-start:1.2rem} dialog.campus-news li{margin:4px 0}" +
        // links in the theme's colour, the same before and after a visit (the browser's blue and purple are hard to read in dark mode)
        " dialog.campus-news a,dialog.campus-news a:visited{color:var(--chip-ink,#3d2fa0);font-weight:600;text-decoration:underline;text-underline-offset:3px} dialog.campus-news a:hover{color:var(--accent,#6b4eff)}";
      document.head.append(style);
      dialog.className = "campus-news";
      dialog.addEventListener("click", e => { if (e.target === dialog) dialog.close(); });   // tap beside the box
      document.body.append(dialog);
    }
    dialog.innerHTML = `<div style="padding:18px 20px 20px;max-height:80vh;overflow:auto">
      <div style="display:flex;align-items:center;gap:8px"><h2 id="campus-news-title" style="margin:0;font-size:1.25rem;flex:1">✨ ${t("news.title")}</h2>
      <button type="button" aria-label="${t("close")}" style="font:inherit;font-size:1.2rem;background:none;border:0;color:inherit;cursor:pointer;padding:4px 8px">✕</button></div>
      <div class="body"><p style="color:var(--muted,#6c6886)">${t("loading")}</p></div></div>`;
    dialog.querySelector("button").addEventListener("click", () => dialog.close());
    dialog.showModal();
    fetch(base + "release-notes.json").then(r => r.json()).then(rn => {
      const body = dialog.querySelector(".body");
      body.replaceChildren();
      const section = (title, items) => {
        if (!items.length) return;
        const h = document.createElement("h3"); h.textContent = title;
        const ul = document.createElement("ul");
        items.forEach(n => { const li = document.createElement("li"); li.append(n); ul.append(li); });
        body.append(h, ul);
      };
      // texts per locale ({"de-CH": …, "en": …}) with the fallback chain; plain values are taken as they are
      const pick = x => (x && typeof x === "object" && !Array.isArray(x)) ? I18n.chain(I18n.locale).map(k => x[k]).find(v => v != null) : x;
      const shortDate = d => I18n.date(d, { day: "numeric", month: "short" });
      // my-family: new and improved tiles of the last weeks (from tiles.json "date", "updated", "note")
      section(t("news.content"), (rn.content || []).map(n => {
        const frag = document.createDocumentFragment();
        const a = document.createElement("a"); a.href = base + n.path; a.textContent = pick(n.title) || n.id;
        const note = pick(n.note);
        frag.append(`${shortDate(n.date)} · ${(n.kind === "updated" ? t("news.updated") : t("news.added"))}: `, a, note ? ` – ${note}` : "");
        return frag;
      }));
      // Family Campus: its notes per version (and what is in progress, in a test build)
      const app = rn.app || {};
      if (v.dev) section(t("news.dev"), pick(app.unreleased) || []);
      (app.versions || []).slice(0, 2).forEach(x => section(t("news.app", { version: x.version }) + ` · ${longDate(x.date)}`, pick(x.notes) || []));
      if (!body.children.length) { const p = document.createElement("p"); p.textContent = t("news.none"); body.append(p); }
    }).catch(() => { const p = document.createElement("p"); p.textContent = t("news.failed"); dialog.querySelector(".body").replaceChildren(p); });
  }
})();
