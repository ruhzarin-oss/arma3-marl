"""DOMAINE 7 - RESTE DU MONDE : ECHANGES, CHANGE, BALANCE DES PAIEMENTS, MIGRATIONS EXTERNES.

FICHE
1. Classes. MondeExterieur ( les prix mondiaux en euros : marche aleatoire du logarithme rappelee vers son niveau,
   facteur commun par famille, energie qui entraine l alimentation, saison agricole, chocs ), Negociant ( un importateur
   exportateur du port, un par marche : caisse, entrepot = Stock du socle, lots en attente de vente ), Contrebandier ( un
   reseau par ile : caisse, Stock ), Douane ( les declarations du jour, les cumuls par bien et par sens, les alertes du
   rapprochement douanier ), BalanceDesPaiements ( les lignes du jour et leurs cumuls, en drachmes, les reserves, les
   erreurs et omissions ), ContexteImport ( ce que le negociant voit quand il commande ), StockE1 ( un dictionnaire du
   moteur vu comme un stock du socle ), RemplaceImporter et RemplaceExporterOr ( les methodes du moteur reprises ),
   Exterieur ( l etat du domaine : parite, reserves de change en euros, migrants, compteurs ). Colonnes par habitant :
   ext_emigre_j ( jour du depart a l etranger, -1 ), ext_immigre_j ( jour de l arrivee, -1 ).
2. Invariants. Toute drachme qui franchit la frontiere passe par `recevoir_de_l_exterieur` / `payer_l_exterieur` sous
   un motif declare ; tout bien par `livre.importer` / `livre.exporter`. BALANCE DES PAIEMENTS, chaque soir, au centime :
   biens ( declarations en douane : valeur transactionnelle, accord de l OMC art. 1 ) + services + revenus primaires +
   revenus secondaires + compte de capital + compte financier + contrebande = variation des avoirs de reserve ( le
   compteur exterieur du grand livre ) + erreurs et omissions, et les erreurs et omissions sont NULLES ; la balance
   PUBLIEE ( sans la contrebande, que la douane ne voit pas ) garde la contrebande dans ses erreurs et omissions, comme
   une vraie. RAPPROCHEMENT DOUANIER : pour chaque motif, les biens importes ou exportes que le grand livre a vus = les
   quantites declarees ( motifs du domaine ) ; tout bien entre sans paiement sous le meme motif est une alerte ; tout
   flux de biens ecrit a la main ( livre.flux sans ligne ) aussi. RESERVES : euros = depart + somme des flux exterieurs,
   chacun au taux du jour. Detient : l argent et les biens des negociants ( famille `negociants` ) et des contrebandiers
   ( famille `contrebandiers` ). MIGRANTS : vivants = vivants du depart + naissances - deces + immigres - emigres ; un
   emigre n est pas mort ( ni deces compte, ni heritage, ni declaration ) ; aucun mineur laisse sans adulte.
3. Decision `importer` ( chaque negociant, pour chacun des 7 biens importables, a 8 h, 12 h et 16 h : 63 decisions
   par jour sur Altis ) : attendre, demi_jour, un_jour, trois_jours ( jours de la demande lissee de SON marche ). Traits :
   couverture du marche, entrepot et commandes en mer, prix d achat du marche sur la parite a l import, tendance du prix
   mondial, manque d hier, tresorerie, reserves de change publiees, bien essentiel. Note ( horizon 5 jours : 2 jours de
   mer + 3 jours de vente ) : chaque jour, pour CE lot, la marge realisee sur ses ventes a SON marche ( sur la valeur d un
   jour de demande ) + les unites servies alors que son marche avait moins d un jour de stock ( en jours de demande ) -
   les pertes de stockage ; au dernier jour, 10 % du cout des invendus ; attendre vaut zero. Ni le profit seul ( il
   affame : une unite servie en manque vaut ici autant qu un jour de marge ), ni le manque du marche ce jour-la ( il est
   le meme pour tous les choix du jour sur ce marche : premiere version, epsilon carre 0,002 ). Regle : commander ce
   qui manque pour tenir la couverture visee + le delai de mer, si le marche peut racheter au prix d import ( ou si le
   bien est essentiel et le marche a moins d un jour ). Temoin : toujours un jour ( expedier sans condition ).
4. Evenements. Individuels : emigration, immigration, devaluation, choc_prix_mondial, saisie_douane. Comptes :
   import_negoce, export_negoce, commande_annulee, controle_des_changes, contrebande_passee, envoi_de_fonds, aide_ue,
   depart_empeche.
5. Liens. Remplace Monde.importer et Monde.exporter_or ( proprietaire ) ; Monde.commerce_exterieur est garde : il
   n y touche aucune caisse ( voyages entre iles ). Les ventes au port des lignes 516 et 522 de monde.py sont dans
   Monde.expedier ( proprietaire : logistique ) : NEUTRALISEES PAR UNE DONNEE - a chaque heure pleine moins 10, le negoce
   rachete l or des marches et la nourriture au-dela du seuil du moteur ( 3 jours + 50 ) et les exporte par le grand
   livre ; a l heure pleine, expedier ne trouve plus rien a vendre ( routine de rang 99 : apres toute vente au marche ;
   au rang 5, les ventes du negoce de 7 h 50 laissaient la ligne 522 exporter a la main - la balance l a vu, 23/09 ).
   Arbitrage a 12 h 50 : quand l etranger paie plus que le marche ne paie ses producteurs, le negoce exporte ( jusqu a un
   jour de stock, une demi-journee de demande par jour ; nourriture, remedes, gazole et brut gardent leur couverture
   visee ). Le prix interieur suit le monde par les QUANTITES : parite a l import ( le negoce ne vend au marche que s il
   peut revendre ) et a l export ; la formation du prix reste au domaine 3. Ecrit chaque matin le prix au port ( drachmes ) de
   chaque bien dans le catalogue du socle ( Bien.prix_monde ) : les domaines qui le lisent ( energie ) suivent le monde.
   Lit : population ( ages, faim7, deplacements, nouveau_menage ), banques ( ouvrir_compte ), economie ( demande lissee,
   non servi, couverture visee ), etat ( taxes_import, percevoir ). Paie et recoit : importations et exportations ( port
   <-> exterieur ), fret maritime ( -> armateurs etrangers ), droits de douane ( -> Etat ), ventes du negoce aux marches,
   investissement direct etranger ( capital des negociants ), aide de l Union ( -> Etat ), epargne des migrants, envois
   de fonds des emigres, contrebande. Classe dans la balance les flux exterieurs des autres domaines par la nature de
   leur motif ( energie : import_combustible, export_petrolier - declares en douane chaque soir, sans rien dupliquer ).
   API en fin de fichier.
6. Portes : tests_d07_exterieur.py.
7. Arma : aucun objet. Un cargo ( C_Boat_Transport_02_F, a verifier ) au quai de Kavala quand un lot debarque : a
   poser par le domaine 15. arma_preuve = None.
8. Cout. Prix mondiaux : un vecteur numpy par jour ( quelques dizaines de biens ). Negoce : marches x biens, 4 passes
   par jour ; balance et douane : les lignes du grand livre du jour. Migrations : une passe vectorisee sur les habitants
   par jour ( ages, faim ), une boucle sur les seuls migrants. Mesure du 23/09 ( test_cout, 10 005 habitants ) : 9 ms par
   jour, 0,6 % d une journee du moteur, 0,9 us par habitant ( migrations 6 ms ) : ~ 1 s par jour a 1 million d habitants,
   ~ 45 s a 50 millions ( la passe des migrations domine ; le negoce suit le nombre de marches, pas la population )."""
import math, time
from collections import deque
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D, registre as R, biens as BI
from . import pays as PAYS, d01_population as POP, d02_banques as BQ, d03_economie as EC, d06_etat as ET

EPS = 1e-9
JOURS_AN = 365.0
EUROS_PAR_DRACHME = PAYS.EUROS_PAR_DRACHME   # la parite de depart : le taux commun du pays

# ================================================================== les prix mondiaux ( euros )
# Volatilite annuelle du logarithme du prix, par famille : Brent 2000-2020 ~ 35 % ( EIA ) ; indice FAO des prix
# alimentaires ~ 15-20 % par an ; metaux de base du LME ~ 25 % ; or ~ 15 % ( a part ) ; produits manufactures et
# pharmaceutiques : prix a l exportation de 3 a 5 % par an ( a calibrer ).
VOLATILITE = {"aliment": 0.18, "eau": 0.0, "matiere_premiere": 0.25, "energie": 0.35, "materiau": 0.15, "chimie": 0.20,
              "produit_fini": 0.05, "piece": 0.05, "sante": 0.03, "munition": 0.05}
VOLATILITE_BIEN = {"or": 0.15}
CORRELATION_FAMILLE = 0.6         # part de la variance commune a la famille ( a calibrer )
ENERGIE_DANS_ALIMENT = 0.3        # charge du choc energetique sur l alimentation ( engrais, transport ; Baffes 2007, a calibrer )
DEMI_VIE_RAPPEL_J = 2 * 365       # retour vers le niveau de long terme : demi-vie de deux ans ( Pindyck 1999, a calibrer )
THETA = math.log(2.0) / DEMI_VIE_RAPPEL_J
SAISON_ALIMENT = 0.06             # +-6 % sur l annee, le creux a la moisson ( fin juillet ; ble, USDA, a calibrer )
JOUR_MOISSON = 200
PROBA_CHOC_PETROLE_AN = 0.1       # 1973, 1979, 1990, 2008, 2022 : environ un par decennie
FACTEUR_CHOC_PETROLE = 1.6        # 2022 : Brent de 78 a 123 dollars en trois mois ( +58 % )
DEMI_VIE_CHOC_J = 365

