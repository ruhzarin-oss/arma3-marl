"""Porte S2, la qualite du stratege ( HMT-198 ). Criteres ecrits avant la mesure ( Plane, 03/10 ) : campagnes de 4 jours,
buts de guerre reels ( blocus, centrale, depot ), trois paires de graines neuves.

Q1  l instrument sait distinguer : sur chacune des 3 paires, la doctrine atteint strictement plus de buts que le mauvais
    stratege.
Q2  Qwen : sur au moins 2 paires sur 3, il atteint au moins autant de buts que la doctrine sans perdre plus d hommes.
python -m guerre.porte_campagne"""
import json
import sys
import time

from . import campagne as CA
from .connaissance import index as IX

SORTIE = "/mnt/data/hmt/arsenal/porte_campagne.json"
PAIRES = ((2095, 2096), (2097, 2098), (2099, 2100))      # ( 03/10 07 h 40 ) graines neuves apres les defauts du port, de la garde et de la mobilisation ; 2081 a 2086 REFUSEE, 2087 a 2094 arretee


def main():
    t0 = time.time(); R = {"paires": []}
    print("PORTE S2 DE LA QUALITE DU STRATEGE : 3 paires, 4 jours", flush=True)
    I = IX.ouvrir()
    for gA, gB in PAIRES:
        res = {}
        for chef in ("doctrine", "mauvais", "qwen"):
            r = CA.campagne("Stratis", gA, "Malden", gB, chef, 4, index=I if chef == "qwen" else None)
            res[chef] = r
            print(f"  {gA}/{gB} {chef} : buts {r['bilan']['buts_atteints']} {r['buts']} pertes A {r['bilan']['pertes_A']} "
                  f"B {r['bilan']['pertes_B']} devises {r['bilan']['devises_depensees_A']} ( {r['bilan']['duree_s']} s )", flush=True)
            json.dump(R | {"en_cours": {f"{gA}/{gB}": {c: x for c, x in res.items()}}}, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
        q1 = res["doctrine"]["bilan"]["buts_atteints"] > res["mauvais"]["bilan"]["buts_atteints"]
        q2 = CA.domine(res["qwen"], res["doctrine"])
        R["paires"].append({"graines": [gA, gB], "q1": q1, "q2": q2, **{c: {k: res[c][k] for k in ("buts", "bilan", "tours")} for c in res}})
        print(f"  paire {gA}/{gB} : Q1 {'OUI' if q1 else 'NON'}, Qwen domine ou egale la doctrine : {'OUI' if q2 else 'NON'}", flush=True)
    Q1 = all(p["q1"] for p in R["paires"]); Q2 = sum(p["q2"] for p in R["paires"]) >= 2
    verdict = "FRANCHIE" if (Q1 and Q2) else "REFUSEE"
    R.update(Q1=Q1, Q2=Q2, verdict=verdict, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"Q1 {'OUI' if Q1 else 'NON'} ; Q2 {'OUI' if Q2 else 'NON'}")
    print(f"PORTE S2 DE LA QUALITE DU STRATEGE : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_CAMPAGNE", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
