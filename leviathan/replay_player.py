#!/usr/bin/env python3
"""replay_player.py — LECTEUR ANIMÉ vue de dessus : la « vidéo » du run, avec le PLAN RÉEL en fond.

Pourquoi pas une vraie vidéo : ffmpeg est absent, et un lecteur HTML fait mieux —
play/pause, curseur temporel, vitesse, traînée réglable. Tu remontes le temps où tu veux.

Entrée : le JSON d'un run (envelop_arma) + le plan baké (bake_map.py) s'il existe.
Sortie : un HTML autonome (canvas + contrôles), aucune dépendance.

Usage : python replay_player.py leviathan/ab3_8_envelop_1.json [--out replay.html]
"""
import sys, os, json, glob, argparse

CSS = """:root{--bg:#fff;--bg2:#f6f7f9;--fg:#111;--mut:#666;--line:#e3e6ea;--ground:#eceff3;--bat:#c3cad4;--road:#dfe4ea}
@media(prefers-color-scheme:dark){:root{--bg:#0f1115;--bg2:#171a20;--fg:#e8eaed;--mut:#9aa0a6;--line:#2a2f38;--ground:#12151b;--bat:#3a4150;--road:#232833}}
:root[data-theme=dark]{--bg:#0f1115;--bg2:#171a20;--fg:#e8eaed;--mut:#9aa0a6;--line:#2a2f38;--ground:#12151b;--bat:#3a4150;--road:#232833}
:root[data-theme=light]{--bg:#fff;--bg2:#f6f7f9;--fg:#111;--mut:#666;--line:#e3e6ea;--ground:#eceff3;--bat:#c3cad4;--road:#dfe4ea}
body{background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,sans-serif;margin:0;padding:20px}
h1{font-size:19px;margin:0 0 2px}.sub{color:var(--mut);font-size:13px;margin-bottom:16px}
.wrap{border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:20px;background:var(--bg)}
canvas{width:100%;max-width:720px;border-radius:8px;display:block;background:var(--ground)}
.ctl{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:10px}
button{font:inherit;padding:5px 14px;border-radius:7px;border:1px solid var(--line);background:var(--bg2);color:var(--fg);cursor:pointer}
button:hover{border-color:var(--mut)}
input[type=range]{flex:1;min-width:180px}
.t{font-variant-numeric:tabular-nums;color:var(--mut);font-size:13px;min-width:104px}
.lg{color:var(--mut);font-size:12px;margin-top:8px}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin:0 4px 0 10px;vertical-align:baseline}
select{font:inherit;padding:4px 8px;border-radius:6px;border:1px solid var(--line);background:var(--bg2);color:var(--fg)}"""

