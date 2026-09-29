"""( 29/09, HMT-145 ) Les enveloppes sur une annee : la ressemblance a la Grece ( epargne, morts de faim, inflation, part
de l alimentation ), la structure REALISEE de la consommation par division contre ELSTAT HBS 2024 ( tableau 1 ), les
substitutions par division, les fuites, le compte des enveloppes, le cout par jour. Deux bras : --enveloppes oui ( le
code de la branche ) ou non ( d03.ENVELOPPES a False dans ce processus seulement : le comportement du tronc ). Lecture
seule. Ecrit resultats/enveloppes_<etiquette>.json et resultats/ressemblance_enveloppes_<etiquette>.md.
   python -m monde.mesure_enveloppes --graine 81 --habitants 6375 --jours 365 --chauffe 40 --demographie grece --enveloppes oui"""
import argparse, json, os, time
from collections import defaultdict
import numpy as np
from . import config as C, ressemblance as RS

RESULTATS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultats")
# ELSTAT HBS 2024, tableau 1 ( % de la depense ), ramene aux 12 divisions du moteur ( divers = assurances et services
# financiers 2,2 + soins personnels et divers 4,9 )
ELSTAT_2024 = {"alimentation": 20.7, "alcool_tabac": 3.4, "habillement": 5.0, "logement": 14.4, "equipement": 4.3,
               "sante": 7.8, "transport": 13.3, "communications": 4.8, "loisirs": 4.0, "education": 3.5,
               "restauration": 11.8, "divers": 7.1}
BIENS_D03 = {"nourriture": "alimentation", "remedes": "sante", "carburant": "transport", "outils": "equipement"}


def structure(argent, nature, EC):
    """La consommation des menages ( et de leurs membres ) par division, TVA des biens des marches repartie comme dans
    ressemblance._budget ; services_marchands a part ( un melange : habillement, boissons et tabac, restauration, divers )."""
    par = defaultdict(float); tva = marches = 0.0
    for (m, pa, re), s in argent.items():
        if pa not in ("Menage", "Habitant"): continue
        if m == "tva": tva += s; continue
        if nature.get(m) != "achat" or m in RS.HORS_CONSOMMATION: continue
        if re == "Menage" and m != "loyer": continue
        if m in BIENS_D03: dv = BIENS_D03[m]; marches += s if re == "Marche" else 0.0
        elif m.startswith("substitution_"): dv = m[len("substitution_"):]
        elif m == "services_marchands": dv = "services_marchands"
        else: dv = EC.MOTIFS_DIVISION.get(m, "autres:" + m)
        par[dv] += s
    if marches > 0:
        for m, dv in BIENS_D03.items():
            q = sum(s for (mo, pa, re), s in argent.items() if mo == m and pa in ("Menage", "Habitant") and re == "Marche")
            par[dv] += tva * q / marches
    tot = sum(par.values())
    return {k: 100.0 * v / tot for k, v in sorted(par.items())} if tot > 0 else {}, tot


