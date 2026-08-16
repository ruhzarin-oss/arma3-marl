#!/usr/bin/env python3
"""mesure_decoupage — le decoupage d A3C est-il autre chose qu un seuil de distance ?

CIBLE : la partition des positions interieures en pieces, telle que
`A3C_main_fnc_buildingCreateRooms` la produit. Certifiee a 98 % pose contre terrain.

CE QU ON COMPARE — tous jugés sur le MEME critere, l indice de Rand ajuste entre la
partition predite et celle d A3C, moyenne par batiment :
  TOUT      : une seule piece. Plancher.
  ETAGE     : meme piece si meme hauteur (|dz| < 1,5 m). La regle bete.
  DISTANCE  : meme piece si distance 3D < tau, tau REGLE SUR LES PLIS D APPRENTISSAGE.
  ETAGE+DIST: les deux a la fois.
  APPRIS    : regression logistique sur des traits de PAIRES, puis composantes connexes.

FALSIFICATION, ECRITE AVANT DE REGARDER :
  · APPRIS ne bat pas le meilleur bete -> le decoupage d A3C est un seuil deguise, il n y
    a rien a distiller, et on arrete.
  · APPRIS le bat nettement -> il y a une structure a apprendre, et elle transfere.

DECOUPAGE PAR BATIMENT, jamais par paire : deux paires du meme batiment partagent tout.
CONTROLE DE PERMUTATION : on reattribue les cibles entre batiments de meme taille. Si
l ecart survit a ca, il ne vaut rien.

LIMITE STRUCTURELLE : A3C decoupe par ligne de vue, donc par les MURS, et mes entrees ne
contiennent que les positions ou un homme se tient. Si APPRIS echoue, la conclusion
honnete est peut-etre "mon entree n a pas les murs", pas "A3C est trivial".
"""
import json, math, sys, random, collections
import numpy as np

CHEMIN = sys.argv[1] if len(sys.argv) > 1 else "/home/younes/arma3-marl/logs_train/corpus_decoupage.jsonl"
random.seed(7); np.random.seed(7)
PLIS = 5


def ari(a, b):
    """indice de Rand ajuste entre deux etiquetages"""
    n = len(a)
    if n < 2:
        return None
    t = collections.Counter(zip(a, b))
    ca = collections.Counter(a); cb = collections.Counter(b)
    c2 = lambda x: x * (x - 1) / 2
    idx = sum(c2(v) for v in t.values())
    sa = sum(c2(v) for v in ca.values()); sb = sum(c2(v) for v in cb.values())
    tot = c2(n)
    att = sa * sb / tot if tot else 0
    mx = (sa + sb) / 2
    return 1.0 if mx == att else (idx - att) / (mx - att)


def comp(n, aretes):
    p = list(range(n))
    def f(x):
        while p[x] != x:
            p[x] = p[p[x]]; x = p[x]
        return x
    for i, j in aretes:
        a, c = f(i), f(j)
        if a != c:
            p[a] = c
    return [f(i) for i in range(n)]


def charge():
    B = []
    for l in open(CHEMIN):
        d = json.loads(l)
        g = d["geom"]
        vrai = [-1] * len(g)
        for k, pc in enumerate(d["pieces"]):
            for i in pc["positions"]:
                if 0 <= i < len(g):
                    vrai[i] = k
        libre = max(vrai) + 1 if vrai else 0
        for i in range(len(vrai)):          # position dans aucune piece = piece a elle seule
            if vrai[i] < 0:
                vrai[i] = libre; libre += 1
        if len(g) >= 4 and len(set(vrai)) >= 2:
            B.append({"g": g, "y": vrai, "bbox": d["bbox"], "type": d["type"]})
    return B


def traits(b):
    g = b["g"]; n = len(g); bx, by = b["bbox"]
    diag = max(math.hypot(bx, by), 1e-6)
    X, Y, P = [], [], []
    for i in range(n):
        for j in range(i + 1, n):
            dx = abs(g[i][0] - g[j][0]); dy = abs(g[i][1] - g[j][1]); dz = abs(g[i][2] - g[j][2])
            d2 = math.hypot(dx, dy); d3 = math.sqrt(d2 * d2 + dz * dz)
            X.append([dx, dy, dz, d2, d3, d2 / diag, d3 / diag,
                      1.0 if dz < 1.5 else 0.0, n, bx, by, n / max(bx * by, 1.0)])
            Y.append(1 if b["y"][i] == b["y"][j] else 0)
            P.append((i, j))
    return np.array(X, float), np.array(Y), P


