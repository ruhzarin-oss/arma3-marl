"""PORTE DE L ARMEE DU BUDGET ( d25, 29/09, chef de projet et Classes ; criteres ecrits AVANT la mesure ; graines NEUVES
111, 112, 113 ). Deux mondes par graine, 28 domaines, une annee ( le monde nait le 15 juin ) : la REGLE, le monde grec
( demographie grece, echelle 12,75 : ~ 10 000 habitants ; le recensement de Classes separe la carriere, au niveau que
le budget paie, et les conscrits, table.recensement["conscrit"] ), et le CONTROLE POSITIF, le monde E1 ( Altis x 20 :
~ 10 000 habitants, 12 % de militaires a sa naissance ; sans recensement, d25 y garde son comportement, identique au
bit ). La bande : grece.json part_militaires ( OTAN 1,07 %, bande 0,8 a 1,45 %, effectifs de l armee ar_rang ).
A1 la carriere du jour 1, nee du recensement : entre l effectif paye - 2 et ceil( MARGE_REDUCTION x paye ), sans aucun
   depart au plan de departs ce jour-la ; controle positif : dans E1, la carriere du jour 1 depasse 1,8 x paye.
A2 l annee : la part des militaires ( ar_rang, vivants ) reste dans [ 0,8 % ; 1,45 % ] les 365 jours ; controle
   positif : dans E1, son maximum depasse 1,45 %.
A3 le contingent de l installation : aucun non-etudiant de 21 ans ou plus sans formation militaire n a de jour d appel
   a l installation ; controle positif : dans E1, au moins 20.
A4 E1 intact : la porte des domaines ( les mondes E1 des 27 domaines ) FRANCHIE contre les references du tronc
   ( commande a part : python -m monde.porte_domaines --comparer <references des 27 domaines du tronc> ).
A5 l emploi des 20-64 ans a l installation ( jour 0, avant le premier pas ) dans la regle ( statuts du domaine 4 : en
   emploi, armee comprise ; le metier ne suffit pas, le chomeur du recensement porte celui qu il cherche ) a 3 points de
   69,3 % ( la cible de P4 ) ; la conservation tient dans les deux mondes. ( Au jour 1, le tourisme a deja embauche ~ 430
   chomeurs pour ses hotels du 15 juin, sur le tronc aussi : un transitoire d installation hors de l armee, rapporte en
   information. )
A6 le flux : les incorporations de l annee, hors contingent de l installation et conscrits du recensement, font entre
   0,24 % et 0,40 % de la population moyenne ( cible 0,32 % ) ; controle positif : sans les anciens etudiants ( les
   sursitaires appeles a leur sortie ), elles font moins de 0,24 %.
Information ( pas un critere ) : l appel des 60 premiers jours, les stocks de carriere et de conscrits jour par jour
( jours 1, 90, 180, 270, 365 ), les departs, le chomage des 20-64 ans aux jours 0, 1 et 365.
   python -m monde.porte_armee_budget [ graines ]"""
import sys, time, math
import numpy as np
from multiprocessing import get_context
from .pays import pays as P, essais as E, d25_armee as A, d04_travail as TR, d01_population as POP
GRAINES = (111, 112, 113)
JOURS = 365
BANDE = (0.008, 0.0145)
POINTS = (1, 90, 180, 270, 365)


def _emploi(p, v):
    """L emploi des 20-64 ans et leur chomage, par les statuts du domaine 4."""
    tb = p.w.table; n = tb.n; col = p.colonnes["habitant"]
    age = (p.jour - col["naissance_j"][:n]) / POP.JOURS_AN
    m = v & (age >= 20) & (age < 65); st = col["tr_statut"][:n]
    emp = np.isin(st, TR.EN_EMPLOI); cho = st == TR.CHOMEUR
    return float(emp[m].mean()), float(cho[m].sum() / max(1, cho[m].sum() + emp[m].sum()))


