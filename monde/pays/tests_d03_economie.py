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


def test_services_marchands_et_usure():
    """Porte ( HMT-126, seuils ecrits avant la mesure ). Fonction pure : trois menages, deux divisions ( habillement,
    restauration ), parts marchandes 1 et 0,5 : l envie vaut 30 x 1 + 20 x 0,5 = 40 drachmes par jour, 80 pour deux jours ;
    bornee a la caisse moins son plancher ( 200 - 150 = 50 ; 100 - 150 : rien ) ; rien pour qui ne fait pas
    ses courses. Controle positif, le pays : seul le domaine 3 installe ( aucun fournisseur de logement, de loisirs, de
    restauration ), tout le budget non servi est marchand ( parts 1 ) ; un jour ouvre, les menages achetent des biens et
    services marchands, le commerce reverse a l Etat exactement ttc x t / ( 1 + t ) de TVA, et aucun menage qui en achete ne
    descend sous sa semaine de nourriture ni sous son tampon de precaution ( sur son revenu permanent ) ; l equipement d un menage qui ne renouvelle pas perd 1 / 3 650 de sa valeur par
    jour. Falsificateurs : avec les domaines fournisseurs, la part marchande de la restauration est 0,5, celle du
    logement 0, celle de l habillement 1 ; un menage ramene a sa semaine de nourriture n achete rien de marchand."""
    att = np.zeros((3, M.K)); ih, ir = M.NOMS_CATEGORIES.index("habillement"), M.NOMS_CATEGORIES.index("restauration")
    att[:, ih] = 30.0; att[:, ir] = 20.0
    pm = np.zeros(M.K); pm[ih] = 1.0; pm[ir] = 0.5
    voulu, ttc = M.achats_marchands(att, pm, np.array([2.0, 1.0, 1.0]), np.array([True, True, False]),
                                    np.array([200.0, 100.0, 500.0]), np.array([150.0, 150.0, 150.0]))
    pur = list(voulu) == [80.0, 40.0, 0.0] and list(ttc) == [50.0, 0.0, 0.0]
    w, p = T.monde(["economie"])
    d = p.domaine("economie"); L = p.socle.livre; g = w.gouv
    T.jours(w, 3)                                         # le 18 juin 2035, un lundi
    _avancer(w, 12)                                       # 18 h : la paie est passee
    n = len(w.menages); v, _ = M._tableaux_menages(p)
    ok_m = (v > 0) & (p.col("menage", "dissous")[:n] == 0)
    reserve = M.reserve_alimentaire(p)
    ids = np.nonzero(ok_m)[0]
    pauvre = int(ids[0])
    L.transferer(w.menages[pauvre], g, max(0.0, w.menages[pauvre].caisse - float(reserve[pauvre])), "amende")
    E = p.col("menage", "eco_equipement"); E0 = E[:n].copy(); r0 = p.col("menage", "eco_dernier_achat")[:n].copy()
    par = {}

    class Espion:                                         # qui paie quoi au marche sous le motif marchand ( lecture seule )
        def __init__(self, suivant): self.suivant = suivant
        def argent(self, motif, de, vers, montant):
            if self.suivant is not None: self.suivant.argent(motif, de, vers, montant)
            if motif == "services_marchands": par[de.id] = par.get(de.id, 0.0) + montant
        def bien(self, *a):
            if self.suivant is not None: self.suivant.bien(*a)
    ancien = getattr(L, "enregistreur", None); L.enregistreur = Espion(ancien)
    t0 = L.jour_argent.get(("tva", "Marche", "Gouvernement"), (0.0, 0))[0]
    _avancer(w, 1 + 1 / 6)                                # 19 h 10 : les achats sont passes
    L.enregistreur = ancien
    tva = L.jour_argent.get(("tva", "Marche", "Gouvernement"), (0.0, 0))[0] - t0
    vendu = math.fsum(par.values())
    res = M.reserve_alimentaire(p)
    _, classe = M._tableaux_menages(p)
    tam = M.tampon_vise(classe, M._revenu_long(p, n))
    garde = all(w.menages[i].caisse >= max(res[i], tam[i]) - 1e-6 for i in par)
    pm0 = M.parts_marchandes(p)
    seul = all(pm0[M.NOMS_CATEGORIES.index(x)] == 1.0 for x in ("logement", "restauration", "loisirs", "habillement"))
    renouvele = p.col("menage", "eco_equipement")[:n] > E0 * (1.0 - 1.0 / 3650.0) + 1e-9
    stables = [i for i in ids.tolist() if not renouvele[i] and E0[i] > 0]
    usure = len(stables) > 10 and all(abs(E[i] - E0[i] * (1.0 - 1.0 / 3650.0)) <= 1e-9 * E0[i] for i in stables)
    tva_ok = vendu > 0 and abs(tva - vendu * g.tva / (1.0 + g.tva)) <= 1e-6 * max(1.0, vendu)

    class _P:
        def a(self, x): return x in ("culture", "immobilier", "energie", "services_publics", "assurances", "medecine",
                                     "hopitaux", "transport", "medias", "education")
    pm2 = M.parts_marchandes(_P())
    fournis = (pm2[ir] == 0.5 and pm2[M.NOMS_CATEGORIES.index("logement")] == 0.0 and pm2[ih] == 1.0)
    rien_pauvre = pauvre not in par
    tenue, msg = p.socle.conservation.tenue()
    ok = pur and seul and tva_ok and garde and usure and fournis and rien_pauvre and len(par) >= 50 and tenue
    return ok, (f"fonction pure {pur} ; seul le domaine 3 : {len(par)} menages achetent {vendu:.0f} drachmes de biens et services "
                f"marchands, TVA reversee {tva:.4f} ( attendu {vendu * g.tva / (1.0 + g.tva):.4f} ), semaine de nourriture "
                f"gardee {garde} ; usure d un jour sur {len(stables)} menages {usure} ; menage a sa reserve : rien {rien_pauvre} ; "
                f"avec les fournisseurs : restauration {pm2[ir]}, logement {pm2[M.NOMS_CATEGORIES.index('logement')]}, habillement "
                f"{pm2[ih]} ; {msg}")


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
        if j == 11 and K_.actives.get(c1.id) is c1: K_.regler(c1, L)     # ( 28/09 : l entreprise a pu la regler elle-meme )
        if j == 12: c2 = K_.constater(ma, e, 80.0, "achat intrant", p.jour)
        if j == 13 and K_.actives.get(c2.id) is c2: K_.abandonner(c2, "remise")
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


