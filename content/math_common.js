/* Shared maths helpers for tiles (put in front of a content module: "module": "math_common.js+my_tile.js"):
   rnd(a, b) random integer, calc("3·4:2") evaluates · : −, show() formats an expression with · : −,
   variants(...) accepted spellings of an answer, fr(a, b) and pw(b, e) fractions and powers as HTML,
   gcd, lcm, isPrime, divisors, factorize, factHtml, factText. Styles in math.css ("css": "math.css"). */
const rnd = (a,b) => a+Math.floor(Math.random()*(b-a+1));
const calc = s => Function('"use strict";return ('+s.replace(/·/g,"*").replace(/:/g,"/").replace(/−/g,"-")+')')();
const show = s => s.replace(/\*/g,"·").replace(/\//g,":").replace(/-/g,"−");
// accepts answers with and without spaces, with - or −, with * or ·
const variants = (...xs) => [...new Set(xs.flatMap(x=>{ x=String(x); const a=[x, x.replace(/\s+/g,""), x.replace(/−/g,"-"), x.replace(/−/g,"-").replace(/\s+/g,"")]; return [...a, ...a.map(y=>y.replace(/·/g,"*")), ...a.map(y=>y.replace(/·/g,""))]; }))];
const fr = (a,b) => `<span class="frac"><sup>${a}</sup><span>⁄</span><sub>${b}</sub></span>`;
const pw = (b,e) => `${b}<sup>${e}</sup>`;
const gcd = (a,b) => b ? gcd(b, a%b) : a;
const lcm = (a,b) => a/gcd(a,b)*b;
const isPrime = n => { if (n<2) return false; for (let i=2;i*i<=n;i++) if (n%i===0) return false; return true; };
const divisors = n => Array.from({length:n},(_,i)=>i+1).filter(d=>n%d===0);
function factorize(n){ const f={}; for (let p=2; n>1; p++) while (n%p===0){ f[p]=(f[p]||0)+1; n/=p; } return f; }
const factHtml = f => Object.entries(f).map(([p,e])=> e>1 ? pw(p,e) : p).join(" · ");
const factText = f => Object.entries(f).map(([p,e])=> e>1 ? p+"^"+e : p).join("·");