def _jouer(args):
    graine, grec = args
    t0 = time.time()
    w, _ = E.monde([nom for nom, mod, _ in P.DOMAINES], graine=graine, echelle=12.75 if grec else 20.0,
                   demographie="grece" if grec else None)
    p = w.pays; tb = w.table; n = tb.n; d = A._dom(p); col = p.colonnes["habitant"]
    viv = tb.vivant[:n] == 1
    age = (p.jour - col["naissance_j"][:n]) / POP.JOURS_AN
    fm = (col["tr_qualifs"][:n] & TR.BIT["formation_militaire"]) > 0
    hom = viv & (col["sexe"][:n] == POP.HOMME)
    etud = col["tr_statut"][:n] == TR.ETUDIANT
    ap = col["ar_appel"][:n]
    a3 = int((hom & ~etud & (age >= A.AGE_SERVI) & ~fm & (ap >= 0)).sum())
    contingent = set(np.nonzero(ap >= 0)[0].tolist()) | {i for (_, i, _, _) in d.incorpores}   # l appel de l installation
    etudiants = set(np.nonzero(hom & etud)[0].tolist())
    appel_60 = len(contingent)
    em0, ch0 = _emploi(p, viv)
    parts, pop, serie = [], [], {}
    j0 = int(w.jour); vu = j0; jour1 = None; ch365 = None
    while int(w.jour) < j0 + JOURS:
        w.pas_suivant()
        if int(w.jour) == vu: continue
        vu = int(w.jour); fini = vu - j0; n = tb.n
        v = tb.vivant[:n] == 1; nv = int(v.sum()); pop.append(nv)
        rang = col["ar_rang"][:n]
        parts.append(float((v & (rang >= 0)).sum()) / nv)
        if fini in POINTS:
            rows = A._lignes(d); Ef = d.eff
            serie[fini] = (int((Ef["conscrit"][rows] == 0).sum()), int((Ef["conscrit"][rows] == 1).sum()))
        if fini == 1:
            rows = A._lignes(d); Ef = d.eff
            paye = float((d.vise or A.effectifs_vises(p))["carriere"])
            em, ch = _emploi(p, v)
            jour1 = {"carriere": int((Ef["conscrit"][rows] == 0).sum()), "paye": round(paye, 2), "departs": int(d.departs),
                     "emploi_20_64": round(em, 4), "chomage_20_64": round(ch, 4)}
        if fini == JOURS:
            ch365 = round(_emploi(p, v)[1], 4)
    inc = [i for (_, i, _, _) in d.incorpores if i not in contingent]
    etu = [i for i in inc if i in etudiants]
    m = float(np.mean(pop))
    return {"graine": graine, "grec": grec, "jour1": jour1, "emploi_20_64_j0": round(em0, 4), "chomage_20_64_j0": round(ch0, 4), "part_min": round(min(parts), 5), "part_max": round(max(parts), 5),
            "jours_hors_bande": int(sum(1 for x in parts if not BANDE[0] <= x <= BANDE[1])), "a3": a3, "appel_60": appel_60,
            "conscrits_recenses": int(getattr(d, "conscrits_recenses", 0) or 0), "sursitaires": int(getattr(d, "sursitaires", 0) or 0),
            "flux": round(len(inc) / m, 5), "flux_sans_etudiants": round((len(inc) - len(etu)) / m, 5), "incorpores": len(inc),
            "anciens_etudiants": len(etu), "serie": serie, "departs_an": int(d.departs), "chomage_20_64_j365": ch365,
            "conservation": bool(p.socle.conservation.tenue()[0]), "secondes": round(time.time() - t0)}


def main():
    graines = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else list(GRAINES)
    t0 = time.time(); ok = {}
    with get_context("spawn").Pool(2, maxtasksperchild=1) as pool:
        rs = pool.map(_jouer, [(g, grec) for g in graines for grec in (True, False)])
    for r in rs: print("  ", r, flush=True)
    for g in graines:
        R = next(r for r in rs if r["graine"] == g and r["grec"]); T = next(r for r in rs if r["graine"] == g and not r["grec"])
        j, t = R["jour1"], T["jour1"]
        ok[f"A1 graine {g} : carriere du jour 1 {j['carriere']} pour {j['paye']} payes ( de paye - 2 a {math.ceil(A.MARGE_REDUCTION * j['paye'])} ), departs {j['departs']}"] = (
            j["paye"] - 2 <= j["carriere"] <= math.ceil(A.MARGE_REDUCTION * j["paye"]) and j["departs"] == 0)
        ok[f"A1 graine {g} : controle positif, E1 {t['carriere']} pour {t['paye']} payes ( plus de 1,8 x )"] = t["carriere"] > 1.8 * t["paye"]
        ok[f"A2 graine {g} : part des militaires de {R['part_min']:.3%} a {R['part_max']:.3%}, {R['jours_hors_bande']} jours hors de [ 0,8 % ; 1,45 % ]"] = R["jours_hors_bande"] == 0
        ok[f"A2 graine {g} : controle positif, E1 au plus {T['part_max']:.2%} ( plus de 1,45 % )"] = T["part_max"] > BANDE[1]
        ok[f"A3 graine {g} : {R['a3']} non-etudiants de 21 ans ou plus sans formation appeles a l installation ; E1 {T['a3']} ( au moins 20 )"] = R["a3"] == 0 and T["a3"] >= 20
        ok[f"A5 graine {g} : emploi des 20-64 ans a l installation {R['emploi_20_64_j0']:.1%} ( 69,3 % a 3 points ) ; conservation"] = (
            abs(R["emploi_20_64_j0"] - 0.693) <= 0.03 and R["conservation"] and T["conservation"])
        ok[f"A6 graine {g} : flux {R['flux']:.3%} de la population ( 0,24 a 0,40 % ; {R['incorpores']} incorpores dont {R['anciens_etudiants']} anciens etudiants )"] = 0.0024 <= R["flux"] <= 0.0040
        ok[f"A6 graine {g} : controle positif, sans les anciens etudiants {R['flux_sans_etudiants']:.3%} ( moins de 0,24 % )"] = R["flux_sans_etudiants"] < 0.0024
        print(f"   information graine {g} : appel des 60 jours {R['appel_60']} ( E1 {T['appel_60']} ), conscrits du recensement {R['conscrits_recenses']}, "
              f"sursitaires {R['sursitaires']}, carriere / conscrits aux jours {R['serie']}, departs {R['departs_an']}, "
              f"chomage des 20-64 ans {R['chomage_20_64_j0']:.1%} ( jour 0 ) -> {j['chomage_20_64']:.1%} ( jour 1 ) -> {R['chomage_20_64_j365']:.1%} ( jour 365 )", flush=True)
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DE L ARMEE DU BUDGET : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s ) ; A4 a part ( porte des domaines )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
