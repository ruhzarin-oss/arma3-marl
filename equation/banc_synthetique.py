"""
Test A : banc synthetique, verite connue ( criteres : equation/CRITERES_BANC_EQUATION.md ).
  python banc_synthetique.py --algos l1,arbre --formules F0,F1,F2,F3 --sortie resultats/synthetique.jsonl
Reprenable : une ligne deja ecrite ( algo, formule, n, rep ) n'est pas recalculee.
"""
import argparse, json, os, time
import numpy as np
from algos import ALGOS, ecarts_croises

NOMS = ["distance", "moment", "alarme", "vehicule_vu", "defenseurs_connus", "leurre_uniforme", "leurre_binaire", "leurre_distance"]
VRAIES = {"F0": [], "F1": ["distance", "vehicule_vu"], "F2": ["distance", "moment"], "F3": ["distance", "alarme"]}
LEURRES = ["leurre_uniforme", "leurre_binaire", "leurre_distance"]
FORMULES = ["F0", "F1", "F2", "F3"]
TAILLES = [200, 500, 1000]
REPS = 20
Z_DECLARE = 2.326          # alpha = 1 % unilateral
ACCORD_MIN = 0.80


def tirer_x(rng, n):
    d = rng.uniform(0.1, 0.9, n)                                   # distance, km
    t = rng.uniform(0.0, 1.0, n)                                   # moment, fraction de la fenetre
    al = rng.binomial(1, 0.5, n)
    vv = rng.binomial(1, 0.4, n)
    de = np.clip(rng.poisson(3, n), 0, 8)
    l1 = rng.uniform(0.0, 1.0, n)
    l2 = rng.binomial(1, 0.5, n)
    l3 = 0.7 * (d - 0.5) / 0.2309 + 0.7141 * rng.normal(0.0, 1.0, n)   # correle a la distance, r = 0,7
    return np.column_stack([d, t, al, vv, de, l1, l2, l3]).astype(float)


def niveau(X):
    """Logit de reussite de l'option 0 : defenseurs_connus agit sur le niveau, jamais sur l'avantage."""
    return -0.15 * (X[:, 4] - 3) - 0.2 * X[:, 2] + 0.2 * (X[:, 0] - 0.5)


def avantage(formule, X):
    """g(x) : avantage de l'option 1 en logit. La bonne regle est g(x) > 0."""
    d, t, al, vv = X[:, 0], X[:, 1], X[:, 2], X[:, 3]
    if formule == "F0":
        return np.zeros(len(X))
    if formule == "F1":
        return np.clip(10.0 * (0.5 - d) + 3.0 * (vv - 0.4), -3.0, 3.0)
    if formule == "F2":
        return np.where((d - 0.5) * (t - 0.5) > 0, 3.0, -3.0)
    if formule == "F3":
        return np.where((al == 1) & (d < 0.7), 3.0, -3.0)
    raise ValueError(formule)


def sig(z):
    return 1.0 / (1.0 + np.exp(-z))


def un_essai(nom_algo, formule, n, rep, decalage=0):
    graine = 20260917 + 100000 * FORMULES.index(formule) + 1000 * TAILLES.index(n) + rep + decalage
    rng = np.random.default_rng(graine)
    X = tirer_x(rng, n)
    a = rng.binomial(1, 0.5, n)
    Y = rng.binomial(1, sig(niveau(X) + a * avantage(formule, X)))
    plis = rng.permutation(np.arange(n) % 5)
    algo = ALGOS[nom_algo]
    t0 = time.time()
    d = ecarts_croises(algo, X, a, Y, NOMS, plis, graine)
    r = algo(X, a, Y, NOMS, graine)
    duree = time.time() - t0
    G, se = float(d.mean()), float(d.std(ddof=1) / np.sqrt(n))
    declare = bool(se > 0 and G - Z_DECLARE * se > 0)
    Xt = tirer_x(np.random.default_rng(graine + 7), 20000)
    gt, e0 = avantage(formule, Xt), niveau(Xt)
    rt = r(Xt)
    m = np.abs(gt) >= 0.5
    accord = float(np.mean(rt[m] == (gt[m] > 0))) if m.any() else None
    v_regle = float(np.mean(sig(e0 + rt * gt)))
    v_const = max(float(np.mean(sig(e0))), float(np.mean(sig(e0 + gt))))
    v_ideal = float(np.mean(sig(e0 + (gt > 0) * gt)))
    return dict(algo=nom_algo, formule=formule, n=n, rep=rep, graine=graine, G=G, se=se, declare=declare,
                accord=accord, retrouvee=(bool(declare and accord is not None and accord >= ACCORD_MIN) if formule != "F0" else None),
                gain_vrai=v_regle - v_const, gain_ideal=v_ideal - v_const,
                variables=r.variables, vraies_trouvees=[v for v in VRAIES[formule] if v in r.variables],
                leurres=[v for v in LEURRES if v in r.variables], niveau_seul="defenseurs_connus" in r.variables,
                formule_apprise=r.texte[:600], duree_s=round(duree, 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algos", default="l1,arbre")
    ap.add_argument("--formules", default=",".join(FORMULES))
    ap.add_argument("--tailles", default=",".join(map(str, TAILLES)))
    ap.add_argument("--reps", type=int, default=REPS)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--fumee", action="store_true", help="graines decalees, disjointes du banc : verifier que le code tourne")
    o = ap.parse_args()
    os.makedirs(os.path.dirname(o.sortie) or ".", exist_ok=True)
    faits = set()
    if os.path.exists(o.sortie):
        for ligne in open(o.sortie):
            j = json.loads(ligne)
            faits.add((j["algo"], j["formule"], j["n"], j["rep"]))
    for nom_algo in o.algos.split(","):
        for formule in o.formules.split(","):
            for n in map(int, o.tailles.split(",")):
                for rep in range(o.reps):
                    if (nom_algo, formule, n, rep) in faits:
                        continue
                    res = un_essai(nom_algo, formule, n, rep, 9_000_000 if o.fumee else 0)
                    with open(o.sortie, "a") as f:
                        f.write(json.dumps(res) + "\n")
                    print(f"{nom_algo} {formule} n={n} rep={rep} declare={res['declare']} accord={res['accord']} {res['duree_s']} s", flush=True)


if __name__ == "__main__":
    main()
