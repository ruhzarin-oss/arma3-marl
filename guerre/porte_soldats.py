"""Porte 3a des blesses ( HMT-194 ). Criteres ecrits avant la mesure ( Plane ) : Malden ( 1971 ), echelle 20, 12 soldats
mobilises et suivis, dommages 0 ; 0,3 ; 0,49 ; 0,5 ; 0,7 ; 0,95 ( deux soldats chacun ).
S1  sous 0,5 : au front ; a 0,5 et au-dela : evacues ( residents, non absents, etat blesse ) avec une blessure balistique
    du domaine 16, cause combat, ISS = la formule ( 9 ; 35 ; 68 ).
S2  un second releve au meme dommage n evacue ni ne blesse personne une deuxieme fois.
S3  les munitions des evacues restent au front ; anomalies() vide.
S4  sans evacuation ( tous sous 0,5 ), identique au bit au jumeau sur 2 jours.
python -m guerre.porte_soldats"""
import json
import pickle
import sys
import time

from monde import archipel as AR, population as PO, tests as T
from monde.pays import d25_armee as A
from . import logistique as LO, moteur as GM, soldats as SO
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_soldats.json"
DOMMAGES = (0.0, 0.3, 0.49, 0.5, 0.7, 0.95) * 2


def blessures(w, depuis):
    return [e for e in list(w.pays.socle.journal.recents)[depuis:] if e.get("type") == "blessure"]


def main():
    t0 = time.time(); R = {}
    print("PORTE 3a DES BLESSES : Malden 1971, 12 soldats", flush=True)
    w0 = AR.creer_ile("Malden", 1971, 20)
    nums = GM.mobiliser(w0, 12); LO.emporter(w0, nums)
    oct_ = pickle.dumps(w0, protocol=4)
    w = pickle.loads(oct_); f = GM._front(w); fr = LO.front(w); d = w.pays.domaines[A.DOMAINE]
    GM.suivre(w, [(n, 1000.0 + k, 1000.0, dg) for k, (n, dg) in enumerate(zip(nums, DOMMAGES))])
    stock_front = sum(float(fr.stock[d.bids[b]]) for b in A.NOMS_MUNITIONS)
    j0 = len(w.pays.socle.journal.recents)
    ev = SO.evacuer_blesses(w)
    bl = blessures(w, j0)
    t = w.table
    attendu = {n: SO.iss_de(dg) for n, dg in zip(nums, DOMMAGES) if dg >= SO.SEUIL_EVAC}
    restes = [n for n, dg in zip(nums, DOMMAGES) if dg < SO.SEUIL_EVAC]
    ok_restes = all(f[n]["etat"] == "front" and t.statut[f[n]["i"]] == PO.ABSENT for n in restes)
    ok_evac = all(f[n]["etat"] == "blesse" and t.statut[f[n]["i"]] == PO.RESIDENT and f[n]["i"] not in w.absents
                  for n in attendu)
    par_hab = {e["habitant"]: e for e in bl}
    ok_med = all(f[n]["i"] in par_hab and par_hab[f[n]["i"]]["iss"] == iss and par_hab[f[n]["i"]]["cause"] == "combat"
                 and par_hab[f[n]["i"]]["nature"] == "balistique" for n, iss in attendu.items())
    S1 = ok_restes and ok_evac and ok_med and sorted(attendu.values()) == sorted([9, 9, 35, 35, 68, 68]) and len(ev) == 6
    R["S1"] = {"ok": S1, "evacues": len(ev), "iss": sorted(i for _n, i, _c in ev), "restent": ok_restes, "evac": ok_evac,
               "medecine": ok_med, "blessures_notees": len(bl)}
    print(f"  S1 seuil : {'OUI' if S1 else 'NON'} {R['S1']}", flush=True)
    j1 = len(w.pays.socle.journal.recents)
    ev2 = SO.evacuer_blesses(w)
    S2 = ev2 == [] and not blessures(w, j1)
    R["S2"] = {"ok": S2, "second": ev2}
    print(f"  S2 une seule fois : {'OUI' if S2 else 'NON'}", flush=True)
    stock_apres = sum(float(fr.stock[d.bids[b]]) for b in A.NOMS_MUNITIONS)
    an = A.anomalies(w.pays)
    S3 = abs(stock_apres - stock_front) <= 1e-9 and not an
    R["S3"] = {"ok": S3, "front": [stock_front, stock_apres], "anomalies": an[:5]}
    print(f"  S3 munitions : {'OUI' if S3 else 'NON'} {R['S3']}", flush=True)
    wa, wb = pickle.loads(oct_), pickle.loads(oct_)
    for x in (wa, wb): GM.suivre(x, [(n, 1000.0, 1000.0, 0.3) for n in nums])
    SO.evacuer_blesses(wa)
    ident = True
    for _ in range(2):
        T.jours(wa, 1); T.jours(wb, 1)
        if PE.empreinte_etendue(wa) != PE.empreinte_etendue(wb): ident = False
    R["S4"] = {"ok": ident}
    print(f"  S4 identite : {'OUI' if ident else 'NON'}", flush=True)
    T.jours(w, 3)
    morts = sum(1 for n in attendu if not w.habitants[f[n]["i"]].vivant)
    R["info"] = {"evacues": len(attendu), "morts_en_3_jours": morts}
    print(f"  info : {morts} morts sur {len(attendu)} evacues en 3 jours", flush=True)
    verdict = "FRANCHIE" if all(R[k]["ok"] for k in ("S1", "S2", "S3", "S4")) else "REFUSEE"
    R.update(verdict=verdict, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 3a DES BLESSES : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_SOLDATS", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
