/* Demo tile of the app: "Internet basics" (content language: English).
   Shows a summary sheet, several question types, generated questions (IP addresses, network costs)
   and an extension with its own question type (Prim's algorithm, see prim_extension.js).
   Sources: RFC 791 (IPv4), RFC 1918 (private addresses), RFC 8200 (IPv6), RFC 1034 (DNS),
   R. C. Prim: "Shortest connection networks and some generalizations" (1957). Written for the app. */

// ---- networks for Prim's algorithm: fixed layout, costs are shuffled on every run
const NETWORKS = [
 {nodes:{A:[40,60],B:[170,30],C:[300,70],D:[60,215],E:[190,160],F:[305,215]},
  edges:[["A","B"],["A","D"],["A","E"],["B","C"],["B","E"],["C","E"],["C","F"],["D","E"],["E","F"],["D","F"]]},
 {nodes:{A:[60,45],B:[280,45],C:[315,185],D:[170,235],E:[30,185],M:[175,135]},
  edges:[["A","B"],["B","C"],["C","D"],["D","E"],["E","A"],["A","M"],["B","M"],["C","M"],["D","M"],["E","M"]]},
 {nodes:{A:[40,40],B:[170,40],C:[300,40],D:[40,215],E:[170,215],F:[300,215],G:[170,128]},
  edges:[["A","B"],["B","C"],["A","D"],["C","F"],["D","E"],["E","F"],["A","G"],["B","G"],["C","G"],["D","G"],["E","G"],["F","G"]]}
];
function primQ(i){
  const n = NETWORKS[i];
  const ws = shuffle(Array.from({length:20},(_,k)=>k+1)).slice(0,n.edges.length);   // all costs different
  const start = pick(Object.keys(n.nodes),1)[0];
  return {t:"prim", q:"A network should connect all houses – as <b>cheaply as possible</b>. Use <b>Prim's algorithm</b>.",
    nodes:n.nodes, edges:n.edges.map((e,k)=>[e[0],e[1],ws[k]]), start,
    e:"Prim: always add the cheapest connection from the connected part to a new point. Never close a cycle."};
}

// ---- IP addresses: generated, checked by rule (four numbers 0–255)
const rnd = (a,b) => a+Math.floor(Math.random()*(b-a+1));
const validIp = () => [rnd(1,223),rnd(0,255),rnd(0,255),rnd(1,254)].join(".");
const invalidIp = () => pick([
  () => [rnd(1,223),rnd(256,320),rnd(0,255),rnd(1,254)].join("."),     // a number above 255
  () => [rnd(1,223),rnd(0,255),rnd(0,255)].join("."),                 // only three parts
  () => [rnd(1,223),rnd(0,255),rnd(0,255),rnd(1,254),rnd(1,9)].join("."),   // five parts
  () => [rnd(1,223),rnd(0,255),"x",rnd(1,254)].join(".")              // not a number
],1)[0]();
function ipValidQ(){
  const ok = Math.random() < .5, ip = ok ? validIp() : invalidIp();
  return {t:"mc", q:`Is <code>${ip}</code> a valid IPv4 address?`, o: ok ? ["yes","no"] : ["no","yes"],
    e:"An IPv4 address has four numbers from 0 to 255, separated by dots."};
}
const PRIVATE = [["10.0.0.1","private"],["10.20.30.40","private"],["172.16.5.4","private"],["172.31.200.1","private"],["192.168.1.10","private"],["192.168.0.254","private"],
  ["8.8.8.8","public"],["1.1.1.1","public"],["172.32.0.1","public"],["193.5.20.1","public"],["11.0.0.1","public"],["192.169.1.1","public"]];

