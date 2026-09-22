"""L ARCHITECTE APPREND. La moitie Architecte du duel : a partir de TOUS les episodes de phase 2, y compris les pieges
de l Oracle, il reapprend sa regle - uniquement sur ce qu il percoit a la decision - et ne la change que si la nouvelle
fait MIEUX sur des mondes qu elle n a jamais vus. L Oracle lit ensuite la nouvelle regle et en cherche les failles.

La valeur d une regle est la compromission qu on aurait si on la suivait. Les options ayant ete IMPOSEES par les jobs,
equilibrees dans chaque campagne, on l estime sans biais en ponderant par l inverse de la probabilite de l option jouee :
    v_i = Y_i . 1{ option jouee = choix de la regle } / pi( option jouee )
  python -m oracle.autonome.architecte_apprend [--fumee]"""
import json, os, random, re, sys, time
import numpy as np
from sklearn.linear_model import LogisticRegressionCV
from . import config as C, donnees as Dn, architecte as A

NOMS = A.PERMISES + ["perception_etendue"]


def jeu(E):
    """Episodes ou le choix pouvait compter, dans des campagnes ou les deux options ont ete imposees."""
    E = [e for e in E if e.get("atteint_decision") and (e.get("p_compromis") or 0) == 0 and e.get("option_imposee") in (1, 2)]
    par = {}
    for e in E: par.setdefault(e["campagne"], []).append(e["option_imposee"])
    pi2 = {c: np.mean([o == 2 for o in v]) for c, v in par.items()}
    E = [e for e in E if 0.1 <= pi2[e["campagne"]] <= 0.9]
    for e in E: e["pi"] = pi2[e["campagne"]] if e["option_imposee"] == 2 else 1 - pi2[e["campagne"]]
    return E


def matrice(E, noms): return np.column_stack([A.colonne(E, n) for n in noms])


def valeurs(E, c):
    return np.array([e["compromis"] * (e["option_imposee"] == ci) / e["pi"] for e, ci in zip(E, c)])


def logistique(E, noms):
    X = matrice(E, noms); mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1; Z = (X - mu) / sd
    a = np.array([1.0 if e["option_imposee"] == 2 else 0.0 for e in E])[:, None]
    Y = np.array([e["compromis"] for e in E])
    m = LogisticRegressionCV(Cs=10, cv=5, penalty="l2", scoring="neg_log_loss", max_iter=5000, random_state=C.GRAINE).fit(np.hstack([Z, a, a * Z]), Y)
    co = m.coef_[0]; p = Z.shape[1]
    return {"type": "lineaire", "g0": float(co[p]), "g": {n: float(co[p + 1 + j]) for j, n in enumerate(noms)},
            "mu": {n: float(mu[j]) for j, n in enumerate(noms)}, "sd": {n: float(sd[j]) for j, n in enumerate(noms)}}


_BF = {1: "({a} + {b})", 2: "({a} - {b})", 3: "({a} * {b})", 4: "div({a},{b})", 5: "loose_div({a},{b})", 6: "pow_({a},{b})",
       7: "loose_pow({a},{b})", 8: "max({a},{b})", 9: "min({a},{b})", 10: "lt({a},{b})", 11: "gt({a},{b})", 12: "le({a},{b})",
       13: "ge({a},{b})"}
_UF = {14: "sin", 15: "cos", 16: "tan", 17: "sinh", 18: "cosh", 19: "tanh", 20: "log_", 21: "loose_log", 22: "exp", 23: "inv",
       24: "loose_inv", 25: "neg", 26: "abs", 27: "sqrt_", 28: "loose_sqrt"}


def vers_python(arbre, noms):
    """Traduit l ARBRE d EvoGP en expression Python evaluable, constantes a pleine precision. Meme parcours que
    Tree.to_infix ( tableaux retournes, pile, premier depile = premier argument ), mais une syntaxe que Python relit."""
    import torch
    n = int(arbre.subtree_size[0])
    types = [int(x) & 0x7F for x in torch.flip(arbre.node_type[:n], [0]).tolist()]
    vals = torch.flip(arbre.node_value[:n], [0]).tolist()
    pile = []
    for ty, v in zip(types, vals):
        if ty == 0: pile.append(noms[int(v)])
        elif ty == 1: pile.append(f"({float(v)!r})")
        elif ty == 2: pile.append(f"{_UF[int(v)]}({pile.pop()})")
        elif ty == 3: a = pile.pop(); b = pile.pop(); pile.append(_BF[int(v)].format(a=a, b=b))
        elif ty == 4: a = pile.pop(); b = pile.pop(); c = pile.pop(); pile.append(f"si({a},{b},{c})")
    return pile.pop()


