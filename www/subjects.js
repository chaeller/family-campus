/* Family Campus – subjects: picture and name, shared by the home page (subject filter, tile tags) and the
   progress page. Exercises name their subjects by id ("math", "german"); the shown name is the key
   "subject.<id>" of the locale catalogue (a campus adds its own subjects there and their icons in
   campus.json → config.json "subjects"). Languages get their flag as a small SVG (flag emoji are not
   shown on Windows), several languages 🌐, every other subject an icon, 📘 by default. */
(function () {
  const FLAGS = {
    german: '<svg viewBox="0 0 5 3"><rect width="5" height="3" fill="#000"/><rect y="1" width="5" height="1" fill="#dd0000"/><rect y="2" width="5" height="1" fill="#ffce00"/></svg>',
    english: '<svg viewBox="0 0 60 30"><clipPath id="uk-t"><path d="M30,15h30v15zv15h-30zh-30v-15zv-15h30z"/></clipPath><rect width="60" height="30" fill="#012169"/><path d="M0,0L60,30M60,0L0,30" stroke="#fff" stroke-width="6"/><path d="M0,0L60,30M60,0L0,30" clip-path="url(#uk-t)" stroke="#c8102e" stroke-width="4"/><path d="M30,0v30M0,15h60" stroke="#fff" stroke-width="10"/><path d="M30,0v30M0,15h60" stroke="#c8102e" stroke-width="6"/></svg>',
    french: '<svg viewBox="0 0 3 2"><rect width="1" height="2" fill="#0055a4"/><rect x="1" width="1" height="2" fill="#fff"/><rect x="2" width="1" height="2" fill="#ef4135"/></svg>',
    italian: '<svg viewBox="0 0 3 2"><rect width="1" height="2" fill="#009246"/><rect x="1" width="1" height="2" fill="#fff"/><rect x="2" width="1" height="2" fill="#ce2b37"/></svg>',
    spanish: '<svg viewBox="0 0 3 2"><rect width="3" height="2" fill="#aa151b"/><rect y=".5" width="3" height="1" fill="#f1bf00"/></svg>'
  };
  const ICONS = {
    math: "📐", geometry: "📏", science: "🔬", physics: "🧲", chemistry: "⚗️", biology: "🧬", history: "🏛️",
    geography: "🌍", "media-it": "💻", "computer-science": "💾", ethics: "⚖️", music: "🎵", art: "🎨",
    sport: "🏃", "study-skills": "🧭", security: "🔐", ai: "🤖", law: "📜", traffic: "🚦", economics: "📈"
  };
  // subjects of the campus (config.json "subjects": {"<id>": {"icon": "🩺"}})
  if (window.I18n) I18n.ready.then(({ config }) => Object.entries(config.subjects || {}).forEach(([id, s]) => { if (s.icon) ICONS[id] = s.icon; }));

  const style = document.createElement("style");
  style.textContent = ".subj-icon{display:inline-block;margin-inline-end:5px;line-height:1}" +
    ".subj-icon.flag{width:1.25em;height:.85em;vertical-align:-1px;border-radius:2px;overflow:hidden;box-shadow:0 0 0 1px rgba(0,0,0,.15)}" +
    ".subj-icon.flag svg{display:block;width:100%;height:100%}";
  document.head.append(style);

  // shown name of a subject id (falls back to the id itself)
  const name = id => window.I18n && I18n.has("subject." + id) ? I18n.t("subject." + id) : id;
  // picture for one subject
  function icon(id) {
    const s = document.createElement("span");
    s.setAttribute("aria-hidden", "true");
    if (FLAGS[id]) { s.className = "subj-icon flag"; s.innerHTML = FLAGS[id]; }
    else { s.className = "subj-icon"; s.textContent = ICONS[id] || "📘"; }
    return s;
  }
  // picture and name for an exercise with its subjects ("3 languages" with 🌐 for several languages)
  function label(subjects) {
    const langs = (subjects || []).filter(x => FLAGS[x]);
    if (langs.length > 1 && langs.length === subjects.length) {
      const g = document.createElement("span"); g.className = "subj-icon"; g.setAttribute("aria-hidden", "true"); g.textContent = "🌐";
      return [g, I18n.t("subjects.languages", { count: langs.length })];
    }
    return subjects && subjects[0] ? [icon(subjects[0]), name(subjects[0])] : [];
  }
  window.CampusSubjects = { icon, label, name };
})();
