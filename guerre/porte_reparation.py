"""Porte de la reparation reelle ( HMT-192, etape 1c ). Criteres ecrits avant la mesure ( Plane, amendes avant toute
mesure sur la graine 1941 ) :

P1  durees : centrale01 payee par l Etat, a degats 1 : panne_jusqu - pas = 365 j ; a 0,3 : 60 j ; port01 : 7 j ; fonderie01
    non payee : machines a l attente ( repar_h = ATTENTE_H ), refus compte, toujours en panne au jour 3.
P2  paiement ( centrale a degats 1 ) : declarer_import rend montant_fob x ( 1 + fret produit_fini ), montant_fob = somme des
    prix au Parc des groupes frappes ; caisse de l Etat apres = max( caisse avant, paye ) - paye.
P3  sans paiement ( durees raccourcies : centrale 2 j, port 3 j ) : port01 detruit ( blocus ), centrale01 a 0,3 en attente,
    toujours en panne au jour 2 ; payee a la retentative de 7 h apres la reouverture ; en service au plus tard au jour 6.
P4  identite : frappe a dommages nuls sur tous les objectifs, identique au bit au jumeau ( 3 jours ), aucune routine posee.

Malden ( 1941 ), echelle 20 ; chaque cas sur une copie.
python -m guerre.porte_reparation"""
import json
import pickle
import sys
import time

from monde import archipel as AR, config as C, tests as T
from monde.pays import d07_exterieur as X, d10_industrie as IN
from monde.socle import objets as O
from . import frappes as FR, objectifs as OB
from .porte_frappes import jumeaux

SORTIE = "/mnt/data/hmt/arsenal/porte_reparation.json"
J = C.PAS_PAR_JOUR


def tout(o, v=1.0): return {c["i"]: v for c in o["composants"]}


def groupes_frappes(w):
    ids = getattr(w, "groupes_frappes", set())
    return [u for u in w.pays.domaine("energie").unites if u.id in ids]


def main():
    t0 = time.time(); R = {}
    print("PORTE DE LA REPARATION : Malden 1941", flush=True)
    w0 = AR.creer_ile("Malden", 1941, 20); oct_ = pickle.dumps(w0, protocol=4)
    objs = {o["id"]: o for o in OB.objectifs_carte("malden")}
    c, f, po = objs["centrale01"], objs["fonderie01"], objs["port01"]
    # P1 et P2 : la centrale a degats 1
    wa = pickle.loads(oct_); pas0 = int(wa.pas); c0 = float(wa.gouv.caisse)
    _d, eff = FR.frapper(wa, c, tout(c))
    r = wa.reparations["centrale01"]; us = groupes_frappes(wa)
    duree1 = sorted({u.panne_jusqu - pas0 for u in us})
    parc = wa.pays.socle.parc
    fob = sum(parc.modeles[u.objet.modele].prix_monde for u in us)
    paye = r.get("paye_dr") or 0.0
    attendu = fob * (1.0 + X.FRET.get("produit_fini", 0.05))
    c1 = float(wa.gouv.caisse)
    P2 = (r.get("paye_pas") == pas0 and abs(r["montant_fob"] - fob) <= 1e-9 * max(1.0, fob)
          and abs(paye - attendu) <= 1e-9 * max(1.0, attendu) and abs(c1 - (max(c0, paye) - paye)) <= 1e-6 * max(1.0, c0, paye))
    # a degats 0,3
    wb = pickle.loads(oct_); FR.frapper(wb, c, tout(c, 0.3)); ub = groupes_frappes(wb)
    duree03 = sorted({u.panne_jusqu - pas0 for u in ub})
    # le port
    wc = pickle.loads(oct_); FR.frapper(wc, po, tout(po)); port = wc.ports_hors_service.get("port01", 0) - pas0
    # la fonderie, non payee
    wd = pickle.loads(oct_); FR.frapper(wd, f, tout(f)); rd = wd.reparations["fonderie01"]
    ms = [m for s in IN._dom(wd.pays).sites if s.entreprise.lieu.id == "fonderie01" for a in s.ateliers for m in a.machines
          if m.objet.id in rd["materiel"]]
    attente0 = all(m.repar_h == FR.ATTENTE_H for m in ms) and rd.get("paye_pas") is None and rd.get("refus", 0) >= 1
    T.jours(wd, 3)
    panne3 = all(m.objet.etat == O.PANNE for m in ms) and rd.get("paye_pas") is None
    P1 = (duree1 == [int(round(365 * J))] and duree03 == [int(round(60 * J))] and len(ub) == 3
          and port == int(round(7 * J)) and bool(ms) and attente0 and panne3)
    R["P1"] = {"ok": P1, "centrale_1": duree1, "centrale_0_3": duree03, "groupes_0_3": len(ub), "port": port,
               "fonderie_machines": len(ms), "fonderie_attente": attente0, "fonderie_panne_j3": panne3,
               "fonderie_montant_fob": rd["montant_fob"], "fonderie_refus": rd.get("refus")}
    R["P2"] = {"ok": P2, "fob": fob, "paye": paye, "attendu": attendu, "caisse_avant": c0, "caisse_apres": c1}
    print(f"  P1 durees : {'OUI' if P1 else 'NON'} {R['P1']}", flush=True)
    print(f"  P2 paiement : {'OUI' if P2 else 'NON'} {R['P2']}", flush=True)
    # P3 : sans paiement tant que le port est detruit
    sauve = dict(FR.DUREE_REPARATION_J); FR.DUREE_REPARATION_J.update(centrale=2.0, port=3.0)
    try:
        we = pickle.loads(oct_)
        FR.frapper(we, po, tout(po)); bloc = X.sous_blocus(we.pays)
        FR.frapper(we, c, tout(c, 0.3)); re_ = we.reparations["centrale01"]; ue = groupes_frappes(we)
        attente = re_.get("paye_pas") is None
        T.jours(we, 2); panne2 = all(u.en_panne for u in ue) and re_.get("paye_pas") is None
        T.jours(we, 4); service6 = not any(u.en_panne for u in ue) and re_.get("paye_pas") is not None
        paye_jour = None if re_.get("paye_pas") is None else (re_["paye_pas"] - pas0) / J
    finally:
        FR.DUREE_REPARATION_J.clear(); FR.DUREE_REPARATION_J.update(sauve)
    P3 = bloc and attente and panne2 and service6 and len(ue) == 3
    R["P3"] = {"ok": P3, "blocus": bloc, "attente": attente, "panne_j2": panne2, "service_j6": service6,
               "paye_au_jour": paye_jour, "refus": re_.get("refus")}
    print(f"  P3 sans paiement : {'OUI' if P3 else 'NON'} {R['P3']}", flush=True)
    # P4 : l identite
    w4 = {}
    def frappe_nulle(w):
        for o in objs.values(): FR.frapper(w, o, {})
        w4["routine"] = getattr(w, "routine_reparations", False)
    _, _, ident = jumeaux(oct_, 3, avant=frappe_nulle)
    P4 = ident and not w4["routine"]
    R["P4"] = {"ok": P4, "identique": ident, "routine": w4["routine"]}
    print(f"  P4 identite : {'OUI' if P4 else 'NON'} {R['P4']}", flush=True)
    verdict = "FRANCHIE" if (P1 and P2 and P3 and P4) else "REFUSEE"
    R.update(verdict=verdict, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE DE LA REPARATION : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_REPARATION", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
