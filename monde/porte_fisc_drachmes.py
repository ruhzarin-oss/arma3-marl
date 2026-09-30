"""PORTE DU FISC EN DRACHMES ( HMT-140 ( 2 ), 29/09, chef de projet ; criteres ecrits AVANT la mesure ; graines NEUVES 91,
92, 93 ). Le bareme de l IR converti en drachmes ( la loi est en euros ) ; le tourisme paie l IS de son resultat et la
retenue de 5 % sur ses dividendes, dont le net entre au revenu declare ( domaine 6 : impot_societes_hors_eco,
verser_dividende ) ; les dividendes du domaine 3 aussi au revenu declare.
F1 le bareme de la loi, exact : les six revenus et les huit cas de reduction de test_ir_par_tranches, en euros, convertis
   en drachmes - bareme_ir et impot_annuel rendent l impot de la loi converti, a 1e-9 pres ; controle positif : l ancien
   bareme ( tranches et reduction en euros appliquees aux drachmes ) se trompe d au moins une drachme sur au moins 3 des
   14 cas.
F2 le tourisme au fisc, une annee de l Altis par defaut ( 28 domaines, echelle 20 ; le monde nait le 15 juin ), sur
   chaque graine : les etablissements du tourisme paient l IS ( plus de 0 sur l annee ) ; la retenue sur leurs dividendes
   vaut 5 % de leurs dividendes bruts a 1e-6 pres ( grand livre ) ; controle positif : le temoin ( l ancien fisc ) ne
   preleve sur eux ni IS ni retenue.
F3 l effet, la meme annee, regle contre temoin : les recettes nettes d IR de l annee montent, de plus de 5 % et de moins
   de 60 % ; la conservation tient dans les deux bras.
Information ( pas un critere ) : le revenu net moyen des menages par personne et par mois ( ce qui leur est verse par
les autres classes, moins ce qu ils paient a l Etat ), regle moins temoin, sur l annee et sur l ete ( jours 0 a 90 ) ;
Classes attendait -40 a -70 euros.
   python -m monde.porte_fisc_drachmes [ graines ]"""
import sys, time, collections
import numpy as np
from multiprocessing import get_context
from .pays import pays as P, essais as E, d06_etat as ET, d28_tourisme as TO
from .pays.pays import EUROS_PAR_DRACHME as EUR
GRAINES = (91, 92, 93)
JOURS = 365
CAS = ((5000, 450.0), (10000, 900.0), (15000, 2000.0), (25000, 4500.0), (35000, 7700.0), (60000, 18300.0))
CAS2 = ((8000, 8000, 0, 0.0), (15000, 15000, 0, 1283.0), (20000, 20000, 2, 2360.0), (50000, 50000, 0, 13883.0),
        (60000, 60000, 0, 18300.0), (15000, 0, 0, 2000.0), (20000, 10000, 0, 2323.0), (30000, 30000, 5, 4340.0))


def _ancien_impot(y, ys, k):
    """L impot de l ancien bareme ( les euros de la loi appliques aux drachmes )."""
    b = float(ET.bareme_ir(y, ET.TAUX_IR, ET.TRANCHES_IR_EUROS))
    base = ET.REDUCTION_IR_EUROS[min(k, 4)] + 220.0 * max(0, k - 4)
    red = max(0.0, base - (0.0 if k >= 5 else 0.02 * max(0.0, ys - 12000.0)))
    ys = min(ys, y); part = ys / y if y > 0 else 0.0
    return max(0.0, b - min(b * part, red))


def f1():
    bar = [abs(float(ET.bareme_ir(y / EUR)) - v / EUR) <= 1e-9 * max(1.0, v) for y, v in CAS]
    red = [abs(float(ET.impot_annuel(y / EUR, ys / EUR, k)) - v / EUR) <= 1e-9 * max(1.0, v) for y, ys, k, v in CAS2]
    faux = sum(1 for y, v in CAS if abs(float(ET.bareme_ir(y / EUR, ET.TAUX_IR, ET.TRANCHES_IR_EUROS)) - v / EUR) >= 1.0)
    faux += sum(1 for y, ys, k, v in CAS2 if abs(_ancien_impot(y / EUR, ys / EUR, k) - v / EUR) >= 1.0)
    return all(bar), all(red), faux


def _mois_ancien(p):
    """Le dividende du tourisme d avant le 29/09 ( le temoin ) : ni IS ni retenue, hors du revenu declare."""
    if p.jour == 0 or p.jour % TO.ECO.MOIS_J: return
    d = TO._dom(p); L = p.socle.livre
    for e in d.etablissements:
        x = e.caisse - TO.RESERVE_DIVIDENDE_J * TO._cout_jour_plein(p, e, max(TO.OCCUPATION_MOIS))
        if x > 1.0 and e.proprietaire is not None: d.cumul["dividendes"] += L.transferer(e, e.proprietaire, x, "dividende")


