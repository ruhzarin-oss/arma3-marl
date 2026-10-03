"""Porte 4b-2 de l operation, du depart au retour ( HMT-197 ). Criteres ecrits avant la mesure ( Plane, 03/10 ) :
A = Stratis ( 2051 ), B = Malden ( 2052 ), echelle 20.

O1  le refus : sans transport ou au-dela de sa capacite, refuse avec sa raison ; aucun soldat mobilise, aucun carburant.
O2  la chaine par la mer ( 2 chalands, 60 hommes ) : assaut au pas d arrivee, pas avant ; avant le retour aucun blesse de
    A evacue, aucun survivant rentre ; au pas du retour, blesses evacues, survivants residents, carburant du retour brule.
O3  le parachutage ( 1 C-130J, 60 hommes ) : l assaut part a 1,5 km de l objectif ; 65 parachutistes refuses.
O4  les morts : l arme de chaque mort de A sort du Parc ( detruit ), ses coups en perte_au_combat ; anomalies vides
    ( amende 03/10, M5 : lues apres deux jours du moteur ).
O5  identite : sans operation, A et B identiques au bit sur 2 jours.
python -m guerre.porte_operation [ graine_A graine_B ]"""
import json
import math
import pickle
import sys
import time

from monde import archipel as AR, population as PO, tests as T
from monde.pays import d25_armee as A, d26_armee_soutien as S
from . import expedition as EX, logistique as LO, moteur as GM, objectifs as OB, projection as PR
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_operation.json"


def sorties(w, motif):
    d = w.pays.domaines[A.DOMAINE]
    return sum(v for (b, m), v in d.sorties.items() if m == motif)


def evacues(w):
    return {int(x[1]) for x in S._dom(w.pays).evacuations}


def jusqu_a(wA, wB, pas, journal=None):
    while int(wA.pas) < pas:
        wA.pas_suivant(); wB.pas_suivant()
        ev = EX.avancer_operations(wA, wB)
        if journal is not None and ev: journal.append((int(wA.pas), ev))


