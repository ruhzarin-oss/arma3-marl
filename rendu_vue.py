#!/usr/bin/env python3
"""Rend VISIBLE ce que la sonde a mesure : le relief de chaque lieu, les objets autour,
et la trace de l homme dessus — de dessus, et de PROFIL.

Le profil est la figure qui tranche : hauteur au-dessus du terrain en fonction de la
distance parcourue. Un homme qui marche y reste colle a zero. Un homme qui vole monte.
Aucune chaine de caracteres n intervient.
"""
import re, sys, ast, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/harmattan-sandbox/logs/serverVUE.out"
DST = sys.argv[2] if len(sys.argv) > 2 else "/mnt/data/preuves/2026-08-19_controle_visuel"
os.makedirs(DST, exist_ok=True)

def arr(s):
    # Les tableaux SQF s impriment presque comme du Python, a trois details pres :
    #  - `true` / `false` en minuscules ;
    #  - les guillemets sont DOUBLES dans le journal (une chaine y apparait doublee) ;
    #  - PIEGE : `typeOf` rend la chaine VIDE pour les objets de terrain, ce qui donne
    #    quatre guillemets d affilee — que literal_eval prend pour un triple guillemet.
    # Rendre les guillemets simples regle les trois d un coup.
    s = s.replace(chr(34) * 2, chr(34))
    s = s.replace("true", "True").replace("false", "False")
    return ast.literal_eval(s)

relief, objets, gestes, ticks, poses = {}, {}, {}, {}, {}
for L in open(SRC, errors="ignore"):
    if "HMT|VUE|" not in L: continue
    L = L[L.index("HMT|VUE|"):].rstrip().rstrip('"')
    # ⚠️ UNE LIGNE PAR RANGEE depuis la 1.1.0 : le journal coupait a 1031 caracteres.
    m = re.match(r'HMT\|VUE\|RELIEF\|etq\|([^|]+)\|x\|(\d+)\|y\|(\d+)\|pas\|(\d+)\|n\|(\d+)\|i\|(\d+)\|r\|(.*)', L)
    if m:
        e = m.group(1)
        d = relief.setdefault(e, (int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), {}))
        d[4][int(m.group(6))] = arr(m.group(7)); continue
    m = re.match(r'HMT\|VUE\|OBJETS\|etq\|([^|]+)\|n\|(\d+)\|o\|(.*)', L)
    if m: objets[m.group(1)] = (int(m.group(2)), arr(m.group(3))); continue
    m = re.match(r'HMT\|VUE\|GESTE\|etq\|([^|]+)\|mode\|([^|]+)\|m\|([\d.-]+)\|n\|(\d+)\|part_sol\|(\d+)\|serie_sol_max\|(\d+)\|z_max\|([\d.-]+)\|v_med_fin\|([\d.-]+)\|fps\|(\d+)', L)
    if m: gestes[(m.group(1), m.group(2))] = dict(m=float(m.group(3)), n=int(m.group(4)),
              part_sol=int(m.group(5)), serie=int(m.group(6)), zmax=float(m.group(7)), vmed=float(m.group(8)), fps=int(m.group(9))); continue
    m = re.match(r'HMT\|VUE\|TICKS\|etq\|([^|]+)\|mode\|([^|]+)\|k\|(\d+)\|tr\|(.*)', L)
    if m:
        ticks.setdefault((m.group(1), m.group(2)), {})[int(m.group(3))] = arr(m.group(4)); continue
    m = re.match(r'HMT\|VUE\|POSE\|etq\|([^|]+)\|mode\|([^|]+)\|z\|([\d.-]+)\|sol\|(\w+)\|anim\|(\w+)', L)
    if m: poses[(m.group(1), m.group(2))] = (float(m.group(3)), m.group(4), m.group(5))

ticks = {k: [t for _, tr in sorted(v.items()) for t in tr] for k, v in ticks.items()}
relief = {e: (x, y, pas, n, [h for _, r in sorted(g.items()) for h in r]) for e, (x, y, pas, n, g) in relief.items()}
print("releves : %d reliefs, %d listes d objets, %d gestes, %d traces" % (len(relief), len(objets), len(gestes), len(ticks)))
if not gestes: sys.exit("aucun geste — rien a rendre")

# ── LE TABLEAU, AVANT TOUTE IMAGE ────────────────────────────────────────────
print("\n%-14s %-9s %7s %9s %9s %8s %8s %7s %5s" % ("lieu", "mode", "metres", "part_sol", "serie_sol", "z_max", "z_pose", "v_med", "fps"))
for (e, md), g in sorted(gestes.items()):
    zp = poses.get((e, md), (float("nan"),))[0]
    print("%-14s %-9s %7.1f %8d %% %9d %8.2f %8.2f %7.1f %5d"
          % (e, md, g["m"], g["part_sol"], g["serie"], g["zmax"], zp, g["vmed"], g["fps"]))

# ── LES IMAGES ───────────────────────────────────────────────────────────────
# DEUX PLANCHES CARREES, pas une bande de 16 : une figure illisible ne prouve rien.
import math
cles = [k for k in sorted(ticks) if k in gestes]

