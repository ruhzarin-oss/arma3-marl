"""Trois oracles de reference, en numpy : uniforme ( borne basse ), cases a poids exponentiels ( le plan, § 4 ), parfait ( borne haute )."""
import json, sys
import numpy as np
from mondes import MONDES, POINTS_PAR_TOUR, TOURS, episodes, separer, evaluer, regret

EPISODES_PAR_POINT = 4


def uniforme(monde, rep):
    rng = np.random.default_rng(1_000_000 + rep)
    T = rng.random((POINTS_PAR_TOUR * TOURS, 3))
    zbar, _ = episodes(monde, T, EPISODES_PAR_POINT, np.random.default_rng(2_000_000 + 1000 * list(MONDES).index(monde) + rep))
    return T.tolist(), separer(T, zbar)


def cases(monde, rep, nd=5, nm=5, nl=2, eta=0.2, nu=3.0, kappa=1.0):
    """Oracle du plan : cases ( distance x moment x leurre ), U = moyenne + kappa * se, poids exponentiels, part uniforme eta."""
    rng = np.random.default_rng(3_000_000 + rep)
    rng_ep = np.random.default_rng(4_000_000 + 1000 * list(MONDES).index(monde) + rep)
    K = nd * nm * nl
    q = np.full(K, 1.0 / K)
    somme, somme2, n = np.zeros(K), np.zeros(K), np.zeros(K)
    explores, zlist = [], []
    def case_de(t): return int(min(t[0] * nd, nd - 1)) * nm * nl + int(min(t[1] * nm, nm - 1)) * nl + int(min(t[2] * nl, nl - 1))
    for tour in range(TOURS):
        ks = rng.choice(K, POINTS_PAR_TOUR, p=q)
        T = []
        for k in ks:
            i, rest = divmod(k, nm * nl); j, l = divmod(rest, nl)
            T.append([(i + rng.random()) / nd, (j + rng.random()) / nm, (l + rng.random()) / nl])
        T = np.array(T)
        zbar, _ = episodes(monde, T, EPISODES_PAR_POINT, rng_ep)
        for t, zb in zip(T, zbar):
            k = case_de(t); somme[k] += zb * EPISODES_PAR_POINT; somme2[k] += (zb ** 2) * EPISODES_PAR_POINT; n[k] += EPISODES_PAR_POINT
        explores += T.tolist()
        zlist.append(zbar)
        moy = np.where(n > 0, somme / np.maximum(n, 1), 0.0)
        se = np.where(n > 0, np.sqrt(2.0 / np.maximum(n, 1)), 1.0)
        U = np.clip(moy + kappa * se, 0, 1)
        w = q * np.exp(nu * U); w /= w.sum()
        q = (1 - eta) * w + eta / K
    # candidats : les situations explorees au meilleur z moyen ( comme l'uniforme ), pas les centres de cases,
    # qui tombent hors des failles etroites ( vu au calibrage : 0,10 region sur 4 en W2 avec les centres )
    E = np.array(explores)
    zpts = np.concatenate(zlist)
    return explores, separer(E, zpts)


def parfait(monde, rep):
    """Connait le monde : explore aux centres des bosses et candidate les centres. Borne haute de la confirmation."""
    b = MONDES[monde]["bosses"]
    if not b:
        rng = np.random.default_rng(5_000_000 + rep)
        T = rng.random((POINTS_PAR_TOUR * TOURS, 3)); return T.tolist(), separer(T, regret(monde, T))
    C = [[c[0], c[1], 0.5] for (c, _, _) in b]
    return [C[i % len(C)] for i in range(POINTS_PAR_TOUR * TOURS)], C


if __name__ == "__main__":
    sortie = sys.argv[1]
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    with open(sortie, "a") as f:
        for monde in MONDES:
            for rep in range(reps):
                for nom, fn in (("uniforme", uniforme), ("cases_plan", cases), ("parfait", parfait)):
                    explores, cand = fn(monde, rep)
                    f.write(json.dumps(evaluer(monde, rep, nom, explores, cand)) + "\n")
    print("fini", sortie)
