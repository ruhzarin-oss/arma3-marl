"""DOMAINE 3 - ECONOMIE REELLE : BUDGET DES MENAGES, ENTREPRISES, MARCHES ET PRIX, CHOMAGE.

FICHE
1. Classes. Categorie ( une division COICOP du budget : part ELSTAT, bien du catalogue qui en sert une partie, domaine
   qui servira le reste ), EtatMarche ( ce que le marchand sait de son marche : demande effective lissee, ruptures,
   demande non solvable, couverture, ventes aux menages ), Comptes ( bilan et compte de resultat d une unite : entreprise
   du moteur ou marche ), ContexteActivite, RemplaceAchats, RemplaceRegler, AjusterPrix ( les methodes du moteur
   reprises, en objets picklables ), Economie ( l etat du domaine ). Colonnes par menage : eco_revenu ( revenu lisse,
   drachmes par jour ), eco_equipement ( valeur des biens durables ), eco_epargne_forcee ( ce qu il voulait depenser et
   que rien ne sert ), eco_credit_j, eco_dernier_achat. Tables eparses : proprietaires ( entreprise -> habitant ),
   chomeurs ( habitant -> jour, ancien employeur, metier, motif ), offres ( unite -> postes ). Aucune classe du moteur
   n est modifiee.
2. Invariants. Le domaine ne DETIENT ni argent ni bien : il tient les comptes d unites du moteur. Tout paiement passe
   par le grand livre ; les biens vendus aux menages quittent le marche et sont consommes ( livre.flux["consomme"] ) ;
   une liquidation deplace les stocks de l entreprise au marche ( deplacement entre detenteurs inscrits ). Chaque
   soir, pour chaque unite : actif ( tresorerie + stocks valorises + capital fixe net + creances ) = dettes ( prets
   bancaires, principal et interets echus + creances du socle dont elle est debitrice ) + capitaux propres, les capitaux
   propres etant PORTES par le compte de resultat ( jamais recalcules comme un reste ) : resultat = variation des
   capitaux propres + distributions - apports - reevaluations. Par classe ( Entreprise, Marche ), les flux ecrits dans
   les comptes ( credit, principal, interets, distributions, exploitation ) = ce que le grand livre a vu passer, motif
   par motif ; les ventes au port que le moteur ecrit a la main pour les marches sont retirees ; tout autre paiement
   ecrit a la main se voit la.
3. Decision `niveau_activite` ( chaque entreprise du moteur, chaque matin a l aube : 27 fermes et 8 sites decident le
   meme jour ) : arret, quart, moitie, trois quarts, plein. Traits : couverture de son produit au marche de sa region,
   manque ( faim de la region pour la nourriture, ruptures pour le reste ), marge unitaire, prix sur prix mondial,
   tresorerie, intrants, activite d hier, tendance du stock. Note ( horizon 3 jours ) : chaque jour, la production de
   CETTE entreprise ( part de sa capacite ) multipliee par ( besoin de SA region + 0,5 x SA marge unitaire ) : produire
   vaut ce qui manque la ou elle livre, plus ce qu elle y gagne ; jamais la faim nationale, jamais le profit seul.
   Regle : plein si la region a faim ou si le stock tombe sous la moitie de sa cible ; un cran de moins si le prix ne
   couvre plus le cout variable ou si le stock depasse deux fois la cible ; un cran de plus sous la cible. Temoin :
   toujours plein. Centrales ( le reseau ) et mine d or ( prix mondial ) gardent leur logique du moteur. Une entreprise
   a plein regime dont la region manque encore publie des offres d emploi ( domaine 4 ).
4. Evenements. Individuels : faillite, licenciement, embauche. Comptes : achat_menages, rupture_de_stock,
   demande_en_attente, achat_durable, credit_economie, dividende_verse.
5. Liens. Lit la population ( ages, menages dissous ), les banques ( prets, taux ), l agenda s il est installe
   ( `tours_du_jour` : seul achete le menage dont un membre fait les courses ; dimanche et feries, tout est ferme ), la
   faim par region ( moteur ). Paie et recoit : achats des menages ( nourriture, carburant, remedes, outils ) et leur
   TVA ( avec la fraude du moteur ), dividendes ( entreprise -> patron, fin de mois ), cessions de liquidation
   ( marche -> entreprise ), creanciers d une faillite, boni ( -> proprietaire ), epargne initiale ( exterieur ->
   menages, a l installation : les caisses du moteur ne valaient que deux semaines de revenu ). Remplace Monde.achats,
   Monde.regler_activite et Marche.ajuster_prix ; garde Monde.repas ( il lit w.faim_region ) ; porte la marge du
   detaillant de 10 a 25 % ( Marche.marge, une donnee ) ; neutralise par une donnee le dividende quotidien du moteur
   ( Entreprise.proprietaire = None, le proprietaire passe dans sa table ). Credit : suspend EXCEPTIONNELLE_AN du
   domaine 2 le temps de son guichet ( 9 h ) et le remplace par de vraies raisons, toutes instruites par le point de
   decision des banques ( `demander_credit` ) : achat durable et decouvert des menages ( 9 h 30, jours ouvres ),
   tresorerie de paie des entreprises ( 17 h 40, jours ouvres ). Donne aux autres ( API en fin de fichier ) :
   embaucher, licencier, salaries, masse_salariale, offres_d_emploi, offres_services, chomage, mesurer_chomage,
   comptes, bilan, compte_de_resultat, assiette_tva, assiette_is, investir, apporter, reevaluer_capital, liquider,
   prix_producteur, cout_unitaire, demande_en_attente, budget_des_menages, ecarts_grand_livre, exterieur_hors_livre.
6. Portes : tests_d03_economie.py.
7. Arma : aucun objet ( un commerce ou une usine sont des batiments, domaine 13 ).
8. Cout. Achats : une passe vectorisee sur les menages, deux paiements par achat ; prix : 9 biens par marche et la
   concurrence entre marches ; comptes : une passe sur les unites ( 51 sur Altis ) et sur les creances ; chomage : une
   passe sur les habitants. Mesure du 23/09 ( test_cout, 10 000 habitants ) : 35 a 45 ms par jour, 2 % d une journee
   du moteur, 4 us par habitant, lineaire en menages : ~ 4 s par jour a 1 million, 3,5 minutes a 50 millions."""
import datetime as dt, importlib, math
from collections import deque
import numpy as np
from .. import config as C, population as PO, roles as RO
from ..socle import decision as D, registre as R
from . import d01_population as POP, d02_banques as BQ

JOURS_AN = 365.0
MOIS_J = 30
EPS = 1e-9
PM = C.PRIX_MONDE

# ================================================================== le budget des menages ( COICOP )
# Parts de la depense de consommation des menages grecs : ELSTAT, Household Budget Survey 2023 ( communique du
# 27/09/2024 ) : alimentation 20,7 %, alcool et tabac 3,4, habillement 4,7, logement 14,1, equipement ( biens
# durables ) 4,4, sante 7,7, transport 13,1, communications 4,2, loisirs 4,4, education 3,4, restaurants et hotels 11,4,
# divers 8,4 ( somme 99,9 : l arrondi d ELSTAT ). Les 20 % de menages qui depensent le moins consacrent 55,8 % de leur
# budget a l alimentation et au logement, les 20 % qui depensent le plus 24,8 %.
# part_bien : la part de la division que sert un bien qui existe deja. Medicaments dans la sante : 0,40 ; carburants
# dans le transport : 0,35 ( ordres de grandeur des sous-postes de l enquete, a calibrer ).
# Ce que rien ne sert encore reste DEMANDE EN ATTENTE : l argent reste au menage ( epargne forcee, mesuree par
# division et par region ) et le domaine qui servira la division herite d une demande chiffree. Pourquoi pas un
# secteur de services generique qui paie du travail : le moteur n a aucun salarie des services ( ses 500 roles sont
# fixes ), la paie appartient au domaine 4, et verser ces depenses au marche les aurait toutes donnees aux 20
# marchands ( benefice marchand du moteur ). Restaurants et divers ( 20 % ) n ont pas de domaine : ils reviennent a
# l economie avec le travail ( services marchands ) - `offres_services` chiffre deja les emplois qu ils paieraient.
class Categorie:
    """Une division COICOP du budget.
      part         part de la division dans la depense de consommation ( ELSTAT 2023 )
      bien         le bien du catalogue qui en sert une partie, ou None
      part_bien    la part de la division que ce bien sert ; le reste attend son domaine
      fournisseur  le ou les domaines qui serviront le reste"""
    __slots__ = ("nom", "coicop", "part", "bien", "part_bien", "fournisseur")

    def __init__(self, nom, coicop, part, bien, part_bien, fournisseur):
        if not 0.0 < part < 1.0: raise ValueError(f"{nom} : part hors ]0 ; 1[ : {part!r}")
        if bien is not None and bien not in C.BIENS: raise ValueError(f"{nom} : bien inconnu {bien!r}")
        if not 0.0 <= part_bien <= 1.0 or (bien is None) != (part_bien == 0.0):
            raise ValueError(f"{nom} : un bien sans part, ou une part sans bien")
        self.nom, self.coicop, self.part, self.bien, self.part_bien, self.fournisseur = nom, coicop, part, bien, part_bien, fournisseur


CATEGORIES = (
    Categorie("alimentation", "01", 0.207, "nourriture", 1.0, "economie ( marches )"),
    Categorie("alcool_tabac", "02", 0.034, None, 0.0, "agriculture, industrie"),
    Categorie("habillement", "03", 0.047, None, 0.0, "industrie, exterieur"),
    Categorie("logement", "04", 0.141, None, 0.0, "immobilier ( loyers ), energie, services_publics ( eau )"),
    Categorie("equipement", "05", 0.044, "outils", 1.0, "industrie"),
    Categorie("sante", "06", 0.077, "remedes", 0.40, "medecine, hopitaux"),
    Categorie("transport", "07", 0.131, "carburant", 0.35, "transport"),
    Categorie("communications", "08", 0.042, None, 0.0, "medias"),
    Categorie("loisirs", "09", 0.044, None, 0.0, "culture"),
    Categorie("education", "10", 0.034, None, 0.0, "education"),
    Categorie("restauration", "11", 0.114, None, 0.0, "economie ( services marchands, avec le travail )"),
    Categorie("divers", "12", 0.084, None, 0.0, "assurances, banques, services marchands"),
)
K = len(CATEGORIES)
NOMS_CATEGORIES = tuple(c.nom for c in CATEGORIES)
I_ALIM, I_EQUIP, I_SANTE, I_TRANSPORT = (NOMS_CATEGORIES.index(x) for x in ("alimentation", "equipement", "sante", "transport"))
PARTS_ELSTAT = np.array([c.part for c in CATEGORIES])
PARTS = PARTS_ELSTAT / PARTS_ELSTAT.sum()
PART_BIEN = np.array([c.part_bien for c in CATEGORIES])
PARTS_HORS_ALIM = PARTS.copy(); PARTS_HORS_ALIM[I_ALIM] = 0.0; PARTS_HORS_ALIM /= PARTS_HORS_ALIM.sum()
BIENS_COURANTS = ((I_TRANSPORT, "carburant"), (I_SANTE, "remedes"))   # achetes au fil des jours ; les durables a part

