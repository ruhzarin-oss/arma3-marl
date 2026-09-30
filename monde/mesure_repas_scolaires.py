"""( 30/09, HMT-177 ) Les repas scolaires sur une annee, pour le critere ecrit avant la mesure ( Plane HMT-177 ). Deux
bras : --repas oui ( d19.REPAS_SCOLAIRES vrai ) ou non ( eteint dans ce processus seulement ; les ecoles couvertes sont
calculees pareil ). Mesure, sur la fenetre qui suit la chauffe :
  1. les jours-eleves de faim grave ( faim > 2 rations au soir ) des eleves du primaire des lieux couverts ;
  2. les morts de faim ( ressemblance.py : evenements ) et celles des enfants de 6 a 12 ans ( domaine 1 ) ;
  3. le cout pour l Etat en drachmes par habitant et par an ;
  4. repas servis, manques, sans crochet, part des eleves couverts ; la ressemblance a la Grece ;
  5. ( rapporte, demande de Classes ) pour chaque enfant de 6 a 12 ans mort de faim : son ecole couverte ou non, les
     repas recus en tout et dans les 30 jours avant sa mort, ses jours de classe et ses absences de l annee, sa faim ;
     et les jours-eleves couverts au-dela de la borne d absence ( C.ABSENCE_FAIM : un eleve plus affame manque la classe,
     donc le repas ). Les repas par eleve sont comptes en enveloppant Monde.manger_dehors DANS CE PROCESSUS seulement
     ( l appel d origine est fait tel quel : le monde n en change pas ).
Lecture seule. Ecrit resultats/repas_<etiquette>.json et resultats/ressemblance_repas_<etiquette>.md.
   python -m monde.mesure_repas_scolaires --graine 177 --habitants 6375 --jours 365 --chauffe 40 --demographie grece --repas oui"""
import argparse, json, os, time
import numpy as np
from . import config as C, ressemblance as RS

RESULTATS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultats")
SEUIL_FAIM = 2.0                  # CHOIX ecrit avant la mesure : ~ 3 a 4 jours de jeune total


