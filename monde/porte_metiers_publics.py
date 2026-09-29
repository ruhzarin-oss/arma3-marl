"""PORTE DES METIERS PUBLICS ( 29/09, HMT-140, emploi public ; criteres ecrits AVANT la mesure, chef de projet ).

Diagnostic de Classes : le monde grec n a que 7 « ministres » pour toute l administration ( 5,6 % de l emploi dans le
reel, -3,4 points ici ) ; les pompiers ( domaine 18 ), les juges et les gardiens ( domaine 21 ) gardent un metier prive.
Le moteur ajoute quatre metiers publics a la fin de config.ROLES : administration, pompier, juge, gardien, a l effectif
0. Classes les remplira dans le monde grec, aux ratios reels ; la Bibliotheque les comptera publics dans d18 et d21.
M1 le monde E1 ( Altis, echelle 20 ) n a aucun habitant de ces metiers. Son identite au bit est prouvee par les portes
   des domaines, des colonnes et d identite, a passer dans la meme livraison.
M2 Altis en mode grec ( echelle 20, tous les domaines ), K habitants par metier pris aux marchands a la generation ( ce
   que fera Classes, pose ici a la main ) : chacun est compte public ( colonne public ), travaille dans une capitale a
   l horaire declare, et les domaines 4 et 6 le tiennent pour public ( PUBLIC_DU_MOTEUR, PUB_ROLE ) a son salaire
   declare ( SAL_ROLE ) ; en 4 jours ( vendredi a lundi ), chaque metier a des heures de travail creditees ; la
   conservation tient.
Controle positif : le meme monde avec le juge declare prive : les juges ne sont pas comptes publics, la porte echoue.

   python -m monde.porte_metiers_publics"""
import sys, time
import numpy as np
from . import config as C, monde as W, population as PO
from .pays import pays as P, essais as E, d04_travail as TV, d06_etat as ET

NOUVEAUX = ("administration", "pompier", "juge", "gardien")
K = 5
ECHELLE = 20.0


def _effectifs_avec(orig):
    def effectifs(*a, **k):                         # la signature d effectifs peut grandir ( fret, Classes 29/09 )
        eff = orig(*a, **k)
        for r in NOUVEAUX:
            k = min(K, eff["marchand"]); eff["marchand"] -= k; eff[r] += k
        return eff
    return effectifs


def m1():
    w = W.Monde(echelle=ECHELLE)
    t = w.table; n = t.n
    compte = {r: int(np.count_nonzero(t.role[:n] == PO.CODE_ROLE[r])) for r in NOUVEAUX}
    return all(v == 0 for v in compte.values()) and all(C.ROLES[r][0] == 0 for r in NOUVEAUX), compte


def m2(juge_prive=False):
    orig, role0 = PO.effectifs, C.ROLES["juge"]
    PO.effectifs = _effectifs_avec(orig)
    if juge_prive: C.ROLES["juge"] = (role0[0], role0[1], False)
    try:
        w, p = E.monde([nom for nom, mod, _ in P.DOMAINES], echelle=ECHELLE, demographie="grece")
        t = w.table; n = t.n; par_n = w.carte.par_n
        ids = {r: np.flatnonzero(t.role[:n] == PO.CODE_ROLE[r]) for r in NOUVEAUX}
        heures = {r: 0.0 for r in NOUVEAUX}
        for _ in range(4 * C.PAS_PAR_JOUR):
            w.pas_suivant()
            for r in NOUVEAUX:
                if ids[r].size: heures[r] = max(heures[r], float(t.heures[ids[r]].max()))
        tenue, msg = p.socle.conservation.tenue()
    finally:
        PO.effectifs, C.ROLES["juge"] = orig, role0
    res = {}
    for r in NOUVEAUX:
        i = ids[r]; c = PO.CODE_ROLE[r]
        res[r] = {"n": int(i.size), "publics": int(np.count_nonzero(t.public[i] == 1)),
                  "capitale": int(sum(1 for x in t.travail[i].tolist() if x >= 0 and par_n[x].type == "capitale")),
                  "horaire": int(np.count_nonzero(t.horaire[i] == PO.CODE_HORAIRE[PO.TRAVAIL[r][1]])),
                  "d04_public": bool(TV.PUBLIC_DU_MOTEUR[c + 1]), "d06_public": bool(ET.PUB_ROLE[c + 1]),
                  "salaire": float(ET.SAL_ROLE[c + 1]), "heures_max": round(heures[r], 2)}
    ok = tenue and all(v["n"] >= 1 and v["publics"] == v["n"] and v["capitale"] == v["n"] and v["horaire"] == v["n"]
                       and v["d04_public"] and v["d06_public"] and v["salaire"] == PO.SALAIRE_HORAIRE[r]
                       and v["heures_max"] > 0 for r, v in res.items())
    return ok, res, msg


def main():
    t0 = time.time()
    ok1, c1 = m1()
    print(f"M1 monde E1 : {c1} -> {'PASSE' if ok1 else 'ECHOUE'}", flush=True)
    ok2, r2, msg = m2()
    for r, v in r2.items(): print(f"M2 {r} : {v}", flush=True)
    print(f"M2 conservation : {msg} -> {'PASSE' if ok2 else 'ECHOUE'}", flush=True)
    okc, rc, _ = m2(juge_prive=True)
    print(f"controle positif ( juge declare prive ) : juges {rc['juge']} -> porte "
          f"{'passe ( FAUX )' if okc else 'echoue ( attendu )'}", flush=True)
    ok = ok1 and ok2 and not okc
    print(f"PORTE DES METIERS PUBLICS : {'FRANCHIE' if ok else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
