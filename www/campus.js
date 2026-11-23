/* Family Campus – connects exercise pages to the server:
   load progress, store every answer and every run, repetition (spaced repetition box).
   Texts come from i18n.js (loaded before this file by every exercise page). */
(function () {
  const base = location.pathname.replace(/\/exercises\/[^/]+\/.*$/, "/").replace(/[^/]*$/, "");
  const ex = (location.pathname.match(/\/exercises\/([^/]+)\//) || [])[1] || "";
  let progress = {}, due = 0;

  async function api(path, body) {
    const r = await fetch(base + "api/" + path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), credentials: "same-origin" } : { credentials: "same-origin" });
    if (r.status === 401) { location.href = base + "login.html?next=" + encodeURIComponent(location.pathname); throw new Error("login"); }
    return r.json();
  }
  // stable key of a question (for the Lernkartei)
  function keyOf(set, q) {
    const core = JSON.stringify([ex, set, q.t, q.q, q.a || q.o || q.pairs || q.steps || q.items || q.rows || q.s || q.nodes || q.kind || ""]);
    let h = 0x811c9dc5;
    for (let i = 0; i < core.length; i++) { h ^= core.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
    return h.toString(16) + "-" + core.length.toString(36);
  }
  const plain = html => { const d = document.createElement("div"); d.innerHTML = html || ""; return d.textContent.replace(/\s+/g, " ").trim().slice(0, 300); };
  // correct solution as text (for the list of recent mistakes)
  const solText = q => { const v = q.sol || (q.a && q.a[0]) || (q.o && q.o[0]) || (q.items && q.items.map(i => i[0] + " → " + i[1]).join(", ")) || (q.steps && q.steps.join(" → ")) || (q.pairs && q.pairs.map(p => p[0] + " – " + p[1]).join(", ")) || "";
    return v ? "  ⟶ ✓ " + plain(String(v)).slice(0, 160) : ""; };   // stored as data: no words, only the sign
  const clean = q => { const c = {}; for (const k in q) if (!k.startsWith("__")) c[k] = q[k]; return c; };
  const fromServer = sets => { const p = {}; for (const [k, v] of Object.entries(sets || {})) p[k] = { best: v.best, runs: v.runs }; return p; };

  window.Campus = {
    ex,
    async init() {
      try { const d = await api("progress?ex=" + encodeURIComponent(ex)); progress = fromServer(d.sets); due = d.due || 0; }
      catch (e) { if (e.message === "login") return new Promise(() => {}); }
    },
    progress: () => progress,
    setProgress(d) { const p = {}; for (const k in d) if (!k.startsWith("__")) p[k] = d[k]; progress = p; },
    answer(mod, set, q, ok, isRetry) {
      const repeat = set.id === "__repeat";
      const setId = repeat ? (q.__set || "?") : set.id;
      api("answer", { ex, set: setId, key: q.__key || keyOf(setId, q), ok, mode: repeat ? "repeat" : isRetry ? "retry" : "normal", q: clean(q), text: plain(q.q) + solText(q) })
        .then(d => { due = d.due; }).catch(() => {});
    },
    result(set, right, total, isRetry) {
      const repeat = set.id === "__repeat";
      api("result", { ex, set: repeat ? "__repeat" : set.id, total, correct: right, mode: repeat ? "repeat" : isRetry ? "retry" : "normal" })
        .then(d => { progress = fromServer(d.sets); due = d.due; }).catch(() => {});
    },
    repeatCard() {
      if (!due) return null;
      const card = document.createElement("div");
      card.className = "card";
      card.style.cssText = "border:2px solid #f59f00;background:#fff9db";
      card.innerHTML = `<div class="row"><div style="flex:1"><b></b><div class="small muted"></div></div></div>`;
      card.querySelector("b").textContent = "🔁 " + I18n.t("repeat.title");
      card.querySelector(".small").textContent = I18n.t("repeat.due", { count: due }) + " – " + I18n.t("repeat.cardHint");
      const b = document.createElement("button"); b.className = "btn"; b.textContent = I18n.t("repeat.start");
      b.onclick = () => Campus.startRepeat();
      card.querySelector(".row").append(b);
      return card;
    },
    async startRepeat() {
      const items = await api("repeat?ex=" + encodeURIComponent(ex));
      if (!items.length) { go("module", MODULES[0]); return; }
      const qs = items.map(it => Object.assign(it.q, { __key: it.key, __set: it.set }));
      const set = { id: "__repeat", title: "🔁 " + I18n.t("repeat.title"), qs: () => qs.map(q => Object.assign({}, q)) };
      runQuiz(MODULES[0], set, shuffle(qs.slice()), false);
    },
    start() {
      Promise.all([Campus.init(), I18n.ready]).then(() => { if (location.hash === "#repeat") Campus.startRepeat(); else go("module", MODULES[0]); });
    }
  };
})();
