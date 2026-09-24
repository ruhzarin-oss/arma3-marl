"""Les portes du domaine 6 ( Etat ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests etat"""
import json, math, time
import numpy as np
from .. import config as C, monde as W
from ..socle import decision as D
from . import essais as T, d01_population as POP, d02_banques as BQ, d03_economie as EC, d06_etat as M


# ================================================================== la loi, sans monde
def test_tva_par_categorie():
    """Porte : quatre achats connus d un menage ( 10 rations a 5, 2 outils a 30, 3 remedes a 25, 4 carburants a 9,
    hors taxe ) paient 0,13 x 50 + 0,24 x 60 + 0,06 x 75 + 0,24 x 36 = 34,04 drachmes de TVA, au centime de millionieme,
    vus a la fois dans la caisse du menage, dans celle de l Etat et dans le grand livre ; la conservation tient.
    Falsificateur : le taux unique ( celui du moteur, 8 %, ou l equivalent du panier ) sur les memes achats donne autre
    chose, et l ecart se voit. Controle positif : le taux reduit porte a 10 % par une action du gouvernement change la
    TVA de la seule nourriture, de 1,50 exactement ; hors bornes et hors ordre, les actions sont refusees."""
    w, p = T.monde(["etat"])
    mg = next(m for m in w.menages if m.caisse > 500)
    achats = (("nourriture", 10, 5.0), ("outils", 2, 30.0), ("remedes", 3, 25.0), ("carburant", 4, 9.0))
    g0, m0 = w.gouv.caisse, mg.caisse
    livre0 = p.socle.livre.jour_argent.get(("tva", "Menage", "Gouvernement"), [0.0, 0])[0]
    paye = math.fsum(M.percevoir_tva(p, mg, b, q * pu) for b, q, pu in achats)
    livre1 = p.socle.livre.jour_argent.get(("tva", "Menage", "Gouvernement"), [0.0, 0])[0]
    exact = (abs(paye - 34.04) <= 1e-9 and abs((w.gouv.caisse - g0) - 34.04) <= 1e-9 and abs((m0 - mg.caisse) - 34.04) <= 1e-9
             and abs((livre1 - livre0) - 34.04) <= 1e-9)
    unique_moteur = math.fsum(q * pu * 0.08 for _, q, pu in achats)
    unique_panier = math.fsum(q * pu * w.gouv.tva for _, q, pu in achats)
    vu = abs(unique_moteur - 34.04) > 0.01 and abs(unique_panier - 34.04) > 0.01
    ok_a, _ = M.appliquer(p, {"type": "fixer_tva", "categorie": "reduite", "valeur": 0.10})
    paye2 = math.fsum(M.percevoir_tva(p, mg, b, q * pu) for b, q, pu in achats)
    positif = ok_a and abs((paye - paye2) - 1.5) <= 1e-9 and abs(w.gouv.tva - M.taux_tva_equivalent(p)) <= 1e-12
    refus = (not M.appliquer(p, {"type": "fixer_tva", "categorie": "normale", "valeur": 0.30})[0]
             and not M.appliquer(p, {"type": "fixer_tva", "categorie": "super_reduite", "valeur": 0.101})[0]
             and not M.appliquer(p, {"type": "fixer_impot", "nom": "tva", "valeur": 0.2})[0])
    ordre = not M.appliquer(p, {"type": "fixer_tva", "categorie": "reduite", "valeur": 0.05})[0]   # sous le super-reduit ( 6 % )
    categories = (M.taux_tva(p, "nourriture") == 0.10 and M.taux_tva(p, "remedes") == 0.06
                  and M.taux_tva(p, "outils") == 0.24 and M.taux_tva(p, "carburant") == 0.24)
    tenue, msg = p.socle.conservation.tenue()
    ok = exact and vu and positif and refus and ordre and categories and tenue
    return ok, (f"TVA des quatre achats {paye:.6f} ( attendu 34,04 ) ; taux unique du moteur {unique_moteur:.2f}, du panier "
                f"( {w.gouv.tva:.4f} apres la baisse ) {unique_panier:.2f} : ecart vu {vu} ; taux reduit a 10 % : {paye2:.2f}, "
                f"la nourriture seule baisse de {paye - paye2:.4f} ; actions hors bornes refusees {refus}, hors ordre {ordre} ; "
                f"{msg}")


