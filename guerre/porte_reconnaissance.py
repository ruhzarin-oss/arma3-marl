"""Porte A3a de la reconnaissance ( HMT-198 ). Criteres ecrits avant la mesure ( Plane, 03/10 05 h 45 ) : Stratis ( 2121 )
contre Malden ( 2122 ), echelle 20, equipe de 8 ; jour : midi du jour 1, nuit : 24 pas plus tard ; port01 et base01,
5 graines de mission chacun.

R1  les vrais yeux : de jour, a 600 m, en infiltration, le rapport voit la garde ( plus de 0 homme ) sur au moins une
    mission de chaque objectif ; sur TOUTES les missions de la porte, jamais plus que la verite ( hommes vus <= garde
    engagee, blindes vus <= blindes engages ).
R2  controle negatif : point d observation a 3 km, depart a 4 km, de jour : 0 homme, 0 blinde vus, equipe jamais
    detectee, sur les 10 missions.
R3  la discretion : de jour a 600 m, sur 10 missions chacune, l infiltration est detectee strictement moins souvent que
    l approche debout.
R4  le retour dans A : une vraie operation ( LCU, 8 hommes, port01, but reconnaissance ) par avancer_operations ; au
    retour, le renseignement de A a port01 avec son pas, la situation de l etat-major le montre ( age >= 0 ) ; morts du
    rapport morts dans A de cause combat, blesses evacues ; survivants residents ; reserve du domaine 27 de A revenue.
R5  l action : valider accepte une reconnaissance de 1 a 30 hommes, refuse 31 ; executer lance une operation de but
    reconnaissance ( la porte S1 repasse a part ).
R6  le defaut du port : pour chaque objectif de Malden et de Stratis, le point d approche ( 800 m, 1,5 km ) est a cette
    distance exacte de l objectif.
python -m guerre.porte_reconnaissance"""
import json
import math
import pickle
import sys
import time

import numpy as np

from monde import archipel as AR, population as PO, tests as T
from monde.pays import d01_population as POP, d26_armee_soutien as S, d27_armee_tactique as TT
from . import etat_major as EM, expedition as EX, logistique as LO, moteur as GM, objectifs as OB, projection as PR
from . import reconnaissance as RC

SORTIE = "/mnt/data/hmt/arsenal/porte_reconnaissance.json"
OBJECTIFS = ("port01", "base01")


def verite(m):
    if m is None: return 0, 0
    return (sum(int((m.h["elt"] == i).sum()) for i, e in enumerate(m.elts) if e.side == 0), len(m.vehicules))


def serie(oc, cp, dist, approche, depart_m=RC.DEPART_M, base=9700):
    out = []
    for oid in OBJECTIFS:
        for sg in range(5):
            w = pickle.loads(oc)
            r = RC.reconnaitre(w, "Stratis", cp, oid, seed=(base + sg,), dist_op=dist, approche=approche, depart_m=depart_m)
            vh, vb = verite(r["mission"]); rp = r["rapport"]
            out.append({"objectif": oid, "vus": rp["hommes_vus"], "vrais": vh, "blindes_vus": rp["blindes_vus"], "blindes": vb,
                        "detectee": bool(r["detectee"]), "pertes": len(r["sorts"])})
    return out


