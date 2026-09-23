"""Les portes du domaine 3 ( economie reelle ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests economie"""
import math, time
import numpy as np
from .. import config as C, monde as W
from ..socle import registre as R
from . import essais as T, d02_banques as BQ, d03_economie as M

ELSTAT_2023 = {"alimentation": 0.207, "alcool_tabac": 0.034, "habillement": 0.047, "logement": 0.141,
               "equipement": 0.044, "sante": 0.077, "transport": 0.131, "communications": 0.042, "loisirs": 0.044,
               "education": 0.034, "restauration": 0.114, "divers": 0.084}     # communique ELSTAT du 27/09/2024
PAS_H = C.PAS_PAR_JOUR // 24


def _avancer(w, heures):
    for _ in range(int(round(heures * PAS_H))): w.pas_suivant()


def _jusqu_apres_cloture(w):
    """Du matin 6 h au pas qui suit la cloture de 23 h 50 : les comptes du soir sont ceux de l instant."""
    _avancer(w, 18)


def _cp_mesure(p, c):
    """Les capitaux propres recomptes sur les objets eux-memes : caisse, stocks, capital, creances, prets du domaine 2,
    dettes du socle - sans rien lire des comptes du domaine hors le capital fixe qu il est seul a tenir."""
    u = c.unite; w = p.w
    m = u if type(u).__name__ == "Marche" else w.marches[u.lieu.marche.id]
    bq = p.domaine("banques")
    prets = [bq.prets[i] for i in bq.prets_de.get(u, ())]
    dettes = math.fsum(pr.principal + pr.du_interet for pr in prets) + math.fsum(cr.montant for cr in p.socle.creances.de(u))
    detenues = math.fsum(cr.montant for cr in p.socle.creances.actives.values() if cr.creancier is u)
    return u.caisse + M._valeur_stocks(w, u, m) + c.capital_net() + detenues - dettes


# ================================================================== le budget des menages
def test_budget_parts():
    """Porte : les parts du budget sont celles d ELSTAT 2023 ( somme 1 a 0,002 pres, chaque part a 1e-9 ) ; en 20 jours,
    la structure voulue hors alimentation suit ELSTAT a 0,5 point pres ; la loi d Engel tient : la part de
    l alimentation du quintile le plus pauvre ( revenu lisse ) vaut au moins 1,5 fois celle du plus riche ( ELSTAT :
    alimentation et logement 55,8 % contre 24,8 % ). Controle positif ( fonction pure ) : doubler le prix de la
    nourriture fait monter sa part d au moins 50 % chez un menage modeste ; la nourriture passe meme quand le revenu ne
    la couvre pas. Le niveau de la part alimentaire est rapporte, pas juge : il depend des salaires du moteur."""
    conf = abs(sum(ELSTAT_2023.values()) - 1.0) <= 0.002 and all(
        abs(c.part - ELSTAT_2023[c.nom]) <= 1e-9 for c in M.CATEGORIES) and len(M.CATEGORIES) == len(ELSTAT_2023)
    w, p = T.monde(["economie"])
    T.jours(w, 20)
    b = M.budget_des_menages(p)
    pa = b["parts"]["alimentation"]
    ref_hors = {k: v / (1.0 - M.PARTS[M.I_ALIM]) for k, v in zip(M.NOMS_CATEGORIES, M.PARTS) if k != "alimentation"}
    structure = max(abs(b["parts"][k] / (1.0 - pa) - v) for k, v in ref_hors.items())
    q = b["alimentation_par_quintile"]
    engel = q[0] / q[4] if q[4] > 0 else math.inf
    _, M1 = M.repartir_budget([40.0], [0.0], [0.0], [8.0])
    _, M2 = M.repartir_budget([40.0], [0.0], [0.0], [16.0])
    s1, s2 = M1[0, M.I_ALIM] / M1[0].sum(), M2[0, M.I_ALIM] / M2[0].sum()
    cv, M3 = M.repartir_budget([5.0], [0.0], [100.0], [8.0])
    positif = s2 >= 1.5 * s1 and M3[0, M.I_ALIM] == 8.0 and cv[0] < 8.0
    ok = conf and structure <= 0.005 and engel >= 1.5 and positif
    return ok, (f"parts ELSTAT {'tenues' if conf else 'FAUSSES'} ; alimentation mesuree {pa:.1%} ( ELSTAT 20,7 % ) ; "
                f"structure hors alimentation a {structure * 100:.2f} point ; alimentation par quintile "
                + ", ".join(f"{x:.1%}" for x in q) + f" ( Engel x{engel:.1f} ) ; prix double : part {s1:.0%} -> {s2:.0%}")


