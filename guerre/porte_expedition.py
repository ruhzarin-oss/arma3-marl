"""Porte 4b-1 de l expedition, l assaut ( HMT-197 ). Criteres ecrits avant la mesure ( Plane, 03/10 ) : A = Stratis
( 2041 ), B = Malden ( 2042 ), echelle 20, 30 soldats de Stratis contre une base de Malden.

X1  les vrais hommes : chaque ligne rouge porte exactement les valeurs de son soldat de A.
X2  controle positif sans defenseur : tous arrivent, dommages 1, la frappe appliquee, aucune perte.
X3  le combat : pertes de B par le domaine 27 ( mort par deceder cause combat, ou evacuation ) ; chaque homme de A hors de
    combat mort ou blesse dans A ; coups tires par A = somme( portes - restants ) en tir_combat ; anomalies vides.
X4  controle positif des statistiques ( amende ) : 5 graines de mission, couvert leger : pertes de B avec les vrais
    tireurs > avec tir 0. ( amende 03/10, M5 : tir indirect coupe, le resultat ouvert en information ; anomalies de X3
    lues apres deux jours du moteur ; amende 03/10, A2 : blindes coupes aussi ; X3 compte les coups des armes
    individuelles, obus et roquettes ayant leurs comptes )
X5  identite : sans expedition, A et B identiques au bit sur 2 jours.
python -m guerre.porte_expedition [ graine_A graine_B ]"""
import json
import pickle
import sys
import time

import numpy as np

from monde import archipel as AR, tests as T
from monde.pays import d01_population as POP, d25_armee as A, d26_armee_soutien as S, d27_armee_tactique as TT
from . import expedition as EX, frappes as FR, logistique as LO, moteur as GM, objectifs as OB
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_expedition.json"


def sorties(w, motif):
    d = w.pays.domaines[A.DOMAINE]
    return sum(v for (b, m), v in d.sorties.items() if m == motif)


def sorties_individuelles(w, motif):
    """( amende 03/10, A2 ) les munitions des armes individuelles : obus et roquettes ont leurs comptes ( M3, B4 )."""
    d = w.pays.domaines[A.DOMAINE]
    return sum(v for (b, m), v in d.sorties.items() if m == motif and b not in ("obus_81", "roquette_84"))


def morts_combat(w):
    col = w.pays.colonnes["habitant"]; n = w.table.n
    return set(np.nonzero((col["cause_deces"][:n] == POP.CAUSES.index("combat")) & (col["deces_j"][:n] >= 0))[0].tolist())


def anomalies(w, avec27=True):
    p = w.pays
    out = list(A.anomalies(p)) + list(S.anomalies(p))
    if avec27 and hasattr(TT, "anomalies"): out += list(TT.anomalies(p))
    return out