def main(argv=None):
    a = argparse.ArgumentParser(description="Les repas scolaires sur une annee ( HMT-177 ).")
    a.add_argument("--habitants", type=int, default=6375)
    a.add_argument("--jours", type=int, default=365)
    a.add_argument("--chauffe", type=int, default=40)
    a.add_argument("--graine", type=int, default=C.GRAINE)
    a.add_argument("--iles", default="Altis")
    a.add_argument("--demographie", default="grece")
    a.add_argument("--repas", choices=("oui", "non"), default="oui")
    a.add_argument("--etiquette", default=None)
    x = a.parse_args(argv)
    from . import monde as W
    from .pays import essais as E, pays as P, d19_education as ED, d01_population as D1
    ED.REPAS_SCOLAIRES = x.repas == "oui"
    recus = {}                             # habitant -> jours ou il a mange a l ecole ( fenetre mesuree seulement )
    fenetre = {"ouverte": False}
    if hasattr(W.Monde, "manger_dehors"):
        origine = W.Monde.manger_dehors

        def compter(self, ids, rations=1.0):
            r = origine(self, ids, rations)
            if fenetre["ouverte"]:
                for i in np.asarray(ids, np.int64).tolist(): recus.setdefault(i, []).append(self.jour)
            return r
        W.Monde.manger_dehors = compter
    et = x.etiquette or f"{x.repas}_g{x.graine}"
    t0 = time.perf_counter()
    kw = {"graine": x.graine, "echelle": x.habitants / 500.0, "iles": tuple(x.iles.split(","))}
    if x.demographie not in (None, "", "moteur"): kw["demographie"] = x.demographie
    w = W.Monde(**kw)
    p = P.installer(w, None)
    crochet = hasattr(w, "manger_dehors")
    print(f"monde : {w.table.n} habitants, {len(p.domaines)} domaines, repas {x.repas}, crochet {crochet} ; installation "
          f"{time.perf_counter() - t0:.0f} s", flush=True)
    E.jours(w, x.chauffe)
    R = ED._repas(ED._dom(p))
    r0 = dict(R); j0 = w.jour
    col = p.colonnes["habitant"]
    suivi = RS.Suivi(w, p)
    jours_faim = 0; jours_eleves = 0; jours_trop_affames = 0; parts = []
    fenetre["ouverte"] = True
    t1 = time.perf_counter()
    for k in range(x.jours):
        E.jours(w, 1); suivi.apres_jour(w, p)
        tb = w.table; n = tb.n; cv = R["couverts"]
        prim = np.nonzero((col["ed_cycle"][:n] == ED.PRIMAIRE) & (tb.vivant[:n] == 1) & (tb.domicile[:n] >= 0))[0]
        if cv is not None and len(prim):
            eux = prim[cv[tb.domicile[prim].astype(np.int64)]]
            jours_eleves += len(eux); jours_faim += int((tb.faim[eux] > SEUIL_FAIM).sum())
            jours_trop_affames += int((tb.faim[eux] > C.ABSENCE_FAIM).sum())
            parts.append(R["part"])
        if (k + 1) % 30 == 0: print(f"  jour {w.jour} ( {k + 1}/{x.jours} ) {time.perf_counter() - t1:.0f} s", flush=True)
    t_jours = time.perf_counter() - t1
    lignes = RS.mesurer(w, p, suivi=suivi, refs=RS.charger())
    rs = {l["id"]: l for l in lignes}
    ch = p.colonnes["habitant"]; n = w.table.n
    faim = D1.CAUSES.index("faim")
    dj = ch["deces_j"][:n].astype(np.int64); nj = ch["naissance_j"][:n].astype(np.int64)
    morts = (ch["cause_deces"][:n] == faim) & (dj > j0) & (dj <= w.jour)
    age = (dj - nj) / 365.0
    enfants = int((morts & (age >= 6.0) & (age < 12.0)).sum())
    cv = R["couverts"]; tb = w.table
    detail = []
    for i in np.nonzero(morts & (age >= 6.0) & (age < 12.0))[0].tolist():
        dom = int(tb.domicile[i]); jm = int(dj[i]); js = recus.get(i, [])
        detail.append({"habitant": i, "age": round(float(age[i]), 1), "jour_mort": jm,
                       "ecole_couverte": bool(cv is not None and dom >= 0 and cv[dom]),
                       "cycle": int(col["ed_cycle"][i]), "repas_recus": len(js),
                       "repas_30j": sum(1 for j in js if jm - 30 <= j <= jm),
                       "jours_classe_annee": int(col["ed_classes"][i]), "absences_annee": int(col["ed_absences"][i]),
                       "faim": round(float(tb.faim[i]), 1)})
    ans = x.jours / 365.0
    hab = float(w.table.vivant[:n].sum())
    paye = R["paye"] - r0["paye"]
    res = {"etiquette": et, "repas": x.repas, "crochet": crochet, "graine": x.graine, "habitants": int(n),
           "vivants_fin": hab, "jours": x.jours, "chauffe": x.chauffe, "demographie": x.demographie,
           "s_par_jour": t_jours / max(1, x.jours),
           "jours_eleves_faim_grave": jours_faim, "jours_eleves_couverts": jours_eleves, "seuil_faim": SEUIL_FAIM,
           "morts_faim_toutes": int(morts.sum()), "morts_faim_6_12": enfants, "enfants_morts": detail,
           "enfants_morts_en_ecole_couverte": sum(1 for e in detail if e["ecole_couverte"]),
           "enfants_morts_nourris_30j": sum(1 for e in detail if e["repas_30j"] > 0),
           "jours_eleves_au_dela_absence_faim": jours_trop_affames, "absence_faim": C.ABSENCE_FAIM,
           "deces_faim_ressemblance": rs.get("deces_faim", {}).get("evenements"),
           "cout_etat_dr_par_hab_an": paye / max(1.0, hab) / ans, "paye_dr": paye,
           "repas_servis": R["servis"] - r0["servis"], "repas_manques": R["manques"] - r0["manques"],
           "repas_sans_crochet": R["sans_crochet"] - r0["sans_crochet"], "jours_de_service": R["jours"] - r0["jours"],
           "part_eleves_couverts_moyenne": float(np.mean(parts)) if parts else None,
           "resume": RS.resume(lignes),
           "ressemblance": [{k: l[k] for k in ("id", "simule", "reel", "bande", "verdict", "surete", "evenements")}
                            for l in lignes]}
    os.makedirs(RESULTATS, exist_ok=True)
    chemin = os.path.join(RESULTATS, f"repas_{et}.json")
    with open(chemin, "w", encoding="utf-8") as f: json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(RESULTATS, f"ressemblance_repas_{et}.md"), "w", encoding="utf-8") as f:
        f.write(RS.tableau_markdown(lignes, f"# Ressemblance : repas scolaires {et}\n\nGraine {x.graine}, repas {x.repas}, "
                                            f"chauffe {x.chauffe} j, mesure {x.jours} j."))
    print(f"jours-eleves de faim grave {jours_faim} sur {jours_eleves} ; morts de faim {int(morts.sum())} dont 6-12 ans "
          f"{enfants} ; cout {res['cout_etat_dr_par_hab_an']:.2f} dr par habitant et par an ; repas {res['repas_servis']} "
          f"servis, {res['repas_manques']} manques, {res['repas_sans_crochet']} sans crochet ; {res['s_par_jour']:.2f} s par jour")
    print(f"ecrit : {chemin}")


if __name__ == "__main__":
    main()