# ================================================================== le change et les reserves
# Regime : PARITE FIXE AJUSTABLE, defendue par les reserves de la banque centrale. Pourquoi pas un change flottant : un
# marche des changes a besoin de nombreux participants ; sur une ile de quelques milliers d habitants, le cours flotterait
# sur une poignee d ordres. C est le regime de la drachme de 1975 a 2001 ( parite glissante puis SME ), avec des
# devaluations discretes : 15,5 % en 1983, 15 % en 1985, 12,3 % a l entree dans le MCE II en 1998.
# Reserves de depart : six mois d importations ( Banque de Grece 1997 : ~ 13 milliards de dollars pour ~ 27 milliards
# d importations annuelles ) au niveau grec de 2019 ( ELSTAT : ~ 63 milliards d euros d importations, 5 900 par habitant ).
# Premiere version : 1 000 euros par habitant, soit 1,6 mois des importations mesurees du pays ( 23/09 ). A calibrer.
RESERVES_EUROS_HAB = 2950.0
COUVERTURE_MIN_MOIS = 3.0         # regle du FMI : trois mois d importations
DEVALUATION = 0.15
DELAI_DEVALUATION_J = 180
HISTOIRE_MIN_J = 60
PLANCHER_RESERVES = 0.0           # euros : sous ce plancher, la banque centrale refuse les devises ( controle des changes )

# ================================================================== le port
# Fret et assurance en part de la valeur FOB, par famille : ~ 5 a 8 % pour un pays developpe, 10-20 % pour le vrac
# ( CNUCED, Review of Maritime Transport ; a calibrer ).
FRET = {"aliment": 0.10, "eau": 0.20, "matiere_premiere": 0.12, "energie": 0.05, "materiau": 0.10, "chimie": 0.06,
        "produit_fini": 0.05, "piece": 0.05, "sante": 0.03, "munition": 0.05}
FRAIS_OR = 0.005                  # essai et assurance d un lingot ( a calibrer )
DELAI_MER_J = 2                   # une commande au fournisseur etranger arrive deux jours plus tard ( a calibrer )
MARGE_NEGOCE = 0.03               # marge du negociant sur son cout rendu ( grossiste, a calibrer )
PERTE_STOCKAGE_J = {"aliment": 0.002}   # nourriture en entrepot portuaire : 0,2 % par jour ( a calibrer )
CAPITAL_NEGOCE_HAB = 100.0        # drachmes de capital par habitant servi, apportes par un investisseur etranger ( a calibrer )
BIENS_IMPORT = ("nourriture", "carburant", "remedes", "outils", "fer", "zinc", "petrole")
ESSENTIELS = ("nourriture", "remedes")
SEUIL_ARBITRAGE = 0.03            # le negoce exporte quand la parite depasse de 3 % ce que le marche paie ses producteurs
GARDE_EXPORT_J = 1.0              # ... et laisse au marche un jour de demande : c est en passant SOUS sa couverture visee
                                  # que le marche monte son prix ( domaine 3 ), jusqu a la parite a l export ( premiere
                                  # version : la moitie de la cible, jamais atteinte - des marches de flux tendu, un choc
                                  # de +60 % ne montait le gazole que de 1 % )
COUVERTURE_EXPORT_NOURRITURE_J = 3.0   # la regle du moteur : trois jours de nourriture restent au marche ; les remedes
                                  # gardent toute leur couverture visee : un bien essentiel ne part pas sous sa cible
CAPACITE_EXPORT_J = 0.5           # au plus une demi-journee de demande exportee par jour, par marche et par bien ( les
                                  # places sur les caboteurs ; a calibrer ) : le prix interieur suit sans a-coup
PART_STOCK_EXPORT = 0.1           # ... ou un dixieme du stock, pour un bien que le marche n ecoule pas
# Biens proteges de l arbitrage a l export ( gardent toute leur couverture visee ) : les essentiels, et l energie dont
# vivent les convois et les centrales. Mesure du 23/09 : exporter le brut et le gazole jusqu a un jour de stock, trois
# jours de demande par jour, transmettait un choc de +60 % au gazole ( x 1,46 ) mais vidait la raffinerie de son brut :
# plus de gazole au jour 21, plus de convois, 100 % des menages sans nourriture au jour 25.
PROTEGES_EXPORT = ESSENTIELS + ("carburant", "petrole")
URGENCE_J = 1.0                   # sous un jour de stock, un bien essentiel est rachete meme a perte
SEUIL_MOTEUR = 50.0               # monde.expedier exporte le surplus de nourriture au-dela de 3 jours + 50 unites
MARGE_SURETE_MOTEUR = 25.0

# ================================================================== la decision
QUANTITES_J = (0.0, 0.5, 1.0, 3.0)
ACTIONS = ("attendre", "demi_jour", "un_jour", "trois_jours")
HEURES_DECISION = (8, 12, 16)
HEURES_VENTE = (7 + 50 / 60, 11 + 50 / 60, 15 + 50 / 60, 18 + 50 / 60)
HORIZON_IMPORT = DELAI_MER_J + 3
LAMBDA_MANQUE = 1.0               # une unite servie a un marche en manque vaut autant qu un jour de demande de marge
PENALITE_INVENDU = 0.10

# ================================================================== les migrations
# ELSTAT, flux migratoires 2019 : 95 020 emigrants ( ~ 55 % de 20 a 39 ans ), 129 459 immigrants, pour 10,7 millions.
# La Grece a perdu ~ 427 000 residents emigres de 2008 a 2013 ( Lazaretou, Banque de Grece, Economic Bulletin 2016 ),
# ~ 400 000 jeunes de 2010 a 2020 : les taux de crise etaient ~ 1,3 fois ceux de 2019 ( FACTEUR_CRISE ).
EMIGRATION_AN = ((18, 0.008), (20, 0.020), (40, 0.009), (65, 0.002))   # par personne et par an, selon l age ( a calibrer )
FACTEUR_CRISE = 1.3
FACTEUR_FAIM_EMIGRATION = 1.0    # un menage qui a eu faim tous les soirs de la semaine voit ses jeunes partir deux fois plus
IMMIGRATION_AN = 129459 / 10.7e6
TAILLE_IMMIGRANTS = ((1, 0.60), (2, 0.25), (3, 0.10), (4, 0.05))   # adultes seuls, couples, familles ( a calibrer )
EPARGNE_IMMIGRANT_EUROS = 2000.0  # par adulte ( a calibrer )
REMISE_EUROS_MOIS = 80.0          # envois de fonds d un emigre adulte ( Banque mondiale, Grece, ordre de grandeur, a calibrer )
EXCLUS_EMIGRATION = ("chef_gouvernement", "ministre")

# ================================================================== l aide et la contrebande
# Fonds de cohesion et structurels, Grece 2014-2020 : ~ 20 milliards d euros sur 7 ans, ~ 270 euros par habitant et par an.
AIDE_UE_EUROS_HAB_AN = 270.0
BIENS_CONTREBANDE = ("carburant", "outils")   # le gazole ( 200 a 300 millions d euros perdus par an, a calibrer )
MARGE_CONTREBANDE = 1.3           # le passeur passe quand il revend 30 % au-dessus de son cout
DECOTE_CONTREBANDE = 0.10         # il vend au marche 10 % sous le prix d achat officiel
PART_CONTREBANDE = 0.05           # jours de demande passes par soir quand c est rentable ( a calibrer )
CONTROLE_DOUANE = 0.10            # probabilite qu un passage soit saisi ( a calibrer ; domaine 21 )
CAPITAL_CONTREBANDE = 2000.0

# ================================================================== la balance des paiements
LIGNES = ("biens", "services", "revenus_primaires", "revenus_secondaires", "capital", "financier", "contrebande",
          "non_classe")
NATURE_LIGNE = {"achat": "biens", "remuneration": "revenus_primaires", "revenu_propriete": "revenus_primaires",
                "impot_production": "revenus_primaires", "subvention": "revenus_primaires",
                "impot_revenu": "revenus_secondaires", "cotisation": "revenus_secondaires",
                "prestation": "revenus_secondaires", "transfert_courant": "revenus_secondaires",
                "transfert_capital": "capital", "financier": "financier", "illegal": "contrebande"}
MOTIFS = {   # motif : ( nature SCN, ligne de la balance ou None si la douane le declare )
    "import_biens": ("achat", None), "export_biens": ("achat", None), "import_etat": ("achat", None),
    "export_or_etat": ("achat", None), "import_sante": ("achat", None), "import_vehicules": ("achat", None),
    "import_armement": ("achat", None),
    "fret_import": ("achat", "services"), "prime_reassurance": ("achat", "services"),
    "indemnite_reassurance": ("transfert_courant", "revenus_secondaires"),
    "vente_import": ("achat", None), "achat_export": ("achat", None),
    "transfert_migrant": ("transfert_capital", "capital"), "envoi_de_fonds": ("transfert_courant", "revenus_secondaires"),
    "aide_ue": ("transfert_capital", "capital"), "investissement_direct": ("financier", "financier"),
    "contrebande": ("illegal", "contrebande")}
MOTIFS_DECLARES = ("import_biens", "export_biens", "import_etat", "export_or_etat", "import_sante", "import_vehicules",
                   "import_armement")
MOTIFS_IMPORT_API = ("import_biens", "import_sante", "import_vehicules", "import_armement", "import_etat")
SANS_PAIEMENT_ADMIS = ("effets_migrants",)   # BPM6 10.18 : les effets personnels des migrants ne sont pas des transactions


# ================================================================== les classes
class StockE1:
    """Un dictionnaire de stocks du moteur ( nom -> quantite ) vu comme un stock du socle ( identifiant -> quantite ) :
    le grand livre y ecrit ses sources, puits et deplacements, avec leur motif."""
    __slots__ = ("d", "cat")

    def __init__(self, d, cat): self.d, self.cat = d, cat

    def _ajouter(self, b, q):
        n = self.cat.biens[b].nom; self.d[n] = self.d.get(n, 0.0) + q

    def _retirer(self, b, q):
        n = self.cat.biens[b].nom; dispo = self.d.get(n, 0.0)
        q = min(q, dispo)
        if not q > 0.0: return 0.0
        self.d[n] = dispo - q
        return q


