"""Porte A2 des blindes au combat ( HMT-198 ). Criteres ecrits avant la mesure ( Plane, 03/10 04 h 30 ) : Malden ( 2111 )
pour B1 a B3 et B5, Stratis ( 2113 ) contre Malden ( 2114 ) pour B4, echelle 20.

B1  l equipage et l emport ( une defense de compagnie, combat ) : chaque blinde engage en service, a la base de l unite,
    dans son arbre ; son equipage a l effectif du domaine 25, de l arbre de l unite du vehicule, chacun dans un seul
    vehicule, conducteurs, equipages ou fusiliers ; chaque M113 emmene le conducteur apte de son groupe ; la reserve de
    12,7 de la base monte exactement des coups de bord emportes ; les equipiers sans arme de bord ne portent rien ; le
    meme ordre en exercice n engage aucun blinde.
B2  la caisse ( impacts poses sur l equipage, au membre : aucune protection individuelle ne s en mele ) : M113 intact,
    balle de fusil et eclat arretes ( l homme reste actif, sans lesion ) ; balle de 12,7 passe ; sur un blindage de char
    ( 6 ), la 12,7 est arretee ; vehicule detruit, la balle de fusil passe.
B3  controle positif du feu de bord ( mortiers coupes pour isoler le mecanisme ; 40 adversaires reperes a 1 500 m ;
    5 graines ) : pertes de la defense strictement moins nombreuses avec les blindes que sans ; des adversaires touches
    par la M2HB ; 12,7 sortis en tir_combat = coups de bord tires ; reserve revenue ; anomalies du domaine 27 vides, du
    domaine 25 vides apres deux jours.
B4  l antichar ( 60 hommes de membres_a_projeter contre une base ; 5 graines de mission ; tout ouvert ) : avec roquettes,
    plus de 0 tiree et plus de 0 blinde detruit ; roquettes a zero, 0 et 0 ; chaque blinde detruit hors du Parc et de la
    table des vehicules du domaine 25, ses munitions de bord perdues = la perte_au_combat de B ( le 12,7 n est porte que
    par les blindes : egalite ; le 7,62 des Leopard s y ajoute aux armes des hommes d une unite qui rompt : au moins ) ;
    anomalies du domaine 27 de B vides ; dans A ( reserve posee comme lancer_operation ), apres rapatrier : tir_combat
    de roquettes = roquettes tirees, perte_au_combat = roquettes restantes des morts, reserve revenue.
B5  identite : blindes coupes, les 5 missions de defense ( mortiers ouverts, 20 adversaires ) identiques au bit a
    l arbre d avant A2 ( 6acd850, atelier-a1b ) ; un exercice de defense ( blindes ouverts ) identique ; un monde sans
    combat, 2 jours, empreinte etendue identique.
B6  ( a part ) les tests du domaine 27 passent.
python -m guerre.porte_blindes"""
import json
import os
import pickle
import subprocess
import sys
import time

from monde import archipel as AR, tests as T
from monde.pays import d25_armee as A, d27_armee_tactique as TT
from . import empreinte_missions as EM, expedition as EX, logistique as LO, moteur as GM, objectifs as OB
from . import porte_tir_indirect as PTI

SORTIE = "/mnt/data/hmt/arsenal/porte_blindes.json"
ARBRE_AVANT = "/mnt/data/hmt/atelier-a1b"
PY = "/mnt/data/hmt/evogp/env/bin/python"
C127 = A.NOMS_MUNITIONS.index("mun_127")
C84 = A.NOMS_MUNITIONS.index("roquette_84")


def sortis(w, bien, motif="tir_combat"):
    d = w.pays.domaines[A.DOMAINE]
    return sum(v for (b, m), v in d.sorties.items() if b == bien and m == motif)


def pertes(m):
    return len(set(m.morts)) + len(set(m.blesses) - set(m.morts))


def ligne_vehicule(p, oid):
    V = A._dom(p).veh
    return next((k for k in range(V.n) if int(V["oid"][k]) == oid), None)