def test_ir_par_tranches():
    """Porte : le bareme de la loi 4646/2019 sur six revenus connus ( 450, 900, 2 000, 4 500, 7 700, 18 300 ), la
    reduction de l article 16 sur huit cas calcules a la main ( 0 ; 1 283 ; 2 360 ; 13 883 ; 18 300 ; 2 000 ; 2 323 ;
    4 340 ), la methode cumulative ( au dernier jour, la retenue cumulee de 365 jours de revenus irreguliers est l impot
    exact de l annee ; a mi-annee, un revenu regulier a paye la moitie de l impot annuel ), tout a 1e-9 pres. Dans le
    monde, 20 jours : le revenu impose que portent les colonnes ( salaires et pensions ; non salarial declare et cache )
    est ce que le grand livre a vu verser a la paie, motif par motif ( 1e-6 relatif ) ; au moins 99 % des menages ont
    verse l impot cumule de leurs membres au centime. Falsificateur : 1 000 drachmes de revenu fantome ecrites a la main
    dans la colonne d un salarie se voient dans ce recoupement ; un taux unique de 15 % ne rend pas le bareme."""
    cas = ((5000, 450.0), (10000, 900.0), (15000, 2000.0), (25000, 4500.0), (35000, 7700.0), (60000, 18300.0))
    bar = all(abs(M.bareme_ir(y) - v) <= 1e-9 for y, v in cas)
    cas2 = ((8000, 8000, 0, 0.0), (15000, 15000, 0, 1283.0), (20000, 20000, 2, 2360.0), (50000, 50000, 0, 13883.0),
            (60000, 60000, 0, 18300.0), (15000, 0, 0, 2000.0), (20000, 10000, 0, 2323.0), (30000, 30000, 5, 4340.0))
    red = all(abs(M.impot_annuel(y, ys, k) - v) <= 1e-9 for y, ys, k, v in cas2)
    rng = np.random.default_rng(3)
    r = rng.gamma(2.0, 30.0, 365); Y = np.cumsum(r)
    cumul = abs(M.impot_cumule(Y[-1], Y[-1], 1, 365, 365) - M.impot_annuel(Y[-1], Y[-1], 1)) <= 1e-9
    moitie = abs(M.impot_cumule(60.0 * 182, 60.0 * 182, 0, 182, 365) - M.impot_annuel(60.0 * 365, 60.0 * 365, 0) * 182 / 365) <= 1e-9
    plat = sum(1 for y, v in cas if abs(0.15 * y - v) > 1.0)
    w, p = T.monde(["etat"])
    e = p.domaine("etat"); f = e.fisc
    livre = {"sal": 0.0, "non": 0.0}
    for _ in range(20):
        T.jours(w, 1)
        for m, pa, re, s, _ in p.comptes_hier["argent"]:
            if re != "Menage": continue
            if m in ("salaire", "salaire public", "pension"): livre["sal"] += s
            elif m in ("revenu agricole", "benefice marchand"): livre["non"] += s
    ch = p.colonnes["habitant"]; nh = len(w.habitants)

    def recoupe():
        sal = math.fsum(ch["fisc_sal"][:nh].tolist())
        non = math.fsum((ch["fisc_revenu"][:nh] - ch["fisc_sal"][:nh] + ch["fisc_cache"][:nh]).tolist())
        egal = abs(sal - livre["sal"]) <= 1e-6 * livre["sal"] + 1e-6 and abs(non - livre["non"]) <= 1e-6 * livre["non"] + 1e-6
        return sal, non, egal
    sal, non, monde_ok = recoupe()
    d, duree = f.jours_exercice(p.jour - 1)
    Yh, Ys, Rt, enf = ch["fisc_revenu"][:nh], ch["fisc_sal"][:nh], ch["fisc_retenu"][:nh], ch["fisc_enfants"][:nh]
    du = np.asarray(M.impot_cumule(Yh, Ys, enf, d, duree, f.taux_ir, f.tranches_ir)) - Rt
    mid = np.array([h.menage.id if h.vivant and h.menage is not None else -1 for h in w.habitants])
    par_m = np.bincount(mid[mid >= 0], weights=du[mid >= 0], minlength=len(w.menages))
    payeurs = np.bincount(mid[(mid >= 0) & (Yh > 0)], minlength=len(w.menages)) > 0
    au_centime = float((np.abs(par_m[payeurs]) < 0.0101).mean()) if payeurs.any() else 0.0
    h = next(x for x in w.habitants if x.vivant and x.role == "soldat")
    ch["fisc_sal"][h.id] += 1000.0; ch["fisc_revenu"][h.id] += 1000.0
    _, _, apres = recoupe()
    vu = not apres
    ok = bar and red and cumul and moitie and plat >= 5 and monde_ok and au_centime >= 0.99 and vu
    return ok, (f"bareme {bar}, reduction {red}, cumul au 31 decembre {cumul}, mi-annee {moitie} ; taux unique 15 % faux "
                f"sur {plat}/6 revenus ; 20 jours : salaires et pensions imposes {sal:.2f} pour {livre['sal']:.2f} au grand "
                f"livre, non salarial {non:.2f} pour {livre['non']:.2f} ( dont declare {f.revenus['declare']:.2f}, non "
                f"attribue {f.revenus['non_attribue']:.2f} ) ; menages a jour au centime {au_centime:.1%} ; retenues "
                f"{f.compte['retenue_ir']:.0f}, remboursements {f.compte['remboursement_ir']:.0f} ; revenu fantome vu {vu}")