class MondeExterieur:
    """Les prix mondiaux, en euros par unite, un par bien du catalogue ( identifiant = rang ).
      base   euros : le niveau de long terme ( le prix au port a l installation, a la parite de depart )
      x      logarithme de l ecart au niveau, marche aleatoire rappelee ( demi-vie DEMI_VIE_RAPPEL_J )
      chocs  [ jour, identifiants, logarithme du choc, demi-vie en jours ]
      prix   euros : le prix du jour ; historique : les 120 derniers jours"""
    __slots__ = ("base", "x", "famille", "sigma", "chocs", "prix", "historique", "saison0")

    def __init__(self):
        self.base = np.zeros(0); self.x = np.zeros(0); self.famille = np.zeros(0, np.int64); self.sigma = np.zeros(0)
        self.chocs = []; self.prix = np.zeros(0); self.historique = deque(maxlen=120); self.saison0 = 0.0


class Negociant:
    """Un importateur exportateur du port, attitre a un marche.
      caisse   drachmes ; stock : son entrepot ( Stock du socle ) ; lots : bien -> deque de [ cle de decision, quantite,
      cout rendu unitaire ] dans l ordre d arrivee ( la vente sort le plus ancien d abord )"""
    __slots__ = ("id", "marche_id", "caisse", "stock", "lots", "en_mer")

    def __init__(self, marche_id):
        self.id, self.marche_id = f"negoce@{marche_id}", marche_id
        self.caisse = 0.0
        self.stock = BI.Stock()
        self.lots = {}
        self.en_mer = {}            # bien -> quantite commandee pas encore arrivee


class Contrebandier:
    """Un reseau de passeurs par ile : caisse et stock de passage ( vide le soir ). Ses comptes sont la verite cachee
    que le domaine 21 cherche."""
    __slots__ = ("id", "ile", "caisse", "stock")

    def __init__(self, ile):
        self.id, self.ile, self.caisse, self.stock = f"contrebande@{ile}", ile, 0.0, BI.Stock()


class Douane:
    """Les declarations en douane : ( sens, motif, bien, quantite, valeur en drachmes, droit, declarant ), du jour ;
    les cumuls par ( sens, bien ) ; les alertes du rapprochement ( jour, nature, motif, bien, quantite ).
      vus      ( nature, bien ) -> quantite que les lignes du grand livre ont montree depuis l installation
      depart   ( nature, bien ) -> livre.flux a l installation : un flux ecrit sans ligne se lit dans l ecart"""
    __slots__ = ("jour", "cumul_q", "cumul_v", "droits", "alertes", "vus", "depart", "base", "ouverts_prec", "autres")

    def __init__(self):
        self.jour = []
        self.cumul_q, self.cumul_v = {}, {}
        self.droits = 0.0
        self.alertes = []
        self.vus, self.depart, self.base, self.ouverts_prec = {}, {}, {}, {}
        self.autres = {}            # motif d un autre domaine -> [ valeur declaree, paiement vu ] ( drachmes, cumul )


class GardeManger:
    """Le garde-manger d un menage du moteur vu comme un stock du socle en nourriture ( un seul bien )."""
    __slots__ = ("mg",)

    def __init__(self, mg): self.mg = mg

    def _ajouter(self, b, q): self.mg.garde_manger += q

    def _retirer(self, b, q):
        q = min(q, self.mg.garde_manger)
        if not q > 0.0: return 0.0
        self.mg.garde_manger -= q
        return q


class BalanceDesPaiements:
    """La balance du pays, en drachmes, au sens du MBP6 simplifie : credits ( entrees de devises ) et debits ( sorties )
    par ligne, du jour et cumules ; la variation des avoirs de reserve ; les erreurs et omissions, vraies ( toutes les
    lignes ) et publiees ( la contrebande en moins )."""
    __slots__ = ("credit", "debit", "reserves", "erreurs", "erreurs_publiees", "serie", "pire_erreur", "ext_prec",
                 "ouverts_prec", "base")

    def __init__(self, ext):
        self.credit = {l: 0.0 for l in LIGNES}; self.debit = {l: 0.0 for l in LIGNES}
        self.reserves = self.erreurs = self.erreurs_publiees = self.pire_erreur = 0.0
        self.serie = deque(maxlen=800)
        self.ext_prec = ext["entree"] - ext["sortie"]
        self.ouverts_prec = {}
        self.base = {}

    def soldes(self):
        s = {l: self.credit[l] - self.debit[l] for l in LIGNES}
        s["courant"] = s["biens"] + s["services"] + s["revenus_primaires"] + s["revenus_secondaires"]
        return s


class ContexteImport:
    __slots__ = ("traits", "cible", "neg", "bien")

    def __init__(self, traits, cible, neg, bien): self.traits, self.cible, self.neg, self.bien = traits, cible, neg, bien


class Exterieur:
    __slots__ = ("monde", "taux", "taux0", "reserves_euros", "reserves0", "ext_reserves", "derniere_devaluation",
                 "devaluations", "negociants", "par_marche", "contrebandiers", "douane", "bop", "decideur", "cle",
                 "suivi", "gains", "emigres", "n_emigres", "n_immigres", "attendu_emigration", "attendu_immigration",
                 "departs", "menages_immigres", "facteur_migration", "epargne_sortie", "epargne_entree", "vivants0", "naissances0",
                 "deces0", "imports_euros", "controle_douane", "contrebande", "chrono", "jour_install",
                 "import_jour_euros")

    def __init__(self):
        self.monde = MondeExterieur()
        self.taux = self.taux0 = EUROS_PAR_DRACHME      # euros par drachme
        self.reserves_euros = self.reserves0 = 0.0
        self.ext_reserves = 0.0                          # flux exterieur net deja converti en euros
        self.derniere_devaluation = -10 ** 6
        self.devaluations = []
        self.negociants = []; self.par_marche = {}; self.contrebandiers = {}
        self.douane = Douane(); self.bop = None
        self.decideur = None
        self.cle = 0
        self.suivi = {}             # cle -> [ marche, bien, jour, jours notes, lot, valeur de reference, demande ]
        self.gains = {}             # cle -> ce que CE lot a rapporte aujourd hui ( dans la note du soir )
        self.emigres = {}           # habitant -> ( menage d origine, jour du depart, adulte )
        self.n_emigres = self.n_immigres = 0
        self.attendu_emigration = self.attendu_immigration = 0.0
        self.departs = 0            # departs tires ( sans les accompagnants ) : ce que les taux predisent
        self.menages_immigres = 0
        self.facteur_migration = 1.0
        self.epargne_sortie = self.epargne_entree = 0.0
        self.vivants0 = self.naissances0 = self.deces0 = 0
        self.imports_euros = deque(maxlen=90)            # importations de biens par jour, euros
        self.import_jour_euros = 0.0
        self.controle_douane = CONTROLE_DOUANE
        self.contrebande = []       # ( jour, lieu, bien, quantite, valeur au port, saisi )
        self.chrono = {}
        self.jour_install = 0


# ================================================================== petits outils
def _ext(p): return p.domaine("exterieur")


def _chrono(e, nom, t0): e.chrono[nom] = e.chrono.get(nom, 0.0) + time.perf_counter() - t0


def _id(p, nom): return p.socle.catalogue.id(nom)


def _famille(p, b): return p.socle.catalogue[b].famille


def prix_mondial(p, bien):
    """Euros par unite, aujourd hui."""
    e = _ext(p); b = bien if isinstance(bien, int) else _id(p, bien)
    _etendre(p, e)
    return float(e.monde.prix[b])


def prix_port(p, bien):
    """Drachmes par unite FOB au port ( prix mondial a la parite du jour )."""
    return prix_mondial(p, bien) / _ext(p).taux


def fret_unitaire(p, bien):
    return prix_port(p, bien) * FRET.get(_famille(p, bien), 0.05)


def prix_import(p, bien):
    """Le cout rendu d une unite importee, en drachmes : FOB + fret + droit de douane ( sans TVA : autoliquidee ).
    C est la parite a l import que le prix interieur retrouve."""
    fob = prix_port(p, bien); fret = fret_unitaire(p, bien)
    nom = bien if isinstance(bien, str) else p.socle.catalogue[bien].nom
    droit = ET.taxes_import(p, nom, fob + fret)[0]
    return fob + fret + droit


def prix_export(p, bien):
    """Ce que l etranger paie une unite chargee au port ( FOB : prix mondial moins le fret jusqu a lui )."""
    nom = bien if isinstance(bien, str) else p.socle.catalogue[bien].nom
    if nom == "or": return prix_port(p, bien) * (1.0 - FRAIS_OR)
    return prix_port(p, bien) - fret_unitaire(p, bien)


def _demande(p, mid, b):
    em = p.domaine("economie").marches[mid]
    return max(EC.DEMANDE_MIN, em.demande_lisse.get(b, 0.0))


def _cible(b): return EC.COUVERTURE_CIBLE_J.get(b, 5.0)


# ================================================================== les prix mondiaux
def _etendre(p, e):
    """Les biens declares apres l installation entrent dans le processus, a leur prix declare."""
    cat = p.socle.catalogue; m = e.monde
    n0, n = len(m.base), len(cat)
    if n0 >= n: return
    fams = list(BI.FAMILLES)
    nb = np.array([cat[i].prix_monde * e.taux for i in range(n0, n)])
    m.base = np.concatenate([m.base, nb]); m.prix = np.concatenate([m.prix, nb]); m.x = np.concatenate([m.x, np.zeros(n - n0)])
    m.famille = np.concatenate([m.famille, np.array([fams.index(cat[i].famille) for i in range(n0, n)], np.int64)])
    m.sigma = np.concatenate([m.sigma, np.array([VOLATILITE_BIEN.get(cat[i].nom, VOLATILITE[cat[i].famille])
                                                 for i in range(n0, n)])])


