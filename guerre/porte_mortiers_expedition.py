"""Porte A1-bis des mortiers de l expedition ( HMT-198 ). Criteres ecrits avant la mesure ( Plane, 03/10 ) : Stratis
( 2091 ) contre Malden ( 2092 ), echelle 20, 60 soldats mobilises, une base de Malden.

M1  l emport : tubes = min( tubes de la base des servants, servants / 2 ), obus = min( 60 x tubes, stock hors reserves ) ;
    lancer_operation reserve exactement ces obus.
M2  controle positif : sur 5 graines de mission, le defenseur perd strictement plus d hommes avec les mortiers de
    l expedition que sans ; plus de 0 obus. ( amende 03/10, A2 : blindes coupes ; les comptes M3 sur les memes graines,
    tout ouvert )
M3  les comptes : obus tires <= emportes ; au rapatriement, tir_combat d obus_81 de l attaquant + exactement les tires ;
    sa reserve revient a ce qu elle etait.
M4  controle negatif : un corps sans servant n emporte aucun tube, aucun obus.
python -m guerre.porte_mortiers_expedition [ graine_A graine_B ]"""
import json
import math
import pickle
import sys
import time

from monde import archipel as AR, tests as T
from monde.pays import d25_armee as A, d27_armee_tactique as TT
from . import expedition as EX, logistique as LO, moteur as GM, objectifs as OB, projection as PR

SORTIE = "/mnt/data/hmt/arsenal/porte_mortiers_expedition.json"


def sortis(w, bien, motif="tir_combat"):
    d = w.pays.domaines[A.DOMAINE]
    return sum(v for (b, m), v in d.sorties.items() if b == bien and m == motif)


def pertes(m):
    return len(set(m.morts)) + len(set(m.blesses) - set(m.morts))