def test_is_penalites_douanes():
    """Porte, sur des cas calcules a la main : IS de 22 % avec report des pertes ( -1 000, 500, 800, -200, 1 000 : 0, 0,
    66, 0, 176 ) et prescription a 5 ans ( une perte de plus de 5 ans n est plus imputee : 220 ) ; penalite
    d inexactitude par seuil ( 4 % : 0 ; 10 % : 10 % ; 30 % : 25 % ; 60 % : 50 % ; rien declare : 50 % ) ; ENFIA ( 100 m2
    a 600 : 280 ; a 5 200 : 1 110 ) ; douane d un outil de 1 000 : 40 de droit, 249,60 de TVA a l importation."""
    pertes, seq = [], ((-1000.0, 0.0), (500.0, 0.0), (800.0, 66.0), (-200.0, 0.0), (1000.0, 176.0))
    is_ok = all(abs(M.impot_societes(b, pertes, 30 * k)[0] - v) <= 1e-9 for k, (b, v) in enumerate(seq))
    vieux = [[0, 1000.0]]
    prescrit = abs(M.impot_societes(1000.0, vieux, 5 * 365 + 1)[0] - 220.0) <= 1e-9
    pen = [M.taux_penalite(a, b) for a, b in ((4, 100), (10, 100), (30, 100), (60, 100), (10, 0))]
    pen_ok = pen == [0.0, 0.10, 0.25, 0.50, 0.50]
    en_ok = abs(M.enfia(100, 600) - 280.0) <= 1e-9 and abs(M.enfia(100, 5200) - 1110.0) <= 1e-9
    w, p = T.monde(["etat"])
    droit, tva = M.taxes_import(p, "outils", 1000.0)
    dou_ok = abs(droit - 40.0) <= 1e-9 and abs(tva - 249.6) <= 1e-9
    ok = is_ok and prescrit and pen_ok and en_ok and dou_ok
    return ok, (f"IS avec reports {is_ok}, prescription {prescrit} ; penalites {pen} ; ENFIA {en_ok} ; douane {droit:.2f} "
                f"+ TVA {tva:.2f}")