def _saison(p, jour):
    """Le logarithme saisonnier des prix agricoles ce jour-la : un creux a la moisson."""
    doy = p.socle.calendrier.date(p.w.pas).timetuple().tm_yday + (jour - p.jour)
    return -SAISON_ALIMENT * math.cos(2.0 * math.pi * (doy - JOUR_MOISSON) / JOURS_AN)


def choc(p, facteur, famille=None, biens=None, demi_vie_j=DEMI_VIE_CHOC_J):
    """Un choc sur les prix mondiaux : `facteur` multiplie le prix d aujourd hui, puis s eteint ( demi-vie ). Une famille
    ( energie : un choc petrolier ) ou une liste de biens."""
    if not 0.05 <= facteur <= 20.0: raise ValueError(f"facteur de choc hors [0,05 ; 20] : {facteur!r}")
    e = _ext(p); _etendre(p, e); cat = p.socle.catalogue
    if famille is not None:
        if famille not in BI.FAMILLES: raise ValueError(f"famille inconnue {famille!r}")
        ids = tuple(b.id for b in cat if b.famille == famille and b.nom != "electricite")
    else:
        ids = tuple(_id(p, b) for b in biens)
    e.monde.chocs.append([p.jour, ids, math.log(facteur), float(demi_vie_j)])
    p.noter("choc_prix_mondial", famille=famille, biens=len(ids), facteur=round(facteur, 3))
    _calculer_prix(p, e)


def _calculer_prix(p, e):
    m = e.monde
    ch = np.zeros(len(m.base))
    garde = []
    for c in m.chocs:
        k = c[2] * 0.5 ** ((p.jour - c[0]) / c[3])
        if abs(k) < 1e-5: continue
        garde.append(c)
        ch[list(c[1])] += k
    m.chocs = garde
    s = np.where(m.famille == BI.FAMILLES.index("aliment"), _saison(p, p.jour) - m.saison0, 0.0)
    m.prix = m.base * np.exp(m.x + s + ch)
    cat = p.socle.catalogue
    for i in range(len(m.prix)):
        cat[i].prix_monde = float(min(BI.PRIX_MAX, max(1e-9, m.prix[i] / e.taux)))


def _prix_du_jour(p, e):
    """Un pas quotidien du processus des prix mondiaux, tire par vecteur."""
    _etendre(p, e); m = e.monde
    n = len(m.base)
    rng = p.du_jour("exterieur_prix")
    zf = rng.standard_normal(len(BI.FAMILLES)); zb = rng.standard_normal(n)
    ie, ia = BI.FAMILLES.index("energie"), BI.FAMILLES.index("aliment")
    zf[ia] = ENERGIE_DANS_ALIMENT * zf[ie] + math.sqrt(1.0 - ENERGIE_DANS_ALIMENT ** 2) * zf[ia]
    r = CORRELATION_FAMILLE
    m.x += -THETA * m.x + m.sigma / math.sqrt(JOURS_AN) * (math.sqrt(r) * zf[m.famille] + math.sqrt(1.0 - r) * zb)
    if p.du_jour("exterieur_choc").random() < PROBA_CHOC_PETROLE_AN / JOURS_AN:
        choc(p, FACTEUR_CHOC_PETROLE, famille="energie")
    _calculer_prix(p, e)
    m.historique.append(m.prix.copy())


# ================================================================== le change et les reserves
def _suivre_reserves(p, e):
    """Chaque flux exterieur du grand livre, converti au taux du jour : les reserves de la banque centrale, en euros.
    Appele avant tout changement de parite, avant tout controle des changes et a la cloture."""
    L = p.socle.livre
    net = L.ext["entree"] - L.ext["sortie"]
    e.reserves_euros += (net - e.ext_reserves) * e.taux
    e.ext_reserves = net


def couverture_reserves_mois(p):
    """Les reserves en mois d importations ( moyenne des jours connus ), ou None sans importations."""
    e = _ext(p)
    if not e.imports_euros: return None
    moy = sum(e.imports_euros) / len(e.imports_euros)
    return e.reserves_euros / (30.0 * moy) if moy > EPS else None


def devaluer(p, part):
    """La banque centrale abaisse la parite : une drachme vaut `part` de moins en euros ; toute importation coute
    1 / ( 1 - part ) fois plus de drachmes."""
    if not 0.0 < part < 0.9: raise ValueError(f"devaluation hors ]0 ; 0,9[ : {part!r}")
    e = _ext(p)
    _suivre_reserves(p, e)
    ancien = e.taux
    e.taux *= (1.0 - part)
    e.derniere_devaluation = p.jour
    e.devaluations.append((p.jour, ancien, e.taux))
    p.noter("devaluation", ancien=round(ancien, 6), nouveau=round(e.taux, 6), part=part)
    _calculer_prix(p, e)


def fixer_parite(p, taux):
    """Une parite choisie ( euros par drachme ) : domaine 24, ou une porte."""
    if not 1e-3 <= taux <= 1e3: raise ValueError(f"parite hors bornes : {taux!r}")
    e = _ext(p); _suivre_reserves(p, e); e.taux = float(taux); _calculer_prix(p, e)


def _politique_de_change(p, e):
    """La regle : sous trois mois d importations de reserves, une devaluation de 15 %, au plus une tous les six mois,
    apres deux mois d histoire."""
    if p.jour - e.jour_install < HISTOIRE_MIN_J or p.jour - e.derniere_devaluation < DELAI_DEVALUATION_J: return
    c = couverture_reserves_mois(p)
    if c is not None and c < COUVERTURE_MIN_MOIS: devaluer(p, DEVALUATION)


def _matin(p):
    """5 h 40 : les reserves, la politique de change, les prix mondiaux du jour ecrits au port."""
    t0 = time.perf_counter()
    e = _ext(p)
    _suivre_reserves(p, e)
    e.imports_euros.append(e.import_jour_euros); e.import_jour_euros = 0.0
    _politique_de_change(p, e)
    _prix_du_jour(p, e)
    _chrono(e, "prix", t0)


# ================================================================== la douane
def _declarer(p, e, sens, motif, bien, q, valeur, droit=0.0, declarant="exterieur"):
    e.douane.jour.append((sens, motif, bien, float(q), float(valeur), float(droit), declarant))
    k = (sens, bien)
    e.douane.cumul_q[k] = e.douane.cumul_q.get(k, 0.0) + q
    e.douane.cumul_v[k] = e.douane.cumul_v.get(k, 0.0) + valeur
    if sens == "import": e.import_jour_euros += valeur * e.taux


def _controle_devises(p, e, euros):
    """La banque centrale fournit-elle ces devises ? Rend la part fournie ( 0 a 1 )."""
    _suivre_reserves(p, e)
    if euros <= EPS: return 1.0
    dispo = e.reserves_euros - PLANCHER_RESERVES
    if dispo >= euros: return 1.0
    p.compter("controle_des_changes")
    return max(0.0, dispo / euros)


def importer_au_port(p, importateur, stock, bien, q, motif="import_biens", droits=True):
    """Une importation complete : devises, prix FOB a l etranger, fret aux armateurs etrangers, droit de douane a l Etat,
    le bien dans `stock` ( Stock du socle ou StockE1 ), la declaration. Ce que la caisse ne paie pas n est pas importe.
    Rend ( quantite importee, drachmes payees en tout )."""
    if motif not in MOTIFS_IMPORT_API: raise ValueError(f"motif d import inconnu {motif!r} : {MOTIFS_IMPORT_API}")
    if not 0.0 <= q < math.inf: raise ValueError(f"quantite invalide {q!r}")
    e = _ext(p); L = p.socle.livre; w = p.w
    b = bien if isinstance(bien, int) else _id(p, bien)
    nom = p.socle.catalogue[b].nom
    fob = prix_port(p, b); fret = fret_unitaire(p, b)
    taux_droit = ET.taxes_import(p, nom, 1.0)[0] if droits and importateur is not w.gouv else 0.0
    unitaire = (fob + fret) * (1.0 + taux_droit)
    q = min(q, max(0.0, importateur.caisse) / unitaire * (1.0 - 1e-12)) if unitaire > 0 else 0.0
    q *= _controle_devises(p, e, q * (fob + fret) * e.taux)
    if q <= EPS: return 0.0, 0.0
    paye = L.payer_l_exterieur(importateur, q * fob, motif)
    q = paye / fob
    f = L.payer_l_exterieur(importateur, q * fret, "fret_import")
    droit = 0.0
    if taux_droit > 0.0: droit = ET.percevoir(p, importateur, q * (fob + fret) * taux_droit, "droit_de_douane")[0]
    e.douane.droits += droit
    L.importer(stock, b, q, motif)
    _declarer(p, e, "import", motif, nom, q, paye, droit)
    return q, paye + f + droit


def declarer_import(p, importateur, valeur_fob, famille, motif="import_vehicules"):
    """Une importation qui n est pas un bien fongible ( un vehicule, une arme : un objet du Parc, domaines 14 et 25 ) :
    devises, prix FOB, fret, droit de la famille, declaration ( bien = famille ). L objet, lui, entre par le Parc du
    domaine qui l importe. Rend les drachmes payees en tout."""
    if motif not in MOTIFS_IMPORT_API: raise ValueError(f"motif d import inconnu {motif!r}")
    if famille not in BI.FAMILLES: raise ValueError(f"famille inconnue {famille!r}")
    e = _ext(p); L = p.socle.livre; w = p.w
    fret = valeur_fob * FRET.get(famille, 0.05)
    taux_droit = ET.DROITS_DOUANE.get(famille, 0.0) if importateur is not w.gouv else 0.0
    if importateur.caisse < (valeur_fob + fret) * (1.0 + taux_droit) - EPS: return 0.0
    if _controle_devises(p, e, (valeur_fob + fret) * e.taux) < 1.0: return 0.0
    paye = L.payer_l_exterieur(importateur, valeur_fob, motif)
    f = L.payer_l_exterieur(importateur, fret, "fret_import")
    droit = ET.percevoir(p, importateur, (valeur_fob + fret) * taux_droit, "droit_de_douane")[0] if taux_droit > 0 else 0.0
    e.douane.droits += droit
    _declarer(p, e, "import", motif, famille, 0.0, paye, droit)
    return paye + f + droit


