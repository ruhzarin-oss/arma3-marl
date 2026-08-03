#!/usr/bin/env python3
"""carte_relief.py — releve du RELIEF de toute la carte, une bonne fois.

Chercher un terrain plat en interrogeant Arma emplacement par emplacement est lent
et grossier (le balayage a 2900 m a rate un denivele de 52 m). On preleve donc une
grille reguliere d altitudes UNE fois, on la garde, et toutes les recherches
suivantes se font en local, instantanement et a la vraie resolution.

Sortie : relief_<monde>.npz  (hauteur du sol + drapeau eau)
"""
import sys, time, argparse
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
ap = argparse.ArgumentParser()
ap.add_argument("--pas", type=int, default=200, help="resolution du releve (m)")
ap.add_argument("--lignes", type=int, default=4, help="lignes par requete")
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)

b = NativeBridge(port=TH.PORT)
r = b.query("(format [" + Q + "W %1" + Q + ", worldSize]) call HMT_EMIT;", r"W (\d+)", want=1, timeout=20)
if not r:
    print("pas de reponse du serveur"); sys.exit(1)
taille = int(r[-1].group(1))
n = taille // a.pas
print("=== releve du relief : monde %d m, grille %dx%d au pas de %d m ===" % (taille, n, n, a.pas), flush=True)

H = np.full((n, n), np.nan, dtype=np.float32)
E = np.zeros((n, n), dtype=np.uint8)
t0 = time.time()
for j0 in range(0, n, a.lignes):
    js = list(range(j0, min(j0 + a.lignes, n)))
    pts = [(i * a.pas, j * a.pas) for j in js for i in range(n)]
    liste = "[" + ",".join("[%d,%d]" % p for p in pts) + "]"
    q = ("private _o = " + Q + Q + "; { _o = _o + format [" + Q + "%1,%2;" + Q + ", "
         "round (getTerrainHeightASL _x), (if (surfaceIsWater _x) then {1} else {0})] } forEach " + liste + "; "
         "(format [" + Q + "H %1" + Q + ", _o]) call HMT_EMIT;")
    rr = b.query(q, r"H (.*)", want=1, timeout=120)
    if not rr:
        print("  (lignes %s sans reponse)" % js, flush=True); continue
    vals = [t for t in rr[-1].group(1).strip().rstrip(";").split(";") if "," in t]
    for k, t in enumerate(vals):
        h, e = t.split(",")
        j = js[k // n]; i = k % n
        if j < n and i < n:
            try:
                H[j, i] = float(h); E[j, i] = int(e)
            except ValueError:
                pass
    if j0 % 20 == 0:
        print("  %d/%d lignes (%.0f s)" % (j0 + len(js), n, time.time() - t0), flush=True)
b.close()

manque = int(np.isnan(H).sum())
np.savez_compressed("/home/younes/arma3-marl/leviathan/relief_%s.npz" % TH.NAME.lower(),
                    H=H, EAU=E, pas=a.pas, taille=taille)
print("\n-> relief_%s.npz | %d points, %d manquants, %.0f s" % (TH.NAME.lower(), n * n, manque, time.time() - t0), flush=True)
print("   altitudes %.0f a %.0f m | %.0f%% de terre" % (np.nanmin(H), np.nanmax(H), 100.0 * (E == 0).mean()), flush=True)
print("RELIEF_DONE", flush=True)
