"""( 29/09, loi d Engel hors alimentation ) Le budget REALISE des menages par quintile de depense equivalente, sur la
fenetre de mesure, a cote de la ressemblance a la Grece. Ce que chaque menage a paye est lu au grand livre, par motif,
par un ecouteur des paiements ( lecture seule, enchaine a l enregistreur s il y en a un ) ; les menages sont classes comme
chez ELSTAT : consommation realisee par unite de consommation ( echelle OCDE modifiee, moyenne des soirs ), quintiles de
personnes. Les postes de consommation sont ceux de ressemblance._budget ( nature achat, hors formation de capital, un
menage qui paie un autre menage seulement pour un loyer ) ; la TVA d un menage est repartie sur ses achats aux marches.
Deux bras : --parts engel ( le code de la branche ) ou --parts identiques ( ENGEL_PARTS remplace par PARTS_HORS_ALIM a
chaque quintile, dans ce processus seulement : le partage du tronc, et le controle positif du critere 1 ).
Ecrit resultats/engel_<etiquette>.json et la ressemblance resultats/ressemblance_<etiquette>.md.
   python -m monde.mesure_engel --graine 71 --habitants 6375 --jours 365 --chauffe 40 --demographie grece --parts engel"""
import argparse, json, math, os, time
from collections import defaultdict
import numpy as np
from . import config as C, ressemblance as RS

RESULTATS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultats")

# Les motifs de consommation d un menage, par poste ( pour le rapport ). « achats du domaine 3 » : ce que le domaine 3
# achete lui-meme selon les parts du budget, hors nourriture et durables ( le critere 2 ).
GROUPES = {"alimentation": ("nourriture",),
           "logement": ("loyer", "facture_electricite", "facture_eau", "consommation_eau", "vente_combustible", "electricite"),
           "equipement": ("outils",),
           "sante": ("remedes", "remede", "consultation_medicale", "participation_hospitaliere", "participation_medicaments"),
           "transport": ("carburant", "carburant_station", "entretien_vehicule", "reparation_vehicule", "vente_vehicule",
                         "reprise_vehicule", "lecons_conduite", "rachat_vehicule_succession"),
           "communications": ("abonnement_telecom", "equipement_telecom"),
           "loisirs": ("spectacle", "panigyri", "abonnement_presse", "service_religieux", "droits_films"),
           "education": ("frontistirio",),
           "restauration": ("sortie_cafe_taverne",),
           "services_marchands": ("services_marchands",)}
ACHATS_D3 = ("services_marchands", "carburant", "remedes")
# ELSTAT 2024, la meme part hors alimentation ( parts voulues du domaine 3 : services marchands = habillement + boissons et
# tabac + moitie de la restauration + 60 % du divers ; carburant 35 % du transport ; remedes 40 % de la sante )


def _elstat_d3(P, EC):
    ix = {k: EC.NOMS_CATEGORIES.index(k) for k in EC.NOMS_CATEGORIES}
    return (P[:, ix["habillement"]] + P[:, ix["alcool_tabac"]] + 0.5 * P[:, ix["restauration"]] + 0.6 * P[:, ix["divers"]]
            + 0.35 * P[:, ix["transport"]] + 0.40 * P[:, ix["sante"]])


class Ecouteur:
    """Les paiements des menages, par ( menage, motif, le receveur est un menage ) ; les autres appels vont a
    l enregistreur enchaine, ou nulle part."""

    def __init__(self, suivant):
        self.suivant, self.actif, self.par = suivant, False, defaultdict(float)

    def argent(self, motif, de, vers, paye):
        if self.actif and paye > 0.0 and type(de).__name__ == "Menage":
            self.par[(int(de.id), motif, type(vers).__name__ == "Menage")] += float(paye)
        if self.suivant is not None: self.suivant.argent(motif, de, vers, paye)

    def __getattr__(self, nom):
        s = self.__dict__.get("suivant")
        if s is not None: return getattr(s, nom)
        return lambda *a, **k: None


