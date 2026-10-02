"""UNE FIN DE GUERRE REELLE ( Arma a fond, etape 5, HMT-196 ) : la capacite et la volonte d une ile, lues dans le moteur.
Jamais un score : ce qu une ile peut encore faire, et ce que sa population et son armee endurent.

5a, la mesure ( lecture seule : rien n est ecrit dans le monde, porte F1 ) :
  capacite        les militaires aptes ( lignes actives du domaine 25, vivants, pas pris en charge par l hopital du
                  domaine 17 ) ; les jours de combat de l ile par classe, comme le domaine 26 les compte pour une
                  garnison mais sur toute l ile : stocks ( armureries + depots de brigade et national ; pour le gazole,
                  les garnisons + le stock de l armee ) / somme des besoins d un jour de combat des garnisons
                  ( d26.besoins_combat ) ; les vehicules en service ; les objectifs reels touches ( guerre/frappes ) ;
                  le blocus ( d07.sous_blocus ). Ce qui roule dans un convoi n est pas encore utilisable ( CHOIX ).
  peut_combattre  CHOIX : une ile ne peut plus combattre quand elle n a plus un militaire apte, ou plus une munition
                  d arme individuelle ( 5,56, 7,62, 9 mm ) dans ses armureries et ses depots ; la raison est dite. Le
                  gazole ou les vivres a zero ne l arretent pas : ils pesent sur ce qu elle peut faire et sur sa volonte.
  volonte         des indicateurs, sans seuil ni decision : moral moyen civil ( domaine 23 ) et militaire ( domaine 25 ),
                  part des menages affames, morts au combat pour 1 000 habitants, part des recettes de l Etat depensee
                  en armes. Demander une treve ou capituler est une DECISION du stratege ( etape 4 ), qui la lit."""
import math

import numpy as np

from monde.pays import d01_population as POP, d25_armee as A, d26_armee_soutien as S
from monde.socle import objets as O

ARMES_INDIVIDUELLES = ("mun_556", "mun_762", "mun_9mm")
EPS = 1e-9


def _p(w):
    p = getattr(w, "pays", None)
    if p is None or not (p.a("armee") and p.a("armee_soutien")): raise RuntimeError("la fin de guerre lit les domaines 25 et 26")
    return p


def stocks_ile(w):
    """{ bien : quantite } de l ile : munitions et rations des armureries et des depots, gazole des garnisons, des depots
    de brigade et du stock de l armee."""
    p = _p(w); a = A._dom(p); d = S._dom(p)
    out = {b: 0.0 for b in A.NOMS_MUNITIONS}
    for arm in a.armureries:
        for b in A.NOMS_MUNITIONS: out[b] += float(arm.stock[a.bids[b]])
    for dep in d.depots:
        for b in A.NOMS_MUNITIONS: out[b] += float(dep.stock[d.ids[b]])
    carb = math.fsum(float(g.get("carburant", 0.0)) for g in w.garnisons.values())
    carb += math.fsum(float(dep.stock[d.ids["carburant"]]) for dep in d.depots if dep.niveau != "national")
    carb += float(w.publics["armee"].get("carburant", 0.0))
    out["carburant"] = carb
    out["jours_homme_vivres"] = math.fsum(S._jours_vivres(d, arm.stock) for arm in a.armureries) \
        + math.fsum(S._jours_vivres(d, dep.stock) for dep in d.depots)
    return out


def besoins_ile(w):
    """( gazole, { munition : coups }, rations ) d un jour de combat de toute l ile ( somme des garnisons )."""
    p = _p(w); d = S._dom(p)
    carb, mun, rat = 0.0, {}, 0.0
    for b in sorted(d.besoins):
        c, m, r = d.besoins[b]
        carb += c; rat += r
        for k, q in m.items(): mun[k] = mun.get(k, 0.0) + q
    return carb, mun, rat


def aptes(w):
    """Les militaires aptes : lignes actives du domaine 25, vivants, pas pris en charge par l hopital ( domaine 17 )."""
    p = _p(w); a = A._dom(p); E = a.eff; tb = w.table
    rows = A._lignes_actives(a)
    hid = E["hid"][rows]
    viv = tb.vivant[hid] == 1
    soignes = set(p.domaine("hopitaux").actifs) if p.a("hopitaux") else set()
    return int(sum(1 for h, v in zip(hid.tolist(), viv.tolist()) if v and h not in soignes))


def capacite(w):
    p = _p(w); a = A._dom(p); V = a.veh
    st = stocks_ile(w); carb, mun, rat = besoins_ile(w)
    jours_mun = {k: (st.get(k, 0.0) / q if q > EPS else None) for k, q in sorted(mun.items())}
    vals = [v for v in jours_mun.values() if v is not None]
    service = int(((V["oid"][:V.n] >= 0) & (V["etat"][:V.n] == O.SERVICE)).sum()) if V.n else 0
    blocus = False
    if p.a("exterieur"):
        from monde.pays import d07_exterieur as X
        blocus = bool(X.sous_blocus(p))
    return {"aptes": aptes(w), "jours_munitions": jours_mun, "jours_munitions_min": min(vals) if vals else None,
            "jours_carburant": st["carburant"] / carb if carb > EPS else None,
            "jours_vivres": st["jours_homme_vivres"] / rat if rat > EPS else None,
            "munitions_individuelles": math.fsum(st[b] for b in ARMES_INDIVIDUELLES),
            "vehicules_en_service": service, "objectifs_touches": dict(sorted(getattr(w, "objectifs_degats", {}).items())),
            "blocus": blocus}


def peut_combattre(w):
    """( vrai ou faux, raison ) : CHOIX de la fiche - plus un militaire apte, ou plus une munition d arme individuelle."""
    if aptes(w) == 0: return False, "soldats"
    st = stocks_ile(w)
    if math.fsum(st[b] for b in ARMES_INDIVIDUELLES) <= EPS: return False, "munitions"
    return True, None


def volonte(w):
    p = _p(w); tb = w.table; n = tb.n; col = p.colonnes["habitant"]
    viv = tb.vivant[:n] == 1
    out = {}
    if p.a("culture"):
        m = col["cul_moral"][:n][viv & (col["cul_base"][:n] >= 0)].astype(np.float64)
        out["moral_civil"] = float(m.mean()) if len(m) else None
    a = A._dom(p); rows = A._lignes_actives(a)
    out["moral_militaire"] = float(a.eff["moral"][rows].mean()) if len(rows) else None
    from guerre import moteur as GM
    out["menages_affames"] = float(GM.faim(w))
    combat = int(((col["cause_deces"][:n] == POP.CAUSES.index("combat")) & (col["deces_j"][:n] >= 0)).sum())
    out["morts_au_combat"] = combat
    out["morts_au_combat_pour_1000"] = 1000.0 * combat / max(1, int(viv.sum()) + combat)
    paye = float(getattr(w, "guerre_paye", 0.0))
    serie = list(p.domaine("etat").tresor.serie) if p.a("etat") else []
    recettes = math.fsum(s[1] for s in serie)
    out["part_recettes_en_armes"] = paye / recettes if recettes > EPS else 0.0
    return out


def etat(w):
    ok, raison = peut_combattre(w)
    return {"jour": int(w.jour), "peut_combattre": ok, "raison": raison, "capacite": capacite(w), "volonte": volonte(w)}