# La regle de consommation ( epargne de precaution : Deaton 1991, Carroll 1997 ) : le menage vise un TAMPON de
# tresorerie, en mois de revenu lisse ; il consomme son revenu lisse, plus ( ou moins ) l ecart a son tampon etale sur
# AJUSTEMENT_J jours. Tampons : ordre de grandeur de l enquete HFCS de la BCE pour la Grece ( depots medians de un a
# deux mois de revenu, moyens de plusieurs mois, tres concentres chez les aises ) - a calibrer.
TAMPON_MOIS = {"populaire": 1.0, "moyenne": 3.0, "aisee": 6.0}
CLASSES = {"populaire": 0, "moyenne": 1, "aisee": 2}
CLASSE_DU_MOTEUR = np.array([CLASSES.get(c, 0) for c in PO.CLASSES], np.int64)
NOMS_CLASSES = ("populaire", "moyenne", "aisee")
EPARGNE_STRUCTURELLE = 0.0      # taux d epargne brut des menages grecs proche de zero ou negatif depuis 2012 ( Eurostat, a calibrer )
AJUSTEMENT_J = 90.0             # un exces ou un manque de tampon se resorbe en trois mois ( a calibrer )
ALPHA_REVENU = 1.0 / 60.0       # revenu lisse : moyenne mobile de 60 jours de ce que la paie ( et les dividendes ) apportent
PRECAUTION_J = 0.5              # le garde-manger vise le besoin jusqu aux prochaines courses, plus une demi-journee
JOUR_SANS_ACHETEUR_J = 1.0      # avec l agenda, un jour sans acheteur peut arriver : un jour de plus en reserve
RESERVE_ALIMENTAIRE_J = 7       # aucun achat non alimentaire ne descend la caisse sous 7 jours de nourriture
JOURS_ACHAT_MAX = 3             # qui n a pas pu faire ses courses rattrape au plus 3 jours de depenses courantes
# Biens durables ( COICOP 05 ) : un stock d equipement qui s use ; le menage le renouvelle d un coup quand il tombe sous
# 80 % de sa cible : c est l ACHAT DURABLE, la premiere vraie raison d emprunter.
DUREE_VIE_EQUIPEMENT_AN = 10.0  # gros electromenager, mobilier : 10 a 12 ans ( a calibrer )
SEUIL_RENOUVELLEMENT = 0.8
EFFORT_MAX_DURABLE = 0.15       # mensualite d un credit durable au plus 15 % du revenu mensuel ( a calibrer )
DUREE_CREDIT_DURABLE = 24       # mois
DELAI_CREDIT_J = 30             # une demande par mois au plus, par menage ou par entreprise
DECOUVERT_HORIZON_J = 7         # le decouvert : les mensualites qui tombent dans la semaine et que la caisse ne couvre pas
TRESORERIE_BESOIN_J = 10        # une entreprise qui ne peut pas payer la paie du jour demande 10 jours de salaires
DUREE_CREDIT_TRESORERIE = 3     # mois
# Revenu attendu par metier, pour la premiere estimation du revenu lisse ( drachmes par jour, avant l impot ) : le salaire
# horaire du moteur fois 8 heures ; paysan : 1,2 ration par heure payee au prix de parite a l export moins la marge du
# detaillant ; marchand et patron : a calibrer sur leur benefice.
REVENU_MARCHAND_J = 30.0
REVENU_PATRON_J = 60.0

# ================================================================== les marches et les prix
# Marge brute du commerce de detail alimentaire : ~ 25 % ( ordre de grandeur des supermarches grecs, a calibrer ). Le
# moteur en prenait 10 %.
MARGE_DETAIL = 0.25
# Couverture visee : jours de demande que le marchand garde en stock. Le moteur exporte la nourriture au-dela de 3 jours :
# la cible est en dessous, pour qu un marche qui exporte tende vers la parite a l export.
COUVERTURE_CIBLE_J = {"nourriture": 2.0, "carburant": 5.0, "remedes": 10.0, "outils": 10.0, "fer": 5.0, "zinc": 5.0,
                      "petrole": 5.0}
BIENS_PRIX = tuple(COUVERTURE_CIBLE_J)
KAPPA_PRIX = 0.08               # au plus 8 % de hausse ou de baisse par jour sur l ecart de stock ( a calibrer )
BETA_COUT = 0.05                # rappel vers le prix de revient des producteurs de la region, par jour
ALPHA_DEMANDE = 0.25            # demande lissee sur ~ 4 jours
DEMANDE_MIN = 0.1               # unites par jour : sous ce plancher, personne ne demande
PLANCHER, PLAFOND = 0.25, 2.5   # bornes en prix mondial ( au-dela : importation, domaine 7 ; en deca : personne ne vend )
PARITE_EXPORT = 0.8             # le moteur exporte les surplus de nourriture a 0,8 fois le prix mondial ( monde.py, expedier )
MARGE_PRODUCTEUR = 0.10         # marge d un producteur sur son prix de revient complet ( a calibrer )
MARGE_COMMERCE = 0.05           # la regle de commerce du moteur exige 5 % de gain au-dela du transport ( monde.py, commerce_regle )
ARBITRAGE_AU_DELA = 1.03        # la borne haute de la concurrence laisse passer l arbitrage ( 3 % au-dessus de son seuil )

# ================================================================== les entreprises
# Capital fixe brut par poste de travail, en drachmes, et duree d amortissement en annees : ordre de grandeur du stock de
# capital net par emploi des comptes nationaux grecs ( industrie lourde et energie de 5 a 7 ans de salaire, agriculture
# hors terres un an ), ramene au salaire du moteur ( 8 drachmes de l heure ) - a calibrer. Le capital est a mi-vie au depart.
CAPITAL_PAR_POSTE = {"ferme": (8000.0, 15), "mine": (60000.0, 20), "carriere": (40000.0, 20), "puits": (80000.0, 25),
                     "raffinerie": (120000.0, 25), "centrale": (150000.0, 30), "fonderie": (60000.0, 20),
                     "pharmacie": (60000.0, 15)}
CAPITAL_MARCHE_PAR_POSTE = (20000.0, 20)
AMORTI_AU_DEPART = 0.4
PART_DISTRIBUEE = 0.5           # dividende : la moitie du resultat du mois ( a calibrer )
RESERVE_TRESORERIE_J = 30       # ... sans descendre la caisse sous un mois de salaires
# Faillite : capitaux propres negatifs ET tresorerie nulle ( caisse videe par la paie de 18 h ) trois soirs de suite -
# la cessation des paiements constatee ( a calibrer ). Liquidation : stocks cedes au marche de la region a moitie de leur
# valeur, capital fixe mis au rebut, creanciers payes dans l ordre legal : salaries, Etat, banques, fournisseurs ; a
# rang egal au marc le franc ; le reste abandonne ; le boni au proprietaire.
SEUIL_TRESORERIE_NULLE = 1.0
JOURS_CESSATION = 3
DECOTE_LIQUIDATION = 0.5
INDEMNITE_JOURS = 15            # indemnite de licenciement : loi 4093/2012, ouvriers 7 a 105 jours de salaire selon
                                # l anciennete, employes 2 a 12 mois ; l anciennete n est pas modelisee ( a calibrer )
RANGS = ("salaries", "etat", "banques", "fournisseurs")
MOTIFS_SALARIES = ("salaire", "salaire public", "indemnite_licenciement")

# ================================================================== la decision
ACTIVITES = (0.0, 0.25, 0.5, 0.75, 1.0)
NOMS_ACTIVITES = ("arret", "quart", "moitie", "trois_quarts", "plein")
HORIZON_ACTIVITE = 3            # la production du jour arrive au marche le jour meme ou le lendemain ; la couverture et la
                                # faim de la region repondent en un a trois jours
POIDS_MARGE = 0.5
MANQUE_URGENCE = 0.05
BONUS = 1.0 + C.BONUS_OUTILS

GROUPES_MOTIFS = {"credit": "credit", "remboursement_principal": "principal", "interet_pret": "interet",
                  "dividende": "distributions", "boni_liquidation": "distributions"}
CLASSES_UNITES = ("Entreprise", "Marche")
LIGNES = ("ebe_tresorerie", "variation_dettes", "variation_stocks", "ebe", "amortissement", "charges_financieres",
          "exceptionnel", "resultat", "dividendes", "boni", "apports", "reevaluation", "credit", "principal_paye",
          "interet_paye", "investissement", "salaires_dus", "valeur_production", "ventes_menages_ht")
PROPRES = ("dividendes", "boni", "apports", "investissement", "rebut", "reevaluation")


# ================================================================== les classes
class EtatMarche:
    """Ce que le marchand sait de son marche, bien par bien : la demande lissee ( ce que menages et entreprises ont
    voulu ET pu payer : la demande effective ), ce qu il n a pas pu servir faute de stock, la couverture qu il en tire.
    Ce qu un menage voulait sans pouvoir le payer est compte a part ( non_solvable ) : un prix qui monterait avec les
    envies des pauvres ne dirait rien de la rarete. Et ce qu il a vendu aux menages : l assiette de la TVA."""
    __slots__ = ("id", "demande_lisse", "non_servi", "non_solvable", "couverture", "ventes_ht", "ventes_q", "ventes_jour")

    def __init__(self, id, demande0):
        self.id = id
        self.demande_lisse = dict(demande0)
        self.non_servi = {b: 0.0 for b in C.BIENS}      # voulu, payable, et pas servi faute de stock ( depuis l aube )
        self.non_solvable = {b: 0.0 for b in C.BIENS}   # voulu et pas payable : la pauvrete, cumul ( pas un signal de prix )
        self.couverture = {b: COUVERTURE_CIBLE_J.get(b, 0.0) for b in C.BIENS}
        self.ventes_ht = {b: 0.0 for b in C.BIENS}       # drachmes hors taxe vendues aux menages, cumul
        self.ventes_q = {b: 0.0 for b in C.BIENS}
        self.ventes_jour = {b: 0.0 for b in C.BIENS}     # drachmes hors taxe du dernier jour d achats


class Comptes:
    """Les comptes d une unite ( entreprise du moteur ou marche ), tenus chaque soir.
      caisse, stocks_val, creances, dettes_banque, dettes_autres   le bilan de la derniere cloture ( drachmes ) ; les
                             stocks au prix auquel le marche de la region les rachete, l or au prix mondial
      capital_brut, amort_cumule, duree_vie_j   le capital fixe : un montant, pas un objet ( les modeles de machines sont
                             au domaine 10 ) ; amortissement lineaire
      cp                     capitaux propres PORTES par le compte de resultat, jamais recalcules
      prets                  les prets suivis : id -> [ Pret, interets payes, principal paye, interets echus, principal ]
                             vus a la derniere cloture ; l objet est garde apres son solde, pour son dernier mouvement
      propres                les flux non courants du jour, ecrits par le domaine ( dividendes, boni, apports,
                             investissement, rebut, reevaluation )
      jour, mois, cumul      compte de resultat du dernier jour, du mois en cours, depuis l installation ( LIGNES )
      ecart, pire_ecart      actif - dettes - capitaux propres portes, du soir et le pire, en tolerances du registre
      cessation              soirs de suite avec capitaux propres negatifs et tresorerie nulle"""
    __slots__ = ("id", "unite", "nature", "marche_id", "caisse0", "caisse", "stocks_val", "creances", "dettes_banque",
                 "dettes_autres", "capital_brut", "amort_cumule", "duree_vie_j", "cp", "cp0", "prets", "propres", "jour",
                 "mois", "mois_clos", "cumul", "ecart", "ecart_drachmes", "pire_ecart", "jours_tenus", "volume",
                 "cessation", "tresorerie_nulle",
                 "liquidee", "liquidee_j", "salaires_dus_j", "salaires_lisses", "produit_vu", "effectif", "capacite_j",
                 "couvertures", "credit_j", "ecart_prets")

    def __init__(self, id, unite, nature, marche_id, capital_brut, duree_vie_ans):
        if nature not in ("entreprise", "marche"): raise ValueError(f"nature d unite inconnue {nature!r}")
        if not capital_brut >= 0.0 or not duree_vie_ans > 0: raise ValueError(f"{id} : capital ou duree de vie invalide")
        self.id, self.unite, self.nature, self.marche_id = id, unite, nature, marche_id
        self.capital_brut = float(capital_brut)
        self.amort_cumule = AMORTI_AU_DEPART * self.capital_brut
        self.duree_vie_j = float(duree_vie_ans) * JOURS_AN
        self.caisse0 = self.caisse = unite.caisse
        self.stocks_val = self.creances = self.dettes_banque = self.dettes_autres = 0.0
        self.cp = self.cp0 = 0.0
        self.prets = {}
        self.propres = {k: 0.0 for k in PROPRES}
        self.jour = {k: 0.0 for k in LIGNES}
        self.mois = {k: 0.0 for k in LIGNES}
        self.mois_clos = {k: 0.0 for k in LIGNES}
        self.cumul = {k: 0.0 for k in LIGNES}
        self.ecart = self.ecart_drachmes = self.pire_ecart = self.volume = 0.0
        self.jours_tenus = 0
        self.cessation = 0
        self.tresorerie_nulle = False
        self.liquidee, self.liquidee_j = False, -1
        self.salaires_dus_j = self.salaires_lisses = 0.0
        self.produit_vu = {}
        self.effectif, self.capacite_j = 0, 0.0
        self.couvertures = deque(maxlen=4)
        self.credit_j = -100000
        self.ecart_prets = 0.0

    def capital_net(self): return self.capital_brut - self.amort_cumule


class ContexteActivite:
    """Ce qu une entreprise voit a l aube : ses traits, et le cran ou elle tourne ( que seule la regle lit )."""
    __slots__ = ("traits", "courant")

    def __init__(self, traits, courant): self.traits, self.courant = traits, courant