JS = r"""
function mkPlayer(el, D){
  const cv = el.querySelector('canvas'), ctx = cv.getContext('2d');
  const rng = el.querySelector('.rng'), lbl = el.querySelector('.t'), btn = el.querySelector('.play');
  const spd = el.querySelector('.spd'), trailSel = el.querySelector('.trail');
  const DPR = Math.min(2, window.devicePixelRatio||1), W=720, H=720;
  cv.width = W*DPR; cv.height = H*DPR; cv.style.height = 'auto'; ctx.scale(DPR,DPR);
  const css = getComputedStyle(document.documentElement);
  // --- cadrage : englobe trajectoires + objectif + plan ---
  let xs=[0], ys=[0];
  D.frames.forEach(f=>f.west.forEach(w=>{xs.push(w[0]-D.fob[0]); ys.push(w[1]-D.fob[1]);}));
  (D.map&&D.map.bat||[]).forEach(o=>{xs.push(o[0]); ys.push(o[1]);});
  const R = Math.max(60, Math.max(...xs.map(Math.abs), ...ys.map(Math.abs))*1.12);
  const S = (W/2-18)/R;                              // pixels par mètre
  const PX = x => W/2 + x*S, PY = y => H/2 - y*S;    // nord vers le haut
  const ROLE = {0:'#3b82f6', 1:'#f59e0b'};
  let t = 0, playing = false, last = 0;

  function bg(){
    ctx.fillStyle = css.getPropertyValue('--ground'); ctx.fillRect(0,0,W,H);
    const M = D.map;
    if (M){
      ctx.fillStyle = css.getPropertyValue('--road');
      (M.route||[]).forEach(o=>rect(o, true));
      ctx.fillStyle = css.getPropertyValue('--bat');
      (M.bat||[]).forEach(o=>rect(o, false));
    }
    // échelle
    ctx.strokeStyle = css.getPropertyValue('--mut'); ctx.lineWidth=2; ctx.beginPath();
    ctx.moveTo(18,H-16); ctx.lineTo(18+50*S,H-16); ctx.stroke();
    ctx.fillStyle = css.getPropertyValue('--mut'); ctx.font='11px system-ui';
    ctx.fillText('50 m', 18, H-22);
  }
  function rect(o, thin){                            // [dx,dy,cap,larg,long] -> empreinte orientée
    const [x,y,dir,w,l] = o, a = -dir*Math.PI/180;
    const hw = Math.max(thin?1.2:1.0, w/2)*S, hl = Math.max(thin?1.2:1.0, l/2)*S;
    ctx.save(); ctx.translate(PX(x), PY(y)); ctx.rotate(a);
    ctx.fillRect(-hw, -hl, hw*2, hl*2); ctx.restore();
  }
  function draw(){
    bg();
    // objectif + rayon de sécurisation
    ctx.strokeStyle='#22c55e'; ctx.setLineDash([5,4]); ctx.lineWidth=1.5;
    ctx.beginPath(); ctx.arc(PX(0),PY(0),25*S,0,7); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle='#22c55e'; ctx.beginPath(); ctx.arc(PX(0),PY(0),4,0,7); ctx.fill();
    const f = D.frames[t]; if(!f) return;
    // défenseurs
    (f.east||[]).forEach(e=>{
      const x=e[0]-D.fob[0], y=e[1]-D.fob[1], alv = e[2]===undefined?1:e[2];
      ctx.beginPath(); ctx.arc(PX(x),PY(y),4,0,7);
      if(alv){ ctx.fillStyle='#ef4444'; ctx.fill(); } else { ctx.strokeStyle='#ef4444'; ctx.globalAlpha=.5; ctx.stroke(); ctx.globalAlpha=1; }
    });
    // traînées
    const TR = +trailSel.value;
    if (TR>0){
      const n = f.west.length;
      for(let i=0;i<n;i++){
        ctx.strokeStyle = ROLE[(f.west[i][3]||0)]; ctx.lineWidth=1.5; ctx.globalAlpha=.45; ctx.beginPath();
        let started=false;
        for(let k=Math.max(0,t-TR); k<=t; k++){
          const w = D.frames[k].west[i]; if(!w||!w[2]) continue;
          const x=w[0]-D.fob[0], y=w[1]-D.fob[1];
          if(!started){ ctx.moveTo(PX(x),PY(y)); started=true; } else ctx.lineTo(PX(x),PY(y));
        }
        ctx.stroke(); ctx.globalAlpha=1;
      }
    }
    // soldats
    f.west.forEach((w,i)=>{
      const x=w[0]-D.fob[0], y=w[1]-D.fob[1], alv=w[2], role=w[3]||0;
      const firing = (f.firew&&f.firew[i])?1:0;
      if(alv){
        if(firing){ ctx.strokeStyle='#fbbf24'; ctx.lineWidth=2; ctx.beginPath(); ctx.arc(PX(x),PY(y),8,0,7); ctx.stroke(); }
        ctx.fillStyle = ROLE[role]; ctx.beginPath(); ctx.arc(PX(x),PY(y),4.5,0,7); ctx.fill();
      } else {
        ctx.strokeStyle='#ef4444'; ctx.lineWidth=2; ctx.beginPath();
        ctx.moveTo(PX(x)-4,PY(y)-4); ctx.lineTo(PX(x)+4,PY(y)+4);
        ctx.moveTo(PX(x)-4,PY(y)+4); ctx.lineTo(PX(x)+4,PY(y)-4); ctx.stroke();
      }
    });
    // JOUEUR (toi) — violet, plus gros, avec halo : impossible à confondre avec les agents
    if (f.player){
      const px = f.player[0]-D.fob[0], py = f.player[1]-D.fob[1];
      ctx.strokeStyle='#a855f7'; ctx.lineWidth=2; ctx.globalAlpha=.55;
      ctx.beginPath(); ctx.arc(PX(px),PY(py),11,0,7); ctx.stroke(); ctx.globalAlpha=1;
      ctx.fillStyle='#a855f7'; ctx.beginPath(); ctx.arc(PX(px),PY(py),6,0,7); ctx.fill();
      ctx.fillStyle='#fff'; ctx.font='bold 8px system-ui'; ctx.textAlign='center';
      ctx.fillText('J', PX(px), PY(py)+3); ctx.textAlign='left';
    }
    const alive = f.west.filter(w=>w[2]).length;
    const inside = f.west.filter(w=>w[2] && Math.hypot(w[0]-D.fob[0],w[1]-D.fob[1])<25).length;
    lbl.textContent = 'pas '+f.t+'/'+(D.frames.length-1)+' · '+alive+' vivants · '+inside+' sur obj.';
    rng.value = t;
  }
  function loop(ts){
    if(!playing) return;
    if(ts-last > 420/(+spd.value)){ last=ts; t=(t+1)%D.frames.length; draw(); }
    requestAnimationFrame(loop);
  }
  btn.onclick = ()=>{ playing=!playing; btn.textContent = playing?'⏸ pause':'▶ lecture';
                      if(playing){ last=0; requestAnimationFrame(loop);} };
  rng.max = D.frames.length-1;
  rng.oninput = ()=>{ t = +rng.value; draw(); };
  trailSel.onchange = draw;
  new MutationObserver(draw).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
  draw();
}
"""


