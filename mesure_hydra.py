#!/usr/bin/env python3
"""mesure_hydra — le degagement referme-t-il l ecart ?

Meme cible, meme critere, memes plis que `mesure_decoupage.py` : indice de Rand ajuste
entre la partition predite et celle d A3C, decoupage PAR BATIMENT.

Bras ajoute — HYDRA : on garde l arete (i,j) si le PASSAGE le long du segment >= tau, on
prend les composantes connexes. tau balaye SUR LES PLIS D APPRENTISSAGE seulement.
C est la dilatation de Hydra transposee aux aretes.

PREDICTION ECRITE AVANT DE REGARDER :
  · HYDRA > ETAGE  -> le degagement etait l ingredient manquant. L etage suivant est un
    modele qui PREDIT le degagement depuis des donnees de capteur : route Isaac.
  · HYDRA <= ETAGE -> un scalaire ne suffit pas, il faut l occupation complete du volume.

TOUS LES BRAS SONT REJUGES SUR LE MEME SOUS-ENSEMBLE TRONQUE (80 positions max), sinon la
comparaison avec les chiffres d hier serait truquee.
"""
import json, math, sys, random, collections
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
from mesure_decoupage import ari, comp, traits, logreg, pred

DEC = "/home/younes/arma3-marl/logs_train/corpus_decoupage.jsonl"
DEG = "/home/younes/arma3-marl/logs_train/corpus_degagement.jsonl"
random.seed(7); np.random.seed(7)
PLIS = 5


def charge():
    deg = {}
    for l in open(DEG):
        d = json.loads(l); deg[d["type"]] = d
    B = []
    for l in open(DEC):
        d = json.loads(l)
        g = d["geom"]
        if d["type"] not in deg:
            continue
        e = deg[d["type"]]
        n = min(len(g), len(e["degagement"]))
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
        B.append({"g": g[:n], "y": vrai, "bbox": d["bbox"], "type": d["type"],
                  "deg": e["degagement"][:n],
                  "ar": [a for a in e["aretes"] if a[0] < n and a[1] < n]})
    return B


def evalue(B, plis):
    s = collections.defaultdict(list)
    taus = []
    for k in range(plis):
        test = [b for i, b in enumerate(B) if i % plis == k]
        train = [b for i, b in enumerate(B) if i % plis != k]
        Tr = [traits(b) for b in train]
        Xtr = np.vstack([t[0] for t in Tr]); ytr = np.concatenate([t[1] for t in Tr])
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
        w = logreg((Xtr - mu) / sd, ytr)
        bd, td = -2, 5.0
        for tau in [1, 2, 3, 4, 5, 6, 8, 10, 14, 20]:
            v = []
            for b in train[:80]:
                X, y, P = traits(b)
                a = comp(len(b["g"]), [P[i] for i in range(len(P)) if X[i][4] < tau])
                r = ari(a, b["y"])
                if r is not None: v.append(r)
            m = sum(v) / max(len(v), 1)
            if m > bd: bd, td = m, tau
        bh, th = -2, 1.0
        for tau in [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0]:
            v = []
            for b in train[:80]:
                a = comp(len(b["g"]), [(x[0], x[1]) for x in b["ar"] if x[2] >= tau])
                r = ari(a, b["y"])
                if r is not None: v.append(r)
            m = sum(v) / max(len(v), 1)
            if m > bh: bh, th = m, tau
        taus.append(th)
        for b in test:
            X, y, P = traits(b); n = len(b["g"])
            arms = {
                "TOUT": [0] * n,
                "ETAGE": comp(n, [P[i] for i in range(len(P)) if X[i][2] < 1.5]),
                "DISTANCE": comp(n, [P[i] for i in range(len(P)) if X[i][4] < td]),
                "APPRIS": comp(n, [P[i] for i in range(len(P)) if pred((X - mu) / sd, w)[i] > 0.5]),
                "HYDRA": comp(n, [(x[0], x[1]) for x in b["ar"] if x[2] >= th]),
                "HYDRA+ETAGE": comp(n, [(x[0], x[1]) for x in b["ar"] if x[2] >= th
                                        and abs(b["g"][x[0]][2] - b["g"][x[1]][2]) < 1.5]),
            }
            for nom, a in arms.items():
                r = ari(a, b["y"])
                if r is not None: s[nom].append(r)
    return s, taus


if __name__ == "__main__":
    B = charge()
    print("batiments joints (decoupage + degagement) : %d" % len(B))
    print("positions : min=%d med=%d max=%d" % (min(len(b["g"]) for b in B),
          sorted(len(b["g"]) for b in B)[len(B) // 2], max(len(b["g"]) for b in B)))
    s, taus = evalue(B, PLIS)
    print("\nindice de Rand ajuste, decoupage par batiment :")
    for nom in ("TOUT", "ETAGE", "DISTANCE", "APPRIS", "HYDRA", "HYDRA+ETAGE"):
        v = s[nom]
        if v: print("   %-12s %.3f   (n=%d)" % (nom, sum(v) / len(v), len(v)))
    print("\ntau de HYDRA choisi par pli : %s" % taus)
    bete = max(sum(s[n]) / len(s[n]) for n in ("TOUT", "ETAGE", "DISTANCE"))
    hy = max(sum(s[n]) / len(s[n]) for n in ("HYDRA", "HYDRA+ETAGE"))
    print("ecart HYDRA - meilleur bete = %+.3f" % (hy - bete))
    print("\nVERDICT : %s" % ("LE DEGAGEMENT SUFFIT — un scalaire de mur referme l ecart"
                              if hy - bete > 0.05 else
                              "un scalaire NE SUFFIT PAS — il faut l occupation du volume"))