def main(gA=2041, gB=2042):
    t0 = time.time(); R = {}
    print(f"PORTE 4b-1 DE L EXPEDITION : Stratis {gA} contre Malden {gB}", flush=True)
    wA0 = AR.creer_ile("Stratis", gA, 20); T.jours(wA0, 1)
    nums = GM.mobiliser(wA0, 30); LO.emporter(wA0, nums)
    octA = pickle.dumps(wA0, protocol=4)
    wB0 = AR.creer_ile("Malden", gB, 20); T.jours(wB0, 1)
    octB = pickle.dumps(wB0, protocol=4)
    oid = next(o["id"] for o in OB.objectifs_carte("malden") if o["type"] == "base" and o.get("composants"))
    # X1
    wA = pickle.loads(octA); pA = wA.pays; cp = EX.corps(wA, nums)
    f = GM._front(wA); ids = [f[int(n)]["i"] for n in cp["numero"]]
    comp = A.competences(pA, ids)
    rang = A._rangs(pA, ids); E = A._dom(pA).eff
    lourd = np.isin(E["arme_m"][rang], [A.IDX_ARME[x] for x in TT.ARMES_LOURDES])
    ok_comp = np.allclose(cp["tir"], comp["tir"]) and np.allclose(cp["moral"], comp["moral"]) and np.allclose(cp["disc"], comp["discipline"])
    ok_port = np.allclose(cp["portee"][~lourd], A.portee_utile(pA, ids)[~lourd])
    ok_coups = np.allclose(cp["coups"], [LO.coups(wA, int(n)) for n in cp["numero"]]) and cp["coups"].sum() > 0
    ok_prot = np.array_equal(cp["prot"], E["protection"][rang]) and np.array_equal(cp["casque"], E["casque"][rang])
    wB = pickle.loads(octB)
    r3 = EX.assaut(wB, "Stratis", cp, oid, seed=(4242,))
    ok_rouges = r3["rouges_avant"] is not None and all(np.array_equal(r3["rouges_avant"][k], cp[k]) for k in EX.CHAMPS)
    X1 = ok_comp and ok_port and ok_coups and ok_prot and ok_rouges
    R["X1"] = {"ok": X1, "hommes": len(cp["numero"]), "competences": ok_comp, "portee": ok_port, "coups": ok_coups,
               "protections": ok_prot, "lignes_rouges": ok_rouges, "coups_portes": float(cp["coups"].sum())}
    print(f"  X1 vrais hommes : {'OUI' if X1 else 'NON'} {R['X1']}", flush=True)
    # X2 : sans defenseur
    w2 = pickle.loads(octB); r2 = EX.assaut(w2, "Stratis", cp, oid, u=None)
    X2 = r2["arrives"] == len(cp["numero"]) and r2["dommages"] == 1.0 and not r2["sorts"] \
        and abs(FR._etat(w2).get(oid, 0.0) - 1.0) <= 1e-12
    R["X2"] = {"ok": X2, "arrives": r2["arrives"], "dommages": r2["dommages"], "degats": FR._etat(w2).get(oid), "frappe": str(r2["frappe"])[:300]}
    print(f"  X2 sans defenseur : {'OUI' if X2 else 'NON'} {R['X2']}", flush=True)
    # X3 : le combat ( le monde wB de X1 a deja combattu : r3 )
    m = r3["mission"]; pB = wB.pays
    mortsB = set(m.morts); blessesB = set(m.blesses) - mortsB
    deceB = morts_combat(wB)
    evB = {int(x[1]) for x in S._dom(pB).evacuations}
    okB = mortsB <= deceB and all((b in evB) or (b in deceB) for b in blessesB)
    avant_tir = sorties_individuelles(wA, "tir_combat"); avant_perte = sorties(wA, "perte_au_combat")
    porte = {int(n): LO.coups(wA, int(n)) for n in cp["numero"]}
    att_tir = sum(max(0.0, porte[n] - r3["restants"][n]) for n in porte)
    rap = EX.rapatrier(wA, r3)
    deceA = morts_combat(wA)
    morts_att = {n for n, e, *_ in r3["sorts"] if e == "mort"}; bless_att = {n for n, e, *_ in r3["sorts"] if e == "blesse"}
    okA_morts = all(f[n]["i"] in deceA for n in morts_att)
    evA = {int(x[1]) for x in S._dom(pA).evacuations}
    okA_bless = all((f[n]["i"] in evA) or (f[n]["i"] in deceA) for n in bless_att)
    ok_tir = abs((sorties_individuelles(wA, "tir_combat") - avant_tir) - att_tir) <= 1e-6
    T.jours(wA, 2); T.jours(wB, 2)          # ( amende 03/10, M5 ) le domaine 25 retire ses morts a sa routine du jour
    anB, anA = anomalies(wB), anomalies(wA, avec27=False)
    X3 = okB and okA_morts and okA_bless and ok_tir and not anB and not anA and len(r3["sorts"]) + len(mortsB) + len(blessesB) > 0
    R["X3"] = {"ok": X3, "defenseur": r3["defenseur"], "arrives": r3["arrives"], "dommages": r3["dommages"],
               "B": {"morts": len(mortsB), "blesses": len(blessesB), "ok": okB},
               "A": {"morts": len(morts_att), "blesses": len(bless_att), "morts_ok": okA_morts, "blesses_ok": okA_bless},
               "coups_tires_A": [att_tir, sorties_individuelles(wA, "tir_combat") - avant_tir], "perte_au_combat_A": sorties(wA, "perte_au_combat") - avant_perte,
               "anomalies_B": [str(a) for a in anB[:5]], "anomalies_A": [str(a) for a in anA[:5]], "issue": m.issue if m else None}
    print(f"  X3 combat : {'OUI' if X3 else 'NON'} {R['X3']}", flush=True)
    # X4 ( amende avant la mesure ) : 5 graines de mission, couvert leger, vrais tireurs contre tir 0
    tot = {False: 0, True: 0}
    TT.TIR_INDIRECT = False                 # ( amende 03/10, M5 ) le tir de A, isole des mortiers du defenseur ( A1 )
    TT.BLINDES = False                      # ( amende 03/10, A2 ) et de ses blindes
    for sg in range(5):
        for zero in (False, True):
            c = {k: v.copy() for k, v in cp.items()}
            if zero: c["tir"][:] = 0.0
            w4 = pickle.loads(octB); r4 = EX.assaut(w4, "Stratis", c, oid, seed=(6000 + sg,), couvert="leger")
            m4 = r4["mission"]; tot[zero] += len(set(m4.morts)) + len(set(m4.blesses) - set(m4.morts))
    TT.TIR_INDIRECT = True; TT.BLINDES = True
    info = {False: 0, True: 0}               # en information : les memes missions, tir indirect ouvert
    for sg in range(5):
        for zero in (False, True):
            c = {k: v.copy() for k, v in cp.items()}
            if zero: c["tir"][:] = 0.0
            w4 = pickle.loads(octB); r4 = EX.assaut(w4, "Stratis", c, oid, seed=(6000 + sg,), couvert="leger")
            m4 = r4["mission"]; info[zero] += len(set(m4.morts)) + len(set(m4.blesses) - set(m4.morts))
    X4 = tot[False] > tot[True]
    R["X4"] = {"ok": X4, "pertes_B_vrais": tot[False], "pertes_B_tir0": tot[True],
               "info_tir_indirect_ouvert": {"vrais": info[False], "tir0": info[True]}}
    print(f"  X4 statistiques : {'OUI' if X4 else 'NON'} {R['X4']}", flush=True)
    # X5
    ident = True
    for oc in (octA, octB):
        w1, w2b = pickle.loads(oc), pickle.loads(oc)
        for _ in range(2):
            T.jours(w1, 1); T.jours(w2b, 1)
            if PE.empreinte_etendue(w1) != PE.empreinte_etendue(w2b): ident = False
    R["X5"] = {"ok": ident}
    print(f"  X5 identite : {'OUI' if ident else 'NON'}", flush=True)
    oks = [R[k]["ok"] for k in ("X1", "X2", "X3", "X4", "X5")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graines=[gA, gB], objectif=oid, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 4b-1 DE L EXPEDITION : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_EXPEDITION", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(main(int(a[0]), int(a[1])) if len(a) >= 2 else main())