def test_gerance_et_cessation():
    """HMT-139, ecrite avant la mesure. GERANCE : une entreprise a patron, caisse de 10 000 au-dela d une semaine de salaires, aucun salaire en retard, paie
    a son patron exactement la gerance du jour ( 3 521 euros par mois / 1,15 / 30 ), dont l impot sur le revenu va a l
    Etat ; avec un arriere de salaire, rien ; avec 50 drachmes au-dela de la semaine de salaires, 50. CESSATION ( loi 4738/2020 ) : un arriere de
    salaire ne il y a 181 jours, au-dela de 30 000 euros et de 40 % des dettes, fait liquider l entreprise a la cloture,
    motif cessation_des_paiements, et son patron entre au registre des chomeurs ; controles : le meme ne il y a 179 jours,
    ou sous 30 000 euros, ou sous 40 % des dettes ( une dette recente plus grosse ), ne la fait pas tomber ; une ferme cooperative non plus. Conservation."""
    w, p = T.monde(["economie"]); T.jours(w, 1)
    d = p.domaine("economie"); K_ = p.socle.creances; g = w.gouv
    ents = [c for c in d.unites if c.nature == "entreprise" and d.proprietaires.get(c.id) is not None and not c.liquidee]
    jour = M.GERANCE_EUROS_MOIS / M._euros_par_drachme() / M.MOIS_J
    c0 = ents[0]; e0 = c0.unite; h0 = d.proprietaires[c0.id]
    # 1. gerance entiere
    def payer_seul(c):
        garde = {x.id: d.proprietaires.pop(x.id) for x in ents if x is not c and x.id in d.proprietaires}
        try:
            av_m, av_g, av_e = h0.menage.caisse, g.caisse, c.unite.caisse
            M._gerance(p, d)
            return c.unite.caisse, av_e - c.unite.caisse, h0.menage.caisse - av_m, g.caisse - av_g
        finally: d.proprietaires.update(garde)
    L = p.socle.livre
    plein = 10000.0 + M.RESERVE_REGLEMENT_J * c0.salaires_lisses       # la gerance se paie au-dela d une semaine de salaires
    if e0.caisse < plein: L.transferer(w.gouv, e0, plein - e0.caisse, "apport_capital")
    _, verse, net, impot = payer_seul(c0)
    entier = abs(verse - jour) < 1e-9 and abs(net - jour * (1 - g.impot_revenu)) < 1e-9 and abs(impot - verse * g.impot_revenu) < 1e-6
    # 2. avec un arriere de salaire : rien
    creancier = next(m for m in w.menages if m is not h0.menage)
    cr = K_.constater(creancier, e0, 100.0, "salaire", p.jour)
    _, verse2, _, _ = payer_seul(c0)
    K_.abandonner(cr, "test")
    # 3. caisse de 50 : 50
    L.transferer(e0, w.gouv, e0.caisse - 50.0 - M.RESERVE_REGLEMENT_J * c0.salaires_lisses, "impot")
    _, verse3, _, _ = payer_seul(c0)
    gerance = entier and verse2 == 0.0 and abs(verse3 - 50.0) < 1e-9
    # 4. cessation des paiements
    seuil = M.SEUIL_CESSATION_EUROS / M._euros_par_drachme()
    def essai(age, montant, recente=0.0):
        w2, p2 = T.monde(["economie"]); T.jours(w2, 1)
        d2 = p2.domaine("economie"); K2 = p2.socle.creances
        c = next(x for x in d2.unites if x.nature == "entreprise" and d2.proprietaires.get(x.id) is not None)
        h = d2.proprietaires[c.id]
        cr = next(m for m in w2.menages if m is not h.menage)
        K2.constater(cr, c.unite, montant, "salaire", p2.jour - age)
        if recente > 0: K2.constater(cr, c.unite, recente, "fournisseur", p2.jour)
        garde = M.PRESOMPTION_CESSATION; M.PRESOMPTION_CESSATION = True      # le mecanisme, eprouve meme suspendu
        try: M._faillites(p2, d2)
        finally: M.PRESOMPTION_CESSATION = garde
        chom = h.id in d2.chomeurs and d2.chomeurs[h.id][3] == "faillite_de_son_entreprise"
        return c.liquidee, chom and c.id not in d2.proprietaires, p2.socle.conservation.tenue()[0]
    tombe, chomeur, tenue = essai(181, seuil * 1.01)
    jeune = essai(179, seuil * 1.01)[0]
    petit = essai(181, seuil * 0.99)[0]
    minoritaire = essai(181, seuil * 1.01, recente=seuil * 2.0)[0]
    # une ferme cooperative ( domaine 9 ) aux vieux arrieres n est pas liquidee : ses exploitants continuent de cultiver
    w3, p3 = T.monde(["economie"]); T.jours(w3, 1); d3 = p3.domaine("economie")
    cf = next((x for x in d3.unites if x.nature == "entreprise" and x.unite.type == "ferme"), None)
    ferme_tient = True
    if cf is not None:
        p3.socle.creances.constater(w3.gouv, cf.unite, seuil * 2.0, "tva", p3.jour - 200)
        garde = M.PRESOMPTION_CESSATION; M.PRESOMPTION_CESSATION = True
        try: M._faillites(p3, d3)
        finally: M.PRESOMPTION_CESSATION = garde
        ferme_tient = not cf.liquidee
    tenue0 = p.socle.conservation.tenue()[0]
    # suspendue ( 29/09 ) : dans le monde, la presomption ne liquide pas
    w4, p4 = T.monde(["economie"]); T.jours(w4, 1); d4 = p4.domaine("economie")
    c4 = next(x for x in d4.unites if x.nature == "entreprise" and d4.proprietaires.get(x.id) is not None)
    p4.socle.creances.constater(next(m for m in w4.menages), c4.unite, seuil * 1.5, "salaire", p4.jour - 200)
    M._faillites(p4, d4); suspendue = (not M.PRESOMPTION_CESSATION) and not c4.liquidee
    ok = gerance and tombe and chomeur and not jeune and not petit and not minoritaire and ferme_tient and suspendue and tenue and tenue0
    return ok, (f"gerance : du jour {jour:.2f} dr, versee {verse:.2f}, net au menage {net:.2f}, impot {impot:.2f} ; avec un "
                f"arriere de salaire {verse2:.2f} ; caisse de 50 : {verse3:.2f} | cessation : 181 j et {seuil * 1.01:.0f} dr -> "
                f"liquidee {tombe}, patron chomeur {chomeur} ; 179 j -> {jeune} ; sous le seuil -> {petit} ; sous 40 % -> "
                f"{minoritaire} ; ferme aux vieux arrieres epargnee {ferme_tient} ; presomption suspendue dans le monde {suspendue} ; conservation {tenue and tenue0}")



