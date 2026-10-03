"""Porte de la prise de l objectif ( HMT-198 ). Criteres ecrits avant la mesure ( Plane, 03/10 06 h 25 ) : Stratis ( 2131 )
contre Malden ( 2132 ), echelle 20, les troupes de membres_a_projeter, 3 graines de mission par cas.

P1  controle positif ( 100 hommes contre port01 ) : la garde rompt ou est aneantie sur au moins une mission ; sur
    chacune de celles-la, arrives = assaillants encore actifs ( > 0 ), dommages = arrives / partis, le port frappe de
    ces dommages.
P2  controle negatif ( 24 hommes contre base01 ) : une garde qui ne rompt pas : 0 arrive, aucun dommage.
P3  l echec reste un echec ( 400 hommes contre base01 ) : si la garde tient, arrives = 0.
python -m guerre.porte_prise [ graine_A graine_B ]"""
import json
import pickle
import sys
import time

import numpy as np

from monde import archipel as AR, tests as T
from . import expedition as EX, frappes as FR, logistique as LO, moteur as GM

SORTIE = "/mnt/data/hmt/arsenal/porte_prise.json"


def cas(octA, octB, n, oid, base):
    w = pickle.loads(octA); nums = GM.mobiliser(w, n, ids=EX.membres_a_projeter(w, n)); LO.emporter(w, nums)
    cp = EX.corps(w, nums); out = []
    for sg in range(3):
        wb = pickle.loads(octB); r = EX.assaut(wb, "Stratis", cp, oid, seed=(base + sg,)); m = r["mission"]
        rouges = np.nonzero(m.h["side"] == 1)[0]
        out.append({"garde_rompue": bool(r["garde_rompue"]), "issue": m.issue, "partis": len(cp["numero"]),
                    "actifs": int(m.h["actif"][rouges].sum()), "arrives": r["arrives"], "dommages": r["dommages"],
                    "degat_objectif": float(FR._etat(wb).get(oid, 0.0)), "pertes_A": len(r["sorts"])})
    return out


def main(gA=2131, gB=2132):
    t0 = time.time(); R = {}
    print(f"PORTE DE LA PRISE : Stratis {gA} contre Malden {gB}", flush=True)
    wA = AR.creer_ile("Stratis", gA, 20); T.jours(wA, 1); wB = AR.creer_ile("Malden", gB, 20); T.jours(wB, 1)
    octA, octB = pickle.dumps(wA, protocol=4), pickle.dumps(wB, protocol=4)
    p1 = cas(octA, octB, 100, "port01", 9900); p2 = cas(octA, octB, 24, "base01", 9910); p3 = cas(octA, octB, 400, "base01", 9920)
    rompues = [x for x in p1 if x["garde_rompue"]]
    P1 = bool(rompues) and all(x["arrives"] == x["actifs"] > 0 and abs(x["dommages"] - min(1.0, x["arrives"] / x["partis"])) <= 1e-12
                               and abs(x["degat_objectif"] - x["dommages"]) <= 1e-9 for x in rompues)
    P2 = all(x["arrives"] == 0 and x["dommages"] == 0.0 and x["degat_objectif"] == 0.0 for x in p2 if not x["garde_rompue"]) \
        and any(not x["garde_rompue"] for x in p2)
    P3 = all(x["arrives"] == 0 for x in p3 if not x["garde_rompue"])
    for k, v, l in (("P1", P1, p1), ("P2", P2, p2), ("P3", P3, p3)):
        R[k] = {"ok": bool(v), "missions": l}
        print(f"  {k} : {'OUI' if v else 'NON'} {json.dumps(l)[:700]}", flush=True)
    verdict = "FRANCHIE" if (P1 and P2 and P3) else "REFUSEE"
    R.update(verdict=verdict, graines=[gA, gB], duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE DE LA PRISE : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_PRISE", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(main(int(a[0]), int(a[1])) if len(a) >= 2 else main())
