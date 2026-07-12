#!/usr/bin/env python3
"""map_altis.py — CARTE DU DISPOSITIF d'occupation.
Lit staff/occupation_altis.json -> ecrit staff/occupation_altis.html (carte tactique autonome).
Reutilisable : relancer apres chaque laydown."""
import json, math, os
ROOT = "/home/younes/arma3-marl"
SRC = os.path.join(ROOT, "staff", "occupation_altis.json")
OUT = os.path.join(ROOT, "staff", "occupation_altis.html")
ISLAND = 30720.0
S = 880.0; M = 60.0                      # aire carte + marge
SEC_COL = {"NE": "#e0a93b", "NO": "#3bb6e0", "SE": "#b06be0", "SO": "#5fd07a"}

d = json.load(open(SRC))
secs = d["sectors"]
els = [{"x": e["pos"][0], "y": e["pos"][1], "n": e["size"], "name": e.get("name",""),
        "cat": e.get("cat",""), "sec": e["sector"], "hmg": e.get("hmg",0), "type": e["type"]}
       for e in d["elements"]]

def sx(x): return M + x / ISLAND * S
def sy(y): return M + (ISLAND - y) / ISLAND * S      # flip nord-haut

# stats par secteur
from collections import Counter
cu = Counter(); ce = Counter()
for e in els: cu[e["sec"]] += e["n"]; ce[e["sec"]] += 1

svg = ['<svg viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;background:#0d1117;border-radius:10px">']
# cadre + grille (10 km)
svg.append(f'<rect x="{M}" y="{M}" width="{S}" height="{S}" fill="#0a1f1a" stroke="#243b36" stroke-width="1"/>')
for g in range(0, int(ISLAND)+1, 5000):
    gx = sx(g); gy = sy(g)
    svg.append(f'<line x1="{gx:.0f}" y1="{M}" x2="{gx:.0f}" y2="{M+S}" stroke="#16302a" stroke-width="0.6"/>')
    svg.append(f'<line x1="{M}" y1="{gy:.0f}" x2="{M+S}" y2="{gy:.0f}" stroke="#16302a" stroke-width="0.6"/>')
    svg.append(f'<text x="{gx:.0f}" y="{M-6}" fill="#3a5a52" font-size="9" text-anchor="middle">{g//1000}km</text>')
# limites de secteur (croix au centre)
cx = sx(d["center"][0] if "center" in d else 13860); 
center = d.get("center",[13860,13860]); cxx=sx(center[0]); cyy=sy(center[1])
svg.append(f'<line x1="{cxx:.0f}" y1="{M}" x2="{cxx:.0f}" y2="{M+S}" stroke="#2e4d45" stroke-width="1.2" stroke-dasharray="6 5"/>')
svg.append(f'<line x1="{M}" y1="{cyy:.0f}" x2="{M+S}" y2="{cyy:.0f}" stroke="#2e4d45" stroke-width="1.2" stroke-dasharray="6 5"/>')

def order(e):  # garnisons d'abord (dessous), points de commandement au-dessus
    return {"garrison":0,"coastal":1,"checkpoint":1,"op":1,"patrol":1,"convoy":1,"comms_relay":1,
            "gbad":2,"qrf":3,"fob":4,"theater_hq":5}.get(e["type"],1)
for e in sorted(els, key=order):
    x, y, n, t, sec = sx(e["x"]), sy(e["y"]), e["n"], e["type"], e["sec"]
    c = SEC_COL.get(sec, "#888")
    if t == "garrison":
        r = 2.4 + math.sqrt(n) * 0.9
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}" fill-opacity="0.55" stroke="{c}" stroke-width="0.8"/>')
        if e.get("cat") == "ville":
            svg.append(f'<text x="{x:.0f}" y="{y-r-3:.0f}" fill="#e8eef0" font-size="9.5" text-anchor="middle" font-weight="600">{e["name"]}</text>')
    elif t == "theater_hq":
        svg.append(f'<path d="M{x:.0f},{y-9:.0f} L{x+9:.0f},{y:.0f} L{x:.0f},{y+9:.0f} L{x-9:.0f},{y:.0f} Z" fill="#ff5b5b" stroke="#fff" stroke-width="1.4"/>')
        svg.append(f'<text x="{x:.0f}" y="{y+22:.0f}" fill="#ff8f8f" font-size="11" text-anchor="middle" font-weight="700">QG THEATRE</text>')
    elif t == "fob":
        svg.append(f'<rect x="{x-7:.0f}" y="{y-7:.0f}" width="14" height="14" fill="none" stroke="#fff" stroke-width="1.6"/>')
        svg.append(f'<text x="{x+10:.0f}" y="{y-8:.0f}" fill="#cfe" font-size="9.5" font-weight="700">{e["name"]}</text>')
    elif t == "qrf":
        svg.append(f'<path d="M{x:.0f},{y-8:.0f} L{x+7:.0f},{y+6:.0f} L{x-7:.0f},{y+6:.0f} Z" fill="#ffd24a" stroke="#7a5a00" stroke-width="0.8"/>')
    elif t == "gbad":
        svg.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="none" stroke="#ff5b5b" stroke-width="1.3"/><circle cx="{x:.0f}" cy="{y:.0f}" r="2" fill="#ff5b5b"/>')
    elif t == "checkpoint":
        svg.append(f'<path d="M{x:.0f},{y-4:.0f} L{x+4:.0f},{y:.0f} L{x:.0f},{y+4:.0f} L{x-4:.0f},{y:.0f} Z" fill="#cfd8dc" stroke="#5a6a6a" stroke-width="0.6"/>')
    elif t == "op":
        svg.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3" fill="none" stroke="#9fb4ad" stroke-width="1"/>')
    elif t == "coastal":
        svg.append(f'<rect x="{x-3:.0f}" y="{y-3:.0f}" width="6" height="6" fill="#4aa3ff" stroke="#1a3a5a" stroke-width="0.6"/>')
    elif t == "patrol":
        svg.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="2.6" fill="#9fe0b0"/>')
    elif t == "comms_relay":
        svg.append(f'<path d="M{x:.0f},{y-5:.0f} L{x:.0f},{y+5:.0f} M{x-5:.0f},{y:.0f} L{x+5:.0f},{y:.0f}" stroke="#e0c050" stroke-width="1.4"/>')
    elif t == "convoy":
        svg.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3" fill="#c08a4a"/>')
