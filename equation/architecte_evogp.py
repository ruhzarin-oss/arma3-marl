"""
Architecte EvoGP « puissant » pour la boucle Arma ( equation/PROTOCOLE_BOUCLE_EVOGP_P5.md ).
Apprend sur psi = 2Y(2a-1) des episodes d'EXPLORATION ( option imposee, equilibree ), choisit la parcimonie par
validation croisee par monde, et rend une formule traduisible en codes pour la mission.
"""
import numpy as np, torch
from evogp.tree import Forest, GenerateDescriptor
from evogp.algorithm import GeneticProgramming, DefaultSelection, DefaultMutation, DefaultCrossover
from evogp.problem import SymbolicRegression
from evogp.pipeline import StandardPipeline
from formule import analyser, encoder, evaluer_codes, texte_lisible, CONSTANTES

PERCEPTIONS = ["alarme", "depuis_alarme", "compromis", "vivants", "defenseurs_connus"]
POPULATION, GENERATIONS = 300000, 300          # « il faut lui donner de la puissance » ( Younes, 17/09 )
PARCIMONIES = [0.001, 0.003, 0.01, 0.03]


def ajuster(X, a, Y, parcimonie, graine):
    class RP(SymbolicRegression):
        def evaluate(self, forest):
            return super().evaluate(forest) - parcimonie * forest.batch_subtree_size[:, 0].float()
    torch.manual_seed(graine); torch.cuda.manual_seed_all(graine)
    psi = 2.0 * Y * (2 * a - 1)
    pb = RP(datapoints=torch.tensor(np.ascontiguousarray(X), dtype=torch.float32, device="cuda").contiguous(),
            labels=torch.tensor(psi, dtype=torch.float32, device="cuda")[:, None].contiguous())
    d = GenerateDescriptor(max_tree_len=32, input_len=X.shape[1], output_len=1, using_funcs=["+", "-", "*", "min", "max", "neg", ">"],
                           max_layer_cnt=5, const_samples=CONSTANTES)
    alg = GeneticProgramming(initial_forest=Forest.random_generate(pop_size=POPULATION, descriptor=d), crossover=DefaultCrossover(),
                             mutation=DefaultMutation(mutation_rate=0.2, descriptor=d.update(max_layer_cnt=3)),
                             selection=DefaultSelection(survival_rate=0.3, elite_rate=0.01))
    best = StandardPipeline(alg, pb, generation_limit=GENERATIONS, is_show_details=False).run()
    arbre = analyser(str(best.to_infix()), [f"x{j}" for j in range(X.shape[1])])
    codes = encoder(arbre)
    return arbre, codes


def regle(codes, X):
    return np.array([1 if evaluer_codes(codes, x) > 0 else 0 for x in X])


def gain_croise(X, a, Y, mondes, parcimonie, graine):
    d = np.zeros(len(Y))
    for w in np.unique(mondes):
        te, tr = mondes == w, mondes != w
        _, codes = ajuster(X[tr], a[tr], Y[tr], parcimonie, graine)
        c = int(np.mean(2 * Y[tr] * (a[tr] == 1)) > np.mean(2 * Y[tr] * (a[tr] == 0)))
        d[te] = 2 * Y[te] * ((a[te] == regle(codes, X[te])).astype(float) - (a[te] == c).astype(float))
    return d


def apprendre(X, a, Y, mondes, graine, B=2000):
    """Rend : formule finale, codes, parcimonie choisie, G croise et IC par mondes pour chaque parcimonie."""
    rapport = {}
    rng = np.random.default_rng(graine)
    liste = sorted(set(mondes.tolist()))
    tirages = [rng.choice(liste, len(liste)) for _ in range(B)]
    for lam in PARCIMONIES:
        d = gain_croise(X, a, Y, mondes, lam, graine)
        par = {w: d[mondes == w] for w in liste}
        boot = [np.concatenate([par[w] for w in t]).mean() for t in tirages]
        rapport[lam] = dict(G=float(d.mean()), ic95=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))])
    meilleur = max(PARCIMONIES, key=lambda l: (round(rapport[l]["G"], 6), l))   # egalite : la plus forte parcimonie
    arbre, codes = ajuster(X, a, Y, meilleur, graine)
    return dict(parcimonie=meilleur, codes=codes, formule=texte_lisible(arbre, PERCEPTIONS), rapport=rapport)