// ---- devices and services
const ROLES = [
 ["Router","forwards data between your home network and the internet"],
 ["Server","a computer that offers data or services to others, day and night"],
 ["Internet service provider","the company that sells you access to the internet"],
 ["DNS","translates names like example.org into IP addresses"],
 ["Wi-Fi access point","connects devices to a network by radio"]
];
const ROLE_CASES = [
 // [case, answer, answers that would also be defensible and are never offered]
 ["Your laptop asks which IP address belongs to «example.org».","DNS"],
 ["The box at home passes data from the internet on to the right phone.","Router",["Wi-Fi access point"]],
 ["A video platform keeps millions of videos ready to be watched.","Server"],
 ["You sign a contract to get internet access at home.","Internet service provider"],
 ["Your phone joins the network by radio without a cable.","Wi-Fi access point",["Router"]]
];

const roleQ = ([c,k,not=[]]) => ({ t:"mc", q:`Which part is this?<br><b>${c}</b>`, o:[k, ...pick(ROLES.map(r=>r[0]).filter(x=>x!==k && !not.includes(x)),3)] });

// ---- think before you post
const POSTS = [
 ["A photo of your own drawing","fine"],
 ["A sunset you photographed yourself","fine"],
 ["A video of your own song","fine"],
 ["A photo of a friend – without asking them","ask first"],
 ["A screenshot of a private chat with someone","ask first"],
 ["A group photo from a party with many people on it","ask first"],
 ["Your home address and phone number","keep private"],
 ["A photo of your passport","keep private"],
 ["Your password, «just for a friend»","keep private"]
];

