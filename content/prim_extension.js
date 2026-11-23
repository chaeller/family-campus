/* Extension for tiles that practise Prim's algorithm: question type "prim".
   The learner connects all points of a network as cheaply as possible by tapping connections;
   a wrong tap (a cycle, a loose connection, a more expensive one) counts as a mistake.
   Question: {t:"prim", q, nodes:{A:[x,y],…}, edges:[[from,to,cost],…], start, e}
   Texts are the tile's content (English); a campus can bring its own version in its language. */
const SVG_NS = "http://www.w3.org/2000/svg";
const S = (tag, attrs) => { const e = document.createElementNS(SVG_NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };

const EXTRA_TYPES = {
 prim(q, card, finish){
  card.append(h("div",{class:"q",html:q.q+'<span class="hint">Start at <b>'+q.start+'</b>. Always tap the cheapest connection from a point that is already connected (blue) to a new point.</span>'}));
  const svg = S("svg",{viewBox:"0 0 340 260",class:"geo prim",style:"width:100%;max-width:420px;touch-action:manipulation"});
  const inTree = new Set([q.start]); const chosen = []; let mistakes = 0, total = 0;
  const nodeEl = {};
  const status = h("div",{class:"small",style:"margin-top:8px;min-height:2.6em"});
  const edgeEls = q.edges.map(([a,b,w])=>{
    const [x1,y1]=q.nodes[a], [x2,y2]=q.nodes[b], mx=(x1+x2)/2, my=(y1+y2)/2;
    const g = S("g",{class:"pe"});
    const line = S("line",{x1,y1,x2,y2,style:"stroke:#b9b3d6;stroke-width:4;stroke-linecap:round"});
    const hit = S("line",{x1,y1,x2,y2,style:"stroke:transparent;stroke-width:22;cursor:pointer"});
    const lab = S("rect",{x:mx-13,y:my-11,width:26,height:22,rx:7,style:"fill:#fff;stroke:#b9b3d6;stroke-width:1.5;cursor:pointer"});
    const t = S("text",{x:mx,y:my+5,"text-anchor":"middle","font-size":"14","font-weight":"700",style:"fill:#26233a;cursor:pointer;user-select:none"});
    t.textContent = w;
    g.append(line,hit,lab,t); g._line=line; g._lab=lab;
    g.addEventListener("click",()=>pickEdge(a,b,w,g));
    return g;
  });
  edgeEls.forEach(g=>svg.append(g));
  Object.entries(q.nodes).forEach(([n,[x,y]])=>{
    const c = S("circle",{cx:x,cy:y,r:16,style:"fill:#fff;stroke:#26233a;stroke-width:2.5"});
    const t = S("text",{x,y:y+5,"text-anchor":"middle","font-size":"15","font-weight":"800",style:"fill:#26233a;pointer-events:none"});
    t.textContent=n; svg.append(c,t); nodeEl[n]={c,t};
  });
  function paint(){
    Object.entries(nodeEl).forEach(([n,{c,t}])=>{ const on=inTree.has(n);
      c.setAttribute("style", on?"fill:#6b4eff;stroke:#6b4eff;stroke-width:2.5":"fill:#fff;stroke:#26233a;stroke-width:2.5");
      t.setAttribute("style", on?"fill:#fff;pointer-events:none":"fill:#26233a;pointer-events:none"); });
    status.innerHTML = `Connected: <b>${[...inTree].join(", ")}</b> · cost so far: <b>${total}</b>`;
  }
  function candidates(){ return q.edges.filter(([a,b])=>inTree.has(a)!==inTree.has(b)); }
  function flash(g,msg){
    mistakes++; g._line.setAttribute("style","stroke:#d64545;stroke-width:5;stroke-linecap:round");
    setTimeout(()=>{ if(!g._done) g._line.setAttribute("style","stroke:#b9b3d6;stroke-width:4;stroke-linecap:round"); },700);
    status.innerHTML = "❌ "+msg;
    setTimeout(paint,1600);
  }
  function pickEdge(a,b,w,g){
    if (g._done || inTree.size===Object.keys(q.nodes).length) return;
    const ia=inTree.has(a), ib=inTree.has(b);
    if (ia && ib) return flash(g,`${a} and ${b} are already connected – this would make a cycle.`);
    if (!ia && !ib) return flash(g,`This connection does not touch the network yet. Start from a blue point.`);
    const min = Math.min(...candidates().map(e=>e[2]));
    if (w>min) return flash(g,`There is a cheaper connection (cost ${min}).`);
    g._done=true; chosen.push(a+b); total+=w; inTree.add(ia?b:a);
    g._line.setAttribute("style","stroke:#1f9d55;stroke-width:7;stroke-linecap:round");
    g._lab.setAttribute("style","fill:#e3f7ea;stroke:#1f9d55;stroke-width:2");
    paint();
    if (inTree.size===Object.keys(q.nodes).length){
      finish(mistakes===0, `Order: <b>${chosen.join(" → ")}</b><br>Total cost: <b>${total}</b>`+(mistakes?` · wrong taps: ${mistakes}`:""));
    }
  }
  card.append(svg,status); paint();
 }
};
