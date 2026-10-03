"""Porte A1 du tir indirect des mortiers de 81 mm ( HMT-198 ). Criteres ecrits avant la mesure ( Plane, 03/10 ) : Malden
( 2071 ), echelle 20 ; une compagnie qui a des mortiers defend sa base contre 20 hommes adverses generiques.

T1  controle positif ( amende avant la mesure ) : adversaire repere avancant de 1 500 m ; sur 5 graines de mission,
    ( a ) des adversaires hors de combat par eclats d obus, ( b ) la defense perd strictement moins d hommes avec les
    mortiers que sans. ( amende 03/10, A2 : blindes coupes ; les comptes T2 sur les memes graines, tout ouvert )
T2  les comptes : obus demandes = obus sortis ( tir_combat ), <= dotation ( 60 x tubes ) et <= stock ; anomalies vides.
T3  controles negatifs : adversaire inconnu ( immobile a 3 km, jamais repere ), repere a 6 km, unite sans mortier :
    0 obus.
T4  ( a part ) les tests du domaine 27 passent.
python -m guerre.porte_tir_indirect [ graine ]"""
import json
import math
import pickle
import sys
import time

import numpy as np

from monde import archipel as AR, tests as T
from monde.pays import d25_armee as A, d26_armee_soutien as S, d27_armee_tactique as TT

SORTIE = "/mnt/data/hmt/arsenal/porte_tir_indirect.json"


def sortis(w, bien, motif="tir_combat"):
    d = w.pays.domaines[A.DOMAINE]
    return sum(v for (b, m), v in d.sorties.items() if b == bien and m == motif)


def compagnie_a_mortiers(p):
    a = A._dom(p); U = a.unites; K = a.coll
    for k in range(K.n):
        if int(K["oid"][k]) < 0: continue
        x = int(K["unite"][k])
        while x >= 0 and int(U["niveau"][x]) != A.COMPAGNIE: x = int(U["parent"][x])
        if x >= 0 and len(TT._aptes(p, x)): return x
    return None


def section_sans_mortier(p, u):
    a = A._dom(p); U = a.unites; K = a.coll
    avec = {int(K["unite"][k]) for k in range(K.n) if int(K["oid"][k]) >= 0}
    for x in range(U.n):
        if int(U["parent"][x]) == u and int(U["niveau"][x]) == A.SECTION and x not in avec and len(TT._aptes(p, x)): return x
    return None


def mission(w, u, dist, reperer=True, fixe=False, seed=1, taille=20):
    """Une defense de la base de u ( combat, voix ) contre `taille` hommes poses a `dist` m."""
    p = w.pays
    x0, y0, ile = S.position(p, S.CAMP_NATIONAL, u)
    cnom = TT._camp(p, "adverse")
    dep = (x0 + dist, y0)
    ent = S.poser_entite(p, cnom, dep[0], dep[1], ile, "accroupi" if fixe else "debout", taille, 0.0)
    cond = TT.Conduite("fixe", regard="objectif", feu="libre") if fixe else TT.Conduite("bond", "objectif", regard="objectif", feu="libre")
    if reperer: TT._reperer(p, u, ent, dep[0], dep[1], ile)
    m = TT.nouvelle_mission(p, "defense", u, (x0, y0), (x0, y0), adverses=[(ent, taille, cond, [] if fixe else [(x0, y0)], None)],
                            mode="combat", voix=True, couvert_poste="leger", seed=(seed,), ile=ile,
                            axe=S.azimut(x0, y0, dep[0], dep[1]))
    TT.executer(p, m)
    return m