def b1(oc, u):
    w = pickle.loads(oc); p = w.pays; a = A._dom(p); U = a.unites; V = a.veh; E = a.eff
    b = int(U["base"][u]); lid = w.carte.par_n[b].id
    r0 = TT._dom(p).reserve.get((lid, C127), 0.0)
    m = EM.mission(w, u, 1500.0, seed=7500)
    vehs = m.vehicules; h = m.h
    ok_v = bool(vehs); ok_e = True; ok_c = True; vus = set(); emport = 0.0; vides = True
    for vh in vehs:
        k = ligne_vehicule(p, vh["oid"]); x = int(V["unite"][k])
        ok_v &= (int(V["etat"][k]) == A.O.SERVICE and int(V["base"][k]) == b and TT._sous_unite(U, x, u)
                 and vh["modele"] in TT.ARMES_DE_VEHICULE)
        hids = [int(h["hid"][i]) for i in vh["equipage"]]; rg = A._rangs(p, hids)
        ok_e &= (len(hids) == A.VEHICULE[vh["modele"]].equipage and not (set(hids) & vus)
                 and all(TT._sous_unite(U, int(E["unite"][r]), x) for r in rg)
                 and all(int(E["spec"][r]) in TT.PREF_EQUIPAGE for r in rg))
        vus |= set(hids)
        if vh["modele"] == "m113a1":
            cond = [int(i) for i in TT._aptes(p, x) if int(E["spec"][A._rangs(p, [int(i)])[0]]) == A.CONDUCTEUR]
            if cond and not (set(cond) & set(hids)): ok_c = False
        for i in vh["equipage"]:
            if i in vh["tireurs"]:
                if int(h["cal"][i]) == C127: emport += float(h["coups"][i])
            elif h["coups"][i] != 0 or h["cal"][i] != -1: vides = False
    r1 = TT._dom(p).reserve.get((lid, C127), 0.0)
    w2 = pickle.loads(oc); m2 = EM.mission(w2, u, 1500.0, mode="exercice", seed=7500)
    ok = ok_v and ok_e and ok_c and abs((r1 - r0) - emport) <= 1e-9 and emport > 0 and vides and m2.vehicules == []
    return {"ok": ok, "blindes": len(vehs), "modeles": sorted({vh["modele"] for vh in vehs}), "equipages": len(vus),
            "vehicules_conformes": ok_v, "equipages_conformes": ok_e, "conducteurs": ok_c, "reserve_12_7": [r0, r1],
            "emport_12_7": emport, "equipiers_sans_arme_vides": vides, "exercice_sans_blinde": m2.vehicules == []}


def b2(oc, u):
    def essai(arme, blindage=None, intact=True):
        w = pickle.loads(oc); p = w.pays; m = EM.mission(w, u, 1500.0, seed=7510)
        vh = next(v for v in m.vehicules if v["modele"] == "m113a1")
        if blindage is not None: vh["blindage"] = blindage
        vh["intact"] = intact
        i = vh["equipage"][0]; n0 = len(m.pendants); a0 = vh["arretes"]
        TT._impact(p, m, int(i), "membre", arme)
        return {"arrete": bool(m.h["actif"][i] == 1 and len(m.pendants) == n0 and vh["arretes"] == a0 + 1),
                "actif": int(m.h["actif"][i]), "lesion": len(m.pendants) > n0}
    fusil = essai(A.IDX_ARME["g3a3"]); eclat = essai(A.IDX_ARME["mortier_81"]); lourde = essai(TT.IDX_BORD["m2hb"])
    char = essai(TT.IDX_BORD["m2hb"], blindage=6); detruit = essai(A.IDX_ARME["g3a3"], intact=False)
    ok = (fusil["arrete"] and eclat["arrete"] and not lourde["arrete"] and lourde["lesion"] and char["arrete"]
          and not detruit["arrete"] and detruit["lesion"])
    return {"ok": ok, "fusil": fusil, "eclat": eclat, "12_7": lourde, "12_7_sur_char": char, "fusil_vehicule_detruit": detruit}