def exporter_au_port(p, exportateur, stock, bien, q, motif="export_biens"):
    """Une exportation : le bien sort de `stock`, l etranger paie `exportateur` au prix FOB, la declaration. Rend
    ( quantite, drachmes recues )."""
    e = _ext(p); L = p.socle.livre
    b = bien if isinstance(bien, int) else _id(p, bien)
    nom = p.socle.catalogue[b].nom
    q = L.exporter(stock, b, q, motif)
    if q <= 0.0: return 0.0, 0.0
    recu = L.recevoir_de_l_exterieur(exportateur, q * prix_export(p, b), motif)
    _declarer(p, e, "export", motif, nom, q, recu)
    return q, recu


# ================================================================== le moteur repris
class RemplaceImporter:
    """Prend la place de Monde.importer ( action « importer » du gouvernement ) : l Etat importe au prix mondial du jour,
    par le grand livre ; le cout que le moteur a calcule a prix fixe ne sert plus. Pas de droit : l Etat ne se paie pas."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self, b, q, cout=None):
        p = self.pays; w = p.w
        q, paye = importer_au_port(p, w.gouv, StockE1(w.publics["reserve"], p.socle.catalogue), b, q, "import_etat")
        w.noter("import", bien=b, quantite=q, cout=round(paye))


class RemplaceExporterOr:
    """Prend la place de Monde.exporter_or : l or des reserves vendu au prix mondial du jour, par le grand livre."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self, q):
        p = self.pays; w = p.w
        q = min(float(q), w.publics["reserve"].get("or", 0.0))
        if q <= 0: return False, "pas d or en reserve"
        q, gain = exporter_au_port(p, w.gouv, StockE1(w.publics["reserve"], p.socle.catalogue), "or", q, "export_or_etat")
        w.noter("export_or", quantite=round(q, 2), gain=round(gain))
        return True, ""


# ================================================================== le negoce : exporter
def _exporter_du_marche(p, e, neg, m, b, q, motif="export_biens"):
    """Le negociant achete au marche `q` unites qu il charge aussitot : l etranger le paie FOB, il paie le marche FOB
    moins sa marge. Rend la quantite partie."""
    L = p.socle.livre; cat = p.socle.catalogue
    if q <= EPS: return 0.0
    q, recu = exporter_au_port(p, neg, StockE1(m.stocks, cat), b, q, motif)
    if q > 0.0:
        L.transferer(neg, m, recu * (1.0 - MARGE_NEGOCE), "achat_export")
        p.compter("export_negoce", recu)
    return q


def _port_horaire(p):
    """Chaque heure pleine moins 10 : l or des marches et la nourriture au-dela du seuil du moteur partent par le negoce,
    par le grand livre - monde.expedier ( lignes 516 et 522 ) n a plus rien a vendre a la main a l heure pleine. A 5 h 50,
    la population comptee comme l index de l aube la comptera."""
    t0 = time.perf_counter()
    e = _ext(p); w = p.w
    frais = abs(w.heure - (5 + 50 / 60)) < 1e-6
    if frais:
        pop = {}
        for mg in w.menages:
            if mg.domicile is None or mg.domicile.marche is None: continue
            k = mg.domicile.marche.id
            pop[k] = pop.get(k, 0) + sum(1 for x in mg.membres if x.vivant)
    else: pop = w._pop_marche
    ior, inour = _id(p, "or"), _id(p, "nourriture")
    for neg in e.negociants:
        m = w.marches[neg.marche_id]
        if m.stocks.get("or", 0.0) > 0.0: _exporter_du_marche(p, e, neg, m, ior, m.stocks["or"])
        besoin = 3 * C.NOURRITURE_PAR_JOUR * pop.get(neg.marche_id, 0)
        surplus = m.stocks["nourriture"] - besoin
        if surplus > MARGE_SURETE_MOTEUR: _exporter_du_marche(p, e, neg, m, inour, surplus)
    _chrono(e, "port", t0)


def _arbitrage_export(p):
    """12 h 50 : quand l etranger paie plus que le marche ne paie ses producteurs, le negoce exporte une part du stock
    du marche, jusqu a un jour de demande ( nourriture : trois jours ; biens proteges : toute leur cible ) : le
    marche passe sous sa cible et monte son prix ( domaine 3 ) jusqu a la parite a l export. C est par ce canal qu un
    choc sur les prix mondiaux atteint un bien que le pays produit lui-meme ( le raffineur grec vend a la parite )."""
    t0 = time.perf_counter()
    e = _ext(p); w = p.w
    for neg in e.negociants:
        m = w.marches[neg.marche_id]
        for nom in BIENS_IMPORT:
            b = _id(p, nom)
            achat = prix_export(p, b) * (1.0 - MARGE_NEGOCE)
            if achat <= m.prix[nom] * (1.0 - m.marge) * (1.0 + SEUIL_ARBITRAGE): continue
            dem = _demande(p, neg.marche_id, nom)
            if nom == "nourriture": garde = max(_cible(nom), COUVERTURE_EXPORT_NOURRITURE_J)
            elif nom in PROTEGES_EXPORT: garde = _cible(nom)
            else: garde = GARDE_EXPORT_J
            q = min(m.stocks[nom] - garde * dem, max(CAPACITE_EXPORT_J * dem, PART_STOCK_EXPORT * m.stocks[nom]))
            if q > 1.0: _exporter_du_marche(p, e, neg, m, b, q)
    _chrono(e, "port", t0)


# ================================================================== le negoce : importer ( le point de decision )
def _observer_import(ctx): return ctx.traits


def _regle_import(x, ctx):
    couv, neg_j, ratio, tres, essentiel = x[0] * 10.0, x[1] * 10.0, x[2] * 3.0, x[5], x[7]
    besoin = ctx.cible + DELAI_MER_J - couv - neg_j
    if besoin < 0.25 or tres < 0.02: return 0
    if ratio < 1.0 and not (essentiel >= 0.5 and couv < URGENCE_J): return 0
    return min(range(1, len(QUANTITES_J)), key=lambda k: (abs(QUANTITES_J[k] - besoin), k))


def _temoin_import(x, ctx, rng): return ACTIONS.index("un_jour")


POINT_IMPORT = D.PointDeDecision(
    "importer", "exterieur",
    traits=(("couverture_marche", "le stock de son marche en jours de demande lissee ( affiche par le marchand ), sur 10"),
            ("stock_negoce", "son entrepot et ses commandes en mer, en jours de demande, sur 10"),
            ("prix_sur_parite", "le prix d achat du marche sur le cout rendu a l import ( prix du port publie ), sur 3"),
            ("tendance_monde", "la variation du prix mondial publie sur 7 jours, de -50 % a +50 % ramenee a [0 ; 1]"),
            ("manque_hier", "la demande que son marche n a pas servie ( ruptures ), en jours de demande, bornee a 1"),
            ("tresorerie", "sa caisse sur la valeur de 3 jours de demande au cout rendu, bornee a 1"),
            ("reserves_change", "les reserves de change publiees par la banque centrale, en mois d importations, sur 12"),
            ("essentiel", "1 si le bien est nourriture ou remedes ( sa nature )")),
    actions=ACTIONS,
    observer=_observer_import, regle=_regle_import, temoin=_temoin_import,
    note="chaque jour, pour CE lot : marge realisee sur ses ventes a SON marche ( sur la valeur d un jour de demande ) + "
         "unites servies quand son marche avait moins d un jour de stock ( en jours de demande ) - pertes de stockage ; "
         "au dernier jour 10 % du cout des invendus ; attendre vaut zero ; moyenne sur 5 jours",
    horizon_j=HORIZON_IMPORT)


def _traits(p, e, neg, nom, b):
    w = p.w; m = w.marches[neg.marche_id]
    dem = _demande(p, neg.marche_id, nom)
    couv = max(0.0, m.stocks[nom]) / dem
    chez = (neg.stock[b] + neg.en_mer.get(b, 0.0)) / dem
    pi = prix_import(p, b)
    ratio = m.prix[nom] * (1.0 - m.marge) / (pi * (1.0 + MARGE_NEGOCE))
    h = e.monde.historique
    tend = (h[-1][b] / h[-8][b] - 1.0) if len(h) >= 8 else 0.0
    em = p.domaine("economie").marches[neg.marche_id]
    cr = couverture_reserves_mois(p)
    return (min(1.0, couv / 10.0), min(1.0, chez / 10.0), min(1.0, max(0.0, ratio / 3.0)),
            min(1.0, max(0.0, 0.5 + tend)), min(1.0, em.non_servi.get(nom, 0.0) / dem),
            min(1.0, max(0.0, neg.caisse) / max(EPS, 3.0 * dem * pi)),
            1.0 if cr is None else min(1.0, max(0.0, cr / 12.0)), 1.0 if nom in ESSENTIELS else 0.0)


def _commander(p):
    """8 h, 12 h, 16 h : chaque negociant decide, bien par bien, d importer ou d attendre."""
    t0 = time.perf_counter()
    e = _ext(p); dec = e.decideur
    for neg in e.negociants:
        for nom in BIENS_IMPORT:
            b = _id(p, nom)
            x = _traits(p, e, neg, nom, b)
            cle = e.cle; e.cle += 1
            a = dec.decider(cle, ContexteImport(x, _cible(nom), neg, nom))
            dem = _demande(p, neg.marche_id, nom)
            e.suivi[cle] = [neg.marche_id, nom, p.jour, 0, None, max(EPS, dem * prix_import(p, b)), dem]
            q = QUANTITES_J[a] * dem
            if q > EPS:
                neg.en_mer[b] = neg.en_mer.get(b, 0.0) + q
                p.poser(DELAI_MER_J * C.PAS_PAR_JOUR, "exterieur_arrivage", cle, (e.negociants.index(neg), b, q))
    _chrono(e, "decision", t0)


