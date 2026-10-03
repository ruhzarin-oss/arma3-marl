"""Porte S1 de l etat-major, sa mecanique ( HMT-198 ). Criteres ecrits avant la mesure ( Plane, 03/10 ) : Stratis
( 2061 ) contre Malden ( 2062 ), echelle 20.

E1  lecture seule : situation() laisse le monde de A identique au bit sur 2 jours.
E2  validation : modele, objectif, parachutage sans avion, nombre hors bornes, type inconnu refuses avec leur raison ;
    les actions valides acceptees.
E3  le jeu ne touche pas au reel : apres jouer(), A identique au bit a son jumeau ; le vrai B jamais lu ( empreinte
    inchangee, jouer() ne le recoit pas ).
E4  l estimation honnete : le B estime n est pas le vrai ( graine, effectifs differents ) et porte exactement les degats
    constates par les operations de A.
E5  un tour complet : doctrine et mauvais strategie executent leur choix dans A ( trace ) ; Qwen rend un JSON valide, au
    moins un mode valide, une decision executee.
E6  la trace : situation, modes, jeux, choix, execution.
python -m guerre.porte_etat_major [ graine_A graine_B ]"""
import inspect
import json
import pickle
import sys
import time

from monde import archipel as AR, tests as T
from . import etat_major as EM, expedition as EX, fin as FI, frappes as FR, projection as PR
from .arsenal import porte_etat_des_lieux as PE
from .connaissance import index as IX

SORTIE = "/mnt/data/hmt/arsenal/porte_etat_major.json"


