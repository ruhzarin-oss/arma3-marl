#!/usr/bin/env python3
"""Assemble envelop_replay.html (self-contained) en inlinant envelop_replay.json."""
import json, sys, io

SRC = sys.argv[1] if len(sys.argv) > 1 else "envelop_replay.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "envelop_replay.html"
data = json.load(open(SRC))
DATA_JS = json.dumps(data, separators=(",", ":"))

HTML = r"""<meta charset="utf-8">
<title>Débordement — replay top-down</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root{
    --bg:#080c0b; --panel:#0e1412; --panel2:#121a17; --grid:#18231e; --ring:#1e2c25;
    --ink:#c2cec8; --dim:#6c7d74; --faint:#3a453f;
    --west:#4d9bff; --deb:#24e0cf; --east:#ff5252; --fob:#ffbe3d; --fire:#fff0b8;
    --line:#1b2620;
  }
  *{box-sizing:border-box}
  html,body{margin:0}
  body{
    background:radial-gradient(120% 90% at 50% 0%,#0c1310 0%,var(--bg) 60%);
    color:var(--ink);
    font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
    -webkit-font-smoothing:antialiased; line-height:1.5;
    min-height:100vh; padding:clamp(14px,3vw,30px);
  }
  .wrap{max-width:920px;margin:0 auto;display:flex;flex-direction:column;gap:16px}
  .eyebrow{font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--dim);
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
  h1{font-size:clamp(22px,4vw,30px);margin:.15em 0 0;font-weight:650;letter-spacing:-.01em;text-wrap:balance}
  .sub{color:var(--dim);font-size:14px;margin:0}
  header{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap}
  .hud{display:flex;gap:8px;flex-wrap:wrap}
  .chip{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:7px 11px;
    display:flex;flex-direction:column;gap:1px;min-width:70px}
  .chip .k{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim)}
  .chip .v{font-size:17px;font-weight:650;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
    font-variant-numeric:tabular-nums;line-height:1.1}
  .v.west{color:var(--west)} .v.east{color:var(--east)} .v.win{color:var(--deb)} .v.lose{color:var(--east)}
  .stage{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
    border-radius:14px;padding:10px;box-shadow:0 10px 40px -20px #000 inset,0 1px 0 #ffffff08 inset}
  canvas{width:100%;display:block;border-radius:8px;touch-action:none}
  .controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
  button{font:inherit;color:var(--ink);background:var(--panel);border:1px solid var(--line);
    border-radius:8px;padding:8px 14px;cursor:pointer;transition:border-color .15s,background .15s}
  button:hover{border-color:var(--deb)}
  button:focus-visible{outline:2px solid var(--deb);outline-offset:2px}
  .play{min-width:96px;font-weight:600}
  .scrub{flex:1;min-width:140px;accent-color:var(--deb);cursor:pointer}
  .speed{display:flex;gap:4px}
  .speed button{padding:6px 9px;font-size:12px;font-family:ui-monospace,monospace}
  .speed button[aria-pressed=true]{border-color:var(--deb);color:var(--deb);background:#0f1a17}
  .tick{font-family:ui-monospace,monospace;font-variant-numeric:tabular-nums;color:var(--dim);
    font-size:13px;min-width:74px;text-align:right}
  .legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12.5px;color:var(--dim)}
  .legend span{display:inline-flex;align-items:center;gap:7px}
  .dot{width:10px;height:10px;border-radius:50%;display:inline-block}
  .note{color:var(--dim);font-size:13px;border-top:1px solid var(--line);padding-top:14px;margin:0}
  .note b{color:var(--ink);font-weight:600}
</style>

<div class="wrap">
  <header>
    <div>
      <div class="eyebrow">Harmattan · After-action · caméra top-down</div>
      <h1>Débordement — replay</h1>
      <p class="sub">Escouade WEST (12) contre une position EAST tenue (8). Fixer de face, déborder par le flanc.</p>
    </div>
    <div class="hud">
      <div class="chip"><span class="k">Tick</span><span class="v" id="hTick">0</span></div>
      <div class="chip"><span class="k">WEST</span><span class="v west" id="hWest">12</span></div>
      <div class="chip"><span class="k">EAST</span><span class="v east" id="hEast">8</span></div>
      <div class="chip"><span class="k">Issue</span><span class="v" id="hOut">—</span></div>
    </div>
  </header>

  <div class="stage">
    <canvas id="cv" aria-label="Vue top-down du débordement"></canvas>
  </div>

  <div class="controls">
    <button class="play" id="play" aria-label="Lecture/pause">▶ Lecture</button>
    <input class="scrub" id="scrub" type="range" min="0" value="0" step="1" aria-label="Position dans le replay">
    <div class="speed" role="group" aria-label="Vitesse">
      <button data-s="0.5">0.5×</button><button data-s="1" aria-pressed="true">1×</button><button data-s="2">2×</button>
    </div>
    <span class="tick" id="tickLbl">0 / 0</span>
  </div>

  <div class="legend">
    <span><i class="dot" style="background:var(--west)"></i>Fixeurs (ligne de feu)</span>
    <span><i class="dot" style="background:var(--deb)"></i>Débordeurs (flanc)</span>
    <span><i class="dot" style="background:var(--east)"></i>Défenseurs</span>
    <span><i class="dot" style="background:var(--fob)"></i>FOB / objectif</span>
    <span><i class="dot" style="background:var(--fire);box-shadow:0 0 6px var(--fire)"></i>Tir</span>
  </div>

  <p class="note"><b>Ce que tu regardes :</b> les fixeurs (bleu) tiennent l'ennemi de face, les débordeurs (cyan) filent au flanc puis rentrent sur le FOB. Source = <b>sandbox</b> (le geste, chiffres du finding) ; le même enregistreur se branche sur le <b>process Arma</b> pour filmer le vrai run. Ton retour : le placement, le geste, le tempo.</p>
</div>

<script>
const REPLAY = __DATA__;
const F = REPLAY.frames, N = F.length, FOB = REPLAY.fob;
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
// bornes monde (toutes frames)
let mnx=1e9,mxx=-1e9,mny=1e9,mxy=-1e9;
const seen=(x,y)=>{mnx=Math.min(mnx,x);mxx=Math.max(mxx,x);mny=Math.min(mny,y);mxy=Math.max(mxy,y)};
for(const fr of F){for(const u of fr.west)if(u[2])seen(u[0],u[1]);for(const u of fr.east)if(u[2])seen(u[0],u[1]);}
seen(FOB[0],FOB[1]);
const spanx=mxx-mnx||1, spany=mxy-mny||1, sp=Math.max(spanx,spany)*1.14;
const CX=(mnx+mxx)/2, CY=(mny+mxy)/2;
let W=800,H=620,dpr=1;
function resize(){
  const cssW=cv.clientWidth||800; dpr=Math.min(window.devicePixelRatio||1,2);
  W=cssW; H=Math.round(cssW*0.76);
  cv.width=W*dpr; cv.height=H*dpr; cv.style.height=H+'px';
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
const pad=26;
function sx(x){return pad+((x-CX)/sp+0.5)*(W-2*pad)}
function sy(y){return pad+(0.5-(y-CY)/sp)*(H-2*pad)}   // nord en haut
const scaleU=(W-2*pad)/sp;

function draw(f){
  const fr=F[Math.max(0,Math.min(N-1,f))];
  ctx.clearRect(0,0,W,H);
  // grille
  ctx.strokeStyle=getCSS('--grid');ctx.lineWidth=1;
  for(let gx=Math.ceil(mnx/25)*25; gx<=mxx; gx+=25){ctx.beginPath();ctx.moveTo(sx(gx),0);ctx.lineTo(sx(gx),H);ctx.stroke();}
  for(let gy=Math.ceil(mny/25)*25; gy<=mxy; gy+=25){ctx.beginPath();ctx.moveTo(0,sy(gy));ctx.lineTo(W,sy(gy));ctx.stroke();}
  // anneaux de portée autour du FOB
  ctx.strokeStyle=getCSS('--ring');
  for(const r of [25,50,75,100]){ctx.beginPath();ctx.arc(sx(FOB[0]),sy(FOB[1]),r*scaleU,0,7);ctx.stroke();}
  // FOB
  const fx=sx(FOB[0]),fy=sy(FOB[1]),fob=getCSS('--fob');
  ctx.strokeStyle=fob;ctx.fillStyle=fob;ctx.lineWidth=1.5;
  ctx.beginPath();ctx.moveTo(fx-8,fy);ctx.lineTo(fx,fy-8);ctx.lineTo(fx+8,fy);ctx.lineTo(fx,fy+8);ctx.closePath();ctx.stroke();
  ctx.globalAlpha=.18;ctx.fill();ctx.globalAlpha=1;
  ctx.font='10px ui-monospace,monospace';ctx.fillStyle=getCSS('--dim');ctx.textAlign='center';
  ctx.fillText('FOB',fx,fy+20);
  // traînées WEST
  const K=7, f0=Math.max(0,f-K);
  for(let i=0;i<REPLAY.A;i++){
    if(!F[f].west[i][2])continue;
    ctx.beginPath();let started=false;
    for(let g=f0;g<=f;g++){const u=F[g].west[i];if(!u[2]){started=false;continue;}
      const X=sx(u[0]),Y=sy(u[1]);if(started)ctx.lineTo(X,Y);else{ctx.moveTo(X,Y);started=true;}}
    ctx.strokeStyle=hex(F[f].west[i][3]?'--deb':'--west',.28);ctx.lineWidth=1.6;ctx.stroke();
  }
  // EAST
  for(const u of fr.east){const X=sx(u[0]),Y=sy(u[1]);
    if(u[2]){ctx.fillStyle=getCSS('--east');ctx.beginPath();ctx.arc(X,Y,3.6,0,7);ctx.fill();}
    else{ctx.strokeStyle=hex('--east',.35);ctx.lineWidth=1.4;cross(X,Y,3)}}
  // WEST
  for(let i=0;i<REPLAY.A;i++){const u=fr.west[i];const X=sx(u[0]),Y=sy(u[1]);const col=u[3]?getCSS('--deb'):getCSS('--west');
    if(!u[2]){ctx.strokeStyle=hex(u[3]?'--deb':'--west',.4);ctx.lineWidth=1.4;cross(X,Y,3);continue;}
    if(fr.firew&&fr.firew[i]){ctx.fillStyle=getCSS('--fire');ctx.globalAlpha=.9;ctx.beginPath();ctx.arc(X,Y,6.5,0,7);ctx.fill();ctx.globalAlpha=1;}
    ctx.fillStyle=col;ctx.beginPath();ctx.arc(X,Y,4,0,7);ctx.fill();}
  // HUD
  const wa=fr.west.filter(u=>u[2]).length, ea=fr.east.filter(u=>u[2]).length;
  document.getElementById('hTick').textContent=fr.t;
  document.getElementById('hWest').textContent=wa+'/'+REPLAY.A;
  document.getElementById('hEast').textContent=ea+'/'+REPLAY.B;
  document.getElementById('tickLbl').textContent=(f+1)+' / '+N;
  const out=document.getElementById('hOut');
  if(f>=N-1){const win=ea===0||wa>0&&ea<REPLAY.B*0.4;out.textContent=ea===0?'FOB pris':(wa===0?'échec':'en cours');out.className='v '+(ea<REPLAY.B*0.5?'win':'');}
  else{out.textContent='—';out.className='v';}
}
function cross(X,Y,r){ctx.beginPath();ctx.moveTo(X-r,Y-r);ctx.lineTo(X+r,Y+r);ctx.moveTo(X+r,Y-r);ctx.lineTo(X-r,Y+r);ctx.stroke();}
function getCSS(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}
function hex(v,a){const c=getCSS(v);const n=parseInt(c.slice(1),16);return `rgba(${n>>16&255},${n>>8&255},${n&255},${a})`;}

let cur=0, playing=false, speed=1, last=0, acc=0;
const scrub=document.getElementById('scrub');scrub.max=N-1;
const playBtn=document.getElementById('play');
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
function setF(f){cur=Math.max(0,Math.min(N-1,f));scrub.value=cur;draw(cur);}
function loop(ts){if(!playing)return;if(!last)last=ts;acc+=(ts-last)/1000;last=ts;
  const step=0.13/speed;
  while(acc>=step){acc-=step;if(cur>=N-1){playing=false;playBtn.textContent='↺ Rejouer';break;}setF(cur+1);}
  if(playing)requestAnimationFrame(loop);}
function play(){if(cur>=N-1)setF(0);playing=true;last=0;acc=0;playBtn.textContent='❚❚ Pause';requestAnimationFrame(loop);}
function pause(){playing=false;playBtn.textContent='▶ Lecture';}
playBtn.onclick=()=>playing?pause():play();
scrub.oninput=()=>{pause();setF(+scrub.value);};
document.querySelectorAll('.speed button').forEach(b=>b.onclick=()=>{
  speed=+b.dataset.s;document.querySelectorAll('.speed button').forEach(x=>x.setAttribute('aria-pressed',x===b));});
addEventListener('resize',()=>{resize();draw(cur);});
resize();setF(0);
if(!reduce)setTimeout(play,600);
</script>
"""

HTML = HTML.replace("__DATA__", DATA_JS)
open(OUT, "w").write(HTML)
print("wrote", OUT, len(HTML), "bytes")
