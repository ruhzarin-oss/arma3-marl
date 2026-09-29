"""PORTE DU DIVIDENDE DU TOURISME ( HMT-140 ( 3 ), 29/09, chef de projet ; criteres ecrits AVANT la mesure ; graines
NEUVES 101, 102, 103 ). L Altis par defaut ( 28 domaines, echelle 20 ; le monde nait le 15 juin ), une annee, deux bras
par graine : la REGLE ( la moitie du resultat net apres l IS, 8 % aux proprietaires etrangers, 0,18 lit par habitant )
et le TEMOIN ( l etat de la cause 2 : toute la caisse au-dela de 30 jours de personnel, aucun etranger, 0,25 lit ).
D1 la regle : sur l annee, les dividendes bruts du tourisme ( residents et etrangers ) ne depassent pas la moitie de la
   somme de ses resultats nets positifs du mois ( 1e-6 pres ) ; la part etrangere fait 8 % des dividendes a un demi-point
   pres ( les devises refusees la reduisent ) ; la retenue vaut 5 % des dividendes bruts ( 1e-6 pres ) ; controle
   positif : le temoin distribue plus de la moitie de ses resultats nets positifs.
D2 les lits : a l installation, les lits du tourisme valent entre 0,17 et 0,19 par habitant ( l arrondi par lieu ).
D3 l annee : les dividendes verses aux menages residents sont plus bas que dans le temoin ; aucun etablissement n a de
   caisse negative ; la conservation tient dans les deux bras.
Information ( pas un critere ) : le revenu net moyen des menages par personne et par mois, regle moins temoin, sur
l annee et sur l ete ( jours 0 a 90 ) ; Classes attendait -80 a -100 euros sur l annee.
   python -m monde.porte_dividende_tourisme [ graines ]"""
import sys, time, collections
import numpy as np
from multiprocessing import get_context
from .pays import pays as P, essais as E, d06_etat as ET, d28_tourisme as TO
from .pays.pays import EUROS_PAR_DRACHME as EUR
GRAINES = (101, 102, 103)
JOURS = 365


def _mois_cause2(p):
    """Le dividende du tourisme de la cause 2 ( le temoin ) : l IS du mois, puis toute la caisse au-dela de la reserve."""
    if p.jour == 0 or p.jour % TO.ECO.MOIS_J: return
    d = TO._dom(p)
    for e in d.etablissements:
        base = getattr(e, "caisse_mois", None)
        if base is not None: ET.impot_societes_hors_eco(p, e, e.caisse - base)
        x = e.caisse - TO.RESERVE_DIVIDENDE_J * TO._cout_jour_plein(p, e, max(TO.OCCUPATION_MOIS))
        if x > 1.0 and e.proprietaire is not None: d.cumul["dividendes"] += ET.verser_dividende(p, e, e.proprietaire, x)
        e.caisse_mois = e.caisse


