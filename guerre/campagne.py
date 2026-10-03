"""LA CAMPAGNE ( HMT-198, chantier S2 ) : une guerre de quelques jours entre deux iles, l une commandee par un stratege
( Qwen, la doctrine fixe, le mauvais stratege ), l autre qui se defend ( ses garnisons, le domaine 27 ).

Les BUTS DE GUERRE sont donnes a tous les strateges, et ce sont des effets REELS lus dans le monde adverse ( jamais un
score ) :
  blocus     l ile adverse ne recoit plus rien par la mer ( d07.sous_blocus : son port detruit ) ;
  centrale   sa centrale est detruite a moitie au moins ( ses groupes en panne, guerre/frappes ) ;
  depot      son depot de carburant est detruit a moitie au moins ( le gazole de son armee brule ).
Le bilan compte les buts atteints, et ce qu ils ont coute : les hommes de l attaquant hors de combat ( aptes perdus ),
ses devises, et ce que l adversaire a perdu. Les strateges se comparent sans poids : atteindre au moins autant de buts
sans perdre plus d hommes ( dominer, au sens de Pareto ).

La doctrine fixe ( le temoin ) : acheter trois chalands, puis chaque jour ou ils sont libres, masser tout ce qu ils
portent sur le premier but non atteint, dans l ordre port, centrale, depot. CHOIX : l adversaire se defend sans contre-
attaquer ( pas encore de stratege chez lui ).

   python -m guerre.campagne Stratis 2081 Malden 2082 qwen 4"""
import json
import pickle
import sys
import time

from monde import archipel as AR, tests as T
from monde.pays import d07_exterieur as X
from . import etat_major as EM, fin as FI, frappes as FR, projection as PR

BUTS = (("blocus", "port01"), ("centrale", "centrale01"), ("depot", "depot01"))
SEUIL_BUT = 0.5
TOUR_PAS = 144                               # un tour d etat-major par jour du moteur


def buts_atteints(wB):
    """{ but : atteint } lus dans le monde adverse."""
    d = FR._etat(wB); p = wB.pays
    return {"blocus": bool(X.sous_blocus(p)), "centrale": d.get("centrale01", 0.0) >= SEUIL_BUT,
            "depot": d.get("depot01", 0.0) >= SEUIL_BUT}


def doctrine_buts(sit):
    """Le temoin de la campagne ( voir la fiche )."""
    fl = sit["flotte"]["lcu"]
    if fl["engins"] < 3:
        return [{"nom": "doctrine", "actions": [{"type": "acheter", "modele": "lcu", "nombre": 3 - fl["engins"]}], "raison": "doctrine"}]
    if fl["libres"] < 1: return [{"nom": "doctrine", "actions": [{"type": "attendre"}], "raison": "transport occupe"}]
    vus = {c["id"]: c["detruit_constate"] for c in sit["objectifs_adverses"]}
    for _but, oid in BUTS:
        if vus.get(oid, 0.0) < SEUIL_BUT:
            return [{"nom": "doctrine", "actions": [{"type": "operation", "objectif": oid, "modele": "lcu", "hommes": 400 * fl["libres"]}],
                     "raison": f"le but {oid}"}]
    return [{"nom": "doctrine", "actions": [{"type": "attendre"}], "raison": "buts atteints"}]


CONSIGNE_BUTS = ("\nLES BUTS DE GUERRE fixes par le gouvernement : 1. le BLOCUS de {B} ( detruire son port, port01 ) ; "
                 "2. sa CENTRALE en panne ( centrale01 ) ; 3. son DEPOT de carburant brule ( depot01 ). Un but est atteint "
                 "quand l objectif est detruit a moitie au moins. Atteins le plus de buts en perdant le moins d hommes.\n")


def campagne(nom_A, g_A, nom_B, g_B, chef, jours=4, echelle=20, index=None, journal=None):
    """La campagne. Rend { buts, bilan, tours }."""
    t0 = time.time()
    wA = AR.creer_ile(nom_A, g_A, echelle); T.jours(wA, 1)
    wB = AR.creer_ile(nom_B, g_B, echelle); T.jours(wB, 1)
    av = {"aptes_A": FI.aptes(wA), "aptes_B": FI.aptes(wB), "devises_A": EM._devises(wA)}
    tours = []
    ancienne = EM.FICHE_DE_COMMANDEMENT
    EM.FICHE_DE_COMMANDEMENT = ancienne + CONSIGNE_BUTS.replace("{B}", "{B}")
    try:
        for _j in range(jours):
            if chef == "doctrine": tr = _tour_temoin(wA, nom_A, nom_B, doctrine_buts, echelle)
            elif chef == "mauvais": tr = _tour_temoin(wA, nom_A, nom_B, EM.mauvais_stratege, echelle)
            else: tr = EM.tour(wA, nom_A, nom_B, chef="qwen", index=index, echelle=echelle)
            tours.append({k: tr.get(k) for k in ("jour", "chef", "modes", "jeux", "choix", "execution", "duree_s")}
                         | {"ordre": (tr.get("decision") or {}).get("reponse", "")[:600]})
            EM.avancer(wA, wB, int(wA.pas) + TOUR_PAS)
        EM.avancer(wA, wB, int(wA.pas) + TOUR_PAS)          # le dernier retour
    finally:
        EM.FICHE_DE_COMMANDEMENT = ancienne
    buts = buts_atteints(wB)
    bilan = {"buts_atteints": sum(buts.values()), "pertes_A": av["aptes_A"] - FI.aptes(wA), "pertes_B": av["aptes_B"] - FI.aptes(wB),
             "devises_depensees_A": round(av["devises_A"] - EM._devises(wA)), "degats_B": dict(FR._etat(wB)),
             "peut_combattre_B": FI.peut_combattre(wB)[0], "duree_s": round(time.time() - t0)}
    out = {"chef": chef, "A": [nom_A, g_A], "B": [nom_B, g_B], "buts": buts, "bilan": bilan, "tours": tours}
    if journal is not None: journal.append(out)
    return out


def _tour_temoin(wA, nom_A, nom_B, regle, echelle):
    """Un tour d un stratege sans Qwen : sa regle propose, on execute ( sans jeu de guerre : il ne sert pas a sa decision )."""
    sit = EM.situation(wA, nom_A, nom_B)
    modes = regle(sit)
    ex = EM.executer(wA, nom_A, nom_B, modes[0].get("actions", []))
    return {"jour": sit["jour"], "chef": modes[0].get("nom"), "modes": modes, "jeux": [], "choix": 0,
            "execution": [(a, {k: r.get(k) for k in ("ok", "raison", "achetes", "arrivee")}) for a, r in ex], "duree_s": 0}


def domine(a, b):
    """a domine-t-il b ( ou l egale ) : au moins autant de buts, pas plus de pertes ?"""
    return a["bilan"]["buts_atteints"] >= b["bilan"]["buts_atteints"] and a["bilan"]["pertes_A"] <= b["bilan"]["pertes_A"]


if __name__ == "__main__":
    a = sys.argv[1:]
    idx = None
    if a[4] == "qwen":
        from .connaissance import index as IX
        idx = IX.ouvrir()
    r = campagne(a[0], int(a[1]), a[2], int(a[3]), a[4], int(a[5]) if len(a) > 5 else 4, index=idx)
    print(json.dumps({k: r[k] for k in ("chef", "buts", "bilan")}, ensure_ascii=False, default=str))
