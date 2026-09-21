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


def evogp(X, a, Y, noms, graine, parcimonie=0.001):
    """Programmation genetique sur GPU ( EvoGP, EMI-Group ) sur psi ; parcimonie ajoutee a la fitness ; regle = formule > 0.
    Amendement 1 des criteres : population 5000, 50 generations, fonctions + - * min max neg >, parcimonie 0,001 par noeud."""
    import torch
    from evogp.tree import Forest, GenerateDescriptor
    from evogp.algorithm import GeneticProgramming, DefaultSelection, DefaultMutation, DefaultCrossover
    from evogp.problem import SymbolicRegression
    from evogp.pipeline import StandardPipeline

    class RegressionParcimonieuse(SymbolicRegression):
        def evaluate(self, forest):
            return super().evaluate(forest) - parcimonie * forest.batch_subtree_size[:, 0].float()

    torch.manual_seed(graine)
    torch.cuda.manual_seed_all(graine)
    psi = pseudo_issue(a, Y)
    Xg = torch.tensor(np.ascontiguousarray(X), dtype=torch.float32, device="cuda").contiguous()   # les noyaux CUDA exigent un tableau contigu
    Yg = torch.tensor(psi, dtype=torch.float32, device="cuda")[:, None].contiguous()
    pb = RegressionParcimonieuse(datapoints=Xg, labels=Yg)
    d = GenerateDescriptor(max_tree_len=32, input_len=X.shape[1], output_len=1,
                           using_funcs=["+", "-", "*", "min", "max", "neg", ">"], max_layer_cnt=5,
                           const_samples=[-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0])
    alg = GeneticProgramming(initial_forest=Forest.random_generate(pop_size=5000, descriptor=d), crossover=DefaultCrossover(),
                             mutation=DefaultMutation(mutation_rate=0.2, descriptor=d.update(max_layer_cnt=3)),
                             selection=DefaultSelection(survival_rate=0.3, elite_rate=0.01))
    best = StandardPipeline(alg, pb, generation_limit=50, is_show_details=False).run()
    texte = str(best.to_infix())          # to_sympy_expr refuse le « > » dans un produit
    variables = []
    for j in sorted({int(m) for m in re.findall(r"\bx(\d+)\b", texte)}, reverse=True):
        variables.append(noms[j])
        texte = re.sub(rf"\bx{j}\b", noms[j], texte)

    def regle(Xn, best=best):
        with torch.no_grad():
            out = best.forward(torch.tensor(np.ascontiguousarray(Xn), dtype=torch.float32, device="cuda").contiguous())
        return (out.reshape(-1).cpu().numpy() > 0)
    return Regle(regle, variables, texte)


def evogp_p01(X, a, Y, noms, graine):
    """EvoGP avec une parcimonie 10 fois plus forte ( 0,01 par noeud ), variante declaree avant calcul."""
    return evogp(X, a, Y, noms, graine, parcimonie=0.01)


def _pysr_export_tolerant():
    """Amendement 3 : l export d une formule vers sympy peut planter ( sympy, « pop from an empty set », sur certaines expressions imbriquees de min, max et
    greater ) et il faisait tomber tout l ajustement. On le rend tolerant : en cas d echec la colonne sympy recoit un symbole neutre. La recherche, la perte, le
    score et la selection de PySR ne passent pas par sympy et ne sont pas touches."""
    import sympy, pysr.export_sympy as es, pysr.export as ex
    if getattr(es, "_tolerant", False): return
    origine = es.pysr2sympy
    def sur(*args, **kw):
        try: return origine(*args, **kw)
        except Exception: return sympy.Symbol("export_sympy_impossible")
    es.pysr2sympy = sur; ex.pysr2sympy = sur; es._tolerant = True


def _pysr_evaluer(texte, X, noms):
    """Evalue la formule de PySR ( sa chaine, en notation infixe ) sans passer par sympy. Controle d equivalence avec model.predict : amendement 3."""
    env = {"min": np.minimum, "max": np.maximum, "neg": np.negative, "greater": lambda x, y: np.greater(x, y).astype(float), "__builtins__": {}}
    env.update({n: X[:, k] for k, n in enumerate(noms)})
    return np.broadcast_to(np.asarray(eval(texte, env), dtype=float), (len(X),))


def pysr(X, a, Y, noms, graine):
    """Regression symbolique PySR ( SymbolicRegression.jl, CPU, 1 thread ) sur psi ; regle = formule > 0. Amendement 2 des criteres :
    memes fonctions que gplearn et EvoGP ( + - * min max neg > ), parcimonie 0,001, taille 25 au plus, mode serie deterministe."""
    from pysr import PySRRegressor
    _pysr_export_tolerant()
    psi = pseudo_issue(a, Y)
    m = PySRRegressor(niterations=PYSR_ITERATIONS, populations=8, population_size=30, ncycles_per_iteration=300, maxsize=25,
                      binary_operators=["+", "-", "*", "min", "max", "greater"], unary_operators=["neg"],
                      parsimony=0.001, elementwise_loss="L2DistLoss()", model_selection="best",
                      parallelism="serial", deterministic=True, random_state=int(graine % (2 ** 31 - 1)),
                      progress=False, verbosity=0, temp_equation_file=True)
    m.fit(X, psi, variable_names=list(noms))
    texte = str(m.get_best()["equation"])
    variables = [n for n in noms if re.search(r"\b" + re.escape(n) + r"\b", texte)]
    return Regle(lambda Xn, texte=texte, noms=list(noms): _pysr_evaluer(texte, Xn, noms) > 0, variables, texte)


