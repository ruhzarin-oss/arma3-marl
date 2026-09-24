"""PORTES DE LA TRAVERSEE ( archipel, phase E1 : les visiteurs ; plans/plan-archipel.md G4 personnes et G5 ).

Archipel OUVERT, six pays, JOURS jours. Chaque soir, le recensement de l archipel :
- G4 un corps par personne : chaque numero d archipel a EXACTEMENT un corps - resident chez lui, etranger en visite
  ailleurs, ou en mer - et chaque ABSENT a son corps ailleurs ; aucun corps perdu, aucun en double ;
- G5 la traversee dure le temps de la mer ( ou de l avion, pour Livonia ), au pas pres ; les visiteurs RENTRENT ;
  une frontiere fermee REFOULE ( Tanoa ferme au jour 3 : aucun etranger n y entre ensuite, des refoulements ont lieu ) ;
- la conservation du socle tient dans chaque pays ; parallele = sequentiel.
Controles positifs : un corps duplique a la main est vu ; inverser deux courriers d un meme pas change le monde.

   python -m monde.porte_traversee --jours 6 --echelle 2"""
import argparse, sys, time
from collections import Counter
from . import config as C
from .archipel import Archipel

ILES = C.ILES_ARCHIPEL


def delai_attendu(a, b):
    if a in C.PAR_AIR_SEULEMENT or b in C.PAR_AIR_SEULEMENT: m = C.AIR_MINUTES
    else: m = 60.0 * C.MER_PORT_A_PORT_KM / 25.0
    return max(1, int(round(m / C.MINUTES_PAR_PAS)))


def recenser(arc):
    corps = {n: arc.commande(n, "corps") for n in ILES}
    mer = arc.en_mer()
    return corps, mer


def un_corps_par_personne(corps, mer):
    """Chaque numero : exactement un corps ( resident, etranger ou en mer ) ; chaque absent a son corps ailleurs."""
    c = Counter()
    for n in ILES:
        c.update(corps[n]["residents"]); c.update(corps[n]["etrangers"])
    c.update(x[0] for x in mer if x[1] in ("arrivee", "retour", "refoule"))
    absents = set().union(*(set(corps[n]["absents"]) for n in ILES))
    ailleurs = set().union(*(set(corps[n]["etrangers"]) for n in ILES)) | {x[0] for x in mer}
    doublons = [k for k, v in c.items() if v != 1]
    return not doublons and absents == ailleurs, len(doublons), len(absents)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jours", type=int, default=6)
    p.add_argument("--echelle", type=float, default=2.0)
    x = p.parse_args()
    ok, t0 = {}, time.time()
    arc = Archipel(echelle=x.echelle, ouvert=True)
    g4, retards, voyages_max, ferme_pas = True, [], 0, None
    for j in range(x.jours):
        if j == 2:
            ferme_pas = arc.pas; arc.commande("Tanoa", "frontiere", False, [])
        arc.jours(1)
        corps, mer = recenser(arc)
        bon, n_dbl, n_abs = un_corps_par_personne(corps, mer)
        g4 &= bon; voyages_max = max(voyages_max, n_abs)
        for n in ILES:
            for nia, orig, dep, arr in arc.commande(n, "etrangers"):
                if arr - dep != delai_attendu(orig, n): retards.append((nia, orig, n, arr - dep))
        print(f"jour {j + 1} : {n_abs} personnes hors de chez elles | un corps chacune : {bon} | {time.time() - t0:.0f} s", flush=True)
    journal = arc.journal
    genres = Counter(m[3][0] for m in journal)
    tanoa_apres = [e for e in arc.commande("Tanoa", "etrangers") if e[3] > ferme_pas]
    refoules_tanoa = sum(1 for (pas, o, d, m) in journal if m[0] == "refoule" and o == "Tanoa")
    tenues = {n: arc.commande(n, "tenue")[0] for n in ILES}
    fin = arc.empreintes()
    # controle positif 1 : un corps duplique ( un resident de Malden declare aussi etranger a Sara )
    corps, mer = recenser(arc)
    faux = {k: dict(v) for k, v in corps.items()}
    faux["Sara"] = dict(faux["Sara"], etrangers=faux["Sara"]["etrangers"] + [faux["Malden"]["residents"][0]])
    cp1 = not un_corps_par_personne(faux, mer)[0]
    arc.fermer()
    # parallele = sequentiel ; controle positif 2 : inverser les courriers d un pas ou il en arrive plusieurs
    seq = Archipel(echelle=x.echelle, ouvert=True, parallele=False)
    for j in range(x.jours):
        if j == 2: seq.commande("Tanoa", "frontiere", False, [])
        seq.jours(1)
    fin_seq = seq.empreintes()
    # le pas ou le plus de courriers arrivent dans une MEME ile : les inverser change l ordre de leur traitement
    arrivees = Counter((pas + delai_attendu(o, d), d) for (pas, o, d, m) in journal)
    (pas_inv, _), n_inv = arrivees.most_common(1)[0] if arrivees else ((None, None), 0)
    seq.fermer()
    inv = Archipel(echelle=x.echelle, ouvert=True)
    inv.inverser_au_pas = {pas_inv} if n_inv >= 2 else set()
    for j in range(x.jours):
        if j == 2: inv.commande("Tanoa", "frontiere", False, [])
        inv.jours(1)
    fin_inv = inv.empreintes(); inv.fermer()
    ok["G4 un corps par personne, chaque soir"] = g4 and voyages_max > 0
    ok["G4 controle positif : un corps duplique est vu"] = cp1
    ok["G5 traversee au pas pres ( mer et air )"] = not retards and genres.get("arrivee", 0) > 0
    ok["G5 les visiteurs rentrent"] = genres.get("retour", 0) > 0
    ok["G5 frontiere fermee : aucune entree, des refoulements"] = not tanoa_apres and refoules_tanoa > 0
    ok["conservation dans chaque pays"] = all(tenues.values())
    ok["parallele = sequentiel ( archipel ouvert )"] = fin == fin_seq
    ok["G3 controle positif : inverser deux courriers change le monde"] = fin_inv != fin
    for k, v in ok.items(): print(f"{'PASSE ' if v else 'ECHOUE'} {k}")
    print(f"   ( inversion au pas {pas_inv} : {n_inv} courriers dans la meme ile )")
    print(f"   ( courrier : {dict(genres)} ; retards {retards[:3]} ; refoules par Tanoa {refoules_tanoa} ; "
          f"conservation {tenues} )")
    passe = all(ok.values())
    print(f"PORTES DE LA TRAVERSEE : {'FRANCHIES' if passe else 'ECHOUEES'}")
    return 0 if passe else 1


if __name__ == "__main__":
    sys.exit(main())
