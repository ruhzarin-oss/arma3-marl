#!/usr/bin/env python3
"""bake_los.py — LA VUE EXACTE : on demande la géométrie RÉELLE à Arma, au lieu de la reconstruire.

Pourquoi : reconstruire les bâtiments depuis leur boîte englobante donne des blocs pleins (une enceinte
avec un portail devient un mur continu) et ignore le relief. Résultat mesuré le 25/07 : 8 % de visibilité
annoncée là où le jeu produit du vrai combat -> deux mesures de coordination inexploitables, et un agent
qui ne peut pas choisir un itinéraire discret.

Ce que fait ce script : pour chaque case d'une grille, il envoie un RAYON VERTICAL dans le moteur et
récupère (a) l'altitude du sol et (b) la hauteur du premier obstacle réel. On obtient un relief + un
« toit » exacts — portails, arcades et pentes compris.

Sortie : los_<monde>_<x>_<y>.npz (sol, obstacle) relu par intentions.Terrain.

Usage : python bake_los.py --theatre altis [--cell 4] [--radius 320]
"""
import sys, time, argparse
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

ap = argparse.ArgumentParser()
ap.add_argument("--cell", type=float, default=4.0)
ap.add_argument("--radius", type=float, default=320.0)
ap.add_argument("--chunk", type=int, default=260)
ap.add_argument("--fob", default=None)
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
fx, fy = [int(v) for v in a.fob.split(",")] if a.fob else TH.FOB
b = NativeBridge(port=TH.PORT)

r = b.query('(format ["W %1", worldName]) call HMT_EMIT;', r"W (\S+)", want=1, timeout=12)
world = r[-1].group(1) if r else "?"
N = int(2 * a.radius / a.cell)
print("=== vue exacte : %s autour de [%d,%d] | grille %dx%d (case %.0f m) ===" % (world, fx, fy, N, N, a.cell), flush=True)

xs = [-a.radius + (i + 0.5) * a.cell for i in range(N)]
pts = [(fx + xs[i], fy + xs[j]) for j in range(N) for i in range(N)]
sol = np.zeros(N * N, dtype="float32")
obs = np.zeros(N * N, dtype="float32")

t0 = time.time()
for s in range(0, len(pts), a.chunk):
    lot = pts[s:s + a.chunk]
    liste = "[" + ",".join("[%d,%d]" % (int(x), int(y)) for x, y in lot) + "]"
    # pour chaque point : altitude du sol, puis rayon vertical du haut vers le bas -> toit du premier obstacle
    q = ('HMT_P = %s; private _o = ""; '
         '{ private _px = _x select 0; private _py = _x select 1; '
         '  private _g = getTerrainHeightASL [_px, _py]; '
         '  private _hit = lineIntersectsSurfaces [[_px,_py,_g+60], [_px,_py,_g-1], objNull, objNull, true, 1]; '
         '  private _t = 0; '
         '  if (count _hit > 0) then { _t = ((_hit select 0) select 0 select 2) - _g; if (_t < 0) then {_t = 0} }; '
         '  _o = _o + format ["%%1,%%2;", round (10*_g), round (10*_t)]; '
         '} forEach HMT_P; (format ["LOS %%1", _o]) call HMT_EMIT;') % liste
    rr = b.query(q, r"LOS (.*)", want=1, timeout=60)
    if not rr:
        print("  (lot %d sans réponse)" % s, flush=True); continue
    vals = [t for t in rr[-1].group(1).strip().rstrip(";").split(";") if "," in t]
    for k, t in enumerate(vals):
        f = t.split(",")
        if s + k < len(pts) and f[0].lstrip("-").isdigit():
            sol[s + k] = int(f[0]) / 10.0
            obs[s + k] = int(f[1]) / 10.0
    if (s // a.chunk) % 15 == 0:
        print("  %5d/%d points (%.0fs)" % (s + len(lot), len(pts), time.time() - t0), flush=True)

sol = sol.reshape(N, N); obs = obs.reshape(N, N)
out = "/home/younes/arma3-marl/leviathan/los_%s_%d_%d.npz" % (world.lower(), fx, fy)
np.savez(out, sol=sol, obs=obs, cx=fx, cy=fy, cell=a.cell, radius=a.radius)
print("\n-> %s" % out, flush=True)
print("  relief : %.1f m à %.1f m (amplitude %.1f m)" % (sol.min(), sol.max(), sol.max() - sol.min()), flush=True)
print("  obstacles : %.0f%% des cases | hauteur moyenne %.1f m | max %.1f m" % (
    100 * (obs > 0.5).mean(), obs[obs > 0.5].mean() if (obs > 0.5).any() else 0, obs.max()), flush=True)
print("BAKE_LOS_DONE", flush=True)
