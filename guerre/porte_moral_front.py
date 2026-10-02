"""Porte 3c du moral ( HMT-194 ). Criteres ecrits avant la mesure ( Plane, 03/10 ) : Malden ( 2011 ), echelle 20, 20
soldats mobilises.

M1  plus de gel : interrupteur ouvert, sur 3 jours le moral d au moins un soldat au front bouge, anomalies() du 23 vide ;
    controle : interrupteur ferme, aucun ne bouge.
M2  un deuil chez lui : le conjoint d un soldat au front meurt de maladie ; le soir, sa part de deuil = celle de son
    jumeau + DEUIL_MENAGE, le tout x 0,5^( 1/90 ), a 1e-6 ; son moral est la somme de ses parts ; controle : interrupteur
    ferme, moral_hors_causes pour lui.
M3  un camarade tue : apres morts_au_combat de X, chaque homme de son unite a exactement DEUIL_PROCHE de plus ( borne ),
    moral recompose ; un soldat d une autre unite inchange ; anomalies() vide ; a 22 h 40, le moral domaine 25 de ses
    camarades plus bas que chez leurs jumeaux.
M4  identite : sans soldat au front, identique au bit sur 2 jours, interrupteur ouvert ou ferme.
python -m guerre.porte_moral_front [ graine ]"""
import json
import pickle
import sys
import time

import numpy as np

from monde import archipel as AR, tests as T
from monde.pays import d01_population as POP, d23_culture as CU, d25_armee as A
from . import moteur as GM
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_moral_front.json"


def moraux(w, ids):
    return w.pays.colonnes["habitant"]["cul_moral"][np.asarray(ids, np.int64)].astype(np.float64).copy()


def hors_causes(w):
    return {i for k, i in CU.anomalies(w.pays) if k == "moral_hors_causes"}


