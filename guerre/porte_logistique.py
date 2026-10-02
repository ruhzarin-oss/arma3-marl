"""Porte 2a' de la logistique, ALIGNEE sur les domaines 26 et 27 ( HMT-193 ). Criteres ecrits avant la mesure ( Plane,
02/10 ) : Malden ( 1981 ), echelle 20, 20 soldats mobilises.

A1  emporter = la regle du 27 : chacun porte floor( dotation x min( 1, ( stock - reserve ) / somme des dotations ) ) par
    ( base, calibre ), recalcule a part ; armureries inchangees au bit ; reserve du 27 = somme portee par cle ; plus
    d armurerie « front » ; anomalies du 25 vides ; somme > 0.
A2  controles positifs : une base videe d abord ne donne rien ; une base tiree jusqu a sa seule reserve donne 0 coup aux
    hommes d une mission du 27 ( _hommes_bleus ).
A3  tirer : 30 coups de moins -> armurerie - 30, tir_combat + 30, reserve - 30, tirs du 27 + 30 ; anomalies vides.
A4  la mort : ramasse -> reserve - reste, stock inchange, perte 0 ; abandonne -> perte_au_combat = reste, stock et
    reserve - reste.
A5  convoi : refuse ( raison ) sans camion libre au 26, sans gazole ; parti -> camion hors de _camions_libres et
    conducteur reserve jusqu a depart + aller + retour ; gazole - 2 x km_route x conso, au livre de flux du 26 ; arrivee
    a depart + aller, rien avant ; reserve + charge au depart, coups + charge a l arrivee ; anomalies du 25 et du 26 vides.
A6  identite : sans appel, identique au bit au jumeau sur 2 jours.

python -m guerre.porte_logistique"""
import json
import math
import pickle
import sys
import time

import numpy as np

from monde import archipel as AR, tests as T
from monde.pays import d15_logistique as LG, d25_armee as A, d26_armee_soutien as S, d27_armee_tactique as T27
from . import logistique as LO, moteur as GM
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_logistique.json"


def stocks(w):
    d = w.pays.domaines[A.DOMAINE]
    return {(a.lieu, b): float(a.stock[d.bids[b]]) for a in d.armureries for b in A.NOMS_MUNITIONS + ("pieces",)}


def sorties(w, motif):
    d = w.pays.domaines[A.DOMAINE]
    return sum(v for (b, m), v in d.sorties.items() if m == motif)


def reserve(w):
    return dict(T27._dom(w.pays).reserve)


def anomalies(w):
    return A.anomalies(w.pays) + S.anomalies(w.pays)


def recalcul(w, nums):
    """La regle du 27, rejouee a part : ( numero -> ( lieu, calibre, coups ) )."""
    p = w.pays; d = A._dom(p); E = d.eff; f = GM._front(w); col = p.col("habitant", "ar_rang")
    lignes = []
    for num in nums:
        r = int(col[f[num]["i"]])
        if r < 0: continue
        k = int(E["arme_m"][r])
        if k >= 0 and A.ARMES[k].nom in T27.ARMES_LOURDES: k = int(E["arme2_m"][r])
        if k < 0: continue
        lid = w.carte.par_n[int(E["base"][r])].id
        lignes.append((num, lid, A.NOMS_MUNITIONS.index(A.ARMES[k].calibre), float(A.DOTATION_COMBAT.get(A.ARMES[k].nom, 0))))
    out = {}; res = {}
    for cle in sorted({(l, c) for _n, l, c, _d in lignes}):
        sel = [x for x in lignes if (x[1], x[2]) == cle]
        stock = float(A.armurerie(p, cle[0]).stock[d.bids[A.NOMS_MUNITIONS[cle[1]]]])
        dispo = max(0.0, stock - res.get(cle, 0.0))
        fr = min(1.0, dispo / max(1e-9, sum(x[3] for x in sel)))
        for num, l, c, dot in sel:
            out[num] = (l, c, float(np.floor(dot * fr)))
        res[cle] = res.get(cle, 0.0) + sum(out[x[0]][2] for x in sel)
    return out, res