# ================================================================== les comptes des entreprises
def test_identite_comptable():
    """Porte : 31 jours ( une fin de mois, ses dividendes ), un pret a une fonderie et a un marche, un remboursement
    anticipe, un investissement, une dette fournisseur reglee, une autre remise, un apport, une reevaluation : chaque
    soir, pour chaque unite, actif = dettes + capitaux propres PORTES, a une tolerance du registre ; a la fin, pour chaque
    unite, resultat cumule = variation des capitaux propres RECOMPTES sur les objets + distributions - apports ; les
    flux des comptes = le grand livre, motif par motif, par classe. Falsificateurs : 777 drachmes posees a la main dans
    la caisse d un marche se voient au recoupement avec le grand livre ( a 1e-6 ) ; 50 drachmes de principal effacees a
    la main sur un pret se voient dans l identite de la fonderie ( a 1e-6 )."""
    w, p = T.monde(["economie"])
    d = p.domaine("economie"); L = p.socle.livre; K_ = p.socle.creances
    e = next(c.unite for c in d.unites if c.id == "fonderie@factory02")
    km, ma = w.marches["Kavala"], w.marches["Athira"]
    patron = d.proprietaires[e.id].menage
    pe = None
    for j in range(30):
        if j == 3:
            pe = BQ.preter(p, BQ.banque_de(p, e), e, 5000.0, "entreprise")
            BQ.preter(p, BQ.banque_de(p, km), km, 3000.0, "entreprise")
        if j == 6: BQ.rembourser_par_anticipation(p, pe, 1000.0)
        if j == 8: M.investir(p, e, 2000.0, fournisseur=ma)
        if j == 9: c1 = K_.constater(ma, e, 150.0, "achat intrant", p.jour)
        if j == 11: K_.regler(c1, L)
        if j == 12: c2 = K_.constater(ma, e, 80.0, "achat intrant", p.jour)
        if j == 13: K_.abandonner(c2, "remise")
        if j == 14: M.apporter(p, e, patron, 500.0)
        if j == 15: M.reevaluer_capital(p, e, 100000.0)
        T.jours(w, 1)
    _jusqu_apres_cloture(w)
    pire = max(c.pire_ecart for c in d.unites)
    jours = sum(c.jours_tenus for c in d.unites)
    pire_res = 0.0
    for c in d.unites:
        cu = c.cumul
        attendu = (_cp_mesure(p, c) - c.cp0) + cu["dividendes"] + cu["boni"] - cu["apports"] - cu["reevaluation"]
        pire_res = max(pire_res, abs(cu["resultat"] - attendu) / R.tolerance(abs(c.cp) + abs(c.cp0), c.volume))
    livre = d.pire_livre
    div = sum(c.cumul["dividendes"] for c in d.unites)
    # les falsificateurs
    km.caisse += 777.0
    pe.principal -= 50.0
    _avancer(w, 24)
    vu_livre = d.ecarts_livre["Marche"]["autres"]
    vu_pret = d.comptes[e.id].ecart_drachmes
    identite_marche = abs(d.comptes["marche@Kavala"].ecart) <= 1.0
    ok = (pire <= 1.0 and pire_res <= 1.0 and livre <= 1.0 and div > 0 and abs(vu_livre - 777.0) <= 1e-6
          and abs(vu_pret - 50.0) <= 1e-6 and identite_marche)
    return ok, (f"{jours} bilans d unite tenus, pire ecart {pire:.3f} tolerance ; resultat = variation des capitaux propres "
                f"recomptes : pire {pire_res:.3f} tolerance ; grand livre : pire {livre:.3f} tolerance ; dividendes "
                f"{div:.0f} drachmes ; caisse falsifiee vue {vu_livre:+.6f} ; principal efface vu {vu_pret:+.6f}")