def grille(n):
    c = int(math.ceil(math.sqrt(n))); r = int(math.ceil(n / c)); return r, c

# ── PLANCHE 1 · LES PROFILS — la figure qui tranche ──────────────────────────
r, c = grille(len(cles))
fig, axes = plt.subplots(r, c, figsize=(3.3 * c, 2.5 * r), squeeze=False)
for j, (e, md) in enumerate(cles):
    ax = axes[j // c][j % c]
    tr = ticks[(e, md)]; g = gestes[(e, md)]
    dx = [t[0] for t in tr]; dy = [t[1] for t in tr]
    z = [t[2] for t in tr]; sol = [t[3] for t in tr]
    d = [(a*a + b*b) ** 0.5 for a, b in zip(dx, dy)]
    ax.fill_between(d, 0, z, color="red", alpha=0.22)
    ax.plot(d, z, "-", color="k", lw=1.1)
    ax.scatter(d, z, c=["deepskyblue" if s_ else "red" for s_ in sol], s=13, zorder=5)
    ax.axhline(0, color="saddlebrown", lw=2.2)
    ax.axvline(23, color="darkgreen", ls="--", lw=1.4)
    ax.set_xlim(0, 30); ax.set_ylim(-0.4, 8.5)
    ax.set_title("%s · %s\n%.1f m — %d %% au sol — z max %.2f m"
                 % (e, md, g["m"], g["part_sol"], g["zmax"]), fontsize=8)
    ax.tick_params(labelsize=6)
    if j // c == r - 1: ax.set_xlabel("distance parcourue (m)", fontsize=7)
    if j % c == 0: ax.set_ylabel("hauteur / terrain (m)", fontsize=7)
for j in range(len(cles), r * c): axes[j // c][j % c].axis("off")
fig.suptitle("PROFIL DU GESTE — bleu = touche le sol, rouge = en l air ; "
             "trait vert = seuil du placeur (23 m)", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.955])
o1 = os.path.join(DST, "profils.png"); fig.savefig(o1, dpi=120); plt.close(fig)

# ── PLANCHE 2 · LES LIEUX VUS DE DESSUS ──────────────────────────────────────
lieux = [k for k in cles if k[0] in relief]
r, c = grille(len(lieux))
fig, axes = plt.subplots(r, c, figsize=(3.1 * c, 3.1 * r), squeeze=False)
for j, (e, md) in enumerate(lieux):
    ax = axes[j // c][j % c]
    tr = ticks[(e, md)]; g = gestes[(e, md)]
    dx = [t[0] for t in tr]; dy = [t[1] for t in tr]; sol = [t[3] for t in tr]
    px, py, pas, nn, gr = relief[e]
    G = np.array(gr).reshape(nn, nn).T
    ext = [-pas*(nn//2), pas*(nn//2), -pas*(nn//2), pas*(nn//2)]
    ax.imshow(G, origin="lower", extent=ext, cmap="terrain", aspect="equal")
    xs = np.linspace(ext[0], ext[1], nn); ys = np.linspace(ext[2], ext[3], nn)
    cs = ax.contour(xs, ys, G, levels=9, colors="k", linewidths=0.4, alpha=0.55)
    ax.clabel(cs, inline=True, fontsize=4.5, fmt="%.0f")
    if e in objets:
        for t, ox, oy, oz in objets[e][1]:
            ax.plot(ox, oy, "s", ms=3.5, color="crimson", alpha=0.85)
    ax.plot(dx, dy, "-", color="white", lw=2.6)
    ax.scatter(dx, dy, c=["deepskyblue" if s_ else "red" for s_ in sol], s=11, zorder=5)
    ax.plot(0, 0, "*", color="yellow", ms=15, mec="k", zorder=6)
    ax.set_xlim(-30, 30); ax.set_ylim(-30, 30); ax.tick_params(labelsize=6)
    pente = (G.max() - G.min())
    ax.set_title("%s  (%d, %d)\n%.1f m — %d %% au sol — denivele %.0f m"
                 % (e, px, py, g["m"], g["part_sol"], pente), fontsize=8)
for j in range(len(lieux), r * c): axes[j // c][j % c].axis("off")
fig.suptitle("LES LIEUX VUS DE DESSUS — relief sur +/- 30 m (courbes de niveau en m), "
             "carres rouges = objets, etoile = depart, trace de l homme", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.955])
o2 = os.path.join(DST, "lieux.png"); fig.savefig(o2, dpi=120); plt.close(fig)
print("\nimages : %s\n         %s" % (o1, o2))

# ── ET LE DENIVELE, QUI EST LA CAUSE CANDIDATE ───────────────────────────────
print("\n%-12s %8s %10s %9s" % ("lieu", "metres", "part_sol", "denivele"))
for (e, md) in lieux:
    px, py, pas, nn, gr = relief[e]
    G = np.array(gr); g = gestes[(e, md)]
    print("%-12s %8.1f %8d %% %8.1f m" % (e, g["m"], g["part_sol"], G.max() - G.min()))