class Economie:
    """L etat du domaine."""
    __slots__ = ("marches", "ids_marches", "rang_marche", "comptes", "unites", "producteurs", "proprietaires",
                 "chomeurs", "offres", "decideur", "attente_region", "budget", "achats_serie", "credits", "serie",
                 "livre_clos", "livre_base", "base_moteur", "ecarts_livre", "pire_livre", "caisses_1750",
                 "exceptionnelle", "recalibrage", "faillites")

    def __init__(self):
        self.marches = {}          # id du marche -> EtatMarche
        self.ids_marches = []
        self.rang_marche = {}
        self.comptes = {}          # id d unite -> Comptes
        self.unites = []           # les Comptes, dans l ordre des identifiants
        self.producteurs = {}      # ( marche, bien ) -> [ id d entreprise ] : les producteurs d une region
        self.proprietaires = {}    # id d entreprise -> Habitant proprietaire ( patron ) ; les fermes n en ont pas
        self.chomeurs = {}         # id d habitant -> [ jour, ancien employeur, metier, motif ]
        self.offres = {}           # id d unite -> postes offerts ( pour le domaine 4 )
        self.decideur = None
        self.attente_region = {}   # marche -> tableau K : drachmes voulues que rien ne sert, cumul
        self.budget = np.zeros((5, K))   # quintile de revenu lisse x division : drachmes voulues, cumul
        self.achats_serie = deque(maxlen=400)   # ( jour, nourriture vendue, menages acheteurs, menages habites )
        self.credits = {}          # motif -> [ demandes, accordes, montant accorde ]
        self.serie = deque(maxlen=400)          # indicateurs du soir ( chomage, sous-emploi, epargne forcee )
        self.livre_clos = {}       # ( motif, payeur, receveur ) -> drachmes, jours clos, pour les classes des unites
        self.livre_base = {}       # le jour en cours au moment de l installation
        self.base_moteur = None    # ( net par classe, exterieur, monnaie, caisse de l Etat ) a l installation
        self.ecarts_livre = {}
        self.pire_livre = 0.0
        self.caisses_1750 = None
        self.exceptionnelle = None
        self.recalibrage = 0.0     # drachmes d epargne initiale versees aux menages a l installation
        self.faillites = []        # rapports de liquidation


# ================================================================== petits outils
def _cal_marche_ouvert(cal, date):
    """Commerces ouverts : du lundi au samedi, hors jours feries ( la meme regle que l agenda )."""
    return date.weekday() < 6 and cal.ferie(date) is None


def _jours_sans_marche(p):
    """Combien de jours de suite, apres aujourd hui, les commerces sont fermes ( dimanche, ferie )."""
    cal = p.socle.calendrier
    base = cal.date(p.w.pas).date()
    k = 0
    while k < 4 and not _cal_marche_ouvert(cal, base + dt.timedelta(days=k + 1)): k += 1
    return k


def _produit_principal(e):
    """Le produit qui fait le chiffre d affaires : comme Monde.economie_entreprise ( l or a part )."""
    return max(e.produits, key=lambda x: e.produits[x] * PM[x] if x != "or" else 0)


def _marche_de(w, unite):
    return unite if type(unite).__name__ == "Marche" else w.marches[unite.lieu.marche.id]


def _valeur_unitaire(w, m, b):
    """Le prix auquel un stock est valorise : ce que le marche de la region paie pour le racheter ; l or au prix mondial,
    l electricite au tarif du reseau."""
    if b == "or": return PM["or"]
    if b == "electricite": return w.reseau.tarif
    return m.prix[b] * (1.0 - m.marge)


def _valeur_stocks(w, unite, m):
    return math.fsum(q * _valeur_unitaire(w, m, b) for b, q in unite.stocks.items() if q)


def _ids_salaries(p, unite):
    """Les numeros des salaries vivants d une unite, dans l ordre de `salaries`, lus dans les colonnes du moteur
    ( 24/09 : sans fabriquer une vue par salarie )."""
    w = p.w; tb = w.table
    roles = ("marchand", "convoyeur") if type(unite).__name__ == "Marche" else (unite.role,)
    ids = [i for r in roles for i in w.ids_au_travail(unite.lieu, r)]
    a = np.array(ids, np.int64)
    if not len(a): return a
    return a[(tb.vivant[a] == 1) & (tb.travail[a] == unite.lieu.n)]


def _salaires_horaires():
    """Le salaire horaire de chaque code de metier ( la derniere case sert au code -1, sans metier )."""
    return np.array([float(PO.SALAIRE_HORAIRE.get(r, 0)) for r in PO.ROLES] + [0.0])


def salaries(p, unite):
    """Les salaries vivants d une unite : l index du moteur ( refait a l aube, tenu par embaucher et licencier ). Un
    marche emploie ses marchands et ses convoyeurs."""
    tb = p.w.table
    return [PO.Habitant(tb, i) for i in _ids_salaries(p, unite).tolist()]


def cout_unitaire(p, e, b=None):
    """( cout variable complet d une unite de `b` au prix du jour, salaire horaire ) : salaires, intrants au prix du marche
    de la region, electricite au tarif, amortissement du capital par heure de capacite ; les produits joints se partagent
    le cout selon leur valeur au prix mondial ; un site outille produit 25 % de plus."""
    w = p.w; m = w.marches[e.lieu.marche.id]
    b = b or _produit_principal(e)
    c = p.domaine("economie").comptes.get(e.id)
    salaire = PO.SALAIRE_HORAIRE.get(e.role, 0)
    cout_h = salaire + math.fsum(q * (w.reseau.tarif if x == "electricite" else m.prix[x]) for x, q in e.intrants.items())
    if c is not None and c.effectif > 0: cout_h += c.capital_brut / c.duree_vie_j / (8.0 * c.effectif)
    val = math.fsum(q * PM[x] for x, q in e.produits.items())
    part = e.produits[b] * PM[b] / val if val > 0 else 1.0
    bonus = BONUS if e.stocks.get("outils", 0.0) >= 1 else 1.0
    return cout_h * part / (e.produits[b] * bonus), salaire


def prix_producteur(p, e, b=None):
    """Ce que le marche de la region paie a l entreprise pour une unite de son produit."""
    m = p.w.marches[e.lieu.marche.id]
    b = b or _produit_principal(e)
    return _valeur_unitaire(p.w, m, b)


# ================================================================== le budget d un jour ( fonction pure )
def repartir_budget(revenu, caisse, tampon, cout_nourriture):
    """Le budget voulu d un jour, pour des tableaux de menages ( drachmes TTC par jour ). Consommation voulue
    C = ( 1 - epargne ) x revenu lisse + ( caisse - tampon ) / AJUSTEMENT_J, jamais negative. La nourriture passe
    d abord : son montant suit le BESOIN ( rations x prix ), meme au-dela de C ; le reste va aux autres divisions selon
    leurs parts ELSTAT. Rend ( C, tableau n x K des montants voulus )."""
    revenu, caisse, tampon, cout_nourriture = (np.asarray(x, dtype=float) for x in (revenu, caisse, tampon, cout_nourriture))
    cv = np.maximum(0.0, (1.0 - EPARGNE_STRUCTURELLE) * revenu + (caisse - tampon) / AJUSTEMENT_J)
    reste = np.maximum(0.0, cv - cout_nourriture)
    M = reste[:, None] * PARTS_HORS_ALIM[None, :]
    M[:, I_ALIM] = cout_nourriture
    return cv, M


def tampon_vise(classe, revenu):
    return np.array([TAMPON_MOIS[NOMS_CLASSES[k]] for k in range(3)])[classe] * MOIS_J * revenu


def equipement_vise(revenu, cout_nourriture):
    """La valeur d equipement durable qu un menage entretient : la depense durable voulue en regime ( son revenu,
    nourriture payee, fois la part ELSTAT des durables ), fois sa duree de vie."""
    flux = np.maximum(0.0, (1.0 - EPARGNE_STRUCTURELLE) * revenu - cout_nourriture) * PARTS_HORS_ALIM[I_EQUIP]
    return flux * JOURS_AN * DUREE_VIE_EQUIPEMENT_AN


# ================================================================== le point de decision
def _observer_activite(ctx): return ctx.traits


def _regle_activite(x, ctx):
    couv, manque, marge = x[0], x[1], 2.0 * x[2] - 1.0
    k = ctx.courant
    if manque > MANQUE_URGENCE or couv < 0.25: return len(ACTIVITES) - 1
    if marge < 0.0 or couv >= 1.0: return max(0, k - 1)
    if couv < 0.5: return min(len(ACTIVITES) - 1, k + 1)
    return k


def _temoin_activite(x, ctx, rng): return len(ACTIVITES) - 1


POINT_ACTIVITE = D.PointDeDecision(
    "niveau_activite", "economie",
    traits=(("couverture", "stock de son produit au marche de sa region, en jours de demande, sur deux fois la cible "
                           "( ce que le marchand affiche )"),
            ("manque", "la part des menages de sa region sans repas hier ( bulletin du soir ) pour la nourriture ; la "
                       "demande non servie de son produit a son marche sinon"),
            ("marge", "( prix que le marche lui paie - son cout variable complet ) / prix, ramene de [-1 ; 1] a [0 ; 1] : "
                      "ses salaires, ses intrants au prix affiche, son amortissement"),
            ("prix", "le prix affiche de son produit sur trois fois le prix mondial"),
            ("tresorerie", "sa caisse sur un mois de couts a pleine activite, bornee a 1"),
            ("intrants", "ses stocks d intrants en jours de besoin a plein, sur 3"),
            ("activite", "son activite d hier"),
            ("tendance", "la variation de la couverture depuis trois jours, sur la cible, ramenee a [0 ; 1]")),
    actions=NOMS_ACTIVITES,
    observer=_observer_activite, regle=_regle_activite, temoin=_temoin_activite,
    note="chaque jour : la production de CETTE entreprise en part de sa capacite, fois ( besoin de SA region - stock sous "
         "la cible et faim - + 0,5 x SA marge unitaire ) ; moyenne sur 3 jours",
    horizon_j=HORIZON_ACTIVITE)


# ================================================================== les methodes du moteur reprises
class RemplaceAchats:
    """Prend la place de Monde.achats ( 19 h ) : un objet, pour rester picklable."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self): _achats(self.pays)


class RemplaceRegler:
    """Prend la place de Monde.regler_activite ( aube ) : le point de decision `niveau_activite`."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self): _regler_activite(self.pays)


class AjusterPrix:
    """Prend la place de Marche.ajuster_prix pour UN marche ( appele par l aube du moteur )."""
    __slots__ = ("pays", "marche")

    def __init__(self, pays, marche): self.pays, self.marche = pays, marche

    def __call__(self): _ajuster_prix(self.pays, self.marche)


# ================================================================== les achats des menages ( 19 h )
def _rang_marche_menages(w, d, n):
    """Le rang du marche de chacun des `n` premiers menages ( celui du domicile ), lu dans les colonnes du moteur."""
    rm = np.full(len(w.carte.par_n), -1, np.int64)
    for k, r in d.rang_marche.items(): rm[w.carte.lieux[k].n] = r
    mi = rm[w._marche_du_lieu[w.table.menages.domicile[:n]]]
    if (mi < 0).any(): raise KeyError("menage dont le marche n a pas de rang")
    return mi


def _tableaux_menages(p):
    """Une passe sur les habitants : vivants par menage et classe du menage ( la plus haute de ses adultes )."""
    w = p.w; H = w.habitants; n = len(w.menages)
    tb = w.table; nh = tb.n                       # colonnes du moteur ( 24/09 )
    mid = np.where((tb.vivant[:nh] == 1) & (tb.statut[:nh] != PO.ABSENT), tb.menage[:nh], -1).astype(np.int64)   # archipel : l absent ne mange pas ici
    cl = np.where(tb.role[:nh] == PO.CODE_ROLE["enfant"], -1, CLASSE_DU_MOTEUR[tb.classe[:nh]]).astype(np.int64)
    ok = mid >= 0
    v = np.bincount(mid[ok], minlength=n)[:n]
    classe = np.zeros(n, np.int64)
    a = ok & (cl >= 0)
    np.maximum.at(classe, mid[a], cl[a])
    return v, classe


def _rationner(q0, mi, dispo):
    """Chacun recoit sa demande si son marche a de quoi ; sinon la meme part de sa demande ( rationnement
    proportionnel, deterministe ). `dispo` : ce que chaque marche peut vendre."""
    tot = np.bincount(mi, weights=q0, minlength=len(dispo))
    f = np.ones_like(tot)
    np.divide(dispo, tot, out=f, where=tot > dispo)
    return q0 * np.clip(f, 0.0, 1.0)[mi]


def _acheteurs(p, n):
    """Les menages qui font leurs courses aujourd hui : tous sans agenda ; avec l agenda, ceux dont un membre a un tour
    de courses, ou travaille au marche de son domicile ( il achete sur place ). Rend un masque, ou None ( tous )."""
    if not p.a("agenda"): return None
    AG = importlib.import_module(".d05_agenda", __package__)
    if p.domaine("agenda").plan is None: return None
    w = p.w
    masque = np.zeros(n, bool)
    cal = p.socle.calendrier
    if not _cal_marche_ouvert(cal, cal.date(w.pas).date()): return masque      # dimanche, ferie : tout est ferme
    t = AG.tours_du_jour(p)
    tb = w.table                                   # colonnes du moteur ( 24/09 )
    c = np.array(t["courses"], np.int64)
    if len(c):
        k = tb.menage[c]
        masque[k[(tb.vivant[c] == 1) & (k >= 0)]] = True
    c = np.array(t["travail"], np.int64)
    if len(c):
        k = tb.menage[c]; tr = tb.travail[c]; dom = tb.domicile[c]
        sel = (tb.vivant[c] == 1) & (k >= 0) & (tr >= 0)
        if (sel & (dom < 0)).any(): raise AttributeError("'NoneType' object has no attribute 'marche'")
        sel[sel] = tr[sel] == w._marche_du_lieu[dom[sel]]      # il travaille au marche de son domicile
        masque[k[sel]] = True
    return masque