def main(argv=None):
    a = argparse.ArgumentParser(description="Budget realise des menages par quintile de depense equivalente.")
    a.add_argument("--habitants", type=int, default=6375)
    a.add_argument("--jours", type=int, default=365)
    a.add_argument("--chauffe", type=int, default=40)
    a.add_argument("--graine", type=int, default=C.GRAINE)
    a.add_argument("--iles", default="Altis")
    a.add_argument("--demographie", default="grece")
    a.add_argument("--parts", choices=("engel", "identiques"), default="engel")
    a.add_argument("--etiquette", default=None)
    x = a.parse_args(argv)
    from . import monde as W
    from .pays import essais as E, pays as P, d03_economie as EC
    vraies = EC.ENGEL_PARTS.copy()
    if x.parts == "identiques": EC.ENGEL_PARTS[:] = np.tile(EC.PARTS_HORS_ALIM, (5, 1))
    et = x.etiquette or f"{x.parts}_g{x.graine}"
    t0 = time.perf_counter()
    kw = {"graine": x.graine, "echelle": x.habitants / 500.0, "iles": tuple(x.iles.split(","))}
    if x.demographie not in (None, "", "moteur"): kw["demographie"] = x.demographie
    w = W.Monde(**kw)
    p = P.installer(w, None)
    print(f"monde : {w.table.n} habitants, {len(p.domaines)} domaines, parts {x.parts} ; installation "
          f"{time.perf_counter() - t0:.0f} s", flush=True)
    E.jours(w, x.chauffe)
    L = p.socle.livre
    ec = Ecouteur(getattr(L, "enregistreur", None)); L.enregistreur = ec; ec.actif = True
    d = p.domaine("economie")
    br0 = d.budget_rang.copy()
    suivi = RS.Suivi(w, p)
    uc_s = np.zeros(0); v_s = np.zeros(0)
    t1 = time.perf_counter()
    for k in range(x.jours):
        E.jours(w, 1); suivi.apres_jour(w, p)
        n = len(w.menages)
        if len(uc_s) < n: uc_s = np.r_[uc_s, np.zeros(n - len(uc_s))]; v_s = np.r_[v_s, np.zeros(n - len(v_s))]
        v, _ = EC._tableaux_menages(p)
        uc_s[:n] += EC._uc_engel(p, n); v_s[:n] += v
        if (k + 1) % 30 == 0: print(f"  jour {w.jour} ( {k + 1}/{x.jours} ) {time.perf_counter() - t1:.0f} s", flush=True)
    t_jours = time.perf_counter() - t1
    ec.actif = False
    # --- la consommation realisee de chaque menage, par motif
    nat = {m: getattr(o, "nature", None) for m, o in L.motifs.items()}
    n = len(uc_s)
    conso = defaultdict(lambda: np.zeros(n))
    tva = np.zeros(n)
    for (i, m, vers_menage), s in ec.par.items():
        if i >= n: continue
        if m == "tva": tva[i] += s; continue
        if nat.get(m) != "achat" or m in RS.HORS_CONSOMMATION: continue
        if vers_menage and m != "loyer": continue
        conso[m][i] += s
    marches = sum((conso[m] for m in RS.BIENS_DES_MARCHES if m in conso), np.zeros(n))
    for m in RS.BIENS_DES_MARCHES:
        if m in conso: conso[m] += np.divide(tva * conso[m], marches, out=np.zeros(n), where=marches > 0)
    total = sum(conso.values(), np.zeros(n))
    sel = (uc_s > 0) & (v_s > 0) & (total > 0)
    r = np.full(n, -1.0)
    r[sel] = EC.rang_pondere(total[sel] / uc_s[sel], v_s[sel])
    q = np.where(sel, EC.quintile_de_rang(np.maximum(r, 0.0)), -1)
    classes = {m for g in GROUPES.values() for m in g}
    quint = []
    for qn in range(5):
        s_ = q == qn
        tot = float(total[s_].sum())
        alim = float(conso["nourriture"][s_].sum()) if "nourriture" in conso else 0.0
        hors = max(1e-12, tot - alim)
        par_groupe = {g: float(sum(conso[m][s_].sum() for m in ms if m in conso)) for g, ms in GROUPES.items()}
        autres = {m: float(v[s_].sum()) for m, v in conso.items() if m not in classes and v[s_].sum() > 0}
        d3 = float(sum(conso[m][s_].sum() for m in ACHATS_D3 if m in conso))
        quint.append({"menages": int(s_.sum()), "personnes_jours": float(v_s[s_].sum()),
                      "conso_par_uc_jour": tot / max(1e-12, float(uc_s[s_].sum())), "part_alimentation": alim / max(1e-12, tot),
                      "parts_hors_alim": {g: par_groupe[g] / hors for g in GROUPES if g != "alimentation"},
                      "part_d3_hors_alim": d3 / hors, "non_classes": autres})
    s1, s5 = quint[0]["part_d3_hors_alim"], quint[4]["part_d3_hors_alim"]
    R = s5 / s1 if s1 > 0 else math.inf
    R_elstat = float(_elstat_d3(vraies, EC)[4] / _elstat_d3(vraies, EC)[0])
    s80s20 = (quint[4]["conso_par_uc_jour"] * quint[4]["personnes_jours"]) / max(1e-12, quint[0]["conso_par_uc_jour"] * quint[0]["personnes_jours"])
    # --- critere 1 : la structure VOULUE hors alimentation par quintile de rang, sur la fenetre, contre les vraies parts
    B = d.budget_rang - br0
    H = B.copy(); H[:, EC.I_ALIM] = 0.0; H /= np.maximum(1e-12, H.sum(axis=1, keepdims=True))
    ecart_voulu = float(np.abs(H - vraies).max())
    lignes = RS.mesurer(w, p, suivi=suivi, refs=RS.charger())
    res = {"etiquette": et, "parts": x.parts, "graine": x.graine, "habitants": int(w.table.n), "jours": x.jours,
           "chauffe": x.chauffe, "demographie": x.demographie, "s_par_jour": t_jours / max(1, x.jours),
           "critere1_ecart_voulu_max": ecart_voulu, "voulu_hors_alim_par_quintile": H.tolist(),
           "critere2_R_d3": R, "R_d3_elstat": R_elstat, "part_d3_Q1": s1, "part_d3_Q5": s5,
           "s80s20_realise": s80s20, "quintiles": quint,
           "resume": RS.resume(lignes),
           "ressemblance": [{k: l[k] for k in ("id", "simule", "reel", "bande", "verdict", "surete")} for l in lignes]}
    os.makedirs(RESULTATS, exist_ok=True)
    chemin = os.path.join(RESULTATS, f"engel_{et}.json")
    with open(chemin, "w", encoding="utf-8") as f: json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(RESULTATS, f"ressemblance_engel_{et}.md"), "w", encoding="utf-8") as f:
        f.write(RS.tableau_markdown(lignes, f"# Ressemblance : engel {et}\n\nGraine {x.graine}, parts {x.parts}, "
                                            f"chauffe {x.chauffe} j, mesure {x.jours} j."))
    print(f"critere 1 : ecart voulu max {ecart_voulu * 100:.2f} point ; critere 2 : R = {R:.3f} ( ELSTAT {R_elstat:.3f} ), "
          f"part d3 Q1 {s1:.3f} Q5 {s5:.3f} ; S80/S20 realise {s80s20:.2f} ; {t_jours / max(1, x.jours):.2f} s par jour")
    print(f"ecrit : {chemin}")


if __name__ == "__main__":
    main()
