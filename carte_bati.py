#!/usr/bin/env python3
"""carte_bati.py — releve du BATI de la carte, pour deriver l ETIQUETTE DE SCENE.

⟨Fable, 07/08 : « l etiquette de scene se derive sans y mettre la main : le corpus porte les
 POSITIONS, la carte d Arma porte les BATIMENTS et les ROUTES — un rayon autour de chaque
 point donne rue / lisiere / ouvert / interieur mecaniquement, sur pieces, pas au juge. »⟩

Calque sur carte_relief.py, qui a releve toute une carte en six secondes. Meme pont, meme
grille, meme protocole — on change ce qu on demande a chaque point :

    nearestObjects [_x, ["House"], R]      -> combien de batiments autour
    nearestTerrainObjects [_x, ["TREE"], R] -> combien d arbres autour
    isOnRoad _x                             -> suis-je sur une route

De ces trois nombres l etiquette se deduit MECANIQUEMENT, sans jugement :
    interieur  batiments tres proches et nombreux
    rue        sur une route, avec du bati autour
    lisiere    des arbres, peu ou pas de bati
    ouvert     ni bati, ni arbres, ni route

LE MONDE EST STRATIS, pas Altis. Le corpus (nuit_20260803) porte « Mission world: Stratis » ;
les cartes deja au dossier sont toutes d Altis, d ou zero recouvrement avec les positions.
8 192 m de cote au lieu de 30 720 : le releve est d autant plus court.

RIEN N EST DEPOSE ICI : ce script produit une CARTE, pas un verdict. Le trieur jugera.
"""
import sys, time, argparse
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
ap = argparse.ArgumentParser()
ap.add_argument("--pas", type=int, default=25, help="resolution du releve (m)")
ap.add_argument("--rayon", type=int, default=30, help="rayon d inspection autour du point (m)")
ap.add_argument("--lignes", type=int, default=2, help="lignes par requete")
theatre.add_theatre_arg(ap)
a = ap.parse_args()
TH = theatre.apply_theatre_arg(a)

b = NativeBridge(port=TH.PORT)
r = b.query("(format [" + Q + "W %1" + Q + ", worldSize]) call HMT_EMIT;", r"W (\d+)", want=1, timeout=20)
if not r:
    print("pas de reponse du serveur"); sys.exit(1)
taille = int(r[-1].group(1))
n = taille // a.pas
print("=== releve du BATI : monde %d m, grille %dx%d au pas de %d m, rayon %d m ==="
      % (taille, n, n, a.pas, a.rayon), flush=True)

MAI = np.full((n, n), -1, dtype=np.int16)      # batiments dans le rayon
ARB = np.full((n, n), -1, dtype=np.int16)      # arbres dans le rayon
ROU = np.full((n, n), -1, dtype=np.int8)       # sur une route
t0 = time.time()
for j0 in range(0, n, a.lignes):
    js = list(range(j0, min(j0 + a.lignes, n)))
    pts = [(i * a.pas, j * a.pas) for j in js for i in range(n)]
    liste = "[" + ",".join("[%d,%d,0]" % p for p in pts) + "]"
    q = ("private _o = " + Q + Q + "; { _o = _o + format [" + Q + "%1,%2,%3;" + Q + ", "
         "count (nearestObjects [_x, [" + Q + "House" + Q + "], " + str(a.rayon) + "]), "
         "count (nearestTerrainObjects [_x, [" + Q + "TREE" + Q + "," + Q + "SMALL TREE" + Q
         + "], " + str(a.rayon) + "]), "
         "(if (isOnRoad _x) then {1} else {0})] } forEach " + liste + "; "
         "(format [" + Q + "B %1" + Q + ", _o]) call HMT_EMIT;")
    rr = b.query(q, r"B (.*)", want=1, timeout=180)
    if not rr:
        print("  (lignes %s sans reponse)" % js, flush=True)
        continue
    vals = [t for t in rr[-1].group(1).strip().rstrip(";").split(";") if "," in t]
    for k, t in enumerate(vals):
        try:
            m_, ar_, ro_ = t.split(",")
        except ValueError:
            continue
        j = js[k // n]; i = k % n
        if j < n and i < n:
            try:
                MAI[j, i] = int(m_); ARB[j, i] = int(ar_); ROU[j, i] = int(ro_)
            except ValueError:
                pass
    if j0 % 20 == 0:
        print("  %d/%d lignes (%.0f s)" % (j0 + len(js), n, time.time() - t0), flush=True)
b.close()

manque = int((MAI < 0).sum())
np.savez_compressed("/home/younes/arma3-marl/leviathan/bati_%s.npz" % TH.NAME.lower(),
                    MAISONS=MAI, ARBRES=ARB, ROUTE=ROU, pas=a.pas, rayon=a.rayon, taille=taille)
ok = MAI >= 0
print("\n-> bati_%s.npz | %d points, %d manquants, %.0f s"
      % (TH.NAME.lower(), n * n, manque, time.time() - t0), flush=True)
if ok.any():
    print("   batiments : mediane %d, max %d · arbres : mediane %d, max %d · sur route %.1f%%"
          % (np.median(MAI[ok]), MAI[ok].max(), np.median(ARB[ok]), ARB[ok].max(),
             100.0 * (ROU[ok] > 0).mean()), flush=True)
print("BATI_DONE", flush=True)