def _payer_tva(p, w, mg, m, du, u_fraude, u_controle, part_fraude, gf):
    """La TVA d un achat alimentaire, avec la fraude du moteur ( point 8 ) : au-dela de 12 % de TVA, une part des achats
    y echappe ; un controle coute trois fois la taxe evitee. Les fraudeurs appris ( roles.py ) gardent la main s ils
    sont installes."""
    L = p.socle.livre
    if gf: fraude = gf.choisir(mg.id, RO.traits_fraude(w, mg, m)) == 1
    else: fraude = part_fraude > 0.0 and u_fraude < part_fraude
    if not fraude:
        w.tva_percue += L.transferer(mg, w.gouv, du, "tva"); return
    w.tva_fraudee += du
    pris = u_controle < w.probabilite_controle(m)
    if pris:
        amende = L.transferer(mg, w.gouv, 3 * du, "amende")
        w.amendes_menage[mg.id] = w.amendes_menage.get(mg.id, 0) + 1
        w.amendes_totales = getattr(w, "amendes_totales", 0.0) + amende
    if gf:
        norme = max(1e-6, m.prix["nourriture"] * C.NOURRITURE_PAR_JOUR * len(mg.membres))
        gf.ajouter(mg.id, (du - (3 * du if pris else 0.0)) / norme)


