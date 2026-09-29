"""PORTE DE L ALLOCATION POUR ENFANT A21 ( 28/09, chef de projet ; criteres ecrits AVANT la mesure ). L allocation est
branchee dans tous les mondes, apres le KEA ( les 9 morts de faim qui restaient sur Altis avec HMT-126 a etaient des
enfants ). Chaque monde joue deux fois, meme graine, meme code : AVEC l allocation ( le defaut ) et SANS ( sa routine
de 18 h retiree ; le KEA reste ). On juge les morts de faim des ENFANTS ( moins de 18 ans ).
K1 Altis par defaut ( echelle 20 ), 90 jours.   K2 Stratis de l archipel ( graine 1, echelle 20 ), 200 jours.
K3 Altis en mode grec ( echelle 20 ), 365 jours.
Criteres, dans chaque monde : les morts de faim d enfants pour 100 000 enfants du depart avec l allocation ne depassent
pas celles sans elle ; la ou le temoin en compte au moins 50 pour 100 000, l allocation en retire au moins la moitie ; la
conservation tient ; le cout ( somme versee ) est entre 0,2 % et 5 % des versements de l Etat de la meme periode ( le
reel grec : environ 1 %, de l ordre d un milliard d euros par an pour 105 milliards de depense publique, A VERIFIER ).
   python -m monde.porte_allocation [ K1,K2,K3 ]"""
import sys, time, math
from multiprocessing import get_context
from .pays import pays as P, d06_etat as ET, d01_population as D1
import numpy as np
from .pays import essais as E

MONDES = {"K1": ("Altis par defaut", 90), "K2": ("Stratis archipel", 200), "K3": ("Altis grec", 365)}


def _monde(cle):
    if cle == "K2":
        from .archipel import creer_ile
        return creer_ile("Stratis", 1, 20.0)
    w, _ = E.monde([nom for nom, mod, _ in P.DOMAINES], echelle=20.0, demographie="grece" if cle == "K3" else None)
    return w


def _jouer(args):
    cle, kea = args
    t0 = time.time()
    w = _monde(cle); p = w.pays; nom, jours = MONDES[cle]
    if not kea:
        for m, rs in p.routines.items(): p.routines[m] = [r for r in rs if r[2] is not ET._allocation_enfant]
    tb = w.table; col = p.colonnes["habitant"]; L = p.socle.livre
    j0 = int(w.jour); v0 = int(tb.vivant[:tb.n].sum())
    age0 = (p.jour - col["naissance_j"][:tb.n].astype(np.float64)) / 365.0
    e0 = int(((tb.vivant[:tb.n] == 1) & (age0 < 18)).sum())
    verse = [0.0]; dep = [0.0]
    tr0 = type(L).transferer
    def tr(self, de, vers, montant, motif):
        r = tr0(self, de, vers, montant, motif)
        if self is L and de is w.gouv:
            dep[0] += r or 0.0
            if motif == "allocation_enfant": verse[0] += r or 0.0
        return r
    type(L).transferer = tr
    for _ in range(jours): E.jours(w, 1)
    n = tb.n
    age_mort = (col["deces_j"][:n].astype(np.float64) - col["naissance_j"][:n].astype(np.float64)) / 365.0
    faim = int(((col["cause_deces"][:n] == D1.CAUSES.index("faim")) & (col["deces_j"][:n] >= j0) & (age_mort < 18)).sum())
    v1 = int(tb.vivant[:n].sum())
    return {"monde": nom, "allocation": kea, "jours": jours, "enfants0": e0, "vivants0": v0, "vivants": v1, "morts_de_faim_enfants": faim,
            "faim_100k": round(faim * 1e5 / max(1, e0), 1), "perdus_pct": round(100.0 * (v0 - v1) / max(1, v0), 2),
            "allocation_versee": round(verse[0]), "depense_publique": round(dep[0]), "part_pct": round(100.0 * verse[0] / max(1.0, dep[0]), 3),
            "conservation": bool(p.socle.conservation.tenue()[0]), "secondes": round(time.time() - t0)}


def main():
    cles = sys.argv[1].split(",") if len(sys.argv) > 1 else list(MONDES)
    t0 = time.time(); ok = {}
    for cle in cles:
        with get_context("spawn").Pool(2) as pool:
            avec, sans = pool.map(_jouer, [(cle, True), (cle, False)])
        print(f"   {cle} {avec['monde']} : AVEC {avec} ; SANS {sans}", flush=True)
        c = f"{cle} {avec['monde']}"
        ok[f"{c} : morts de faim d enfants avec l allocation pas plus qu sans ; conservation"] = avec["faim_100k"] <= sans["faim_100k"] and avec["conservation"]
        if sans["faim_100k"] >= 50:
            ok[f"{c} : l allocation retire au moins la moitie des morts de faim d enfants"] = avec["faim_100k"] <= 0.5 * sans["faim_100k"]
        ok[f"{c} : l allocation coute entre 0,2 % et 5 % des versements de l Etat"] = 0.2 <= avec["part_pct"] <= 5.0
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DE L ALLOCATION POUR ENFANT : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