def b3(oc, u):
    tot = {True: 0, False: 0}; touches = 0; comptes = []
    TT.TIR_INDIRECT = False
    try:
        for bl in (True, False):
            TT.BLINDES = bl
            for sg in range(5):
                w = pickle.loads(oc); p = w.pays
                lid = w.carte.par_n[int(A._dom(p).unites["base"][u])].id
                s0 = sortis(w, "mun_127"); res0 = TT._dom(p).reserve.get((lid, C127), 0.0)
                m = EM.mission(w, u, 1500.0, seed=7700 + sg, taille=40); TT.executer(p, m)
                tot[bl] += pertes(m)
                if not bl: continue
                touches += sum(1 for x in m.lesions_adverses if x[2] == "m2hb" and not x[4])
                tires = sum(float(m.h["tires"][i]) for vh in m.vehicules for i in vh["tireurs"]
                            if TT.ARME_BORD[TT.ARMES_DE_VEHICULE[vh["modele"]][vh["tireurs"].index(i)][0]][1] == "mun_127")
                an27 = [str(x) for x in TT.anomalies(p)]
                c = {"tires": tires, "sortis": sortis(w, "mun_127") - s0, "reserve": [res0, TT._dom(p).reserve.get((lid, C127), 0.0)],
                     "anomalies_27": an27[:3]}
                T.jours(w, 2); c["anomalies_25_apres_2_jours"] = [str(x) for x in A.anomalies(p)][:3]
                comptes.append(c)
    finally:
        TT.BLINDES = True; TT.TIR_INDIRECT = True
    ok_c = all(abs(c["tires"] - c["sortis"]) <= 1e-9 and abs(c["reserve"][0] - c["reserve"][1]) <= 1e-9
               and not c["anomalies_27"] and not c["anomalies_25_apres_2_jours"] for c in comptes)
    return {"ok": tot[True] < tot[False] and touches > 0 and ok_c, "pertes_defense_avec": tot[True],
            "pertes_defense_sans": tot[False], "adversaires_touches_m2hb": touches, "comptes": comptes}


def b4(gA, gB):
    wA0 = AR.creer_ile("Stratis", gA, 20); T.jours(wA0, 1)
    wB0 = AR.creer_ile("Malden", gB, 20); T.jours(wB0, 1); octB = pickle.dumps(wB0, protocol=4)
    oid = next(o["id"] for o in OB.objectifs_carte("malden") if o["type"] == "base" and o.get("composants"))
    nums = GM.mobiliser(wA0, 60, ids=EX.membres_a_projeter(wA0, 60)); LO.emporter(wA0, nums)
    cp = EX.corps(wA0, nums); octA = pickle.dumps(wA0, protocol=4)
    roq = {True: 0, False: 0}; det = {True: 0, False: 0}; ok_b = True; detail = []; ok_a = None
    for avec in (True, False):
        for sg in range(5):
            c = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in cp.items()}
            if not avec: c["at"][:] = 0.0
            wb = pickle.loads(octB); pB = wb.pays; parc = pB.socle.parc
            p0 = {bien: sortis(wb, bien, "perte_au_combat") for bien in ("mun_127", "mun_762")}
            r = EX.assaut(wb, "Stratis", c, oid, seed=(9500 + sg,)); m = r["mission"]
            d_ = [vh for vh in m.vehicules if not vh["intact"]]
            roq[avec] += int(m.roquettes[1]); det[avec] += len(d_)
            if not avec: continue
            V = A._dom(pB).veh; vivants = set(int(x) for x in V["oid"][:V.n])
            hors = all(vh["oid"] not in parc.objets and vh["oid"] not in vivants for vh in d_)
            perdu = {"mun_127": 0.0, "mun_762": 0.0}
            for vh in d_:
                cal = TT.ARME_BORD[TT.ARMES_DE_VEHICULE[vh["modele"]][0][0]][1]; perdu[cal] += vh["perdus"]
            dp = {bien: sortis(wb, bien, "perte_au_combat") - p0[bien] for bien in p0}
            ok_p = abs(dp["mun_127"] - perdu["mun_127"]) <= 1e-9 and dp["mun_762"] >= perdu["mun_762"] - 1e-9
            an = [str(x) for x in TT.anomalies(pB)]
            ok_b &= hors and ok_p and not an
            detail.append({"roquettes": int(m.roquettes[1]), "detruits": len(d_), "modeles": [vh["modele"] for vh in d_],
                           "hors_parc": hors, "perdus": perdu, "perte_au_combat_B": dp, "anomalies_27_B": an[:3]})
            if sg == 0:                                     # le cote de A
                wa = pickle.loads(octA); pA = wa.pays; res = TT._dom(pA).reserve
                avant = {lid: res.get((lid, C84), 0.0) for lid in EX.roquettes_par_base(cp)}
                for lid, q in EX.roquettes_par_base(cp).items(): res[(lid, C84)] = res.get((lid, C84), 0.0) + q
                s0, l0 = sortis(wa, "roquette_84"), sortis(wa, "roquette_84", "perte_au_combat")
                EX.rapatrier(wa, r)
                morts = {num for num, e, *_ in r["sorts"] if e == "mort"}
                tirees = sum(q0 - q1 for _n, _l, q0, q1 in r["roquettes"])
                restes_morts = sum(q1 for n, _l, _q0, q1 in r["roquettes"] if n in morts)
                ok_a = {"tirees": tirees, "tir_combat": sortis(wa, "roquette_84") - s0, "restes_des_morts": restes_morts,
                        "perte_au_combat": sortis(wa, "roquette_84", "perte_au_combat") - l0,
                        "reserve": {lid: [avant[lid], res.get((lid, C84), 0.0)] for lid in avant}}
                ok_a["ok"] = (abs(ok_a["tir_combat"] - tirees) <= 1e-9 and abs(ok_a["perte_au_combat"] - restes_morts) <= 1e-9
                              and all(abs(x - y) <= 1e-9 for x, y in ok_a["reserve"].values()))
    ok = roq[True] > 0 and det[True] > 0 and roq[False] == 0 and det[False] == 0 and ok_b and ok_a is not None and ok_a["ok"]
    return {"ok": ok, "antichar": int((cp["at"] > 0).sum()), "roquettes_emportees": float(cp["at"].sum()),
            "roquettes_tirees": roq, "blindes_detruits": det, "B": ok_b, "A": ok_a, "missions": detail}


