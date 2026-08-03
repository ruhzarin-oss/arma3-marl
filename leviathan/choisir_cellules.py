#!/usr/bin/env python3
"""choisir_cellules — emplacements de banc TERRE, PLATS, SECS et espaces.

Le scan par requetes Arma est mort de sa propre lourdeur (14 lots, zero reponse : SQF trop
long pour l'ordonnanceur). Le relief d'Altis est deja en cache : relief_altis.npz, grille
153x153 au pas de 200 m, hauteur + masque d'eau. On selectionne hors ligne, et on ne
demande a Arma que la VERIFICATION des finalistes (eau, altitude, bati).
"""
import sys
import json
import math
import numpy as np

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")

LEV = "/home/younes/arma3-marl/leviathan"
D = np.load(LEV + "/relief_altis.npz")
H = D["H"].astype(np.float32)
EAU = D["EAU"].astype(np.uint8)
PAS = int(D["pas"])
N = H.shape[0]

MARGE_EAU = 2          # cases de 200 m -> 400 m sans eau autour
DH_MAX = 6.0           # m d ecart d altitude sur le voisinage 3x3 (+-200 m)
ESPACE = 700.0

# H[i, j] : i = ? j = ? -- on teste les deux conventions contre un repere connu (Pyrgos, alt ~19)
def h_at(x, y, arr=H):
    i = int(round(y / PAS)); j = int(round(x / PAS))
    i = min(max(i, 0), N - 1); j = min(max(j, 0), N - 1)
    return float(arr[i, j])


print("test de convention sur Pyrgos (16781,12604), altitude reelle 19 m :")
print("  H[y,x] = %.0f    H[x,y] = %.0f" % (h_at(16781, 12604), float(H[int(round(16781 / PAS)), int(round(12604 / PAS))])))

cands = []
for i in range(MARGE_EAU, N - MARGE_EAU):
    for j in range(MARGE_EAU, N - MARGE_EAU):
        if EAU[i, j]:
            continue
        vois = EAU[i - MARGE_EAU:i + MARGE_EAU + 1, j - MARGE_EAU:j + MARGE_EAU + 1]
        if vois.any():
            continue
        bloc = H[i - 1:i + 2, j - 1:j + 2]
        if float(bloc.max() - bloc.min()) > DH_MAX:
            continue
        if H[i, j] < 2.0:
            continue
        x = j * PAS
        y = i * PAS
        cands.append((x, y, float(H[i, j]), float(bloc.max() - bloc.min())))

print("%d cases plates, seches, a 400 m de toute eau" % len(cands))
cands.sort(key=lambda t: t[3])          # les plus plates d abord
serie = []
for (x, y, h, dh) in cands:
    if all(math.hypot(x - sx, y - sy) >= ESPACE for (sx, sy, _, _) in serie):
        serie.append((x, y, h, dh))
    if len(serie) >= 24:
        break
print("%d cellules mutuellement espacees de %d m :" % (len(serie), ESPACE))
for (x, y, h, dh) in serie:
    print("   %6d %6d  alt %5.1f  relief %4.1f" % (x, y, h, dh))
json.dump({"serie": [[int(x), int(y), int(round(h))] for (x, y, h, dh) in serie]},
          open(LEV + "/cellules_altis_brut.json", "w"), indent=1)
print("-> cellules_altis_brut.json")