def main():
    t0 = time.time(); R = {}
    print("PORTE 2a' DE LA LOGISTIQUE ( alignee 26 et 27 ) : Malden 1981, 20 soldats", flush=True)
    w0 = AR.creer_ile("Malden", 1981, 20); oct_ = pickle.dumps(w0, protocol=4)
    # A1
    w = pickle.loads(oct_); p = w.pays
    nums = GM.mobiliser(w, 20)
    att, res_att = recalcul(w, nums)
    av = stocks(w); r0 = reserve(w)
    porte = LO.emporter(w, nums)
    ap = stocks(w); r1 = reserve(w)
    ecarts = [n for n in nums if abs(porte.get(n, 0.0) - (att[n][2] if n in att else 0.0)) > 1e-9]
    res_ok = all(abs(r1.get(k, 0.0) - r0.get(k, 0.0) - q) <= 1e-9 for k, q in res_att.items()) \
        and set(k for k, v in r1.items() if v > 0) == set(k for k, v in res_att.items() if v > 0)
    pas_de_front = not any(a.lieu == "front" for a in A._dom(p).armureries)
    an1 = anomalies(w)
    A1 = bool(nums) and not ecarts and av == ap and res_ok and pas_de_front and not an1 and sum(porte.values()) > 0
    R["A1"] = {"ok": A1, "soldats": len(nums), "militaires": len(att), "coups": sum(porte.values()), "ecarts": ecarts[:5],
               "armureries_inchangees": av == ap, "reserve": {f"{k[0]}:{k[1]}": v for k, v in r1.items()}, "reserve_juste": res_ok,
               "plus_de_front": pas_de_front, "anomalies": an1[:5]}
    print(f"  A1 emporter : {'OUI' if A1 else 'NON'} {R['A1']}", flush=True)
    # A2 : une base videe d abord ; une base tiree jusqu a sa reserve
    w2 = pickle.loads(oct_); p2 = w2.pays; d2 = A._dom(p2)
    n2 = GM.mobiliser(w2, 20)
    att2, _ = recalcul(w2, n2)
    lieu0 = next(att2[n][0] for n in n2 if n in att2)
    arm0 = A.armurerie(p2, lieu0)
    for bien in A.NOMS_MUNITIONS:
        q = float(arm0.stock[d2.bids[bien]])
        if q > 0: A.tirer(p2, lieu0, bien, q, "tir_instruction")
    pv = LO.emporter(w2, n2)
    de_b0 = [n for n in n2 if n in att2 and att2[n][0] == lieu0]
    autres = [n for n in n2 if n in att2 and att2[n][0] != lieu0]
    a2a = bool(de_b0) and all(pv[n] == 0 for n in de_b0) and (not autres or any(pv[n] > 0 for n in autres))
    # la reserve vue par le 27 : la base de w ( apres emporter ) tiree jusqu a sa seule reserve
    w3 = pickle.loads(pickle.dumps(w, protocol=4)); p3 = w3.pays; d3 = A._dom(p3)
    (lid3, c3), q3 = next((k, v) for k, v in reserve(w3).items() if v > 0)
    bien3 = A.NOMS_MUNITIONS[c3]
    exces = float(A.armurerie(p3, lid3).stock[d3.bids[bien3]]) - q3
    if exces > 0: A.tirer(p3, lid3, bien3, exces, "tir_instruction")
    E3 = d3.eff; f3 = GM._front(w3); engages = {f3[n]["i"] for n in nums}
    rows = A._lignes_actives(d3)
    autres3 = [int(E3["hid"][r]) for r in rows.tolist() if w3.carte.par_n[int(E3["base"][r])].id == lid3
               and int(E3["arme_m"][r]) >= 0 and A.ARMES[int(E3["arme_m"][r])].calibre == bien3
               and int(E3["hid"][r]) not in engages][:8]
    h3 = T27._hommes_bleus(p3, autres3, np.zeros(len(autres3), np.int16), False, dict(T27._dom(p3).reserve)) if autres3 else None
    a2b = h3 is not None and float(h3["coups"].sum()) == 0.0
    # temoin : sans la reserve, ces hommes auraient eu des coups ( la base n est pas vide )
    h3t = T27._hommes_bleus(p3, autres3, np.zeros(len(autres3), np.int16), False, {}) if autres3 else None
    a2b = a2b and h3t is not None and float(h3t["coups"].sum()) > 0
    A2 = a2a and a2b
    R["A2"] = {"ok": A2, "base_videe": lieu0, "soldats_de_la_base": len(de_b0), "coups_de_la_base": sum(pv[n] for n in de_b0),
               "base_a_sa_reserve": lid3, "bien": bien3, "hommes_du_27": len(autres3),
               "coups_du_27": None if h3 is None else float(h3["coups"].sum()),
               "coups_du_27_sans_reserve": None if h3t is None else float(h3t["coups"].sum())}
    print(f"  A2 controles positifs : {'OUI' if A2 else 'NON'} {R['A2']}", flush=True)
    # A3 : tirer
    t27 = T27._dom(p)
    na = next(n for n in nums if LO.coups(w, n) >= 30)
    lid, c = att[na][0], att[na][1]; bien = A.NOMS_MUNITIONS[c]
    s0 = stocks(w)[(lid, bien)]; tc0 = sorties(w, "tir_combat"); rv0 = reserve(w)[(lid, c)]; ti0 = t27.tirs.get((lid, bien), 0.0)
    sortis = LO.tirer(w, na, LO.coups(w, na) - 30)
    s1 = stocks(w)[(lid, bien)]; tc1 = sorties(w, "tir_combat"); rv1 = reserve(w)[(lid, c)]; ti1 = t27.tirs.get((lid, bien), 0.0)
    an3 = anomalies(w)
    A3 = abs(sortis - 30) <= 1e-9 and abs(s0 - s1 - 30) <= 1e-9 and abs(tc1 - tc0 - 30) <= 1e-9 \
        and abs(rv0 - rv1 - 30) <= 1e-9 and abs(ti1 - ti0 - 30) <= 1e-9 and not an3
    R["A3"] = {"ok": A3, "sortis": sortis, "armurerie": [s0, s1], "tir_combat": [tc0, tc1], "reserve": [rv0, rv1],
               "tirs_27": [ti0, ti1], "anomalies": an3[:5]}
    print(f"  A3 tirer : {'OUI' if A3 else 'NON'} {R['A3']}", flush=True)
    # A4 : la mort, ramasse puis abandonne
    nb, nc_ = [n for n in nums if n != na and LO.coups(w, n) > 0][:2]
    out4 = {}
    for n, ab in ((nb, False), (nc_, True)):
        l4, c4 = att[n][0], att[n][1]; b4 = A.NOMS_MUNITIONS[c4]; reste = LO.coups(w, n)
        s_a = stocks(w)[(l4, b4)]; r_a = reserve(w)[(l4, c4)]; p_a = sorties(w, "perte_au_combat")
        perdu = LO.mort(w, n, abandonne=ab)
        s_b = stocks(w)[(l4, b4)]; r_b = reserve(w)[(l4, c4)]; p_b = sorties(w, "perte_au_combat")
        if ab: ok = abs(perdu - reste) <= 1e-9 and abs(p_b - p_a - reste) <= 1e-9 and abs(s_a - s_b - reste) <= 1e-9 and abs(r_a - r_b - reste) <= 1e-9
        else: ok = perdu == 0 and p_b == p_a and s_a == s_b and abs(r_a - r_b - reste) <= 1e-9
        out4["abandonne" if ab else "ramasse"] = {"ok": ok and LO.coups(w, n) == 0, "reste": reste, "perdu": perdu,
                                                    "stock": [s_a, s_b], "reserve": [r_a, r_b], "perte": [p_a, p_b]}
    A4 = all(v["ok"] for v in out4.values()) and not anomalies(w)
    R["A4"] = {"ok": A4, **out4}
    print(f"  A4 mort : {'OUI' if A4 else 'NON'} {R['A4']}", flush=True)
    # A5 : le convoi
    nd = next(n for n in nums if n not in (na, nb, nc_) and n in att and LO.coups(w, n) > 0)
    lieu_c = att[nd][0]; o = w.carte.lieux[lieu_c]; b_c = o.n
    loin = [l for l in w.carte.par_n if l.ile == o.ile and l.id != lieu_c and LG.route_praticable(p, o, l)]
    cible = max(loin, key=lambda l: w.carte.km_route(o, l))
    dest = (cible.pos[0] + 5.0, cible.pos[1])
    # sans camion libre : tous les camions de la base pris au 26
    wn = pickle.loads(pickle.dumps(w, protocol=4)); dn = S._dom(wn.pays)
    for k in S._camions_libres(wn.pays, dn, b_c): dn.camion_libre[k] = 10 ** 9
    r_sans_camion = LO.convoi(wn, lieu_c, [nd], 100, dest)
    # sans gazole
    wg = pickle.loads(pickle.dumps(w, protocol=4)); g = wg.garnisons[lieu_c]
    wg.flux["brule"]["carburant"] += float(g["carburant"]); g["carburant"] = 0.0
    r_sans_gazole = LO.convoi(wg, lieu_c, [nd], 100, dest)
    # avec les deux
    d26 = S._dom(p)
    libres0 = S._camions_libres(p, d26, b_c)
    carb0 = float(w.garnisons[lieu_c]["carburant"]); fl0 = dict(d26.flux) if hasattr(d26, "flux") else None
    c_nd = att[nd][1]; rv0 = reserve(w).get((lieu_c, c_nd), 0.0); coups0 = LO.coups(w, nd)
    rc = LO.convoi(w, lieu_c, [nd], 100, dest)
    km = w.carte.km_route(o, w.carte.lieux[rc["vers"]]) if rc.get("ok") else None
    aller, retour = LG.duree_convoi_pas(p, o, w.carte.lieux[rc["vers"]], km) if rc.get("ok") else (None, None)
    gaz_att = 2.0 * km * A.VEHICULE[S.CAMION].unites_par_km if km is not None else None
    ok_dep = bool(rc.get("ok")) and rc["vers"] == cible.id and rc["arrivee"] - rc["depart"] == aller \
        and abs(rc["gazole"] - gaz_att) <= 1e-9 and abs(carb0 - float(w.garnisons[lieu_c]["carburant"]) - gaz_att) <= 1e-9
    charge = rc["charge"].get(nd, 0.0) if rc.get("ok") else 0.0
    reserve_dep = abs(reserve(w).get((lieu_c, c_nd), 0.0) - rv0 - charge) <= 1e-9 and charge > 0
    k_pris = rc.get("camion"); h_pris = rc.get("chauffeur")
    fl1 = dict(d26.flux) if hasattr(d26, "flux") else None
    flux_ok = None
    if fl0 is not None:
        delta = {k: fl1.get(k, 0.0) - fl0.get(k, 0.0) for k in set(fl0) | set(fl1) if abs(fl1.get(k, 0.0) - fl0.get(k, 0.0)) > 1e-12}
        flux_ok = len(delta) == 1 and abs(list(delta.values())[0] - gaz_att) <= 1e-9 and "carburant_convoi_militaire" in str(list(delta)[0])
    pris_jusqu = rc["depart"] + aller + retour if rc.get("ok") else None
    double_emploi = []
    rien_avant = True
    while int(w.pas) < rc["arrivee"] - 1:
        w.pas_suivant(); LO.avancer(w)
        if LO.coups(w, nd) != coups0: rien_avant = False
        if k_pris in S._camions_libres(p, d26, b_c): double_emploi.append(("camion", int(w.pas)))
        if d26.chauffeur_libre.get(h_pris, -1) <= int(w.pas): double_emploi.append(("chauffeur", int(w.pas)))
    while int(w.pas) < rc["arrivee"]:
        w.pas_suivant()
    livres = LO.avancer(w)
    arrive = rc["id"] in livres and abs(LO.coups(w, nd) - coups0 - charge) <= 1e-9
    an5 = anomalies(w)
    A5 = (not r_sans_camion["ok"] and "camion" in r_sans_camion["raison"] and not r_sans_gazole["ok"]
          and "gazole" in r_sans_gazole["raison"] and ok_dep and reserve_dep and k_pris in libres0
          and d26.camion_libre.get(k_pris) == pris_jusqu and d26.chauffeur_libre.get(h_pris) == pris_jusqu
          and not double_emploi and flux_ok is not False and rien_avant and arrive and not an5)
    R["A5"] = {"ok": A5, "sans_camion": r_sans_camion, "sans_gazole": r_sans_gazole, "vers": rc.get("vers"), "km_route": km,
               "aller_retour": [aller, retour], "gazole": [rc.get("gazole"), gaz_att], "flux_26": flux_ok,
               "charge": charge, "reserve_au_depart": reserve_dep, "camion": k_pris, "chauffeur": h_pris,
               "pris_jusqu": pris_jusqu, "double_emploi": double_emploi, "rien_avant": rien_avant, "arrive": arrive,
               "anomalies": an5[:5]}
    print(f"  A5 convoi : {'OUI' if A5 else 'NON'} {R['A5']}", flush=True)
    # A6 : l identite
    wa, wb = pickle.loads(oct_), pickle.loads(oct_)
    ident = True
    for _ in range(2):
        T.jours(wa, 1); T.jours(wb, 1)
        if PE.empreinte_etendue(wa) != PE.empreinte_etendue(wb): ident = False
    R["A6"] = {"ok": ident}
    print(f"  A6 identite : {'OUI' if ident else 'NON'}", flush=True)
    oks = [R[k]["ok"] for k in ("A1", "A2", "A3", "A4", "A5", "A6")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 2a' DE LA LOGISTIQUE : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_LOGISTIQUE", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
