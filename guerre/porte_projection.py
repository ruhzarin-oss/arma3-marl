"""Porte 4a de la flotte de projection ( HMT-197 ). Criteres ecrits avant la mesure ( Plane, 03/10 ) : Malden ( 2031 ),
echelle 20.

P1  l achat : l Etat paie exactement ce que rend d07.declarer_import ( FOB converti, fret compris ) ; l objet entre au
    Parc ( source importe, proprietaire le depot national ) au port ( chaland ), a l aerodrome ou a la capitale ( avion ) ;
    sous blocus, rien n est paye ni cree.
P2  la traversee : refusee au-dela de la capacite, sans engin libre, sans carburant ( avec sa raison ) ; sinon duree =
    km / vitesse ( + bloc ), carburant brule = consommation x duree de l aller ( le retour au retour ), au grand livre
    ( nature brule ) ; l engin reserve jusqu au retour.
P3  identite : sans achat ni traversee, identique au bit sur 2 jours.
python -m guerre.porte_projection [ graine ]"""
import json
import math
import pickle
import sys
import time

from monde import archipel as AR, config as C, tests as T
from monde.pays import d07_exterieur as X, d26_armee_soutien as S
from . import projection as PR
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_projection.json"


def brule(w, bien):
    return float(w.flux["brule"].get(bien, 0.0))