def _arrivage(p, cle, donnees):
    """Le lot commande il y a deux jours arrive : il est paye au prix du jour ( achat au comptant, contre documents )."""
    t0 = time.perf_counter()
    e = _ext(p); k, b, q = donnees
    neg = e.negociants[k]
    neg.en_mer[b] = max(0.0, neg.en_mer.get(b, 0.0) - q)
    q_in, cout = importer_au_port(p, neg, neg.stock, b, q, "import_biens")
    s = e.suivi.get(cle)
    if q_in <= EPS:
        p.compter("commande_annulee"); _chrono(e, "arrivage", t0); return
    lot = [cle, q_in, cout / q_in]
    neg.lots.setdefault(b, deque()).append(lot)
    if s is not None: s[4] = lot
    p.compter("import_negoce", cout)
    _chrono(e, "arrivage", t0)


def _vendre_aux_marches(p):
    """7 h 50, 11 h 50, 15 h 50, 18 h 50 : le marche rachete a son negociant ce qui manque a sa couverture visee, lot le
    plus ancien d abord, au cout rendu plus la marge du negoce - s il peut le revendre avec la sienne, ou si le bien est
    essentiel et qu il lui reste moins d un jour."""
    t0 = time.perf_counter()
    e = _ext(p); w = p.w; L = p.socle.livre; cat = p.socle.catalogue
    for neg in e.negociants:
        m = w.marches[neg.marche_id]
        for b, lots in neg.lots.items():
            if not lots: continue
            nom = cat[b].nom
            dem = _demande(p, neg.marche_id, nom)
            while lots:
                lot = lots[0]
                besoin = _cible(nom) * dem - m.stocks[nom]
                if besoin <= EPS: break
                cession = lot[2] * (1.0 + MARGE_NEGOCE)
                urgence = nom in ESSENTIELS and m.stocks[nom] < URGENCE_J * dem
                if m.prix[nom] * (1.0 - m.marge) < cession and not urgence: break
                q = min(lot[1], besoin, max(0.0, m.caisse) / cession)
                if q <= EPS: break
                en_manque = min(q, max(0.0, URGENCE_J * dem - m.stocks[nom]))
                paye = L.transferer(m, neg, q * cession, "vente_import")
                q = paye / cession
                q = L.deplacer(neg.stock, StockE1(m.stocks, cat), b, q, "vente_import")
                m.offre[nom] += q
                lot[1] -= q
                s = e.suivi.get(lot[0])
                if s is not None:
                    e.gains[lot[0]] = e.gains.get(lot[0], 0.0) + (cession - lot[2]) * q / s[5] + LAMBDA_MANQUE * min(q, en_manque) / s[6]
                if lot[1] <= 1e-9: lots.popleft()
                else: break
    _chrono(e, "ventes", t0)


def _soir_negoce(p):
    """23 h 40 : les pertes d entrepot, puis la note du jour de chaque decision en attente."""
    t0 = time.perf_counter()
    e = _ext(p); L = p.socle.livre; cat = p.socle.catalogue; dec = e.decideur
    for neg in e.negociants:
        for b, lots in neg.lots.items():
            perte = PERTE_STOCKAGE_J.get(cat[b].famille, 0.0)
            if perte <= 0.0 or not lots: continue
            for lot in lots:
                q = L.perimer(neg.stock, b, lot[1] * perte, "stockage_port")
                lot[1] -= q
                s = e.suivi.get(lot[0])
                if s is not None: e.gains[lot[0]] = e.gains.get(lot[0], 0.0) - lot[2] * q / s[5]
    for cle in [k for k, a in dec.attentes.items() if a.choix]:
        s = e.suivi.get(cle)
        if s is None: continue
        r = e.gains.pop(cle, 0.0)
        s[3] += 1
        if s[3] >= HORIZON_IMPORT and s[4] is not None and s[4][1] > 0.0:
            r -= PENALITE_INVENDU * s[4][2] * s[4][1] / s[5]
        dec.noter(cle, r, p.jour)
    for cle in [k for k, a in dec.attentes.items() if not a.choix]:
        del dec.attentes[cle]; e.suivi.pop(cle, None); e.gains.pop(cle, None)
    _chrono(e, "notes", t0)


# ================================================================== la contrebande ( donnees du domaine 21 )
def _contrebande(p):
    """21 h 30 : quand le gazole ou les outils se revendent 30 % au-dessus du prix mondial rendu, sans droit ni TVA, le
    reseau de l ile en passe un peu ; la douane en saisit une part ( au profit de l Etat )."""
    t0 = time.perf_counter()
    e = _ext(p); w = p.w; L = p.socle.livre; cat = p.socle.catalogue
    rng = p.du_jour("exterieur_contrebande")
    for neg in e.negociants:
        m = w.marches[neg.marche_id]
        cb = e.contrebandiers.get(m.lieu.ile)
        if cb is None: continue
        for nom in BIENS_CONTREBANDE:
            b = _id(p, nom)
            cout = prix_port(p, b) + fret_unitaire(p, b)
            vente = m.prix[nom] * (1.0 - m.marge) * (1.0 - DECOTE_CONTREBANDE)
            u = rng.random()
            if vente < MARGE_CONTREBANDE * cout: continue
            q = min(PART_CONTREBANDE * _demande(p, neg.marche_id, nom), max(0.0, cb.caisse) / cout,
                    max(0.0, m.caisse) / vente)
            if q <= EPS: continue
            paye = L.payer_l_exterieur(cb, q * cout, "contrebande")
            q = L.importer(cb.stock, b, paye / cout, "contrebande")
            saisi = u < e.controle_douane
            if saisi:
                L.deplacer(cb.stock, StockE1(w.publics["reserve"], cat), b, q, "saisie_douane")
                p.noter("saisie_douane", lieu=m.lieu.id, bien=nom, quantite=round(q, 2))
            else:
                x = L.transferer(m, cb, q * vente, "contrebande")
                L.deplacer(cb.stock, StockE1(m.stocks, cat), b, cb.stock[b], "contrebande")
                m.offre[nom] += q
                p.compter("contrebande_passee", q * cout)
            e.contrebande.append((p.jour, m.lieu.id, nom, q, q * cout, saisi))
    _chrono(e, "contrebande", t0)


# ================================================================== les migrations
_POPCOUNT = np.array([bin(i).count("1") for i in range(256)], np.int64)


def taux_emigration_jour(age, facteur=1.0):
    """Le hasard journalier de partir a l etranger, pour un tableau d ages entiers ( fonction pure )."""
    r = np.zeros(len(age))
    for a, v in EMIGRATION_AN: r = np.where(age >= a, v, r)
    return 1.0 - (1.0 - np.minimum(0.99, r * facteur)) ** (1.0 / JOURS_AN)


def _unite_de_depart(p, h):
    """Qui part avec h : son conjoint s il vit dans le menage, leurs enfants mineurs du menage."""
    col = p.colonnes["habitant"]; mg = h.menage
    gens = [h]
    c = int(col["conjoint"][h.id])
    if c >= 0:
        x = p.w.habitants[c]
        if x.vivant and x.menage is mg: gens.append(x)
    ids = {g.id for g in gens}
    for x in mg.membres:
        if x.vivant and x not in gens and POP.age_de(p, x) < POP.AGE_MAJEUR and (
                int(col["mere"][x.id]) in ids or int(col["pere"][x.id]) in ids):
            gens.append(x)
    return gens


def _peut_partir(p, gens):
    w = p.w
    for g in gens:
        if g.poste == "voyage" or g.id in w.sejours or g.incarne or g.eleve or g.role in EXCLUS_EMIGRATION: return False
    mg = gens[0].menage
    reste = [x for x in mg.membres if x.vivant and x not in gens]
    return not reste or any(POP.age_de(p, x) >= POP.AGE_MAJEUR for x in reste)


def emigrer(p, gens, motif_journal="emigration"):
    """Des habitants quittent le pays. Ils ne sont pas morts : pas de deces compte, pas d heritage, pas de declaration
    ( l etat civil grec ne raye pas un emigre : il reste inscrit, comme dans le vrai dimotologio ). Le moteur ne les voit
    plus ( vivant = faux, lieu = None ) ; deces_j recoit le jour de la SORTIE pour que le domaine 1 ne les reprenne pas
    comme morts de maladie ; ext_emigre_j dit qu ils sont partis. Leur part de la caisse part par payer_l_exterieur ; un
    menage vide part avec tout, son garde-manger compris ( effets personnels : MBP6, pas une transaction )."""
    e = _ext(p); w = p.w; L = p.socle.livre
    mg = gens[0].menage
    col = p.colonnes["habitant"]
    adultes = POP.adultes_vivants(p, mg)
    partants = [g for g in gens if POP.age_de(p, g) >= POP.AGE_MAJEUR]
    vide = all((not x.vivant) or x in gens for x in mg.membres)
    part = mg.caisse if vide else mg.caisse * len(partants) / max(1, len(adultes))
    x = L.payer_l_exterieur(mg, part, "transfert_migrant") if part > 0 else 0.0
    e.epargne_sortie += x
    if vide and mg.garde_manger > 0:
        L.exporter(GardeManger(mg), _id(p, "nourriture"), mg.garde_manger, "effets_migrants")
    for g in gens:
        c = int(col["conjoint"][g.id])
        if c >= 0 and w.habitants[c] not in gens: col["conjoint"][c] = -1; col["conjoint"][g.id] = -1
        g.vivant = False; g.lieu = None
        col["deces_j"][g.id] = p.jour
        col["ext_emigre_j"][g.id] = p.jour
        e.emigres[g.id] = (mg.id, p.jour, POP.age_de(p, g) >= POP.AGE_MAJEUR)
        e.n_emigres += 1
    if vide: p.col("menage", "dissous")[mg.id] = 1
    p.noter(motif_journal, menage=mg.id, personnes=len(gens), epargne=round(x, 2))