PYSR_ITERATIONS = 30      # fixe par l amendement 2 apres la fumee de DUREE ( graines decalees ), avant tout calcul du banc


def dsr(X, a, Y, noms, graine):
    """Deep Symbolic Regression ( dso-org : reseau recurrent + gradient de politique, CPU, TensorFlow 1.14 ) sur psi ; regle = formule > 0.
    Amendement 2 : memes fonctions que les autres. Les jetons « min » et « max » de DSO sont declares d arite 1 ( defaut amont : inutilisables ) et DSO n a
    pas de comparaison : on ajoute trois jetons binaires min2, max2 et gt2 ( x > y ). Constantes fixes d EvoGP, pas de jeton « const » ( optimisation interne
    trop lente ), expressions de 25 jetons au plus, budget DSR_ECHANTILLONS expressions par lots de 500."""
    import os, warnings
    warnings.filterwarnings("ignore")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    from dso import DeepSymbolicRegressor
    from dso.functions import function_map
    from dso.library import Token
    if "gt2" not in function_map:
        function_map["min2"] = Token(np.minimum, "min2", arity=2, complexity=1)
        function_map["max2"] = Token(np.maximum, "max2", arity=2, complexity=1)
        function_map["gt2"] = Token(lambda x, y: np.greater(x, y).astype(np.float32), "gt2", arity=2, complexity=1)
    psi = pseudo_issue(a, Y)
    config = {"task": {"task_type": "regression", "function_set": ["add", "sub", "mul", "neg", "min2", "max2", "gt2", -1.0, -0.5, -0.25, 0.25, 0.5, 1.0],
                       "metric": "inv_nrmse", "metric_params": [1.0], "threshold": 1e-12, "protected": False},
              "training": {"n_samples": DSR_ECHANTILLONS, "batch_size": 500, "n_cores_batch": 1, "verbose": False, "early_stopping": False},
              "prior": {"length": {"min_": 1, "max_": 25, "on": True}},
              "experiment": {"seed": int(graine % (2 ** 31 - 1)), "logdir": None},
              "logging": {"save_summary": False, "save_all_iterations": False, "save_positional_entropy": False, "save_pareto_front": False, "save_cache": False, "hof": None}}
    m = DeepSymbolicRegressor(config)
    m.fit(X, psi)
    expr = ",".join(str(t) for t in m.program_.traversal)          # notation prefixe : sympy ne connait pas min2, max2, gt2
    num = sorted({int(k) for k in re.findall(r"\bx(\d+)\b", expr)}, reverse=True)
    variables = [noms[k - 1] for k in sorted(num) if 1 <= k <= len(noms)]
    for k in num:
        if 1 <= k <= len(noms): expr = re.sub(rf"\bx{k}\b", noms[k - 1], expr)
    return Regle(lambda Xn, m=m: np.asarray(m.predict(Xn)).reshape(-1) > 0, variables, expr)


DSR_ECHANTILLONS = 20000  # fixe par l amendement 2 apres la fumee de DUREE, avant tout calcul du banc


def dsr_100k(X, a, Y, noms, graine):
    """DSR avec un budget cinq fois plus grand ( 100 000 expressions ), variante declaree avant tout calcul ( amendement 2 ) : sensibilite au budget."""
    global DSR_ECHANTILLONS
    ancien, DSR_ECHANTILLONS = DSR_ECHANTILLONS, 100000
    try: return dsr(X, a, Y, noms, graine)
    finally: DSR_ECHANTILLONS = ancien


ALGOS = {"l1": l1, "arbre": arbre, "gplearn": gplearn, "evogp": evogp, "evogp_p01": evogp_p01, "pysr": pysr, "dsr": dsr, "dsr_100k": dsr_100k}


def ecarts_croises(algo, X, a, Y, noms, plis, graine):
    """d_i = 2 Y_i ( 1{a_i = r(x_i)} - 1{a_i = c} ), r et c appris sans le pli de i. E[d] = V(r) - V(c)."""
    d = np.zeros(len(Y))
    for k in np.unique(plis):
        te, tr = plis == k, plis != k
        r = algo(X[tr], a[tr], Y[tr], noms, graine)
        c = int(np.mean(2 * Y[tr] * (a[tr] == 1)) > np.mean(2 * Y[tr] * (a[tr] == 0)))
        d[te] = 2 * Y[te] * ((a[te] == r(X[te])).astype(float) - (a[te] == c).astype(float))
    return d