def main(gA=2051, gB=2052):
    t0 = time.time(); R = {}
    print(f"PORTE 4b-2 DE L OPERATION : Stratis {gA} contre Malden {gB}", flush=True)
    wA0 = AR.creer_ile("Stratis", gA, 20); T.jours(wA0, 1)
    wB0 = AR.creer_ile("Malden", gB, 20); T.jours(wB0, 1)
    octA0, octB = pickle.dumps(wA0, protocol=4), pickle.dumps(wB0, protocol=4)
    PR.acheter(wA0, "lcu", 2); octA_lcu = pickle.dumps(wA0, protocol=4)
    wv = pickle.loads(octA0); PR.acheter(wv, "c130j", 1); octA_avion = pickle.dumps(wv, protocol=4)
    oid = next(o["id"] for o in OB.objectifs_carte("malden") if o["type"] == "base" and o.get("composants"))
    # O1
    w = pickle.loads(octA0); front0 = len(GM._front(w)); b0 = float(w.flux["brule"].get("carburant", 0.0))
    r_sans = EX.lancer_operation(w, "Stratis", oid, "lcu", 60)
    w2 = pickle.loads(octA_lcu); f2 = len(GM._front(w2)); b2 = float(w2.flux["brule"].get("carburant", 0.0))
    r_trop = EX.lancer_operation(w2, "Stratis", oid, "lcu", 900)
    O1 = (not r_sans["ok"] and "libre" in r_sans["raison"] and len(GM._front(w)) == front0
          and float(w.flux["brule"].get("carburant", 0.0)) == b0
          and not r_trop["ok"] and "capacite" in r_trop["raison"] and len(GM._front(w2)) == f2
          and float(w2.flux["brule"].get("carburant", 0.0)) == b2)
    R["O1"] = {"ok": O1, "sans_transport": r_sans, "trop": r_trop}
    print(f"  O1 refus : {'OUI' if O1 else 'NON'} {R['O1']}", flush=True)
    # O2 : la mer
    wA = pickle.loads(octA_lcu); wB = pickle.loads(octB)
    op = EX.lancer_operation(wA, "Stratis", oid, "lcu", 60)
    journal = []
    jusqu_a(wA, wB, op["arrivee"] - 1, journal)
    avant = EX._ops(wA)[0]["etat"]
    jusqu_a(wA, wB, op["arrivee"], journal)
    o_ = EX._ops(wA)[0]; pas_assaut = (o_["assaut"] or {}).get("pas")
    f = GM._front(wA)
    touches = [n for n, *_ in o_["assaut"]["sorts"]] if o_["assaut"] else []
    blesses = [n for n, e, *_ in o_["assaut"]["sorts"] if e == "blesse"] if o_["assaut"] else []
    jusqu_a(wA, wB, op["retour"] - 1, journal)
    ev_avant = {f[n]["i"] for n in blesses} & evacues(wA)
    rentres_avant = [n for n in op["numeros"] if f[n]["etat"] == "rentre"]
    b_r0 = float(wA.flux["brule"].get("carburant", 0.0))
    jusqu_a(wA, wB, op["retour"], journal)
    b_r1 = float(wA.flux["brule"].get("carburant", 0.0))
    o_ = EX._ops(wA)[0]
    ev_apres = {f[n]["i"] for n in blesses} <= (evacues(wA) | {i for i in range(wA.table.n) if not wA.table.vivant[i]})
    survivants = [n for n in op["numeros"] if n not in touches]
    residents = all(int(wA.table.statut[f[n]["i"]]) == PO.RESIDENT and f[n]["i"] not in wA.absents for n in survivants)
    O2 = (op["ok"] and avant == "en_route" and pas_assaut == op["arrivee"] and not ev_avant and not rentres_avant
          and o_["etat"] == "rentree" and ev_apres and residents and abs((b_r1 - b_r0) - op_carburant(wA)) <= 1e-6)
    R["O2"] = {"ok": O2, "arrivee": op["arrivee"], "retour": op["retour"], "pas_assaut": pas_assaut, "etat_avant": avant,
               "assaut": {k: (o_["assaut"] or {}).get(k) for k in ("arrives", "dommages", "defenseur")},
               "touches": len(touches), "blesses": len(blesses), "evacues_avant_retour": len(ev_avant),
               "rentres_avant_retour": len(rentres_avant), "survivants_residents": residents,
               "carburant_retour": [b_r1 - b_r0, op_carburant(wA)], "rapatriement": {k: v for k, v in (o_["rapatriement"] or {}).items() if k != "rentres"}}
    print(f"  O2 mer : {'OUI' if O2 else 'NON'} {R['O2']}", flush=True)
    # O3 : le parachutage
    wA3 = pickle.loads(octA_avion); wB3 = pickle.loads(octB)
    trop = EX.lancer_operation(wA3, "Stratis", oid, "c130j", 65, parachutage=True)
    op3 = EX.lancer_operation(wA3, "Stratis", oid, "c130j", 60, parachutage=True)
    jusqu_a(wA3, wB3, op3["arrivee"])
    a3 = EX._ops(wA3)[0]["assaut"]
    o3 = EX.objectif("Malden", oid)
    d_saut = math.dist(a3["depart_assaut"], o3["pos"][:2]) if a3 and a3["depart_assaut"] else None
    O3 = (not trop["ok"] and "capacite" in trop["raison"] and op3["ok"] and d_saut is not None and abs(d_saut - EX.DISTANCE_LARGAGE) <= 1e-6)
    R["O3"] = {"ok": O3, "trop": trop, "distance_saut": d_saut, "assaut": {k: (a3 or {}).get(k) for k in ("arrives", "dommages")}}
    print(f"  O3 parachutage : {'OUI' if O3 else 'NON'} {R['O3']}", flush=True)
    # O4 : les morts ( ceux de O2, et un mort pose sur un monde jumeau )
    w4 = pickle.loads(octA_lcu); n4 = GM.mobiliser(w4, 5); LO.emporter(w4, n4)
    p4 = w4.pays; rang4 = p4.col("habitant", "ar_rang"); f4 = GM._front(w4)
    num = next(n for n in n4 if int(rang4[f4[n]["i"]]) >= 0 and LO.coups(w4, n) > 0
               and int(A._dom(p4).eff["arme"][int(rang4[f4[n]["i"]])]) >= 0)
    i = f4[num]["i"]; rg = int(rang4[i])
    oa = int(A._dom(p4).eff["arme"][rg]); parc = p4.socle.parc
    reste = LO.coups(w4, num); perte0 = sorties(w4, "perte_au_combat")
    det0 = sum(c["detruit"] for c in parc.comptes)
    rap = EX.rapatrier(w4, {"sorts": [(num, "mort", "tete", "m4a1", 6, 75)], "restants": {num: reste}})
    det1 = sum(c["detruit"] for c in parc.comptes)
    perte1 = sorties(w4, "perte_au_combat")
    T.jours(w4, 1)                     # le domaine 25 retire ses morts a sa routine du jour ( comme apres une mort dans Arma )
    T.jours(wA, 2)                     # ( amende 03/10, M5 ) de meme pour les morts de O2
    O4 = (rap["morts"] == [num] and oa not in parc.objets and det1 - det0 == 1 and rap["armes_perdues"] == 1
          and abs(perte1 - perte0 - reste) <= 1e-9 and not w4.table.vivant[i]
          and not A.anomalies(p4) and not A.anomalies(wA.pays))
    R["O4"] = {"ok": O4, "arme_hors_parc": oa not in parc.objets, "detruits": det1 - det0, "perte": perte1 - perte0,
               "reste": reste, "morts_O2": len((o_["rapatriement"] or {}).get("morts", [])), "anomalies": [str(a) for a in A.anomalies(p4)[:3]]}
    print(f"  O4 morts : {'OUI' if O4 else 'NON'} {R['O4']}", flush=True)
    # O5
    ident = True
    for oc in (octA0, octB):
        w1, w2b = pickle.loads(oc), pickle.loads(oc)
        for _ in range(2):
            T.jours(w1, 1); T.jours(w2b, 1)
            if PE.empreinte_etendue(w1) != PE.empreinte_etendue(w2b): ident = False
    R["O5"] = {"ok": ident}
    print(f"  O5 identite : {'OUI' if ident else 'NON'}", flush=True)
    oks = [R[k]["ok"] for k in ("O1", "O2", "O3", "O4", "O5")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graines=[gA, gB], objectif=oid, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 4b-2 DE L OPERATION : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_OPERATION", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


def op_carburant(w):
    """Le carburant du retour de la premiere traversee ( le meme que l aller )."""
    t = PR._P(w)["traversees"][0]
    return t.get("retour_carburant", t["carburant"])


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(main(int(a[0]), int(a[1])) if len(a) >= 2 else main())