def test_faillite():
    """Porte, sur un cas construit : une centrale empruntant plus que son capital, videe de sa caisse chaque jour a 17 h,
    et qui recoit 5 000 drachmes a 20 h ( une recette tardive ), avec une dette salariale ( 100 ), fiscale ( 200 ) et
    fournisseur ( 400 ) : la faillite tombe au plus tard 5 jours apres ; chaque rang recoit exactement min( du, reste )
    dans l ordre salaries, Etat, banques, fournisseurs ( 1e-6 ) ; ses salaries sont licencies et inscrits ; ses stocks
    sont au marche ; la conservation tient ; ce qui reste du aux fournisseurs est abandonne ; elle ne produit plus ; son
    identite comptable a tenu tous les soirs."""
    w, p = T.monde(["economie"])
    d = p.domaine("economie"); L = p.socle.livre; K_ = p.socle.creances
    T.jours(w, 1)
    c = min((c for c in d.unites if c.nature == "entreprise" and c.unite.type == "centrale"), key=lambda c: c.id)
    e = c.unite
    gens = M.salaries(p, e)
    autre = next(m for k, m in sorted(w.marches.items()) if m is not w.marches[e.lieu.marche.id])
    BQ.preter(p, BQ.banque_de(p, e), e, c.capital_net() + 20000.0, "entreprise", duree=12)
    K_.constater(gens[0].menage, e, 100.0, "salaire", p.jour)
    K_.constater(w.gouv, e, 200.0, "tva", p.jour)
    K_.constater(autre, e, 400.0, "achat intrant", p.jour)
    jour0 = p.jour
    for _ in range(6):
        _avancer(w, 11)
        if not c.liquidee: L.payer_l_exterieur(e, e.caisse, "achat intrant")
        _avancer(w, 3)
        if not c.liquidee: L.transferer(w.gouv, e, 5000.0, "electricite")
        _avancer(w, 10)
        if c.liquidee: break
    if not c.liquidee: return False, f"pas de faillite en 6 jours : capitaux propres {c.cp:.0f}, caisse {e.caisse:.0f}"
    r = d.faillites[-1]
    reste, ordre = r["disponible"], True
    for rang in M.RANGS:
        du, paye = r[rang]
        attendu = min(du, max(0.0, reste))
        ordre &= abs(paye - attendu) <= 1e-6 * max(1.0, du)
        reste -= paye
    produit = dict(e.produit_du_jour)
    T.jours(w, 1)
    arret = e.produit_du_jour == produit
    licencies = all(h.travail is None and d.chomeurs.get(h.id, [None] * 4)[3] == "faillite" for h in gens)
    vide = all(q <= 1e-9 for q in e.stocks.values())
    tenue, msg = p.socle.conservation.tenue()
    abandon = p.socle.creances.abandonnees.get("faillite", 0.0)
    ok = (c.liquidee_j - jour0 <= 5 and ordre and licencies and vide and tenue and abandon >= 400.0 - 1e-6 and arret
          and c.pire_ecart <= 1.0)
    return ok, (f"{e.id} liquidee le jour {c.liquidee_j} ( {c.liquidee_j - jour0} jours ) : disponible "
                f"{r['disponible']:.0f} ; " + ", ".join(f"{k} {r[k][1]:.0f}/{r[k][0]:.0f}" for k in M.RANGS)
                + f" ; ordre {'respecte' if ordre else 'VIOLE'} ; {len(gens)} licencies {licencies} ; stocks au marche "
                f"{vide} ; abandonne {abandon:.0f} ; production arretee {arret} ; {msg} ; identite {c.pire_ecart:.3f}")