def main(graine=2011):
    t0 = time.time(); R = {}
    print(f"PORTE 3c DU MORAL : Malden {graine}", flush=True)
    w00 = AR.creer_ile("Malden", graine, 20); T.jours(w00, 1)
    oct0 = pickle.dumps(w00, protocol=4)
    nums = GM.mobiliser(w00, 20)
    oct_ = pickle.dumps(w00, protocol=4)
    f = GM._front(w00); ids = [f[n]["i"] for n in nums]
    # M1
    out1 = {}
    for ouvert in (True, False):
        CU.MORAL_AU_FRONT = ouvert
        w = pickle.loads(oct_); av = moraux(w, ids)
        T.jours(w, 3); ap = moraux(w, ids)
        out1[ouvert] = {"bougent": int((np.abs(ap - av) > 1e-7).sum()), "anomalies": len(CU.anomalies(w.pays)),
                        "ecart_max": float(np.abs(ap - av).max())}
    CU.MORAL_AU_FRONT = True
    M1 = out1[True]["bougent"] > 0 and out1[True]["anomalies"] == 0 and out1[False]["bougent"] == 0
    R["M1"] = {"ok": M1, "ouvert": out1[True], "ferme": out1[False]}
    print(f"  M1 plus de gel : {'OUI' if M1 else 'NON'} {R['M1']}", flush=True)
    # M2 : le conjoint d un soldat au front meurt
    w = pickle.loads(oct_); col = w.pays.colonnes["habitant"]; tb = w.table
    S = next((i for i in ids if int(col["conjoint"][i]) >= 0 and tb.vivant[int(col["conjoint"][i])]
              and int(tb.menage[i]) == int(tb.menage[int(col["conjoint"][i])])), None)
    if S is None:
        R["M2"] = {"ok": False, "raison": "aucun soldat au front avec un conjoint dans son menage"}
    else:
        c = int(col["conjoint"][S])
        res = {}
        for ouvert, avec in ((True, True), (True, False), (False, True)):
            CU.MORAL_AU_FRONT = ouvert
            w = pickle.loads(oct_)
            if avec: POP.deceder(w.pays, w.habitants[c], "maladie")
            T.jours(w, 1)
            cc = w.pays.colonnes["habitant"]
            res[(ouvert, avec)] = {"deuil": float(cc["cul_deuil"][S]), "hors_causes": S in hors_causes(w)}
        CU.MORAL_AU_FRONT = True
        fct = 0.5 ** (1.0 / CU.DEMI_VIE_DEUIL_J)
        d_avec, d_sans = res[(True, True)]["deuil"], res[(True, False)]["deuil"]
        attendu = max(CU.DEUIL_MIN, d_sans / fct + CU.DEUIL_MENAGE) * fct
        M2 = abs(d_avec - attendu) <= 1e-6 and not res[(True, True)]["hors_causes"] and res[(False, True)]["hors_causes"]
        R["M2"] = {"ok": M2, "soldat": S, "conjoint": c, "deuil_avec": d_avec, "deuil_sans": d_sans, "attendu": attendu,
                   "hors_causes_ouvert": res[(True, True)]["hors_causes"], "hors_causes_ferme": res[(False, True)]["hors_causes"]}
    print(f"  M2 deuil chez lui : {'OUI' if R['M2']['ok'] else 'NON'} {R['M2']}", flush=True)
    # M3 : un camarade tue dans Arma ( amende avant la mesure : le deuil frappe le soir )
    w = pickle.loads(oct_); p = w.pays; col = p.colonnes["habitant"]; a = A._dom(p); E = a.eff
    rows = A._lignes_actives(a); rang = p.col("habitant", "ar_rang")
    def camarades(i):
        u = int(E["unite"][int(rang[i])])
        return [int(E["hid"][x]) for x in rows[E["unite"][rows] == u].tolist() if int(E["hid"][x]) != i
                and w.table.vivant[int(E["hid"][x])] and col["cul_base"][int(E["hid"][x])] >= 0]
    nX = next(n for n in nums if int(rang[f[n]["i"]]) >= 0 and camarades(f[n]["i"]))
    X = f[nX]["i"]; cam = camarades(X); uX = int(E["unite"][int(rang[X])])
    fam = {int(col[k][X]) for k in ("conjoint", "mere", "pere")} | set(p.domaine("population").enfants_de.get(X, ()))
    autre = next(int(E["hid"][x]) for x in rows.tolist() if int(E["unite"][x]) != uX and int(E["hid"][x]) not in cam
                 and int(E["hid"][x]) != X and int(E["hid"][x]) not in fam and col["cul_base"][int(E["hid"][x])] >= 0
                 and int(w.table.menage[int(E["hid"][x])]) != int(w.table.menage[X]))
    GM.morts_au_combat(w, [nX])
    T.jours(w, 1)
    wt = pickle.loads(oct_); T.jours(wt, 1)
    ct = wt.pays.colonnes["habitant"]; ca = np.array(cam, np.int64)
    fct = 0.5 ** (1.0 / CU.DEMI_VIE_DEUIL_J)
    d_a = col["cul_deuil"][ca].astype(np.float64); d_t = ct["cul_deuil"][ca].astype(np.float64)
    att = np.maximum(CU.DEUIL_MIN, d_t / fct + CU.DEUIL_PROCHE) * fct
    pleure = bool(np.all(np.abs(d_a - att) <= 1e-6))
    inchange = abs(float(col["cul_deuil"][autre]) - float(ct["cul_deuil"][autre])) <= 1e-12
    an3 = CU.anomalies(p)
    T.jours(w, 1); T.jours(wt, 1)              # le 25 lit le moral du 23 a 22 h 40, avant le soir du 23 : le lendemain
    rg_c = [int(rang[i]) for i in cam if int(rang[i]) >= 0]
    m25 = A._dom(w.pays).eff["moral"][rg_c]; m25t = A._dom(wt.pays).eff["moral"][rg_c]
    plus_bas = bool(len(rg_c)) and bool(np.all((m25 < m25t - 1e-9) | (m25t <= 0.0)))
    M3 = pleure and inchange and not an3 and plus_bas
    R["M3"] = {"ok": M3, "soldat": X, "unite": uX, "camarades": len(cam), "deuil": d_a.tolist()[:6], "jumeau": d_t.tolist()[:6],
               "attendu": att.tolist()[:6], "autre": autre, "autre_inchange": inchange, "anomalies": an3[:5],
               "moral25": [float(m25.mean()) if len(rg_c) else None, float(m25t.mean()) if len(rg_c) else None], "plus_bas": plus_bas}
    print(f"  M3 camarade tue : {'OUI' if M3 else 'NON'} {R['M3']}", flush=True)
    # M4 : l identite sans soldat au front
    emp = {}
    for ouvert in (True, False):
        CU.MORAL_AU_FRONT = ouvert
        w = pickle.loads(oct0); e = []
        for _ in range(2):
            T.jours(w, 1); e.append((PE.empreinte_etendue(w), w.pays.colonnes["habitant"]["cul_moral"][:w.table.n].tobytes()))
        emp[ouvert] = e
    CU.MORAL_AU_FRONT = True
    M4 = emp[True] == emp[False]
    R["M4"] = {"ok": M4}
    print(f"  M4 identite : {'OUI' if M4 else 'NON'}", flush=True)
    oks = [R[k]["ok"] for k in ("M1", "M2", "M3", "M4")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graine=graine, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 3c DU MORAL : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_MORAL", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2011))
