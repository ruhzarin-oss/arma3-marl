"""PORTES DE LA POPULATION COPIEE SUR LA GRECE ( `Monde( demographie="grece" )`, monde/demographie_grece.py ).

Seuils ecrits le 27/09 AVANT la premiere mesure. Chaque porte a son controle positif ( elle refuse la population par
defaut, ou voit un defaut pose expres ) et, la ou c est possible, un falsificateur.
  P1 defaut identique au bit : portes.sh ( les references des domaines ) ; ici en plus, l empreinte de la population
     par defaut ( toutes les colonnes des habitants et des menages ) contre celle de la base f13be95.
  P2 pyramide : chaque groupe de 5 ans a 1 point de sa part, 0-14, 15-64 et 65 ans et plus a 1 point, rapport hommes /
     femmes a 0,03 ; le domaine 1 garde la pyramide.
  P3 menages : taille moyenne a 0,1 de 2,4, chaque taille ( 1 a 5, 6 et plus ) a 3 points, aucun mineur sans adulte ; le
     domaine 1 garde les familles ( sexe, conjoint, mere, pere, menages ) et n y voit aucune incoherence.
  P4 activite : emploi des 20-64 ans a 3 points de 69,3 %, militaires de 1,0 a 1,8 % de la population, petits enfants
     presents ( tous les 0-5 ans ) ; le domaine 4 mesure le meme emploi a 3 points.
  P5 vivable : les 28 domaines, ~10 000 habitants, 30 jours : conservation tenue ( argent, biens, objets ), argent hors
     du grand livre exterieur seulement, aucune exception, au moins 97 % des vivants du depart ; la faim ( part des
     menages habites sans repas, moyenne des 30 soirs ) au plus celle du monde par defaut au meme nombre de
     travailleurs, plus 2 points.
  P6 determinisme : deux creations de meme graine sont identiques ( toutes les colonnes ) ; une autre graine differe.
  P7 cout : creation puis installation des 28 domaines a ~10 000 et ~100 000 habitants ; le cout par habitant a 100 000
     au plus 1,5 fois celui a 10 000.
    python -m monde.porte_population_grece [ P1 P2 ... P7 ]"""
import hashlib, sys, time, traceback
import numpy as np
from . import config as C, monde as W, population as P, demographie_grece as R

ECHELLE_10K = 13.0            # ~10 200 habitants en mode grec
ECHELLE_100K = 130.0          # ~102 000
GRAINE = 11
# l empreinte de la population par defaut ( graine config.GRAINE, echelle 1 ) mesuree sur la base f13be95, avant toute
# modification de ce chantier
EMPREINTE_DEFAUT_F13BE95 = "6482559b883ff86bf0ddd7ea3769732499b277a5a58205656f5148cbce07a22f"
TRAVAILLEURS = [P.CODE_ROLE[r] for r in P.ROLES if P.TRAVAIL[r][0] and r not in ("enfant", "etudiant")]
MILITAIRES = [P.CODE_ROLE[r] for r in ("soldat", "officier")]