def _achats(p):
    """19 h, apres la paie : les menages achetent. Nourriture d abord, au BESOIN ( le garde-manger vise les jours
    jusqu aux prochaines courses ), puis les biens courants ( carburant, remedes ) et les durables selon le budget ;
    ce que rien ne sert reste demande en attente. Rationnement proportionnel quand le stock manque ; la demande non
    servie faute de stock est le signal du marchand, celle qui manque faute d argent est comptee a part ( le prix ne
    dit pas la faim des pauvres )."""
    w = p.w
    if w.doctrine is not None:                     # l experience des menages appris ( agents.py ) garde sa regle
        type(w).achats(w); return
    d = p.domaine("economie"); L = p.socle.livre; g = w.gouv
    n = len(w.menages)
    v, classe = _tableaux_menages(p)
    dis = p.col("menage", "dissous")[:n]
    ok = (v > 0) & (dis == 0)
    masque = _acheteurs(p, n)
    achete = ok if masque is None else ok & masque
    marches = [w.marches[k] for k in d.ids_marches]
    mi = _rang_marche_menages(w, d, n)
    tva = g.tva
    ration = g.lois["rationnement_nourriture"] or C.NOURRITURE_PAR_JOUR
    caisse = w.table.menages.caisse[:n].copy()
    gm = w.table.menages.garde_manger[:n].copy()
    pn = np.array([m.prix["nourriture"] for m in marches])[mi]
    pn_ttc = pn * (1.0 + tva)
    besoin = ration * v
    # --- la nourriture
    ecart = _jours_sans_marche(p) if masque is not None else 0      # sans l agenda, le moteur n a jamais ferme
    cible = 1.0 + ecart + PRECAUTION_J + (JOUR_SANS_ACHETEUR_J if masque is not None else 0.0)
    voulu = np.where(achete, np.maximum(0.0, besoin * cible - gm), 0.0)
    abordable = np.minimum(voulu, np.maximum(0.0, caisse) / pn_ttc)
    dispo = np.array([max(0.0, m.stocks["nourriture"]) for m in marches])
    q = _rationner(abordable, mi, dispo)
    rupture = float((abordable - q).sum())
    for k, m in enumerate(marches):
        sel = mi == k
        em = d.marches[m.lieu.id]
        m.demande["nourriture"] += float(abordable[sel].sum())
        em.non_servi["nourriture"] += float((abordable[sel] - q[sel]).sum())
        em.non_solvable["nourriture"] += float((voulu[sel] - abordable[sel]).sum())
    idx = np.nonzero(q > 0.0)[0]
    part_fraude = w.part_fraudeuse(); gf = w.agents.get("fraudeurs")
    u = p.du_jour("economie_fraude").random((n, 2)) if part_fraude > 0.0 else np.ones((n, 2))
    vendu = 0.0
    # une vue par menage, gardee pour toute la routine ( 24/09 : la meme vue sert a la nourriture et aux autres biens )
    mt = w.menages._mt; vues = {}; Mg = PO.Menage
    ems = [d.marches[m.lieu.id] for m in marches]
    mi_l = mi.tolist(); q_l = q.tolist(); gmc = mt.garde_manger
    for i in idx.tolist():
        mg = vues[i] = Mg(i, mt); k = mi_l[i]; m = marches[k]; qi = q_l[i]
        m.stocks["nourriture"] -= qi; gmc[i] += qi; vendu += qi
        ht = L.transferer(mg, m, qi * m.prix["nourriture"], "nourriture")
        em = ems[k]; em.ventes_ht["nourriture"] += ht; em.ventes_q["nourriture"] += qi
        em.ventes_jour["nourriture"] += ht
        du = qi * m.prix["nourriture"] * tva
        if not gf and not (part_fraude > 0.0 and u[i, 0] < part_fraude):
            w.tva_percue += L.transferer(mg, w.gouv, du, "tva")        # _payer_tva, sans fraude
        else: _payer_tva(p, w, mg, m, du, u[i, 0], u[i, 1], part_fraude, gf)
    caisse = w.table.menages.caisse[:n].copy()
    # --- le budget du jour
    rev = p.col("menage", "eco_revenu")[:n]
    tampon = tampon_vise(classe, rev)
    cout_n = besoin * pn_ttc
    _, M = repartir_budget(rev, caisse, tampon, cout_n)
    M[~ok] = 0.0
    jours = np.clip(p.jour - p.col("menage", "eco_dernier_achat")[:n], 1, JOURS_ACHAT_MAX).astype(float)
    reserve = RESERVE_ALIMENTAIRE_J * cout_n
    dispo_argent = np.where(achete, np.maximum(0.0, caisse - reserve), 0.0)
    envies = [(k, b, np.where(achete, M[:, k] * PART_BIEN[k] * jours, 0.0)) for k, b in BIENS_COURANTS]
    tot_env = sum(e for _, _, e in envies)
    f_argent = np.ones(n)
    np.divide(dispo_argent, tot_env, out=f_argent, where=tot_env > dispo_argent)
    non_servi_valeur = np.zeros(n)
    for k, b, env in envies:
        prix = np.array([m.prix[b] for m in marches])
        pt = prix[mi] * (1.0 + tva)
        q0 = env * f_argent / pt
        reserve_b = RESERVE_CARBURANT if b == "carburant" else 0.0
        q = _rationner(q0, mi, np.array([max(0.0, m.stocks[b] - reserve_b) for m in marches]))
        non_servi_valeur += (q0 - q) * pt
        for j, m in enumerate(marches):
            sel = mi == j
            em = d.marches[m.lieu.id]
            m.demande[b] += float(q0[sel].sum())
            em.non_servi[b] += float((q0[sel] - q[sel]).sum())
            em.non_solvable[b] += float((env[sel] / pt[sel] - q0[sel]).sum())
        q_l = q.tolist()
        for i in np.nonzero(q > 0.0)[0].tolist():
            mg = vues.get(i)
            if mg is None: mg = vues[i] = Mg(i, mt)
            _vendre(p, d, mg, marches[mi_l[i]], b, q_l[i], tva)
    # --- les durables : un renouvellement d un coup, sans descendre sous la moitie du tampon
    E = p.col("menage", "eco_equipement")
    cible_e = equipement_vise(rev, cout_n)
    caisse = w.table.menages.caisse[:n].copy()
    bas = achete & (E[:n] < SEUIL_RENOUVELLEMENT * cible_e)
    if bas.any():
        po = np.array([m.prix["outils"] for m in marches]); pt = po[mi] * (1.0 + tva)
        libre = np.maximum(0.0, caisse - np.maximum(0.5 * tampon, reserve))
        voulu_e = np.where(bas, cible_e - E[:n], 0.0)
        q0 = np.minimum(voulu_e, libre) / pt
        q = _rationner(q0, mi, np.array([max(0.0, m.stocks["outils"]) for m in marches]))
        for j, m in enumerate(marches):
            sel = mi == j
            em = d.marches[m.lieu.id]
            m.demande["outils"] += float(q0[sel].sum())
            em.non_servi["outils"] += float((q0[sel] - q[sel]).sum())
            em.non_solvable["outils"] += float((voulu_e[sel] / pt[sel] - q0[sel]).sum())
        q_l = q.tolist()
        for i in np.nonzero(q > 0.0)[0].tolist():
            mg = vues.get(i)
            if mg is None: mg = vues[i] = Mg(i, mt)
            valeur = _vendre(p, d, mg, marches[mi_l[i]], "outils", q_l[i], tva)
            E[i] += valeur
            p.compter("achat_durable", valeur)
    # --- ce que rien ne sert : demande en attente, epargne forcee
    attente = M * (1.0 - PART_BIEN)[None, :]
    attente[:, I_ALIM] = 0.0; attente[:, I_EQUIP] = 0.0
    tot_att = attente.sum(axis=1) + non_servi_valeur
    p.col("menage", "eco_epargne_forcee")[:n] += tot_att
    for j, m in enumerate(marches):
        sel = ok & (mi == j)
        d.attente_region[m.lieu.id] += attente[sel].sum(axis=0)
    p.compter("demande_en_attente", float(tot_att.sum()))
    # --- les parts du budget voulu, par quintile de revenu lisse
    io = np.nonzero(ok)[0]
    if len(io):
        rang = np.empty(len(io), np.int64); rang[np.argsort(rev[io], kind="stable")] = np.arange(len(io))
        quint = np.minimum(4, rang * 5 // len(io))
        for qn in range(5): d.budget[qn] += M[io[quint == qn]].sum(axis=0)
    p.col("menage", "eco_dernier_achat")[:n][achete] = p.jour
    d.achats_serie.append((p.jour, vendu, len(idx), int(achete.sum()), int(ok.sum())))
    p.compter("achat_menages", vendu)
    p.compter("rupture_de_stock", rupture)
    # --- la ration de l Etat, comme le moteur : aux menages dont le garde-manger tient moins d une demi-journee
    stock = w.publics["population"]["nourriture"]
    if stock > 0:
        io = np.nonzero(ok)[0]
        v_l = v.tolist()
        for i in io[gmc[io] < 0.5 * v[io]].tolist():      # les colonnes trouvent les menages, dans leur ordre
            x = min(stock, float(v_l[i]))
            gmc[i] += x; stock -= x
        w.publics["population"]["nourriture"] = stock


RESERVE_CARBURANT = 120.0       # le moteur garde 120 unites de carburant a chaque marche pour ses convois ( monde.py )


def _vendre(p, d, mg, m, b, q, tva):
    """Un bien courant ou durable vendu a un menage et consomme : le stock du marche baisse, la consommation est
    comptee dans les flux du grand livre, le menage paie le prix et la TVA. Rend la valeur TTC."""
    L = p.socle.livre
    m.stocks[b] -= q
    L.flux["consomme"][b] = L.flux["consomme"].get(b, 0.0) + q
    ht = L.transferer(mg, m, q * m.prix[b], b)
    p.w.tva_percue += L.transferer(mg, p.w.gouv, q * m.prix[b] * tva, "tva")
    em = d.marches[m.lieu.id]; em.ventes_ht[b] += ht; em.ventes_q[b] += q; em.ventes_jour[b] += ht
    return q * m.prix[b] * (1.0 + tva)


# ================================================================== la formation des prix
def _ancrage(p, d, m, b):
    """Le prix de revient complet des producteurs de la region, majore de leur marge et de celle du detaillant ; None
    s il n y en a pas, ou s ils ne paient pas de salaire ( les fermes cooperatives : le revenu de leurs membres est ce
    qui reste, il n est pas un cout )."""
    w = p.w
    tot = som = 0.0
    for eid in d.producteurs.get((m.lieu.id, b), ()):
        c = d.comptes[eid]
        if c.liquidee or eid in p.repris or c.effectif <= 0: continue
        cu, salaire = cout_unitaire(p, c.unite, b)
        if salaire <= 0: continue
        tot += c.effectif * cu; som += c.effectif
    if som <= 0: return None
    return tot / som * (1.0 + MARGE_PRODUCTEUR) / (1.0 - m.marge)


def _borner(w, b, x):
    bas = (PARITE_EXPORT if b == "nourriture" else PLANCHER) * PM[b]
    x = min(PLAFOND * PM[b], max(bas, x))
    plafond = w.gouv.lois.get("prix_plafond", {}).get(b)
    return min(x, float(plafond)) if plafond else x


def _ajuster_prix(p, mid):
    """L aube, pour un marche : chaque prix suit l ecart entre le stock et la demande qu il doit couvrir ( en JOURS de
    demande, pas en unites : la faute du moteur ), plus les ruptures de la veille, avec un rappel lent vers le prix de
    revient des producteurs de la region. Bornes : parite a l export pour la nourriture, 0,25 et 2,5 fois le prix
    mondial sinon, et le plafond legal s il y en a un. L or garde le prix mondial ; l electricite est au reseau. Apres
    un jour de fermeture ( dimanche, ferie, avec l agenda ), aucun prix ne change : personne n a rien vendu."""
    w = p.w; d = p.domaine("economie"); m = w.marches[mid]; em = d.marches[mid]
    cal = p.socle.calendrier
    ferme_hier = p.a("agenda") and not _cal_marche_ouvert(cal, (cal.date(w.pas) - dt.timedelta(days=1)).date())
    for b in C.BIENS:
        if ferme_hier: pass                        # commerces fermes hier : ni ventes, ni prix nouveau
        elif b in COUVERTURE_CIBLE_J:
            cible = COUVERTURE_CIBLE_J[b]
            em.demande_lisse[b] = (1.0 - ALPHA_DEMANDE) * em.demande_lisse[b] + ALPHA_DEMANDE * m.demande[b]
            dem = max(DEMANDE_MIN, em.demande_lisse[b])
            couv = max(0.0, m.stocks[b]) / dem
            em.couverture[b] = couv
            x = max(-1.0, min(1.0, (cible - couv) / cible))
            if em.non_servi[b] > 0.0: x = max(x, min(1.0, em.non_servi[b] / dem))
            dlog = KAPPA_PRIX * x
            a = _ancrage(p, d, m, b)
            if a is not None and a > 0.0: dlog += BETA_COUT * (math.log(a) - math.log(m.prix[b]))
            m.prix[b] = _borner(w, b, m.prix[b] * math.exp(dlog))
        elif b == "or":
            m.prix[b] = PM[b]
        m.demande[b] = 0.0; m.offre[b] = 0.0; em.non_servi[b] = 0.0


def _transport_unitaire(w, a, o):
    """Le cout d une unite portee d un marche a l autre : le carburant d un camion aller et retour, reparti sur sa
    charge ( la regle de commerce du moteur )."""
    km = w.carte.km_route(a.lieu, o.lieu)
    return 2.0 * km * C.CARBURANT_PAR_KM * a.prix["carburant"] / C.CAPACITE_CAMION


def _concurrence(p):
    """6 h, apres l aube : la concurrence entre marches d une meme ile. Un marchand peut revendre ailleurs ( au prix
    d achat de l autre marche, moins le transport ) : son prix ne reste pas dessous. Il peut aussi acheter a un marche
    qui a du surplus : son prix ne reste pas au-dessus du prix de l autre plus le transport, marge comprise. Chaque
    matin, la moitie de l ecart a ces bornes se referme. Les deux bornes sont posees JUSTE AU-DELA du seuil ou la
    regle de commerce du moteur envoie un camion ( prix d achat la-bas > prix ici + 5 % + transport ) : posees
    dessus, elles tenaient les deux prix a l ecart exact ou aucun camion ne part - le plancher de l un montait avec le
    prix de l autre, le plafond de l autre suivait le premier ( Kavala a sec de carburant, 23/09 )."""
    w = p.w; d = p.domaine("economie")
    ms = [w.marches[k] for k in d.ids_marches]
    for b in C.BIENS_COMMERCE:
        if b not in COUVERTURE_CIBLE_J: continue
        prix = [m.prix[b] for m in ms]
        for i, a in enumerate(ms):
            bas, haut = -math.inf, math.inf
            for j, o in enumerate(ms):
                if j == i or o.lieu.ile != a.lieu.ile: continue
                t = _transport_unitaire(w, a, o)
                bas = max(bas, (prix[j] * (1.0 - o.marge) - t) / (1.0 + MARGE_COMMERCE) / ARBITRAGE_AU_DELA)
                if d.marches[o.lieu.id].couverture.get(b, 0.0) >= COUVERTURE_CIBLE_J[b]:
                    haut = min(haut, ARBITRAGE_AU_DELA * ((1.0 + MARGE_COMMERCE) * prix[j] + t) / (1.0 - a.marge))
            x = a.prix[b]
            if x < bas: x += 0.5 * (bas - x)
            if x > haut: x -= 0.5 * (x - haut)
            a.prix[b] = _borner(w, b, x)


# ================================================================== la decision de production ( aube )
def _couverture(d, m, b):
    return max(0.0, m.stocks[b]) / max(DEMANDE_MIN, d.marches[m.lieu.id].demande_lisse[b])


def _traits_activite(p, d, e, c):
    w = p.w; m = w.marches[e.lieu.marche.id]; em = d.marches[m.lieu.id]
    b = _produit_principal(e)
    cible = COUVERTURE_CIBLE_J.get(b, 5.0)
    couv = _couverture(d, m, b)
    if b == "nourriture": manque = w.faim_region.get(m.lieu.id, 0.0)
    else: manque = min(1.0, em.non_servi[b] / max(DEMANDE_MIN, em.demande_lisse[b]))
    pp = prix_producteur(p, e, b)
    cu, _ = cout_unitaire(p, e, b)
    mu = max(-1.0, min(1.0, (pp - cu) / pp)) if pp > 0 else -1.0
    cout_h = PO.SALAIRE_HORAIRE.get(e.role, 0) + math.fsum(
        q * (w.reseau.tarif if x == "electricite" else m.prix[x]) for x, q in e.intrants.items())
    cout_j = cout_h * 8.0 * c.effectif
    tres = 1.0 if cout_j <= 0 else min(1.0, max(0.0, e.caisse) / (30.0 * cout_j))
    besoins = [e.stocks.get(x, 0.0) / (q * 8.0 * c.effectif * 3.0) for x, q in e.intrants.items() if x != "electricite" and q > 0]
    intr = min(1.0, min(besoins)) if besoins else 1.0
    ancien = c.couvertures[0] if c.couvertures else couv
    c.couvertures.append(couv)
    tend = (max(-1.0, min(1.0, (couv - ancien) / cible)) + 1.0) / 2.0
    return (min(1.0, couv / (2.0 * cible)), max(0.0, min(1.0, manque)), (mu + 1.0) / 2.0,
            min(1.0, m.prix[b] / PM[b] / 3.0), tres, intr, max(0.0, min(1.0, e.activite)), tend)


def _cran(activite):
    return min(range(len(ACTIVITES)), key=lambda k: abs(ACTIVITES[k] - activite))


def _regler_activite(p):
    """L aube : chaque entreprise du moteur choisit son niveau d activite ( point `niveau_activite` ). Les entreprises
    reprises par un autre domaine, liquidees ou sans salarie ne decident pas ; centrales et mine d or gardent la
    logique du moteur."""
    w = p.w; d = p.domaine("economie")
    d.offres = {}
    for e in sorted(w.entreprises.values(), key=lambda e: e.id):
        c = d.comptes[e.id]
        if c.liquidee: e.activite = 0.0; continue
        if e.id in p.repris or e.type == "centrale": continue
        if "or" in e.produits: e.activite = 1.0; continue
        c.effectif = len(_ids_salaries(p, e))
        if c.effectif == 0: continue
        b = _produit_principal(e)
        bonus = BONUS if e.stocks.get("outils", 0.0) >= 1 else 1.0
        c.capacite_j = c.effectif * 8.0 * e.produits[b] * bonus
        x = _traits_activite(p, d, e, c)
        k = d.decideur.decider(e.id, ContexteActivite(x, _cran(e.activite)))
        e.activite = ACTIVITES[k]
        if k == len(ACTIVITES) - 1 and x[0] < 0.25 and x[2] > 0.5:
            d.offres[e.id] = max(1, int(math.ceil(0.2 * c.effectif)))   # plein, et la region manque encore : il embaucherait


def _besoin_region(p, d, m, b):
    """Ce qu une unite de plus vaut a la region, le soir : de -0,5 ( stock a deux fois la cible et plus ) a 1 ( stock
    vide ), plus deux fois le manque ( faim de la region, ruptures ), borne a [-0,5 ; 1]."""
    cible = COUVERTURE_CIBLE_J.get(b, 5.0)
    x = max(-0.5, min(1.0, (cible - _couverture(d, m, b)) / cible))
    em = d.marches[m.lieu.id]
    if b == "nourriture": manque = p.w.faim_region.get(m.lieu.id, 0.0)
    else: manque = min(1.0, em.non_servi[b] / max(DEMANDE_MIN, em.demande_lisse[b]))
    return max(-0.5, min(1.0, x + 2.0 * manque))


def _noter_activite(p, d):
    """Le soir : chaque choix en attente encaisse la journee de SON entreprise ( production du jour en part de sa
    capacite, fois besoin de sa region et marge )."""
    w = p.w; dec = d.decideur
    for eid in list(dec.attentes):
        if not dec.attentes[eid].choix:
            del dec.attentes[eid]; continue
        c = d.comptes[eid]; e = c.unite
        b = _produit_principal(e); m = w.marches[e.lieu.marche.id]
        prod = e.produit_du_jour[b] - c.produit_vu.get(b, e.produit_du_jour[b])
        part = prod / c.capacite_j if c.capacite_j > 0 else 0.0
        pp = prix_producteur(p, e, b); cu, _ = cout_unitaire(p, e, b)
        mu = max(-1.0, min(1.0, (pp - cu) / pp)) if pp > 0 else -1.0
        dec.noter(eid, part * (_besoin_region(p, d, m, b) + POIDS_MARGE * mu), p.jour)


# ================================================================== la paie observee, les salaires dus
def _avant_paie(p):
    """17 h 50 : les caisses des menages avant la paie ( leur revenu du jour ), et les salaires que chaque unite doit
    pour les heures du jour ( ce que le domaine 4 lira comme masse salariale )."""
    w = p.w; d = p.domaine("economie")
    d.caisses_1750 = w.table.menages.caisse[:len(w.menages)].copy()
    tb = w.table; sal = _salaires_horaires(); conv = PO.CODE_ROLE["convoyeur"]
    for c in d.unites:
        u = c.unite
        ids = _ids_salaries(p, u)
        c.effectif = len(ids)
        ro = tb.role[ids]; hr = tb.heures[ids]
        if c.nature == "marche": dus = math.fsum((float(PO.SALAIRE_HORAIRE["convoyeur"]) * hr[ro == conv]).tolist())
        else: dus = math.fsum((sal[ro] * hr).tolist())
        c.salaires_dus_j = dus
        c.salaires_lisses = c.salaires_lisses * (1.0 - 1.0 / 30.0) + dus / 30.0 if c.salaires_lisses > 0 else dus
        c.mois["salaires_dus"] += dus; c.cumul["salaires_dus"] += dus


def _apres_paie(p):
    """18 h : ce que la paie a verse a chaque menage entre dans son revenu lisse ; une entreprise que la paie a videe a
    une tresorerie nulle."""
    w = p.w; d = p.domaine("economie")
    if d.caisses_1750 is not None:
        n = len(d.caisses_1750)
        maintenant = w.table.menages.caisse[:n].copy()
        entree = np.maximum(0.0, maintenant - d.caisses_1750)
        rv = p.col("menage", "eco_revenu")
        vivant = p.col("menage", "dissous")[:n] == 0
        rv[:n] = np.where(vivant, rv[:n] * (1.0 - ALPHA_REVENU) + ALPHA_REVENU * entree, rv[:n])
        d.caisses_1750 = None
    for c in d.unites: c.tresorerie_nulle = c.unite.caisse < SEUIL_TRESORERIE_NULLE


# ================================================================== le credit : de vraies raisons d emprunter
def _suspendre_exceptionnelle(p):
    """9 h, juste avant le guichet des banques : leurs depenses exceptionnelles tirees au hasard sont suspendues ( le
    budget des menages en donne les vraies raisons ) ; retablies juste apres, pour qu un monde sans economie reste
    celui du domaine 2."""
    d = p.domaine("economie")
    d.exceptionnelle = BQ.EXCEPTIONNELLE_AN
    BQ.EXCEPTIONNELLE_AN = 0.0


def _retablir_exceptionnelle(p):
    d = p.domaine("economie")
    if d.exceptionnelle is not None: BQ.EXCEPTIONNELLE_AN = d.exceptionnelle
    d.exceptionnelle = None


def _demander(p, d, emp, montant, type_, motif, duree):
    pr = BQ.demander_credit(p, emp, montant, type_, motif, duree)
    s = d.credits.setdefault(motif, [0, 0, 0.0])
    s[0] += 1
    if pr is not None: s[1] += 1; s[2] += pr.montant
    p.compter("credit_economie", montant)
    return pr


def _credits(p):
    """9 h 30, jours ouvres : les demandes de credit que le budget justifie.
      achat_durable  l equipement est sous 80 % de sa cible et la caisse, gardee a la moitie de son tampon, ne paie pas
                     le renouvellement ; mensualite au plus 15 % du revenu ;
      decouvert      les mensualites de la semaine ne tiennent pas dans la caisse, nourriture de la semaine gardee.
    La tresorerie des entreprises se demande a 17 h 40 ( _tresorerie_de_paie )."""
    w = p.w; d = p.domaine("economie")
    cal = p.socle.calendrier
    if not cal.ouvre(cal.date(w.pas)): return
    n = len(w.menages)
    v, classe = _tableaux_menages(p)
    dis = p.col("menage", "dissous")[:n]; bq = p.col("menage", "banque")[:n]
    cj = p.col("menage", "eco_credit_j")
    rev = p.col("menage", "eco_revenu")[:n]
    caisse = w.table.menages.caisse[:n].copy()
    mi = _rang_marche_menages(w, d, n)
    pn = np.array([w.marches[k].prix["nourriture"] for k in d.ids_marches])[mi] * (1.0 + w.gouv.tva)
    cout_n = (w.gouv.lois["rationnement_nourriture"] or C.NOURRITURE_PAR_JOUR) * v * pn
    reserve = RESERVE_ALIMENTAIRE_J * cout_n
    tampon = tampon_vise(classe, rev)
    ok = (v > 0) & (dis == 0) & (bq >= 0) & (p.jour - cj[:n] >= DELAI_CREDIT_J)
    E = p.col("menage", "eco_equipement")[:n]
    cible_e = equipement_vise(rev, cout_n)
    libre = np.maximum(0.0, caisse - np.maximum(0.5 * tampon, reserve))
    manque = cible_e - E - libre
    taux = BQ.taux_credit(p, "conso")
    for i in np.nonzero(ok & (E < SEUIL_RENOUVELLEMENT * cible_e) & (manque > BQ.PRET_MIN * 2))[0].tolist():
        if BQ.mensualite(float(manque[i]), taux, DUREE_CREDIT_DURABLE) > EFFORT_MAX_DURABLE * MOIS_J * rev[i]: continue
        _demander(p, d, w.menages[i], float(manque[i]), "conso", "achat_durable", DUREE_CREDIT_DURABLE)
        cj[i] = p.jour
    bqd = p.domaine("banques")
    limite = w.pas + DECOUVERT_HORIZON_J * C.PAS_PAR_JOUR
    for emp in [x for x in bqd.prets_de if type(x) is PO.Menage]:
        i = emp.id
        if not ok[i] or cj[i] > p.jour - DELAI_CREDIT_J: continue
        du = math.fsum(pr.mensualite + pr.du_interet + pr.du_principal for pr in (bqd.prets[j] for j in bqd.prets_de[emp])
                       if pr.defaut_j < 0 and 0 <= pr.pas_echeance <= limite)
        if du <= 0.0 or emp.caisse >= du + reserve[i]: continue
        _demander(p, d, emp, du + 2 * reserve[i] - emp.caisse, "conso", "decouvert", 1)
        cj[i] = p.jour


def _tresorerie_de_paie(p):
    """17 h 40, jours ouvres, avant la paie de 18 h : l entreprise ( pas la ferme cooperative ) dont la caisse ne paie
    pas les heures deja faites aujourd hui demande un credit de tresorerie de 10 jours de salaires. Le fonds de roulement
    que le domaine 2 propose le matin ( 5 jours de couts ) n y suffit pas toujours : ici c est la paie qui manque."""
    w = p.w; d = p.domaine("economie")
    cal = p.socle.calendrier
    if not cal.ouvre(cal.date(w.pas)): return
    tb = w.table; sal = _salaires_horaires()
    for c in d.unites:
        e = c.unite
        if c.nature != "entreprise" or c.liquidee or e.type == "ferme" or p.jour - c.credit_j < DELAI_CREDIT_J: continue
        ids = _ids_salaries(p, e)
        dus = math.fsum((sal[tb.role[ids]] * tb.heures[ids]).tolist())
        if dus <= 0.0 or e.caisse >= dus or BQ.banque_de(p, e) is None: continue
        besoin = max(TRESORERIE_BESOIN_J * max(c.salaires_lisses, dus), dus) - e.caisse
        _demander(p, d, e, besoin, "entreprise", "tresorerie", DUREE_CREDIT_TRESORERIE)
        c.credit_j = p.jour


# ================================================================== les comptes du soir
def _creances_par_detenteur(p):
    """{ detenteur : [ dettes de recouvrement, autres dettes, creances detenues ] } : une passe sur les creances."""
    out = {}
    for cr in p.socle.creances.actives.values():
        t = out.setdefault(cr.debiteur, [0.0, 0.0, 0.0])
        t[0 if cr.motif == "recouvrement_pret" else 1] += cr.montant
        out.setdefault(cr.creancier, [0.0, 0.0, 0.0])[2] += cr.montant
    return out


def _suivre_prets(p, c):
    """Les mouvements des prets de l unite depuis la derniere cloture, lus sur les objets Pret du domaine 2 : credit recu,
    principal et interets payes, interets courus ( payes + echus ), conversion d un pret radie en creance de
    recouvrement ( neutre ), reste d arrondi abandonne par la banque au solde ( un gain ). Un mouvement du principal d un
    pret actif que rien n explique n est PAS ecrit : il se verra dans l identite comptable. Rend ( flux, encours )."""
    bq = p.domaine("banques")
    f = {"credit": 0.0, "principal_paye": 0.0, "interet_paye": 0.0, "interets_courus": 0.0, "conversion": 0.0,
         "abandon_banque": 0.0, "inexplique": 0.0}
    for pid in bq.prets_de.get(c.unite, ()):
        if pid not in c.prets:
            pr = bq.prets[pid]
            c.prets[pid] = [pr, 0.0, 0.0, 0.0, pr.montant]
            f["credit"] += pr.montant
    encours = 0.0
    for pid in list(c.prets):
        t = c.prets[pid]; pr = t[0]
        di = pr.paye_interet - t[1]; dpp = pr.paye_principal - t[2]
        f["interet_paye"] += di; f["principal_paye"] += dpp; f["interets_courus"] += di + pr.du_interet - t[3]
        inexplique = -(pr.principal - t[4]) - dpp
        if bq.prets.get(pid) is pr:
            f["inexplique"] += inexplique
            t[1], t[2], t[3], t[4] = pr.paye_interet, pr.paye_principal, pr.du_interet, pr.principal
            encours += pr.principal + pr.du_interet
        else:
            f["conversion" if pr.defaut_j >= 0 else "abandon_banque"] += inexplique + pr.du_interet
            del c.prets[pid]
    return f, encours


def _tenir_comptes(p, d, c, cr, ouverture=False):
    """Le bilan et le compte de resultat du jour d une unite. Le compte de resultat se lit sur les flux :
      EBE de tresorerie   variation de la caisse moins les flux non courants identifies ( credit, principal, interets,
                          dividendes, boni, apports, investissement )
      + variation des dettes d exploitation ( une charge due et impayee ) et des creances detenues
      + variation des stocks valorises ( production stockee et effet prix )
      = EBE ; - amortissement - interets courus + reste abandonne par la banque - capital mis au rebut = resultat.
    Les capitaux propres sont portes : cp += resultat - dividendes - boni + apports + reevaluation. L ecart
    actif - dettes - cp est l identite comptable du soir."""
    w = p.w; u = c.unite
    m = _marche_de(w, u)
    caisse = u.caisse
    st = _valeur_stocks(w, u, m)
    rec, autres, detenues = cr.get(u, (0.0, 0.0, 0.0))
    f, encours = _suivre_prets(p, c)
    if ouverture:
        c.caisse, c.stocks_val, c.creances, c.dettes_banque, c.dettes_autres = caisse, st, detenues, encours, rec + autres
        c.cp = c.cp0 = caisse + st + c.capital_net() + detenues - encours - rec - autres
        for k in PROPRES: c.propres[k] = 0.0
        return
    pr = c.propres
    dot = min(max(0.0, c.capital_net()), c.capital_brut / c.duree_vie_j) if not c.liquidee else 0.0
    c.amort_cumule += dot
    non_courant = (f["credit"] - f["principal_paye"] - f["interet_paye"] - pr["dividendes"] - pr["boni"] + pr["apports"]
                   - pr["investissement"])
    ebe_t = (caisse - c.caisse) - non_courant
    dettes_autres = rec + autres
    var_d = -((dettes_autres - c.dettes_autres) - f["conversion"]) + (detenues - c.creances)
    var_s = st - c.stocks_val
    ebe = ebe_t + var_d + var_s
    exc = f["abandon_banque"] - pr["rebut"]
    res = ebe - dot - f["interets_courus"] + exc
    c.cp += res - pr["dividendes"] - pr["boni"] + pr["apports"] + pr["reevaluation"]
    actif = caisse + st + c.capital_net() + detenues
    dettes = encours + dettes_autres
    ecart = actif - dettes - c.cp
    c.volume += (abs(caisse - c.caisse) + abs(var_s) + abs(var_d) + dot + f["credit"] + f["principal_paye"]
                 + f["interets_courus"] + sum(abs(x) for x in pr.values()))
    c.ecart_drachmes = ecart
    c.ecart = ecart / R.tolerance(abs(actif) + abs(dettes), c.volume)
    c.pire_ecart = max(c.pire_ecart, abs(c.ecart))
    c.jours_tenus += 1
    c.ecart_prets += f["inexplique"]
    prod = 0.0
    if c.nature == "entreprise":
        for b in u.produits:
            if b in ("electricite",): continue
            prod += (u.produit_du_jour[b] - c.produit_vu.get(b, u.produit_du_jour[b])) * _valeur_unitaire(w, m, b)
    ventes_m = math.fsum(d.marches[u.lieu.id].ventes_jour.values()) if c.nature == "marche" else 0.0
    lignes = {"ebe_tresorerie": ebe_t, "variation_dettes": var_d, "variation_stocks": var_s, "ebe": ebe,
              "amortissement": dot, "charges_financieres": f["interets_courus"], "exceptionnel": exc, "resultat": res,
              "dividendes": pr["dividendes"], "boni": pr["boni"], "apports": pr["apports"],
              "reevaluation": pr["reevaluation"], "credit": f["credit"], "principal_paye": f["principal_paye"],
              "interet_paye": f["interet_paye"], "investissement": pr["investissement"],
              "salaires_dus": c.salaires_dus_j, "valeur_production": prod, "ventes_menages_ht": ventes_m}
    for k, x in lignes.items():
        c.jour[k] = x
        if k != "salaires_dus": c.mois[k] += x; c.cumul[k] += x
    c.caisse, c.stocks_val, c.creances, c.dettes_banque, c.dettes_autres = caisse, st, detenues, encours, dettes_autres
    for k in PROPRES: pr[k] = 0.0


def _cumul_livre(p, d):
    """Ce que le grand livre a vu passer depuis l installation, pour les classes des unites, par ( motif, payeur,
    receveur ) : les jours clos plus le jour en cours, moins le jour de l installation avant elle."""
    out = dict(d.livre_clos)
    for (mo, pa, re), (s, n) in p.socle.livre.jour_argent.items():
        if pa in CLASSES_UNITES or re in CLASSES_UNITES: out[(mo, pa, re)] = out.get((mo, pa, re), 0.0) + s
    for k, s in d.livre_base.items(): out[k] = out.get(k, 0.0) - s
    return out


def exterieur_hors_livre(p):
    """L argent que le moteur E1 fait entrer ou sortir A LA MAIN depuis l installation ( ventes au port des marches :
    or et surplus de nourriture ; importations et or de l Etat - monde.py 136, 145, 516, 522 ), et la part de l Etat
    ( son rapprochement ). Rend ( total, part de l Etat ) : le reste est celle des marches."""
    d = p.domaine("economie"); L = p.socle.livre
    net0, ext0, mon0, g0 = d.base_moteur
    net = L.net_par_classe()
    total = ((L.ext["entree"] - ext0["entree"]) - (L.ext["sortie"] - ext0["sortie"])
             + (L.monnaie["emise"] - mon0["emise"]) - (L.monnaie["detruite"] - mon0["detruite"])
             + sum(net.get(k, 0.0) - net0.get(k, 0.0) for k in ("Exterieur", "Emission")))
    etat = (p.w.gouv.caisse - g0) - (net.get("Gouvernement", 0.0) - net0.get("Gouvernement", 0.0))
    return total, etat


def ecarts_grand_livre(p):
    """Par classe d unites ( Entreprise, Marche ) et par groupe de motifs ( credit, principal, interets,
    distributions, autres ) : ce que les comptes du domaine ont ecrit moins ce que le grand livre a vu, depuis
    l installation. A lire a la cloture ( les comptes sont ceux du soir ). Les ventes au port que le moteur ecrit a la
    main pour les marches sont retirees de `autres` ( exterieur_hors_livre ) ; tout autre paiement ecrit a la main
    ( `caisse +=` ) s y voit."""
    d = p.domaine("economie")
    cum = _cumul_livre(p, d)
    ext_total, ext_etat = exterieur_hors_livre(p)
    out = {}
    for classe in CLASSES_UNITES:
        livre = {"credit": 0.0, "principal": 0.0, "interet": 0.0, "distributions": 0.0, "autres": 0.0}
        for (mo, pa, re), s in cum.items():
            if pa == classe and re == classe: continue
            sg = 1.0 if re == classe else -1.0 if pa == classe else 0.0
            if sg: livre[GROUPES_MOTIFS.get(mo, "autres")] += sg * s
        us = [c for c in d.unites if type(c.unite).__name__ == classe]
        moi = {"credit": math.fsum(c.cumul["credit"] for c in us),
               "principal": -math.fsum(c.cumul["principal_paye"] for c in us),
               "interet": -math.fsum(c.cumul["interet_paye"] for c in us),
               "distributions": -math.fsum(c.cumul["dividendes"] + c.cumul["boni"] for c in us)}
        total = math.fsum(c.caisse - c.caisse0 for c in us)
        moi["autres"] = total - math.fsum(moi.values())
        vol = math.fsum(abs(s) for s in cum.values())
        out[classe] = {g: (moi[g] - livre[g]) for g in livre}
        if classe == "Marche":
            out[classe]["autres"] -= ext_total - ext_etat
            out[classe]["exterieur_moteur"] = ext_total - ext_etat
        out[classe]["tolerance"] = R.tolerance(abs(total), vol + abs(ext_total))
    return out


def _cloture(p, comptes):
    """Les comptes clos du grand livre du jour, pour le recoupement."""
    d = p.domaine("economie")
    for mo, pa, re, s, n in comptes["argent"]:
        if pa in CLASSES_UNITES or re in CLASSES_UNITES: d.livre_clos[(mo, pa, re)] = d.livre_clos.get((mo, pa, re), 0.0) + s


def _dividendes(p, d):
    """Fin de mois : chaque entreprise a proprietaire verse la moitie du resultat du mois, sans descendre sous un mois de
    salaires ni sous des capitaux propres nuls ; l impot sur le revenu comme le moteur le prelevait."""
    w = p.w; L = p.socle.livre; g = w.gouv
    dis = p.col("menage", "dissous"); rv = p.col("menage", "eco_revenu")
    for c in d.unites:
        h = d.proprietaires.get(c.id)
        if h is None or c.liquidee or h.menage is None or dis[h.menage.id]: continue
        e = c.unite
        x = min(PART_DISTRIBUEE * c.mois["resultat"], e.caisse - RESERVE_TRESORERIE_J * c.salaires_lisses, c.cp)
        if x <= 1.0: continue
        paye = L.transferer(e, h.menage, x, "dividende")
        L.transferer(h.menage, g, paye * g.impot_revenu, "impot")
        c.propres["dividendes"] += paye
        rv[h.menage.id] += ALPHA_REVENU * paye * (1.0 - g.impot_revenu)
        p.compter("dividende_verse", paye)


def _faillites(p, d):
    for c in d.unites:
        if c.nature != "entreprise" or c.liquidee: continue
        c.cessation = c.cessation + 1 if (c.cp < 0.0 and c.tresorerie_nulle) else 0
        if c.cessation >= JOURS_CESSATION: liquider(p, c.unite)


def mesurer_chomage(p):
    """Le chomage au sens du BIT, compte sur les habitants : actifs = vivants de 16 a 64 ans qui ne sont ni enfants ( a
    l ecole ) ni retraites ; chomeurs = actifs sans lieu de travail. Inscrits : ceux que `licencier` a portes au
    registre ; un ecart dit qu un domaine a retire un emploi sans le dire. Sous-emploi : la part des heures que les
    entreprises n ouvrent pas ( activite sous 1 ), ponderee par leurs salaries."""
    w = p.w; d = p.domaine("economie")
    tb = w.table; nh = tb.n                        # colonnes du moteur ( 24/09 )
    nj = p.col("habitant", "naissance_j")
    ro = tb.role[:nh]
    act = (tb.vivant[:nh] == 1) & (ro != PO.CODE_ROLE["enfant"]) & (ro != PO.CODE_ROLE["retraite"])
    age = (p.jour - nj[:nh].astype(np.int64)) / POP.JOURS_AN
    act &= (C.AGE_TRAVAIL <= age) & (age < C.AGE_RETRAITE)
    sans = act & (tb.travail[:nh] < 0)
    actifs = int(np.count_nonzero(act)); chom = int(np.count_nonzero(sans))
    ks = np.fromiter(d.chomeurs.keys(), np.int64, len(d.chomeurs))
    inscrits = int(np.count_nonzero(sans[ks[(ks >= 0) & (ks < nh)]]))
    eff = inact = 0.0
    for c in d.unites:
        if c.nature != "entreprise" or c.liquidee: continue
        n = len(_ids_salaries(p, c.unite)); eff += n; inact += n * (1.0 - max(0.0, min(1.0, c.unite.activite)))
    return {"jour": p.jour, "actifs": actifs, "chomeurs": chom, "inscrits": inscrits, "non_inscrits": chom - inscrits,
            "taux": chom / actifs if actifs else 0.0, "sous_emploi": inact / eff if eff else 0.0,
            "epargne_forcee": float(p.col("menage", "eco_epargne_forcee")[:len(w.menages)].sum())}


def _cloturer(p):
    """23 h 50, apres les banques : les comptes de chaque unite, le recoupement avec le grand livre, les notes de la
    decision, les faillites, les dividendes de fin de mois, le chomage."""
    d = p.domaine("economie"); w = p.w
    cr = _creances_par_detenteur(p)
    for c in d.unites: _tenir_comptes(p, d, c, cr)
    d.ecarts_livre = ecarts_grand_livre(p)
    for ec in d.ecarts_livre.values():
        d.pire_livre = max(d.pire_livre, max(abs(v) for k, v in ec.items() if k not in ("tolerance", "exterieur_moteur"))
                           / ec["tolerance"])
    _noter_activite(p, d)
    for c in d.unites:
        if c.nature == "entreprise": c.produit_vu = dict(c.unite.produit_du_jour)
    for em in d.marches.values():
        for b in em.ventes_jour: em.ventes_jour[b] = 0.0
    _faillites(p, d)
    if p.jour % MOIS_J == MOIS_J - 1:
        _dividendes(p, d)
        for c in d.unites:
            c.mois_clos = c.mois; c.mois = {k: 0.0 for k in LIGNES}
    d.serie.append(mesurer_chomage(p))


# ================================================================== la liquidation
def liquider(p, e, motif="faillite"):
    """Une entreprise en cessation des paiements est liquidee :
      1. ses salaries sont licencies ; leurs heures du jour et une indemnite deviennent des creances de rang salarial ;
      2. ses stocks sont cedes au marche de sa region a moitie de leur valeur ( ce que le marche peut payer ) ;
      3. son capital fixe est mis au rebut ( pas de marche de l occasion industrielle ) ;
      4. ses creanciers sont payes dans l ordre legal - salaries, Etat, banques, fournisseurs -, au marc le franc dans un
         rang ; ce qui reste du est abandonne ( les prets restent au domaine 2, qui les menera au defaut ) ;
      5. le boni, s il en reste, va au proprietaire.
    Rend le rapport : disponible, et par rang ( du, paye )."""
    w = p.w; d = p.domaine("economie"); L = p.socle.livre; K_ = p.socle.creances
    c = d.comptes[e.id]
    if c.liquidee: raise ValueError(f"{e.id} deja liquidee")
    m = w.marches[e.lieu.marche.id]
    gens = salaries(p, e)
    for h in gens:
        s = PO.SALAIRE_HORAIRE.get(h.role, 0)
        if h.heures_jour > 0 and s > 0:
            K_.constater(h.menage, e, s * h.heures_jour, "salaire", p.jour); h.heures_jour = 0.0
        if s > 0: K_.constater(h.menage, e, INDEMNITE_JOURS * 8.0 * s, "indemnite_licenciement", p.jour)
        licencier(p, h, motif)
    valeur = _valeur_stocks(w, e, m)
    prix = DECOTE_LIQUIDATION * valeur
    paye = L.transferer(m, e, prix, "cession_liquidation") if prix > 0 else 0.0
    frac = paye / prix if prix > 0 else 0.0
    for b in list(e.stocks):
        x = e.stocks[b] * frac
        if x > 0: e.stocks[b] -= x; m.stocks[b] += x
    c.propres["rebut"] += max(0.0, c.capital_net()); c.amort_cumule = c.capital_brut
    disponible = e.caisse
    rapport = {"unite": e.id, "jour": p.jour, "disponible": disponible, "cession": paye}
    bq = p.domaine("banques")

    def rang(cr):
        if cr.motif in MOTIFS_SALARIES and type(cr.creancier) is PO.Menage: return "salaries"
        if cr.creancier is w.gouv: return "etat"
        if cr.motif == "recouvrement_pret": return "banques"
        return "fournisseurs"
    dettes = {r: [] for r in RANGS}
    for cr in sorted(K_.de(e), key=lambda x: x.id): dettes[rang(cr)].append(cr)
    prets = [bq.prets[i] for i in sorted(bq.prets_de.get(e, ()))]
    for r in RANGS:
        du = math.fsum(cr.montant for cr in dettes[r])
        if r == "banques": du += math.fsum(pr.principal + pr.du_interet for pr in prets)
        avant = e.caisse
        if du > 0 and avant > 0:
            k = min(1.0, avant / du)
            for cr in dettes[r]: K_.regler(cr, L, cr.montant * k)
            if r == "banques":
                for pr in prets:
                    if pr.id not in bq.prets: continue
                    voulu = (pr.principal + pr.du_interet) * k
                    if pr.defaut_j >= 0 or pr.du_interet + pr.du_principal >= voulu:
                        BQ.rembourser_par_anticipation(p, pr, 0.0)
                    else:
                        BQ.rembourser_par_anticipation(p, pr, max(0.0, voulu - pr.du_interet - pr.du_principal))
        rapport[r] = (du, avant - e.caisse)
    for cr in list(K_.de(e)): K_.abandonner(cr, "faillite")
    h = d.proprietaires.get(e.id)
    if e.caisse > 0 and h is not None and h.menage is not None:
        boni = L.transferer(e, h.menage, e.caisse, "boni_liquidation"); c.propres["boni"] += boni
        rapport["boni"] = boni
    e.activite = 0.0
    c.liquidee, c.liquidee_j = True, p.jour
    d.offres.pop(e.id, None)
    d.faillites.append(rapport)
    p.noter("faillite", unite=e.id, actif=round(disponible + valeur, 2),
            passif=round(math.fsum(rapport[r][0] for r in RANGS), 2), salaries=len(gens))
    return rapport


# ================================================================== l emploi ( API du domaine 4 )
def embaucher(p, h, unite, role=None, equipe=None):
    """`h` entre chez `unite` ( entreprise du moteur, ou marche avec role marchand ou convoyeur ) : metier, lieu,
    horaire du metier ; l index du moteur est tenu tout de suite ; le registre des chomeurs le retire."""
    w = p.w; d = p.domaine("economie")
    if not h.vivant: raise ValueError(f"habitant {h.id} mort")
    role = role or (unite.role if type(unite).__name__ != "Marche" else "marchand")
    if role not in PO.TRAVAIL: raise ValueError(f"metier inconnu {role!r}")
    if h.travail is not None: licencier(p, h, "mutation", inscrire=False)
    h.role, h.classe = role, C.ROLES[role][1]
    h.travail, h.horaire = unite.lieu, PO.TRAVAIL[role][1]
    if equipe is not None: h.equipe = int(equipe)
    w._par_travail.setdefault((unite.lieu.id, role), []).append(h)
    w._lieux_par_role.setdefault(role, set()).add(unite.lieu)
    d.chomeurs.pop(h.id, None)
    p.noter("embauche", habitant=h.id, unite=getattr(unite, "id", unite.lieu.id))
    if p.a("agenda"): importlib.import_module(".d05_agenda", __package__).replanifier(p, h)


def licencier(p, h, motif="economique", inscrire=True):
    """`h` perd son emploi : plus de lieu ni d horaire de travail ( il reste chez lui, la paie ne lui doit plus d heures ),
    son metier reste sa qualification ; il entre au registre des chomeurs."""
    w = p.w; d = p.domaine("economie")
    lieu, role = h.travail, h.role
    if lieu is None: return
    lst = w._par_travail.get((lieu.id, role))
    if lst is not None and h in lst: lst.remove(h)
    h.travail, h.horaire = None, None
    if h.poste == "travail": h.lieu, h.poste = h.domicile, "maison"
    if inscrire:
        d.chomeurs[h.id] = [p.jour, lieu.id, role, motif]
        p.noter("licenciement", habitant=h.id, unite=lieu.id, motif=motif)
    if p.a("agenda"): importlib.import_module(".d05_agenda", __package__).replanifier(p, h, rentrer=True)


def masse_salariale(p, unite):
    """{ jour : salaires dus pour les heures du jour ( 17 h 50 ), lisse : moyenne 30 jours, mois : cumul du mois,
    effectif }."""
    c = p.domaine("economie").comptes[_id_unite(unite)]
    return {"jour": c.salaires_dus_j, "lisse": c.salaires_lisses, "mois": c.mois["salaires_dus"],
            "effectif": len(_ids_salaries(p, unite))}


def offres_d_emploi(p):
    """{ unite : postes } : les entreprises a plein regime dont la region manque encore de leur produit, et ce que la
    demande en attente de services paierait ( `offres_services` )."""
    return dict(p.domaine("economie").offres)


def offres_services(p, salaire_horaire=None):
    """{ marche : emplois } : ce que la demande en attente de restauration et de services divers de la region paierait
    en emplois a plein temps ( 8 heures, 6 jours sur 7 ) au salaire d un ouvrier du moteur, en moyenne depuis
    l installation : le signal que le domaine 4 attend pour ouvrir des emplois de services."""
    d = p.domaine("economie")
    s = salaire_horaire or PO.SALAIRE_HORAIRE["ouvrier"]
    ks = [NOMS_CATEGORIES.index("restauration"), NOMS_CATEGORIES.index("divers")]
    return {mid: float(d.attente_region[mid][ks].sum()) / (p.jour + 1) / (s * 8.0 * 6.0 / 7.0) for mid in d.ids_marches}


def chomage(p):
    """Les indicateurs du dernier soir ( mesurer_chomage )."""
    d = p.domaine("economie")
    return d.serie[-1] if d.serie else mesurer_chomage(p)


# ================================================================== les comptes ( API des domaines 4, 6, 9 a 11 )
def _id_unite(unite):
    return f"marche@{unite.lieu.id}" if type(unite).__name__ == "Marche" else unite.id


def comptes(p, unite):
    return p.domaine("economie").comptes[_id_unite(unite)]


def bilan(p, unite):
    c = comptes(p, unite)
    return {"tresorerie": c.caisse, "stocks": c.stocks_val, "capital_net": c.capital_net(), "creances": c.creances,
            "dettes_banque": c.dettes_banque, "autres_dettes": c.dettes_autres, "capitaux_propres": c.cp,
            "ecart": c.ecart}


def compte_de_resultat(p, unite, periode="jour"):
    c = comptes(p, unite)
    return dict({"jour": c.jour, "mois": c.mois, "mois_clos": c.mois_clos, "cumul": c.cumul}[periode])


def assiette_tva(p):
    """{ marche : { bien : ventes hors taxe aux menages, cumul } } : la base de la TVA ( domaine 6 applique ses taux
    par categorie du catalogue )."""
    d = p.domaine("economie")
    return {mid: dict(em.ventes_ht) for mid, em in d.marches.items()}


def assiette_is(p):
    """{ unite : resultat du dernier mois clos } ( positif ou negatif : le report des pertes est au domaine 6 )."""
    return {c.id: c.mois_clos["resultat"] for c in p.domaine("economie").unites}


def investir(p, unite, montant, fournisseur=None, motif="investissement"):
    """L unite achete du capital fixe : elle paie `fournisseur` ( un detenteur inscrit ) ou l exterieur ( machine
    importee ) ; le capital brut monte de ce qui est paye. Rend le montant paye."""
    L = p.socle.livre; c = comptes(p, unite)
    paye = L.transferer(unite, fournisseur, montant, motif) if fournisseur is not None else L.payer_l_exterieur(unite, montant, motif)
    c.capital_brut += paye; c.propres["investissement"] += paye
    return paye


def apporter(p, unite, apporteur, montant):
    """Un apport en capital ( le proprietaire, l Etat ) : la caisse et les capitaux propres montent ensemble."""
    paye = p.socle.livre.transferer(apporteur, unite, montant, "apport_capital")
    comptes(p, unite).propres["apports"] += paye
    return paye


def reevaluer_capital(p, unite, valeur_nette, duree_vie_ans=None):
    """Un domaine qui reprend une entreprise ( 9, 10, 11 ) remplace son capital comptable par la valeur de ses objets
    ( Parc ) : l ecart passe en capitaux propres ( ecart de reevaluation ), pas en resultat."""
    c = comptes(p, unite)
    if not valeur_nette >= 0.0: raise ValueError(f"valeur nette invalide : {valeur_nette!r}")
    c.propres["reevaluation"] += valeur_nette - c.capital_net()
    c.capital_brut, c.amort_cumule = float(valeur_nette), 0.0
    if duree_vie_ans is not None: c.duree_vie_j = float(duree_vie_ans) * JOURS_AN


def demande_en_attente(p):
    """{ marche : { division : drachmes voulues que rien ne sert, cumul } }."""
    d = p.domaine("economie")
    return {mid: {NOMS_CATEGORIES[k]: float(x) for k, x in enumerate(a) if x} for mid, a in d.attente_region.items()}


def budget_des_menages(p):
    """Les parts du budget voulu, mesurees depuis l installation : ensemble et par quintile de revenu lisse."""
    B = p.domaine("economie").budget
    tot = B.sum()
    return {"parts": dict(zip(NOMS_CATEGORIES, (B.sum(axis=0) / tot).tolist())) if tot > 0 else {},
            "alimentation_par_quintile": (B[:, I_ALIM] / np.maximum(1e-12, B.sum(axis=1))).tolist(),
            "elstat": dict(zip(NOMS_CATEGORIES, PARTS.tolist()))}


# ================================================================== installation
def _revenu_attendu(h, impot):
    """Le revenu journalier qu un metier rapporte, pour la premiere estimation du revenu lisse."""
    r = h.role
    if not h.vivant or r == "enfant": return 0.0
    if r == "retraite": return float(PO.PENSION_JOUR)
    if r == "paysan": brut = 1.2 * 8 * PARITE_EXPORT * PM["nourriture"] * (1.0 - MARGE_DETAIL)
    elif r == "marchand": brut = REVENU_MARCHAND_J
    elif r == "patron": brut = REVENU_PATRON_J
    else: brut = PO.SALAIRE_HORAIRE.get(r, 0) * 8.0
    return brut * (1.0 - impot)


def installer(p):
    w = p.w; L = p.socle.livre
    L.declarer_motif("epargne_initiale", "financier", "economie")
    L.declarer_motif("cession_liquidation", "achat", "economie")
    L.declarer_motif("boni_liquidation", "revenu_propriete", "economie")
    L.declarer_motif("indemnite_licenciement", "remuneration", "economie")
    L.declarer_motif("investissement", "achat", "economie")
    L.declarer_motif("apport_capital", "financier", "economie")
    J = p.socle.journal
    J.declarer("faillite", "economie", "individuel", ("unite", "actif", "passif", "salaries"))
    J.declarer("licenciement", "economie", "individuel", ("habitant", "unite", "motif"))
    J.declarer("embauche", "economie", "individuel", ("habitant", "unite"))
    for t in ("achat_menages", "rupture_de_stock", "demande_en_attente", "achat_durable", "credit_economie",
              "dividende_verse"):
        J.declarer(t, "economie", "compte")
    cm = p.colonnes["menage"]
    for nom, dt, defaut in (("eco_revenu", np.float64, 0.0), ("eco_equipement", np.float64, 0.0),
                            ("eco_epargne_forcee", np.float64, 0.0), ("eco_credit_j", np.int32, -100000),
                            ("eco_dernier_achat", np.int32, -1)):
        cm.ajouter(nom, dt, defaut)
    cm.assurer(len(w.menages))
    d = Economie()
    p.domaines["economie"] = d
    # --- les marches : marge du detaillant, prix repris, demande de depart ( celle qui tient la couverture a sa cible )
    d.ids_marches = sorted(w.marches)
    d.rang_marche = {k: i for i, k in enumerate(d.ids_marches)}
    for k in d.ids_marches:
        m = w.marches[k]
        m.marge = MARGE_DETAIL
        dem = {b: 0.0 for b in C.BIENS}
        for b, cible in COUVERTURE_CIBLE_J.items(): dem[b] = max(DEMANDE_MIN, m.stocks[b] / cible)
        dem["nourriture"] = max(DEMANDE_MIN, C.NOURRITURE_PAR_JOUR * w._pop_marche.get(k, 0))
        d.marches[k] = EtatMarche(k, dem)
        d.attente_region[k] = np.zeros(K)
        m.ajuster_prix = AjusterPrix(p, k)
        m.prix["or"] = PM["or"]
    # --- les unites : capital a mi-vie, proprietaires sortis du moteur ( la distribution est ici )
    for e in sorted(w.entreprises.values(), key=lambda e: e.id):
        n = len(salaries(p, e))
        val, vie = CAPITAL_PAR_POSTE.get(e.type, (40000.0, 20))
        c = Comptes(e.id, e, "entreprise", e.lieu.marche.id, val * n, vie)
        c.effectif = n
        d.comptes[e.id] = c
        if e.proprietaire is not None:
            d.proprietaires[e.id] = e.proprietaire; e.proprietaire = None
        for b in e.produits: d.producteurs.setdefault((e.lieu.marche.id, b), []).append(e.id)
    for k in d.ids_marches:
        m = w.marches[k]
        val, vie = CAPITAL_MARCHE_PAR_POSTE
        n = len(salaries(p, m))
        c = Comptes(f"marche@{k}", m, "marche", k, val * n, vie)
        c.effectif = n
        d.comptes[c.id] = c
    d.unites = [d.comptes[k] for k in sorted(d.comptes)]
    # --- les menages : revenu attendu, epargne recalibree, equipement a son age de regime
    n = len(w.menages)
    rv = p.col("menage", "eco_revenu")
    for h in w.habitants:
        if h.menage is not None: rv[h.menage.id] += _revenu_attendu(h, w.gouv.impot_revenu)
    v, classe = _tableaux_menages(p)
    ok = (v > 0) & (p.col("menage", "dissous")[:n] == 0)
    cible = tampon_vise(classe, rv[:n])
    for i in np.nonzero(ok)[0].tolist():
        mg = w.menages[i]
        x = float(cible[i]) - mg.caisse
        if x > 0: d.recalibrage += L.recevoir_de_l_exterieur(mg, x, "epargne_initiale")
    mi = _rang_marche_menages(w, d, n)
    pn = np.array([w.marches[k].prix["nourriture"] for k in d.ids_marches])[mi] * (1.0 + w.gouv.tva)
    u = p.hasard("economie_equipement").random(n)
    # l age de l equipement en regime : il descend de 1 a 0,8 de sa cible a vitesse constante ( exponentielle )
    p.col("menage", "eco_equipement")[:n] = np.where(ok, equipement_vise(rv[:n], C.NOURRITURE_PAR_JOUR * v * pn)
                                                     * SEUIL_RENOUVELLEMENT ** u, 0.0)
    # --- le bilan d ouverture
    cr = _creances_par_detenteur(p)
    for c in d.unites: _tenir_comptes(p, d, c, cr, ouverture=True)
    for (mo, pa, re), (s, _) in L.jour_argent.items():
        if pa in CLASSES_UNITES or re in CLASSES_UNITES: d.livre_base[(mo, pa, re)] = s
    d.base_moteur = (L.net_par_classe(), dict(L.ext), dict(L.monnaie), w.gouv.caisse)
    for c in d.unites:
        if c.nature == "entreprise": c.produit_vu = dict(c.unite.produit_du_jour)
    d.decideur = p.decideur(POINT_ACTIVITE)
    w.achats = RemplaceAchats(p)
    w.regler_activite = RemplaceRegler(p)
    p.routine(6, 30, "economie", _concurrence)
    p.routine(9, 19, "economie", _suspendre_exceptionnelle)
    p.routine(9, 21, "economie", _retablir_exceptionnelle)
    p.routine(9.5, 30, "economie", _credits)
    p.routine(17 + 40 / 60, 30, "economie", _tresorerie_de_paie)
    p.routine(17 + 50 / 60, 30, "economie", _avant_paie)
    p.routine(18, 30, "economie", _apres_paie)
    p.routine(23 + 50 / 60, 97, "economie", _cloturer)
    p.cloture("economie", _cloture)
    return d
