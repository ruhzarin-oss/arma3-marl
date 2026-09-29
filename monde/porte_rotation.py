"""PORTE DE LA ROTATION ( HMT-140 ( 1 ), 29/09, chef de projet ; criteres ecrits AVANT la mesure ; graines NEUVES 81, 82,
83 ). L Altis par defaut ( 28 domaines, echelle 20 : 10 000 habitants ; le monde nait le 15 juin ), une annee ( 365
jours ), deux fois par graine : la REGLE ( le travail par rotation et le plafond des licenciements collectifs, domaine
4 ) et le TEMOIN ( l ancienne regle : ROTATION_MAX_AN_J = 0, PLAFOND_COLLECTIF = False ). Criteres, sur chaque graine :
R1 controle positif : dans le temoin, la vague - au moins 100 licenciements economiques pour disponibilite epuisee en
   7 jours, quelque part entre les jours 90 et 110 ;
R2 plus de vague : avec la regle, le plus grand nombre de licenciements economiques ( tous motifs ) en 7 jours, sur
   l annee, ne depasse pas le tiers de celui du temoin ;
R3 la loi tenue : aucun employeur ne licencie pour disponibilite epuisee au-dela de son plafond collectif dans un mois
   civil ( son effectif lu le premier jour du mois ) ; aucun salarie ne depasse 270 jours de rotation dans l annee ;
R4 la rotation sert : des jours de rotation comptes ; l emploi salarie du prive, en moyenne sur l annee, au moins
   celui du temoin ;
R5 la conservation tient dans les deux bras.
CHOIX ecrit avant la mesure ( a trancher par Younes ) : pas de rotation sous 20 % de l activite de l employeur
( ROTATION_PART_MIN ) - la loi ( 3846/2010 art. 2 ) ne fixe aucun minimum, seulement neuf mois par annee civile et le
caractere collectif ; la raison : un employeur presque sans travail paierait presque rien pendant neuf mois a des
salaries qui, employes, n ont pas droit a l indemnite de chomage. Ce seuil ne sera pas regle apres la mesure.
Mesure d information ( question du chef de projet, pas un critere ) : les salaries de l hotellerie aux jours 250 et 340
( la saison suivante reembauche-t-elle vers avril et mai ? ).
   python -m monde.porte_rotation [ graines ]"""
import sys, time, collections
import numpy as np
from multiprocessing import get_context
from .pays import pays as P, essais as E, d04_travail as TV
GRAINES = (81, 82, 83)
JOURS = 365


def _effectifs(p, d, col, tb, g):
    """{ employeur du prive : ses salaries }, lu par la porte elle-meme."""
    n = tb.n; paires, eff = {}, collections.Counter()
    for i in np.nonzero((col["tr_statut"][:n] == TV.SALARIE) & (tb.vivant[:n] == 1) & (tb.travail[:n] >= 0))[0].tolist():
        c = (int(tb.travail[i]), int(tb.role[i]))
        if c not in paires:
            x = TV._payeur_de(p, d, tb.par_n[c[0]].id, TV.PO.ROLES[c[1]] if c[1] >= 0 else None)
            paires[c] = None if (x is None or x is g) else TV._cle_payeur(x)
        if paires[c] is not None: eff[paires[c]] += 1
    return dict(eff)