def test_comptes_nationaux():
    """Porte, sur une journee construite : une commande publique de 1 000, 500 de nourriture et 65 de TVA payes par des
    menages, 300 d achats intermediaires d une entreprise, 400 exportes a la main par le moteur, 200 importes a la main
    par l Etat : consommation des menages 565, des administrations 1 200, PIB 1 965 ( les achats intermediaires n y
    entrent pas, l importation de l Etat s y compense ). Puis dans le monde, 10 jours : chaque jour un PIB positif et
    une consommation finale des administrations positive."""
    w, p = T.monde(["etat"])
    comptes = {"argent": [("commande publique", "Gouvernement", "Marche", 1000.0, 1), ("nourriture", "Menage", "Marche", 500.0, 3),
                          ("tva", "Menage", "Gouvernement", 65.0, 3), ("achat intrant", "Entreprise", "Marche", 300.0, 1)]}
    c = M.comptes_nationaux(p, comptes, 400.0, 200.0)
    construit = (abs(c["conso_menages"] - 565.0) <= 1e-9 and abs(c["conso_apu"] - 1200.0) <= 1e-9
                 and abs(c["pib"] - 1965.0) <= 1e-9 and abs(c["exportations"] - 400.0) <= 1e-9)
    T.jours(w, 10)
    serie = [cn for _, cn in p.domaine("etat").stat.comptes]
    vivant = len(serie) >= 10 and all(x["pib"] > 0 for x in serie)
    apu = all(x["conso_apu"] > 0 for x in serie)
    moy = {k: np.mean([x[k] for x in serie]) for k in ("pib", "conso_menages", "conso_apu", "exportations", "importations")}
    ok = construit and vivant and apu
    return ok, (f"journee construite : menages {c['conso_menages']:.0f}, administrations {c['conso_apu']:.0f}, PIB "
                f"{c['pib']:.0f} ; 10 jours du monde, par jour : PIB {moy['pib']:.0f} ( menages {moy['conso_menages']:.0f}, "
                f"administrations {moy['conso_apu']:.0f}, exportations {moy['exportations']:.0f}, importations "
                f"{moy['importations']:.0f} ) ; PIB annuel publie {p.domaine('etat').stat.publie['pib_annuel']:.0f}")


# ================================================================== le Tresor, le budget, la dette
def test_solde_budgetaire():
    """Porte : 40 jours, bons a 7 jours pour que des echeances tombent : chaque soir, recettes - depenses = - variation
    de la dette nette ( dette brute lue a part - caisse ) a un demi-centime, et le cumul aussi ; aucun reste hors livre
    non attribue. Doivent avoir joue : des bons emis ET rembourses, une vente d or ( ecrite a la main par le moteur,
    attribuee ), une avance de la banque centrale posee a la main. Falsificateur : 100 drachmes retirees a la main de la
    caisse du Tresor se voient le soir meme ( ecart de +100, reste non attribue de -100 )."""
    w, p = T.monde(["etat"])
    e = p.domaine("etat"); tr = e.tresor
    tr.duree_bons_j = 7
    remb = 0.0; or_ok = False
    for j in range(40):
        if j == 5: or_ok = M.appliquer(p, {"type": "exporter_or", "quantite": 1.0})[0]
        if j == 25: BQ.avance_a_l_etat(p, 5000.0)
        T.jours(w, 1)
        remb += sum(s for m, pa, re, s, _ in p.comptes_hier["argent"] if m == "remboursement_titre")
    serie = list(tr.serie)
    pire = max(abs(s[7]) for s in serie); cumul = math.fsum(s[7] for s in serie)
    reste = max(abs(s[8]) for s in serie)
    identite = pire <= 0.005 and abs(cumul) <= 0.005 and reste <= 0.005
    joue = tr.n_bons >= 1 and remb > 0 and or_ok and e.budget.recettes["vente_or"] > 0
    w.gouv.caisse -= 100.0
    T.jours(w, 1)
    der = tr.serie[-1]
    vu = abs(der[7] - 100.0) <= 0.01 and abs(der[8] + 100.0) <= 0.01
    ex = M.execution_budget(p)
    dep = math.fsum(x[1] for x in ex["depenses"].values()); cred = math.fsum(x[0] for x in ex["depenses"].values())
    ok = identite and joue and vu
    return ok, (f"{len(serie)} soirs : pire ecart {pire:.2e}, cumul {cumul:+.2e}, reste hors livre non attribue {reste:.2e} ; "
                f"{tr.n_bons} bons ( {tr.emis_bons:.0f} drachmes ), rembourses {remb:.0f}, "
                f"vente d or {e.budget.recettes['vente_or']:.0f}, "
                f"dette brute {M.dette_brute(p):.0f} ; budget execute {dep:.0f} sur {cred:.0f} de credits a "
                f"{ex['ecoule']:.1%} de l exercice, solde {ex['solde']:.0f} ; caisse videe de 100 a la main : ecart {der[7]:+.2f}, "
                f"reste {der[8]:+.2f}")