def _emigration(p, e):
    w = p.w; H = w.habitants; n = len(H)
    vivant = np.fromiter((h.vivant for h in H), bool, n)
    ids = np.nonzero(vivant)[0]
    if not len(ids): return
    age = POP._age_ans(p, ids)
    f7 = p.col("menage", "faim7")
    mids = np.fromiter((H[i].menage.id for i in ids.tolist()), np.int64, len(ids))
    faim = _POPCOUNT[f7[mids].astype(np.int64) & 0x7F] / 7.0
    hz = taux_emigration_jour(age, e.facteur_migration) * (1.0 + FACTEUR_FAIM_EMIGRATION * faim)
    hz = np.where(age >= EMIGRATION_AN[0][0], hz, 0.0)
    e.attendu_emigration += float(hz.sum())
    u = p.du_jour("exterieur_emigration").random(len(ids))
    for i in ids[u < hz].tolist():
        h = H[i]
        if not h.vivant: continue                        # parti avec son conjoint ou ses parents
        e.departs += 1
        gens = _unite_de_depart(p, h)
        if not _peut_partir(p, gens): p.compter("depart_empeche"); continue
        emigrer(p, gens)


def _immigrer(p, e, rng):
    """Un menage arrive de l etranger : de nouveaux habitants, inscrits, un metier libre, leur epargne par le grand
    livre. Ils s installent dans une capitale, au prorata de sa population."""
    w = p.w; d = p.domaine("population"); L = p.socle.livre
    capitales = sorted(w.marches)
    poids = np.array([max(1, w._pop_marche.get(k, 0)) for k in capitales], float)
    dom = w.marches[capitales[int(rng.choice(len(capitales), p=poids / poids.sum()))]].lieu
    taille = TAILLE_IMMIGRANTS[int(rng.choice(len(TAILLE_IMMIGRANTS), p=[t[1] for t in TAILLE_IMMIGRANTS]))][0]
    mg = POP.nouveau_menage(p, dom)
    col = p.colonnes["habitant"]
    gens = []
    for k in range(taille):
        adulte = k < min(2, taille)
        age = int(rng.integers(20, 46)) if adulte else int(rng.integers(0, 13))
        h = PO.Habitant(d.prochain_habitant, "enfant", "populaire", age)
        d.prochain_habitant += 1
        if h.id != len(w.habitants): raise RuntimeError("identifiants d habitants non denses")
        h.menage, h.domicile, h.lieu, h.poste = mg, dom, dom, "maison"
        h.decalage = float(rng.integers(-30, 31))
        w.habitants.append(h); mg.membres.append(h)
        p.colonnes["habitant"].assurer(len(w.habitants))
        if adulte and min(2, taille) == 2: col["sexe"][h.id] = POP.HOMME if k == 0 else POP.FEMME
        else: col["sexe"][h.id] = int(rng.integers(0, 2))
        col["naissance_j"][h.id] = p.jour - age * 365 - int(rng.integers(0, 365))
        h.age = (p.jour - int(col["naissance_j"][h.id])) / POP.JOURS_AN
        col["inscrit"][h.id] = 1
        col["ext_immigre_j"][h.id] = p.jour
        d.etat_civil.inscrits_vivants += 1
        if adulte: h.role = "ouvrier"; w.embaucher(h)
        else:
            h.horaire, h.travail = ("ecole", dom.marche) if h.age >= POP.AGE_ECOLE else (None, None)
        gens.append(h)
    adultes = [g for g in gens if POP.age_de(p, g) >= POP.AGE_MAJEUR]
    if len(adultes) == 2:
        a, b = adultes
        col["conjoint"][a.id] = b.id; col["conjoint"][b.id] = a.id
        col["union_j"][a.id] = col["union_j"][b.id] = p.jour
    for g in gens:
        if g in adultes: continue
        for a in adultes:
            k = "mere" if col["sexe"][a.id] == POP.FEMME else "pere"
            col[k][g.id] = a.id; d.enfants_de.setdefault(a.id, []).append(g.id)
    x = L.recevoir_de_l_exterieur(mg, EPARGNE_IMMIGRANT_EUROS * len(adultes) / e.taux, "transfert_migrant")
    e.epargne_entree += x
    e.n_immigres += len(gens); e.menages_immigres += 1
    p.noter("immigration", menage=mg.id, personnes=len(gens), lieu=dom.id, epargne=round(x, 2))


def _migrations(p):
    """21 h 10, apres le repas : les departs du jour, les arrivees, les envois de fonds des emigres."""
    t0 = time.perf_counter()
    e = _ext(p); w = p.w; L = p.socle.livre
    _emigration(p, e)
    vivants = sum(1 for h in w.habitants if h.vivant)
    lam = IMMIGRATION_AN * vivants / JOURS_AN * e.facteur_migration
    e.attendu_immigration += lam
    rng = p.du_jour("exterieur_immigration")
    for _ in range(int(rng.poisson(lam))): _immigrer(p, e, rng)
    dis = p.col("menage", "dissous")
    for hid, (mid, j, adulte) in e.emigres.items():
        if adulte and p.jour > j and (p.jour - j) % 30 == 0 and not dis[mid]:
            x = L.recevoir_de_l_exterieur(w.menages[mid], REMISE_EUROS_MOIS / e.taux, "envoi_de_fonds")
            p.compter("envoi_de_fonds", x)
    _chrono(e, "migrations", t0)


# ================================================================== l aide
def _aide(p):
    """9 h, tous les 30 jours : les fonds structurels de l Union au Tresor ( transfert en capital )."""
    e = _ext(p); w = p.w
    if (p.jour - e.jour_install) % 30 or p.jour == e.jour_install: return
    vivants = sum(1 for h in w.habitants if h.vivant)
    x = p.socle.livre.recevoir_de_l_exterieur(w.gouv, AIDE_UE_EUROS_HAB_AN * vivants / 12.0 / e.taux, "aide_ue")
    p.compter("aide_ue", x)


# ================================================================== la balance des paiements et la douane ( le soir )
def _lignes_ouvertes(p):
    """Les lignes exterieures du jour pas encore closes : ecrites apres la cloture du grand livre, pendant les clotures
    des domaines ( elles entrent dans les comptes de demain, et deja dans le compteur exterieur )."""
    out = {}
    for (m, pa, re), (s, n) in p.socle.livre.jour_argent.items():
        if pa == "Exterieur" or re == "Exterieur": out[(m, pa, re)] = s
    return out


def _cloture(p, comptes):
    t0 = time.perf_counter()
    e = _ext(p); L = p.socle.livre; bop = e.bop
    _suivre_reserves(p, e)
    lignes = dict(bop.base); bop.base = {}
    lignes = {k: -v for k, v in lignes.items()}
    for m, pa, re, s, _ in comptes["argent"]:
        if pa == "Exterieur" or re == "Exterieur": lignes[(m, pa, re)] = lignes.get((m, pa, re), 0.0) + s
    ouverts = _lignes_ouvertes(p)
    for k, s in ouverts.items(): lignes[k] = lignes.get(k, 0.0) + s
    for k, s in bop.ouverts_prec.items(): lignes[k] = lignes.get(k, 0.0) - s
    bop.ouverts_prec = ouverts
    cr = {l: [] for l in LIGNES}; db = {l: [] for l in LIGNES}
    par_motif = {}
    for (m, pa, re), s in lignes.items():
        if abs(s) <= 0.0: continue
        sg = 1.0 if pa == "Exterieur" else -1.0
        par_motif[m] = par_motif.get(m, 0.0) + sg * s
        if m in MOTIFS_DECLARES: continue
        if m in MOTIFS: l = MOTIFS[m][1] or "non_classe"
        else:
            mo = L.motifs.get(m)
            l = NATURE_LIGNE.get(mo.nature, "non_classe") if mo is not None else "non_classe"
        (cr if sg > 0 else db)[l].append(s)
    for sens, motif, bien, q, v, droit, qui in e.douane.jour:
        if motif in MOTIFS_DECLARES: (cr if sens == "export" else db)["biens"].append(v)
    jc = {l: math.fsum(cr[l]) for l in LIGNES}; jd = {l: math.fsum(db[l]) for l in LIGNES}
    net = L.ext["entree"] - L.ext["sortie"]
    d_res = net - bop.ext_prec
    bop.ext_prec = net
    somme = math.fsum([jc[l] for l in LIGNES] + [-jd[l] for l in LIGNES])
    eo = d_res - somme
    eo_pub = eo + jc["contrebande"] - jd["contrebande"]
    for l in LIGNES: bop.credit[l] += jc[l]; bop.debit[l] += jd[l]
    bop.reserves += d_res; bop.erreurs += eo; bop.erreurs_publiees += eo_pub
    bop.pire_erreur = max(bop.pire_erreur, abs(eo))
    bop.serie.append((p.jour, {l: jc[l] - jd[l] for l in LIGNES}, d_res, eo, eo_pub))
    _rapprochement_douanier(p, e, comptes, par_motif)
    e.douane.jour = []
    _chrono(e, "balance", t0)


def _lignes_biens(p):
    cat = p.socle.catalogue
    return {(n, m, cat[b].nom): q for (n, m, b), q in p.socle.livre.jour_biens.items() if n in ("importe", "exporte")}