def block(path, d, mp, idx):
    m = d.get("metrics", {})
    took = "OUI (pas %s)" % m.get("took_tick") if m.get("took") else "non"
    payload = {"fob": d["fob"], "frames": d["frames"], "map": mp}
    return ('<div class="wrap" id="p%d"><h2 style="font-size:15px;margin:0 0 2px">%s</h2>'
            '<div class="sub">mode <b>%s</b> · objectif pris : <b>%s</b> · pertes %s/%s · plan : %s</div>'
            '<canvas></canvas>'
            '<div class="ctl"><button class="play">▶ lecture</button>'
            '<input class="rng" type="range" min="0" value="0" step="1">'
            '<span class="t">—</span>'
            '<select class="spd" title="vitesse"><option value="0.5">0,5×</option><option value="1" selected>1×</option>'
            '<option value="2">2×</option><option value="4">4×</option></select>'
            '<select class="trail" title="traînée"><option value="0">sans traînée</option>'
            '<option value="6">traînée courte</option><option value="999" selected>trajectoire complète</option></select></div>'
            '<div class="lg"><span class="dot" style="background:#3b82f6"></span>assaut/fixeur'
            '<span class="dot" style="background:#f59e0b"></span>débordeur'
            '<span class="dot" style="background:#ef4444"></span>défenseur'
            '<span class="dot" style="background:#a855f7"></span><b>toi (J)</b>'
            '<span class="dot" style="background:#fbbf24"></span>tire · ✕ = tombé</div>'
            '<script>mkPlayer(document.getElementById("p%d"), %s)</script></div>'
            % (idx, os.path.basename(path), d.get("mode", "?"), took,
               m.get("west_losses", "?"), m.get("nag", "?"),
               ("%d bâtiments" % len(mp["bat"])) if mp else "non baké (lance bake_map.py)",
               idx, json.dumps(payload, separators=(",", ":"))))


def find_map(d, mapdir):
    """cherche le plan baké le plus proche de l'objectif du run."""
    fx, fy = d["fob"]
    best, bestd = None, 1e9
    for p in glob.glob(os.path.join(mapdir, "map_*.json")):
        try:
            m = json.load(open(p))
        except Exception:
            continue
        dd = abs(m.get("cx", 0) - fx) + abs(m.get("cy", 0) - fy)
        if dd < bestd and dd < 500:
            best, bestd = m, dd
    return best


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--glob", default=None)
    ap.add_argument("--out", default="/home/younes/arma3-marl/leviathan/replay.html")
    args = ap.parse_args()
    D = "/home/younes/arma3-marl/leviathan"
    paths = list(args.files) + (sorted(glob.glob(os.path.join(D, args.glob))) if args.glob else [])
    if not paths:
        print("aucun fichier. ex: python replay_player.py --glob 'ab3_*.json'"); sys.exit(1)
    blocks = []
    for i, p in enumerate(paths):
        try:
            d = json.load(open(p))
            mp = find_map(d, D)
            blocks.append(block(p, d, mp, i))
            print("  %s  (plan: %s)" % (os.path.basename(p), "oui" if mp else "NON baké"))
        except Exception as e:
            print("  ignoré %s (%s)" % (p, e))
    doc = ("<!doctype html><meta charset=utf-8><title>HARMATTAN — rejeu vue de dessus</title>"
           "<style>%s</style><script>%s</script>"
           "<h1>HARMATTAN — rejeu vue de dessus</h1>"
           "<div class=sub>Lecture animée des runs, sur le plan réel de la carte.</div>%s"
           % (CSS, JS, "".join(blocks)))
    open(args.out, "w").write(doc)
    print("\n-> %s  (%d run(s), %d Ko)" % (args.out, len(blocks), len(doc) // 1024))
