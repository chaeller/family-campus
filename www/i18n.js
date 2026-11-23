/* Family Campus – languages and locales (ADR-0012, spec B-17). No library.
   Which locale applies: the person's choice (stored on the server, /api/me), else the choice made
   on the login page (this browser), else the browser's languages matched against the locales the
   campus offers (config.json), else the campus default, else "en".
   Catalogues: locales/<tag>.json with a fallback chain, e.g. de-CH → de → en. A missing key falls
   back to English, never to the key name. Formats (dates, numbers, relative times, plurals) come
   from the browser's Intl APIs.
   Usage:  await I18n.ready;  I18n.t("login.submit");  I18n.t("sets", {count: 3});
           I18n.date(iso, {weekday: "short", day: "numeric", month: "short"});  I18n.number(1234.5);
           <span data-i18n="key"></span>, <input data-i18n-attr="placeholder:key">  → I18n.apply() */
(function () {
  const base = location.pathname.replace(/\/exercises\/[^/]+\/.*$/, "/").replace(/[^/]*$/, "");
  const STORE = "campus-locale";
  const RTL = ["ar", "he", "fa", "ur"];
  const store = { get() { try { return localStorage.getItem(STORE); } catch (e) { return null; } },
                  set(v) { try { localStorage.setItem(STORE, v); } catch (e) {} } };

  let locale = "en", messages = {}, config = { locales: ["en"], defaultLocale: "en", currency: "EUR" }, me = null;

  // "de-CH" → ["de-CH", "de", "en"]
  const chain = tag => { const out = []; const parts = tag.split("-");
    for (let i = parts.length; i > 0; i--) out.push(parts.slice(0, i).join("-"));
    if (!out.includes("en")) out.push("en"); return out; };

  // the first wish (in the order of the wishes) that the campus offers: per wish the exact tag, else the
  // same language (de-AT → de-CH); else nothing. A later exact match never beats an earlier wish:
  // ["de-DE", "de", "en"] on a de-CH/en campus gives de-CH, not en.
  function negotiate(wishes, offered) {
    const low = offered.map(o => o.toLowerCase());
    for (const w of wishes.filter(Boolean)) {
      const i = low.indexOf(w.toLowerCase()); if (i >= 0) return offered[i];
      const lang = w.split("-")[0].toLowerCase();
      const j = low.findIndex(o => o.split("-")[0] === lang); if (j >= 0) return offered[j];
    }
    return null;
  }

  // set <html lang> at once, before anything is fetched: the browser decides early whether to offer a
  // translation. The build writes the offered locales into the page (data-locales); the person's stored
  // choice on the server is applied after /api/me (see ready).
  const setLang = tag => { const html = document.documentElement; html.lang = tag; html.dir = RTL.includes(tag.split("-")[0]) ? "rtl" : "ltr"; };
  { const offered = (document.documentElement.dataset.locales || "").split(" ").filter(Boolean);
    const early = offered.length && (negotiate([store.get()], offered) || negotiate(navigator.languages || [navigator.language], offered));
    if (early) setLang(early); }

  const getJSON = url => fetch(url, { credentials: "same-origin" }).then(r => r.ok ? r.json() : null).catch(() => null);

  async function load(tag) {
    const parts = await Promise.all(chain(tag).reverse().map(t => getJSON(base + "locales/" + t + ".json")));
    messages = Object.assign({}, ...parts.filter(Boolean));   // en, then de, then de-CH: the most specific wins
    locale = tag;
    setLang(tag);
  }

  function t(key, params) {
    let m = messages[key];
    if (m === undefined) { console.warn("i18n: missing key", key); return key; }
    if (m && typeof m === "object") {   // plural forms: {"one": "…", "other": "…"}
      const n = params && params.count != null ? params.count : 0;
      m = m[new Intl.PluralRules(locale).select(n)] ?? m.other;
    }
    return String(m).replace(/\{(\w+)\}/g, (_, k) => params && params[k] != null
      ? (typeof params[k] === "number" ? number(params[k]) : params[k]) : "{" + k + "}");
  }

  const toDate = d => d instanceof Date ? d : new Date(/^\d{4}-\d\d-\d\d$/.test(d) ? d + "T12:00:00" : d);
  const date = (d, opts) => new Intl.DateTimeFormat(locale, opts || { day: "numeric", month: "long", year: "numeric" }).format(toDate(d));
  const time = d => new Intl.DateTimeFormat(locale, { hour: "2-digit", minute: "2-digit" }).format(toDate(d));
  const number = (n, opts) => new Intl.NumberFormat(locale, opts).format(n);
  const percent = n => new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: 0 }).format(n);
  const money = n => new Intl.NumberFormat(locale, { style: "currency", currency: config.currency }).format(n);
  // whole days from today: "heute", "morgen", "in 3 Tagen" / "today", "tomorrow", "in 3 days"
  const days = n => new Intl.RelativeTimeFormat(locale, { numeric: "auto" }).format(n, "day");
  // name of a locale in its own language: "Deutsch (Schweiz)", "English" – from the catalogue ("locale.name",
  // collected by tools/build.py into config.json), else from the browser
  const nameOf = tag => { if (config.localeNames && config.localeNames[tag]) return config.localeNames[tag]; try { const n = new Intl.DisplayNames([tag], { type: "language" }).of(tag); return n.charAt(0).toUpperCase() + n.slice(1); } catch (e) { return tag; } };

  const has = key => messages[key] !== undefined;
  // a name from the catalogue data: a plain string, or names per locale ({"en": "Primary school", "de": "Volksschule"})
  const name = v => v && typeof v === "object" ? (chain(locale).map(k => v[k]).find(x => x != null) ?? Object.values(v)[0]) : v;

  function apply(root) {
    (root || document).querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
    (root || document).querySelectorAll("[data-i18n-attr]").forEach(el => el.dataset.i18nAttr.split(",").forEach(pair => {
      const [attr, key] = pair.split(":"); el.setAttribute(attr.trim(), t(key.trim())); }));
  }

  // choose a locale: stored for the person (when logged in) and in this browser; reloads the page
  async function setLocale(tag) {
    if (!config.locales.includes(tag)) return;
    store.set(tag);
    if (me) await fetch(base + "api/me/locale", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ locale: tag }) }).catch(() => {});
    location.reload();
  }

  const ready = (async () => {
    const [cfg, who] = await Promise.all([getJSON(base + "config.json"), getJSON(base + "api/me")]);
    if (cfg) Object.assign(config, cfg);
    me = who && who.name ? who : null;
    const offered = config.locales.length ? config.locales : ["en"];
    const tag = negotiate([me && me.locale, store.get()], offered)
      || negotiate(navigator.languages || [navigator.language], offered)
      || negotiate([config.defaultLocale], offered) || offered[0];
    await load(tag);
    apply();
    return { locale, me, config };
  })();

  window.I18n = { ready, t, has, name, apply, date, time, number, percent, money, days, nameOf, setLocale, chain, negotiate,
    get locale() { return locale; }, get locales() { return config.locales; }, get config() { return config; },
    // a locale chosen by hand in this browser (login page switcher), null if it was only detected
    get chosen() { return store.get(); } };
})();