def main(gA=2061, gB=2062):
    t0 = time.time(); R = {}
    print(f"PORTE S1 DE L ETAT-MAJOR : Stratis {gA} contre Malden {gB}", flush=True)
    wA0 = AR.creer_ile("Stratis", gA, 20); T.jours(wA0, 1)
    wB0 = AR.creer_ile("Malden", gB, 20); T.jours(wB0, 1)
    octA, octB = pickle.dumps(wA0, protocol=4), pickle.dumps(wB0, protocol=4)
    # E1
    w1, w2 = pickle.loads(octA), pickle.loads(octA); ident = True
    for _ in range(2):
        EM.situation(w1, "Stratis", "Malden")
        T.jours(w1, 1); T.jours(w2, 1)
        if PE.empreinte_etendue(w1) != PE.empreinte_etendue(w2): ident = False
    R["E1"] = {"ok": ident}
    print(f"  E1 lecture seule : {'OUI' if ident else 'NON'}", flush=True)
    # E2
    w = pickle.loads(octA)
    mauvaises = [{"type": "voler"}, {"type": "acheter", "modele": "f16", "nombre": 1}, {"type": "acheter", "modele": "lcu", "nombre": 9},
                 {"type": "operation", "objectif": "lune01", "modele": "lcu", "hommes": 100},
                 {"type": "operation", "objectif": "port01", "modele": "lcu", "hommes": 100, "parachutage": True},
                 {"type": "operation", "objectif": "port01", "modele": "lcu", "hommes": 0}]
    bonnes = [{"type": "attendre"}, {"type": "acheter", "modele": "c130j", "nombre": 1},
              {"type": "operation", "objectif": "port01", "modele": "c130j", "hommes": 60, "parachutage": True}]
    rm = [EM.valider(w, "Malden", a) for a in mauvaises]; rb = [EM.valider(w, "Malden", a) for a in bonnes]
    E2 = all(v is None and r for v, r in rm) and all(v is not None and r is None for v, r in rb)
    R["E2"] = {"ok": E2, "refus": [r for _v, r in rm], "acceptees": [v for v, _r in rb]}
    print(f"  E2 validation : {'OUI' if E2 else 'NON'} {R['E2']}", flush=True)
    # E3
    wa, wt = pickle.loads(octA), pickle.loads(octA); wb = pickle.loads(octB); emp_b = PE.empreinte_etendue(wb)
    mode = {"nom": "essai", "actions": [{"type": "acheter", "modele": "lcu", "nombre": 2},
                                        {"type": "operation", "objectif": "port01", "modele": "lcu", "hommes": 400}]}
    jeu = EM.jouer(wa, "Stratis", "Malden", mode)
    sans_b = "wB" not in inspect.signature(EM.jouer).parameters
    E3 = PE.empreinte_etendue(wa) == PE.empreinte_etendue(wt) and PE.empreinte_etendue(wb) == emp_b and sans_b
    R["E3"] = {"ok": E3, "jeu": jeu["bilan"], "jouer_ne_recoit_pas_B": sans_b}
    print(f"  E3 jeu sans effet : {'OUI' if E3 else 'NON'} {R['E3']}", flush=True)
    # E4 : l estimation porte exactement les degats constates
    we = pickle.loads(octA)
    EX._ops(we).append({"id": 99, "objectif": "depot01", "etat": "rentree", "numeros": [], "assaut": {"dommages": 0.5, "sorts": [], "arrives": 1}})
    est = EM.estimation("Malden", 20, we)
    wB_vrai = pickle.loads(octB)
    E4 = (FR._etat(est) == {"depot01": 0.5} and FI.aptes(est) != FI.aptes(wB_vrai)
          and EM.GRAINE_ESTIMATION not in (gA, gB) and int(est.pas) == int(we.pas))
    R["E4"] = {"ok": E4, "degats_estimes": FR._etat(est), "aptes_estime": FI.aptes(est), "aptes_vrai": FI.aptes(wB_vrai), "pas": [int(est.pas), int(we.pas)]}
    print(f"  E4 estimation : {'OUI' if E4 else 'NON'} {R['E4']}", flush=True)
    # E5 et E6 : des tours complets
    out5 = {}; traces = []
    for chef in ("doctrine", "mauvais"):
        wc = pickle.loads(octA)
        tr = EM.tour(wc, "Stratis", "Malden", chef=chef)
        ok_exec = all(r.get("ok") for _a, r in tr["execution"])
        achats = sum(r.get("achetes") or 0 for _a, r in tr["execution"])
        flotte = sum(1 for _ in PR._P(wc)["flotte"])
        out5[chef] = {"ok": ok_exec and achats == flotte and achats > 0, "execution": tr["execution"], "flotte": flotte}
        traces.append(tr)
    I = IX.ouvrir(); wq = pickle.loads(octA)
    trq = EM.tour(wq, "Stratis", "Malden", chef="qwen", index=I)
    traces.append(trq)
    valides = [m for m in trq["modes"] if all(EM.valider(wq, "Malden", a)[0] is not None for a in m.get("actions", []))]
    out5["qwen"] = {"ok": bool(trq["proposition"]["json"]) and bool(valides) and any(r.get("ok") for _a, r in trq["execution"]),
                    "modes": [m.get("nom") for m in trq["modes"]], "choix": trq["choix"], "execution": trq["execution"],
                    "ordre": trq.get("decision", {}).get("reponse", "")[:600], "duree_s": trq["duree_s"]}
    E5 = all(v["ok"] for v in out5.values())
    R["E5"] = {"ok": E5, **out5}
    print(f"  E5 tours : {'OUI' if E5 else 'NON'} {R['E5']}", flush=True)
    cles = ("jour", "chef", "modes", "jeux", "choix", "execution")
    E6 = all(all(k in tr for k in cles) for tr in traces)
    R["E6"] = {"ok": E6}
    print(f"  E6 trace : {'OUI' if E6 else 'NON'}", flush=True)
    oks = [R[k]["ok"] for k in ("E1", "E2", "E3", "E4", "E5", "E6")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graines=[gA, gB], duree_s=round(time.time() - t0), traces=traces)
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE S1 DE L ETAT-MAJOR : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_ETAT_MAJOR", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(main(int(a[0]), int(a[1])) if len(a) >= 2 else main())