def verifier_traduction(arbre, expr, X, noms):
    """La traduction doit calculer LA MEME CHOSE que l arbre sur les donnees ; sinon le candidat est ecarte."""
    import torch
    with torch.no_grad(): ref = arbre.forward(torch.tensor(np.ascontiguousarray(X), dtype=torch.float32, device="cuda")).reshape(-1).cpu().numpy()
    env = dict(A.FONCTIONS); env.update({nm: X[:, j].astype(np.float32) for j, nm in enumerate(noms)})
    with np.errstate(all="ignore"):
        v = np.asarray(eval(expr, {"__builtins__": {}}, env), dtype=np.float32) * np.ones(len(X), dtype=np.float32)
    ok = np.isclose(np.nan_to_num(v, nan=1e30), np.nan_to_num(ref, nan=1e30), rtol=1e-4, atol=1e-4)
    return float(ok.mean())


def evogp(E, noms, pop, gen, graines, parc):
    import torch
    from evogp.tree import Forest, GenerateDescriptor
    from evogp.algorithm import GeneticProgramming, DefaultSelection, DefaultMutation, DefaultCrossover
    from evogp.problem import SymbolicRegression
    from evogp.pipeline import StandardPipeline

    class Parc(SymbolicRegression):
        def evaluate(self, forest): return super().evaluate(forest) - parc * forest.batch_subtree_size[:, 0].float()
    tous = ["attendre"] + noms
    X = np.column_stack([np.array([1.0 if e["option_imposee"] == 2 else 0.0 for e in E]), matrice(E, noms)])
    Y = np.array([e["compromis"] for e in E], dtype=np.float32)
    Xg = torch.tensor(np.ascontiguousarray(X), dtype=torch.float32, device="cuda").contiguous()
    Yg = torch.tensor(Y, device="cuda")[:, None].contiguous()
    meilleur = None
    for s in range(graines):
        torch.manual_seed(C.GRAINE + s); torch.cuda.manual_seed_all(C.GRAINE + s)
        d = GenerateDescriptor(max_tree_len=48, input_len=X.shape[1], output_len=1,
                               using_funcs=["+", "-", "*", "loose_div", "min", "max", "neg", ">", "<", "tanh", "abs"],
                               max_layer_cnt=5, const_samples=[-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0])
        alg = GeneticProgramming(initial_forest=Forest.random_generate(pop_size=pop, descriptor=d), crossover=DefaultCrossover(),
                                 mutation=DefaultMutation(mutation_rate=0.2, descriptor=d.update(max_layer_cnt=3)),
                                 selection=DefaultSelection(survival_rate=0.3, elite_rate=0.01))
        b = StandardPipeline(alg, Parc(datapoints=Xg, labels=Yg), generation_limit=gen, is_show_details=False).run()
        with torch.no_grad(): out = b.forward(Xg).reshape(-1).cpu().numpy()
        mse = float(np.mean((np.nan_to_num(out, nan=0.5) - Y) ** 2))
        if meilleur is None or mse < meilleur[0]: meilleur = (mse, b)
    expr = vers_python(meilleur[1], tous)
    accord = verifier_traduction(meilleur[1], expr, X, tous)
    if accord < 0.99: raise ValueError(f"traduction de l arbre non fidele : {accord:.1%} des points identiques")
    aff = str(meilleur[1].to_infix())
    for j in sorted({int(m) for m in re.findall(r"\bx(\d+)\b", aff)}, reverse=True): aff = re.sub(rf"\bx{j}\b", tous[j], aff)
    return {"type": "formule", "formule": expr, "noms": tous, "affichage": aff, "fidelite_traduction": accord}


def ic_ecart(v1, v0, mondes, B=4000, alpha=0.05):
    r = random.Random(C.GRAINE); d = v1 - v0; M = sorted(set(mondes)); par = {w: d[mondes == w] for w in M}; t = []
    for _ in range(B): t.append(np.concatenate([par[r.choice(M)] for _ in M]).mean())
    t.sort(); return float(d.mean()), t[int(alpha / 2 * B)], t[min(B - 1, int((1 - alpha / 2) * B))]


