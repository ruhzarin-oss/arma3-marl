"""PORTE DE L HISTORIQUE DU KEA ( 29/09, chef de projet ; criteres ecrits AVANT la mesure sur les graines 51 a 53 ; sur
la graine du moteur, la sonde avait deja vu : paie du premier mois / m0 pose = 1,019 dans l Altis par defaut, 1,041 dans
l Altis grec ). Les six mois declares avant le jour 0 suivent la situation REELLE de chaque membre
( d06._revenu_avant_le_jour_0 ), et non plus le revenu estime par le domaine 3 avant le recensement du travail.
H1, a l installation, Altis par defaut et Altis grec ( echelle 20 ), graines 51, 52 et 53 :
  a) un menage dont aucun membre n est en emploi, ne touche de pension, ni n est chomeur a un historique NUL ( six mois ) ;
  b) un menage dont tous les membres vivants sont en emploi ou enfants ( sans pension ni chomeur ) : chaque mois vaut
     30 fois la somme des revenus attendus de ses membres ( 1e-9 relatif ) ;
  c) un menage d un seul adulte, chomeur, et d enfants : sans emploi depuis plus de 540 jours ( ses douze mois d indemnite
     finis avant la fenetre ), son historique est nul ; depuis moins de 30 jours, les mois m1 a m5 valent son salaire
     entier ( 30 fois son revenu attendu ) ;
  d) la paie vue le premier mois ( rmg_mois apres 30 jours, KEA exclu ) est a 10 % pres du mois m0 pose, en somme sur le
     pays ;
  chaque cas a), b), c) compte au moins 5 menages sur les trois graines ( sinon rien n est prouve ).
  Controle positif : l ancien historique ( 30 fois le revenu estime par le domaine 3 ) echoue a a) dans l Altis par defaut.
H2, l effet, Altis par defaut ( le monde de K1 ), 90 jours, graines 51 a 53, AVEC et SANS le KEA ( sa routine retiree ) :
  le KEA verse des le premier mois ( plus de 0 les 30 premiers jours ) ; son cout sur 90 jours est entre 0,1 % et 3 % de la
  depense publique ; les morts de faim avec le KEA ne depassent pas celles sans lui ; la conservation tient.
   python -m monde.porte_historique_kea [ H1,H2 ]"""
import sys, time
import numpy as np
from multiprocessing import get_context
from .pays import pays as P, essais as E, d01_population as D1, d03_economie as EC, d04_travail as TV, d06_etat as ET

GRAINES = (51, 52, 53)
MONDES = {"defaut": None, "grec": "grece"}
J = float(EC.MOIS_J)


def _monde(demographie, graine):
    w, _ = E.monde([nom for nom, mod, _ in P.DOMAINES], graine=graine, echelle=20.0, demographie=demographie)
    return w


def _h1(args):
    nom, graine = args
    w = _monde(MONDES[nom], graine); p = w.pays; tb = w.table; M = len(w.menages)
    cm = p.colonnes["menage"]; col = p.colonnes["habitant"]; d4 = p.domaine("travail"); imp = w.gouv.impot_revenu
    passe = np.stack([cm[c][:M] for c in ET.KEA_COMPTES], axis=1).copy()
    ancien = J * cm["eco_revenu"][:M]
    age = (p.jour - col["naissance_j"][:tb.n].astype(np.float64)) / 365.0
    membres = {}
    for i in np.nonzero(tb.vivant[:tb.n] == 1)[0].tolist():
        m = int(tb.menage[i])
        if 0 <= m < M: membres.setdefault(m, []).append(i)
    a = b = c = 0; a_ok = b_ok = c_ok = True; a_ancien = 0
    for m, ids in membres.items():
        if cm["dissous"][m]: continue
        st = [int(col["tr_statut"][i]) for i in ids]; pen = [i in d4.pensions for i in ids]
        emploi = [s in TV.EN_EMPLOI for s in st]; chom = [s == TV.CHOMEUR for s in st]
        enfant = [age[i] < ET.AGE_ADULTE_KEA for i in ids]
        if not any(emploi) and not any(pen) and not any(chom):
            a += 1; a_ok &= bool(np.all(passe[m] == 0.0)); a_ancien += int(ancien[m] > 0)
        elif not any(pen) and not any(chom) and all(e or f for e, f in zip(emploi, enfant)):
            att = J * sum(EC._revenu_attendu(w.habitants[i], imp) for i, e in zip(ids, emploi) if e)
            b += 1; b_ok &= bool(np.all(np.abs(passe[m] - att) <= 1e-9 * max(1.0, att)))
        adultes = [i for i, f in zip(ids, enfant) if not f]
        autres = [x for x in ids if x not in adultes]
        if (len(adultes) == 1 and int(col["tr_statut"][adultes[0]]) == TV.CHOMEUR and not any(pen)
                and not any(int(col["tr_statut"][x]) in TV.EN_EMPLOI or x in d4.indemnites for x in autres)):
            i = adultes[0]; perte = float(col["tr_chomage_j"][i]) - p.jour
            if perte < -540:
                c += 1; c_ok &= bool(np.all(passe[m] == 0.0))
            elif perte > -30:
                c += 1; sal = J * EC._revenu_attendu(w.habitants[i], imp)
                c_ok &= bool(np.all(np.abs(passe[m, 1:] - sal) <= 1e-9 * max(1.0, sal)))
    m0 = float(passe[:, 0][cm["dissous"][:M] == 0].sum())
    for _ in range(30): E.jours(w, 1)
    vu = float(cm["rmg_mois"][:M][cm["dissous"][:M] == 0].sum())
    return {"monde": nom, "graine": graine, "a": a, "a_ok": a_ok, "a_ancien_non_nul": a_ancien, "b": b, "b_ok": b_ok,
            "c": c, "c_ok": c_ok, "m0": round(m0), "vu": round(vu), "rapport": round(vu / max(1.0, m0), 3)}


