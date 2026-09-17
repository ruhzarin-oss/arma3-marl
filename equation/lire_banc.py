"""
Lecture du test A ( criteres : equation/CRITERES_BANC_EQUATION.md ). Une seule lecture, quand tout est calcule.
  python lire_banc.py resultats/synthetique.jsonl
"""
import json, sys
from collections import defaultdict

FORMULES, TAILLES, REPS = ["F0", "F1", "F2", "F3"], [200, 500, 1000], 20
lignes = [json.loads(l) for l in open(sys.argv[1])]
par = defaultdict(list)
for j in lignes:
    par[(j["algo"], j["formule"], j["n"])].append(j)
algos = sorted({j["algo"] for j in lignes})

moy = lambda v: sum(v) / len(v) if v else float("nan")
print("== TEST A, banc synthetique : une ligne par ( algo, formule, n )")
print("algo     form    n  reps  declare  retrouvee  accord  vraies  leurres  niveau_seul  gain_vrai/ideal  duree_s")
for al in algos:
    for fo in FORMULES:
        for n in TAILLES:
            L = par.get((al, fo, n), [])
            if not L:
                continue
            acc = [j["accord"] for j in L if j["accord"] is not None]
            vraies = moy([len(j["vraies_trouvees"]) / 2 for j in L]) if fo != "F0" else float("nan")
            print(f"{al:8s} {fo:3s} {n:5d} {len(L):4d}  {sum(j['declare'] for j in L):4d}/{len(L):<3d} "
                  f"{(str(sum(bool(j['retrouvee']) for j in L)) + '/' + str(len(L))) if fo != 'F0' else '   -  ':>8s}  "
                  f"{moy(acc):6.3f}  {vraies:6.2f}  {moy([len(j['leurres']) for j in L]):6.2f}  "
                  f"{moy([j['niveau_seul'] for j in L]):8.2f}     {moy([j['gain_vrai'] for j in L]):+.3f}/{moy([j['gain_ideal'] for j in L]):+.3f}  "
                  f"{moy([j['duree_s'] for j in L]):7.1f}")

print("\n== CRITERES ECRITS AVANT")
for al in algos:
    manque = [k for k in [(al, fo, n) for fo in FORMULES for n in TAILLES] if len(par.get(k, [])) < REPS]
    if manque:
        print(f"   {al} : INCOMPLET ( {len(manque)} cases sous {REPS} repetitions ), aucun critere lu")
        continue
    ok_formules = {fo: sum(bool(j["retrouvee"]) for j in par[(al, fo, 500)]) >= 18 for fo in ["F1", "F2", "F3"]}
    ok_nul = {n: sum(j["declare"] for j in par[(al, "F0", n)]) <= 1 for n in TAILLES}
    retenu = all(ok_formules.values()) and all(ok_nul.values())
    print(f"   {al} : F1/F2/F3 retrouvees >= 18/20 a n = 500 : "
          + ", ".join(f"{fo} {'OUI' if v else 'NON'}" for fo, v in ok_formules.items())
          + " ; F0 declarees <= 1/20 : " + ", ".join(f"n={n} {'OUI' if v else 'NON'}" for n, v in ok_nul.items())
          + f"  ->  {'RETENU' if retenu else 'NON RETENU'}")

print("\n== EXEMPLES DE FORMULES APPRISES ( rep 0, n = 1000 )")
for al in algos:
    for fo in FORMULES:
        L = [j for j in par.get((al, fo, 1000), []) if j["rep"] == 0]
        if L:
            print(f"   {al} {fo} : {L[0]['formule_apprise'][:300]}")