def apprendre(E, courante, candidats=("logistique", "evogp"), budget=None):
    """Retourne le resultat ; n installe rien. Chaque candidat est appris SANS le monde sur lequel il est juge."""
    budget = budget or C.ARCHITECTE_EVOGP_CV
    E = jeu(E); mondes = np.array([e["graine"] for e in E])
    noms = [n for n in NOMS if matrice(E, [n]).std() > 0]
    v_cour = valeurs(E, A.choix(courante, E))
    choix_cv = {k: np.zeros(len(E), dtype=int) for k in ("toujours_traverser", "toujours_attendre") + tuple(candidats)}
    choix_cv["toujours_traverser"][:] = 1; choix_cv["toujours_attendre"][:] = 2
    ratees = []
    for w in sorted(set(mondes)):
        te, tr = mondes == w, mondes != w
        Etr, Ete = [e for e, k in zip(E, tr) if k], [e for e, k in zip(E, te) if k]
        for k in candidats:
            try:
                r = logistique(Etr, noms) if k == "logistique" else evogp(Etr, noms, **budget)
                choix_cv[k][te] = A.choix(r, Ete)
            except Exception as ex:                     # garde-fou A5 : un candidat qui plante est ecarte, rien ne s arrete
                ratees.append(f"{k} monde {w} : {str(ex)[:80]}"); choix_cv[k][te] = A.choix(courante, Ete)
    # ! 22/09 : sur un monde de test SANS effet, l Architecte a adopte une regle ( IC [-0,058 ; -0,006] ). Choisir le
    # meilleur de plusieurs candidats puis le juger sur les memes donnees surestime le gagnant - le defaut du 19/09.
    # Correction de Bonferroni : l IC de chaque candidat est pris au niveau 1 - 0,05 / k, k = candidats distincts de
    # la regle courante. Le taux de fausses adoptions est MESURE sur des mondes sans effet ( test 12 ).
    distincts = [k for k, c in choix_cv.items() if not np.array_equal(c, A.choix(courante, E))]
    alpha = 0.05 / max(1, len(distincts))
    res = {}
    for k, c in choix_cv.items():
        v = valeurs(E, c); e_, lo, hi = ic_ecart(v, v_cour, mondes, alpha=alpha)
        res[k] = dict(valeur=float(v.mean()), ecart_a_la_courante=float(e_), ic=[float(lo), float(hi)], attend=float(np.mean(c == 2)))
    meilleur = min(res, key=lambda k: res[k]["valeur"])
    adoptee = bool(res[meilleur]["ic"][1] < 0)
    regle = None
    if adoptee:
        if meilleur == "toujours_traverser": regle = {"type": "constante", "option": 1}
        elif meilleur == "toujours_attendre": regle = {"type": "constante", "option": 2}
        elif meilleur == "logistique": regle = logistique(E, noms)
        else: regle = evogp(E, noms, **C.ARCHITECTE_EVOGP_FINAL)
        A.choix(regle, E)                               # garde-fou A3 : la regle installee doit s evaluer sans erreur
    return dict(n=len(E), mondes=len(set(mondes)), niveau_ic=1 - alpha, valeur_courante=float(v_cour.mean()), courante=A.texte(courante),
                candidats=res, meilleur=meilleur, adoptee=adoptee, regle=regle, texte=A.texte(regle) if regle else None,
                candidats_rates=ratees)


if __name__ == "__main__":
    t0 = time.time(); fumee = "--fumee" in sys.argv
    out = f"{C.ETAT_DIR}/architecte_resultat{'_fumee' if fumee else ''}.json"
    json.dump(dict(fini=False, debut=time.time()), open(out, "w"))
    courante = A.charger()
    budget = dict(pop=3000, gen=5, graines=1, parc=1e-3) if fumee else None
    r = apprendre(Dn.utilisables(Dn.episodes(lambda c: True)), courante, budget=budget)
    if fumee and r["adoptee"] and r["meilleur"] == "evogp": r["regle"] = evogp(jeu(Dn.utilisables(Dn.episodes(lambda c: True))), [n for n in NOMS], **budget)
    r.update(fini=True, id=f"{time.strftime('%Y%m%d-%H%M%S')}", duree_s=time.time() - t0)
    json.dump(r, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in r.items() if k != "regle"}, indent=1, ensure_ascii=False)[:3000])
