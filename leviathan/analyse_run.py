#!/usr/bin/env python3
"""analyse_run.py — SCHÉMAS D'ANALYSE d'un run Arma : voir la manœuvre au lieu de la lire.

Entrée  : les JSON produits par envelop_arma.py (frames tick par tick : positions, vivants, rôle, tirs).
Sortie  : un HTML autonome avec 3 schémas + le bilan chiffré.

  1) CARTE DE MOUVEMENT  — la trajectoire de chaque soldat (couleur = rôle), l'objectif, les défenseurs,
     une croix là où chacun est tombé. On VOIT si l'escouade a contourné ou foncé.
  2) PROFIL D'APPROCHE   — distance à l'objectif au fil du temps, une courbe par soldat.
     Une courbe qui descend = il avance. Une courbe plate = il est cloué.
  3) COURBE DE FORCE     — vivants et hommes dans l'objectif, tick par tick.

Usage : python analyse_run.py leviathan/ab3_8_envelop_1.json [autre.json ...]
        python analyse_run.py --glob 'ab3_*.json'
"""
import sys, os, json, glob, math, argparse

ROLE_COL = {0: "#3b82f6", 1: "#f59e0b"}      # 0 = fixeur/assaut (bleu), 1 = débordeur (orange)
ROLE_NAME = {0: "assaut/fixeur", 1: "débordeur"}


def load(path):
    d = json.load(open(path))
    return d


def analyse(d):
    """Extrait les séries par soldat : trajectoire, distance à l'objectif, tick de mort."""
    fx, fy = d["fob"]
    frames = d["frames"]
    n = max(len(f["west"]) for f in frames)
    tracks = [{"xy": [], "dist": [], "role": 0, "death": None, "fired": 0} for _ in range(n)]
    force = []          # (t, vivants, dans_objectif)
    for f in frames:
        alive_n = 0; inside = 0
        for i, w in enumerate(f["west"]):
            x, y, alv = w[0], w[1], int(w[2])
            role = w[3] if len(w) > 3 else 0
            tr = tracks[i]
            tr["role"] = role
            dist = math.hypot(x - fx, y - fy)
            if alv:
                tr["xy"].append((x, y)); tr["dist"].append((f["t"], dist))
                alive_n += 1
                if dist < 25: inside += 1
            elif tr["death"] is None and tr["xy"]:
                tr["death"] = (f["t"], tr["xy"][-1][0], tr["xy"][-1][1], dist)
        for i, fw in enumerate(f.get("firew", [])):
            if i < n and fw: tracks[i]["fired"] += 1
        force.append((f["t"], alive_n, inside))
    east = frames[-1].get("east", []) if frames else []
    return dict(fx=fx, fy=fy, tracks=tracks, force=force, east=east,
                metrics=d.get("metrics", {}), mode=d.get("mode", "?"))


def svg_map(a, W=560, H=560, pad=28):
    """Carte top-down : trajectoires + objectif + défenseurs + morts."""
    fx, fy = a["fx"], a["fy"]
    pts = [p for t in a["tracks"] for p in t["xy"]] + [(fx, fy)] + [(e[0], e[1]) for e in a["east"]]
    if not pts: return "<p>pas de données</p>"
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
    span = max(x1 - x0, y1 - y0, 60.0) * 1.08
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    def P(x, y):    # monde -> écran (y inversé : le nord vers le haut)
        sx = pad + (x - (cx - span / 2)) / span * (W - 2 * pad)
        sy = H - pad - (y - (cy - span / 2)) / span * (H - 2 * pad)
        return sx, sy
    m_per_px = span / (W - 2 * pad)
    o = ['<svg viewBox="0 0 %d %d" width="100%%" style="max-width:%dpx">' % (W, H, W)]
    o.append('<rect width="%d" height="%d" fill="var(--bg2)"/>' % (W, H))
    # rayon de sécurisation (25 m) + objectif
    ox, oy = P(fx, fy); r25 = 25.0 / m_per_px
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#22c55e" stroke-dasharray="4 3" opacity=".9"/>' % (ox, oy, r25))
    o.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#22c55e"/>' % (ox, oy))
    o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#22c55e">objectif</text>' % (ox + 7, oy - 7))
    # défenseurs
    for e in a["east"]:
        ex, ey = P(e[0], e[1]); alv = int(e[2]) if len(e) > 2 else 1
        if alv: o.append('<circle cx="%.1f" cy="%.1f" r="3.5" fill="#ef4444"/>' % (ex, ey))
        else:   o.append('<circle cx="%.1f" cy="%.1f" r="3.5" fill="none" stroke="#ef4444" opacity=".5"/>' % (ex, ey))
    # trajectoires
    for t in a["tracks"]:
        if len(t["xy"]) < 2: continue
        col = ROLE_COL.get(t["role"], "#3b82f6")
        pth = " ".join("%.1f,%.1f" % P(x, y) for x, y in t["xy"])
        o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.6" opacity=".75"/>' % (pth, col))
        sx, sy = P(*t["xy"][0])
        o.append('<circle cx="%.1f" cy="%.1f" r="2.4" fill="%s" opacity=".85"/>' % (sx, sy, col))
        if t["death"]:
            dx, dy = P(t["death"][1], t["death"][2])
            o.append('<g stroke="#ef4444" stroke-width="1.8"><line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                     '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/></g>'
                     % (dx - 4, dy - 4, dx + 4, dy + 4, dx - 4, dy + 4, dx + 4, dy - 4))
        else:
            ex, ey = P(*t["xy"][-1])
            o.append('<circle cx="%.1f" cy="%.1f" r="3.2" fill="none" stroke="%s" stroke-width="1.8"/>' % (ex, ey, col))
    # échelle
    bar = 50.0 / m_per_px
    o.append('<line x1="%d" y1="%d" x2="%.1f" y2="%d" stroke="var(--fg)" stroke-width="2"/>' % (pad, H - 12, pad + bar, H - 12))
    o.append('<text x="%d" y="%d" font-size="10" fill="var(--fg)">50 m</text>' % (pad, H - 16))
    o.append("</svg>")
    return "".join(o)


