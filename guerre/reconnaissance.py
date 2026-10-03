"""LA RECONNAISSANCE ( HMT-198, chantier A3 d Arma a fond ) : une equipe de l ile A va voir un objectif de l ile B avant
de l attaquer. Le combat, s il y en a, est juge par le domaine 27 de B, comme l assaut ( guerre/expedition ).

Dans B, la garde de l objectif ( expedition.defenseur ) tient sa position ( la tactique « defense » : elle ne tire que
sur ce que son camp connait ). L equipe est un element adverse pose au domaine 26 de B ( camp expedition_<A> ), de vrais
soldats de A ( expedition.corps ) : elle part a DEPART_M de l objectif ( du cote de son port ), s approche jusqu au
point d observation ( DIST_OP ), observe DUREE_OBS_MIN minutes feu tenu, puis repart a son point de depart ; prise sous
le feu, elle decroche aussitot ( CHOIX : une reconnaissance ne se bat pas ). Elle ne voit que par le domaine 26 de B :
la portee d une entite ( 550 m de jour, 300 m de nuit ), la posture de la cible ( couche : 0,105 ; accroupi : 0,42 ;
vehicule ou element qui tire : 3 ), son regard. La garde ne la voit que de meme ( ses guetteurs, leurs jumelles ).

Le RAPPORT ( jamais la verite ) : pour chaque element de la garde que le camp de l equipe connait a la fin, sa taille
connue et l age de l observation ; les blindes intacts de ces elements ( un blinde se voit, CHOIX ) ; des obus tombes
sur l equipe ( des mortiers ). Il revient dans A avec ses pertes ( expedition.rapatrier ) et nourrit le renseignement de
l etat-major ( `renseignement` : par objectif, avec son pas ).
   python -m guerre.reconnaissance Stratis 2121 Malden 2122 port01"""
import math
import sys

import numpy as np

from monde import archipel as AR, tests as T
from monde.pays import d16_medecine as MED, d26_armee_soutien as S, d27_armee_tactique as TT
from . import expedition as EX, logistique as LO, moteur as GM

DEPART_M = 1500.0                 # CHOIX : l approche part hors de la vue de jour d un guetteur couche
DIST_OP = 600.0                   # CHOIX : le point d observation, a la portee d une entite de jour ( 550 m ) pres
DUREE_OBS_MIN = 20.0              # la phase d observation de la tactique reconnaissance du domaine 27


def _renseignement(w): return w.__dict__.setdefault("renseignement", {})