# ================================================================== les mesures ( fonctions pures sur des tableaux )
def mesure_pyramide(age, sexe):
    """Parts des groupes de 5 ans ( 0-4 ... 100 et plus ), des grands groupes, et le rapport hommes / femmes."""
    age = np.asarray(age); sexe = np.asarray(sexe)
    g = np.minimum(age // 5, len(R.GROUPES) - 1).astype(np.int64)
    parts = np.bincount(g, minlength=len(R.GROUPES)) / max(1, age.size)
    return {"groupes": parts, "0-14": float((age < 15).mean()), "15-64": float(((age >= 15) & (age < 65)).mean()),
            "65+": float((age >= 65).mean()),
            "hommes_femmes": float((sexe == R.HOMME).sum() / max(1, (sexe == R.FEMME).sum()))}


def cible_pyramide():
    tot = np.array(R.PYRAMIDE[R.HOMME]) + np.array(R.PYRAMIDE[R.FEMME])
    g = tot / tot.sum()
    return {"groupes": g, "0-14": float(g[:3].sum()), "15-64": float(g[3:13].sum()), "65+": float(g[13:].sum()),
            "hommes_femmes": sum(R.PYRAMIDE[R.HOMME]) / sum(R.PYRAMIDE[R.FEMME])}


def ecarts_pyramide(m):
    c = cible_pyramide()
    return {"groupe_max_points": 100 * float(np.abs(m["groupes"] - c["groupes"]).max()),
            "grands_groupes_max_points": 100 * max(abs(m[k] - c[k]) for k in ("0-14", "15-64", "65+")),
            "hommes_femmes": abs(m["hommes_femmes"] - c["hommes_femmes"])}


def pyramide_ok(e):
    return e["groupe_max_points"] <= 1.0 and e["grands_groupes_max_points"] <= 1.0 and e["hommes_femmes"] <= 0.03


def mesure_menages(age, menage):
    """Tailles ( 1 a 5, 6 et plus ), taille moyenne, et le nombre de menages ou vivent des mineurs sans adulte."""
    age = np.asarray(age); menage = np.asarray(menage)
    M = int(menage.max()) + 1
    taille = np.bincount(menage, minlength=M)
    habites = taille > 0
    t = taille[habites]
    dist = np.bincount(np.minimum(t, 6), minlength=7)[1:] / t.size
    adultes = np.bincount(menage[age >= 18], minlength=M)[habites]
    mineurs = np.bincount(menage[age < 18], minlength=M)[habites]
    return {"tailles": dist, "moyenne": float(t.mean()), "mineurs_sans_adulte": int(((mineurs > 0) & (adultes == 0)).sum()),
            "menages": int(t.size)}


def menages_ok(m):
    ecart = 100 * float(np.abs(m["tailles"] - np.array(R.TAILLES)).max())
    return abs(m["moyenne"] - R.TAILLE_MOYENNE) <= 0.1 and ecart <= 3.0 and m["mineurs_sans_adulte"] == 0, ecart


def types_menages(age, menage, role, mere):
    """Les types d EU-SILC ( ilc_lvph04 ) : adultes et enfants a charge ( moins de 18 ans, ou 18-24 ans inactif qui vit
    avec sa mere ). Une mesure rapportee, pas une porte."""
    age = np.asarray(age); menage = np.asarray(menage); role = np.asarray(role); mere = np.asarray(mere)
    M = int(menage.max()) + 1
    inactif = np.isin(role, [P.CODE_ROLE[r] for r in ("etudiant", "inactif", "chomeur")])
    chez_mere = (mere >= 0) & (menage[np.maximum(mere, 0)] == menage)
    dep = (age < 18) | ((age < 25) & inactif & chez_mere)
    na = np.bincount(menage[~dep], minlength=M); nd = np.bincount(menage[dep], minlength=M)
    v = np.bincount(menage[~dep & (age >= 65)], minlength=M)
    hab = (na + nd) > 0
    na, nd, v = na[hab], nd[hab], v[hab]
    return {"un_adulte": float(((na == 1) & (nd == 0)).mean()), "un_adulte_65_plus": float(((na == 1) & (nd == 0) & (v == 1)).mean()),
            "un_adulte_enfants": float(((na == 1) & (nd > 0)).mean()), "deux_adultes": float(((na == 2) & (nd == 0)).mean()),
            "deux_adultes_65_plus": float(((na == 2) & (nd == 0) & (v >= 1)).mean()),
            "deux_adultes_1_enfant": float(((na == 2) & (nd == 1)).mean()),
            "deux_adultes_2_enfants": float(((na == 2) & (nd == 2)).mean()),
            "deux_adultes_3_enfants_et_plus": float(((na == 2) & (nd >= 3)).mean()),
            "trois_adultes_et_plus": float(((na >= 3) & (nd == 0)).mean()),
            "trois_adultes_enfants": float(((na >= 3) & (nd > 0)).mean())}


def mesure_activite(age, role):
    """Emploi des 20-64 ans ( metiers avec un lieu de travail, armee comprise ), part des militaires, petits enfants."""
    age = np.asarray(age); role = np.asarray(role)
    m = (age >= 20) & (age < 65)
    trav = np.isin(role, TRAVAILLEURS)
    cho = role == P.CODE_ROLE["chomeur"]
    petits = role == P.CODE_ROLE["petit_enfant"]
    return {"emploi_20_64": float(trav[m].mean()) if m.any() else 0.0,
            "militaires": float(np.isin(role, MILITAIRES).mean()),
            "petits_enfants": int(petits.sum()), "zero_cinq_ans": int((age < 6).sum()),
            "chomage_20_64": float(cho[m].sum() / max(1, cho[m].sum() + trav[m].sum()))}


def activite_ok(a):
    return (abs(a["emploi_20_64"] - R.CIBLE_EMPLOI_20_64) <= 0.03 and 0.010 <= a["militaires"] <= 0.018
            and a["petits_enfants"] > 0 and a["petits_enfants"] == a["zero_cinq_ans"])


def secteurs(role):
    """La structure de l emploi par secteur : celle du monde ( metiers avec un lieu ) et celle de la Grece ( NACE )."""
    role = np.asarray(role)
    monde = {}
    for r, s in R.SECTEUR_DU_METIER.items():
        if r in P.CODE_ROLE: monde[s] = monde.get(s, 0) + int((role == P.CODE_ROLE[r]).sum())
    tot = sum(monde.values())
    nace = sum(v for k, v in R.EMPLOI_NACE.items() if k != "NRP")
    grece = {s: sum(R.EMPLOI_NACE[k] for k in ks) / nace for s, ks in R.SECTEURS.items()}
    return {s: (monde.get(s, 0) / max(1, tot), grece[s]) for s in R.SECTEURS}


def empreinte(w):
    """L empreinte de la population d un monde : toutes les colonnes des habitants et des menages ( et le recensement
    s il y en a un )."""
    t = w.table; n = t.n; mt = t.menages
    h = hashlib.sha256()
    for nom in sorted(P.Table.CHAMPS): h.update(nom.encode()); h.update(np.ascontiguousarray(getattr(t, nom)[:n]).tobytes())
    for nom in sorted(P.TableMenages.CHAMPS): h.update(nom.encode()); h.update(np.ascontiguousarray(getattr(mt, nom)[:mt.n]).tobytes())
    rec = getattr(t, "recensement", None)
    if rec is not None:
        for k in sorted(rec):
            if k != "demographie": h.update(k.encode()); h.update(np.ascontiguousarray(rec[k]).tobytes())
    return h.hexdigest()


def _grec(echelle=ECHELLE_10K, graine=GRAINE):
    return W.Monde(graine=graine, echelle=echelle, demographie="grece")


def _sexe_d01(w, p):
    return p.colonnes["habitant"]["sexe"][:w.table.n]


# ================================================================== les portes
def porte_p1():
    """L empreinte de la population par defaut est celle de la base. Controle positif : l empreinte voit un seul octet
    change ( un age de 0,1 an ), et la population grecque a une autre empreinte."""
    w = W.Monde()
    e = empreinte(w)
    w.table.age[0] += 0.1
    voit = empreinte(w) != e
    w.table.age[0] -= 0.1
    autre = empreinte(W.Monde(demographie="grece")) != e
    ok = e == EMPREINTE_DEFAUT_F13BE95 and voit and autre
    return ok, (f"empreinte par defaut {e[:16]} ( base f13be95 : {EMPREINTE_DEFAUT_F13BE95[:16]} ) ; controle positif : "
                f"un age change {'vu' if voit else 'NON VU'}, population grecque {'differente' if autre else 'IDENTIQUE'}")


def porte_p2():
    from .pays import essais as T
    w = _grec()
    t = w.table; n = t.n
    m = mesure_pyramide(t.age[:n], t.recensement["sexe"])
    e = ecarts_pyramide(m)
    # le domaine 1 garde la pyramide ( les ages prennent leur jour dans l annee, les sexes sont lus )
    w1, p1 = T.monde(["population"], graine=GRAINE, echelle=ECHELLE_10K, demographie="grece")
    e1 = ecarts_pyramide(mesure_pyramide(w1.table.age[:w1.table.n], _sexe_d01(w1, p1)))
    # controle positif : la population par defaut ( sexes du domaine 1 ). Falsificateurs : les 0-4 ans vieillis de 5 ans
    # ( un groupe vide ) ; 5 % des femmes inscrites hommes. ( 27/09 : le premier falsificateur, 3 % des habitants
    # vieillis de 20 ans, ne deplacait que 0,24 point : sous le seuil, il ne pouvait pas etre vu. Remplace. )
    w0, p0 = T.monde(["population"], graine=GRAINE, echelle=1.0)
    e0 = ecarts_pyramide(mesure_pyramide(w0.table.age[:w0.table.n], _sexe_d01(w0, p0)))
    age_f = t.age[:n].copy(); age_f[age_f < 5] += 5
    ef = ecarts_pyramide(mesure_pyramide(age_f, t.recensement["sexe"]))
    sexe_f = t.recensement["sexe"].copy(); f = np.nonzero(sexe_f == R.FEMME)[0]; sexe_f[f[::20]] = R.HOMME
    es = ecarts_pyramide(mesure_pyramide(t.age[:n], sexe_f))
    ok = pyramide_ok(e) and pyramide_ok(e1) and not pyramide_ok(e0) and not pyramide_ok(ef) and not pyramide_ok(es)
    f = lambda x: (f"groupe {x['groupe_max_points']:.2f} pt, grands groupes {x['grands_groupes_max_points']:.2f} pt, "
                   f"H/F {x['hommes_femmes']:.3f}")
    return ok, (f"{n} habitants : ecarts max {f(e)} ; parts 0-14 {m['0-14']:.1%}, 15-64 {m['15-64']:.1%}, 65+ "
                f"{m['65+']:.1%}, H/F {m['hommes_femmes']:.3f} ; apres le domaine 1 : {f(e1)} ; controle positif ( defaut ) : "
                f"{f(e0)} -> {'refuse' if not pyramide_ok(e0) else 'ACCEPTE'} ; falsificateurs : 0-4 ans vieillis de 5 ans "
                f"{f(ef)} -> {'refuse' if not pyramide_ok(ef) else 'ACCEPTE'}, 5 % des femmes inscrites hommes {f(es)} -> "
                f"{'refuse' if not pyramide_ok(es) else 'ACCEPTE'}")


def porte_p3():
    from .pays import essais as T, d01_population as D1
    w = _grec()
    t = w.table; n = t.n; rec = t.recensement
    m = mesure_menages(t.age[:n], t.menage[:n])
    ok_m, ecart = menages_ok(m)
    ty = types_menages(t.age[:n], t.menage[:n], t.role[:n], rec["mere"])
    # le domaine 1 garde les familles
    w1, p1 = T.monde(["population"], graine=GRAINE, echelle=ECHELLE_10K, demographie="grece")
    col = p1.colonnes["habitant"]; t1 = w1.table
    garde = (all(np.array_equal(col[k][:n], rec[k]) for k in ("sexe", "conjoint", "mere", "pere"))
             and np.array_equal(t1.menage[:n], t.menage[:n]))
    anomalies = D1.anomalies_familles(p1)
    m1 = mesure_menages(t1.age[:n], t1.menage[:n])
    # controle positif : la population par defaut ; falsificateur : un mineur seul dans un menage neuf
    w0 = W.Monde(graine=GRAINE)
    m0 = mesure_menages(w0.table.age[:w0.table.n], w0.table.menage[:w0.table.n])
    mg_f = t.menage[:n].copy(); i = int(np.nonzero(t.age[:n] < 10)[0][0]); mg_f[i] = mg_f.max() + 1
    mf = mesure_menages(t.age[:n], mg_f)
    ok = ok_m and garde and not anomalies and m1["mineurs_sans_adulte"] == 0 and not menages_ok(m0)[0] \
        and mf["mineurs_sans_adulte"] == 1
    tailles = " / ".join(f"{100 * x:.1f}" for x in m["tailles"])
    cibles = " / ".join(f"{100 * x:.1f}" for x in R.TAILLES)
    types = ", ".join(f"{k} {100 * v:.1f} ( {100 * R.TYPES[k]:.1f} )" for k, v in ty.items())
    return ok, (f"{m['menages']} menages : tailles 1 a 6+ {tailles} % ( cible {cibles} ), ecart max {ecart:.1f} pt ; "
                f"moyenne {m['moyenne']:.2f} ( cible {R.TAILLE_MOYENNE} ) ; mineurs sans adulte {m['mineurs_sans_adulte']} ; "
                f"domaine 1 : familles {'gardees' if garde else 'CHANGEES'}, incoherences {len(anomalies)} ; controle positif "
                f"( defaut ) : moyenne {m0['moyenne']:.2f}, tailles {' / '.join(f'{100 * x:.0f}' for x in m0['tailles'])} -> "
                f"{'refuse' if not menages_ok(m0)[0] else 'ACCEPTE'} ; falsificateur ( un mineur seul ) : vu "
                f"{mf['mineurs_sans_adulte']} ; types EU-SILC ( cible ) : {types}")


def porte_p4():
    from .pays import essais as T, d04_travail as D4
    w = _grec()
    t = w.table; n = t.n
    a = mesure_activite(t.age[:n], t.role[:n])
    wt, pt = T.monde(["travail"], graine=GRAINE, echelle=ECHELLE_10K, demographie="grece")
    d4 = D4.mesurer_emploi(pt)
    ok4 = abs(d4["taux_emploi"] - R.CIBLE_EMPLOI_20_64) <= 0.03
    # controle positif : la population par defaut ; falsificateur : 10 % des travailleurs de 20-64 ans rendus inactifs
    w0 = W.Monde(graine=GRAINE)
    a0 = mesure_activite(w0.table.age[:w0.table.n], w0.table.role[:w0.table.n])
    ro = t.role[:n].copy()
    k = np.nonzero(np.isin(ro, TRAVAILLEURS) & (t.age[:n] >= 20) & (t.age[:n] < 65))[0]
    ro[k[::10]] = P.CODE_ROLE["inactif"]
    af = mesure_activite(t.age[:n], ro)
    ok = activite_ok(a) and ok4 and not activite_ok(a0) and not activite_ok(af)
    sec = secteurs(t.role[:n])
    s = ", ".join(f"{k} {100 * m:.1f} % ( Grece {100 * g:.1f} % )" for k, (m, g) in sec.items())
    return ok, (f"emploi 20-64 ans {a['emploi_20_64']:.1%} ( cible {R.CIBLE_EMPLOI_20_64:.1%} ), chomage {a['chomage_20_64']:.1%}, "
                f"militaires {a['militaires']:.2%}, petits enfants {a['petits_enfants']} ( 0-5 ans : {a['zero_cinq_ans']} ) ; "
                f"domaine 4 : emploi {d4['taux_emploi']:.1%} ( hommes {d4['taux_hommes']:.1%}, femmes {d4['taux_femmes']:.1%} ), "
                f"chomage {d4['taux_chomage']:.1%}, statuts {d4['statuts']} ; controle positif ( defaut ) : emploi "
                f"{a0['emploi_20_64']:.1%}, militaires {a0['militaires']:.1%}, petits enfants {a0['petits_enfants']} -> "
                f"{'refuse' if not activite_ok(a0) else 'ACCEPTE'} ; falsificateur ( 10 % rendus inactifs ) : emploi "
                f"{af['emploi_20_64']:.1%} -> {'refuse' if not activite_ok(af) else 'ACCEPTE'} ; secteurs : {s}")


def _vivre(demographie, echelle, jours=30):
    """Les 28 domaines, `jours` jours : ( faim de chaque soir, conservation, argent hors livre, vivants, exception )."""
    from .pays import essais as T, pays as PA
    from .socle import registre as RG
    w, p = T.monde([nom for nom, _, _ in PA.DOMAINES], graine=GRAINE, echelle=echelle, demographie=demographie)
    L = p.socle.livre
    net0, ext0, monnaie0 = L.net_par_classe(), dict(L.ext), dict(L.monnaie)
    rap = RG.Rapprochement(p.socle.registre, L)
    vivants0 = int(w.table.vivant[:w.table.n].sum())
    faims, erreur = [], None
    t0 = time.time()
    try:
        for _ in range(jours):
            T.jours(w, 1)
            faims.append(T.faim(w))
    except Exception:
        erreur = traceback.format_exc(limit=6)
    duree = time.time() - t0
    tenue, msg = p.socle.conservation.tenue()
    restes = rap.restes()
    autres = {k: v for k, v in restes.items() if k not in T.FAMILLES_HORS_LIVRE_E1 and abs(v) > RG.tolerance(v)}
    attendu = T.hors_livre(p, net0, ext0, monnaie0)
    exterieur = not autres and abs(sum(restes.values()) - attendu) <= RG.tolerance(attendu) + 1e-6
    vivants = int(w.table.vivant[:w.table.n].sum())
    return {"w": w, "p": p, "faims": faims, "tenue": tenue, "msg": msg, "exterieur": exterieur, "autres": autres,
            "vivants0": vivants0, "vivants": vivants, "erreur": erreur, "duree": duree, "n": w.table.n}


def porte_p5():
    g = _vivre("grece", ECHELLE_10K)
    d = _vivre(None, ECHELLE_10K)
    fg = float(np.mean(g["faims"])) if g["faims"] else 1.0
    fd = float(np.mean(d["faims"])) if d["faims"] else 1.0
    # controle positif : la conservation voit 1 000 drachmes posees a la main dans un menage, hors du grand livre
    mg = g["w"].menages[0]
    mg.caisse = mg.caisse + 1000.0
    voit, _ = g["p"].socle.conservation.tenue()
    mg.caisse = mg.caisse - 1000.0
    ok = (g["erreur"] is None and g["tenue"] and g["exterieur"] and g["vivants"] >= 0.97 * g["vivants0"]
          and fg <= fd + 0.02 and not voit)
    f = lambda x: ", ".join(f"{100 * v:.1f}" for v in x["faims"])
    return ok, (f"grece {g['n']} habitants, 30 jours en {g['duree']:.0f} s : {'aucune exception' if g['erreur'] is None else 'EXCEPTION ' + g['erreur']} ; "
                f"conservation {g['msg']} ; argent hors livre {'exterieur seulement' if g['exterieur'] else 'NON EXTERIEUR ' + str(g['autres'])} ; "
                f"vivants {g['vivants']}/{g['vivants0']} ; faim moyenne {fg:.1%} contre {fd:.1%} au monde par defaut "
                f"( {d['n']} habitants, meme echelle, {'aucune exception' if d['erreur'] is None else 'EXCEPTION'} ) ; "
                f"controle positif ( 1 000 drachmes hors livre ) : {'vu' if not voit else 'NON VU'} ; faim par soir, grece : "
                f"{f(g)} ; defaut : {f(d)}")


def porte_p6():
    a, b = _grec(), _grec()
    c = _grec(graine=GRAINE + 1)
    ea, eb, ec = empreinte(a), empreinte(b), empreinte(c)
    ok = ea == eb and ea != ec
    return ok, f"meme graine : {'identiques' if ea == eb else 'DIFFERENTES'} ( {ea[:16]} ) ; autre graine : {'differente' if ea != ec else 'IDENTIQUE'} ( {ec[:16]} )"


def porte_p7():
    from .pays import pays as PA
    res = []
    for ech in (ECHELLE_10K, ECHELLE_100K):
        t0 = time.time(); w = _grec(ech); t1 = time.time()
        PA.installer(w)
        t2 = time.time()
        res.append((w.table.n, t1 - t0, t2 - t1))
        del w
    (n1, c1, i1), (n2, c2, i2) = res
    r = ((c2 + i2) / n2) / ((c1 + i1) / n1)
    ok = r <= 1.5
    return ok, (f"{n1} habitants : creation {c1:.2f} s, installation des 28 domaines {i1:.1f} s ; {n2} habitants : creation "
                f"{c2:.2f} s, installation {i2:.1f} s ; cout par habitant a 100 000 / a 10 000 : {r:.2f} ( seuil 1,5 )")


PORTES = {"P1": porte_p1, "P2": porte_p2, "P3": porte_p3, "P4": porte_p4, "P5": porte_p5, "P6": porte_p6, "P7": porte_p7}


if __name__ == "__main__":
    noms = [a for a in sys.argv[1:] if a in PORTES] or list(PORTES)
    refus = 0
    for nom in noms:
        t0 = time.time()
        try:
            ok, msg = PORTES[nom]()
        except Exception:
            ok, msg = False, "EXCEPTION " + traceback.format_exc(limit=8)
        refus += not ok
        print(f"{'PASSE ' if ok else 'ECHOUE'}  {nom} ( {time.time() - t0:.0f} s ) : {msg}", flush=True)
    print(f"PORTES DE LA POPULATION GRECQUE : {'FRANCHIES' if not refus else f'{refus} REFUSEE(S)'}")
    sys.exit(refus)