def test_plancher_sans_revenu():
    """Porte ( HMT-126 e, seuils ecrits avant la mesure ) : le plancher des depenses que l on peut remettre vaut 7 jours de
    nourriture pour un menage dont le revenu lisse couvre sa nourriture d un jour, JOURS_SANS_REVENU ( 90 ) sinon, a 1e-9.
    Controle positif : un menage sans revenu qui a 30 jours de nourriture en caisse achete sa nourriture le soir mais
    aucun bien ou service marchand, aucun equipement. Falsificateur : le meme soir, un menage aise avec un revenu en
    achete ; et le plancher d un menage au revenu suffisant reste a 7 jours."""
    w, p = T.monde(["economie"])
    L = p.socle.livre; cm = p.colonnes["menage"]
    T.jours(w, 3); _avancer(w, 12)                         # 18 h
    jour = M.reserve_alimentaire(p, 1)
    ids = [k for k in range(len(w.menages)) if jour[k] > 0]
    A, B = ids[0], ids[1]
    M.revenu_recent(p, len(w.menages))                 # le revenu qui decide : celui des 30 derniers jours
    for k, r in ((A, 0.0), (B, 10.0 * jour[B])): cm["eco_revenu_30"][k] = r; cm["eco_revenu_30_n"][k] = 30
    pl = M.plancher_discretionnaire(p)
    valeurs = abs(pl[A] - M.JOURS_SANS_REVENU * jour[A]) <= 1e-9 * pl[A] and abs(pl[B] - M.RESERVE_ALIMENTAIRE_J * jour[B]) <= 1e-9 * pl[B]
    mA, mB = w.menages[A], w.menages[B]
    if mA.caisse > 30.0 * jour[A]: L.transferer(mA, w.gouv, mA.caisse - 30.0 * jour[A], "amende")
    else: L.recevoir_de_l_exterieur(mA, 30.0 * jour[A] - mA.caisse, "epargne_initiale")
    L.recevoir_de_l_exterieur(mB, 100000.0, "epargne_initiale")
    par = {}

    class Espion:
        def __init__(self, suivant): self.suivant = suivant
        def argent(self, motif, de, vers, montant):
            if self.suivant is not None: self.suivant.argent(motif, de, vers, montant)
            if type(de).__name__ == "Menage": par[(de.id, motif)] = par.get((de.id, motif), 0.0) + montant
        def bien(self, *a):
            if self.suivant is not None: self.suivant.bien(*a)
    ancien = getattr(L, "enregistreur", None); L.enregistreur = Espion(ancien)
    _avancer(w, 1 + 1 / 6)                                 # 19 h 10 : les achats sont passes
    L.enregistreur = ancien
    a_nourri = par.get((A, "nourriture"), 0.0) > 0.0
    a_rien = par.get((A, "services_marchands"), 0.0) == 0.0 and par.get((A, "outils"), 0.0) == 0.0
    b_achete = par.get((B, "services_marchands"), 0.0) > 0.0
    tenue, msg = p.socle.conservation.tenue()
    ok = valeurs and a_nourri and a_rien and b_achete and tenue
    return ok, (f"plancher sans revenu {pl[A] / jour[A]:.0f} jours, avec revenu {pl[B] / jour[B]:.0f} jours ; sans revenu, 30 jours "
                f"en caisse : nourriture {par.get((A, 'nourriture'), 0.0):.2f}, marchand {par.get((A, 'services_marchands'), 0.0):.2f}, "
                f"equipement {par.get((A, 'outils'), 0.0):.2f} ; menage aise : marchand {par.get((B, 'services_marchands'), 0.0):.2f} ; {msg}")

