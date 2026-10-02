"""Porte 2a de la logistique ( HMT-193 ). Criteres ecrits avant la mesure ( Plane ) : Malden ( 1961 ), echelle 20,
20 soldats mobilises.

L1  emporter : chacun a min( dotation de combat, disponible a sa base ) par calibre ; bases + front inchange ; anomalies
    vides.
L2  controle positif : une base videe d abord ne donne rien a ses soldats.
L3  tirer : 30 coups de moins rendus pour un soldat -> front - 30, sorties tir_combat + 30, anomalies vides.
L4  la mort : perte_au_combat = exactement le reste porte.
L5  convoi : refuse sans camion, refuse sans gazole ; sinon arrivee au pas depart + ceil( duree ), pas avant ; gazole
    brule = km aller-retour x consommation ; conservation.
L6  identite : sans logistique, identique au bit au jumeau sur 2 jours.

python -m guerre.porte_logistique"""
import json
import math
import pickle
import sys
import time

from monde import archipel as AR, config as C, tests as T
from monde.pays import d25_armee as A
from . import logistique as LO, moteur as GM
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_logistique.json"


def total(w):
    d = w.pays.domaines[A.DOMAINE]
    return {b: sum(float(a.stock[d.bids[b]]) for a in d.armureries) for b in A.NOMS_MUNITIONS + ("pieces",)}


def sorties(w, motif):
    d = w.pays.domaines[A.DOMAINE]
    return sum(v for (b, m), v in d.sorties.items() if m == motif)