def main(graine=2031):
    t0 = time.time(); R = {}
    print(f"PORTE 4a DE LA FLOTTE DE PROJECTION : Malden {graine}", flush=True)
    w0 = AR.creer_ile("Malden", graine, 20); T.jours(w0, 1)
    oct_ = pickle.dumps(w0, protocol=4)
    # P1 ( amende avant la mesure : des mondes separes ; les devises ne paient qu un avion OU quelques chalands )
    def achat(w, nom, n):
        p = w.pays; parc = p.socle.parc; d = S._dom(p)
        m = PR.MODELES[nom]; attendu_un = S._dr(m.prix_eur) * (1.0 + X.FRET["produit_fini"])
        r = PR.acheter(w, nom, n); mid = PR._P(w)["mids"][nom]
        objs = [parc.objets[o] for o in r["objets"]]; lieu = PR.lieu_de_base(w, nom)
        ok = (r["achetes"] == n and abs(r["paye"] - n * attendu_un) <= 1e-6 * attendu_un
              and all(o.modele == mid and o.proprietaire is d.national and o.lieu == lieu for o in objs)
              and parc.comptes[mid]["importe"] == n)
        return {"ok": ok, "achetes": r["achetes"], "paye": r["paye"], "attendu": n * attendu_un, "lieu": lieu,
                "importe": parc.comptes[mid]["importe"]}
    w = pickle.loads(oct_); out = {"chalands": achat(w, "lcu", 2)}
    wv = pickle.loads(oct_); out["avion"] = achat(wv, "c130j", 1)
    wd = pickle.loads(oct_); PR.acheter(wd, "lcu", 2); caisse_d = float(wd.gouv.caisse)
    rd = PR.acheter(wd, "c130j", 1)
    devises = rd["achetes"] == 0 and rd["paye"] == 0.0 and not any(x == "c130j" for x in PR._P(wd)["flotte"].values())
    wb = pickle.loads(oct_); pb = wb.pays
    wb.ports_hors_service = {l: 10 ** 9 for l, x in wb.carte.lieux.items() if x.type == "port"}
    caisse_b = float(wb.gouv.caisse); rb = PR.acheter(wb, "lcu", 1)
    bloque = X.sous_blocus(pb) and rb["achetes"] == 0 and rb["paye"] == 0.0 and float(wb.gouv.caisse) == caisse_b \
        and not PR._P(wb)["flotte"]
    P1 = out["chalands"]["ok"] and out["avion"]["ok"] and devises and bloque
    R["P1"] = {"ok": P1, **out, "devises": {"ok": devises, "resultat": rd}, "blocus": {"ok": bloque, "sous_blocus": X.sous_blocus(pb)}}
    print(f"  P1 achat : {'OUI' if P1 else 'NON'} {R['P1']}", flush=True)
    p = w.pays; d = S._dom(p)
    # P2 : le chaland sur ( a ), l avion sur ( b )
    oct1 = pickle.dumps(wv, protocol=4); oct_ch = pickle.dumps(w, protocol=4)
    res = {}
    lcu = PR.MODELES["lcu"]; avion = PR.MODELES["c130j"]
    res["trop"] = PR.traverser(w, "lcu", 900)
    g0 = S._quantite(p, d, "depot", d.national.k, "carburant"); b0 = brule(w, "carburant")
    r_ok = PR.traverser(w, "lcu", 600)
    h = PR.KM_TRAVERSEE / lcu.vitesse_kmh
    q_att = lcu.unites_h() * h * 2
    pas_att = math.ceil(h * C.PAS_PAR_JOUR / 24.0 - 1e-9)
    g1 = S._quantite(p, d, "depot", d.national.k, "carburant"); b1 = brule(w, "carburant")
    res["deuxieme"] = PR.traverser(w, "lcu", 10)
    ok_lcu = (not res["trop"]["ok"] and "capacite" in res["trop"]["raison"] and r_ok["ok"] and len(r_ok["engins"]) == 2
              and abs(r_ok["carburant"] - q_att) <= 1e-9 and abs(g0 - g1 - q_att) <= 1e-9 and abs(b1 - b0 - q_att) <= 1e-9
              and r_ok["arrivee"] - r_ok["depart"] == pas_att and r_ok["retour"] - r_ok["depart"] == 2 * pas_att
              and not res["deuxieme"]["ok"] and "libre" in res["deuxieme"]["raison"])
    # le retour : rien avant, le carburant du retour au retour
    avant_retour = PR.rentrer(w)
    while int(w.pas) < r_ok["retour"]: w.pas_suivant()
    g2 = S._quantite(p, d, "depot", d.national.k, "carburant")
    clos = PR.rentrer(w)
    g3 = S._quantite(p, d, "depot", d.national.k, "carburant")
    ok_retour = avant_retour == [] and r_ok["id"] in clos and abs(g2 - g3 - q_att) <= 1e-6 and len(PR.libres(w, "lcu")) == 2
    # l avion : parachutistes et kerosene
    wa = pickle.loads(oct1); pa = wa.pays; da = S._dom(pa)
    trop_para = PR.traverser(wa, "c130j", 100, parachutage=True)
    k0 = S._quantite(pa, da, "depot", da.national.k, "kerosene")
    ra = PR.traverser(wa, "c130j", 60, parachutage=True)
    ha = PR.KM_TRAVERSEE / avion.vitesse_kmh + avion.bloc_h
    qa = avion.unites_h() * ha * 1
    k1 = S._quantite(pa, da, "depot", da.national.k, "kerosene")
    para_chaland = PR.traverser(wa, "lcu", 10, parachutage=True)
    ok_avion = (not trop_para["ok"] and "capacite" in trop_para["raison"] and ra["ok"] and len(ra["engins"]) == 1
                and abs(k0 - k1 - qa) <= 1e-9 and not para_chaland["ok"])
    # sans carburant
    wc = pickle.loads(oct_ch); wc.publics["armee"]["carburant"] = 0.0
    sans = PR.traverser(wc, "lcu", 100)
    ok_sans = not sans["ok"] and "carburant" in sans["raison"]
    P2 = ok_lcu and ok_retour and ok_avion and ok_sans
    R["P2"] = {"ok": P2, "chaland": {"ok": ok_lcu, "trop": res["trop"], "traversee": {k: r_ok.get(k) for k in ("engins", "depart", "arrivee", "retour", "carburant")},
               "carburant_attendu": q_att, "pas_attendus": pas_att, "deuxieme": res["deuxieme"]},
               "retour": {"ok": ok_retour, "rien_avant": avant_retour, "clos": clos, "brule_au_retour": g2 - g3},
               "avion": {"ok": ok_avion, "trop": trop_para, "kerosene": [k0, k1, qa], "chaland_parachutage": para_chaland},
               "sans_carburant": {"ok": ok_sans, "resultat": sans}, "capacite_par_jour": PR.capacite_par_jour(w)}
    print(f"  P2 traversee : {'OUI' if P2 else 'NON'} {R['P2']}", flush=True)
    # P3
    w1, w2 = pickle.loads(oct_), pickle.loads(oct_); ident = True
    for _ in range(2):
        T.jours(w1, 1); T.jours(w2, 1)
        if PE.empreinte_etendue(w1) != PE.empreinte_etendue(w2): ident = False
    R["P3"] = {"ok": ident}
    print(f"  P3 identite : {'OUI' if ident else 'NON'}", flush=True)
    oks = [R[k]["ok"] for k in ("P1", "P2", "P3")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graine=graine, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 4a DE LA FLOTTE DE PROJECTION : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_PROJECTION", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2031))