def test_transmission_nourriture():
    """Porte de construction ( 29/09, HMT-140, ecrite avant la mesure ) : le cours mondial lisse force a +10 % de son
    niveau de depart, la reference de la nourriture monte de 1,4 % ( s = 0,14, a 1e-9 pres ) et celle du gazole de 10 %
    ( transmission entiere, inchangee ). Controle positif : sans PART_MATIERES ( l ancienne formule ), la nourriture
    monte de 10 % et la porte echoue."""
    w, p = T.monde(["economie"])
    d = p.domaine("economie"); mid = sorted(w.marches)[0]; em = d.marches[mid]; m = w.marches[mid]
    orig, part0 = M._prix_mondial_du_jour, dict(M.PART_MATIERES)
    def ref(b, parts):
        M.PART_MATIERES.clear(); M.PART_MATIERES.update(parts)
        em.prix_ref = {b: [4.0, 2.0, 2.2]}                    # prix d installation, cours d alors, cours lisse a +10 %
        M._prix_mondial_du_jour = lambda w_, b_: 2.2           # le cours du jour a +10 % : le lisse n en bouge pas
        try: return M._prix_de_reference(p, em, m, b) / 4.0 - 1.0
        finally: M._prix_mondial_du_jour = orig; M.PART_MATIERES.clear(); M.PART_MATIERES.update(part0)
    n, g, n0 = ref("nourriture", part0), ref("carburant", part0), ref("nourriture", {})
    juge = lambda x: abs(x - 0.014) <= 1e-9
    ok = juge(n) and abs(g - 0.10) <= 1e-9 and not juge(n0)
    return ok, (f"cours a +10 % : reference de la nourriture {n:+.4%} ( attendu +1,40 % ), du gazole {g:+.4%} ( +10 % ) ; "
                f"ancienne formule : nourriture {n0:+.4%}, porte {'passe ( FAUX )' if juge(n0) else 'echoue ( attendu )'}")


TESTS = [test_budget_parts, test_services_marchands_et_usure, test_identite_comptable, test_faillite, test_chomage, test_prix_choc_de_demande,
         test_commerces_fermes, test_credit, test_recalibrage, test_part_du_choix, test_pays_vivable, test_cout, test_plancher_sans_revenu, test_gerance_et_cessation, test_transmission_nourriture]
