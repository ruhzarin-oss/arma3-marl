#!/usr/bin/env python3
"""mesure_grille — HYDRA sans transposition : occupation -> champ de distance -> elagage.

C est la methode de Hydra appliquee telle quelle :
  1. grille d occupation du batiment (recoltee par 3 balayages de rayons)
  2. champ de distance euclidien exact aux obstacles (transformee separable, 3 axes)
  3. on ELAGUE les voxels libres dont la distance passe sous tau : les portes se ferment
  4. composantes connexes en 6-voisinage = les pieces
  5. chaque position de station recoit la composante du voxel survivant le plus proche

Difference avec la transposition d hier : la, le degagement etait mesure AUX POSITIONS DE
STATION, souvent collees aux murs. Ici il est mesure PARTOUT, donc les voxils du milieu de
piece portent bien un degagement maximal — c est l entree que Hydra attend.

MEME CIBLE, MEME CRITERE, MEMES PLIS. tau balaye sur les plis d apprentissage seulement.
Tous les bras sont rejuges sur le sous-ensemble effectivement joint.

PREDICTION ECRITE AVANT :
  · GRILLE > 0,438 (le ETAGE+HYDRA d hier) -> l occupation etait bien ce qui manquait.
  · GRILLE <= 0,438 -> ce n est pas une affaire de resolution d entree ; la regle d A3C
    (visibilite mutuelle globale) n est pas reductible a une dilatation locale.
"""
import json, math, sys, random, collections
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
from mesure_decoupage import ari, comp, traits, logreg, pred

GRI = "/home/younes/arma3-marl/logs_train/corpus_grille.jsonl"
DEC = "/home/younes/arma3-marl/logs_train/corpus_decoupage.jsonl"
random.seed(7); np.random.seed(7)
PLIS = 5
TAUS = [0.3, 0.5, 0.7, 0.9, 1.1, 1.4, 1.8]


def edt1d(f):
    n = len(f); d = np.empty(n); v = np.zeros(n, int); z = np.empty(n + 1)
    k = 0; v[0] = 0; z[0] = -1e20; z[1] = 1e20
    for q in range(1, n):
        while True:
            s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2.0 * q - 2.0 * v[k])
            if s <= z[k] and k > 0:
                k -= 1
            else:
                break
        k += 1; v[k] = q; z[k] = s; z[k + 1] = 1e20
    k = 0
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        d[q] = (q - v[k]) ** 2 + f[v[k]]
    return d


def edt3(occ, res):
    """distance euclidienne exacte de chaque voxel au plus proche voxel occupe"""
    INF = 1e18
    f = np.where(occ, 0.0, INF)
    nx, ny, nz = f.shape
    for y in range(ny):
        for z in range(nz):
            f[:, y, z] = edt1d(f[:, y, z])
    for x in range(nx):
        for z in range(nz):
            f[x, :, z] = edt1d(f[x, :, z])
    for x in range(nx):
        for y in range(ny):
            f[x, y, :] = edt1d(f[x, y, :])
    return np.sqrt(np.minimum(f, 1e18)) * res


def composantes(mask):
    """6-voisinage, retourne un tableau d etiquettes (-1 = hors masque)"""
    nx, ny, nz = mask.shape
    lab = -np.ones(mask.shape, int)
    cur = 0
    idx = np.argwhere(mask)
    vus = set(map(tuple, idx))
    for start in map(tuple, idx):
        if lab[start] >= 0:
            continue
        pile = [start]; lab[start] = cur
        while pile:
            x, y, z = pile.pop()
            for dx, dy, dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                v = (x+dx, y+dy, z+dz)
                if v in vus and lab[v] < 0:
                    lab[v] = cur; pile.append(v)
        cur += 1
    return lab, cur


