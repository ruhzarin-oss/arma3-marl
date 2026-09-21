"""Sonde d ingenierie ( pas de lecture ) : fonctions disponibles dans EvoGP, et temps par generation selon la
population, sur une table de la taille de la notre ( ~900 lignes, ~20 variables ). Sert a fixer le budget AVANT
d ecrire les criteres."""
import time, inspect, numpy as np, torch
import evogp, evogp.tree as T
from evogp.tree import Forest, GenerateDescriptor
from evogp.algorithm import GeneticProgramming, DefaultSelection, DefaultMutation, DefaultCrossover
from evogp.problem import SymbolicRegression
from evogp.pipeline import StandardPipeline
src = inspect.getsource(T)
import re
fonctions = sorted(set(re.findall(r'"([a-z]{2,6}|[+\-*/<>])"', src)))
print("chaines candidates de fonctions dans evogp.tree :", fonctions[:80])
try:
    from evogp.tree.utils import FUNCS_NAMES
    print("FUNCS_NAMES", FUNCS_NAMES)
except Exception as e:
    print("pas de FUNCS_NAMES :", e)
rng = np.random.default_rng(0)
X = torch.tensor(rng.normal(size=(900, 20)), dtype=torch.float32, device="cuda").contiguous()
Y = torch.tensor((rng.random(900) < 0.16).astype(np.float32), device="cuda")[:, None].contiguous()
pb = SymbolicRegression(datapoints=X, labels=Y)
for pop in (20000, 100000, 300000):
    d = GenerateDescriptor(max_tree_len=64, input_len=20, output_len=1, using_funcs=["+", "-", "*", "/", "min", "max", "neg", ">"],
                           max_layer_cnt=6, const_samples=[-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0])
    alg = GeneticProgramming(initial_forest=Forest.random_generate(pop_size=pop, descriptor=d), crossover=DefaultCrossover(),
                             mutation=DefaultMutation(mutation_rate=0.2, descriptor=d.update(max_layer_cnt=4)),
                             selection=DefaultSelection(survival_rate=0.3, elite_rate=0.01))
    t0 = time.time(); StandardPipeline(alg, pb, generation_limit=10, is_show_details=False).run(); dt = (time.time() - t0) / 10
    print(f"population {pop:>7} : {dt:.3f} s par generation ; memoire GPU {torch.cuda.max_memory_allocated() / 1e9:.1f} Go")