def main():
    t0 = time.time(); R = {}
    print("PORTE 2a DE LA LOGISTIQUE : Malden 1961, 20 soldats", flush=True)
    w0 = AR.creer_ile("Malden", 1961, 20); oct_ = pickle.dumps(w0, protocol=4)
    # L1
    w = pickle.loads(oct_); d = w.pays.domaines[A.DOMAINE]
    nums = GM.mobiliser(w, 20)
    avant = total(w)
    dispo = {}; attendu = {}
    for num in nums:                                   # la regle, rejouee a part dans le meme ordre
        s = GM._front(w)[num]; r = LO._rang(w, s["i"])
        att = {}
        if r >= 0:
            b = int(d.eff["base"][r]); arm = d.armureries[d.par_base[b]]
            for nom, bien in LO._armes(d, r):
                k = (b, bien); dispo.setdefault(k, float(arm.stock[d.bids[bien]]))
                q = min(float(A.DOTATION_COMBAT[nom]), dispo[k]); dispo[k] -= q
                att[bien] = att.get(bien, 0.0) + q
        attendu[num] = att
    porte = LO.emporter(w, nums)
    apres = total(w)
    ecart_regle = [n for n in nums if any(abs(porte[n].get(b, 0.0) - q) > 1e-9 for b, q in attendu[n].items())
                   or set(k for k, v in porte[n].items() if v > 0) - set(k for k, v in attendu[n].items() if v > 0)]
    conserve = all(abs(apres[b] - avant[b]) <= 1e-6 * max(1.0, avant[b]) for b in avant)
    an1 = A.anomalies(w.pays)
    L1 = bool(nums) and not ecart_regle and conserve and not an1 and sum(sum(v.values()) for v in porte.values()) > 0
    R["L1"] = {"ok": L1, "soldats": len(nums), "coups": sum(sum(v.values()) for v in porte.values()),
               "ecarts": ecart_regle[:5], "conserve": conserve, "anomalies": an1[:5]}
    print(f"  L1 emporter : {'OUI' if L1 else 'NON'} {R['L1']}", flush=True)
    # L2 : une base videe
    w2 = pickle.loads(oct_); d2 = w2.pays.domaines[A.DOMAINE]
    n2 = GM.mobiliser(w2, 20)
    s0 = GM._front(w2)[n2[0]]; r0 = LO._rang(w2, s0["i"]); b0 = int(d2.eff["base"][r0]); lieu0 = w2.carte.par_n[b0].id
    arm0 = d2.armureries[d2.par_base[b0]]
    for bien in A.NOMS_MUNITIONS:
        q = float(arm0.stock[d2.bids[bien]])
        if q > 0: A.tirer(w2.pays, lieu0, bien, q, "tir_instruction")
    p2 = LO.emporter(w2, n2)
    de_b0 = [n for n in n2 if int(d2.eff["base"][LO._rang(w2, GM._front(w2)[n]["i"])]) == b0]
    autres = [n for n in n2 if n not in de_b0]
    L2 = bool(de_b0) and all(sum(p2[n].values()) == 0 for n in de_b0) and (not autres or any(sum(p2[n].values()) > 0 for n in autres))
    R["L2"] = {"ok": L2, "base_videe": lieu0, "soldats_de_la_base": len(de_b0), "coups_de_la_base": sum(sum(p2[n].values()) for n in de_b0)}
    print(f"  L2 base videe : {'OUI' if L2 else 'NON'} {R['L2']}", flush=True)
    # L3 : tirer
    fr = LO.front(w)
    na = next(n for n in nums if LO.coups(w, n) >= 30)
    av_front = sum(float(fr.stock[d.bids[b]]) for b in A.NOMS_MUNITIONS); av_s = sorties(w, "tir_combat")
    tire = LO.tirer(w, na, LO.coups(w, na) - 30)
    ap_front = sum(float(fr.stock[d.bids[b]]) for b in A.NOMS_MUNITIONS); ap_s = sorties(w, "tir_combat")
    an3 = A.anomalies(w.pays)
    L3 = abs(tire - 30) <= 1e-9 and abs(av_front - ap_front - 30) <= 1e-9 and abs(ap_s - av_s - 30) <= 1e-9 and not an3
    R["L3"] = {"ok": L3, "tire": tire, "front": [av_front, ap_front], "tir_combat": [av_s, ap_s], "anomalies": an3[:5]}
    print(f"  L3 tirer : {'OUI' if L3 else 'NON'} {R['L3']}", flush=True)
    # L4 : la mort
    nb = next(n for n in nums if n != na and LO.coups(w, n) > 0)
    reste = LO.coups(w, nb); av_p = sorties(w, "perte_au_combat")
    perdu = LO.mort(w, nb); ap_p = sorties(w, "perte_au_combat")
    L4 = abs(perdu - reste) <= 1e-9 and abs(ap_p - av_p - reste) <= 1e-9 and not A.anomalies(w.pays)
    R["L4"] = {"ok": L4, "reste": reste, "perdu": perdu, "perte_au_combat": [av_p, ap_p]}
    print(f"  L4 mort : {'OUI' if L4 else 'NON'} {R['L4']}", flush=True)
    # L5 : le convoi
    nc = next(n for n in nums if n not in (na, nb) and LO._L(w)["porte"][n]["armes"])
    s_c = GM._front(w)[nc]; b_c = int(d.eff["base"][LO._rang(w, s_c["i"])]); lieu_c = w.carte.par_n[b_c].id
    pos = w.carte.lieux[lieu_c].pos; dest = (pos[0] + 10000.0, pos[1])
    # sans camion
    wn = pickle.loads(pickle.dumps(w, protocol=4))
    Vn = wn.pays.domaines[A.DOMAINE].veh; m = A.IDX_VEHICULE[LO.CAMION]
    for k in range(Vn.n):
        if Vn["base"][k] == b_c and Vn["modele"][k] == m and Vn["oid"][k] >= 0: LO._L(wn)["camions_pris"][int(Vn["oid"][k])] = 10 ** 9
    r_sans_camion = LO.convoi(wn, lieu_c, [nc], 100, dest)
    # sans gazole
    wg = pickle.loads(pickle.dumps(w, protocol=4)); g = wg.garnisons[lieu_c]
    wg.flux["brule"]["carburant"] += float(g["carburant"]); g["carburant"] = 0.0
    r_sans_gazole = LO.convoi(wg, lieu_c, [nc], 100, dest)
    # avec les deux
    av_t = total(w); carb0 = float(w.garnisons[lieu_c]["carburant"]); brule0 = float(w.flux["brule"]["carburant"])
    coups0 = LO.coups(w, nc)
    rc = LO.convoi(w, lieu_c, [nc], 100, dest)
    km = math.dist(pos, dest) * LO.DETOUR / 1000.0
    pas_att = int(math.ceil(km / LO.VITESSE_CONVOI_KMH * C.PAS_PAR_JOUR / 24.0))
    gazole_att = 2 * km * A.VEHICULE[LO.CAMION].unites_par_km
    ok_dep = rc["ok"] and rc["arrivee"] - rc["depart"] == pas_att and abs(rc["gazole"] - gazole_att) <= 1e-9 \
        and abs(carb0 - float(w.garnisons[lieu_c]["carburant"]) - gazole_att) <= 1e-9 \
        and abs(float(w.flux["brule"]["carburant"]) - brule0 - gazole_att) <= 1e-9
    pas_avant = True
    while int(w.pas) < rc["arrivee"] - 1:
        w.pas_suivant(); LO.avancer(w)
        if LO.coups(w, nc) != coups0: pas_avant = False
    while int(w.pas) < rc["arrivee"]:
        w.pas_suivant()
    livres = LO.avancer(w)
    charge = sum(rc["charge"].get(nc, {}).values())
    arrive = rc["id"] in livres and abs(LO.coups(w, nc) - coups0 - charge) <= 1e-9 and charge > 0
    ap_t = total(w)
    conserve5 = all(abs(ap_t[b] - av_t[b]) <= 1e-6 * max(1.0, av_t[b]) for b in av_t
                    if b not in ("mun_556", "mun_762", "mun_9mm", "mun_127", "pieces")) and not A.anomalies(w.pays)
    L5 = (not r_sans_camion["ok"] and "camion" in r_sans_camion["raison"] and not r_sans_gazole["ok"]
          and "gazole" in r_sans_gazole["raison"] and ok_dep and pas_avant and arrive and not A.anomalies(w.pays))
    R["L5"] = {"ok": L5, "sans_camion": r_sans_camion, "sans_gazole": r_sans_gazole, "km_aller": km, "pas_route": pas_att,
               "gazole": [rc.get("gazole"), gazole_att], "rien_avant": pas_avant, "arrive": arrive, "charge": charge,
               "conserve_hors_instruction": conserve5}
    print(f"  L5 convoi : {'OUI' if L5 else 'NON'} {R['L5']}", flush=True)
    # L6 : l identite
    wa, wb = pickle.loads(oct_), pickle.loads(oct_)
    ident = True
    for _ in range(2):
        T.jours(wa, 1); T.jours(wb, 1)
        if PE.empreinte_etendue(wa) != PE.empreinte_etendue(wb): ident = False
    R["L6"] = {"ok": ident}
    print(f"  L6 identite : {'OUI' if ident else 'NON'}", flush=True)
    oks = [R[k]["ok"] for k in ("L1", "L2", "L3", "L4", "L5", "L6")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 2a DE LA LOGISTIQUE : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_LOGISTIQUE", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