const MODULES = [
{ id:"internet", emo:"🌐", c:"#0e8f7e", title:"Internet basics", desc:"Router, server and provider, IP addresses, Prim's algorithm and thinking before you post.",
learn:`
<h2>🌐 Internet basics</h2>
<p>This is the demo tile of Family Campus: a summary sheet, then short sets to practise. Mistakes come back later in the revision box until they stick.</p>

<h3>1. Who does what?</h3>
<div class="scroll"><table class="t">
<tr><th>Part</th><th>What it does</th><th>Example</th></tr>
${ROLES.map(([a,b])=>`<tr><td><b>${a}</b></td><td>${b}</td><td>${{"Router":"the internet box at home","Server":"the computers of a video platform","Internet service provider":"your phone or cable company","DNS":"example.org → its IP address","Wi-Fi access point":"often built into the router"}[a]}</td></tr>`).join("")}
</table></div>

<h3>2. IP addresses</h3>
<p>Every device on the internet has an <b>IP address</b> (Internet Protocol), like a postal address for data. An <b>IPv4</b> address has <b>four numbers from 0 to 255</b>, separated by dots: <code>192.0.2.17</code>. That gives about 4.3 billion addresses – not enough, so the newer <b>IPv6</b> uses 128 bits instead of 32: <code>2001:db8::1</code>.</p>
<div class="key"><b>Private addresses</b> (RFC 1918) are used inside home and office networks and are not reachable from the internet:<br>
<code>10.0.0.0 – 10.255.255.255</code> · <code>172.16.0.0 – 172.31.255.255</code> · <code>192.168.0.0 – 192.168.255.255</code><br>
<code>127.0.0.1</code> is always your own device ("localhost").</div>
<p>From an IP address, websites can often tell your <b>approximate location</b> and your <b>provider</b> – which is why search results and ads can be local.</p>

<h3>3. Prim's algorithm</h3>
<p>An <b>algorithm</b> is an exact step-by-step recipe. <b>Prim's algorithm</b> connects all points of a network as cheaply as possible:</p>
<ol>
<li>Start at any point.</li>
<li>Among all connections from the connected part to a <b>new</b> point, take the <b>cheapest</b>.</li>
<li>Repeat until every point is connected. Never add a connection between two points that are already connected (that would make a cycle).</li>
</ol>

<h3>4. Think before you post</h3>
<ul>
<li><b>Your own work</b> (your drawing, your photo of a sunset) – fine to share.</li>
<li><b>Other people</b> on a photo or in a chat – <b>ask them first</b>.</li>
<li><b>Personal data</b> (address, phone number, passwords, ID documents) – <b>keep private</b>.</li>
</ul>
<p>What you post can stay online for a long time and be copied by others: your <b>digital footprint</b>. Rules about photos of people differ from country to country.</p>

<h3>Sources</h3>
<ul class="small">
<li><a href="https://www.rfc-editor.org/rfc/rfc791" target="_blank" rel="noopener">RFC 791</a> (IPv4), <a href="https://www.rfc-editor.org/rfc/rfc1918" target="_blank" rel="noopener">RFC 1918</a> (private addresses), <a href="https://www.rfc-editor.org/rfc/rfc8200" target="_blank" rel="noopener">RFC 8200</a> (IPv6), <a href="https://www.rfc-editor.org/rfc/rfc1034" target="_blank" rel="noopener">RFC 1034</a> (DNS)</li>
<li>R. C. Prim: <i>Shortest connection networks and some generalizations</i>, Bell System Technical Journal, 1957</li>
</ul>
`,
sets: [
 {id:"ib1", title:"Router, server, provider", qs: () => [
  { t:"match", q:"Match each part with what it does.", pairs: pick(ROLES,4).map(([a,b])=>[a,b]) },
  ...pick(ROLE_CASES,4).map(roleQ),
  { t:"in", q:"What does <b>IP</b> stand for? Internet …", a:["Protocol"], sol:"Protocol" }
 ]},
 {id:"ib2", title:"IP addresses", qs: () => [
  ...Array.from({length:4}, ipValidQ),
  { t:"sort", q:"Private or public address?", cats:["private","public"], items: pick(PRIVATE.filter(x=>x[1]==="private"),3).concat(pick(PRIVATE.filter(x=>x[1]==="public"),3)) },
  { t:"in", q:"How many numbers does an IPv4 address have?", a:["4","four"], sol:"4", num:true },
  { t:"in", q:"What is the largest number in one part of an IPv4 address?", a:["255"], sol:"255", num:true },
  { t:"mc", q:"Which address always means <b>your own device</b>?", o:["127.0.0.1","192.168.1.1","8.8.8.8","0.0.0.0"] },
  { t:"mc", q:"How long is an <b>IPv6</b> address?", o:["128 bits","32 bits","64 bits","256 bits"], e:"IPv4 has 32 bits (about 4.3 billion addresses), IPv6 has 128 bits." }
 ]},
 {id:"ib3", title:"Prim's algorithm", noShuffle:true, qs: () => [
  { t:"order", q:"Put the steps of Prim's algorithm in order.", steps:["Start at any point.","Look at all connections from the connected part to a new point.","Take the cheapest of them.","Repeat until every point is connected."] },
  primQ(0), primQ(1), primQ(2),
  { t:"mc", q:"Why must Prim's algorithm never add a connection between two points that are <b>already connected</b>?", o:["It would make a cycle and cost more without connecting anything new.","It would disconnect the network.","It is always the most expensive one.","Points may only have one connection."] }
 ]},
 {id:"ib4", title:"Think before you post", qs: () => [
  { t:"sort", q:"Post it, ask first, or keep it private?", cats:["fine","ask first","keep private"], items: ["fine","ask first","keep private"].flatMap(k => pick(POSTS.filter(x=>x[1]===k),2)) },
  { t:"mc", q:"You took a funny photo of a friend. What do you do before posting it?", o:["Ask the friend whether it is okay.","Post it – it is your photo.","Post it, but only for one day.","Blur the background."] },
  { t:"mc", q:"What is your <b>digital footprint</b>?", o:["Everything about you that can be found online","The weight of your phone","Your Wi-Fi password","The speed of your connection"] },
  { t:"mc", q:"A stranger in a game asks for your address «to send you a prize». What do you do?", o:["Do not send it and tell an adult you trust.","Send it – prizes are fun.","Send only the street.","Send your phone number instead."] }
 ]},
 {id:"ib5", title:"Mix", qs: () => [
  ...pick(ROLE_CASES,2).map(roleQ),
  ipValidQ(), ipValidQ(),
  primQ(Math.floor(Math.random()*NETWORKS.length)),
  ...pick(POSTS,2).map(([p,k])=>({ t:"mc", q:`<b>${p}</b> – post it?`, o:[k, ...["fine","ask first","keep private"].filter(x=>x!==k)] }))
 ]}
]}
];