def reconnaitre(wB, nom_A, cp, oid, seed=None, dist_op=DIST_OP, approche="infiltration", depart_m=DEPART_M):
    """La reconnaissance de l objectif `oid` de B par les hommes `cp` ( corps ). approche : infiltration ( accroupie,
    lente ) ou simultane ( debout ). Rend { mission, rapport, detectee, sorts, restants, roquettes, mortiers, obus_tires,
    arrives, dommages, defenseur }."""
    pB = wB.pays; c = wB.carte; ile = c.par_n[0].ile; ii = c.iles.index(ile)
    o = EX.objectif(ile, oid); ox, oy = float(o["pos"][0]), float(o["pos"][1])
    ax, ay = EX.point_d_approche(wB, o, max(depart_m, dist_op))             # du cote ou debarque le transport
    L = max(1.0, math.hypot(ax - ox, ay - oy)); ux, uy = (ax - ox) / L, (ay - oy) / L
    depart = (ox + depart_m * ux, oy + depart_m * uy); op = (ox + dist_op * ux, oy + dist_op * uy)
    u, couvert = EX.defenseur(wB, o)
    n = len(cp["numero"])
    sorts = []; restants = {int(k): float(q) for k, q in zip(cp["numero"].tolist(), cp["coups"].tolist())}
    roquettes = [(int(cp["numero"][k]), cp["at_lid"][k], float(q), float(q)) for k, q in enumerate(cp.get("at", [])) if q > 0]
    vide = {"mission": None, "rapport": {"objectif": oid, "pas": int(wB.pas), "elements": [], "hommes_vus": 0,
                                         "blindes_vus": 0, "mortiers_vus": False, "defendu_vu": False},
            "detectee": False, "sorts": sorts, "restants": restants, "roquettes": roquettes, "mortiers": None,
            "obus_tires": 0.0, "arrives": 0, "dommages": 0.0, "defenseur": u}
    if u is None or n == 0: return vide
    camp = EX._camp(pB, nom_A)
    ent = S.poser_entite(pB, camp, depart[0], depart[1], ii, "accroupi" if approche == "infiltration" else "debout", n, 0.0)
    cond = TT.Conduite(approche, "objectif", regard="objectif", feu="tenu")
    m = TT.nouvelle_mission(pB, "defense", u, (ox, oy), (ox, oy), adverses=[(ent, n, cond, [op], None)], mode="combat",
                            voix=True, couvert_poste=couvert or "leger", seed=seed, axe=S.azimut(ox, oy, depart[0], depart[1]),
                            ile=ii)
    rouges = np.nonzero(m.h["side"] == 1)[0]
    for k in EX.CHAMPS: m.h[k][rouges] = cp[k]
    if "at" in cp and "at" in m.h: m.h["at"][rouges] = cp["at"]
    e_r = next(e for e in m.elts if e.side == 1)
    if all(e.cond is None for e in m.elts if e.side == 0): TT._ouvrir_phase(pB, m)
    phase = "approche"; t_obs = None; pris_a_partie = False
    while not m.fini:
        TT._avancer(pB, m, TT.DT_S)
        if m.fini: break
        if e_r.feu_recu > 0 and phase != "retour":
            pris_a_partie = True; phase = "retour"
            e_r.cond = TT.Conduite(approche, "depart", regard="arriere", feu="riposte"); e_r.chemin = [depart]; e_r.arrive = False
        elif phase == "approche" and e_r.arrive:
            phase = "observation"; t_obs = m.t_s
            e_r.cond = TT.Conduite("fixe", posture="couche", regard="objectif", feu="tenu")
        elif phase == "observation" and m.t_s - t_obs >= 60.0 * DUREE_OBS_MIN - 1e-6:
            phase = "retour"
            e_r.cond = TT.Conduite(approche, "depart", regard="arriere", feu="riposte"); e_r.chemin = [depart]; e_r.arrive = False
        elif phase == "retour" and e_r.arrive:
            TT._clore(pB, m, "fin"); break
        if not len(TT._actifs(m, m.elts.index(e_r))):
            TT._clore(pB, m, "fin"); break
        if m.t_s >= TT.DUREE_MAX_S: TT._clore(pB, m, "temps"); break
    h = m.h
    lesion = {int(v): (zone, arme, int(ais)) for v, zone, arme, ais, arrete in m.lesions_adverses if not arrete}
    for k, v in enumerate(rouges.tolist()):
        num = int(cp["numero"][k]); restants[num] = float(h["coups"][v])
        if v in lesion:
            zone, arme, ais = lesion[v]; iss = MED.iss_depuis_ais({zone: ais})
            sorts.append((num, "mort" if iss >= 75 else "blesse", zone, arme, ais, iss))
    if "at" in h:
        roquettes = [(int(cp["numero"][k]), cp["at_lid"][k], float(cp["at"][k]), float(h["at"][v]))
                     for k, v in enumerate(rouges.tolist()) if cp["at"][k] > 0]
    detectee = S.connaissance(pB, S.CAMP_NATIONAL, ent) is not None
    if S._dom(pB).ent["vivant"][ent]: S.retirer_entite(pB, ent)
    rapport = rapport_de(pB, m, camp, oid)
    if detectee: EX._subies(wB).append({"pas": int(wB.pas), "type": "reconnaissance", "attaquant": nom_A, "objectif": oid,
                                        "hommes": n})                # ( S3 ) une equipe vue : l ile le sait
    rapport["pris_a_partie"] = pris_a_partie
    wB.noter("reconnaissance", attaquant=nom_A, objectif=oid, hommes=n, vus=rapport["hommes_vus"], pertes=len(sorts))
    return {"mission": m, "rapport": rapport, "detectee": detectee, "sorts": sorts, "restants": restants,
            "roquettes": roquettes, "mortiers": None, "obus_tires": 0.0, "arrives": 0, "dommages": 0.0, "defenseur": u}


def rapport_de(pB, m, camp, oid):
    """Ce que le camp de l equipe sait de la garde ( le domaine 26 de B ) : jamais la verite."""
    els = []; blindes = 0
    for i, e in enumerate(m.elts):
        if e.side != 0 or e.ent < 0: continue
        c = S.connaissance(pB, camp, e.ent)
        if c is None: continue
        nb = sum(1 for vh in (getattr(m, "vehicules", None) or ()) if m.elts[int(m.h["elt"][vh["equipage"][0]])] is e)
        els.append({"role": e.role, "taille": float(c["taille"]), "age_h": round(float(c["age_h"]), 2), "blindes": nb,
                    "sigma_m": round(float(c["sigma_m"]), 1)})
        blindes += nb
    M = getattr(m, "mortiers", None) or {}
    return {"objectif": oid, "pas": int(pB.w.pas), "elements": els, "hommes_vus": int(round(sum(x["taille"] for x in els))),
            "blindes_vus": int(blindes), "mortiers_vus": float(M.get("tires", 0.0)) > 0, "defendu_vu": bool(els)}


if __name__ == "__main__":
    a = sys.argv[1:]
    wA = AR.creer_ile(a[0], int(a[1]), 20); T.jours(wA, 1)
    wB = AR.creer_ile(a[2], int(a[3]), 20); T.jours(wB, 1)
    nums = GM.mobiliser(wA, 8); LO.emporter(wA, nums)
    r = reconnaitre(wB, a[0], EX.corps(wA, nums), a[4], seed=(1,))
    print(r["rapport"], "detectee", r["detectee"], "pertes", len(r["sorts"]))