def _rapprochement_douanier(p, e, comptes, par_motif):
    """Les biens que le grand livre a vus franchir la frontiere aujourd hui, motif par motif, contre les declarations
    ( motifs du domaine ) ou contre un paiement sous le meme motif ( autres domaines : declares ici, a la valeur payee ) ;
    puis livre.flux contre toutes les lignes vues depuis l installation : un flux ecrit a la main s y lit."""
    L = p.socle.livre; dz = e.douane
    vus = {k: -q for k, q in dz.base.items()}; dz.base = {}
    for n, m, b, q in comptes["biens"]:
        if n in ("importe", "exporte"): vus[(n, m, b)] = vus.get((n, m, b), 0.0) + q
    ouverts = _lignes_biens(p)
    for k, q in ouverts.items(): vus[k] = vus.get(k, 0.0) + q
    for k, q in dz.ouverts_prec.items(): vus[k] = vus.get(k, 0.0) - q
    dz.ouverts_prec = ouverts
    declares = {}
    for sens, motif, bien, q, v, droit, qui in dz.jour:
        k = ("importe" if sens == "import" else "exporte", motif, bien)
        declares[k] = declares.get(k, 0.0) + q
    autres = {}
    for k in sorted(vus):
        n, m, b = k; q = vus[k]
        if abs(q) <= 1e-12: continue
        dz.vus[(n, b)] = dz.vus.get((n, b), 0.0) + q
        if m in MOTIFS_DECLARES:
            ecart = q - declares.get(k, 0.0)
            if abs(ecart) > 1e-9 * max(1.0, abs(q)): dz.alertes.append((p.jour, "non_declare", m, b, ecart))
        elif m not in SANS_PAIEMENT_ADMIS: autres.setdefault((n, m), []).append((b, q))
    # les flux d un autre domaine ( energie ) : declares ici, le paiement du motif reparti entre ses biens au prix du port
    for (n, m), lst in sorted(autres.items()):
        v = par_motif.get(m, 0.0)
        if (n == "importe" and v >= -EPS) or (n == "exporte" and v <= EPS):
            for b, q in lst: dz.alertes.append((p.jour, "sans_paiement", m, b, q))
            continue
        poids = [q * prix_port(p, b) for b, q in lst]; tot = math.fsum(poids)
        for (b, q), x in zip(lst, poids):
            _declarer(p, e, "import" if n == "importe" else "export", m, b, q, abs(v) * x / tot, 0.0, "autre_domaine")
        a = dz.autres.setdefault(m, [0.0, 0.0]); a[0] += math.fsum(abs(v) * x / tot for x in poids); a[1] += abs(v)
    for k, q in declares.items():
        if q > 1e-9 and abs(vus.get(k, 0.0)) <= 1e-12: dz.alertes.append((p.jour, "declare_sans_bien", k[1], k[2], q))
    for nat in ("importe", "exporte"):
        for nom, v in L.flux[nat].items():
            ecart = v - dz.depart.get((nat, nom), 0.0) - dz.vus.get((nat, nom), 0.0)
            if abs(ecart) > 1e-6 * max(1.0, abs(v)):
                dz.alertes.append((p.jour, "hors_livre", nat, nom, ecart))
                dz.vus[(nat, nom)] = dz.vus.get((nat, nom), 0.0) + ecart      # signale une fois


# ================================================================== installation
def _membres_negociants(w): return w.pays.domaines["exterieur"].negociants
def _membres_contrebandiers(w): return list(w.pays.domaines["exterieur"].contrebandiers.values())


def installer(p):
    w = p.w; L = p.socle.livre
    for m, (nature, _) in MOTIFS.items(): L.declarer_motif(m, nature, "exterieur")
    J = p.socle.journal
    for t, champs in (("emigration", ("menage", "personnes", "epargne")),
                      ("immigration", ("menage", "personnes", "lieu", "epargne")),
                      ("devaluation", ("ancien", "nouveau", "part")), ("choc_prix_mondial", ("famille", "biens", "facteur")),
                      ("saisie_douane", ("lieu", "bien", "quantite"))):
        J.declarer(t, "exterieur", "individuel", champs)
    for t in ("import_negoce", "export_negoce", "commande_annulee", "controle_des_changes", "contrebande_passee",
              "envoi_de_fonds", "aide_ue", "depart_empeche"):
        J.declarer(t, "exterieur", "compte")
    ch = p.colonnes["habitant"]
    ch.ajouter("ext_emigre_j", np.int32, -1); ch.ajouter("ext_immigre_j", np.int32, -1)
    ch.assurer(len(w.habitants))
    e = Exterieur()
    p.domaines["exterieur"] = e
    e.jour_install = p.jour
    # la balance part d ici : les lignes exterieures deja ecrites aujourd hui ( epargne initiale du domaine 3 ) n en sont pas
    e.bop = BalanceDesPaiements(L.ext)
    e.bop.base = _lignes_ouvertes(p)
    e.douane.base = _lignes_biens(p)
    for nat in ("importe", "exporte"):
        for nom, v in L.flux[nat].items(): e.douane.depart[(nat, nom)] = v
    e.ext_reserves = L.ext["entree"] - L.ext["sortie"]
    # les prix mondiaux : le prix au port d aujourd hui, a la parite de depart
    _etendre(p, e)
    e.monde.saison0 = _saison(p, p.jour)
    e.monde.historique.append(e.monde.prix.copy())
    vivants = sum(1 for h in w.habitants if h.vivant)
    e.reserves_euros = e.reserves0 = RESERVES_EUROS_HAB * vivants
    e.vivants0 = vivants
    dp = p.domaine("population"); e.naissances0, e.deces0 = dp.naissances, dp.deces
    # les negociants : un par marche, capital apporte de l etranger ( investissement direct ), un compte en banque
    for mid in sorted(w.marches):
        neg = Negociant(mid)
        e.negociants.append(neg); e.par_marche[mid] = neg
    for ile in w.carte.iles: e.contrebandiers[ile] = Contrebandier(ile)
    p.socle.registre.inscrire("negociants", "entreprises", _membres_negociants, "caisse", "stock", "Negociant")
    p.socle.registre.inscrire("contrebandiers", "menages", _membres_contrebandiers, "caisse", "stock", "Contrebandier")
    for neg in e.negociants:
        L.recevoir_de_l_exterieur(neg, CAPITAL_NEGOCE_HAB * max(1, w._pop_marche.get(neg.marche_id, 0)), "investissement_direct")
        BQ.ouvrir_compte(p, neg)
    for cb in e.contrebandiers.values(): L.recevoir_de_l_exterieur(cb, CAPITAL_CONTREBANDE, "contrebande")
    e.decideur = p.decideur(POINT_IMPORT)
    w.importer = RemplaceImporter(p)
    w.exporter_or = RemplaceExporterOr(p)
    p.echeance("exterieur_arrivage", _arrivage)
    p.routine(5 + 40 / 60, 5, "exterieur", _matin)
    for h in range(24): p.routine(h + 50 / 60, 99, "exterieur", _port_horaire)   # le dernier : apres toute vente au marche
    for h in HEURES_VENTE: p.routine(h, 45, "exterieur", _vendre_aux_marches)
    for h in HEURES_DECISION: p.routine(h, 40, "exterieur", _commander)
    p.routine(12 + 50 / 60, 46, "exterieur", _arbitrage_export)
    p.routine(9, 40, "exterieur", _aide)
    p.routine(21 + 10 / 60, 20, "exterieur", _migrations)
    p.routine(21.5, 20, "exterieur", _contrebande)
    p.routine(23 + 40 / 60, 50, "exterieur", _soir_negoce)
    p.cloture("exterieur", _cloture)
    _port_horaire(p)       # ce que les marches ont deja en trop part avant la premiere heure pleine
    return e


# ================================================================== API pour les autres domaines
def balance_des_paiements(p, publiee=False):
    """La balance cumulee depuis l installation : { ligne : ( credit, debit, solde ) }, soldes courant, reserves,
    erreurs et omissions. `publiee` : sans la contrebande ( ce que la douane voit ), comme une balance publiee."""
    b = _ext(p).bop
    out = {l: (b.credit[l], b.debit[l], b.credit[l] - b.debit[l]) for l in LIGNES
           if not (publiee and l == "contrebande")}
    s = b.soldes()
    out["solde_courant"] = s["courant"]
    out["variation_reserves"] = b.reserves
    out["erreurs_omissions"] = b.erreurs_publiees if publiee else b.erreurs
    return out


def reserves_de_change(p):
    """( euros, mois d importations ou None )."""
    e = _ext(p); _suivre_reserves(p, e)
    return e.reserves_euros, couverture_reserves_mois(p)


def taux_de_change(p):
    """Euros par drachme."""
    return _ext(p).taux


def payer_reassurance(p, assureur, prime):
    """Domaine 20 : la prime cedee au reassureur etranger ( services d assurance )."""
    e = _ext(p)
    if _controle_devises(p, e, prime * e.taux) < 1.0: return 0.0
    return p.socle.livre.payer_l_exterieur(assureur, prime, "prime_reassurance")


def recevoir_reassurance(p, assureur, indemnite):
    """Domaine 20 : l indemnite du reassureur etranger apres un sinistre ( revenus secondaires )."""
    return p.socle.livre.recevoir_de_l_exterieur(assureur, indemnite, "indemnite_reassurance")


def fixer_controle_douane(p, proba):
    """Domaine 21 : la probabilite qu un passage de contrebande soit saisi."""
    if not 0.0 <= proba <= 1.0: raise ValueError(f"probabilite hors [0 ; 1] : {proba!r}")
    _ext(p).controle_douane = float(proba)


def contrebande(p):
    """Domaine 21 : les passages ( jour, lieu, bien, quantite, valeur au port, saisi ) - la verite ; la douane ne voit
    que les saisies."""
    return list(_ext(p).contrebande)


def alertes_douane(p): return list(_ext(p).douane.alertes)


def emigres(p):
    """{ habitant : ( menage d origine, jour du depart, adulte ) }."""
    return dict(_ext(p).emigres)


def bilan_population(p):
    """( vivants, attendus ) : vivants du depart + naissances - deces + immigres - emigres."""
    e = _ext(p); d = p.domaine("population")
    viv = sum(1 for h in p.w.habitants if h.vivant)
    return viv, e.vivants0 + (d.naissances - e.naissances0) - (d.deces - e.deces0) + e.n_immigres - e.n_emigres
