#!/usr/bin/env python3
"""juge_corpus — les deux profs ecrivent-ils la MEME geometrie ?

LA FALSIFICATION, posee avant de regarder : si un juge ne sait pas distinguer une
trajectoire A3C d une trajectoire LAMBS sur la geometrie seule, l usine ne produit rien
que LAMBS ne produisait deja, et le pari tombe.

SEPARABILITE = CONDITION NECESSAIRE, PAS SUFFISANTE. Deux corpus distinguables peuvent
etre egalement pauvres pour l aval. Mais s ils sont confondus, inutile d entrainer.

DECOUPAGE PAR MANCHE, JAMAIS PAR TICK. Deux ticks voisins de la meme manche sont quasi
identiques : un decoupage naif mettrait l un en apprentissage et l autre en test, et
rendrait n importe quoi separable. C est la panne du 235e run.

CONTROLE DE PERMUTATION : on rebat l etiquette AU NIVEAU DE LA MANCHE, 200 fois. Si
l AUC observee ne sort pas de cette distribution, elle ne vaut rien.

Regression logistique ecrite a la main (pas de sklearn sur cette machine).
"""
import json, math, sys, itertools, random
import numpy as np

CHEMIN = sys.argv[1] if len(sys.argv) > 1 else "/home/younes/arma3-marl/logs_train/corpus_a3c_lambs.jsonl"
random.seed(12345); np.random.seed(12345)


def traits(d):
    """Geometrie SEULE. Pas d issue (def_vivants, dedans) : on demande si les profs
    ECRIVENT differemment, pas s ils gagnent differemment."""
    v = [u for u in d["u"] if u[4] == 1]
    if not v:
        return None
    dist = sorted(math.hypot(u[0], u[1]) for u in v)
    z = sorted(u[2] for u in v)
    while len(dist) < 8: dist.append(dist[-1] if dist else 0.0)
    while len(z) < 8: z.append(z[-1] if z else 0.0)
    st = [0, 0, 0, 0]
    for u in v: st[min(u[3], 3)] += 1
    xs = [u[0] for u in v]; ys = [u[1] for u in v]
    import os
    if os.environ.get("SANS_DISTANCE"):
        return (z[:8] + st + [len(v), float(np.std(xs)), float(np.std(ys))])
    return (dist[:8] + z[:8] + st + [len(v), float(np.std(xs)), float(np.std(ys)),
            float(np.mean(dist)), float(max(dist) - min(dist))])


def charge():
    X, y, g = [], [], []
    for l in open(CHEMIN):
        d = json.loads(l)
        import os
        pa = os.environ.get("PAIRE", "A3C:LAMBS").split(":")
        if d.get("manifeste") or "u" not in d:
            continue
        if d["bras"] not in pa:
            continue
        f = traits(d)
        if f is None:
            continue
        X.append(f); y.append(1 if d["bras"] == pa[0] else 0); g.append(d["rid"])
    return np.array(X, float), np.array(y), np.array(g)


def logreg(X, y, pas=0.2, iters=3000, l2=1e-3):
    X = np.hstack([X, np.ones((len(X), 1))])
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))
        w -= pas * (X.T @ (p - y) / len(y) + l2 * w)
    return w


def predit(X, w):
    X = np.hstack([X, np.ones((len(X), 1))])
    return 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))


def auc(y, s):
    p = [s[i] for i in range(len(y)) if y[i] == 1]
    n = [s[i] for i in range(len(y)) if y[i] == 0]
    if not p or not n:
        return float("nan")
    c = sum((1.0 if a > b else 0.5 if a == b else 0.0) for a in p for b in n)
    return c / (len(p) * len(n))


def cv_par_manche(X, y, g, yg_map):
    """Leave-one-round-out par classe : a chaque pli, une manche A3C et une manche LAMBS
    sortent ensemble. Score agrege au niveau MANCHE (moyenne des ticks)."""
    ra = sorted(r for r in yg_map if yg_map[r] == 1)
    rl = sorted(r for r in yg_map if yg_map[r] == 0)
    scores, vrais = [], []
    for a, l in zip(ra, rl):
        test = np.isin(g, [a, l]); train = ~test
        mu, sd = X[train].mean(0), X[train].std(0) + 1e-9
        w = logreg((X[train] - mu) / sd, y[train])
        s = predit((X[test] - mu) / sd, w)
        for r in (a, l):
            m = g[test] == r
            if m.sum():
                scores.append(float(s[m].mean())); vrais.append(yg_map[r])
    return auc(vrais, scores), len(vrais)


if __name__ == "__main__":
    X, y, g = charge()
    yg = {}
    for i in range(len(g)): yg[int(g[i])] = int(y[i])
    na = sum(1 for r in yg if yg[r] == 1); nl = len(yg) - na
    import os
    pa = os.environ.get("PAIRE", "A3C:LAMBS").split(":")
    print("corpus : %d ticks, %d manches (%s=%d, %s=%d), %d traits geometriques"
          % (len(X), len(yg), pa[0], na, pa[1], nl, X.shape[1]))
    if na < 3 or nl < 3:
        print("pas assez de manches"); sys.exit(1)

    obs, nm = cv_par_manche(X, y, g, yg)
    print("\nAUC observee (decoupage par manche, score agrege par manche) = %.3f  sur %d manches" % (obs, nm))

    nul = []
    manches = sorted(yg)
    for _ in range(200):
        et = [yg[r] for r in manches]; random.shuffle(et)
        m2 = dict(zip(manches, et))
        y2 = np.array([m2[int(r)] for r in g])
        a, _ = cv_par_manche(X, y2, g, m2)
        if not math.isnan(a): nul.append(a)
    nul = sorted(nul)
    p = (sum(1 for a in nul if a >= obs) + 1) / (len(nul) + 1)
    print("controle de permutation (200 rebats AU NIVEAU MANCHE) : nul median=%.3f, 95e centile=%.3f"
          % (nul[len(nul) // 2], nul[int(0.95 * len(nul))]))
    print("p = %.4f" % p)
    print("\nVERDICT : %s" % ("les deux profs ecrivent une geometrie DISTINGUABLE -> condition necessaire remplie"
                              if p < 0.05 else
                              "geometries CONFONDUES -> l usine ne produit rien que LAMBS ne produisait deja"))