def _impayes_etat(p):
    return math.fsum(v[0] for m, v in p.comptes_hier["impayes"].items() if m in M.MOTIFS_ETAT_SEUL)


def _vivre_pas_a_pas(w, p, jours):
    mini, imp, premier = math.inf, 0.0, None
    for _ in range(jours):
        for _ in range(C.PAS_PAR_JOUR):
            w.pas_suivant(); mini = min(mini, w.gouv.caisse)
        x = _impayes_etat(p); imp += x
        if x > 0 and premier is None: premier = p.jour - 1
    return mini, imp, premier


def test_tresor_jamais_a_sec():
    """Porte : 1 500 habitants ( echelle 3, ou le Tresor du moteur est a sec vers le 25e jour ), 40 jours, pas a pas :
    la caisse de l Etat ne descend jamais sous zero et aucun paiement que seul l Etat fait ( salaires publics, pensions,
    commandes, subventions, remboursements d impot, interets ) n est impaye ; la caisse de depart vaut 400 drachmes par
    habitant, empruntee ( la dette d ouverture l egale ). Controle positif : le meme monde sans financement et avec la
    caisse du moteur ( 200 000 ) a des impayes de l Etat avant le 40e jour."""
    w, p = T.monde(["etat"], echelle=3)
    e = p.domaine("etat")
    n = sum(1 for h in w.habitants if h.vivant)
    cible = M.TRESORERIE_PAR_HABITANT * n
    ouverture = abs(w.gouv.caisse - cible) <= 1e-6 * cible and abs(M.dette_brute(p) - e.tresor.ouverture) <= 1e-6 * cible
    mini, imp, premier = _vivre_pas_a_pas(w, p, 40)
    ancien = M.PROPORTIONNER_TRESORERIE
    M.PROPORTIONNER_TRESORERIE = False
    try: w2, p2 = T.monde(["etat"], echelle=3)
    finally: M.PROPORTIONNER_TRESORERIE = ancien
    p2.domaine("etat").tresor.financement = False
    mini2, imp2, premier2 = _vivre_pas_a_pas(w2, p2, 40)
    ok = ouverture and mini >= 0.0 and imp == 0.0 and imp2 > 0.0
    return ok, (f"{n} habitants : caisse de depart {cible:.0f} ( dette d ouverture {e.tresor.ouverture:.0f} ) : {ouverture} ; "
                f"40 jours finances : caisse minimale {mini:.0f}, impayes de l Etat {imp:.2f}, dette {M.dette_brute(p):.0f} "
                f"( {e.tresor.n_bons} bons, avances {p.domaine('banques').bc.avances:.0f} ) ; sans financement : caisse "
                f"minimale {mini2:.0f}, impayes {imp2:.0f} des le jour {premier2}")


