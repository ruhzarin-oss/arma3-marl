"""Porte des frappes sur les objectifs reels ( HMT-192, etape 1b ). Criteres ecrits avant la mesure ( Plane ).
Malden ( 1931 ) et Stratis ( 1932 ), echelle 20 ; chaque frappe sur une COPIE du monde, contre son jumeau non frappe.

F0  frappe a dommages nuls sur tous les objectifs de Malden : identique au bit au jumeau ( 3 jours ).
F1  centrale01 a degats 1 : tous ses groupes en panne « frappe », 3 jours ; a degats 0,5 : exactement ceil( 0,5 n ) ;
    chez le jumeau, aucun.
F2  fonderie01 a degats 1 : production des 5 jours <= 5 % du jumeau ; a duree raccourcie ( 2 journees de poste ),
    > 50 % du jumeau sur les jours 4 a 6.
F3  depot01 a degats 1 : carburant de l armee a 0 ; flux « brule » + ce stock ; ecarts de conservation inchanges.
F4  base02 a degats 1 : vehicules detruits ( Parc +n ) ; munitions, pieces, carburant de garnison a 0 ; anomalies vides ;
    recoupement de l etat des lieux 0 ecart.
F5  Stratis port01 a degats 1 : sous_blocus vrai, avis aux voyageurs du domaine 28 a 0 ; jumeau faux ; a duree raccourcie
    ( 2 jours ), faux au jour 3.
F6  Stratis aeroport01 a degats 1 : identique au bit au jumeau ( 3 jours ).

python -m guerre.porte_frappes"""
import json
import math
import pickle
import sys
import time

from monde import archipel as AR, tests as T
from monde.pays import d10_industrie as IN, d25_armee as A, d07_exterieur as X
from . import frappes as FR, objectifs as OB
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_frappes.json"
PROD = {}                          # ( id du monde, lieu ) -> unites produites ( instrument, le meme dans chaque bras )
_ORIG = IN._produire_bien


def _compter(p, D_, s, b, q):
    k = (id(p.w), s.entreprise.lieu.id); PROD[k] = PROD.get(k, 0.0) + q
    return _ORIG(p, D_, s, b, q)


IN._produire_bien = _compter


def tout(o, v=1.0): return {c["i"]: v for c in o["composants"]}


def jumeaux(octets, jours, avant=None, apres=None):
    """Deux copies ; `avant(w)` sur la premiere ; rend ( w1, w2, identiques chaque jour )."""
    w1, w2 = pickle.loads(octets), pickle.loads(octets)
    if avant: avant(w1)
    ok = True
    for _ in range(jours):
        T.jours(w1, 1); T.jours(w2, 1)
        if PE.empreinte_etendue(w1) != PE.empreinte_etendue(w2): ok = False
    return w1, w2, ok


def groupes(w, lid):
    return sorted((u for u in w.pays.domaine("energie").unites if u.lieu == lid), key=lambda u: u.id)