def main(gA=2121, gB=2122):
    t0 = time.time(); R = {}
    print(f"PORTE A3a DE LA RECONNAISSANCE : Stratis {gA} contre Malden {gB}", flush=True)
    wA0 = AR.creer_ile("Stratis", gA, 20); T.jours(wA0, 1)
    wB0 = AR.creer_ile("Malden", gB, 20); T.jours(wB0, 1)
    for _ in range(72): wA0.pas_suivant(); wB0.pas_suivant()
    octA, jour = pickle.dumps(wA0, protocol=4), pickle.dumps(wB0, protocol=4)
    wn = pickle.loads(jour)
    for _ in range(24): wn.pas_suivant()
    nuit = pickle.dumps(wn, protocol=4)
    wt = pickle.loads(octA); nums = GM.mobiliser(wt, 8); LO.emporter(wt, nums); cp = EX.corps(wt, nums)
    s600 = serie(jour, cp, 600.0, "infiltration"); sdeb = serie(jour, cp, 600.0, "simultane", base=9710)
    sloin = serie(jour, cp, 3000.0, "infiltration", depart_m=4000.0, base=9720); snuit = serie(nuit, cp, 600.0, "infiltration", base=9730)
    tout = s600 + sdeb + sloin + snuit
    R1 = (all(any(x["vus"] > 0 for x in s600 if x["objectif"] == oid) for oid in OBJECTIFS)
          and all(x["vus"] <= x["vrais"] and x["blindes_vus"] <= x["blindes"] for x in tout))
    R["R1"] = {"ok": R1, "jour_600": s600, "nuit_600": snuit, "jamais_plus_que_la_verite": all(x["vus"] <= x["vrais"] and x["blindes_vus"] <= x["blindes"] for x in tout)}
    R2 = all(x["vus"] == 0 and x["blindes_vus"] == 0 and not x["detectee"] for x in sloin)
    R["R2"] = {"ok": R2, "loin": sloin}
    d_inf = sum(x["detectee"] for x in s600); d_deb = sum(x["detectee"] for x in sdeb)
    R3 = d_inf < d_deb
    R["R3"] = {"ok": R3, "detectee_infiltration": d_inf, "detectee_debout": d_deb, "debout": sdeb}
    for k in ("R1", "R2", "R3"): print(f"  {k} : {'OUI' if R[k]['ok'] else 'NON'} {json.dumps(R[k], default=str)[:900]}", flush=True)
    # R4 : la vraie operation
    wA = pickle.loads(octA); wB = pickle.loads(jour); pA = wA.pays
    PR.acheter(wA, "lcu", 1)
    res0 = {k: v for k, v in TT._dom(pA).reserve.items() if v > 1e-9}
    op = EX.lancer_operation(wA, "Stratis", "port01", "lcu", 8, but="reconnaissance")
    k = 0
    while op.get("ok") and EX._ops(wA)[0]["etat"] != "rentree" and k < 600:
        wA.pas_suivant(); wB.pas_suivant(); EX.avancer_operations(wA, wB); k += 1
    o_ = EX._ops(wA)[0] if op.get("ok") else {}
    rens = RC._renseignement(wA).get("port01"); sit = EM.situation(wA, "Stratis", "Malden")
    a = o_.get("assaut") or {}; f = GM._front(wA); col = pA.colonnes["habitant"]
    morts = [n for n, e, *_ in a.get("sorts", []) if e == "mort"]; blesses = [n for n, e, *_ in a.get("sorts", []) if e == "blesse"]
    ok_m = all(not wA.table.vivant[f[n]["i"]] and col["cause_deces"][f[n]["i"]] == POP.CAUSES.index("combat") for n in morts)
    ev = {int(x[1]) for x in S._dom(pA).evacuations}
    ok_b = all(f[n]["i"] in ev or not wA.table.vivant[f[n]["i"]] for n in blesses)
    touches = {n for n, *_ in a.get("sorts", [])}
    ok_r = all(int(wA.table.statut[f[n]["i"]]) == PO.RESIDENT and f[n]["i"] not in wA.absents for n in o_.get("numeros", []) if n not in touches)
    res1 = {k: v for k, v in TT._dom(pA).reserve.items() if v > 1e-9}
    ok_res = set(res0) == set(res1) and all(abs(res0[k] - res1[k]) <= 1e-9 for k in res0)
    R4 = (bool(op.get("ok")) and o_.get("etat") == "rentree" and rens is not None and rens.get("pas_A") == a.get("pas")
          and "port01" in sit["renseignement"] and sit["renseignement"]["port01"]["age_h"] >= 0 and ok_m and ok_b and ok_r and ok_res)
    R["R4"] = {"ok": R4, "etat": o_.get("etat"), "renseignement": rens, "situation": sit["renseignement"].get("port01"),
               "morts": len(morts), "blesses": len(blesses), "morts_ok": ok_m, "blesses_ok": ok_b, "residents": ok_r,
               "reserve": [res0, res1], "pas": k}
    print(f"  R4 : {'OUI' if R4 else 'NON'} {json.dumps(R['R4'], default=str)[:900]}", flush=True)
    # R5
    w5 = pickle.loads(octA); PR.acheter(w5, "lcu", 1)
    ok30 = EM.valider(w5, "Malden", {"type": "reconnaissance", "objectif": "port01", "modele": "lcu", "hommes": 30})[0] is not None
    ok1 = EM.valider(w5, "Malden", {"type": "reconnaissance", "objectif": "port01", "modele": "lcu", "hommes": 1})[0] is not None
    ko31 = EM.valider(w5, "Malden", {"type": "reconnaissance", "objectif": "port01", "modele": "lcu", "hommes": 31})[0] is None
    ex = EM.executer(w5, "Stratis", "Malden", [{"type": "reconnaissance", "objectif": "base01", "modele": "lcu", "hommes": 6}])
    R5 = ok30 and ok1 and ko31 and ex[0][1].get("ok") and EX._ops(w5) and EX._ops(w5)[-1].get("but") == "reconnaissance"
    R["R5"] = {"ok": bool(R5), "30": ok30, "1": ok1, "31_refuse": ko31, "execution": str(ex)[:300]}
    print(f"  R5 : {'OUI' if R5 else 'NON'} {R['R5']}", flush=True)
    # R6
    ecarts = []
    for ile, oc in (("Malden", jour), ("Stratis", octA)):
        w6 = pickle.loads(oc)
        for o in OB.objectifs_carte(ile.lower()):
            for dist in (EX.DISTANCE_ASSAUT, EX.DISTANCE_LARGAGE):
                x, y = EX.point_d_approche(w6, o, dist)
                ecarts.append((ile, o["id"], dist, round(math.hypot(x - o["pos"][0], y - o["pos"][1]) - dist, 9)))
    R6 = all(abs(e[3]) <= 1e-6 for e in ecarts)
    R["R6"] = {"ok": R6, "pires": sorted(ecarts, key=lambda e: -abs(e[3]))[:4], "n": len(ecarts)}
    print(f"  R6 : {'OUI' if R6 else 'NON'} {R['R6']}", flush=True)
    oks = [R[k]["ok"] for k in ("R1", "R2", "R3", "R4", "R5", "R6")]
    verdict = "FRANCHIE ( S1 a part )" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graines=[gA, gB], duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE A3a DE LA RECONNAISSANCE : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_RECONNAISSANCE", flush=True)
    return 0 if all(oks) else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(main(int(a[0]), int(a[1])) if len(a) >= 2 else main())