# ================================================================== la statistique publique
def test_sitrep_sans_verite_cachee():
    """Porte : apres 5 jours, le bulletin du gouvernement est construit sur la statistique. Falsificateur : une incubation
    et un cas benin injectes a la main ne changent pas un caractere du bulletin, alors que le bulletin du moteur ( qui lit
    la verite ) les voit - l instrument sait voir une fuite. Controle positif : un deces et un cas grave poses a la main
    sont absents du bulletin du jour, puis y sont apres leur retard ( declaration du deces le lendemain, recensement
    hospitalier du soir ) ; les vivants du bulletin sont les inscrits publies de l etat civil."""
    w, p = T.monde(["etat"])
    T.jours(w, 5)
    e = p.domaine("etat"); ec = p.domaine("population").etat_civil
    s0 = json.dumps(w.sitrep(), sort_keys=True)
    m0 = W.Monde.sitrep(w)["sante"]
    libres = [x for x in w.habitants if x.vivant and x.etat == "S" and x.poste != "hopital"]
    h, k = libres[0], libres[1]
    h.etat, h.jours_etat = "E", 0.0
    k.etat, k.gravite, k.jours_etat = "I", 0.2, 0.0
    s1 = json.dumps(w.sitrep(), sort_keys=True)
    m1 = W.Monde.sitrep(w)["sante"]
    invisible = s0 == s1 and m1 != m0
    v = next(x for x in w.habitants if x.vivant and x not in (h, k) and POP.age_de(p, x) >= 30
             and len(POP.adultes_vivants(p, x.menage, sauf=x)) >= 1)
    g = next(x for x in libres[2:] if x is not v)
    POP.deceder(p, v, "accident")
    g.etat, g.gravite, g.jours_etat = "I", 0.9, 0.0
    s2 = w.sitrep()
    meme_jour = json.dumps(s2, sort_keys=True) == s1
    T.jours(w, 2)
    s3 = w.sitrep()
    col = p.colonnes["habitant"]
    declare = (int(col["deces_declare"][v.id]) == 1 and s3["population"]["morts"] >= s2["population"]["morts"] + 1
               and s3["population"]["morts"] == ec.deces - e.stat.base_deces)
    hospit = (g.id in e.stat.hospitalises or not g.vivant) and s3["sante"]["infectes"] == len(e.stat.hospitalises)
    inscrits = s3["population"]["vivants"] == e.stat.publie["population"]["inscrits"]
    vrais = sum(1 for x in w.habitants if x.vivant)
    ok = invisible and meme_jour and declare and hospit and inscrits
    return ok, (f"incubation et cas benin injectes : bulletin inchange {s0 == s1}, bulletin du moteur change {m1 != m0} "
                f"( incubations {m0['incubation']} -> {m1['incubation']} ) ; deces et cas grave : absents le jour meme "
                f"{meme_jour}, deces publie apres declaration {declare}, cas grave au recensement hospitalier {hospit} "
                f"( {s3['sante']['infectes']} hospitalises publies ) ; vivants du bulletin {s3['population']['vivants']} "
                f"( inscrits publies {inscrits} ; vrais vivants {vrais} )")