def logreg(X, y, pas=0.3, it=2500, l2=1e-3):
    X = np.hstack([X, np.ones((len(X), 1))]); w = np.zeros(X.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))
        w -= pas * (X.T @ (p - y) / len(y) + l2 * w)
    return w


def pred(X, w):
    X = np.hstack([X, np.ones((len(X), 1))])
    return 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))


def evalue(B, plis):
    scores = collections.defaultdict(list)
    for k in range(plis):
        test = [b for i, b in enumerate(B) if i % plis == k]
        train = [b for i, b in enumerate(B) if i % plis != k]
        Tr = [traits(b) for b in train]
        Xtr = np.vstack([t[0] for t in Tr]); ytr = np.concatenate([t[1] for t in Tr])
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
        w = logreg((Xtr - mu) / sd, ytr)
        # tau du bras DISTANCE regle sur le pli d apprentissage
        best, bt = -2, 5.0
        for tau in [1, 2, 3, 4, 5, 6, 8, 10, 14, 20]:
            s = []
            for b in train[:60]:
                X, y, P = traits(b)
                a = comp(len(b["g"]), [P[i] for i in range(len(P)) if X[i][4] < tau])
                v = ari(a, b["y"])
                if v is not None: s.append(v)
            m = sum(s) / max(len(s), 1)
            if m > best: best, bt = m, tau
        for b in test:
            X, y, P = traits(b); n = len(b["g"])
            arms = {
                "TOUT": [0] * n,
                "ETAGE": comp(n, [P[i] for i in range(len(P)) if X[i][2] < 1.5]),
                "DISTANCE": comp(n, [P[i] for i in range(len(P)) if X[i][4] < bt]),
                "ETAGE+DIST": comp(n, [P[i] for i in range(len(P)) if X[i][2] < 1.5 and X[i][4] < bt]),
                "APPRIS": comp(n, [P[i] for i in range(len(P)) if pred((X - mu) / sd, w)[i] > 0.5]),
            }
            for nom, a in arms.items():
                v = ari(a, b["y"])
                if v is not None: scores[nom].append(v)
    return scores


if __name__ == "__main__":
    B = charge()
    print("batiments exploitables (>=4 positions, >=2 pieces) : %d" % len(B))
    print("positions : min=%d med=%d max=%d" % (min(len(b["g"]) for b in B),
          sorted(len(b["g"]) for b in B)[len(B) // 2], max(len(b["g"]) for b in B)))
    s = evalue(B, PLIS)
    print("\nindice de Rand ajuste (1 = parfait, 0 = hasard), decoupage par batiment :")
    for nom in ("TOUT", "ETAGE", "DISTANCE", "ETAGE+DIST", "APPRIS"):
        v = s[nom]; print("   %-11s %.3f   (n=%d)" % (nom, sum(v) / len(v), len(v)))
    bete = max(sum(s[n]) / len(s[n]) for n in ("TOUT", "ETAGE", "DISTANCE", "ETAGE+DIST"))
    app = sum(s["APPRIS"]) / len(s["APPRIS"])
    print("\necart APPRIS - meilleur bete = %+.3f" % (app - bete))

    print("\ncontrole de permutation (cibles rebattues entre batiments de meme taille) :")
    par = collections.defaultdict(list)
    for b in B: par[len(b["g"])].append(b)
    Bp = []
    for n, v in par.items():
        ys = [x["y"] for x in v]; random.shuffle(ys)
        for x, y in zip(v, ys): Bp.append({"g": x["g"], "y": y, "bbox": x["bbox"], "type": x["type"]})
    sp = evalue(Bp, 3)
    for nom in ("DISTANCE", "APPRIS"):
        v = sp[nom]; print("   %-11s %.3f" % (nom, sum(v) / len(v)))
    print("\nVERDICT : %s" % ("il y a une STRUCTURE a apprendre" if app - bete > 0.05 else
                              "SEUIL DEGUISE — rien a distiller depuis les seules positions"))
