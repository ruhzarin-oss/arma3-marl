"""PORTE DE LA PAIE REELLE ( HMT-126 a, 28/09 ; criteres ecrits AVANT la mesure, chef de projet ). Une famine dans tous
les mondes, en paix aussi ( Classes : Altis grec, un an, 12 354 morts de faim pour 100 000 ; Altis par defaut, 90 jours,
202 ; Stratis, 200 jours, 12 % de la population ; la Malden de l essai22n, 562 morts de faim en 30 jours ). Le
diagnostic de la guerre : 74 % des menages affames ont un salarie que son employeur ne paie plus ( convoyeurs, ouvriers
des fonderies ), et 95 % des marchands touchent 0. Le correctif ( references/correctifs/patch_paie_reelle.py ) : le
salarie sans paie nette depuis 30 jours devient chomeur ( indemnite DYPA ), le marchand vit de la marge de la veille.

Chaque monde joue deux fois, meme graine, meme code : AVEC le correctif et SANS ( le temoin : la rupture neutralisee,
IMPAYE_RUPTURE_J infini, et la marge du soir retiree - l ancienne regle des marchands ). On juge les MORTS de faim pour
100 000 vivants du depart et la population perdue, pas la faim des vivants ( HMT-136 ).
P1 la Malden de l essai22n ( instantane d arret, jour 111 ), 30 jours.
P2 Altis par defaut ( echelle 20 : 10 000 habitants, tous les domaines ), 90 jours.
P3 Stratis de l archipel ( graine 1, echelle 20 ), 200 jours.
P4 Altis en mode grec ( echelle 20, demographie « grece » ), 365 jours.
Critere : dans chaque monde ou le temoin compte au moins 50 morts de faim pour 100 000, le correctif en compte au plus
le dixieme ( un ordre de grandeur de moins ; le reel grec : environ 0 ) ; la conservation tient. Controle positif : au
moins deux mondes ou le temoin atteint 50 pour 100 000 - sinon la porte ne sait pas echouer et elle est REFUSEE.

   python -m monde.porte_paie [ P1,P2,P3,P4 ]"""
import sys, time
from multiprocessing import get_context
import numpy as np
from . import config as C, monde as W
from .pays import pays as P, d04_travail as TV, d01_population as D1
from .pays import essais as E

MALDEN = "/mnt/data/hmt/guerre/essai22n/Malden_j111.pkl"
MONDES = {"P1": ("Malden essai22n", 30), "P2": ("Altis par defaut", 90), "P3": ("Stratis archipel", 200),
          "P4": ("Altis grec", 365)}


def _monde(cle):
    if cle == "P1":
        from .archipel import charger, _convois
        return _convois(charger(MALDEN), 200.0)
    if cle == "P3":
        from .archipel import creer_ile
        return creer_ile("Stratis", 1, 20.0)
    w, _ = E.monde([nom for nom, mod, _ in P.DOMAINES], echelle=20.0, demographie="grece" if cle == "P4" else None)
    return w


def _jouer(args):
    cle, correctif = args
    t0 = time.time()
    if not correctif: TV.IMPAYE_RUPTURE_J = 10 ** 9
    w = _monde(cle); p = w.pays; nom, jours = MONDES[cle]
    if not correctif:
        for m, rs in p.routines.items(): p.routines[m] = [r for r in rs if r[2] is not TV._marge_du_jour]
        p.domaine("travail").marge_veille = None
    tb = w.table; col = p.colonnes["habitant"]
    j0 = int(w.jour); v0 = int(tb.vivant[:tb.n].sum())
    ruptures = 0.0
    for _ in range(jours):
        E.jours(w, 1)
        c = p.socle.journal.comptes.get("rupture_salaire_impaye") if hasattr(p.socle.journal, "comptes") else None
        ruptures += c[0] if c else 0
    n = tb.n
    faim = int(((col["cause_deces"][:n] == D1.CAUSES.index("faim")) & (col["deces_j"][:n] >= j0)).sum())
    morts = int(((col["deces_j"][:n] >= j0)).sum())
    v1 = int(tb.vivant[:n].sum())
    return {"monde": nom, "correctif": correctif, "jours": jours, "vivants0": v0, "vivants": v1, "morts": morts,
            "morts_de_faim": faim, "faim_100k": round(faim * 1e5 / max(1, v0), 1), "perdus_pct": round(100.0 * (v0 - v1) / max(1, v0), 2),
            "ruptures": int(ruptures), "conservation": bool(p.socle.conservation.tenue()[0]), "secondes": round(time.time() - t0)}


def main():
    cles = sys.argv[1].split(",") if len(sys.argv) > 1 else list(MONDES)
    t0 = time.time(); res = {}
    for cle in cles:
        with get_context("spawn").Pool(2) as pool:
            avec, sans = pool.map(_jouer, [(cle, True), (cle, False)])
        res[cle] = (avec, sans)
        print(f"   {cle} {avec['monde']} : AVEC {avec} ; SANS {sans}", flush=True)
    informatifs = [c for c, (a, s) in res.items() if s["faim_100k"] >= 50]
    ok = {}
    for c, (a, s) in res.items():
        if c in informatifs:
            ok[f"{c} {a['monde']} : morts de faim pour 100 000 au plus le dixieme du temoin ; conservation"] = (
                a["faim_100k"] <= 0.1 * s["faim_100k"] and a["conservation"])
    ok["controle positif : au moins deux mondes ou le temoin atteint 50 morts de faim pour 100 000"] = len(informatifs) >= 2 or len(res) < 4
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DE LA PAIE : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