def test_enquete_chomage():
    """Porte : 2 000 habitants, un chomage pose a la main ( 30 % des actifs licencies dans une region, 5 % ailleurs ).
    300 enquetes de 120 menages, chacune sur son propre tirage : l erreur est dans la bande theorique du sondage -
    biais moyen sous 3 sigma / racine de 300, ecart-type des erreurs de 0,85 a 1,15 sigma theorique ( estimateur par le
    ratio, correction de population finie ), de 91 a 99 % des erreurs dans +/- 1,96 sigma. Falsificateurs : le registre
    exact ( tout le pays interroge ) n a aucune erreur - hors de la bande d un sondage ; une base de sondage reduite a
    la region la plus touchee est biaisee au-dela de 3 sigma / racine de 300."""
    w, p = T.monde(["etat"], echelle=4)
    T.jours(w, 1)
    rng = np.random.default_rng(5)
    region_a = sorted(w.marches)[0]
    nj = p.col("habitant", "naissance_j")
    lic = 0
    for h in list(w.habitants):
        if not h.vivant or h.role in ("enfant", "retraite") or h.travail is None: continue
        if not C.AGE_TRAVAIL <= (p.jour - int(nj[h.id])) / POP.JOURS_AN < C.AGE_RETRAITE: continue
        taux = 0.30 if h.domicile.marche.id == region_a else 0.05
        if rng.random() < taux: EC.licencier(p, h, "porte"); lic += 1
    cadre = M.cadre_enquete(p)
    y, x, _, _ = M.repondre(p, cadre)
    r = y.sum() / x.sum()
    n, K = 120, 300
    sig = M.sigma_theorique(y, x, n)
    est = []
    for k in range(K):
        yy, xx, _, _ = M.enqueter(p, n, np.random.default_rng(1000 + k), cadre)
        est.append(yy.sum() / xx.sum())
    err = np.array(est) - r
    biais, sd, couv = float(err.mean()), float(err.std(ddof=1)), float((np.abs(err) <= M.Z95 * sig).mean())
    bande = abs(biais) <= 3 * sig / math.sqrt(K) and 0.85 <= sd / sig <= 1.15 and 0.91 <= couv <= 0.99
    exact = np.full(K, y.sum() / x.sum()) - r
    vu_exact = not (0.85 <= float(exact.std(ddof=1)) / sig <= 1.15)
    cadre_a = np.array([i for i in cadre.tolist() if w.menages[i].domicile.marche.id == region_a], dtype=np.int64)
    est_a = []
    for k in range(K):
        yy, xx, _, _ = M.enqueter(p, n, np.random.default_rng(5000 + k), cadre_a)
        est_a.append(yy.sum() / xx.sum())
    biais_a = float(np.mean(est_a) - r)
    vu_biais = abs(biais_a) > 3 * sig / math.sqrt(K)
    ok = bande and vu_exact and vu_biais and lic > 0
    return ok, (f"{lic} licencies, chomage vrai {r:.2%} sur {len(cadre)} menages ; {K} enquetes de {n} menages : biais "
                f"{biais:+.4f} ( borne {3 * sig / math.sqrt(K):.4f} ), ecart-type {sd:.4f} pour {sig:.4f} theorique "
                f"( {sd / sig:.2f} ), couverture a 95 % {couv:.1%} ; registre exact vu {vu_exact} ; base biaisee "
                f"( region {region_a} ) : biais {biais_a:+.4f}, vu {vu_biais}")


# ================================================================== la decision
def _instrument(notes):
    """Le decideur du socle rempli de notes donnees ( jour, action, note ) : son epsilon carre et son test par
    permutation, sur d autres notes que celles que le point a vraiment rendues."""
    d = D.Decideur(M.POINT_CONTROLE, "hasard")
    for j, a, x in notes:
        st = d.stats.get((j, a))
        if st is None: d.stats[(j, a)] = [1, x, x * x]
        else: st[0] += 1; st[1] += x; st[2] += x * x
        d.echantillon.append((j, a, x))
    return d.part_du_choix(), d.p_permutation(n=200, graine=0)


