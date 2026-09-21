"""Amendement 3, controle d equivalence : sur des ajustements ou l export sympy REUSSIT, l evaluateur direct de la formule doit rendre les memes predictions que
model.predict ( le chemin des 131 essais deja ecrits ). Graines decalees ( fumee ) : aucun essai du banc n est touche."""
import numpy as np, sys
sys.path.insert(0, "/mnt/data/hmt/equation/code_controle")
import algos, banc_synthetique as b
from pysr import PySRRegressor
algos._pysr_export_tolerant()
pire = 0.0; desaccords = 0; total = 0
for formule in ("F1", "F2", "F3"):
    graine = 20260917 + 9_000_000 + 77 + b.FORMULES.index(formule); rng = np.random.default_rng(graine)
    X = b.tirer_x(rng, 500); a = rng.binomial(1, 0.5, 500); Y = rng.binomial(1, b.sig(b.niveau(X) + a * b.avantage(formule, X))); psi = algos.pseudo_issue(a, Y)
    m = PySRRegressor(niterations=algos.PYSR_ITERATIONS, populations=8, population_size=30, ncycles_per_iteration=300, maxsize=25, binary_operators=["+", "-", "*", "min", "max", "greater"],
                      unary_operators=["neg"], parsimony=0.001, elementwise_loss="L2DistLoss()", model_selection="best", parallelism="serial", deterministic=True,
                      random_state=int(graine % (2 ** 31 - 1)), progress=False, verbosity=0, temp_equation_file=True)
    m.fit(X, psi, variable_names=list(b.NOMS)); Xt = b.tirer_x(np.random.default_rng(graine + 7), 20000)
    for k in range(len(m.equations_)):                      # TOUTES les formules du front, pas seulement la retenue
        texte = str(m.equations_.iloc[k]["equation"])
        if "export_sympy_impossible" in str(m.equations_.iloc[k].get("sympy_format", "")): continue
        p1 = np.asarray(m.predict(Xt, index=k)).reshape(-1); p2 = algos._pysr_evaluer(texte, Xt, b.NOMS)
        pire = max(pire, float(np.max(np.abs(p1 - p2)))); desaccords += int(np.sum((p1 > 0) != (p2 > 0))); total += len(Xt)
    print(formule, "| formules comparees :", len(m.equations_), "| retenue :", str(m.get_best()["equation"])[:110])
print(f"ECART MAX des valeurs : {pire:.3g} ; DESACCORDS de regle ( > 0 ) : {desaccords} sur {total}")
print("EQUIVALENCE", "OK" if desaccords == 0 and pire < 1e-4 else "ECHEC")