def main():
    t0 = time.time(); R = {}
    print("PORTE DES FRAPPES : Malden 1931", flush=True)
    wM = AR.creer_ile("Malden", 1931, 20); oM = pickle.dumps(wM, protocol=4)
    objM = {o["id"]: o for o in OB.objectifs_carte("malden")}
    # F0
    _, _, F0 = jumeaux(oM, 3, avant=lambda w: [FR.frapper(w, o, {}) for o in objM.values()])
    R["F0"] = F0; print(f"  F0 identite a dommages nuls : {'OUI' if F0 else 'NON'}", flush=True)
    # F1
    c = objM["centrale01"]
    w1 = pickle.loads(oM); d1, e1 = FR.frapper(w1, c, tout(c)); us = groupes(w1, "centrale01")
    tenus = all(u.en_panne for u in us)
    for _ in range(3):
        T.jours(w1, 1); tenus = tenus and all(u.en_panne for u in groupes(w1, "centrale01"))
    w5 = pickle.loads(oM); d5, e5 = FR.frapper(w5, c, tout(c, 0.5))
    n5 = sum(1 for u in groupes(w5, "centrale01") if u.id in w5.groupes_frappes)
    wj = pickle.loads(oM); T.jours(wj, 3)
    jumeau_frappe = len(getattr(wj, "groupes_frappes", ()))
    F1 = bool(us) and d1 == 1.0 and tenus and n5 == math.ceil(0.5 * len(us)) and abs(d5 - 0.5) < 1e-9 and jumeau_frappe == 0
    R["F1"] = {"ok": F1, "groupes": len(us), "tenus_3j": tenus, "a_0_5": n5, "degats_0_5": d5, "jumeau": jumeau_frappe}
    print(f"  F1 centrale : {'OUI' if F1 else 'NON'} {R['F1']}", flush=True)
    # F2
    f = objM["fonderie01"]
    wa = pickle.loads(oM); wt = pickle.loads(oM)
    base = {id(x): PROD.get((id(x), "fonderie01"), 0.0) for x in (wa, wt)}   # un id peut resservir apres un monde libere
    FR.frapper(wa, f, tout(f))
    for _ in range(5): T.jours(wa, 1); T.jours(wt, 1)
    pa, pt = (PROD.get((id(x), "fonderie01"), 0.0) - base[id(x)] for x in (wa, wt))
    sauve = FR.DUREE_REPARATION_J["fonderie"]; FR.DUREE_REPARATION_J["fonderie"] = 2.0
    try:
        ws = pickle.loads(oM); wt2 = pickle.loads(oM); FR.frapper(ws, f, tout(f))
    finally:
        FR.DUREE_REPARATION_J["fonderie"] = sauve
    for _ in range(3): T.jours(ws, 1); T.jours(wt2, 1)
    s0, t0_ = PROD.get((id(ws), "fonderie01"), 0.0), PROD.get((id(wt2), "fonderie01"), 0.0)        # les jours 4 a 6 : une difference
    for _ in range(3): T.jours(ws, 1); T.jours(wt2, 1)
    s46 = PROD.get((id(ws), "fonderie01"), 0.0) - s0; t46 = PROD.get((id(wt2), "fonderie01"), 0.0) - t0_
    F2 = pt > 0 and pa <= 0.05 * pt and t46 > 0 and s46 > 0.5 * t46
    R["F2"] = {"ok": F2, "frappee_5j": pa, "jumeau_5j": pt, "reparee_j4_6": s46, "jumeau_j4_6": t46}
    print(f"  F2 fonderie : {'OUI' if F2 else 'NON'} {R['F2']}", flush=True)
    # F3
    dep = objM["depot01"]
    w3 = pickle.loads(oM)
    stock = float(w3.publics["armee"]["carburant"]); brule = float(w3.flux["brule"]["carburant"])
    da, db = w3.verifier_conservation()
    FR.frapper(w3, dep, tout(dep))
    da2, db2 = w3.verifier_conservation()
    F3 = (stock > 0 and float(w3.publics["armee"]["carburant"]) == 0.0
          and abs(float(w3.flux["brule"]["carburant"]) - brule - stock) <= 1e-9 * max(1.0, stock)
          and abs(da2 - da) <= 1e-6 and all(abs(db2[k] - db[k]) <= 1e-6 for k in db))
    R["F3"] = {"ok": F3, "stock": stock, "brule_plus": float(w3.flux["brule"]["carburant"]) - brule,
               "conservation_avant": [da, max(abs(v) for v in db.values())], "apres": [da2, max(abs(v) for v in db2.values())]}
    print(f"  F3 depot : {'OUI' if F3 else 'NON'} {R['F3']}", flush=True)
    # F4
    b = objM["base02"]
    w4 = pickle.loads(oM); p4 = w4.pays; d4 = p4.domaines[A.DOMAINE]; V = d4.veh; bn = w4.carte.lieux["base02"].n
    n_av = sum(1 for k in range(V.n) if V["base"][k] == bn and V["oid"][k] >= 0)
    det_av = sum(p4.socle.parc.comptes[d4.mids[v.nom]]["detruit"] for v in A.VEHICULES)
    FR.frapper(w4, b, tout(b))
    n_ap = sum(1 for k in range(V.n) if V["base"][k] == bn and V["oid"][k] >= 0)
    det_ap = sum(p4.socle.parc.comptes[d4.mids[v.nom]]["detruit"] for v in A.VEHICULES)
    arm = A.armurerie(p4, "base02")
    restes = {x: float(arm.stock[d4.bids[x]]) for x in A.NOMS_MUNITIONS + ("pieces",)}
    garn = float(w4.garnisons["base02"]["carburant"])
    an = A.anomalies(p4); ecarts, _e = PE.recouper(w4)
    F4 = n_av > 0 and n_ap == 0 and det_ap - det_av == n_av and all(v == 0 for v in restes.values()) and garn == 0 \
        and not an and not ecarts
    R["F4"] = {"ok": F4, "vehicules": [n_av, n_ap], "detruits_plus": det_ap - det_av, "restes": restes, "garnison": garn,
               "anomalies": an[:5], "ecarts": ecarts[:5]}
    print(f"  F4 base : {'OUI' if F4 else 'NON'} {R['F4']}", flush=True)
    print("PORTE DES FRAPPES : Stratis 1932", flush=True)
    wS = AR.creer_ile("Stratis", 1932, 20); oS = pickle.dumps(wS, protocol=4)
    objS = {o["id"]: o for o in OB.objectifs_carte("stratis")}
    # F5
    po = objS["port01"]
    w5a = pickle.loads(oS); FR.frapper(w5a, po, tout(po))
    bloc = X.sous_blocus(w5a.pays)
    avis = None
    if w5a.pays.a("tourisme"):
        from monde.pays import d28_tourisme as TO
        avis = TO.avis(w5a.pays)
    w5j = pickle.loads(oS); bloc_j = X.sous_blocus(w5j.pays)
    sauve = FR.DUREE_REPARATION_J["port"]; FR.DUREE_REPARATION_J["port"] = 2.0
    try:
        w5c = pickle.loads(oS); FR.frapper(w5c, po, tout(po))
    finally:
        FR.DUREE_REPARATION_J["port"] = sauve
    bloc_c0 = X.sous_blocus(w5c.pays)
    T.jours(w5c, 3); bloc_c3 = X.sous_blocus(w5c.pays)
    F5 = bloc and (avis is None or avis == 0.0) and not bloc_j and bloc_c0 and not bloc_c3
    R["F5"] = {"ok": F5, "sous_blocus": bloc, "avis_tourisme": avis, "jumeau": bloc_j, "court_j0": bloc_c0, "court_j3": bloc_c3}
    print(f"  F5 port : {'OUI' if F5 else 'NON'} {R['F5']}", flush=True)
    # F6
    ae = objS["aeroport01"]
    _, _, F6 = jumeaux(oS, 3, avant=lambda w: FR.frapper(w, ae, tout(ae)))
    R["F6"] = F6; print(f"  F6 aeroport sans effet : {'OUI' if F6 else 'NON'}", flush=True)
    oks = [R["F0"], R["F1"]["ok"], R["F2"]["ok"], R["F3"]["ok"], R["F4"]["ok"], R["F5"]["ok"], R["F6"]]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"F0..F6 {oks}")
    print(f"PORTE DES FRAPPES : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_FRAPPES", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