def _h2(args):
    graine, kea = args
    t0 = time.time()
    w = _monde(None, graine); p = w.pays; tb = w.table; col = p.colonnes["habitant"]; L = p.socle.livre
    if not kea:
        for m, rs in p.routines.items(): p.routines[m] = [r for r in rs if r[2] is not ET._revenu_minimum]
    j0 = int(w.jour); v0 = int(tb.vivant[:tb.n].sum())
    verse = [0.0]; dep = [0.0]; mois1 = [0.0]
    tr0 = type(L).transferer
    def tr(self, de, vers, montant, motif):
        r = tr0(self, de, vers, montant, motif)
        if self is L and de is w.gouv:
            dep[0] += r or 0.0
            if motif == "revenu_minimum":
                verse[0] += r or 0.0
                if p.jour - j0 < 30: mois1[0] += r or 0.0
        return r
    type(L).transferer = tr
    for _ in range(90): E.jours(w, 1)
    type(L).transferer = tr0
    n = tb.n
    faim = int(((col["cause_deces"][:n] == D1.CAUSES.index("faim")) & (col["deces_j"][:n] >= j0)).sum())
    return {"graine": graine, "kea": kea, "vivants0": v0, "morts_de_faim": faim, "kea_mois1": round(mois1[0]),
            "kea_verse": round(verse[0]), "depense_publique": round(dep[0]),
            "kea_part_pct": round(100.0 * verse[0] / max(1.0, dep[0]), 3),
            "conservation": bool(p.socle.conservation.tenue()[0]), "secondes": round(time.time() - t0)}


def main():
    quoi = sys.argv[1].split(",") if len(sys.argv) > 1 else ["H1", "H2"]
    t0 = time.time(); ok = {}
    with get_context("spawn").Pool(3) as pool:
        if "H1" in quoi:
            rs = pool.map(_h1, [(nom, g) for nom in MONDES for g in GRAINES])
            for r in rs: print("   H1", r, flush=True)
            for nom in MONDES:
                q = [r for r in rs if r["monde"] == nom]
                ok[f"H1 {nom} : a) sans emploi, pension ni chomage, historique nul ( {sum(r['a'] for r in q)} menages )"] = (
                    all(r["a_ok"] for r in q) and sum(r["a"] for r in q) >= 5)
                ok[f"H1 {nom} : b) en emploi ou enfants, 30 x les revenus attendus ( {sum(r['b'] for r in q)} menages )"] = (
                    all(r["b_ok"] for r in q) and sum(r["b"] for r in q) >= 5)
                ok[f"H1 {nom} : c) un seul adulte chomeur : nul apres 540 jours, salaire entier avant 30 jours ( {sum(r['c'] for r in q)} menages )"] = (
                    all(r["c_ok"] for r in q) and sum(r["c"] for r in q) >= 5)
                ok[f"H1 {nom} : d) paie du premier mois a 10 % pres de m0 ( {[r['rapport'] for r in q]} )"] = all(
                    abs(r["rapport"] - 1.0) <= 0.10 for r in q)
            ok["H1 controle positif : l ancien historique echoue a a) dans l Altis par defaut"] = any(
                r["a_ancien_non_nul"] > 0 for r in rs if r["monde"] == "defaut")
        if "H2" in quoi:
            rs = pool.map(_h2, [(g, k) for g in GRAINES for k in (True, False)])
            for r in rs: print("   H2", r, flush=True)
            for g in GRAINES:
                avec = next(r for r in rs if r["graine"] == g and r["kea"]); sans = next(r for r in rs if r["graine"] == g and not r["kea"])
                ok[f"H2 graine {g} : le KEA verse le premier mois ( {avec['kea_mois1']} )"] = avec["kea_mois1"] > 0
                ok[f"H2 graine {g} : cout entre 0,1 % et 3 % ( {avec['kea_part_pct']} % )"] = 0.1 <= avec["kea_part_pct"] <= 3.0
                ok[f"H2 graine {g} : morts de faim avec le KEA pas plus qu sans ( {avec['morts_de_faim']} contre {sans['morts_de_faim']} ) ; conservation"] = (
                    avec["morts_de_faim"] <= sans["morts_de_faim"] and avec["conservation"] and sans["conservation"])
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DE L HISTORIQUE DU KEA : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