svg.append('</svg>')
svg = "\n".join(svg)

rows = "".join(
    f'<tr><td><span class="dot" style="background:{SEC_COL[s["name"]]}"></span>{s["name"]}</td>'
    f'<td>{s["n_localites"]}</td><td>{ce[s["name"]]}</td><td><b>{cu[s["name"]]}</b></td>'
    f'<td>{["QG" if s["name"]=="NE" else "FOB"][0]} @ {s["hq"][0]//1000},{s["hq"][1]//1000}km</td></tr>'
    for s in secs)

html = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>HARMATTAN — Dispositif d'occupation Altis (REDFOR/CSAT)</title>
<style>
 body{{margin:0;background:#0d1117;color:#c9d1d9;font-family:-apple-system,Segoe UI,Roboto,sans-serif;padding:20px}}
 h1{{font-size:19px;margin:0 0 2px;color:#e8eef0}} .sub{{color:#7d8a93;font-size:13px;margin-bottom:14px}}
 .wrap{{display:flex;gap:22px;flex-wrap:wrap;align-items:flex-start}}
 .map{{flex:1 1 560px;min-width:380px}}
 .side{{flex:0 1 330px;min-width:280px}}
 .card{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px 16px;margin-bottom:14px}}
 .card h2{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#7d8a93;margin:0 0 10px}}
 .big{{font-size:30px;font-weight:800;color:#e8eef0;line-height:1}} .big small{{font-size:13px;color:#7d8a93;font-weight:500}}
 table{{width:100%;border-collapse:collapse;font-size:13px}} td,th{{padding:5px 6px;text-align:left;border-bottom:1px solid #21262d}}
 th{{color:#7d8a93;font-weight:600;font-size:11px;text-transform:uppercase}}
 .dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px;vertical-align:middle}}
 .leg{{display:flex;flex-direction:column;gap:6px;font-size:12px}} .leg div{{display:flex;align-items:center;gap:8px}}
 .lk{{width:18px;text-align:center;flex:0 0 18px}}
 .ok{{color:#5fd07a}} .warn{{color:#e0a93b}}
</style></head><body>
<h1>HARMATTAN — Dispositif d'occupation · {d['world']} (REDFOR / CSAT)</h1>
<div class="sub">Adversaire généré · cible {d['target']} hommes · seed {d.get('seed',0)} · nord en haut · grille 5 km</div>
<div class="wrap">
 <div class="map">{svg}</div>
 <div class="side">
  <div class="card"><h2>Masse</h2>
   <div class="big">{d['total_units']:,}<small> hommes</small></div>
   <div style="margin-top:6px;color:#7d8a93;font-size:13px">{d['n_elements']} éléments · 4 secteurs · 111 localités garnisonnées</div></div>
  <div class="card"><h2>Secteurs</h2>
   <table><tr><th>Secteur</th><th>Loc.</th><th>Élém.</th><th>Hommes</th><th>Cmdt</th></tr>{rows}</table></div>
  <div class="card"><h2>Symboles</h2>
   <div class="leg">
    <div><span class="lk">◆</span> QG de théâtre (NE)</div>
    <div><span class="lk">▢</span> FOB de secteur (×4)</div>
    <div><span class="lk" style="color:#ffd24a">▲</span> QRF mobile (réserve)</div>
    <div><span class="lk" style="color:#ff5b5b">◎</span> DCA / GBAD</div>
    <div><span class="lk">●</span> Garnison (taille ∝ effectif)</div>
    <div><span class="lk">◇</span> Checkpoint routier</div>
    <div><span class="lk">○</span> Poste d'observation</div>
    <div><span class="lk" style="color:#4aa3ff">▪</span> Défense côtière</div>
    <div><span class="lk" style="color:#e0c050">+</span> Relais radio</div>
   </div></div>
  <div class="card"><h2>Runtime validé (sur Arma réel)</h2>
   <div style="font-size:13px;line-height:1.55">
    <div class="ok">✔ Dynamic Simulation</div> 49 vs 13,6 FPS serveur (×3,6)<br>
    <div class="warn">▸ budget actif</div> ~700–1000 hommes éveillés/serveur<br>
    <div class="warn">▸ effondrement</div> ~1200 actifs · 2000 = vivier gelé<br>
    <div class="ok">✔ Moteur d'alerte</div> contact→détection <b>t+32 s</b>, alerte 0→3/3, QRF dispatchée + rapprochement
   </div></div>
 </div>
</div>
<div style="color:#3a4a52;font-size:11px;margin-top:10px">map_altis.py · lit occupation_altis.json · projet HARMATTAN</div>
</body></html>"""
open(OUT, "w", encoding="utf-8").write(html)
print("ecrit", OUT, len(html), "octets")
