"""
Algorithmes d'equation testes sans Oracle ( criteres : equation/CRITERES_BANC_EQUATION.md ).
Chacun apprend une regle r(x) -> {0, 1} a partir de ( X, a, Y ), l'option ayant ete tiree a p = 1/2.
Quantite commune : psi = 2 * Y * ( 2a - 1 ), dont la moyenne sachant x vaut exactement tau(x).
"""
import re
import numpy as np
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor, export_text


def pseudo_issue(a, Y):
    return 2.0 * Y * (2 * a - 1)


class Regle:
    def __init__(self, fonction, variables, texte):
        self.fonction, self.variables, self.texte = fonction, sorted(set(variables)), texte

    def __call__(self, X):
        return np.asarray(self.fonction(X)).astype(int)


def constante(option):
    return Regle(lambda X, o=option: np.full(len(X), o), [], f"constante {option}")


def l1(X, a, Y, noms, graine):
    """Logistique L1 : logit P(Y) = alpha + beta.x + a.(gamma0 + gamma.x) ; regle = gamma0 + gamma.x > 0."""
    varie = X.std(axis=0) > 0
    if len(np.unique(Y)) < 2 or min(np.bincount(Y.astype(int))) < 5 or not varie.any():
        return constante(int(pseudo_issue(a, Y).mean() > 0))
    nv = [n for n, v in zip(noms, varie) if v]
    sc = StandardScaler().fit(X[:, varie])
    Z = sc.transform(X[:, varie])
    D = np.column_stack([Z, a, a[:, None] * Z])
    m = LogisticRegressionCV(Cs=10, cv=5, penalty="l1", solver="liblinear", scoring="neg_log_loss",
                             max_iter=5000, random_state=graine).fit(D, Y)
    coef = m.coef_[0]
    p = Z.shape[1]
    g0, gam = coef[p], coef[p + 1:]
    garde = [j for j in range(p) if abs(gam[j]) > 1e-9]
    texte = f"{g0:+.3f} " + " ".join(f"{gam[j]:+.3f}*z({nv[j]})" for j in garde)
    return Regle(lambda Xn, sc=sc, g0=g0, gam=gam, varie=varie: g0 + sc.transform(Xn[:, varie]) @ gam > 0,
                 [nv[j] for j in garde], texte)


def arbre(X, a, Y, noms, graine):
    """Arbre de regression sur psi, profondeur 0 a 3 choisie par validation croisee ; regle = prediction > 0."""
    psi = pseudo_issue(a, Y)
    n = len(Y)
    feuille = max(20, n // 20)
    kf = KFold(5, shuffle=True, random_state=graine)
    meilleur = -np.mean([np.mean((psi[te] - psi[tr].mean()) ** 2) for tr, te in kf.split(X)])
    prof = 0
    for d in (1, 2, 3):
        s = cross_val_score(DecisionTreeRegressor(max_depth=d, min_samples_leaf=feuille, random_state=graine),
                            X, psi, cv=kf, scoring="neg_mean_squared_error").mean()
        if s > meilleur:
            meilleur, prof = s, d
    if prof == 0:
        return constante(int(psi.mean() > 0))
    t = DecisionTreeRegressor(max_depth=prof, min_samples_leaf=feuille, random_state=graine).fit(X, psi)
    variables = [noms[i] for i in t.tree_.feature if i >= 0]
    return Regle(lambda Xn, t=t: t.predict(Xn) > 0, variables,
                 export_text(t, feature_names=list(noms), decimals=3).replace("\n", " ; "))


def _gt(x1, x2):
    return (x1 > x2).astype(float)


def gplearn(X, a, Y, noms, graine):
    """Programmation genetique ( gplearn ) sur psi ; regle = formule > 0."""
    from gplearn.functions import make_function
    from gplearn.genetic import SymbolicRegressor
    psi = pseudo_issue(a, Y)
    gt = make_function(function=_gt, name="gt", arity=2)
    est = SymbolicRegressor(population_size=500, generations=15, tournament_size=20, const_range=(-1.0, 1.0),
                            init_depth=(2, 4), function_set=("add", "sub", "mul", "min", "max", "neg", gt),
                            metric="mse", parsimony_coefficient=0.001, p_crossover=0.7, p_subtree_mutation=0.1,
                            p_hoist_mutation=0.05, p_point_mutation=0.1, n_jobs=1, random_state=graine,
                            feature_names=list(noms))
    est.fit(X, psi)
    prog = str(est._program)
    variables = [n for n in noms if re.search(r"\b" + re.escape(n) + r"\b", prog)]
    return Regle(lambda Xn, e=est: e.predict(Xn) > 0, variables, prog)


ALGOS = {"l1": l1, "arbre": arbre, "gplearn": gplearn}


def ecarts_croises(algo, X, a, Y, noms, plis, graine):
    """d_i = 2 Y_i ( 1{a_i = r(x_i)} - 1{a_i = c} ), r et c appris sans le pli de i. E[d] = V(r) - V(c)."""
    d = np.zeros(len(Y))
    for k in np.unique(plis):
        te, tr = plis == k, plis != k
        r = algo(X[tr], a[tr], Y[tr], noms, graine)
        c = int(np.mean(2 * Y[tr] * (a[tr] == 1)) > np.mean(2 * Y[tr] * (a[tr] == 0)))
        d[te] = 2 * Y[te] * ((a[te] == r(X[te])).astype(float) - (a[te] == c).astype(float))
    return d