def main(graine=2071):
    t0 = time.time(); R = {}
    print(f"PORTE A1 DU TIR INDIRECT : Malden {graine}", flush=True)
    w0 = AR.creer_ile("Malden", graine, 20); T.jours(w0, 1)
    oct_ = pickle.dumps(w0, protocol=4)
    u = compagnie_a_mortiers(w0.pays)
    if u is None: raise SystemExit("aucune compagnie avec des mortiers")
    # T1 et T2
    tot = {True: 0, False: 0}; pertes = {True: 0, False: 0}; obus = 0; comptes = []; anom = []
    orig = TT._impact; eclats = [0]
    def espion(p_, m_, v, zone, arme):
        if arme == A.IDX_ARME["mortier_81"] and int(m_.h["side"][v]) == 1:
            a_, arrete = TT.lesion(zone, "mortier_81", int(m_.h["prot"][v]), int(m_.h["casque"][v]))
            if not arrete and int(m_.h["actif"][v]) == 1: eclats[0] += 1
        return orig(p_, m_, v, zone, arme)
    TT._impact = espion
    TT.BLINDES = False                     # ( amende 03/10, A2 ) T1 isole les mortiers des blindes de la defense
    for sg in range(5):
        for ouvert in (True, False):
            TT.TIR_INDIRECT = ouvert
            w = pickle.loads(oct_); p = w.pays
            s0 = sortis(w, "obus_81"); st0 = float(A.armurerie(p, w.carte.par_n[int(A._dom(p).unites["base"][u])].id).stock[A._dom(p).bids["obus_81"]])
            m = mission(w, u, 1500.0, seed=7100 + sg)
            tot[ouvert] += int(m.neutr_adv); pertes[ouvert] += len(set(m.morts)) + len(set(m.blesses) - set(m.morts))
            if ouvert:
                M = m.mortiers or {}; t_ = float(M.get("tires", 0.0)); obus += t_
    TT.TIR_INDIRECT = True; TT._impact = orig; TT.BLINDES = True
    for sg in range(5):                    # ( amende 03/10, A2 ) les comptes T2 avec tout ouvert, memes graines
        w = pickle.loads(oct_); p = w.pays
        s0 = sortis(w, "obus_81"); st0 = float(A.armurerie(p, w.carte.par_n[int(A._dom(p).unites["base"][u])].id).stock[A._dom(p).bids["obus_81"]])
        m = mission(w, u, 1500.0, seed=7100 + sg)
        M = m.mortiers or {}; t_ = float(M.get("tires", 0.0))
        comptes.append({"tires": t_, "sortis": sortis(w, "obus_81") - s0, "dotation": M.get("dotation"), "stock": st0,
                        "tubes": len(M.get("tubes", []))})
        anom += [str(a) for a in TT.anomalies(p)]
    T1 = eclats[0] > 0 and pertes[True] < pertes[False] and obus > 0
    T2 = all(abs(c["tires"] - c["sortis"]) <= 1e-9 and c["tires"] <= (c["dotation"] or 0) + 1e-9 and c["tires"] <= c["stock"] + 1e-9
             for c in comptes) and not anom
    R["T1"] = {"ok": T1, "hors_de_combat_par_eclats": eclats[0], "pertes_defense_avec": pertes[True], "pertes_defense_sans": pertes[False],
               "neutralises_avec": tot[True], "neutralises_sans": tot[False], "obus": obus,
               "obus_par_neutralise": round(obus / max(1, tot[True] - tot[False]), 1)}
    R["T2"] = {"ok": T2, "comptes": comptes, "anomalies": anom[:5]}
    print(f"  T1 controle positif : {'OUI' if T1 else 'NON'} {R['T1']}", flush=True)
    print(f"  T2 comptes : {'OUI' if T2 else 'NON'} {R['T2']}", flush=True)
    # T3
    w = pickle.loads(oct_); m_inc = mission(w, u, 3000.0, reperer=False, fixe=True, seed=7200)
    w = pickle.loads(oct_); m_loin = mission(w, u, 6000.0, reperer=True, fixe=True, seed=7201)
    w = pickle.loads(oct_); us = section_sans_mortier(w.pays, u)
    m_sec = mission(w, us, 1500.0, seed=7202) if us is not None else None
    t_inc = (m_inc.mortiers or {}).get("tires", 0.0); t_loin = (m_loin.mortiers or {}).get("tires", 0.0)
    T3 = t_inc == 0 and t_loin == 0 and m_sec is not None and m_sec.mortiers is None
    R["T3"] = {"ok": T3, "inconnu": t_inc, "hors_portee": t_loin, "section_sans_mortier": None if m_sec is None else m_sec.mortiers,
               "tubes_compagnie": len((m_inc.mortiers or {}).get("tubes", []))}
    print(f"  T3 controles negatifs : {'OUI' if T3 else 'NON'} {R['T3']}", flush=True)
    oks = [R[k]["ok"] for k in ("T1", "T2", "T3")]
    verdict = "FRANCHIE ( T4 a part : tests du domaine 27 )" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graine=graine, compagnie=u, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE A1 DU TIR INDIRECT : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_TIR_INDIRECT", flush=True)
    return 0 if all(oks) else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2071))
