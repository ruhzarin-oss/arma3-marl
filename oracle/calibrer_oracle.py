"""Calibrage sur graines disjointes ( rep >= 1000 ) : puissance de la confirmation pour l'oracle PARFAIT, et reperes uniforme / cases."""
import numpy as np
from mondes import MONDES, evaluer, regret
from oracles_simples import parfait, uniforme, cases
for monde in MONDES:
    for nom, fn, reps in (("parfait", parfait, 200), ("uniforme", uniforme, 40), ("cases_plan", cases, 40)):
        R = [evaluer(monde, 1000 + r, nom, *fn(monde, 1000 + r)) for r in range(reps)]
        print(f"{monde:16s} {nom:10s} regions {np.mean([x['regions_trouvees'] for x in R]):.2f}/{R[0]['K']}  fausses {sum(x['fausses'] for x in R)}/{reps}  "
              f"part budget en faille {np.mean([x['part_budget_en_faille'] for x in R]):.3f}")
print("aire des failles ( r > 0,10 ) :", {m: float(np.mean(regret(m, np.random.default_rng(0).random((200000, 3))) > 0.10)) for m in MONDES})