def b5(g):
    def lancer(arbre):
        env = dict(os.environ, PYTHONPATH=arbre, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        r = subprocess.run([PY, os.path.join(os.path.dirname(os.path.abspath(__file__)), "empreinte_missions.py"), str(g)],
                           env=env, capture_output=True, text=True, timeout=3000)
        lignes = [l for l in r.stdout.strip().splitlines() if l.startswith("{")]
        return json.loads(lignes[-1]) if lignes else {"erreur": r.stderr[-800:]}
    ici = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    neuf, avant = lancer(ici), lancer(ARBRE_AVANT)
    diff = sorted(k for k in set(neuf) | set(avant) if neuf.get(k) != avant.get(k))
    return {"ok": not diff and "erreur" not in neuf and len(neuf) == 7, "differences": diff, "arbre_avant": ARBRE_AVANT,
            "neuf": neuf, "avant": avant}


def main(g=2111, gA=2113, gB=2114):
    t0 = time.time(); R = {}
    print(f"PORTE A2 DES BLINDES : Malden {g} ; Stratis {gA} contre Malden {gB}", flush=True)
    w0 = AR.creer_ile("Malden", g, 20); T.jours(w0, 1); oc = pickle.dumps(w0, protocol=4)
    u = PTI.compagnie_a_mortiers(w0.pays)
    for nom, f in (("B1", lambda: b1(oc, u)), ("B2", lambda: b2(oc, u)), ("B3", lambda: b3(oc, u)),
                   ("B4", lambda: b4(gA, gB)), ("B5", lambda: b5(g))):
        R[nom] = f()
        print(f"  {nom} : {'OUI' if R[nom]['ok'] else 'NON'} {json.dumps(R[nom], default=str)[:1200]}", flush=True)
    oks = [R[k]["ok"] for k in ("B1", "B2", "B3", "B4", "B5")]
    verdict = "FRANCHIE ( B6 a part : tests du domaine 27 )" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graines=[g, gA, gB], compagnie=u, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE A2 DES BLINDES : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_BLINDES", flush=True)
    return 0 if all(oks) else 1


if __name__ == "__main__":
    sys.exit(main())
