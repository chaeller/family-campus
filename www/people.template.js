/* Family Campus – names and colours of the people, shared by the login, home and progress page.
   Template: tools/build.py writes people.js from campus.json. Public on purpose (the login page lists
   the names before anybody is logged in); everything else about a person (level, focus list, exams)
   stays in exercises.json behind the login. A new person needs an entry in campus.json and in
   CAMPUS_USERS (campus.env). */
(function () {
  const LIST = /* LIST */[];   // written by tools/build.py from campus.json
  const color = name => (LIST.find(p => p.name === name) || {}).color || "#6c6886";
  // black or white text, whichever reads better on the colour
  function textOn(hex) {
    const n = parseInt(hex.slice(1), 16), lin = c => { c /= 255; return c <= .03928 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4; };
    const L = .2126 * lin(n >> 16 & 255) + .7152 * lin(n >> 8 & 255) + .0722 * lin(n & 255);
    return (L + .05) / .05 > 1.05 / (L + .05) ? "#1a1726" : "#ffffff";
  }
  // give an element the person's colours as CSS variables (--c background, --c-text text on it)
  function paint(el, name) { const c = color(name); el.style.setProperty("--c", c); el.style.setProperty("--c-text", textOn(c)); return el; }
  window.CampusPeople = { list: LIST, names: LIST.map(p => p.name), color, textOn, paint };
})();
