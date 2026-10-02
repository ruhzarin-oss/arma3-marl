"""Porte 5a de la fin de guerre, la mesure ( HMT-196 ). Criteres ecrits avant la mesure ( Plane ) : Malden ( 2021 ),
echelle 20.

F1  lecture seule : capacite, volonte, peut_combattre appeles chaque jour, identique au bit au jumeau sur 3 jours.
F2  coherence : jours de munitions de l ile d un calibre = recalcul a part ( armureries + depots / somme des besoins des
    garnisons ) a 1e-9 ; pour une ile a une seule garnison de besoin, >= les jours de cette garnison ( d26.autonomie ).
F3  controle positif des munitions : toutes les munitions d arme individuelle tirees -> faux, « munitions » ; une base
    reapprovisionnee de 1 000 coups de 5,56 -> vrai.
F4  controle positif des soldats : tous les militaires du domaine 25 morts -> faux, « soldats ».
F5  une ile ordinaire : vrai, jours de munitions > 0, aptes > 0.
python -m guerre.porte_fin [ graine ]"""
import json
import pickle
import sys
import time

from monde import archipel as AR, tests as T
from monde.pays import d01_population as POP, d25_armee as A, d26_armee_soutien as S
from . import fin as FI
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_fin.json"


def main(graine=2021):
    t0 = time.time(); R = {}
    print(f"PORTE 5a DE LA FIN DE GUERRE : Malden {graine}", flush=True)
    w0 = AR.creer_ile("Malden", graine, 20); T.jours(w0, 1)
    oct_ = pickle.dumps(w0, protocol=4)
    # F1
    wa, wb = pickle.loads(oct_), pickle.loads(oct_); ident = True; etats = []
    for _ in range(3):
        etats.append(FI.etat(wa)); T.jours(wa, 1); T.jours(wb, 1)
        if PE.empreinte_etendue(wa) != PE.empreinte_etendue(wb): ident = False
    R["F1"] = {"ok": ident, "etat_jour1": etats[0]}
    print(f"  F1 lecture seule : {'OUI' if ident else 'NON'} {etats[0]}", flush=True)
    # F2
    w = pickle.loads(oct_); p = w.pays; a = A._dom(p); d = S._dom(p)
    cap = FI.capacite(w)
    bases = sorted(d.besoins)
    besoin = {}
    for b in bases:
        for k, q in S.besoins_combat(p, w.carte.par_n[b].id)[1].items(): besoin[k] = besoin.get(k, 0.0) + q
    ecarts = {}
    for k, q in sorted(besoin.items()):
        if q <= 0: continue
        stock = sum(float(x.stock[a.bids[k]]) for x in a.armureries) + sum(float(dep.stock[d.ids[k]]) for dep in d.depots)
        if abs(cap["jours_munitions"][k] - stock / q) > 1e-9: ecarts[k] = (cap["jours_munitions"][k], stock / q)
    avec_besoin = [b for b in bases if any(v > 0 for v in d.besoins[b][1].values())]
    une_seule = None
    if len(avec_besoin) == 1:
        lid = w.carte.par_n[avec_besoin[0]].id
        une_seule = cap["jours_munitions_min"] >= S.autonomie(p, lid)["munitions"] - 1e-9
    mediant = {}                                          # information : l ile >= la pire garnison, calibre par calibre
    for k, q in sorted(besoin.items()):
        if q <= 0: continue
        pires = [float(A.armurerie(p, w.carte.par_n[b].id).stock[a.bids[k]]) / d.besoins[b][1][k] for b in bases
                 if d.besoins[b][1].get(k, 0) > 0]
        mediant[k] = cap["jours_munitions"][k] >= min(pires) - 1e-9
    F2 = not ecarts and une_seule is not False and bool(besoin)
    R["F2"] = {"ok": F2, "ecarts": ecarts, "garnisons_avec_besoin": len(avec_besoin), "une_seule_garnison": une_seule,
               "ile_au_moins_la_pire_garnison": mediant, "jours_munitions": cap["jours_munitions"]}
    print(f"  F2 coherence : {'OUI' if F2 else 'NON'} {R['F2']}", flush=True)
    # F3
    w = pickle.loads(oct_); p = w.pays; a = A._dom(p); d = S._dom(p)
    for arm in a.armureries:
        for b in FI.ARMES_INDIVIDUELLES:
            q = float(arm.stock[a.bids[b]])
            if q > 0 and arm.lieu in w.carte.lieux: A.tirer(p, arm.lieu, b, q, "tir_instruction")
    for dep in d.depots:
        for b in FI.ARMES_INDIVIDUELLES:
            q = float(dep.stock[d.ids[b]])
            if q > 0: S._sortir(p, d, "depot", dep.k, b, q, "consommation_campagne")
    vide = FI.peut_combattre(w)
    b0 = sorted(d.besoins)[0]
    S._entrer(p, d, "base", b0, "mun_556", 1000.0, "achat_militaire")
    plein = FI.peut_combattre(w)
    F3 = vide == (False, "munitions") and plein == (True, None)
    R["F3"] = {"ok": F3, "vide": vide, "reapprovisionne": plein}
    print(f"  F3 munitions : {'OUI' if F3 else 'NON'} {R['F3']}", flush=True)
    # F4
    w = pickle.loads(oct_); p = w.pays; a = A._dom(p); E = a.eff
    for r in A._lignes_actives(a).tolist():
        i = int(E["hid"][r])
        if w.table.vivant[i]: POP.deceder(p, w.habitants[i], "maladie")
    morts = FI.peut_combattre(w)
    F4 = morts == (False, "soldats")
    R["F4"] = {"ok": F4, "resultat": morts}
    print(f"  F4 soldats : {'OUI' if F4 else 'NON'} {R['F4']}", flush=True)
    # F5
    w = pickle.loads(oct_); e = FI.etat(w)
    F5 = e["peut_combattre"] and e["capacite"]["aptes"] > 0 and (e["capacite"]["jours_munitions"].get("mun_556") or 0) > 0
    R["F5"] = {"ok": F5, "etat": e}
    print(f"  F5 ile ordinaire : {'OUI' if F5 else 'NON'} {e}", flush=True)
    oks = [R[k]["ok"] for k in ("F1", "F2", "F3", "F4", "F5")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graine=graine, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 5a DE LA FIN DE GUERRE : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_FIN", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2021))