def _jouer(args):
    graine, regle = args
    t0 = time.time()
    if not regle:                                    # le temoin, pose AVANT l installation
        TO._mois = _mois_cause2; TO.LITS_PAR_HABITANT = 0.25; TO.PART_ETRANGERE = 0.0
    nets = []; is0 = ET.impot_societes_hors_eco

    def impot(p_, unite, resultat):
        i = is0(p_, unite, resultat)
        if str(getattr(unite, "id", "")).startswith("tourisme@") and resultat - i > 0: nets.append(resultat - i)
        return i
    ET.impot_societes_hors_eco = impot
    w, _ = E.monde([nom for nom, mod, _ in P.DOMAINES], graine=graine, echelle=20.0)
    p = w.pays; tb = w.table; d = TO._dom(p)
    lits = sum(e.lits for e in d.etablissements) / max(1, int(tb.vivant[:tb.n].sum()))
    an, ete = collections.Counter(), collections.Counter(); pop = []; negatif = False
    j0 = int(w.jour); vu = j0
    while int(w.jour) < j0 + JOURS:
        w.pas_suivant()
        if int(w.jour) == vu: continue
        vu = int(w.jour); fini = vu - j0 - 1
        pop.append(int(tb.vivant[:tb.n].sum()))
        negatif |= any(e.caisse < -1e-6 for e in d.etablissements)
        for m, pa, re, s_, _ in p.comptes_hier["argent"]:
            an[(m, pa, re)] += s_
            if fini < 90: ete[(m, pa, re)] += s_
    tour = {re for (m, pa, re) in an if m == "recette_touristique"}
    s = lambda c, f: float(sum(v for k, v in c.items() if f(*k)))
    ret = s(an, lambda m, pa, re: m == "retenue_dividende" and pa in tour)
    loc = s(an, lambda m, pa, re: m == "dividende" and pa in tour)
    etr = s(an, lambda m, pa, re: m == "dividende_exterieur_tourisme" and pa in tour)
    rev = lambda c: s(c, lambda m, pa, re: re == "Menage" and pa != "Menage") - s(c, lambda m, pa, re: pa == "Menage" and re == "Gouvernement")
    brut = ret + loc + etr
    return {"graine": graine, "regle": regle, "lits_par_habitant": round(lits, 4), "resultats_nets_positifs": round(float(sum(nets)), 2),
            "dividendes_bruts": round(brut, 2), "retenue": round(ret, 2), "dividendes_menages": round(loc, 2),
            "part_etrangere": round((etr / 0.95) / max(1e-9, brut), 4),     # le brut etranger : son net verse / 0,95
            "etr_verse": round(etr, 2), "caisse_negative": negatif,
            "revenu_mois_personne": round(rev(an) / float(np.mean(pop)) / (JOURS / 30.0), 2),
            "revenu_mois_personne_ete": round(rev(ete) / float(np.mean(pop[:90])) / 3.0, 2),
            "conservation": bool(p.socle.conservation.tenue()[0]), "secondes": round(time.time() - t0)}


def main():
    graines = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else list(GRAINES)
    t0 = time.time(); ok = {}
    with get_context("spawn").Pool(2, maxtasksperchild=1) as pool:
        rs = pool.map(_jouer, [(g, r) for g in graines for r in (True, False)])
    for r in rs: print("  ", r, flush=True)
    for g in graines:
        R = next(r for r in rs if r["graine"] == g and r["regle"]); T = next(r for r in rs if r["graine"] == g and not r["regle"])
        ok[f"D1 graine {g} : dividendes {R['dividendes_bruts']} au plus la moitie des resultats nets {R['resultats_nets_positifs']}"] = (
            R["dividendes_bruts"] <= 0.5 * R["resultats_nets_positifs"] * (1 + 1e-6) + 0.01 and R["dividendes_bruts"] > 0)
        ok[f"D1 graine {g} : part etrangere {R['part_etrangere']} ( 8 % a un demi-point ) ; retenue {R['retenue']} = 5 %"] = (
            abs(R["part_etrangere"] - 0.08) <= 0.005 and abs(R["retenue"] - 0.05 * R["dividendes_bruts"]) <= 1e-6 * R["dividendes_bruts"] + 0.01)
        ok[f"D1 graine {g} : controle positif, le temoin distribue plus de la moitie ( {T['dividendes_bruts']} pour {T['resultats_nets_positifs']} )"] = (
            T["dividendes_bruts"] > 0.5 * T["resultats_nets_positifs"])
        ok[f"D2 graine {g} : {R['lits_par_habitant']} lit par habitant ( 0,17 a 0,19 )"] = 0.17 <= R["lits_par_habitant"] <= 0.19
        ok[f"D3 graine {g} : dividendes aux menages {R['dividendes_menages']} sous le temoin {T['dividendes_menages']} ; caisses positives ; conservation"] = (
            R["dividendes_menages"] < T["dividendes_menages"] and not R["caisse_negative"] and R["conservation"] and T["conservation"])
        print(f"   information graine {g} : revenu net par personne et par mois, regle moins temoin : annee "
              f"{R['revenu_mois_personne'] - T['revenu_mois_personne']:+.2f}, ete {R['revenu_mois_personne_ete'] - T['revenu_mois_personne_ete']:+.2f} "
              f"( drachmes ; x {EUR} en euros )", flush=True)
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DU DIVIDENDE DU TOURISME : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
