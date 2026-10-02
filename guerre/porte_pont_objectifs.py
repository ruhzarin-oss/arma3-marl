"""Porte 1d-a du pont des objectifs, HORS LIGNE avec le faux pont ( HMT-192 ). Criteres ecrits avant la mesure ( Plane ) :

B1  les composants de Malden poses une fois chacun, commandes < 8 500 octets, OBJFIN juste.
B2  controle negatif : 5 composants absents ( les 5 premiers de centrale01 ) = exactement les 5 introuvables, « absent » ;
    les endommager ne change rien.
B3  controle positif : centrale01 entierement endommagee ; degats = poids trouve / poids total ; ceil( d x n ) groupes en
    panne.
B4  sans dommage, relever ne frappe rien ; identique au bit au jumeau sur 1 jour.
B5  depot01 a dommage 0,5 : degats 0,5, la moitie du carburant de l armee brule ( 1e-9 ).

Malden ( 1951 ), echelle 20.  python -m guerre.porte_pont_objectifs"""
import json
import math
import pickle
import sys
import time

from monde import archipel as AR, tests as T
from . import frappes as FR, pont_objectifs as PO
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_pont_objectifs.json"


def main():
    t0 = time.time(); R = {}
    print("PORTE 1d-a DU PONT DES OBJECTIFS : Malden 1951, faux pont", flush=True)
    w0 = AR.creer_ile("Malden", 1951, 20); oct_ = pickle.dumps(w0, protocol=4)
    # B1
    w = pickle.loads(oct_); fl = PO.FauxLiaison(); p = PO.PontObjectifs(w, "malden", fl)
    st = p.poser()
    b1 = st["composants"] == len(p.index) == st["trouves"] and max(fl.tailles) < PO.TAILLE_MAX and not p.introuvables
    R["B1"] = {"ok": b1, **st, "commandes": len(fl.tailles), "plus_grande": max(fl.tailles)}
    print(f"  B1 pose : {'OUI' if b1 else 'NON'} {R['B1']}", flush=True)
    # B2 et B3 : 5 absents a centrale01, puis toute la centrale endommagee
    w = pickle.loads(oct_)
    p0 = PO.PontObjectifs(w, "malden", PO.FauxLiaison())
    ks_c = [k for k, (o, c) in enumerate(p0.index) if o["id"] == "centrale01"]
    absents = ks_c[:5]
    fl = PO.FauxLiaison(absents=absents); p = PO.PontObjectifs(w, "malden", fl); p.poser()
    intro = sorted(k for k, _r in p.introuvables); raisons = {r for _k, r in p.introuvables}
    for k in absents: fl.objets[k][1] = 1.0                 # endommager un absent : le faux ne le rapporte pas
    rien = p.relever()
    b2 = intro == sorted(absents) and raisons == {"absent"} and rien == []
    for k in ks_c: fl.endommager(k, 1.0)
    out = p.relever()
    o_c = p.index[ks_c[0]][0]
    poids_trouves = sum(p.index[k][1]["poids"] for k in ks_c if k not in absents)
    d_att = poids_trouves / o_c["poids_total"]
    d_lu = next((d for oid, d, _e in out if oid == "centrale01"), None)
    us = [u for u in w.pays.domaine("energie").unites if u.lieu == "centrale01"]
    en_panne = sum(1 for u in us if u.en_panne and u.id in getattr(w, "groupes_frappes", set()))
    b3 = d_lu is not None and abs(d_lu - d_att) <= 1e-12 and en_panne == math.ceil(d_att * len(us) - 1e-9) and d_att < 1.0
    R["B2"] = {"ok": b2, "absents": absents, "introuvables": intro, "raisons": sorted(raisons), "relever_absents": rien}
    R["B3"] = {"ok": b3, "degats_attendus": d_att, "degats_lus": d_lu, "groupes": len(us), "en_panne": en_panne}
    print(f"  B2 controle negatif : {'OUI' if b2 else 'NON'} {R['B2']}", flush=True)
    print(f"  B3 controle positif : {'OUI' if b3 else 'NON'} {R['B3']}", flush=True)
    # B4 : sans dommage
    w1, w2 = pickle.loads(oct_), pickle.loads(oct_)
    p4 = PO.PontObjectifs(w1, "malden", PO.FauxLiaison()); p4.poser(); r4 = p4.relever()
    T.jours(w1, 1); T.jours(w2, 1)
    ident = PE.empreinte_etendue(w1) == PE.empreinte_etendue(w2)
    b4 = r4 == [] and ident
    R["B4"] = {"ok": b4, "frappes": r4, "identique": ident}
    print(f"  B4 sans dommage : {'OUI' if b4 else 'NON'} {R['B4']}", flush=True)
    # B5 : depot01 a moitie
    w5 = pickle.loads(oct_); fl5 = PO.FauxLiaison(); p5 = PO.PontObjectifs(w5, "malden", fl5); p5.poser()
    stock = float(w5.publics["armee"]["carburant"])
    for k, (o, c) in enumerate(p5.index):
        if o["id"] == "depot01": fl5.endommager(k, 0.5)
    out5 = p5.relever()
    d5 = next((d for oid, d, _e in out5 if oid == "depot01"), None)
    reste = float(w5.publics["armee"]["carburant"])
    b5 = d5 is not None and abs(d5 - 0.5) <= 1e-12 and abs(reste - 0.5 * stock) <= 1e-9 * max(1.0, stock)
    R["B5"] = {"ok": b5, "degats": d5, "stock": stock, "reste": reste}
    print(f"  B5 proportion : {'OUI' if b5 else 'NON'} {R['B5']}", flush=True)
    oks = [R[k]["ok"] for k in ("B1", "B2", "B3", "B4", "B5")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 1d-a DU PONT DES OBJECTIFS : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_PONT_OBJECTIFS", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