def test_controle_fiscal():
    """Porte de la decision : 1 500 habitants, tous les policiers presents a 10 h controlent ( une vingtaine de
    decisions par jour ), en choisissant leur critere au hasard ( mode hasard ), 45 jours ( l IS du premier mois est
    liquide au 30e ). La note doit dependre du choix ( conventions, section 4 ) : part du choix ( epsilon carre a jour
    egal ) >= 0,01 ET p_permutation < 0,05 ; au moins 200 notes murees. La note est le logarithme signe du net
    encaisse ( note_controle ) : les drachmes brutes, domineees par quelques arrieres geants, sont mesurees a cote
    par le meme instrument ( 0,004 le 23/09 ). Falsificateur de l instrument : des notes tirees sans lien avec le choix,
    aux memes jours et aux memes actions, ne passent pas. Au moins 10 controles qui redressent, la conservation tient."""
    w, p = T.monde(["etat"], echelle=3, modes={"controle_fiscal": "hasard"})
    M.appliquer(p, {"type": "fixer_controle", "part": 1.0})
    T.jours(w, 45)
    e = p.domaine("etat"); dec = e.decideur; f = e.fisc
    eps, pval, brute = dec.part_du_choix(), dec.p_permutation(n=200, graine=0), dec.part_du_choix_brute()
    notes = list(f.notes)
    rng = np.random.default_rng(17)
    eps_bruit, p_bruit = _instrument([(j, a, float(z)) for (j, a, _, _), z in zip(notes, rng.standard_normal(len(notes)))])
    eps_dr, p_dr = _instrument([(j, a, net) for j, a, _, net in notes])
    par = {}
    for _, a, x, net in notes: par.setdefault(M.CRITERES[a], []).append((x, net))
    moy = ", ".join(f"{k} {np.mean([x for x, _ in v]):+.2f} ( {np.mean([n for _, n in v]):+.0f} dr, {len(v)} )"
                    for k, v in par.items())
    tenue, msg = p.socle.conservation.tenue()
    ok = (len(notes) >= 200 and eps >= 0.01 and pval < 0.05 and not (eps_bruit >= 0.01 and p_bruit < 0.05)
          and f.compte["controles_positifs"] >= 10 and tenue)
    return ok, (f"{dec.n_decisions} decisions, {len(notes)} notes murees ; note moyenne par critere ( drachmes nettes, "
                f"nombre ) : {moy} ; part du choix {eps:.3f} ( epsilon carre ; eta carre brut {brute:.3f} ), p = {pval:.3f} ; "
                f"en drachmes brutes : {eps_dr:.3f}, p = {p_dr:.3f} ; notes sans lien avec le choix : {eps_bruit:.3f}, "
                f"p = {p_bruit:.3f} ; {f.compte['controles_positifs']:.0f} redressements sur {f.compte['controles']:.0f} "
                f"controles, {f.compte['redressements']:.0f} drachmes redressees + {f.compte['penalites']:.0f} de "
                f"penalites, {f.compte['recouvre']:.0f} recouvrees ; IS liquide {f.compte['impot_societes']:.0f}, elude "
                f"{f.compte['is_elude']:.0f} ; {msg}")


# ================================================================== le pays
def test_pays_vivable():
    return T.porte_commune("etat", n_jours=12)


def test_cout():
    """Les routines propres du domaine ( chronometrees ) coutent au plus 15 % d une journee du moteur seul, a 10 000
    habitants."""
    w0 = W.Monde(echelle=20)
    T.jours(w0, 1)
    t0 = time.perf_counter(); T.jours(w0, 2); t_e1 = (time.perf_counter() - t0) / 2
    w, p = T.monde(["etat"], echelle=20)
    T.jours(w, 1)
    e = p.domaine("etat"); e.chrono.clear()
    t0 = time.perf_counter(); T.jours(w, 2); t_pays = (time.perf_counter() - t0) / 2
    propre = sum(e.chrono.values()) / 2
    detail = ", ".join(f"{k} {v / 2 * 1000:.0f}" for k, v in sorted(e.chrono.items(), key=lambda kv: -kv[1]))
    ok = propre <= 0.15 * t_e1
    return ok, (f"{len(w.habitants)} habitants : moteur seul {t_e1:.2f} s par jour, pays avec l Etat et ses dependances "
                f"{t_pays:.2f} s ; routines propres de l Etat {propre * 1000:.0f} ms par jour ( {propre / t_e1:.1%} ; "
                f"{detail} ms ), {propre / len(w.habitants) * 1e6:.1f} us par habitant")


TESTS = [test_tva_par_categorie, test_ir_par_tranches, test_is_penalites_douanes, test_comptes_nationaux,
         test_solde_budgetaire, test_tresor_jamais_a_sec, test_sitrep_sans_verite_cachee, test_enquete_chomage,
         test_controle_fiscal, test_pays_vivable, test_cout]