def _jouer(args):
    graine, regle = args
    t0 = time.time()
    TV.ROTATION_MAX_AN_J = 9 * TV.MOIS_J if regle else 0; TV.PLAFOND_COLLECTIF = bool(regle)   # chaque bras pose sa regle
    w, _ = E.monde([nom for nom, mod, _ in P.DOMAINES], graine=graine, echelle=20.0)
    p = w.pays; d = p.domaine("travail"); col = p.colonnes["habitant"]; tb = w.table; g = w.gouv
    licencies = collections.Counter()                 # jour -> licenciements economiques ( tous motifs )
    vague = collections.Counter()                     # jour -> pour disponibilite epuisee
    par_mois = collections.Counter()                  # ( mois, employeur ) -> licenciements pour disponibilite epuisee
    l0 = TV.licencier_economique

    def licencier(p_, h, motif="economique"):
        if h.travail is not None and col["tr_statut"][h.id] in TV.PAYES_A_L_HEURE:
            j = int(p_.w.jour); licencies[j] += 1
            if motif == "disponibilite_epuisee":
                vague[j] += 1
                x = TV._payeur(p_, d, h)
                if x is not None: par_mois[(p_.socle.calendrier.date(p_.w.pas).strftime("%Y-%m"), TV._cle_payeur(x))] += 1
        return l0(p_, h, motif)
    TV.licencier_economique = licencier
    effectifs = {}; prive = []; hotellerie = {}; rot_max = 0; jr = [0.0, 0.0]
    J = p.socle.journal
    j0 = int(w.jour); vu = j0 - 1
    while int(w.jour) < j0 + JOURS:
        date = p.socle.calendrier.date(w.pas); m = date.strftime("%Y-%m")
        if m not in effectifs and (vu == j0 - 1 or (date.day == 1 and w.heure > 6.2)):   # apres 6 h 10, comme le domaine 4
            effectifs[m] = _effectifs(p, d, col, tb, g)
        if int(w.jour) != vu:
            vu = int(w.jour); n = tb.n
            sal = np.nonzero((col["tr_statut"][:n] == TV.SALARIE) & (tb.vivant[:n] == 1) & (tb.travail[:n] >= 0))[0]
            paires, eff = {}, collections.Counter()
            for i in sal.tolist():
                c = (int(tb.travail[i]), int(tb.role[i]))
                if c not in paires:
                    x = TV._payeur_de(p, d, tb.par_n[c[0]].id, TV.PO.ROLES[c[1]] if c[1] >= 0 else None)
                    paires[c] = None if (x is None or x is g) else TV._cle_payeur(x)
                if paires[c] is not None: eff[paires[c]] += 1
            prive.append(sum(eff.values()))
            if vu - j0 in (250, 340):
                hotellerie[vu - j0] = int(sum(1 for i in sal.tolist() if TV.PO.ROLES[int(tb.role[i])] == "hotellerie"))
            if "tr_rotation_an" in col: rot_max = max(rot_max, int(col["tr_rotation_an"][:n].max()))
        w.pas_suivant()
        v = (J.comptes.get("jours_en_rotation") or (0, 0.0))[1]
        jr[0] += v - jr[1] if v >= jr[1] else v; jr[1] = v
    TV.licencier_economique = l0
    semaine = lambda c, a=0, b=10 ** 9: max([sum(c.get(j0 + x + k, 0) for k in range(7)) for x in range(JOURS) if a <= x <= b] or [0])
    depasse = [(m, k, n_, effectifs.get(m, {}).get(k, 0)) for (m, k), n_ in par_mois.items()
               if n_ > TV.plafond_collectif(effectifs.get(m, {}).get(k, 0))]
    return {"graine": graine, "regle": regle, "vague_90_110": semaine(vague, 90 - 6, 110), "pire_semaine": semaine(licencies),
            "licencies_an": int(sum(licencies.values())), "plafond_depasse": depasse[:5], "n_depasse": len(depasse),
            "rotation_max_j": rot_max, "jours_en_rotation": round(jr[0]), "prive_moyen": round(float(np.mean(prive)), 1),
            "prive_j0": prive[0], "prive_fin": prive[-1], "hotellerie": hotellerie,
            "conservation": bool(p.socle.conservation.tenue()[0]), "secondes": round(time.time() - t0)}


def main():
    graines = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else list(GRAINES)
    t0 = time.time(); ok = {}
    with get_context("spawn").Pool(2, maxtasksperchild=1) as pool:
        rs = pool.map(_jouer, [(g, r) for g in graines for r in (True, False)])
    for r in rs: print("  ", r, flush=True)
    for g in graines:
        R = next(r for r in rs if r["graine"] == g and r["regle"]); T = next(r for r in rs if r["graine"] == g and not r["regle"])
        ok[f"R1 graine {g} : controle positif, le temoin fait la vague ( {T['vague_90_110']} en 7 jours, jours 90 a 110 )"] = T["vague_90_110"] >= 100
        ok[f"R2 graine {g} : plus de vague ( pire semaine {R['pire_semaine']} contre {T['pire_semaine']} )"] = R["pire_semaine"] * 3 <= T["pire_semaine"]
        ok[f"R3 graine {g} : plafond collectif tenu ( {R['n_depasse']} depassements ) ; rotation au plus 270 jours ( {R['rotation_max_j']} )"] = (
            R["n_depasse"] == 0 and R["rotation_max_j"] <= TV.ROTATION_MAX_AN_J)
        ok[f"R4 graine {g} : la rotation sert ( {R['jours_en_rotation']} jours ) ; emploi prive moyen {R['prive_moyen']} contre {T['prive_moyen']}"] = (
            R["jours_en_rotation"] > 0 and R["prive_moyen"] >= T["prive_moyen"])
        ok[f"R5 graine {g} : conservation"] = R["conservation"] and T["conservation"]
        print(f"   hotellerie ( information ) graine {g} : regle {R['hotellerie']}, temoin {T['hotellerie']}", flush=True)
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DE LA ROTATION : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