def svg_profile(a, W=560, H=240, pad=34):
    """Distance à l'objectif au fil du temps, une courbe par soldat. Descend = avance. Plate = cloué."""
    tracks = [t for t in a["tracks"] if t["dist"]]
    if not tracks: return "<p>pas de données</p>"
    tmax = max(p[0] for t in tracks for p in t["dist"]) or 1
    dmax = max(p[1] for t in tracks for p in t["dist"]) or 1
    def P(t, d):
        return pad + t / tmax * (W - 2 * pad), pad + (d / dmax) * (H - 2 * pad - 10)
    o = ['<svg viewBox="0 0 %d %d" width="100%%" style="max-width:%dpx">' % (W, H, W)]
    o.append('<rect width="%d" height="%d" fill="var(--bg2)"/>' % (W, H))
    # ligne des 25 m (sécurisation)
    _, y25 = P(0, 25);
    o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#22c55e" stroke-dasharray="4 3"/>' % (pad, y25, W - pad, y25))
    o.append('<text x="%d" y="%.1f" font-size="10" fill="#22c55e">25 m — objectif sécurisé</text>' % (pad + 4, y25 - 4))
    for t in tracks:
        col = ROLE_COL.get(t["role"], "#3b82f6")
        pth = " ".join("%.1f,%.1f" % P(tt, dd) for tt, dd in t["dist"])
        o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.4" opacity=".7"/>' % (pth, col))
        if t["death"]:
            dx, dy = P(t["death"][0], t["death"][3])
            o.append('<circle cx="%.1f" cy="%.1f" r="3" fill="#ef4444"/>' % (dx, dy))
    o.append('<text x="%d" y="%d" font-size="10" fill="var(--fg)">temps (décisions) →</text>' % (pad, H - 8))
    o.append('<text x="6" y="%d" font-size="10" fill="var(--fg)" transform="rotate(-90 12,%d)">distance (m)</text>' % (H // 2, H // 2))
    o.append("</svg>")
    return "".join(o)


def svg_force(a, W=560, H=170, pad=34):
    """Vivants + hommes DANS l'objectif, tick par tick."""
    F = a["force"]
    if not F: return "<p>pas de données</p>"
    tmax = max(f[0] for f in F) or 1
    vmax = max(max(f[1] for f in F), 1)
    def P(t, v):
        return pad + t / tmax * (W - 2 * pad), H - pad - v / vmax * (H - 2 * pad)
    o = ['<svg viewBox="0 0 %d %d" width="100%%" style="max-width:%dpx">' % (W, H, W)]
    o.append('<rect width="%d" height="%d" fill="var(--bg2)"/>' % (W, H))
    for key, col, lab in ((1, "#3b82f6", "vivants"), (2, "#22c55e", "dans l'objectif")):
        pth = " ".join("%.1f,%.1f" % P(f[0], f[key]) for f in F)
        o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>' % (pth, col))
    o.append('<text x="%d" y="%d" font-size="11" fill="#3b82f6">— vivants</text>' % (W - 150, 18))
    o.append('<text x="%d" y="%d" font-size="11" fill="#22c55e">— dans l\'objectif</text>' % (W - 150, 32))
    o.append("</svg>")
    return "".join(o)


def bilan(a):
    """Chiffres dérivés : qui a avancé, qui a stagné, où on meurt."""
    rows = []
    for i, t in enumerate(a["tracks"]):
        if not t["dist"]: continue
        d0 = t["dist"][0][1]; dmin = min(p[1] for p in t["dist"])
        parcouru = sum(math.hypot(t["xy"][k + 1][0] - t["xy"][k][0], t["xy"][k + 1][1] - t["xy"][k][1])
                       for k in range(len(t["xy"]) - 1))
        rows.append(dict(i=i, role=ROLE_NAME.get(t["role"], "?"), col=ROLE_COL.get(t["role"], "#3b82f6"),
                         gain=d0 - dmin, dmin=dmin, parcouru=parcouru, fired=t["fired"],
                         mort=("tick %d à %.0f m" % (t["death"][0], t["death"][3])) if t["death"] else "—"))
    rows.sort(key=lambda r: -r["gain"])
    return rows


CSS = """:root{--bg:#fff;--bg2:#f6f7f9;--fg:#111;--mut:#666;--line:#e3e6ea}
@media(prefers-color-scheme:dark){:root{--bg:#0f1115;--bg2:#171a20;--fg:#e8eaed;--mut:#9aa0a6;--line:#2a2f38}}
:root[data-theme=dark]{--bg:#0f1115;--bg2:#171a20;--fg:#e8eaed;--mut:#9aa0a6;--line:#2a2f38}
:root[data-theme=light]{--bg:#fff;--bg2:#f6f7f9;--fg:#111;--mut:#666;--line:#e3e6ea}
body{background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,sans-serif;margin:0;padding:22px}
h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:22px 0 6px}
.sub{color:var(--mut);font-size:13px;margin-bottom:18px}
.run{border:1px solid var(--line);border-radius:10px;padding:16px;margin:0 0 22px;background:var(--bg)}
.grid{display:flex;flex-wrap:wrap;gap:18px}.grid>div{flex:1 1 380px;min-width:0}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:6px}
th,td{text-align:left;padding:4px 8px;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-weight:600}
.kpi{display:flex;gap:20px;flex-wrap:wrap;margin:8px 0 4px}
.kpi div{background:var(--bg2);border-radius:8px;padding:8px 12px}
.kpi b{display:block;font-size:18px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}
.note{color:var(--mut);font-size:12px;margin-top:6px}
.scroll{overflow-x:auto}"""


def html_run(path, d):
    a = analyse(d)
    m = a["metrics"]
    rows = bilan(a)
    took = m.get("took"); nag = m.get("nag", "?")
    kpis = [("mode", a["mode"]), ("objectif pris", "OUI (tick %s)" % m.get("took_tick") if took else "non"),
            ("pertes", "%s/%s" % (m.get("west_losses", "?"), nag)),
            ("défenseurs neutralisés", "%s/%s" % (m.get("east_neutralized", "?"), m.get("east_start", "?"))),
            ("approche max", "%s m" % m.get("min_fob_dist", "?"))]
    o = ['<div class="run"><h2>%s</h2>' % os.path.basename(path)]
    o.append('<div class="kpi">' + "".join('<div>%s<b>%s</b></div>' % (k, v) for k, v in kpis) + "</div>")
    o.append('<div class="grid"><div><h2>Carte de mouvement</h2>' + svg_map(a) +
             '<div class="note"><span class="dot" style="background:#3b82f6"></span>assaut/fixeur '
             '<span class="dot" style="background:#f59e0b"></span>débordeur '
             '<span class="dot" style="background:#ef4444"></span>défenseur — ✕ = tombé, ○ = survivant</div></div>')
    o.append('<div><h2>Profil d\'approche</h2>' + svg_profile(a) +
             '<div class="note">Une courbe qui descend = il avance. Plate = cloué. Point rouge = mort.</div>'
             '<h2>Courbe de force</h2>' + svg_force(a) + "</div></div>")
    o.append('<h2>Par soldat</h2><div class="scroll"><table><tr><th>#</th><th>rôle</th><th>terrain gagné</th>'
             '<th>approche max</th><th>distance parcourue</th><th>tirs</th><th>issue</th></tr>')
    for r in rows:
        o.append('<tr><td>%d</td><td><span class="dot" style="background:%s"></span>%s</td>'
                 '<td>%.0f m</td><td>%.0f m</td><td>%.0f m</td><td>%d</td><td>%s</td></tr>'
                 % (r["i"], r["col"], r["role"], r["gain"], r["dmin"], r["parcouru"], r["fired"], r["mort"]))
    o.append("</table></div></div>")
    return "".join(o)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--glob", default=None)
    ap.add_argument("--out", default="/home/younes/arma3-marl/leviathan/analyse_runs.html")
    args = ap.parse_args()
    paths = list(args.files)
    if args.glob:
        paths += sorted(glob.glob(os.path.join("/home/younes/arma3-marl/leviathan", args.glob)))
    if not paths:
        print("aucun fichier. ex: python analyse_run.py --glob 'ab3_*.json'"); sys.exit(1)
    blocks = []
    for p in paths:
        try:
            blocks.append(html_run(p, load(p)))
            print("  lu : %s" % os.path.basename(p))
        except Exception as e:
            print("  ignoré %s (%s)" % (p, e))
    doc = ("<!doctype html><meta charset=utf-8><title>HARMATTAN — analyse de runs</title>"
           "<style>%s</style><h1>HARMATTAN — analyse de runs</h1>"
           "<div class=sub>Schémas de mouvement générés depuis les enregistrements tick par tick.</div>%s"
           % (CSS, "".join(blocks)))
    open(args.out, "w").write(doc)
    print("\n-> %s  (%d run(s), %d Ko)" % (args.out, len(blocks), len(doc) // 1024))