def main(argv=None):
    a = argparse.ArgumentParser(description="Les enveloppes sur une annee ( HMT-145 ).")
    a.add_argument("--habitants", type=int, default=6375)
    a.add_argument("--jours", type=int, default=365)
    a.add_argument("--chauffe", type=int, default=40)
    a.add_argument("--graine", type=int, default=C.GRAINE)
    a.add_argument("--iles", default="Altis")
    a.add_argument("--demographie", default="grece")
    a.add_argument("--enveloppes", choices=("oui", "non"), default="oui")
    a.add_argument("--etiquette", default=None)
    x = a.parse_args(argv)
    from . import monde as W
    from .pays import essais as E, pays as P, d03_economie as EC
    EC.ENVELOPPES = x.enveloppes == "oui"
    et = x.etiquette or f"{x.enveloppes}_g{x.graine}"
    t0 = time.perf_counter()
    kw = {"graine": x.graine, "echelle": x.habitants / 500.0, "iles": tuple(x.iles.split(","))}
    if x.demographie not in (None, "", "moteur"): kw["demographie"] = x.demographie
    w = W.Monde(**kw)
    p = P.installer(w, None)
    print(f"monde : {w.table.n} habitants, {len(p.domaines)} domaines, enveloppes {x.enveloppes} ; installation "
          f"{time.perf_counter() - t0:.0f} s", flush=True)
    E.jours(w, x.chauffe)
    d = p.domaine("economie")
    ec0 = getattr(d, "env_compte", np.zeros((3, EC.K))).copy()
    suivi = RS.Suivi(w, p)
    t1 = time.perf_counter()
    for k in range(x.jours):
        E.jours(w, 1); suivi.apres_jour(w, p)
        if (k + 1) % 30 == 0: print(f"  jour {w.jour} ( {k + 1}/{x.jours} ) {time.perf_counter() - t1:.0f} s", flush=True)
    t_jours = time.perf_counter() - t1
    L = p.socle.livre
    nature = {m: getattr(o, "nature", None) for m, o in L.motifs.items()}
    struct, conso = structure(suivi.argent, nature, EC)
    ec = getattr(d, "env_compte", np.zeros((3, EC.K))) - ec0
    n = len(w.menages)
    env = {}
    if x.enveloppes == "oui":
        for k_ in EC.IDX_ENVELOPPE:
            nom = EC.NOMS_CATEGORIES[k_]; c = p.col("menage", f"eco_env_{nom}")[:n]
            env[nom] = {"entrees": float(ec[0, k_]), "encaisse": float(ec[1, k_]), "substitue": float(ec[2, k_]),
                        "part_negative": float((c < 0).mean()) if n else 0.0}
    st = p.col("menage", "im_statut")[:n] if "im_statut" in p.colonnes["menage"] else np.zeros(0)
    occupation = {}
    if len(st):
        v_, _ = EC._tableaux_menages(p); hb = (v_ > 0) & (p.col("menage", "dissous")[:n] == 0)
        _, s = EC.parts_d_occupation(st, hb) if hasattr(EC, "parts_d_occupation") else (None, float("nan"))
        f_p, f_l = EC.multiplicateurs_occupation(s)
        occupation = {"part_locataires_monde": s, "part_locataires_grece": EC.PART_LOCATAIRES_GRECE, "f_proprietaire": f_p,
                      "f_locataire": f_l, "moyenne_ponderee": (1.0 - s) * f_p + s * f_l,
                      "habites": int(hb.sum()), "sans_statut_habites": int((hb & (st != 1) & (st != 2)).sum())}
    lignes = RS.mesurer(w, p, suivi=suivi, refs=RS.charger())
    rs = {l["id"]: l for l in lignes}
    res = {"etiquette": et, "enveloppes": x.enveloppes, "graine": x.graine, "habitants": int(w.table.n), "jours": x.jours,
           "chauffe": x.chauffe, "demographie": x.demographie, "s_par_jour": t_jours / max(1, x.jours),
           "structure_realisee": struct, "elstat_2024": ELSTAT_2024, "consommation_fenetre": conso,
           "enveloppes_par_division": env, "fuites": dict(getattr(d, "sans_division", {})),
           "occupation": occupation,
           "statuts": {str(int(k)): int((st == k).sum()) for k in np.unique(st)} if len(st) else {},
           "resume": RS.resume(lignes),
           "ressemblance": [{k: l[k] for k in ("id", "simule", "reel", "bande", "verdict", "surete", "evenements")}
                            for l in lignes]}
    os.makedirs(RESULTATS, exist_ok=True)
    chemin = os.path.join(RESULTATS, f"enveloppes_{et}.json")
    with open(chemin, "w", encoding="utf-8") as f: json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(RESULTATS, f"ressemblance_enveloppes_{et}.md"), "w", encoding="utf-8") as f:
        f.write(RS.tableau_markdown(lignes, f"# Ressemblance : enveloppes {et}\n\nGraine {x.graine}, enveloppes "
                                            f"{x.enveloppes}, chauffe {x.chauffe} j, mesure {x.jours} j."))
    def v(i): return rs[i]["simule"] if i in rs and rs[i]["simule"] is not None else float("nan")
    print(f"epargne {v('taux_epargne'):.1f} % ; morts de faim {v('deces_faim'):.0f} / 100 000 ; inflation "
          f"{v('inflation'):.1f} % ; alimentation {v('part_alimentation'):.1f} % ; logement {v('part_logement'):.1f} % ; "
          f"transport {v('part_transport'):.1f} % ; fuites {res['fuites'] or 'aucune'} ; {res['s_par_jour']:.2f} s par jour")
    print(f"ecrit : {chemin}")


if __name__ == "__main__":
    main()