# ================================================================== le chomage
def test_chomage():
    """Porte : licencier 5 mineurs par l API fait monter le chomage mesure d exactement 5 / actifs et le registre de 5 ;
    le lendemain ils n ont travaille aucune heure pendant que leurs collegues travaillaient ; en reembaucher 2 le fait
    baisser de 2. Falsificateur : un mineur prive de son lieu de travail a la main est compte chomeur mais pas inscrit
    ( non inscrits = 1 )."""
    w, p = T.monde(["economie"])
    d = p.domaine("economie")
    T.jours(w, 1)
    mine = next(c.unite for c in d.unites if c.nature == "entreprise" and c.unite.type == "mine")
    a0 = M.mesurer_chomage(p)
    gens = M.salaries(p, mine)
    partis = gens[:5]
    for h in partis: M.licencier(p, h, "economique")
    a1 = M.mesurer_chomage(p)
    monte = (a1["chomeurs"] - a0["chomeurs"] == 5 and a1["inscrits"] - a0["inscrits"] == 5
             and abs(a1["taux"] - a0["taux"] - 5 / a1["actifs"]) <= 1e-12)
    _avancer(w, 11 + 5 / 6)
    oisifs = all(h.heures_jour == 0.0 for h in partis)
    restes = [h for h in M.salaries(p, mine)]
    travail = sum(h.heures_jour for h in restes) > 0 and not any(h in M.salaries(p, mine) for h in partis)
    _avancer(w, 12 + 1 / 6)
    for h in partis[:2]: M.embaucher(p, h, mine)
    a2 = M.mesurer_chomage(p)
    baisse = a1["chomeurs"] - a2["chomeurs"] == 2 and a2["inscrits"] == a1["inscrits"] - 2
    x = restes[0]; x.travail = None
    a3 = M.mesurer_chomage(p)
    vu = a3["non_inscrits"] - a2["non_inscrits"] == 1
    ok = monte and oisifs and travail and baisse and vu
    return ok, (f"{a0['actifs']} actifs ; 5 licenciements : chomage {a0['taux']:.2%} -> {a1['taux']:.2%} ( inscrits "
                f"{a1['inscrits']} ) ; le lendemain licencies sans heure {oisifs}, collegues au travail {travail} ; 2 "
                f"reembauches : {a2['taux']:.2%} ; emploi retire a la main vu en non inscrit {vu} ; sous-emploi "
                f"{a2['sous_emploi']:.0%}")


# ================================================================== les prix
def test_prix_choc_de_demande():
    """Controle positif : deux mondes jumeaux ; dans l un, a partir du jour 5, chacun veut 3 rations par jour ( achats de
    panique ) : le prix moyen de la nourriture des jours 7 a 10 depasse d au moins 10 % celui du jumeau. Porte contre la
    chute du moteur ( indice 44 au jour 10 ) : dans le jumeau sans choc, l indice des prix de la banque centrale reste
    dans [70 ; 130] au jour 10, et la nourriture ne descend jamais sous la parite a l export ( 0,8 fois le prix mondial )."""
    def vivre(choc):
        w, p = T.monde(["economie"])
        plus_bas = math.inf
        for j in range(5):
            T.jours(w, 1); plus_bas = min(plus_bas, min(m.prix["nourriture"] for m in w.marches.values()))
        if choc: w.gouv.lois["rationnement_nourriture"] = 3.0
        T.jours(w, 1)
        prix = []
        for j in range(4):
            T.jours(w, 1)
            prix.append(np.mean([m.prix["nourriture"] for m in w.marches.values()]))
            plus_bas = min(plus_bas, min(m.prix["nourriture"] for m in w.marches.values()))
        return float(np.mean(prix)), BQ.indice_des_prix(p), plus_bas
    p0, ipc, bas = vivre(False)
    p1, _, _ = vivre(True)
    parite = M.PARITE_EXPORT * C.PRIX_MONDE["nourriture"]
    ok = p1 >= 1.10 * p0 and 70.0 <= ipc <= 130.0 and bas >= parite - 1e-9
    return ok, (f"nourriture jours 7-10 : {p0:.2f} sans choc, {p1:.2f} avec ( x{p1 / p0:.2f} ) ; indice au jour 10 "
                f"{ipc:.1f} ( le moteur seul : 44 ) ; plus bas prix de la nourriture {bas:.2f} pour une parite a "
                f"l export de {parite:.2f}")