def main(gA=2091, gB=2092):
    t0 = time.time(); R = {}
    print(f"PORTE A1-bis DES MORTIERS DE L EXPEDITION : Stratis {gA} contre Malden {gB}", flush=True)
    wA0 = AR.creer_ile("Stratis", gA, 20); T.jours(wA0, 1)
    wB0 = AR.creer_ile("Malden", gB, 20); T.jours(wB0, 1)
    octB = pickle.dumps(wB0, protocol=4)
    oid = next(o["id"] for o in OB.objectifs_carte("malden") if o["type"] == "base" and o.get("composants"))
    # des soldats qui comptent des servants de mortier : la base qui en a le plus
    pA = wA0.pays; a = A._dom(pA); E = a.eff; rows = A._lignes_actives(a)
    serv_rows = [r for r in rows.tolist() if int(E["spec"][r]) == A.MORTIER]
    b0 = int(E["base"][serv_rows[0]]) if serv_rows else -1
    octA = pickle.dumps(wA0, protocol=4)
    # M1
    w = pickle.loads(octA); PR.acheter(w, "lcu", 1)
    nums = GM.mobiliser(w, 60, ids=EX.membres_a_projeter(w, 60)); LO.emporter(w, nums)
    cp = EX.corps(w, nums); Mx = cp["mortiers"]
    p = w.pays; a = A._dom(p); K = a.coll
    serv = [k for k, sp in enumerate(cp["spec"].tolist()) if sp == A.MORTIER]
    b = int(a.eff["base"][A._rangs(p, cp["hid"][serv[:1]])[0]]) if serv else -1
    dispo = sum(1 for k in range(K.n) if int(K["oid"][k]) >= 0 and int(K["modele"][k]) == A.IDX_ARME["mortier_81"] and int(K["base"][k]) == b)
    t_att = min(dispo, len(serv) // TT.SERVANTS_PAR_TUBE)
    lid = w.carte.par_n[b].id if b >= 0 else None; cal = A.NOMS_MUNITIONS.index("obus_81")
    stock = float(A.armurerie(p, lid).stock[a.bids["obus_81"]]) if lid else 0.0
    o_att = float(min(60 * t_att, math.floor(stock - TT._dom(p).reserve.get((lid, cal), 0.0)))) if lid else 0.0
    res0 = TT._dom(p).reserve.get((lid, cal), 0.0)
    # lancer_operation sur un jumeau : la reserve
    wj = pickle.loads(octA); PR.acheter(wj, "lcu", 1)
    op = EX.lancer_operation(wj, "Stratis", oid, "lcu", 60)
    Mj = op["corps"]["mortiers"] if op.get("ok") else {}
    resj = TT._dom(wj.pays).reserve.get((Mj.get("base"), cal), 0.0) if Mj.get("base") else 0.0
    M1 = (Mx["tubes"] == (t_att if o_att > 0 else 0) and abs(Mx["obus"] - o_att) <= 1e-9 and t_att > 0
          and op.get("ok") and abs(resj - Mj.get("obus", -1)) <= 1e-9)
    R["M1"] = {"ok": M1, "servants": len(serv), "tubes_base": dispo, "tubes": Mx["tubes"], "tubes_attendus": t_att,
               "obus": Mx["obus"], "obus_attendus": o_att, "reserve_operation": resj, "base_des_servants": lid}
    print(f"  M1 emport : {'OUI' if M1 else 'NON'} {R['M1']}", flush=True)
    # M2 et M3
    tot = {True: 0, False: 0}; obus = 0.0; comptes = []
    TT.BLINDES = False                     # ( amende 03/10, A2 ) M2 isole les mortiers de l expedition des blindes de B
    for sg in range(5):
        for avec in (True, False):
            c = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in cp.items()}
            if not avec: c["mortiers"] = {"tubes": 0, "obus": 0.0, "base": None}
            wb = pickle.loads(octB)
            r = EX.assaut(wb, "Stratis", c, oid, seed=(9100 + sg,))
            tot[avec] += pertes(r["mission"])
            if avec: obus += r["obus_tires"]
    TT.BLINDES = True
    for sg in range(5):                    # ( amende 03/10, A2 ) les comptes M3 avec tout ouvert, memes graines
        for avec in (True,):
            c = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in cp.items()}
            wb = pickle.loads(octB)
            r = EX.assaut(wb, "Stratis", c, oid, seed=(9100 + sg,))
            if avec:
                wa = pickle.loads(pickle.dumps(w, protocol=4)); pa = wa.pays
                ra = TT._dom(pa).reserve; ra[(lid, cal)] = ra.get((lid, cal), 0.0) + Mx["obus"]      # comme lancer_operation
                s0 = sortis(wa, "obus_81"); r_av = ra.get((lid, cal), 0.0)
                rap = EX.rapatrier(wa, r)
                comptes.append({"tires": r["obus_tires"], "emportes": Mx["obus"], "sortis": sortis(wa, "obus_81") - s0,
                                "reserve": [r_av, TT._dom(pa).reserve.get((lid, cal), 0.0), res0]})
    M2 = tot[True] > tot[False] and obus > 0
    M3 = all(c["tires"] <= c["emportes"] + 1e-9 and abs(c["sortis"] - c["tires"]) <= 1e-9 and abs(c["reserve"][1] - c["reserve"][2]) <= 1e-9
             for c in comptes)
    R["M2"] = {"ok": M2, "pertes_defense_avec": tot[True], "pertes_defense_sans": tot[False], "obus_tires": obus}
    R["M3"] = {"ok": M3, "comptes": comptes}
    print(f"  M2 controle positif : {'OUI' if M2 else 'NON'} {R['M2']}", flush=True)
    print(f"  M3 comptes : {'OUI' if M3 else 'NON'} {R['M3']}", flush=True)
    # M4
    sans = [k for k, sp in enumerate(cp["spec"].tolist()) if sp != A.MORTIER]
    c4 = {k: (v[sans] if hasattr(v, "__len__") and not isinstance(v, dict) and len(v) == len(cp["numero"]) else v) for k, v in cp.items()}
    c4["mortiers"] = EX.mortiers_emportes(w, c4)
    wb = pickle.loads(octB); r4 = EX.assaut(wb, "Stratis", c4, oid, seed=(9200,))
    M4 = c4["mortiers"]["tubes"] == 0 and r4["obus_tires"] == 0
    R["M4"] = {"ok": M4, "mortiers": c4["mortiers"], "obus_tires": r4["obus_tires"]}
    print(f"  M4 sans servant : {'OUI' if M4 else 'NON'} {R['M4']}", flush=True)
    oks = [R[k]["ok"] for k in ("M1", "M2", "M3", "M4")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graines=[gA, gB], objectif=oid, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE A1-bis DES MORTIERS DE L EXPEDITION : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_MORTIERS_EXPEDITION", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(main(int(a[0]), int(a[1])) if len(a) >= 2 else main())
