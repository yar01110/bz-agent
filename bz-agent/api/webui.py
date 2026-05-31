"""Minimal browser UI for the demo (served at GET /).

A single self-contained HTML page: a text box + button that POSTs to
/plan-itinerary and renders the returned itinerary. No build step, no framework;
markdown is rendered with a tiny CDN script so the output looks nice in a demo.
"""

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>BZ-Agent · Bolzano Smart-City Orchestrator</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  :root { --bz:#2563eb; }
  * { box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
         margin:0; background:#0f172a; color:#e2e8f0; }
  .wrap { max-width:720px; margin:0 auto; padding:32px 20px 64px; }
  h1 { font-size:1.5rem; margin:0 0 4px; }
  .sub { color:#94a3b8; margin:0 0 24px; font-size:.95rem; }
  form { display:flex; gap:8px; }
  input { flex:1; padding:12px 14px; border-radius:10px; border:1px solid #334155;
          background:#1e293b; color:#e2e8f0; font-size:1rem; }
  button { padding:12px 18px; border:0; border-radius:10px; background:var(--bz);
           color:#fff; font-weight:600; cursor:pointer; font-size:1rem; }
  button:disabled { opacity:.5; cursor:wait; }
  .chips { margin:12px 0 0; display:flex; gap:8px; flex-wrap:wrap; }
  .chip { font-size:.8rem; color:#cbd5e1; background:#1e293b; border:1px solid #334155;
          padding:6px 10px; border-radius:999px; cursor:pointer; }
  #steps { margin-top:18px; display:flex; flex-direction:column; gap:6px; }
  .step { color:#94a3b8; font-size:.9rem; opacity:.5; transition:opacity .2s; }
  .step.done { color:#10b981; opacity:1; }
  #out { margin-top:16px; background:#1e293b; border:1px solid #334155; border-radius:12px;
         padding:20px; min-height:60px; line-height:1.55; }
  #out h1,#out h2 { font-size:1.1rem; }
  .status { color:#94a3b8; font-style:italic; }
  footer { margin-top:28px; color:#64748b; font-size:.8rem; }
</style>
</head>
<body>
<div class="wrap">
  <h1>🏔️ BZ-Agent</h1>
  <p class="sub">Multi-agent smart-city orchestrator for Bolzano · live Open Data Hub + Bedrock</p>

  <form id="f">
    <input id="q" autocomplete="off"
           placeholder="e.g. I want to visit a museum in the centre and find parking"/>
    <button id="b" type="submit">Plan</button>
  </form>
  <div class="chips">
    <span class="chip">I want to visit a museum and find parking nearby</span>
    <span class="chip">Show me places to see near the centre</span>
    <span class="chip">Where can I park downtown?</span>
  </div>

  <div id="steps"></div>
  <div id="out"><span class="status">Your itinerary will appear here.</span></div>
  <footer>Retriever → Reasoner → Generator · streamed live · state in DynamoDB</footer>
</div>

<script>
const f=document.getElementById('f'), q=document.getElementById('q'),
      b=document.getElementById('b'), out=document.getElementById('out'),
      steps=document.getElementById('steps');
document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{q.value=c.textContent.trim();q.focus();});

function addStep(msg){ const d=document.createElement('div'); d.className='step done';
  d.textContent='✓ '+msg; steps.appendChild(d); }

f.onsubmit=async(e)=>{
  e.preventDefault();
  const text=q.value.trim(); if(!text) return;
  b.disabled=true; steps.innerHTML=''; out.innerHTML='<span class="status">Working…</span>';
  try{
    const r=await fetch('/plan-itinerary/stream',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({user_id:'web',session_id:'web-'+Date.now(),request:text})});
    const reader=r.body.getReader(); const dec=new TextDecoder(); let buf='';
    while(true){
      const {value,done}=await reader.read(); if(done) break;
      buf+=dec.decode(value,{stream:true});
      let idx;
      while((idx=buf.indexOf('\\n\\n'))>=0){
        const line=buf.slice(0,idx).trim(); buf=buf.slice(idx+2);
        if(!line.startsWith('data:')) continue;
        const ev=JSON.parse(line.slice(5).trim());
        if(ev.type==='progress'){ addStep(ev.message); }
        else if(ev.type==='done'){ out.innerHTML=marked.parse(ev.itinerary||'(no itinerary)'); }
      }
    }
  }catch(err){ out.innerHTML='<span class="status">Request failed: '+err+'</span>'; }
  b.disabled=false;
};
</script>
</body>
</html>"""