def _jouer(args):
    graine, regle = args
    t0 = time.time()
    if not regle:                                    # le temoin : l ancien fisc, pose AVANT l installation
        ET.REDUCTION_IR = ET.REDUCTION_IR_EUROS; ET.REDUCTION_PAR_ENFANT_SUP = 220.0; ET.SEUIL_DEGRESSIVITE = 12000.0
        ET._declarer_revenu = lambda p, menage, montant: None
        TO._mois = _mois_ancien
    w, _ = E.monde([nom for nom, mod, _ in P.DOMAINES], graine=graine, echelle=20.0)
    p = w.pays; tb = w.table
    if not regle: ET._etat(p).fisc.tranches_ir = tuple(ET.TRANCHES_IR_EUROS)
    an, ete = collections.Counter(), collections.Counter(); pop = []
    j0 = int(w.jour); vu = j0
    while int(w.jour) < j0 + JOURS:
        w.pas_suivant()
        if int(w.jour) == vu: continue
        vu = int(w.jour); fini = vu - j0 - 1
        pop.append(int(tb.vivant[:tb.n].sum()))
        for m, pa, re, s_, _ in p.comptes_hier["argent"]:
            an[(m, pa, re)] += s_
            if fini < 90: ete[(m, pa, re)] += s_
    tour = {re for (m, pa, re) in an if m == "recette_touristique"}
    s = lambda c, f: float(sum(v for k, v in c.items() if f(*k)))
    is_t = s(an, lambda m, pa, re: m == "impot_societes" and pa in tour)
    ret_t = s(an, lambda m, pa, re: m == "retenue_dividende" and pa in tour)
    net_t = s(an, lambda m, pa, re: m == "dividende" and pa in tour)
    ir = s(an, lambda m, pa, re: m == "retenue_ir") - s(an, lambda m, pa, re: m == "remboursement_ir")
    rev = lambda c: s(c, lambda m, pa, re: re == "Menage" and pa != "Menage") - s(c, lambda m, pa, re: pa == "Menage" and re == "Gouvernement")
    habitants = float(np.mean(pop))
    return {"graine": graine, "regle": regle, "classes_tourisme": sorted(tour), "is_tourisme": round(is_t),
            "retenue_tourisme": round(ret_t, 2), "dividendes_tourisme_bruts": round(ret_t + net_t, 2),
            "ir_net": round(ir), "revenu_mois_personne": round(rev(an) / habitants / (JOURS / 30.0), 2),
            "revenu_mois_personne_ete": round(rev(ete) / float(np.mean(pop[:90])) / 3.0, 2),
            "conservation": bool(p.socle.conservation.tenue()[0]), "secondes": round(time.time() - t0)}


def main():
    graines = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else list(GRAINES)
    t0 = time.time(); ok = {}
    bar, red, faux = f1()
    ok["F1 le bareme de la loi converti, exact ( six revenus, huit reductions )"] = bar and red
    ok[f"F1 controle positif : l ancien bareme se trompe ( {faux} cas sur 14, au moins 3 )"] = faux >= 3
    with get_context("spawn").Pool(2, maxtasksperchild=1) as pool:
        rs = pool.map(_jouer, [(g, r) for g in graines for r in (True, False)])
    for r in rs: print("  ", r, flush=True)
    for g in graines:
        R = next(r for r in rs if r["graine"] == g and r["regle"]); T = next(r for r in rs if r["graine"] == g and not r["regle"])
        brut = R["dividendes_tourisme_bruts"]
        ok[f"F2 graine {g} : le tourisme paie l IS ( {R['is_tourisme']} ) et 5 % sur ses dividendes ( {R['retenue_tourisme']} sur {brut} )"] = (
            R["is_tourisme"] > 0 and brut > 0 and abs(R["retenue_tourisme"] - 0.05 * brut) <= 1e-6 * brut + 0.01)
        ok[f"F2 graine {g} : controle positif, le temoin ne preleve rien sur le tourisme ( IS {T['is_tourisme']}, retenue {T['retenue_tourisme']} )"] = (
            T["is_tourisme"] == 0 and T["retenue_tourisme"] == 0)
        hausse = R["ir_net"] / max(1.0, T["ir_net"]) - 1.0
        ok[f"F3 graine {g} : l IR net de l annee monte de {100 * hausse:.1f} % ( entre 5 et 60 ) ; conservation"] = (
            0.05 < hausse < 0.60 and R["conservation"] and T["conservation"])
        print(f"   information graine {g} : revenu net par personne et par mois, regle moins temoin : annee "
              f"{R['revenu_mois_personne'] - T['revenu_mois_personne']:+.2f}, ete {R['revenu_mois_personne_ete'] - T['revenu_mois_personne_ete']:+.2f} "
              f"( drachmes ; x {EUR} en euros )", flush=True)
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DU FISC EN DRACHMES : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