def test_commerces_fermes():
    """Porte : avec l agenda, personne n achete le dimanche 17 juin ni le lundi 18 juin 2035 ( lundi de Pentecote
    orthodoxe, ferie grec ) : ni vente, ni acheteur ; on achete le samedi et le mardi, et la faim ne depasse pas 5 % des
    menages ces jours-la ( le garde-manger du samedi couvre deux jours fermes ). Controle : sans l agenda, on achete le
    dimanche."""
    w, p = T.monde(["economie", "agenda"])
    d = p.domaine("economie")
    faims = []
    for _ in range(5):
        T.jours(w, 1); faims.append(T.faim(w))
    s = {x[0]: x for x in d.achats_serie}
    cal = p.socle.calendrier
    fermes = cal.date(2 * C.PAS_PAR_JOUR).weekday() == 6 and cal.ferie(cal.date(3 * C.PAS_PAR_JOUR)) is not None
    w2, p2 = T.monde(["economie"])
    T.jours(w2, 3)
    s2 = {x[0]: x for x in p2.domaine("economie").achats_serie}
    ok = (fermes and all(s[j][1] == 0.0 and s[j][3] == 0 for j in (2, 3)) and s[1][1] > 0 and s[4][1] > 0
          and max(faims[1:]) <= 0.05 and s2[2][1] > 0)
    return ok, (f"samedi {s[1][1]:.0f} rations vendues ( {s[1][3]} menages avec un acheteur sur {s[1][4]} ) ; dimanche "
                f"{s[2][1]:.0f} ( {s[2][3]} acheteurs ), lundi ferie {s[3][1]:.0f} ( {s[3][3]} ) ; mardi {s[4][1]:.0f} ; "
                "faim samedi-mardi " + "/".join(f"{f:.1%}" for f in faims[1:]) + f" ; sans agenda le dimanche : {s2[2][1]:.0f}")


# ================================================================== le credit
def test_credit():
    """Porte : 1 500 habitants, 30 jours. Les depenses exceptionnelles tirees au hasard du domaine 2 ne tombent plus
    ( zero ) et sa constante est rendue intacte ; des achats durables demandent un credit ( au moins un ) ; toutes les
    demandes passent par le point de decision des banques. Controle positif : une pharmacie videe de sa caisse le mardi
    19 juin ( jour 4, le premier jour ouvre apres le lundi de Pentecote ) a midi, apres le guichet des banques, demande
    un credit de tresorerie avant la paie du soir."""
    avant = BQ.EXCEPTIONNELLE_AN
    w, p = T.monde(["economie"], echelle=3)
    d = p.domaine("economie"); bq = p.domaine("banques")
    c = next(c for c in d.unites if c.nature == "entreprise" and c.unite.type == "pharmacie")
    for j in range(30):
        if j == 4:
            _avancer(w, 6)
            p.socle.livre.payer_l_exterieur(c.unite, c.unite.caisse, "achat intrant")
            _avancer(w, 18)
        else: T.jours(w, 1)
    miens = sum(v[0] for v in d.credits.values())
    ok = (BQ.EXCEPTIONNELLE_AN == avant and bq.compte["exceptionnelles"] == 0
          and d.credits.get("achat_durable", [0])[0] >= 1 and c.credit_j == 4
          and bq.decideur.n_decisions >= miens and bq.compte["demandes"] >= miens)
    return ok, ("demandes du budget : " + ", ".join(f"{k} {v[0]} ( {v[1]} accordees, {v[2]:.0f} drachmes )"
                                                     for k, v in sorted(d.credits.items()))
                + f" ; exceptionnelles du domaine 2 : {bq.compte['exceptionnelles']} ( constante {BQ.EXCEPTIONNELLE_AN} "
                f"rendue ) ; pharmacie videe : demande le jour {c.credit_j} ; decisions de la banque {bq.decideur.n_decisions}")