def charge():
    dec = {}
    for l in open(DEC):
        d = json.loads(l); dec[d["type"]] = d
    B = []
    for l in open(GRI):
        g = json.loads(l)
        if g["type"] not in dec:
            continue
        d = dec[g["type"]]
        nx, ny, nz = g["n"]
        if nx * ny * nz > 300000:
            continue
        occ = np.zeros((nx, ny, nz), bool)
        for z, v in g["couches"].items():
            z = int(z)
            for k in v:
                occ[k % nx, (k // nx) % ny, z] = True
        pos = g["positions"]
        n = min(len(pos), len(d["geom"]))
        if n < 4:
            continue
        vrai = [-1] * n
        for k, pc in enumerate(d["pieces"]):
            for i in pc["positions"]:
                if 0 <= i < n:
                    vrai[i] = k
        libre = max(vrai) + 1
        for i in range(n):
            if vrai[i] < 0:
                vrai[i] = libre; libre += 1
        if len(set(vrai)) < 2:
            continue
        B.append({"type": g["type"], "occ": occ, "res": g["res"], "org": g["origine"],
                  "pos": pos[:n], "y": vrai, "g": d["geom"][:n], "bbox": d["bbox"]})
    return B


def prepare(b):
    b["edt"] = edt3(b["occ"], b["res"])
    nx, ny, nz = b["occ"].shape
    ox, oy, oz = b["org"]; r = b["res"]
    b["vox"] = []
    for p in b["pos"]:
        ix = min(max(int((p[0] - ox) / r), 0), nx - 1)
        iy = min(max(int((p[1] - oy) / r), 0), ny - 1)
        iz = min(max(int((p[2] + 1.0 - oz) / r), 0), nz - 1)
        b["vox"].append((ix, iy, iz))
    return b


def hydra(b, tau):
    mask = (~b["occ"]) & (b["edt"] >= tau)
    if mask.sum() == 0:
        return list(range(len(b["pos"])))
    lab, k = composantes(mask)
    survivants = np.argwhere(mask)
    out = []
    for v in b["vox"]:
        if mask[v]:
            out.append(int(lab[v]))
        else:
            d = ((survivants - np.array(v)) ** 2).sum(1)
            out.append(int(lab[tuple(survivants[int(d.argmin())])]))
    return out


if __name__ == "__main__":
    B = [prepare(b) for b in charge()]
    print("batiments joints (grille + decoupage) : %d" % len(B))
    s = collections.defaultdict(list); taus = []
    for k in range(PLIS):
        test = [b for i, b in enumerate(B) if i % PLIS == k]
        train = [b for i, b in enumerate(B) if i % PLIS != k]
        best, bt = -2, TAUS[0]
        for tau in TAUS:
            v = [ari(hydra(b, tau), b["y"]) for b in train[:60]]
            v = [x for x in v if x is not None]
            m = sum(v) / max(len(v), 1)
            if m > best: best, bt = m, tau
        taus.append(bt)
        for b in test:
            X, y, P = traits(b); n = len(b["g"])
            arms = {"ETAGE": comp(n, [P[i] for i in range(len(P)) if X[i][2] < 1.5]),
                    "GRILLE": hydra(b, bt)}
            gl = arms["GRILLE"]
            aretes = [(a, c) for a in range(n) for c in range(a + 1, n)
                      if gl[a] == gl[c] and abs(b["g"][a][2] - b["g"][c][2]) < 1.5]
            arms["GRILLE+ETAGE"] = comp(n, aretes)
            for nom, a in arms.items():
                r = ari(a, b["y"])
                if r is not None: s[nom].append(r)
    print("\nindice de Rand ajuste :")
    for nom in ("ETAGE", "GRILLE", "GRILLE+ETAGE"):
        v = s[nom]
        if v: print("   %-13s %.3f  (n=%d)" % (nom, sum(v) / len(v), len(v)))
    print("\ntau par pli : %s" % taus)
    print("rappel : ETAGE+HYDRA (degagement aux positions) = 0.438")
