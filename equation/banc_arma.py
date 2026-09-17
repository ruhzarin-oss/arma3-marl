"""
Test B : les memes algorithmes sur les vrais episodes Arma ( criteres : equation/CRITERES_BANC_EQUATION.md ).
  python banc_arma.py /mnt/c/hmt/tmp/equation/arma_choix.parquet resultats/arma.jsonl
Plis = mondes ( graine ) ; IC par reechantillonnage des mondes ; gain declare si le percentile 1 % est > 0.
"""
import json, sys
import numpy as np
import pandas as pd
from algos import ALGOS, ecarts_croises

PERCEPTIONS = ["alarme", "depuis_alarme", "compromis", "vivants", "defenseurs_connus"]
EXTRAS = {"TRAVERSEE": ["vehicule_vu"], "OBS_DUREE": ["reco_vivants"], "EXFIL_ALLURE": ["distance_point"]}
B, GRAINE = 10000, 20260917

df = pd.read_parquet(sys.argv[1])
sortie = open(sys.argv[2], "w")
for (camp, point), g in df.groupby(["campagne", "point"]):
    noms = PERCEPTIONS + EXTRAS.get(point, [])
    X = g[noms].fillna(0).to_numpy(float)
    a, Y, mondes = g["a"].to_numpy(int), g["Y"].to_numpy(int), g["graine"].to_numpy(int)
    variables_qui_varient = [n for n, s in zip(noms, X.std(axis=0)) if s > 0]
    print(f"\n== {camp} {point} : {len(g)} episodes, {len(set(mondes))} mondes, option 1 jouee {a.mean():.2f}, "
          f"issue {Y.mean():.3f} ; perceptions qui varient : {variables_qui_varient or 'aucune'}")
    liste_mondes = sorted(set(mondes))
    rng = np.random.default_rng(GRAINE)
    tirages = [rng.choice(liste_mondes, len(liste_mondes)) for _ in range(B)]
    for nom_algo, algo in ALGOS.items():
        d = ecarts_croises(algo, X, a, Y, noms, mondes, GRAINE)
        par_monde = {w: d[mondes == w] for w in liste_mondes}
        boot = [np.concatenate([par_monde[w] for w in t]).mean() for t in tirages]
        G, p01, p025, p975 = float(d.mean()), *np.percentile(boot, [1, 2.5, 97.5])
        r = algo(X, a, Y, noms, GRAINE)
        res = dict(campagne=camp, point=point, algo=nom_algo, n=len(g), G=G, ic95=[float(p025), float(p975)],
                   p01=float(p01), declare=bool(p01 > 0), variables=r.variables, formule_apprise=r.texte[:600],
                   perceptions_qui_varient=variables_qui_varient)
        sortie.write(json.dumps(res) + "\n")
        print(f"   {nom_algo:8s} G {G:+.3f}  IC95 [{p025:+.3f} ; {p975:+.3f}]  p1% {p01:+.3f}  "
              f"{'GAIN DECLARE' if res['declare'] else 'pas de gain'}  variables {r.variables}  formule : {r.texte[:160]}")
sortie.close()
