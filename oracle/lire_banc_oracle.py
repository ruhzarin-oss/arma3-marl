"""Lecture du banc des oracles ( criteres : oracle/CRITERES_BANC_ORACLE.md ), une fois tout calcule.
  python lire_banc_oracle.py resultats/*.jsonl"""
import json, sys, glob
import numpy as np
from collections import defaultdict
L = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
par = defaultdict(list)
for x in L:
    if x["rep"] < 1000: par[(x["oracle"], x["monde"])].append(x)
oracles = sorted({o for o, _ in par}); mondes = ["W0_nul", "W1_aiguille", "W2_quatre", "W3_large_faible"]
rng = np.random.default_rng(20260917)
def ic(v, B=10000):
    v = np.array(v, float); b = [rng.choice(v, len(v)).mean() for _ in range(B)]
    return np.percentile(b, 2.5), np.percentile(b, 97.5)
print("oracle              monde             reps  decouverte  regions [IC95]            reps_avec_fausse  budget_en_faille  duree_s")
for o in oracles:
    for m in mondes:
        X = par.get((o, m), [])
        if not X: continue
        reg = [x["regions_trouvees"] for x in X]; lo, hi = ic(reg)
        print(f"{o:19s} {m:17s} {len(X):4d}  {sum(r > 0 for r in reg):3d}/{len(X):<3d}     {np.mean(reg):.2f}/{X[0]['K']} [{lo:.2f} ; {hi:.2f}]    "
              f"{sum(x['fausses'] > 0 for x in X):3d}/{len(X):<3d}          {np.mean([x['part_budget_en_faille'] for x in X]):.3f}          {np.mean([x.get('duree_s', 0) for x in X]):.1f}")
print("\n== CRITERES ECRITS AVANT")
U = lambda m: par.get(("uniforme", m), [])
for o in oracles:
    if o in ("uniforme", "parfait"): continue
    if any(len(par.get((o, m), [])) < 20 for m in mondes) or any(len(U(m)) < 20 for m in mondes):
        print(f"   {o} : INCOMPLET"); continue
    nul = sum(x["declares"] > 0 for x in par[(o, "W0_nul")])
    d1 = sum(x["regions_trouvees"] > 0 for x in par[(o, "W1_aiguille")]); d1u = sum(x["regions_trouvees"] > 0 for x in U("W1_aiguille"))
    r2 = np.mean([x["regions_trouvees"] for x in par[(o, "W2_quatre")]]); r2u = np.mean([x["regions_trouvees"] for x in U("W2_quatre")])
    utile = nul <= 1 and (d1 >= d1u + 5 or r2 >= r2u + 1.0)
    print(f"   {o} : controle nul {nul}/20 ( <= 1 ) ; aiguille {d1}/20 contre uniforme {d1u}/20 ( +5 ? {'OUI' if d1 >= d1u + 5 else 'NON'} ) ; "
          f"quatre failles {r2:.2f} contre uniforme {r2u:.2f} ( +1 ? {'OUI' if r2 >= r2u + 1 else 'NON'} )  ->  {'UTILE' if utile else 'PAS UTILE'}")
print("\n== COMPARAISONS AU PLAN ( cases ), regions trouvees, ecart et IC95 par reechantillonnage des repetitions")
for o in oracles:
    if o in ("cases_plan", "parfait", "uniforme"): continue
    for m in ("W1_aiguille", "W2_quatre", "W3_large_faible"):
        a = [x["regions_trouvees"] for x in par.get((o, m), [])]; b = [x["regions_trouvees"] for x in par.get(("cases_plan", m), [])]
        if len(a) < 20 or len(b) < 20: continue
        d = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(10000)]
        print(f"   {o:19s} - cases_plan, {m:17s} : {np.mean(a) - np.mean(b):+.2f} [{np.percentile(d, 2.5):+.2f} ; {np.percentile(d, 97.5):+.2f}]")
