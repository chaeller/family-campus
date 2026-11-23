"""Smoke test for exercise pages: renders every question of every set (several runs)
and checks content consistency. Usage: python3 selftest.py <index.html>..."""
import sys, subprocess, re, os, tempfile

CAMPUS_STUB = """<script>window.Campus={progress:()=>({}),setProgress(){},answer(){},result(){},repeatCard:()=>null,init(){},start(){}};
window.I18n={t:k=>k,has:()=>true,name:v=>v,percent:x=>Math.round(x*100)+" %",number:x=>String(x),date:x=>String(x),time:x=>String(x),days:n=>String(n),locale:"en",locales:["en"],ready:Promise.resolve({})};</script>"""
PROBE = r'''
window.onerror=(m,src,l)=>{document.body.setAttribute("data-test","ERR "+m+" @"+l)};
go("module", MODULES[0]);
(function(){
 const out=[], probs=[]; let nq=0;
 try{
  for (const m of MODULES){
   go("learn",m);
   for (const s of m.sets){
    for (let run=0; run<6; run++){
     const qs=s.qs();
     runQuiz(m,s,qs,false);
     qs.forEach((q,i)=>{
      current.idx=i; showQ(); nq++;
      if(!TYPES[q.t]) probs.push(s.id+": unknown type "+q.t);
      if(q.t==="mc"){ if(new Set(q.o).size!==q.o.length) probs.push(s.id+": duplicate mc option in «"+q.q.replace(/<[^>]+>/g,"")+"» "+JSON.stringify(q.o)); }
      if(q.t==="in"){ const sol=(q.nospace||/</.test(q.sol||"")||/ Fr\.$/.test(q.sol||"")) ? q.a[0] : (q.sol||q.a[0]); const typed = q.nospace ? sol.replace(/([+\-=])/g," $1 ").replace(/\s+/g," ").trim() : sol; const chk = q.nospace ? typed.replace(/\s+/g,"").replace(/−/g,"-").replace(/[·*]/g,"") : (q.num ? (q.sol||q.a[0]).trim().replace(/\s*[^\d\s,.\-−][^\d]*$/,"") : typed); if(checkText(chk,q.a)!=="ok") probs.push(s.id+": sol not accepted «"+sol+"» "+JSON.stringify(q.a)); }
      if(q.t==="match"){ const l=q.pairs.map(p=>p[0]), r=q.pairs.map(p=>p[1]); if(new Set(l).size!==l.length||new Set(r).size!==r.length) probs.push(s.id+": duplicate match side "+JSON.stringify(q.pairs)); }
      if(q.t==="tap"){ const toks=q.s.split(" ").map(t=>t.replace(/[.,!?;:«»]/g,"").toLowerCase()); q.a.forEach(a=>{ if(!toks.includes(a)) probs.push(s.id+": tap answer not in sentence: "+a+" | "+q.s); }); }
      if(q.t==="sort"){ q.items.forEach(([w,c])=>{ if(!q.cats.includes(c)) probs.push(s.id+": sort cat "+c); }); }
     });
    }
   }
  }
  out.push("questions rendered: "+nq);
 }catch(e){ out.push("ERR "+e.stack); }
 out.push(probs.length? "PROBLEMS:\n  "+[...new Set(probs)].join("\n  ") : "no problems");
 document.body.setAttribute("data-test", out.join(" | "));
})();
'''

for path in sys.argv[1:]:
    src = open(path, encoding="utf-8").read()
    assert src.count('\nCampus.start();\n') == 1, path
    html = src.replace('<script src="../../i18n.js"></script>', '').replace('<script src="../../campus.js"></script>', CAMPUS_STUB).replace('\nCampus.start();\n', "\n" + PROBE.replace('go("module", MODULES[0]);', 'Campus.init(); go("module", MODULES[0]);', 1) + "\n")
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html); tmp = f.name
    dom = subprocess.run(["chromium", "--headless", "--disable-gpu", "--dump-dom", "file://" + tmp],
                         capture_output=True, text=True, timeout=120).stdout
    os.unlink(tmp)
    m = re.search(r'data-test="([^"]*)"', dom)
    import html as H
    print("==", os.path.basename(os.path.dirname(path)) + ":", H.unescape(m.group(1)) if m else "NO RESULT")