def test_recalibrage():
    """Porte : a l installation, chaque menage habite a au moins son tampon ( 1, 3, 6 mois de revenu attendu selon sa
    classe ) ; l epargne versee est exactement celle que le grand livre a vue entrer de l exterieur sous son motif ; trois
    jours plus tard, les bilans des banques et de la banque centrale tiennent ( une tolerance )."""
    w, p = T.monde(["economie"])
    d = p.domaine("economie"); L = p.socle.livre
    n = len(w.menages)
    v, classe = M._tableaux_menages(p)
    rv = p.col("menage", "eco_revenu")[:n].copy()
    cible = M.tampon_vise(classe, rv)
    habites = np.nonzero((v > 0) & (p.col("menage", "dissous")[:n] == 0))[0]
    tenu = all(w.menages[i].caisse >= cible[i] - 1e-6 for i in habites)
    vu = L.jour_argent.get(("epargne_initiale", "Exterieur", "Menage"), [0.0, 0])[0]
    exact = abs(vu - d.recalibrage) <= R.tolerance(vu)
    mois = np.array([w.menages[i].caisse / max(1e-9, 30.0 * rv[i]) for i in habites if rv[i] > 0])
    T.jours(w, 3)
    pire, pire_bc, _ = BQ.verifier_bilans(p)
    ok = tenu and exact and pire <= 1.0 and pire_bc <= 1.0
    return ok, (f"{len(habites)} menages au tampon {tenu} ; epargne initiale {d.recalibrage:.0f} drachmes, vue au grand "
                f"livre {vu:.0f} ; caisses en mois de revenu : mediane {np.median(mois):.1f}, 90e centile "
                f"{np.percentile(mois, 90):.1f} ; bilans des banques {pire:.3f} et banque centrale {pire_bc:.3f} tolerance")


# ================================================================== la decision
def test_part_du_choix():
    """Porte de la decision : en mode hasard, 20 jours, toutes les entreprises decidant chaque matin, la note depend du
    choix ( part du choix >= 0,01 ) et au moins 25 decisions par jour ont ete prises ; la conservation tient."""
    w, p = T.monde(["economie"], modes={"niveau_activite": "hasard"})
    T.jours(w, 20)
    dec = p.domaine("economie").decideur
    part = dec.part_du_choix()
    notes = dec.notes_par_action()
    tenue, msg = p.socle.conservation.tenue()
    ok = part >= 0.01 and dec.n_decisions >= 20 * 25 and tenue
    return ok, (f"{dec.n_decisions} decisions ; notes : " + ", ".join(f"{a} {m:+.3f} ( {k} )" for a, (k, m) in notes.items())
                + f" ; part du choix {part:.3f} ; faim finale {T.faim(w):.1%} ; {msg}")


def test_pays_vivable():
    return T.porte_commune("economie", n_jours=12)


def test_cout():
    """Les routines propres du domaine coutent au plus 25 % d une journee du moteur seul, a 10 000 habitants."""
    def jour_moyen(avec):
        w = W.Monde(echelle=20)
        if avec: T.P.installer(w, ["economie"])
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants)
    t_e1, n = jour_moyen(False)
    t_eco, _ = jour_moyen(True)
    w, p = T.monde(["economie"], echelle=20)
    d = p.domaine("economie")
    T.jours(w, 3)
    t0 = time.perf_counter()
    for _ in range(3):
        M._regler_activite(p)
        for k in d.ids_marches: M._ajuster_prix(p, k)
        M._concurrence(p); M._credits(p); M._tresorerie_de_paie(p); M._avant_paie(p); M._apres_paie(p)
        M._achats(p); M._cloturer(p)
    propre = (time.perf_counter() - t0) / 3
    ok = propre <= 0.25 * t_e1
    return ok, (f"{n} habitants : moteur seul {t_e1:.2f} s par jour, avec population, banques et economie {t_eco:.2f} s ; "
                f"routines propres du domaine {propre * 1000:.0f} ms par jour ( {propre / t_e1:.0%} du moteur ), "
                f"{propre / n * 1e6:.1f} us par habitant")


TESTS = [test_budget_parts, test_identite_comptable, test_faillite, test_chomage, test_prix_choc_de_demande,
         test_commerces_fermes, test_credit, test_recalibrage, test_part_du_choix, test_pays_vivable, test_cout]
