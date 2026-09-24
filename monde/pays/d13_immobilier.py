"""DOMAINE 13 - IMMOBILIER ET CONSTRUCTION : TERRAINS, BATIMENTS, LOYERS, VENTES, CHANTIERS, MATERIAUX, PERMIS.

FICHE
1. Classes. Les tables : Lieux ( prix et loyers au m2, valeur de zone, par lieu de la carte ), Cadastre ( les parcelles :
   lieu, zonage constructible ou agricole, surface, coefficient d occupation, surface batie, proprietaire ),
   TableBatiments ( les donnees propres a chaque batiment individuel, indexees par un rang dense : numero d objet du
   Parc, modele, lieu, parcelle, surface, annee, etat de dommage, occupant, bail, offre, chantier ). Les objets :
   Bail ( loyer, duree, depot de garantie, impayes ), Chantier ( permis, devis, besoins en materiaux, heures, stock du
   socle ), EntrepriseBTP ( une famille d argent nouvelle : caisse, stock des restes de chantier ), ContexteLoyer,
   Immobilier ( l etat du domaine ). Colonnes par menage : im_logement ( rang du batiment habite, -1 ), im_statut
   ( 0 sans, 1 proprietaire occupant, 2 locataire, 3 abri d urgence ), im_chef ( l adulte qui le represente :
   succession ), im_possede ( batiments possedes ). Tables eparses : chercheurs de logement, baux, litiges, chantiers.
   REPRESENTATION : un logement habite est un INDIVIDU du Parc ( modele appartement ou maison ) : son menage, son bail,
   sa surface, ses degats changent seuls, et il y en a un par menage - la memoire suit donc les menages ( ~ 200 octets
   par logement en Python, ~ 60 en Rust : 4 Go puis 1,2 Go pour 20 millions de logements ). Les COHORTES servent la ou
   l individu n est pas necessaire : les commerces d un marche ( un nombre et une usure : aucun bail, aucun occupant
   suivi ) et la reserve d abris d urgence de l Etat ; un commerce touche par un seisme, un abri donne a un menage, en
   sont tires ( Parc.materialiser ) ; un abri rendu y est refondu. Batiments publics ( ecoles, hopitaux, casernes,
   bureaux ) et ateliers des entreprises : individus ( quelques milliers a 50 millions ; leur surface fait les lits et
   les places ).
2. Invariants et ce que le domaine detient. OBJETS : chaque batiment de mes modeles nait par une source declaree
   ( initial au recensement, fabrique a la fin d un chantier, importe pour un abri achete a l etranger ) et ne sort que
   par un puits ( detruit : seisme, incendie ) ; l audit ( `audit_batiments` ) confronte les comptes du Parc aux
   naissances que le domaine a faites et les individus du Parc a sa table : un batiment cree hors chantier ou hors
   recensement est vu. LOGEMENT : chaque menage habite a un logement ( au besoin un abri d urgence de l Etat ) ; un
   logement n a qu un menage occupant et pas plus de personnes que sa capacite. ARGENT : tout par le grand livre ; le
   domaine DETIENT les caisses et les stocks des entreprises de BTP ( famille `entreprises_btp` ) et les stocks des
   chantiers ( famille `chantiers` ). LOYERS au centime : pour chaque bail, loyers echus = payes + impayes ( creances du
   socle, motif loyer ). BIENS : un chantier recoit ses materiaux par `industrie.livrer` ( deplacement ) et les consomme
   ( puits consomme, motif construction ) : livre = consomme + reste, le reste passe au stock de l entreprise de BTP.
3. Decision `fixer_loyer` ( chaque logement vide offert a la location, a sa mise sur le marche puis tous les 14 jours
   tant qu il reste vide ; 9 h ) : baisse forte, baisse, marche, hausse, hausse forte ( 0,80 a 1,25 fois le loyer de
   reference ). Traits : jours de vacance, tension du lieu ( candidats sur offres ), loyer de reference sur le revenu
   median des candidats, surface, age, degats, dernier loyer demande, part du parc offerte. Note ( horizon 30 jours :
   le premier loyer se paie a la signature, puis chaque mois ; une vacance grecque dure quelques semaines ) : chaque jour,
   pour CE logement, le loyer percu sans impaye sur le loyer de reference, plus 1 si un menage y vit, moins 1 si ce
   menage n a pas mange ce soir : ni le seul profit ( la vacance et le menage loge comptent ), ni une moyenne. Regle :
   hausse si le lieu a plus de 1,5 candidat par offre et le logement moins d un mois de vide, baisse apres 45 jours ou
   si le loyer depasse 40 % du revenu median des candidats, baisse forte apres 90 jours. Temoin : le loyer du marche.
   Sans decision ( regles ) : le candidat choisit le meilleur rapport surface utile sur loyer sous 40 % de son revenu ;
   le bailleur l accepte s il a moins de deux incidents bancaires et de quoi payer le depot.
4. Evenements. Individuels : expulsion, chantier_ouvert, chantier_termine, seisme_dommages, abri_importe. Comptes :
   bail_signe, bail_renouvele, depart_fin_bail, loyer_paye, loyer_impaye, vente_logement, enfia_percue,
   enfia_reportee, relogement_urgence, heritage_logement, candidat_refuse, permis_depose, emmenagement_proprietaire.
5. Liens. Territoire ( 8 ) : lieux, parcelles agricoles ( zonage agricole, proprietaire : la ferme ), seismes ( MMI par
   lieu ). Etat ( 6 ) : ENFIA ( `enfia`, `percevoir_enfia` par tranches mensuelles, exoneree pour un batiment
   inhabitable ), droits de permis ( `droits_permis`, `percevoir` ), `DELAI_PERMIS_J` ; droits de mutation ( 3,09 %,
   motif du domaine : `percevoir` ne les accepte pas ). Banques ( 2 ) : credit immobilier ( `demander_credit( type_ =
   "immo" )` ) pour acheter ou reconstruire, `ouvrir_compte` des entreprises de BTP. Industrie ( 10 ) : ciment, acier,
   sable, calcaire, verre, gypse par `commander` et `livrer`. Travail ( 4, s il est installe ) : `declarer_employeur`,
   `ouvrir_postes`, `rompre_contrat` ; le domaine credite `Habitant.heures_jour` des heures pointees sur le chantier,
   que la paie du domaine 4 fait payer par l entreprise de BTP ; sans lui, les chomeurs du registre du domaine 3 sont
   engages et payes directement. Population ( 1 ) : menages dissous, nouveaux menages, `enfants_de` ( succession ).
   Paie et recoit : loyers et depots ( menage -> bailleur ), ventes ( acheteur -> vendeur ), droits de mutation
   ( -> Etat ), frais de transaction ( -> marche ), travaux ( maitre d ouvrage -> BTP ), second oeuvre ( BTP ->
   exterieur ), aide a la reconstruction ( Etat -> sinistre ), abris importes ( Etat -> exterieur ), dividendes du BTP.
   Ne remplace aucune methode du moteur. API en fin de fichier pour les domaines 3, 12, 17, 18, 19, 20, 21, 25.
6. Portes : tests_d13_immobilier.py.
7. Arma. Classnames du jeu de base, d Apex et de Malden : appartement Land_i_House_Big_02_V1_F, maison
   Land_i_House_Small_01_V1_F, abri Land_Cargo_House_V1_F, commerce Land_i_Shop_01_V1_F, atelier Land_i_Shed_Ind_F,
   bureau Land_Offices_01_V1_F, ecole Land_School_01_F, hopital Land_Hospital_main_F, caserne Land_i_Barracks_V1_F ;
   chantier en cours : Land_Unfinished_Building_01_F. arma_preuve = None partout : rien n a ete vu vivre en jeu.
8. Cout. Par jour : trois lectures vectorisees des menages ( vivants par menage, lieu du domicile, statut ), le marche
   locatif sur les seuls chercheurs et logements offerts ( par lieu ), l ENFIA d un trentieme du parc, les chantiers en
   cours ; un loyer par bail et par mois ( echeancier ), une fin de bail par bail et par trois ans. Le seisme : une
   passe vectorisee sur les batiments des lieux touches. Mesure : tests_d13_immobilier.test_cout."""
import importlib, math
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D, objets as O, biens as BI
from . import pays as P, d01_population as POP, d02_banques as BQ, d06_etat as DE, d08_territoire as TER
from . import d10_industrie as IND

JOURS_AN = 365.0
MOIS_J = 30
EPS = 1e-9
TOL = 1e-6                        # drachmes : en dessous, un reste est de l arrondi
EUROS = P.EUROS_PAR_DRACHME
ANNEE_DEPART = C.DATE_DEPART[0]

# ================================================================== les prix du sol et des loyers ( Grece )
# Prix demandes au m2 ( euros, 2024 ) : Athenes ~ 2 400, autres villes ~ 1 700, villages ~ 1 000 ; loyers demandes au m2
# et par mois : Athenes ~ 11, villes ~ 8, villages ~ 5,5 ( Spitogatos et Banque de Grece, indices 2024 : ordres de
# grandeur a verifier ). Rendement locatif brut 5,5 a 6,6 % ( Global Property Guide, Grece 2024 : 5 a 7 % ). Les lieux
# qui ne sont pas habites ( sites, bases ) prennent un prix de terrain industriel ( a calibrer ).
HABITABLES = ("capitale", "ville", "village")
PRIX_M2_EUROS = {"capitale": 2400.0, "ville": 1700.0, "village": 1000.0, "site": 700.0}
LOYER_M2_EUROS = {"capitale": 11.0, "ville": 8.0, "village": 5.5, "site": 4.0}
DISPERSION_LIEU = 0.15            # +/- 15 % d un lieu a l autre du meme type ( a calibrer )
PART_VALEUR_ZONE = 0.70           # valeur de zone ( objective ) sur prix de marche : les valeurs de 2022 restent sous le marche ( a calibrer )
COUT_CONSTRUCTION_M2_EUROS = 1100.0   # batiment residentiel neuf hors terrain et hors TVA : devis grecs 2024 de 1 000 a 1 300 ( a calibrer )
FACTEUR_COUT = {"hopital": 1.8, "ecole": 1.2}   # un hopital coute ~ deux fois un logement au m2 ( a calibrer )
CROISSANCE_LOYERS_AN = 0.06       # loyers grecs 2019-2024 : + 6 a 9 % par an ; un bail ancien est sous le marche
PRIME_NEUF, DECOTE_AGE_AN, PLANCHER_AGE = 0.10, 0.006, 0.70     # prix selon l age ( a calibrer )

# ================================================================== le parc de logements
PART_PROPRIETAIRES = 0.735        # Eurostat ilc_lvho02, Grece 2023 : 73,5 % des personnes vivent chez leur menage proprietaire ( a verifier )
BANDE_PROPRIETAIRES = (0.70, 0.78)
P_MAISON = {"capitale": 0.25, "ville": 0.45, "village": 0.85, "site": 0.5}   # la polykatoikia domine en ville ( a calibrer )
SURFACE = {"appartement": (78.0, 0.30), "maison": (105.0, 0.35)}   # moyenne ( m2 ), ecart-type du log ; ELSTAT 2011 : ~ 80 m2 en moyenne
SURFACE_BORNES = (25.0, 300.0)
# Periodes de construction du parc grec ( ELSTAT, recensement des batiments 2011, ordres de grandeur prolonges a 2034 ) :
PERIODES = ((1900, 1945, 0.08), (1946, 1959, 0.12), (1960, 1984, 0.37), (1985, 1999, 0.25), (2000, 2011, 0.13),
            (2012, ANNEE_DEPART - 1, 0.05))
TAUX_VACANTS = 0.08               # logements vides offerts, en part des menages ( le reste du parc vide grec, 30 %, est hors marche )
POIDS_BAILLEUR = {"aisee": 6.0, "moyenne": 2.0, "populaire": 0.5}   # qui possede les logements loues ( a calibrer )
TAILLE_IMMEUBLE = 6               # appartements par parcelle d immeuble ( polykatoikia de 4 a 12 logements, a calibrer )
COS = {"capitale": 2.4, "ville": 1.6, "village": 0.8, "site": 0.8}   # coefficient d occupation du sol ( SD grec, a calibrer )
PARCELLE_MIN_M2 = {"capitale": 150.0, "ville": 250.0, "village": 500.0, "site": 1000.0}
PARCELLES_LIBRES = 0.05           # terrains a batir libres, en part des logements du lieu ( a calibrer )
PART_TERRAIN = 0.25               # part du terrain dans le prix d un logement neuf ( a calibrer )
VIE_ANS = 50                      # duree d utilisation de projet d un batiment courant ( EN 1990 : 50 ans )

# ================================================================== le marche locatif
DUREE_BAIL_J = 3 * 365            # duree minimale d un bail d habitation grec : 3 ans ( a verifier )
DEPOT_MOIS = 2                    # depot de garantie : 1 a 2 mois en usage grec ( a calibrer )
EFFORT_MAX = 0.40                 # seuil de surcharge du cout du logement ( Eurostat ) : le candidat ne loue pas au-dela
EFFORT_RECENSEMENT = 0.35
RAYON_RECHERCHE_KM = 25.0        # un menage cherche dans sa zone, sans changer d emploi ( a calibrer )
INCIDENTS_MAX = 2                 # le bailleur refuse un candidat qui a deja deux incidents bancaires ( fichier Tiresias )
P_DEPART_FIN_BAIL = 0.35          # part des locataires qui partent a la fin du bail ( a calibrer )
RECHERCHE_MAX_J = 60              # un menage loge qui cherche mieux renonce apres deux mois
REVISION_J = 14                   # un bailleur revoit le loyer d un logement vide tous les 14 jours
VENTE_APRES_J = 120               # un logement vide depuis 4 mois est mis en vente ( a calibrer )
BAISSE_PRIX_MOIS = 0.02
MOIS_IMPAYES_LITIGE = 3           # trois termes impayes : le bailleur saisit le juge ( a calibrer )
DELAI_EXPULSION_J = 120           # du litige a l expulsion ( procedure grecque : 4 a 12 mois, a calibrer )
RESERVE_NOURRITURE_J = 7          # un menage garde 7 jours de nourriture avant de payer loyer, impot ou travaux
MULT_LOYER = (0.80, 0.90, 1.00, 1.12, 1.25)
ACTIONS_LOYER = ("baisse_forte", "baisse", "marche", "hausse", "hausse_forte")
MARCHE_LOYER = 2
HORIZON_LOYER = 30

# ================================================================== les ventes
DROITS_MUTATION = 0.0309          # FMA 3 % + surtaxe communale de 3 % de l impot ( loi 1587/1950 ), paye par l acheteur
FRAIS_TRANSACTION = 0.012         # notaire ~ 0,8 %, cadastre 0,475 % ( a calibrer )
APPORT_MIN = 0.20                 # quotite de pret de 80 % ( pratique des banques grecques, a calibrer )

# ================================================================== les chantiers
# Materiaux d un batiment en beton arme, tonnes par m2 de plancher : 0,35 a 0,5 m3 de beton par m2, dose a ~ 320 kg de
# ciment par m3 ( C25/30, EN 206 ) ; 90 a 110 kg d acier par m3 de beton ; sable ( beton, mortiers, enduits ) et
# granulats calcaires concasses ; verre des menuiseries ( ~ 15 % de la surface en double vitrage de 2 x 4 mm ) ; gypse
# des enduits et cloisons. Ordres de grandeur a calibrer.
MATERIAUX_M2 = {"ciment": 0.150, "acier": 0.045, "sable": 0.35, "calcaire": 0.55, "verre": 0.004, "gypse": 0.012}
HEURES_M2 = 25.0                  # heures-ouvrier par m2 de plancher neuf ( 20 a 40, gros oeuvre et finitions ; a calibrer )
HEURES_REPARATION_M2 = 30.0       # par m2 et par unite de degats : la reparation coute plus de main-d oeuvre ( a calibrer )
MATERIAUX_REPARATION = 0.8
FACTEUR_REPARATION = 1.2
PART_SECOND_OEUVRE = 0.40         # menuiseries, plomberie, electricite, carrelage : fournitures importees ( a calibrer )
ACOMPTE = 0.30
DELAI_IMPORT_J = 7                # un materiau que l industrie du pays ne livre pas en 7 jours est importe
FRET_IMPORT = 0.10                # fret et marge de l importateur sur le prix mondial ( a calibrer )
SITUATION_J = 10                  # le maitre d ouvrage paie l avancement tous les 10 jours
DUREE_CIBLE_J = 120
EQUIPE_BORNES = (2, 12)
AIDE_SEISME = 0.5                 # aide publique au logement sinistre ( stegastiki syndromi ), part du devis ( a calibrer )
DELAI_RELANCE_J = 30
RESERVE_BTP = 2000.0              # drachmes gardes par l entreprise de BTP avant dividende ( a calibrer )
PART_DIVIDENDE_BTP = 0.5
NEUF, RENOVATION, RECONSTRUCTION = 0, 1, 2
NATURES_CHANTIER = ("neuf", "renovation", "reconstruction")

# ================================================================== les seismes
# Methode macrosismique Risk-UE ( Giovinazzi et Lagomarsino 2004 ) : degat moyen mu = 2,5 ( 1 + tanh( ( I + 6,25 V -
# 13,1 ) / Q ) ), V indice de vulnerabilite, Q = 2,3 ; degats de 0 a 5 ( EMS-98 ) tires d une loi binomiale de moyenne mu
# ( Braga, Dolce et Liberatore 1982 ). I : l intensite MMI du territoire, prise egale a l EMS-98 ( a une demi-classe
# pres, Musson et al. 2010 ). V selon la periode : maconnerie de pierre avant le premier code grec ( 1959 ), beton arme
# sans conception parasismique ( 1960-1984 ), code de 1984, EAK 2000 ( valeurs Risk-UE ajustees, a calibrer ).
Q_DUCTILITE = 2.3
I_DOMMAGE_MIN = 5.0               # EMS-98 : les intensites I a IV ne causent aucun dommage
V_PERIODE = ((1959, 0.74), (1984, 0.62), (1999, 0.50), (10 ** 4, 0.36))
V_ABRI = 0.30
RATIO_DOMMAGE = (0.0, 0.02, 0.10, 0.30, 0.60, 1.0)   # cout de reparation sur valeur a neuf ( type HAZUS, a calibrer )
DS_INHABITABLE = 3                # EMS-98 D3 : fiche jaune, evacue
DS_DETRUIT = 4                    # D4 et D5 : fiche rouge, demoli

# ================================================================== les batiments publics, les abris
ABRIS_PAR_MENAGE = 0.01           # reserve de protection civile ( conteneurs habitables, a calibrer )
PRIX_ABRI_M2_EUROS = 600.0        # conteneur habitable ~ 15 000 a 20 000 euros pour 30 m2 ( a calibrer )
LITS_PAR_HABITANT = 4.2e-3        # Eurostat hlth_rs_bds, Grece ~ 4,2 lits pour 1 000 habitants
M2_PAR_LIT = 100.0                # surface brute hospitaliere par lit ( 80 a 120, a calibrer )
M2_PAR_ELEVE = 8.0                # a calibrer
M2_PAR_SOLDAT = 20.0              # a calibrer
M2_PAR_AGENT = 20.0               # a calibrer
HABITANTS_PAR_COMMERCE = 40.0     # ~ 25 commerces pour 1 000 habitants ( a calibrer )
SURFACE_ATELIER = {"ferme": 300.0, "mine": 2000.0, "carriere": 1500.0, "puits": 500.0, "raffinerie": 5000.0,
                   "centrale": 3000.0, "fonderie": 4000.0, "pharmacie": 1500.0}

# nom : ( usage, surface typique m2, classname Arma, kg par m2, duree de vie en annees, source )
MODELES = (
    ("appartement", "logement", 78.0, "Land_i_House_Big_02_V1_F", 1000.0, VIE_ANS,
     "logement en immeuble ; ~ 1 t de structure par m2 de plancher en beton arme ( a calibrer )"),
    ("maison", "logement", 105.0, "Land_i_House_Small_01_V1_F", 1000.0, VIE_ANS, "maison individuelle"),
    ("abri_urgence", "logement", 30.0, "Land_Cargo_House_V1_F", 150.0, 20, "conteneur habitable de protection civile"),
    ("commerce", "commerce", 60.0, "Land_i_Shop_01_V1_F", 1000.0, VIE_ANS, "boutique de rez-de-chaussee"),
    ("atelier", "atelier", 400.0, "Land_i_Shed_Ind_F", 600.0, 40, "hangar d entreprise"),
    ("bureau_public", "public", 800.0, "Land_Offices_01_V1_F", 1000.0, VIE_ANS, "administration"),
    ("ecole", "public", 1200.0, "Land_School_01_F", 1000.0, VIE_ANS, "ecole ( Apex )"),
    ("hopital", "public", 2000.0, "Land_Hospital_main_F", 1200.0, VIE_ANS, "hopital"),
    ("caserne", "public", 800.0, "Land_i_Barracks_V1_F", 1000.0, VIE_ANS, "casernement"),
)
NOMS_MODELES = tuple(m[0] for m in MODELES)
USAGE = {m[0]: m[1] for m in MODELES}
SURFACE_TYPIQUE = {m[0]: m[2] for m in MODELES}
ARMA_CHANTIER = "Land_Unfinished_Building_01_F"
LOGEMENTS = ("appartement", "maison", "abri_urgence")
SANS, PROPRIETAIRE, LOCATAIRE, ABRI = 0, 1, 2, 3
MOTIFS_RECHERCHE = ("nouveau", "fin_bail", "surpeuplement", "migration", "sinistre", "expulsion", "dissolution")


def cout_m2():
    return COUT_CONSTRUCTION_M2_EUROS / EUROS


def surface_min(n):
    """La surface minimale pour n personnes : 9 m2 pour une, 16 pour deux, 9 de plus par personne ( normes de
    peuplement, art. D542-14 du code francais de la securite sociale, faute d une norme grecque ; a calibrer )."""
    return 0.0 if n <= 0 else 9.0 if n == 1 else 16.0 + 9.0 * (n - 2)


def capacite(surface):
    """Le nombre de personnes qu une surface loge decemment ( reciproque de surface_min )."""
    s = float(surface)
    return 0 if s < 9.0 else 1 if s < 16.0 else 2 + int((s - 16.0) // 9.0)


def facteur_age(age_ans):
    return max(PLANCHER_AGE, 1.0 + PRIME_NEUF - DECOTE_AGE_AN * max(0.0, age_ans))


def vulnerabilite(annee, modele):
    if modele == "abri_urgence": return V_ABRI
    for borne, v in V_PERIODE:
        if annee <= borne: return v
    return V_PERIODE[-1][1]


def degat_moyen(intensite, v):
    """Degat moyen EMS-98 ( 0 a 5 ) de la methode Risk-UE, vectorise."""
    return 2.5 * (1.0 + np.tanh((np.asarray(intensite, float) + 6.25 * np.asarray(v, float) - 13.1) / Q_DUCTILITE))


def tirer_dommages(intensite, v, rng):
    """Les etats de dommage 0 a 5 d un ensemble de batiments ( loi binomiale de moyenne degat_moyen ). Sous
    l intensite V, aucun dommage : l echelle EMS-98 n en decrit aucun de I a IV ( la queue de la loi binomiale en
    donnait a III, porte test_seisme )."""
    I = np.asarray(intensite, float)
    mu = np.where(I < I_DOMMAGE_MIN, 0.0, degat_moyen(I, v))
    return rng.binomial(5, np.clip(mu / 5.0, 0.0, 1.0)).astype(np.int8)


# ================================================================== les tables
class Table:
    """Des champs par rang dense, en tableaux numpy qui doublent a la demande ( Vec<T> en Rust ). Relire t[nom] a
    chaque usage : un tableau change apres une croissance."""
    __slots__ = ("n", "cap", "cols", "defauts")

    def __init__(self, champs, cap=256):
        self.n, self.cap = 0, cap
        self.cols = {nom: np.full(cap, defaut, dtype=dt) for nom, dt, defaut in champs}
        self.defauts = {nom: defaut for nom, dt, defaut in champs}

    def ajouter(self, **valeurs):
        if self.n >= self.cap:
            cap = 2 * self.cap
            for nom, a in self.cols.items():
                b = np.full(cap, self.defauts[nom], dtype=a.dtype); b[:self.cap] = a; self.cols[nom] = b
            self.cap = cap
        i = self.n
        for nom, v in valeurs.items(): self.cols[nom][i] = v
        self.n += 1
        return i

    def __getitem__(self, nom): return self.cols[nom]


CHAMPS_BATIMENTS = (
    ("oid", np.int64, -1), ("modele", np.int16, -1), ("lieu", np.int32, -1), ("parcelle", np.int32, -1),
    ("surface", np.float64, 0.0), ("annee", np.int16, 0), ("dommage", np.int8, 0), ("degats", np.float64, 0.0),
    ("vivant", np.int8, 0),           # 1 individu du Parc ; 0 sorti par un puits ; 2 refondu dans sa cohorte
    ("occupant", np.int32, -1), ("bail", np.int32, -1),
    ("offre", np.int8, 0),            # 0 hors marche, 1 a louer, 2 a vendre
    ("prix", np.float64, 0.0),        # loyer mensuel demande, ou prix de vente demande ( drachmes )
    ("vacant_j", np.int32, -1), ("decide_j", np.int32, -100000), ("chantier", np.int32, -1),
    ("origine", np.int8, 0))          # 0 recensement, 1 chantier, 2 abri importe, 3 tire d une cohorte
CHAMPS_PARCELLES = (("lieu", np.int32, -1), ("zonage", np.int8, 0), ("surface", np.float64, 0.0),
                    ("cos", np.float64, 0.0), ("bati", np.float64, 0.0))
CONSTRUCTIBLE, AGRICOLE = 0, 1


class Cadastre:
    """Les parcelles : constructibles ( logements, immeubles en copropriete, terrains a batir ) et agricoles ( celles du
    territoire, une par village, a la ferme du village ). proprietaires : le detenteur, ou None pour une copropriete."""
    __slots__ = ("t", "proprietaires")

    def __init__(self):
        self.t = Table(CHAMPS_PARCELLES)
        self.proprietaires = []

    def ajouter(self, lieu, zonage, surface, cos, proprietaire, bati=0.0):
        if not surface > 0.0: raise ValueError(f"parcelle de surface {surface!r}")
        if zonage not in (CONSTRUCTIBLE, AGRICOLE): raise ValueError(f"zonage inconnu {zonage!r}")
        self.proprietaires.append(proprietaire)
        return self.t.ajouter(lieu=lieu, zonage=zonage, surface=surface, cos=cos, bati=bati)

    def constructible_restant(self, i):
        t = self.t
        return max(0.0, t["surface"][i] * t["cos"][i] - t["bati"][i]) if t["zonage"][i] == CONSTRUCTIBLE else 0.0


class Bail:
    """Un bail d habitation. loyer : drachmes par mois, paye d avance a chaque terme ( tous les 30 jours depuis la
    signature ) ; depot : ce que le bailleur `garant` detient et rendra ; impayes : les creances du socle ( motif
    loyer ) nees de termes non payes ; du, paye : cumuls ( la porte au centime )."""
    __slots__ = ("id", "b", "locataire", "loyer", "debut_j", "fin_j", "depot", "garant", "impayes", "litige_j",
                 "fin_vue", "du", "paye")

    def __init__(self, id, b, locataire, loyer, debut_j, fin_j):
        if not 0.0 < loyer < 1e7: raise ValueError(f"loyer invalide {loyer!r}")
        if fin_j <= debut_j: raise ValueError("bail qui finit avant de commencer")
        self.id, self.b, self.locataire, self.loyer, self.debut_j, self.fin_j = id, b, locataire, float(loyer), debut_j, fin_j
        self.depot, self.garant = 0.0, None
        self.impayes = []
        self.litige_j = -1
        self.fin_vue = False
        self.du = self.paye = 0.0


class EntrepriseBTP:
    """Une entreprise de construction, une par zone de marche. caisse : ses drachmes ; stock : les restes de chantier
    ( un Stock du socle ) ; proprietaire : le menage qui recoit ses dividendes."""
    __slots__ = ("id", "lieu", "caisse", "stock", "proprietaire", "role", "encaisse", "salaires", "materiaux", "fournitures")

    def __init__(self, lieu, proprietaire):
        self.id, self.lieu, self.proprietaire, self.role = f"btp@{lieu.id}", lieu, proprietaire, "ouvrier"
        self.caisse = 0.0
        self.stock = BI.Stock()
        self.encaisse = self.salaires = self.materiaux = self.fournitures = 0.0


class Chantier:
    """Un chantier : construction neuve, renovation, reconstruction apres un seisme.
      maitre     le maitre d ouvrage ( menage, Etat, entreprise, BTP en promotion ) ; btp : l entreprise qui construit
      devis      drachmes ; paye : ce que le maitre a verse ; aide : aide publique versee au maitre
      permis_j   jour ou le permis est delivre ; debut_j, fin_j : travaux
      heures_req, heures, avancement ( 0 a 1 ) ; equipe : ouvriers vises
      besoins, livre, consomme : tonnes par bien ; stock : le Stock du socle du chantier ( materiaux sur place )
      unites     logements ou batiments produits ( surface chacun : surface / unites ) ; vendre : promotion a vendre
      retour     le menage sinistre qui reviendra a la fin, -1"""
    __slots__ = ("id", "nature", "b", "modele", "lieu", "parcelle", "surface", "unites", "maitre", "btp", "devis",
                 "paye", "aide", "permis_j", "debut_j", "fin_j", "heures_req", "heures", "avancement", "equipe",
                 "besoins", "livre", "consomme", "reste", "stock", "etat", "vendre", "retour", "relance_j",
                 "situation_j", "ouvriers", "importe")

    def __init__(self, id, nature, b, modele, lieu, parcelle, surface, unites, maitre, btp, devis, heures_req, besoins):
        if nature not in (NEUF, RENOVATION, RECONSTRUCTION): raise ValueError(f"nature inconnue {nature!r}")
        if not surface > 0.0 or not devis > 0.0 or not heures_req > 0.0: raise ValueError("chantier vide")
        self.id, self.nature, self.b, self.modele, self.lieu, self.parcelle = id, nature, b, modele, lieu, parcelle
        self.surface, self.unites, self.maitre, self.btp, self.devis = surface, unites, maitre, btp, devis
        self.paye = self.aide = 0.0
        self.permis_j = self.debut_j = self.fin_j = -1
        self.heures_req, self.heures, self.avancement = heures_req, 0.0, 0.0
        self.equipe = max(EQUIPE_BORNES[0], min(EQUIPE_BORNES[1], math.ceil(heures_req / (8.0 * DUREE_CIBLE_J))))
        self.besoins = dict(besoins)
        self.livre = {b_: 0.0 for b_ in besoins}; self.consomme = {b_: 0.0 for b_ in besoins}
        self.reste = {b_: 0.0 for b_ in besoins}
        self.importe = {b_: 0.0 for b_ in besoins}   # dont importe ( compte aussi dans livre )
        self.stock = BI.Stock()
        self.etat = "permis"
        self.vendre, self.retour, self.relance_j, self.situation_j = False, -1, -1, -1
        self.ouvriers = []          # sans le domaine 4 : habitants engages directement


class ContexteLoyer:
    __slots__ = ("traits", "b")

    def __init__(self, traits, b): self.traits, self.b = traits, b


class Immobilier:
    """L etat du domaine."""
    __slots__ = ("lieux", "k_lieu", "type_lieu", "prix_m2", "loyer_m2", "zone_m2", "zone_de", "ile_de",
                 "modele_parc", "idx_modele", "B", "cadastre", "baux", "prochain_bail", "par_proprio", "cherche",
                 "chantiers", "prochain_chantier", "btp", "btp_de_zone", "decideur", "enfia_du", "nes", "sortis",
                 "seismes_vus", "sinistres", "litiges", "stats", "delai_permis_j", "p_depart_fin_bail",
                 "justice_externe", "delai_expulsion_j", "commandes", "promotion", "objet_b", "ouvriers_libres", "voisins")

    def __init__(self):
        self.lieux, self.k_lieu = [], {}
        self.type_lieu = []; self.zone_de = []; self.ile_de = []
        self.prix_m2 = self.loyer_m2 = self.zone_m2 = None
        self.modele_parc, self.idx_modele = {}, {}
        self.B = Table(CHAMPS_BATIMENTS)
        self.cadastre = Cadastre()
        self.baux = {}; self.prochain_bail = 0
        self.par_proprio = {}          # cle du detenteur -> set de rangs de batiments individuels
        self.cherche = {}              # menage -> [ jour du debut, motif ]
        self.chantiers = {}; self.prochain_chantier = 0
        self.btp = []; self.btp_de_zone = {}
        self.decideur = None
        self.enfia_du = {}             # cle du proprietaire -> ENFIA echue non payee ( drachmes )
        self.nes = {n: {s: 0 for s in O.SOURCES} for n in NOMS_MODELES}
        self.sortis = {n: {s: 0 for s in O.PUITS} for n in NOMS_MODELES}
        self.seismes_vus = set()
        self.sinistres = []            # ( jour, rang, dommage, cout de reparation ) : assurance ( domaine 20 )
        self.litiges = {}              # bail -> jour d ouverture
        self.stats = {k: 0.0 for k in ("baux_signes", "renouvellements", "departs", "expulsions", "ventes",
                                       "abris_donnes", "abris_importes", "chantiers_ouverts", "chantiers_termines",
                                       "loyers_payes", "loyers_impayes", "loyers_encaisses", "enfia", "enfia_reportee",
                                       "candidats_refuses", "heritages", "detruits", "inhabitables")}
        self.delai_permis_j = DE.DELAI_PERMIS_J
        self.p_depart_fin_bail = P_DEPART_FIN_BAIL
        self.justice_externe = False   # le domaine 21 pose vrai : il juge et expulse lui-meme ( `expulser` )
        self.delai_expulsion_j = DELAI_EXPULSION_J
        self.commandes = {}            # bien -> unites par jour commandees a l industrie
        self.promotion = True          # le BTP construit pour vendre quand un lieu manque de logements
        self.objet_b = {}              # numero d objet du Parc -> rang dans la table
        self.ouvriers_libres = {}      # sans le domaine 4 : habitant -> chantier
        self.voisins = {}              # lieu -> [ ( km, lieu voisin de la zone ) ]


def _dom(p): return p.domaines["immobilier"]
def _membres_btp(w): return w.pays.domaines["immobilier"].btp
def _membres_chantiers(w): return w.pays.domaines["immobilier"].chantiers.values()


def cle(x):
    """La cle stable d un detenteur ( jamais id() ni hash() : l instantane et une autre execution les changent )."""
    n = type(x).__name__
    if n == "Menage": return ("M", x.id)
    if n == "Entreprise": return ("E", x.id)
    if n == "Marche": return ("K", x.lieu.id)
    if n == "Gouvernement": return ("G", "")
    return (n, str(getattr(x, "id", "")))


def _est_menage(x): return type(x).__name__ == "Menage"


def _n_vivants(mg): return sum(1 for x in mg.membres if x.vivant)


def annee(p): return ANNEE_DEPART + p.jour // 365


# ================================================================== la decision : fixer le loyer d un logement vide
def _observer_loyer(ctx): return ctx.traits


def _regle_loyer(x, ctx):
    vac, tension, effort = x[0] * 90.0, x[1] * 3.0, x[2]
    if vac >= 90.0: return 0
    if tension >= 1.5 and vac < 30.0: return 3
    if vac >= 45.0 or effort > EFFORT_MAX: return 1
    return MARCHE_LOYER


def _temoin_loyer(x, ctx, rng): return MARCHE_LOYER


POINT_LOYER = D.PointDeDecision(
    "fixer_loyer", "immobilier",
    traits=(("vacance", "jours depuis que le logement est vide, sur 90 ( son registre )"),
            ("tension", "candidats en recherche au lieu par logement offert, borne a 3, sur 3 ( annonces, agences )"),
            ("effort", "loyer de reference sur le revenu mensuel median des candidats du lieu, borne a 1 ( dossiers )"),
            ("surface", "surface du logement sur 150 m2 ( cadastre )"),
            ("age", "age du batiment sur 80 ans ( permis de construire )"),
            ("degats", "part des degats non reparee ( expertise )"),
            ("dernier_loyer", "dernier loyer demande sur le loyer de reference, sur 1,5 ( son annonce )"),
            ("offres_lieu", "logements offerts sur logements du lieu, sur 0,2 ( annonces )")),
    actions=ACTIONS_LOYER, observer=_observer_loyer, regle=_regle_loyer, temoin=_temoin_loyer,
    note=("chaque jour, pour CE logement : loyer percu sans impaye sur loyer de reference, plus 1 si un menage y vit, "
          "moins 1 si ce menage n a pas mange ce soir"),
    horizon_j=HORIZON_LOYER)


# ================================================================== petits outils
def _prix_nourriture(p, mg):
    w = p.w
    m = w.marches.get(mg.domicile.marche.id) if mg.domicile is not None and mg.domicile.marche is not None else None
    return (m.prix["nourriture"] if m is not None else C.PRIX_MONDE["nourriture"]) * (1.0 + w.gouv.tva)


def reserve(p, mg):
    """Ce qu un menage garde pour manger avant de payer loyer, impot ou travaux : 7 jours de nourriture."""
    return RESERVE_NOURRITURE_J * C.NOURRITURE_PAR_JOUR * _n_vivants(mg) * _prix_nourriture(p, mg)


def disponible(p, x):
    if _est_menage(x): return max(0.0, x.caisse - reserve(p, x))
    return max(0.0, float(getattr(x, "caisse", 0.0)))


def _revenu_roles(p, mg):
    """Le revenu net journalier que les metiers des membres rapportent : la paie du moteur ( a defaut du revenu lisse
    du domaine 3, qui part de zero pour un menage neuf )."""
    w = p.w; t = 1.0 - w.gouv.impot_revenu
    s = 0.0
    for h in mg.membres:
        if not h.vivant or h.role == "enfant": continue
        if h.role == "retraite": s += PO.PENSION_JOUR; continue
        if h.travail is None: continue
        if h.role == "paysan": s += 23.0 * t
        elif h.role == "marchand": s += 30.0 * t
        elif h.role == "patron": s += 60.0 * t
        else: s += PO.SALAIRE_HORAIRE.get(h.role, 0) * 8.0 * t
    return s


def revenu_mensuel(p, mg):
    rv = float(p.col("menage", "eco_revenu")[mg.id]) if "eco_revenu" in p.colonnes["menage"] else 0.0
    return MOIS_J * max(rv, _revenu_roles(p, mg))


def _vivants_par_menage(p):
    w = p.w; H = w.habitants; n = len(H)
    viv = np.fromiter((h.vivant for h in H), bool, n)
    mid = np.fromiter((h.menage.id if h.menage is not None else 0 for h in H), np.int64, n)
    return np.bincount(mid[viv], minlength=len(w.menages)), viv


def loyer_reference(p, b):
    """Le loyer mensuel du marche pour ce logement : surface x loyer du lieu x age x degats."""
    d = _dom(p); T = d.B
    k = int(T["lieu"][b])
    return float(T["surface"][b] * d.loyer_m2[k] * facteur_age(annee(p) - int(T["annee"][b])) * (1.0 - T["degats"][b]))


def valeur(p, b):
    """Valeur venale d un batiment ( drachmes ) : prix du lieu pour un logement ou un commerce, cout de remplacement
    deprecie pour les autres."""
    d = _dom(p); T = d.B
    k = int(T["lieu"][b]); nom = NOMS_MODELES[int(T["modele"][b])]
    age = annee(p) - int(T["annee"][b])
    if USAGE[nom] in ("logement", "commerce") and nom != "abri_urgence":
        v = T["surface"][b] * d.prix_m2[k] * facteur_age(age)
    else:
        v = T["surface"][b] * cout_m2() * FACTEUR_COUT.get(nom, 1.0) * max(0.3, 1.0 - age / VIE_ANS)
    return float(v * (1.0 - T["degats"][b]))


def valeur_reconstruction(p, b):
    d = _dom(p); T = d.B
    nom = NOMS_MODELES[int(T["modele"][b])]
    return float(T["surface"][b] * cout_m2() * FACTEUR_COUT.get(nom, 1.0))


def _objet(p, d, b):
    return p.socle.parc.objets.get(int(d.B["oid"][b]))


def proprietaire(p, b):
    o = _objet(p, _dom(p), b)
    return o.proprietaire if o is not None else None


def _indexer(d, p, x, b, signe):
    k = cle(x)
    s = d.par_proprio.get(k)
    if signe > 0:
        if s is None: s = d.par_proprio[k] = set()
        s.add(b)
    elif s is not None:
        s.discard(b)
        if not s: del d.par_proprio[k]
    if _est_menage(x):
        c = p.col("menage", "im_possede"); c[x.id] = max(0, int(c[x.id]) + signe)


def _nouveau(p, d, nom, proprietaire_, lieu_id, surface, annee_, source, origine, parcelle=-1):
    """Un batiment individuel entre dans le pays par une source declaree, et dans la table."""
    k = d.k_lieu[lieu_id]
    age = max(0, annee(p) - annee_)
    o = p.socle.parc.creer(d.modele_parc[nom], proprietaire_, lieu_id, source, p.pas,
                           min(1.0, age / (VIE_ANS if nom != "abri_urgence" else 20)))
    d.nes[nom][source] += 1
    return _inscrire(p, d, o, nom, k, surface, annee_, origine, parcelle)


def _inscrire(p, d, o, nom, k, surface, annee_, origine, parcelle=-1):
    b = d.B.ajouter(oid=o.id, modele=d.idx_modele[nom], lieu=k, parcelle=parcelle, surface=surface, annee=annee_,
                    vivant=1, origine=origine)
    d.objet_b[o.id] = b
    _indexer(d, p, o.proprietaire, b, +1)
    return b


def _ceder(p, d, b, vers, motif):
    o = _objet(p, d, b)
    _indexer(d, p, o.proprietaire, b, -1)
    p.socle.parc.ceder(o, vers, motif)
    _indexer(d, p, vers, b, +1)


def _sortir(p, d, b, puits):
    o = _objet(p, d, b)
    nom = NOMS_MODELES[int(d.B["modele"][b])]
    _indexer(d, p, o.proprietaire, b, -1)
    p.socle.parc.sortir(o, puits)
    d.sortis[nom][puits] += 1
    d.B["vivant"][b] = 0
    del d.objet_b[o.id]


def _chercher(p, d, mid, motif):
    if mid not in d.cherche: d.cherche[mid] = [p.jour, MOTIFS_RECHERCHE.index(motif)]


def _offrir(p, d, b):
    """Le logement vide passe sur le marche locatif ; son loyer sera fixe au prochain matin de marche."""
    T = d.B
    T["offre"][b] = 1; T["prix"][b] = 0.0
    if T["vacant_j"][b] < 0: T["vacant_j"][b] = p.jour
    T["decide_j"][b] = -100000


def _habitable(T, b):
    return T["vivant"][b] == 1 and T["dommage"][b] < DS_INHABITABLE


# ================================================================== le logement d un menage
def _occuper(p, d, mg, b, statut):
    T = d.B
    T["occupant"][b] = mg.id; T["offre"][b] = 0; T["vacant_j"][b] = -1; T["prix"][b] = 0.0 if statut != LOCATAIRE else T["prix"][b]
    p.col("menage", "im_logement")[mg.id] = b
    p.col("menage", "im_statut")[mg.id] = statut
    if p.col("menage", "im_chef")[mg.id] < 0: _choisir_chef(p, mg)
    d.cherche.pop(mg.id, None)


def _choisir_chef(p, mg):
    ad = [h for h in mg.membres if h.vivant and h.role != "enfant"] or [h for h in mg.membres if h.vivant]
    if ad: p.col("menage", "im_chef")[mg.id] = max(ad, key=lambda h: (h.age, -h.id)).id


def _liberer(p, d, mg, raison, offrir=True):
    """Le menage quitte son logement : fin de bail ( depot rendu ), abri rendu a la reserve, ou logement de proprietaire
    laisse vide et offert a la location."""
    T = d.B
    col = p.col("menage", "im_logement")
    b = int(col[mg.id])
    if b < 0: return
    col[mg.id] = -1; p.col("menage", "im_statut")[mg.id] = SANS
    if T["occupant"][b] != mg.id: return
    T["occupant"][b] = -1
    bid = int(T["bail"][b])
    if bid >= 0 and bid in d.baux:
        _fin_bail(p, d, d.baux[bid], raison, offrir)
        return
    nom = NOMS_MODELES[int(T["modele"][b])]
    if nom == "abri_urgence":
        o = _objet(p, d, b)
        if o is not None and o.etat == O.SERVICE:
            p.socle.parc.fondre(o)
            _indexer(d, p, o.proprietaire, b, -1)
            T["vivant"][b] = 2; del d.objet_b[o.id]
        return
    T["vacant_j"][b] = p.jour
    if offrir and _habitable(T, b) and T["chantier"][b] < 0: _offrir(p, d, b)


def _fin_bail(p, d, bail, raison, offrir=True):
    """Fin d un bail : le garant rend le depot, dont le locataire regle d abord ses arrieres ; les impayes qui restent
    demeurent des creances ( domaine 21 )."""
    L = p.socle.livre; K = p.socle.creances; T = d.B
    loc = bail.locataire
    if bail.depot > TOL and bail.garant is not None:
        rendu = L.transferer(bail.garant, loc, bail.depot, "restitution_depot")
        if bail.depot - rendu > TOL: K.constater(loc, bail.garant, bail.depot - rendu, "restitution_depot", p.jour)
        reste = rendu
        for c in list(bail.impayes):
            if reste <= TOL: break
            if K.actives.get(c.id) is not c: continue
            x = K.regler(c, L, min(reste, c.montant))
            bail.paye += x; reste -= x; _dom(p).stats["loyers_encaisses"] += x
    bail.impayes = [c for c in bail.impayes if K.actives.get(c.id) is c]
    b = bail.b
    T["bail"][b] = -1
    if T["occupant"][b] == loc.id:
        T["occupant"][b] = -1
        p.col("menage", "im_logement")[loc.id] = -1; p.col("menage", "im_statut")[loc.id] = SANS
    T["vacant_j"][b] = p.jour
    del d.baux[bail.id]
    d.litiges.pop(bail.id, None)
    if offrir and _habitable(T, b) and T["chantier"][b] < 0: _offrir(p, d, b)


def _signer(p, d, b, mg, loyer):
    """Le candidat accepte signe : il quitte son logement, verse le depot et le premier terme."""
    T = d.B; L = p.socle.livre
    _liberer(p, d, mg, "demenagement")
    bail = Bail(d.prochain_bail, b, mg, loyer, p.jour, p.jour + DUREE_BAIL_J)
    d.prochain_bail += 1
    d.baux[bail.id] = bail
    T["bail"][b] = bail.id; T["prix"][b] = loyer
    _occuper(p, d, mg, b, LOCATAIRE)
    garant = proprietaire(p, b)
    bail.garant = garant
    bail.depot = L.transferer(mg, garant, min(DEPOT_MOIS * loyer, disponible(p, mg)), "depot_garantie")
    _terme(p, bail.id, (p.jour,))
    p.poser(DUREE_BAIL_J * C.PAS_PAR_JOUR, "immobilier_fin_bail", bail.id, (bail.fin_j,))
    d.stats["baux_signes"] += 1; p.compter("bail_signe", loyer)
    return bail


def _pas_a(jour, heure):
    return int((jour * 1440 + heure * 60 - (C.DATE_DEPART[3] * 60 + C.DATE_DEPART[4])) // C.MINUTES_PAR_PAS)


def _terme(p, bid, donnees):
    """Un terme mensuel : les arrieres d abord ( les plus anciens ), puis le mois ; ce que le locataire ne peut payer
    sans toucher a sa reserve de nourriture devient une creance du bailleur."""
    d = _dom(p); bail = d.baux.get(bid)
    if bail is None: return
    L = p.socle.livre; K = p.socle.creances
    loc = bail.locataire
    bailleur = proprietaire(p, bail.b)
    dispo = disponible(p, loc)
    for c in list(bail.impayes):
        if dispo <= TOL: break
        if K.actives.get(c.id) is not c: continue
        x = K.regler(c, L, min(dispo, c.montant)); dispo -= x; bail.paye += x; d.stats["loyers_encaisses"] += x
    bail.impayes = [c for c in bail.impayes if K.actives.get(c.id) is c]
    x = L.transferer(loc, bailleur, min(bail.loyer, dispo), "loyer") if bailleur is not loc else bail.loyer
    bail.du += bail.loyer; bail.paye += x; d.stats["loyers_encaisses"] += x
    d.stats["loyers_payes"] += x; p.compter("loyer_paye", x)
    if bail.loyer - x > TOL:
        bail.impayes.append(K.constater(bailleur, loc, bail.loyer - x, "loyer", p.jour))
        d.stats["loyers_impayes"] += bail.loyer - x; p.compter("loyer_impaye", bail.loyer - x)
    if len(bail.impayes) >= MOIS_IMPAYES_LITIGE and bail.litige_j < 0:
        bail.litige_j = p.jour; d.litiges[bail.id] = p.jour
    elif not bail.impayes and bail.litige_j >= 0:
        bail.litige_j = -1; d.litiges.pop(bail.id, None)
    p.poser(max(0, _pas_a(p.jour + MOIS_J, 9.0) - p.w.pas), "immobilier_terme", bid, (p.jour + MOIS_J,))


def _fin_de_bail(p, bid, donnees):
    """Le bail arrive a son terme : le locataire part ( il cherche en gardant le logement ) ou le bail est renouvele,
    le loyer rapproche de moitie du marche."""
    d = _dom(p); bail = d.baux.get(bid)
    if bail is None or bail.fin_j != donnees[0]: return
    if p.hasard("immobilier_fin_bail").random() < d.p_depart_fin_bail and not bail.fin_vue:
        bail.fin_vue = True
        _chercher(p, d, bail.locataire.id, "fin_bail")
        d.stats["departs"] += 1; p.compter("depart_fin_bail")
    else:
        _renouveler(p, d, bail)


def _renouveler(p, d, bail):
    ref = loyer_reference(p, bail.b)
    if ref > 0: bail.loyer = max(1.0, bail.loyer + 0.5 * (ref - bail.loyer))
    bail.fin_j = p.jour + DUREE_BAIL_J; bail.fin_vue = False
    d.B["prix"][bail.b] = bail.loyer
    p.poser(DUREE_BAIL_J * C.PAS_PAR_JOUR, "immobilier_fin_bail", bail.id, (bail.fin_j,))
    d.stats["renouvellements"] += 1; p.compter("bail_renouvele")


def expulser(p, bid, motif="impayes"):
    """L expulsion d un locataire ( domaine 21, ou la procedure du domaine quand la justice n est pas la ) : le bail
    finit, le depot compense les arrieres, le menage cherche un logement ( au besoin un abri d urgence )."""
    d = _dom(p); bail = d.baux.get(bid)
    if bail is None: return False
    loc = bail.locataire
    arr = sum(c.montant for c in bail.impayes)
    _fin_bail(p, d, bail, "expulsion")
    _chercher(p, d, loc.id, "expulsion")
    d.stats["expulsions"] += 1
    p.noter("expulsion", bail=bid, menage=loc.id, arrieres=round(arr, 2), motif=motif)
    return True


# ================================================================== la journee
def _successions(p, d, nv, dis):
    """Les batiments d un menage disparu ( dissous, ou sans vivant ) passent a son heritier : le menage ou son
    representant est parti ( union ), sinon ses enfants, sinon l Etat ( desherence )."""
    w = p.w; n = len(w.menages)
    pos = p.col("menage", "im_possede")[:n]
    for i in np.nonzero((pos > 0) & ((dis == 1) | (nv[:n] == 0)))[0].tolist():
        mg = w.menages[i]
        heritier = _heritier(p, mg, dis)
        for b in sorted(d.par_proprio.get(("M", i), ())):
            _ceder(p, d, b, heritier, "heritage")
            d.stats["heritages"] += 1; p.compter("heritage_logement")


def _heritier(p, mg, dis):
    w = p.w; H = w.habitants
    chef = int(p.col("menage", "im_chef")[mg.id])
    def ok(m): return m is not None and m is not mg and not p.col("menage", "dissous")[m.id] and _n_vivants(m) > 0
    if chef >= 0 and H[chef].vivant and ok(H[chef].menage): return H[chef].menage
    enfants_de = p.domaine("population").enfants_de
    for x in ([chef] if chef >= 0 else []) + sorted(h.id for h in mg.membres):
        for e in sorted(enfants_de.get(x, ())):
            if H[e].vivant and ok(H[e].menage): return H[e].menage
    return w.gouv


def _matin(p):
    """6 h 30 : les menages disparus liberent leur logement, les successions, les menages partis ailleurs, les
    nouveaux menages et les surpeuples cherchent ; les litiges, les permis, l ENFIA du jour, les chefs de menage."""
    d = _dom(p); w = p.w; T = d.B
    n = len(w.menages)
    p.colonnes["menage"].assurer(n)
    nv, viv = _vivants_par_menage(p)
    dis = p.col("menage", "dissous")[:n]
    log = p.col("menage", "im_logement")
    for i in np.nonzero((log[:n] >= 0) & ((dis == 1) | (nv == 0)))[0].tolist():
        _liberer(p, d, w.menages[i], "dissolution")
    _successions(p, d, nv, dis)
    for mid in [m for m in d.cherche if dis[m] or nv[m] == 0]: del d.cherche[mid]
    dom = np.fromiter((d.k_lieu.get(mg.domicile.id, -1) if mg.domicile is not None else -1 for mg in w.menages), np.int64, n)
    a = log[:n] >= 0
    lieu_log = np.where(a, T["lieu"][np.maximum(log[:n], 0)], -1)
    for i in np.nonzero(a & (lieu_log != dom) & (nv > 0) & (dis == 0))[0].tolist():
        _liberer(p, d, w.menages[i], "migration"); _chercher(p, d, i, "migration")
    for i in np.nonzero((log[:n] < 0) & (nv > 0) & (dis == 0))[0].tolist(): _chercher(p, d, i, "nouveau")
    a = log[:n] >= 0
    cap = np.zeros(n, np.int64)
    idx = np.nonzero(a)[0]
    if len(idx):
        s = T["surface"][log[idx]]
        cap[idx] = np.where(s < 9.0, 0, np.where(s < 16.0, 1, 2 + ((s - 16.0) // 9.0).astype(np.int64)))
    for i in np.nonzero(a & (nv > cap) & (dis == 0))[0].tolist(): _chercher(p, d, i, "surpeuplement")
    for mid in sorted(d.cherche):
        debut, motif = d.cherche[mid]
        if log[mid] >= 0 and p.jour - debut > RECHERCHE_MAX_J and MOTIFS_RECHERCHE[motif] in ("fin_bail", "surpeuplement"):
            del d.cherche[mid]
            b = int(log[mid]); bid = int(T["bail"][b])
            if bid >= 0 and bid in d.baux and d.baux[bid].fin_vue: _renouveler(p, d, d.baux[bid])
    if not d.justice_externe:
        for bid in sorted(d.litiges):
            if p.jour - d.litiges[bid] >= d.delai_expulsion_j:
                bail = d.baux.get(bid)
                if bail is None: del d.litiges[bid]; continue
                if len(bail.impayes) >= 1: expulser(p, bid)
                else: bail.litige_j = -1; del d.litiges[bid]
    for ch in sorted(d.chantiers.values(), key=lambda c: c.id):
        if ch.etat == "permis" and p.jour >= ch.permis_j: _demarrer(p, d, ch)
        elif ch.etat == "financement" and p.jour >= ch.relance_j: _demarrer(p, d, ch)
    _enfia(p, d)
    if not p.a("travail"):
        for lid in sorted({c.lieu for c in d.chantiers.values() if c.etat == "travaux"}): _postes(p, d, lid)
    chef = p.col("menage", "im_chef")[:n]
    pos = p.col("menage", "im_possede")[:n]
    garde = ((log[:n] >= 0) | (pos > 0)) & (dis == 0) & (nv > 0)
    morts = garde & ((chef < 0) | ~viv[np.maximum(chef, 0)])
    for i in np.nonzero(morts)[0].tolist(): _choisir_chef(p, w.menages[i])


def _enfia(p, d):
    """L ENFIA d un trentieme du parc chaque jour, pour 30 jours ( le proprietaire paie par mensualites ). Ce qu un
    menage ne peut payer sans toucher a sa reserve de nourriture est reporte ( arriere non encore constate ). Exoneres :
    l Etat, les batiments inhabitables ( loi grecque apres un seisme ), les abris."""
    T = d.B; n = T.n
    parc = p.socle.parc; g = p.w.gouv
    dus = {}
    sel = np.nonzero((T["vivant"][:n] == 1) & (np.arange(n) % MOIS_J == p.jour % MOIS_J)
                     & (T["dommage"][:n] < DS_INHABITABLE))[0]
    ab = d.idx_modele["abri_urgence"]
    for b in sel.tolist():
        if T["modele"][b] == ab: continue
        o = parc.objets.get(int(T["oid"][b]))
        if o is None or o.proprietaire is g: continue
        x = DE.enfia(float(T["surface"][b]), float(d.zone_m2[T["lieu"][b]])) * MOIS_J / JOURS_AN
        k = cle(o.proprietaire)
        if k not in dus: dus[k] = [o.proprietaire, 0.0]
        dus[k][1] += x
    if p.jour % MOIS_J == 0:                                   # les cohortes ( commerces ), une fois par mois
        mes = {d.modele_parc[n_].id for n_ in NOMS_MODELES if n_ != "abri_urgence"}
        for (m, prop, lid), c in sorted(parc.cohortes.items(), key=lambda kv: (kv[0][0], cle(kv[0][1]), kv[0][2])):
            if m not in mes or prop is g or lid not in d.k_lieu: continue
            x = c.nombre * DE.enfia(SURFACE_TYPIQUE[parc.modeles[m].nom], float(d.zone_m2[d.k_lieu[lid]])) * MOIS_J / JOURS_AN
            k = cle(prop)
            if k not in dus: dus[k] = [prop, 0.0]
            dus[k][1] += x
    for k in sorted(dus):
        prop, x = dus[k]
        tout = x + d.enfia_du.pop(k, 0.0)
        payable = min(tout, disponible(p, prop))
        if payable > TOL:
            DE.percevoir(p, prop, payable, "enfia"); d.stats["enfia"] += payable; p.compter("enfia_percue", payable)
        if tout - payable > TOL:
            d.enfia_du[k] = tout - payable; d.stats["enfia_reportee"] += tout - payable
            p.compter("enfia_reportee", tout - payable)


# ================================================================== le marche locatif et les ventes ( 9 h )
def _chercheurs_par_lieu(p, d):
    w = p.w; out = {}
    for mid in sorted(d.cherche):
        mg = w.menages[mid]
        if mg.domicile is None: continue
        k = d.k_lieu.get(mg.domicile.id)
        if k is not None: out.setdefault(k, []).append(mid)
    return out


def _offres(d, genre=1):
    T = d.B; n = T.n
    idx = np.nonzero((T["offre"][:n] == genre) & (T["vivant"][:n] == 1) & (T["occupant"][:n] < 0)
                     & (T["dommage"][:n] < DS_INHABITABLE) & (T["chantier"][:n] < 0))[0]
    out = {}
    for b in idx.tolist(): out.setdefault(int(T["lieu"][b]), []).append(b)
    return out


def _decider_loyers(p, d, offres, chercheurs):
    T = d.B; w = p.w
    logements_lieu = np.bincount(T["lieu"][:T.n][(T["vivant"][:T.n] == 1) & (T["occupant"][:T.n] >= 0)],
                                 minlength=len(d.lieux))
    for k in sorted(offres):
        cands = chercheurs.get(k, [])
        revs = sorted(revenu_mensuel(p, w.menages[m]) for m in cands)
        med = revs[len(revs) // 2] if revs else 0.0
        tension = min(3.0, len(cands) / max(1, len(offres[k])))
        part = len(offres[k]) / max(1, logements_lieu[k] + len(offres[k]))
        for b in offres[k]:
            if T["prix"][b] > 0 and p.jour - T["decide_j"][b] < REVISION_J: continue
            ref = loyer_reference(p, b)
            if ref <= 0: continue
            x = (min(1.0, max(0, p.jour - int(T["vacant_j"][b])) / 90.0), tension / 3.0,
                 min(1.0, ref / med) if med > 0 else 1.0, min(1.0, T["surface"][b] / 150.0),
                 min(1.0, max(0, annee(p) - int(T["annee"][b])) / 80.0), float(min(1.0, T["degats"][b])),
                 min(1.0, T["prix"][b] / ref / 1.5), min(1.0, part / 0.2))
            a = d.decideur.decider(b, ContexteLoyer(x, b))
            T["prix"][b] = round(ref * MULT_LOYER[a], 2); T["decide_j"][b] = p.jour


def _voisins(p, d, k):
    """Les lieux habitables de la meme zone de marche a moins de RAYON_RECHERCHE_KM de route, du plus proche au plus
    loin ( km ) : la ou un menage cherche un logement sans changer d emploi ni de marche."""
    v = d.voisins.get(k)
    if v is None:
        w = p.w; a = w.carte.lieux[d.lieux[k]]
        v = []
        for k2, lid in enumerate(d.lieux):
            if d.type_lieu[k2] == "site" or d.zone_de[k2] != d.zone_de[k]: continue
            km = 0.0 if k2 == k else w.carte.km_route(a, w.carte.lieux[lid])
            if km <= RAYON_RECHERCHE_KM: v.append((km, k2))
        v.sort(); d.voisins[k] = v
    return v


def _changer_de_lieu(p, mg, lieu):
    """Le menage s installe dans un autre lieu de sa zone : meme marche, memes emplois, memes ecoles."""
    if mg.domicile is lieu: return
    ancien = mg.domicile
    mg.domicile = lieu
    for h in mg.membres:
        if not h.vivant: continue
        rentre = h.lieu is ancien or h.lieu is None
        h.domicile = lieu
        if rentre and h.poste == "maison": h.lieu = lieu


def _apparier(p, d, offres, chercheurs):
    """Chaque chercheur ( les sans-logis et les menages en abri d abord, puis par anciennete de recherche ) prend, dans
    son lieu ou un lieu voisin de sa zone ( moins de 25 km ), le logement offert au meilleur rapport surface utile sur
    loyer ( rabattu de la distance ), sous 40 % de son revenu ; le bailleur l accepte s il a moins de deux incidents
    bancaires et de quoi payer le depot. Un proprietaire qui cherche reprend d abord son propre logement vide."""
    T = d.B; w = p.w
    log = p.col("menage", "im_logement"); st = p.col("menage", "im_statut")
    inc = p.col("menage", "incidents") if "incidents" in p.colonnes["menage"] else None
    libres = {k: [b for b in lst if T["prix"][b] > 0] for k, lst in offres.items()}
    tous = sorted((m for lst in chercheurs.values() for m in lst),
                  key=lambda m: (0 if log[m] < 0 or st[m] == ABRI else 1, d.cherche[m][0], m))
    for mid in tous:
        mg = w.menages[mid]
        n = _n_vivants(mg)
        if n == 0 or mg.domicile is None: continue
        k = d.k_lieu[mg.domicile.id]
        siens = [b for b in sorted(d.par_proprio.get(("M", mid), ())) if T["occupant"][b] < 0 and _habitable(T, b)
                 and T["chantier"][b] < 0 and T["lieu"][b] == k and capacite(T["surface"][b]) >= n and T["bail"][b] < 0]
        if siens:
            b = max(siens, key=lambda x: (T["surface"][x], -x))
            if b in libres.get(k, ()): libres[k].remove(b)
            _liberer(p, d, mg, "demenagement"); _occuper(p, d, mg, b, PROPRIETAIRE)
            p.compter("emmenagement_proprietaire"); continue
        plafond = EFFORT_MAX * revenu_mensuel(p, mg)
        actuel = int(log[mid])
        s_act = T["surface"][actuel] if actuel >= 0 and st[mid] != ABRI else 0.0
        libre_choix = s_act == 0.0 or MOTIFS_RECHERCHE[d.cherche[mid][1]] == "fin_bail"
        utile = surface_min(n) + 30.0
        cands = []
        for km, k2 in _voisins(p, d, k):
            for b in libres.get(k2, ()):
                if T["prix"][b] <= plafond and capacite(T["surface"][b]) >= n and (libre_choix or T["surface"][b] > s_act):
                    cands.append((-min(T["surface"][b], utile) / T["prix"][b] / (1.0 + km / RAYON_RECHERCHE_KM), b, k2))
        for _, b, k2 in sorted(cands)[:3]:
            loyer = float(T["prix"][b])
            if (inc is not None and inc[mid] >= INCIDENTS_MAX) or mg.caisse < loyer or proprietaire(p, b) is mg:
                d.stats["candidats_refuses"] += 1; p.compter("candidat_refuse"); continue
            _liberer(p, d, mg, "demenagement")
            _changer_de_lieu(p, mg, w.carte.lieux[d.lieux[k2]])
            _signer(p, d, b, mg, loyer)
            libres[k2].remove(b)
            break


def _loger_en_urgence(p, d):
    """Un menage sans logement apres le marche du jour recoit un abri d urgence de l Etat : tire de la reserve la
    plus proche de son ile, sinon achete a l etranger."""
    w = p.w; log = p.col("menage", "im_logement"); dis = p.col("menage", "dissous")
    for mid in sorted(d.cherche):
        mg = w.menages[mid]
        if log[mid] >= 0 or dis[mid] or mg.domicile is None: continue
        n = _n_vivants(mg)
        if n == 0: continue
        motif = d.cherche[mid]
        b = _abri(p, d, mg.domicile, n)
        _occuper(p, d, mg, b, ABRI)
        d.cherche[mid] = motif                            # il cherche toujours, depuis son abri
        d.stats["abris_donnes"] += 1; p.compter("relogement_urgence")


def _abri(p, d, lieu, n):
    parc = p.socle.parc; w = p.w; g = w.gouv
    m = d.modele_parc["abri_urgence"].id
    surf = max(SURFACE_TYPIQUE["abri_urgence"], surface_min(n))
    cands = [(lid, c) for (mm, prop, lid), c in parc.cohortes.items()
             if mm == m and prop is g and c.nombre > 0 and w.carte.lieux[lid].ile == lieu.ile]
    if cands:
        lid, c = min(cands, key=lambda x: (w.carte.lieux[x[0]].distance(lieu), x[0]))
        o = parc.materialiser(c, p.pas)
        parc.deplacer(o, lieu.id)
        b = _inscrire(p, d, o, "abri_urgence", d.k_lieu[lieu.id], surf, annee(p), 3)
        return b
    prix = surf * PRIX_ABRI_M2_EUROS / EUROS
    p.socle.livre.payer_l_exterieur(g, prix, "achat_abri")
    b = _nouveau(p, d, "abri_urgence", g, lieu.id, surf, annee(p), "importe", 2)
    d.stats["abris_importes"] += 1
    p.noter("abri_importe", lieu=lieu.id, surface=round(surf, 1))
    return b


def _ventes(p, d):
    """Un logement vide depuis 4 mois passe en vente ; chaque semaine, un locataire ou un sans-logis qui a l apport
    achete le logement a vendre le moins cher de son lieu qui le loge : credit immobilier ( decision des banques ),
    droits de mutation a l Etat, frais au marche."""
    T = d.B; w = p.w; L = p.socle.livre; n = T.n
    for b in np.nonzero((T["offre"][:n] == 1) & (T["vivant"][:n] == 1) & (T["occupant"][:n] < 0)
                        & (T["vacant_j"][:n] >= 0) & (p.jour - T["vacant_j"][:n] >= VENTE_APRES_J))[0].tolist():
        T["offre"][b] = 2; T["prix"][b] = round(valeur(p, b), 2); T["decide_j"][b] = p.jour
    for b in np.nonzero((T["offre"][:n] == 2) & (T["vivant"][:n] == 1))[0].tolist():
        if p.jour > T["decide_j"][b] and (p.jour - T["decide_j"][b]) % MOIS_J == 0:
            T["prix"][b] = round(T["prix"][b] * (1.0 - BAISSE_PRIX_MOIS), 2)
    ventes = _offres(d, 2)
    if not ventes: return
    st = p.col("menage", "im_statut"); log = p.col("menage", "im_logement"); dis = p.col("menage", "dissous")
    acheteurs = [i for i in range(len(w.menages)) if i % 7 == p.jour % 7 and st[i] in (LOCATAIRE, ABRI, SANS)
                 and not dis[i] and (log[i] >= 0 or i in d.cherche)]
    for mid in acheteurs:
        mg = w.menages[mid]
        if mg.domicile is None: continue
        k = d.k_lieu.get(mg.domicile.id)
        n = _n_vivants(mg)
        cands = [b for b in ventes.get(k, []) if T["occupant"][b] < 0 and T["offre"][b] == 2 and capacite(T["surface"][b]) >= n]
        dispo = disponible(p, mg)
        cands = [b for b in cands if dispo >= APPORT_MIN * T["prix"][b] * (1 + DROITS_MUTATION + FRAIS_TRANSACTION)]
        if not cands: continue
        b = min(cands, key=lambda x: (T["prix"][x], x))
        if vendre(p, b, mg, float(T["prix"][b])):
            ventes[k].remove(b)


def vendre(p, b, acheteur, prix):
    """La vente d un batiment vide a `acheteur` au prix `prix` : apport, credit immobilier pour le reste ( les banques
    decident ; un credit incomplet est rembourse et la vente tombe ), prix au vendeur, droits de mutation a l Etat,
    frais au marche du lieu. Rend vrai si la vente a lieu."""
    d = _dom(p); T = d.B; L = p.socle.livre; w = p.w
    vendeur = proprietaire(p, b)
    if vendeur is None or vendeur is acheteur or T["occupant"][b] >= 0: return False
    droits, frais = DROITS_MUTATION * prix, FRAIS_TRANSACTION * prix
    total = prix + droits + frais
    apport = min(total, disponible(p, acheteur))
    besoin = total - apport
    if besoin > TOL:
        if not _est_menage(acheteur) and type(acheteur).__name__ != "EntrepriseBTP": return False
        pr = BQ.demander_credit(p, acheteur, besoin, type_="immo", motif="achat_logement")
        if pr is None: return False
        if pr.montant < besoin - TOL:
            BQ.rembourser_par_anticipation(p, pr); return False
    L.transferer(acheteur, vendeur, prix, "vente_logement")
    L.transferer(acheteur, w.gouv, droits, "droits_mutation")
    k = T["lieu"][b]
    marche = w.marches.get(w.carte.lieux[d.lieux[k]].marche.id)
    if marche is not None: L.transferer(acheteur, marche, frais, "frais_transaction")
    _ceder(p, d, b, acheteur, "vente")
    T["offre"][b] = 0; T["prix"][b] = 0.0
    if _est_menage(acheteur) and USAGE[NOMS_MODELES[int(T["modele"][b])]] == "logement":
        _liberer(p, d, acheteur, "achat")
        _occuper(p, d, acheteur, b, PROPRIETAIRE)
    d.stats["ventes"] += 1; p.compter("vente_logement", prix)
    return True


def _marche(p):
    d = _dom(p)
    chercheurs = _chercheurs_par_lieu(p, d)
    offres = _offres(d, 1)
    _decider_loyers(p, d, offres, chercheurs)
    _apparier(p, d, offres, chercheurs)
    _loger_en_urgence(p, d)
    _ventes(p, d)
    if d.promotion and p.jour % MOIS_J == 15: _promotions(p, d)


# ================================================================== les chantiers
def ouvrir_chantier(p, maitre, lieu_id, modele, surface, nature=NEUF, b=-1, unites=1, parcelle=-1, vendre_=False,
                    retour=-1, aide=0.0):
    """Un chantier : devis, besoins, heures ; le maitre d ouvrage paie les droits de permis ( domaine 6 ) et attend le
    permis ( DELAI_PERMIS_J ). Une aide publique ( part du devis ) est versee au maitre a l ouverture. Rend le Chantier,
    ou None si le maitre ne peut payer les droits."""
    d = _dom(p); w = p.w; T = d.B
    if modele not in NOMS_MODELES: raise KeyError(f"modele inconnu {modele!r}")
    if not surface > 0 or not (isinstance(unites, int) and unites >= 1): raise ValueError("surface ou unites invalides")
    lieu = w.carte.lieux[lieu_id]
    btp = d.btp_de_zone[lieu.marche.id]
    f = FACTEUR_COUT.get(modele, 1.0)
    if nature == RENOVATION:
        deg = float(T["degats"][b])
        if deg <= 0: raise ValueError("renovation d un batiment sans degats")
        devis = surface * cout_m2() * f * deg * FACTEUR_REPARATION
        heures = surface * HEURES_REPARATION_M2 * deg
        besoins = {x: q * surface * deg * MATERIAUX_REPARATION for x, q in MATERIAUX_M2.items()}
    else:
        devis = surface * cout_m2() * f
        heures = surface * HEURES_M2
        besoins = {x: q * surface for x, q in MATERIAUX_M2.items()}
    ch = Chantier(d.prochain_chantier, nature, b, modele, lieu_id, parcelle, float(surface), unites, maitre, btp,
                  round(devis, 2), heures, besoins)
    L = p.socle.livre
    if aide > 0:
        ch.aide = L.transferer(w.gouv, maitre, aide * ch.devis, "aide_reconstruction")
    droits = DE.droits_permis(ch.devis)
    if maitre is not w.gouv:
        if disponible(p, maitre) < droits - TOL: return None
        DE.percevoir(p, maitre, droits, "droits_permis")
    d.prochain_chantier += 1
    d.chantiers[ch.id] = ch
    ch.vendre, ch.retour = vendre_, retour
    ch.permis_j = p.jour + int(d.delai_permis_j)
    if b >= 0: T["chantier"][b] = ch.id
    d.stats["chantiers_ouverts"] += 1; p.compter("permis_depose", ch.devis)
    p.noter("chantier_ouvert", chantier=ch.id, nature=NATURES_CHANTIER[nature], modele=modele, lieu=lieu_id,
            devis=round(ch.devis, 2))
    return ch


def _demarrer(p, d, ch):
    """Le permis est la : le maitre verse l acompte ( un menage emprunte ce qui lui manque ) ; l entreprise ouvre ses
    postes. Sans financement, le chantier attend un mois."""
    L = p.socle.livre; w = p.w
    m = ch.maitre
    besoin = ch.devis - ch.paye
    if _est_menage(m) and disponible(p, m) < besoin - TOL:
        pr = BQ.demander_credit(p, m, besoin - disponible(p, m), type_="immo", motif="travaux")
        if pr is None and disponible(p, m) < ACOMPTE * ch.devis:
            ch.etat = "financement"; ch.relance_j = p.jour + DELAI_RELANCE_J; return
    if m is ch.btp:
        ch.paye = ch.devis                                  # une promotion : l entreprise paie ses propres couts
    else:
        acompte = min(ACOMPTE * ch.devis, disponible(p, m)) if m is not w.gouv else ACOMPTE * ch.devis
        x = L.transferer(m, ch.btp, acompte, "travaux")
        ch.paye += x; ch.btp.encaisse += x
    ch.etat = "travaux"; ch.debut_j = ch.situation_j = p.jour
    _postes(p, d, ch.lieu)


def _chantiers_du_lieu(d, lieu_id):
    return [c for c in d.chantiers.values() if c.lieu == lieu_id and c.etat == "travaux"]


def _postes(p, d, lieu_id):
    """Les ouvriers vises au lieu : la somme des equipes des chantiers en travaux. Avec le domaine 4, l entreprise est
    l employeur declare ( lieu, ouvrier ) ; sans lui, les chomeurs du registre du domaine 3 sont engages."""
    cs = _chantiers_du_lieu(d, lieu_id)
    total = sum(c.equipe for c in cs)
    if p.a("travail"):
        TR = importlib.import_module(".d04_travail", __package__)
        if cs: TR.declarer_employeur(p, lieu_id, "ouvrier", cs[0].btp)
        TR.ouvrir_postes(p, lieu_id, "ouvrier", total)
        if total == 0:
            for h in list(p.w.au_travail_de(p.w.carte.lieux[lieu_id], "ouvrier")):
                if h.vivant and h.travail is not None and h.travail.id == lieu_id:
                    TR.rompre_contrat(p, h, "fin_chantier", involontaire=True)
        return
    for ch in cs:
        ch.ouvriers = [i for i in ch.ouvriers if p.w.habitants[i].vivant and p.w.habitants[i].travail is None]
        manque = ch.equipe - len(ch.ouvriers)
        if manque <= 0: continue
        for i in _chomeurs(p, d, lieu_id)[:manque]:
            ch.ouvriers.append(i); d.ouvriers_libres[i] = ch.id
    for i in [i for i, c in d.ouvriers_libres.items() if c not in d.chantiers or d.chantiers[c].etat != "travaux"]:
        del d.ouvriers_libres[i]


def _chomeurs(p, d, lieu_id):
    w = p.w; lieu = w.carte.lieux[lieu_id]
    eco = p.domaine("economie")
    out = []
    for i in sorted(eco.chomeurs):
        h = w.habitants[i]
        if (i in d.ouvriers_libres or not h.vivant or h.travail is not None or h.role in ("enfant", "retraite")
                or h.domicile is None or h.domicile.ile != lieu.ile or POP.age_de(p, h) < 18
                or w.carte.km_route(h.domicile, lieu) > 40.0): continue
        out.append(i)
    return out


def _materiaux(p):
    """16 h 10, apres les livraisons de l industrie : chaque chantier en travaux recoit ce qui lui manque, du site le
    mieux pourvu ; la commande permanente a l industrie suit les besoins restants."""
    d = _dom(p)
    reste = {x: 0.0 for x in MATERIAUX_M2}
    for ch in sorted(d.chantiers.values(), key=lambda c: c.id):
        if ch.etat not in ("travaux", "permis", "financement"): continue
        for x in sorted(ch.besoins):
            manque = ch.besoins[x] - ch.livre[x]
            if manque <= EPS: continue
            if ch.etat == "travaux":
                q = IND.livrer(p, x, manque, ch.stock, ch.btp)
                ch.livre[x] += q; ch.btp.materiaux += q * IND.BIENS[x][2]
                manque -= q
                if manque > EPS and p.jour - ch.debut_j >= DELAI_IMPORT_J:
                    pu = IND.BIENS[x][2] * (1.0 + FRET_IMPORT)
                    paye = p.socle.livre.payer_l_exterieur(ch.btp, manque * pu, "import_materiaux")
                    q = paye / pu
                    if q > 0:
                        p.socle.livre.importer(ch.stock, p.socle.catalogue.id(x), q, "import_materiaux")
                        ch.livre[x] += q; ch.importe[x] += q; ch.btp.materiaux += paye
                        manque -= q
            reste[x] += max(0.0, manque)
    for x in sorted(reste):
        v = round(reste[x] / 10.0, 3)                      # dix jours pour livrer ce qui reste
        if d.commandes.get(x, 0.0) != v:
            IND.commander(p, x, v); d.commandes[x] = v


def _travail(p):
    """17 h 50, avant la paie : les heures pointees sur chaque chantier ( domaine 4 ) sont creditees aux ouvriers,
    que la paie fait payer par l entreprise ; sans le domaine 4, l entreprise paie elle-meme ses ouvriers. L avancement
    suit les heures, borne par les materiaux sur place ; les materiaux sont consommes et le second oeuvre paye au prorata."""
    d = _dom(p); w = p.w; L = p.socle.livre
    avec_travail = p.a("travail")
    par_lieu = {}
    for ch in sorted(d.chantiers.values(), key=lambda c: c.id):
        if ch.etat == "travaux": par_lieu.setdefault(ch.lieu, []).append(ch)
    for lid in sorted(par_lieu):
        cs = par_lieu[lid]
        heures = 0.0
        if avec_travail:
            pt = p.col("habitant", "tr_pointage")
            for h in w.au_travail_de(w.carte.lieux[lid], "ouvrier"):
                if not h.vivant or h.travail is None or h.travail.id != lid: continue
                x = float(pt[h.id]) / 6.0
                if x > h.heures_jour: heures += x - h.heures_jour; h.heures_jour = x
        else:
            for ch in cs:
                for i in ch.ouvriers:
                    h = w.habitants[i]
                    if (not h.vivant or h.travail is not None or (h.etat == "I" and h.gravite > 0.5)
                            or h.faim > C.ABSENCE_FAIM): continue
                    brut = 8.0 * PO.SALAIRE_HORAIRE["ouvrier"]
                    paye, _ = L.payer_ou_devoir(ch.btp, h.menage, brut, "salaire", p.socle.creances, p.jour)
                    ch.btp.salaires += brut
                    if w.gouv.impot_revenu > 0 and paye > 0:
                        L.transferer(h.menage, w.gouv, paye * w.gouv.impot_revenu, "impot sur le revenu")
                    heures += 8.0
        eq = sum(c.equipe for c in cs)
        for ch in cs:
            _avancer(p, d, ch, heures * ch.equipe / eq if eq else 0.0)


def _avancer(p, d, ch, heures):
    L = p.socle.livre; cat = p.socle.catalogue
    if heures <= 0: return
    ch.heures += heures
    visee = min(1.0, ch.heures / ch.heures_req)
    permis = min((ch.consomme[x] + ch.stock[cat.id(x)]) / q for x, q in ch.besoins.items() if q > 0)
    nouvelle = min(visee, permis)
    delta = nouvelle - ch.avancement
    if delta <= 1e-12: return
    for x, q in sorted(ch.besoins.items()):
        voulu = q * nouvelle - ch.consomme[x]
        if voulu > 0:
            ch.consomme[x] += L.consommer(ch.stock, cat.id(x), min(voulu, ch.stock[cat.id(x)]), "construction")
    f = L.payer_l_exterieur(ch.btp, PART_SECOND_OEUVRE * ch.devis * delta, "second_oeuvre")
    ch.btp.fournitures += f
    ch.avancement = nouvelle
    if ch.avancement >= 1.0 - 1e-12: _terminer(p, d, ch)


def _situations(p, d):
    """Tous les 10 jours, le maitre paie l avancement ; ce qu il ne peut payer devient une creance de l entreprise."""
    L = p.socle.livre; w = p.w; K = p.socle.creances
    for ch in sorted(d.chantiers.values(), key=lambda c: c.id):
        if ch.etat != "travaux" or p.jour - ch.situation_j < SITUATION_J: continue
        ch.situation_j = p.jour
        du = ch.devis * max(ACOMPTE, ch.avancement) - ch.paye
        if du <= TOL: continue
        x = L.transferer(ch.maitre, ch.btp, min(du, disponible(p, ch.maitre)), "travaux")
        ch.paye += x; ch.btp.encaisse += x


def _terminer(p, d, ch):
    """Le chantier finit : les restes vont au stock de l entreprise, le solde est du, le batiment nait ( source
    fabrique ) ou est repare ; le sinistre revient ; les ouvriers sont liberes."""
    L = p.socle.livre; w = p.w; T = d.B; cat = p.socle.catalogue; K = p.socle.creances
    for x in sorted(ch.besoins):
        q = ch.stock[cat.id(x)]
        if q > 0: ch.reste[x] += L.deplacer(ch.stock, ch.btp.stock, cat.id(x), q, "restes_chantier")
    du = ch.devis - ch.paye
    if du > TOL:
        x = L.transferer(ch.maitre, ch.btp, min(du, disponible(p, ch.maitre)), "travaux")
        ch.paye += x; ch.btp.encaisse += x
        if du - x > TOL: K.constater(ch.btp, ch.maitre, du - x, "travaux", p.jour)
    ch.etat = "termine"; ch.fin_j = p.jour
    lieu = w.carte.lieux[ch.lieu]
    nes = []
    if ch.nature == RENOVATION:
        b = ch.b
        T["dommage"][b] = 0; T["degats"][b] = 0.0; T["chantier"][b] = -1
        o = _objet(p, d, b)
        if o is not None and o.etat != O.SERVICE: p.socle.parc.mettre_en_etat(o, O.SERVICE)
        nes = [b]
    else:
        if ch.b >= 0: T["chantier"][ch.b] = -1
        for _ in range(ch.unites):
            b = _nouveau(p, d, ch.modele, ch.maitre, ch.lieu, ch.surface / ch.unites, annee(p), "fabrique", 1, ch.parcelle)
            nes.append(b)
        if ch.parcelle >= 0: d.cadastre.t["bati"][ch.parcelle] += ch.surface
    d.stats["chantiers_termines"] += 1
    p.noter("chantier_termine", chantier=ch.id, nature=NATURES_CHANTIER[ch.nature], jours=ch.fin_j - ch.debut_j,
            devis=round(ch.devis, 2))
    for b in nes:
        if USAGE[ch.modele] != "logement": continue
        if ch.retour >= 0 and b == nes[0]:
            mg = w.menages[ch.retour]
            if not p.col("menage", "dissous")[mg.id] and _n_vivants(mg) > 0 and mg.domicile is lieu \
                    and proprietaire(p, b) is mg:
                _liberer(p, d, mg, "retour"); _occuper(p, d, mg, b, PROPRIETAIRE); continue
        if T["occupant"][b] >= 0: continue
        T["vacant_j"][b] = p.jour
        if ch.vendre:
            T["offre"][b] = 2; T["prix"][b] = round(valeur(p, b), 2); T["decide_j"][b] = p.jour
        else: _offrir(p, d, b)
    _postes(p, d, ch.lieu)


def _promotions(p, d):
    """Une fois par mois : dans un lieu ou au moins trois menages attendent un logement dans un abri ou sans logement
    et ou rien n est offert, l entreprise de BTP de la zone batit pour vendre sur un terrain libre, si sa caisse paie
    le terrain et un tiers du devis."""
    w = p.w; T = d.B; ca = d.cadastre; L = p.socle.livre
    st = p.col("menage", "im_statut")
    offres = _offres(d, 1)
    attente = {}
    for mid in sorted(d.cherche):
        mg = w.menages[mid]
        if st[mid] in (SANS, ABRI) and mg.domicile is not None and mg.domicile.id in d.k_lieu:
            k = d.k_lieu[mg.domicile.id]; attente[k] = attente.get(k, 0) + 1
    for k in sorted(attente):
        if attente[k] < 3 or offres.get(k): continue
        if any(c.lieu == d.lieux[k] and c.vendre and c.etat != "termine" for c in d.chantiers.values()): continue
        typ = d.type_lieu[k]
        modele = "maison" if typ == "village" else "appartement"
        unites = 2 if typ == "village" else 4
        surf = SURFACE_TYPIQUE[modele] * unites
        libres = [i for i in range(ca.t.n) if ca.t["lieu"][i] == k and ca.constructible_restant(i) >= surf]
        if not libres: continue
        i = libres[0]
        lieu = w.carte.lieux[d.lieux[k]]
        btp = d.btp_de_zone[lieu.marche.id]
        terrain = PART_TERRAIN * surf * d.prix_m2[k]
        if btp.caisse < terrain + ACOMPTE * surf * cout_m2() + DE.droits_permis(surf * cout_m2()): continue
        vendeur = ca.proprietaires[i]
        if vendeur is not None and vendeur is not btp:
            L.transferer(btp, vendeur, terrain, "vente_terrain")
            ca.proprietaires[i] = btp
        ouvrir_chantier(p, btp, lieu.id, modele, surf, NEUF, -1, unites, i, vendre_=True)


def _soir(p):
    """20 h 10, apres le repas : la note du jour de chaque logement dont un choix de loyer attend ; les situations de
    travaux ; les dividendes du BTP en fin de mois."""
    d = _dom(p); w = p.w; T = d.B
    dec = d.decideur
    nourri = w.nourri_menage
    for b in [k for k, a in dec.attentes.items() if a.choix]:
        occ = int(T["occupant"][b])
        r = 0.0
        if occ >= 0 and T["vivant"][b] == 1:
            r += 1.0
            bid = int(T["bail"][b])
            if bid >= 0 and bid in d.baux and not d.baux[bid].impayes:
                ref = loyer_reference(p, b)
                if ref > 0: r += d.baux[bid].loyer / ref
            if not nourri.get(occ, True): r -= 1.0
        dec.noter(b, r, p.jour)
    for k in [k for k, a in dec.attentes.items() if not a.choix]: del dec.attentes[k]
    _situations(p, d)
    if p.jour % MOIS_J == MOIS_J - 1:
        for btp in d.btp:
            engage = sum(c.devis * (1 - c.avancement) for c in d.chantiers.values() if c.btp is btp and c.etat == "travaux")
            x = PART_DIVIDENDE_BTP * (btp.caisse - RESERVE_BTP - 0.3 * engage)
            if x > TOL and btp.proprietaire is not None:
                p.socle.livre.transferer(btp, btp.proprietaire, x, "dividende_btp")
    for i in [i for i, c in d.chantiers.items() if c.etat == "termine" and p.jour - c.fin_j > 30]:
        del d.chantiers[i]


# ================================================================== les seismes
def _seismes(p):
    """0 h 10 : les seismes ressentis du jour ( territoire, intensite MMI par lieu ) endommagent les batiments."""
    d = _dom(p)
    for c in TER.catastrophes_en_cours(p, type_="seisme"):
        if c.debut_j != p.jour or not c.intensites: continue
        k = (c.debut_j, c.ile, c.lieu, round(c.valeur, 3))
        if k in d.seismes_vus: continue
        d.seismes_vus.add(k)
        appliquer_seisme(p, c.intensites)


def appliquer_seisme(p, intensites):
    """Les dommages d un seisme : pour chaque lieu et son intensite, chaque batiment tire un etat de dommage EMS-98
    selon sa vulnerabilite ; D3 : inhabitable, evacue, repare ; D4-D5 : detruit ( puits detruit ), reconstruit ; D2 :
    repare en restant habite. Les commerces des cohortes touches en sont tires. Les sinistres sont reloges le jour meme.
    Rend { lieu : ( batiments, touches, inhabitables, detruits ) }."""
    d = _dom(p); T = d.B; w = p.w; parc = p.socle.parc
    rng = p.hasard("immobilier_seisme")
    out = {}
    for lid in sorted(intensites):
        k = d.k_lieu.get(lid)
        if k is None: continue
        I = float(intensites[lid])
        n = T.n
        sel = np.nonzero((T["vivant"][:n] == 1) & (T["lieu"][:n] == k))[0]
        # les commerces de la cohorte du lieu
        mcom = d.modele_parc["commerce"].id
        for (m, prop, l2), c in sorted(parc.cohortes.items(), key=lambda kv: (kv[0][0], cle(kv[0][1]), kv[0][2])):
            if m != mcom or l2 != lid or c.nombre == 0: continue
            ds = tirer_dommages(np.full(c.nombre, I), np.full(c.nombre, vulnerabilite(1975, "commerce")), rng)
            detruits = int((ds >= DS_DETRUIT).sum())
            if detruits: parc.sortir_de_cohorte(c, detruits, "detruit"); d.sortis["commerce"]["detruit"] += detruits
            for x in sorted(ds[(ds >= 2) & (ds < DS_DETRUIT)].tolist()):
                cc = parc.cohortes.get((m, prop, l2))
                if cc is None or cc.nombre == 0: break
                o = parc.materialiser(cc, p.pas)
                b = _inscrire(p, d, o, "commerce", k, SURFACE_TYPIQUE["commerce"], 1975, 3)
                T["dommage"][b] = x; T["degats"][b] = RATIO_DOMMAGE[x]
                if x >= DS_INHABITABLE: parc.mettre_en_etat(o, O.IMMOBILISE)
        if len(sel) == 0: out[lid] = (0, 0, 0, 0); continue
        v = np.array([vulnerabilite(int(T["annee"][b]), NOMS_MODELES[int(T["modele"][b])]) for b in sel.tolist()])
        ds = tirer_dommages(np.full(len(sel), I), v, rng)
        touches = inhab = detr = 0
        for b, x in zip(sel.tolist(), ds.tolist()):
            if x <= T["dommage"][b]: continue
            touches += 1
            T["dommage"][b] = x; T["degats"][b] = max(T["degats"][b], RATIO_DOMMAGE[x])
            d.sinistres.append((p.jour, b, x, round(RATIO_DOMMAGE[x] * valeur_reconstruction(p, b), 2)))
            if x >= DS_DETRUIT: detr += 1; _detruire_seisme(p, d, b)
            elif x >= DS_INHABITABLE: inhab += 1; _evacuer(p, d, b)
            elif x >= 2: _reparer(p, d, b, RENOVATION)
        d.stats["detruits"] += detr; d.stats["inhabitables"] += inhab
        out[lid] = (len(sel), touches, inhab, detr)
        p.noter("seisme_dommages", lieu=lid, intensite=round(I, 1), touches=touches, inhabitables=inhab, detruits=detr)
    offres = _offres(d, 1)
    ch = _chercheurs_par_lieu(p, d)
    _decider_loyers(p, d, offres, ch)
    _apparier(p, d, offres, ch)
    _loger_en_urgence(p, d)
    return out


def _chasser(p, d, b, motif):
    """Les occupants d un batiment qui ne loge plus quittent les lieux : fin de bail ( force majeure ), le proprietaire
    occupant reviendra a la fin des travaux."""
    T = d.B; w = p.w
    occ = int(T["occupant"][b])
    if occ < 0: return -1
    mg = w.menages[occ]
    proprio = p.col("menage", "im_statut")[occ] == PROPRIETAIRE
    _liberer(p, d, mg, motif, offrir=False)
    _chercher(p, d, occ, "sinistre")
    return occ if proprio else -1


def _evacuer(p, d, b):
    o = _objet(p, d, b)
    retour = _chasser(p, d, b, "sinistre")
    d.B["offre"][b] = 0
    if o is not None: p.socle.parc.mettre_en_etat(o, O.IMMOBILISE)
    _reparer(p, d, b, RENOVATION, retour)


def _detruire_seisme(p, d, b):
    T = d.B
    retour = _chasser(p, d, b, "sinistre")
    proprio = proprietaire(p, b)
    nom = NOMS_MODELES[int(T["modele"][b])]
    lid = d.lieux[int(T["lieu"][b])]
    surf = float(T["surface"][b]); parcelle = int(T["parcelle"][b])
    bid = int(T["bail"][b])
    if bid >= 0 and bid in d.baux: _fin_bail(p, d, d.baux[bid], "detruit", offrir=False)
    T["offre"][b] = 0
    _sortir(p, d, b, "detruit")
    if parcelle >= 0: d.cadastre.t["bati"][parcelle] = max(0.0, d.cadastre.t["bati"][parcelle] - surf)
    if proprio is not None and nom != "abri_urgence" and type(proprio).__name__ in ("Menage", "Gouvernement", "Entreprise"):
        ouvrir_chantier(p, proprio, lid, nom, surf, RECONSTRUCTION, b, 1, parcelle, retour=retour,
                        aide=AIDE_SEISME if _est_menage(proprio) else 0.0)


def _reparer(p, d, b, nature, retour=-1):
    """Le proprietaire fait reparer ( regle ) : un menage recoit l aide publique a la reconstruction."""
    T = d.B
    if T["chantier"][b] >= 0: return
    proprio = proprietaire(p, b)
    nom = NOMS_MODELES[int(T["modele"][b])]
    if proprio is None or nom == "abri_urgence" or type(proprio).__name__ not in ("Menage", "Gouvernement", "Entreprise"): return
    ouvrir_chantier(p, proprio, d.lieux[int(T["lieu"][b])], nom, float(T["surface"][b]), nature, b, 1,
                    int(T["parcelle"][b]), retour=retour, aide=AIDE_SEISME if _est_menage(proprio) else 0.0)


def _nuit(p):
    """23 h 50, apres la reprise des morts par la population : les menages disparus dans la journee liberent leur
    logement et leurs biens passent a leurs heritiers ( sans attendre le matin )."""
    d = _dom(p); w = p.w
    n = len(w.menages)
    nv, _ = _vivants_par_menage(p)
    dis = p.col("menage", "dissous")[:n]
    log = p.col("menage", "im_logement")
    for i in np.nonzero((log[:n] >= 0) & ((dis == 1) | (nv == 0)))[0].tolist():
        _liberer(p, d, w.menages[i], "dissolution")
    _successions(p, d, nv, dis)


def _cloture(p, comptes):
    pass


# ================================================================== installation : le recensement du parc
def _lieux(p, d):
    w = p.w
    rng = p.hasard("immobilier_zones")
    ids = sorted(w.carte.lieux)
    d.lieux = ids; d.k_lieu = {l: k for k, l in enumerate(ids)}
    n = len(ids)
    d.prix_m2 = np.zeros(n); d.loyer_m2 = np.zeros(n); d.zone_m2 = np.zeros(n)
    u = rng.random(n)
    for k, lid in enumerate(ids):
        l = w.carte.lieux[lid]
        t = l.type if l.type in HABITABLES else "site"
        f = 1.0 + DISPERSION_LIEU * (2 * u[k] - 1)
        d.type_lieu.append(t); d.zone_de.append(l.marche.id if l.marche is not None else lid); d.ile_de.append(l.ile)
        d.prix_m2[k] = PRIX_M2_EUROS[t] * f / EUROS
        d.loyer_m2[k] = LOYER_M2_EUROS[t] * f / EUROS
        d.zone_m2[k] = PART_VALEUR_ZONE * d.prix_m2[k]


def _tirer_annee(rng):
    poids = np.array([x[2] for x in PERIODES]); poids = poids / poids.sum()
    i = int(rng.choice(len(PERIODES), p=poids))
    a, b_, _ = PERIODES[i]
    return int(rng.integers(a, b_ + 1))


def _tirer_surface(rng, modele, n):
    m, s = SURFACE[modele]
    x = float(rng.lognormal(math.log(m) - s * s / 2, s))
    return float(np.clip(max(x, surface_min(n + 1)), SURFACE_BORNES[0], SURFACE_BORNES[1]))


def _recensement(p, d, rng):
    """Le jour de l installation : chaque menage habite recoit un logement. Proprietaires : les menages les plus enclins
    ( age du chef, classe, village, et du hasard ) jusqu a 73,5 % des personnes ; les autres louent a un menage
    bailleur de leur lieu, a un loyer de marche au jour de leur bail ( signe dans les trois dernieres annees ). Plus
    8 % de logements vides offerts, les parcelles, les batiments publics, les ateliers et les commerces."""
    w = p.w; T = d.B; ca = d.cadastre
    n = len(w.menages)
    dis = p.col("menage", "dissous")
    nv, _ = _vivants_par_menage(p)
    habites = [mg for mg in w.menages if not dis[mg.id] and nv[mg.id] > 0]
    for mg in habites: _choisir_chef(p, mg)
    H = w.habitants
    score = {}
    for mg in habites:
        chef = H[int(p.col("menage", "im_chef")[mg.id])]
        k = d.k_lieu[mg.domicile.id]
        score[mg.id] = ((chef.age - 18) / 60.0 + {"aisee": 0.5, "moyenne": 0.2}.get(chef.classe, 0.0)
                        + (0.25 if d.type_lieu[k] == "village" else 0.0) + 0.6 * float(rng.random()))
    total = sum(int(nv[mg.id]) for mg in habites)
    proprios, cumul = set(), 0
    for mg in sorted(habites, key=lambda m: (-score[m.id], m.id)):
        if cumul >= PART_PROPRIETAIRES * total: break
        proprios.add(mg.id); cumul += int(nv[mg.id])
    # les bailleurs de chaque lieu ( poids par classe )
    bailleurs = {}
    for mg in habites:
        if mg.id not in proprios: continue
        chef = H[int(p.col("menage", "im_chef")[mg.id])]
        bailleurs.setdefault(d.k_lieu[mg.domicile.id], []).append((mg, POIDS_BAILLEUR.get(chef.classe, 1.0)))
    zone_bailleurs = {}
    for k, lst in bailleurs.items(): zone_bailleurs.setdefault(d.zone_de[k], []).extend(lst)
    def tirer_bailleur(k, sauf):
        lst = [x for x in bailleurs.get(k, []) if x[0] is not sauf] or [x for x in zone_bailleurs.get(d.zone_de[k], []) if x[0] is not sauf]
        if not lst: return w.gouv
        pw = np.array([x[1] for x in lst]); pw = pw / pw.sum()
        return lst[int(rng.choice(len(lst), p=pw))][0]
    immeubles = {}       # lieu -> ( parcelle, logements deja dedans )
    def parcelle_pour(k, modele, surface, proprio):
        typ = d.type_lieu[k]
        if modele == "maison":
            return ca.ajouter(k, CONSTRUCTIBLE, max(PARCELLE_MIN_M2[typ], surface / COS[typ]), COS[typ], proprio, surface)
        cur = immeubles.get(k)
        if cur is None or cur[1] >= TAILLE_IMMEUBLE:
            i = ca.ajouter(k, CONSTRUCTIBLE, max(PARCELLE_MIN_M2[typ], TAILLE_IMMEUBLE * SURFACE["appartement"][0] / COS[typ]),
                           COS[typ], None, 0.0)
            cur = immeubles[k] = [i, 0]
        cur[1] += 1; ca.t["bati"][cur[0]] += surface
        return cur[0]
    an = annee(p)
    for mg in habites:
        k = d.k_lieu[mg.domicile.id]
        typ = d.type_lieu[k]
        nvm = int(nv[mg.id])
        modele = "maison" if rng.random() < P_MAISON[typ] else "appartement"
        s = _tirer_surface(rng, modele, nvm)
        a = _tirer_annee(rng)
        if mg.id in proprios:
            b = _nouveau(p, d, modele, mg, mg.domicile.id, s, a, "initial", 0)
            T["parcelle"][b] = parcelle_pour(k, modele, s, mg)
            _occuper(p, d, mg, b, PROPRIETAIRE)
            continue
        loyer_m2 = d.loyer_m2[k] * facteur_age(an - a)
        s_aff = EFFORT_RECENSEMENT * revenu_mensuel(p, mg) / max(EPS, loyer_m2)
        s = float(np.clip(max(min(s, s_aff), surface_min(nvm)), SURFACE_BORNES[0], SURFACE_BORNES[1]))
        bailleur = tirer_bailleur(k, mg)
        b = _nouveau(p, d, modele, bailleur, mg.domicile.id, s, a, "initial", 0)
        T["parcelle"][b] = parcelle_pour(k, modele, s, bailleur)
        age_bail = int(rng.integers(0, DUREE_BAIL_J))
        ref = loyer_reference(p, b)
        loyer = round(max(1.0, ref * (1.0 + CROISSANCE_LOYERS_AN) ** (-age_bail / JOURS_AN)), 2)
        bail = Bail(d.prochain_bail, b, mg, loyer, p.jour - age_bail, p.jour - age_bail + DUREE_BAIL_J)
        bail.garant = bailleur
        d.prochain_bail += 1; d.baux[bail.id] = bail
        T["bail"][b] = bail.id; T["prix"][b] = loyer
        _occuper(p, d, mg, b, LOCATAIRE)
        prochain = p.jour + (bail.debut_j - p.jour) % MOIS_J
        p.poser(max(0, _pas_a(prochain, 9.0) - w.pas), "immobilier_terme", bail.id, (prochain,))
        p.poser(max(0, (bail.fin_j - p.jour) * C.PAS_PAR_JOUR), "immobilier_fin_bail", bail.id, (bail.fin_j,))
    # les logements vides offerts
    par_lieu = {}
    for mg in habites: par_lieu[d.k_lieu[mg.domicile.id]] = par_lieu.get(d.k_lieu[mg.domicile.id], 0) + 1
    for k in sorted(par_lieu):
        typ = d.type_lieu[k]
        nvac = int(round(TAUX_VACANTS * par_lieu[k] + rng.random() - 0.5))
        for _ in range(max(0, nvac)):
            modele = "maison" if rng.random() < P_MAISON[typ] else "appartement"
            s = _tirer_surface(rng, modele, int(rng.integers(1, 5)))
            bailleur = tirer_bailleur(k, None)
            b = _nouveau(p, d, modele, bailleur, d.lieux[k], s, _tirer_annee(rng), "initial", 0)
            T["parcelle"][b] = parcelle_pour(k, modele, s, bailleur)
            T["vacant_j"][b] = p.jour - int(rng.integers(0, 60))
            _offrir(p, d, b)
            T["vacant_j"][b] = p.jour - int(rng.integers(0, 60))
    # les terrains a batir libres
    for k in sorted(par_lieu):
        typ = d.type_lieu[k]
        proprios_k = [x[0] for x in bailleurs.get(k, [])]
        for _ in range(max(1, int(round(PARCELLES_LIBRES * par_lieu[k])))):
            prop = w.gouv if not proprios_k or rng.random() < 0.3 else proprios_k[int(rng.integers(0, len(proprios_k)))]
            ca.ajouter(k, CONSTRUCTIBLE, 2 * PARCELLE_MIN_M2[typ], COS[typ], prop, 0.0)
    # les parcelles agricoles du territoire
    Tr = p.domaine("territoire")
    for lid, ha in zip(Tr.parcelles.lieu_id, Tr.parcelles.surface_ha.tolist()):
        if lid in d.k_lieu:
            ca.ajouter(d.k_lieu[lid], AGRICOLE, ha * 1e4, 0.0, w.entreprises.get(lid), 0.0)
    _batiments_publics(p, d, rng)


def _batiments_publics(p, d, rng):
    w = p.w; parc = p.socle.parc; g = w.gouv
    an = annee(p)
    pop_zone, enfants_zone, agents_zone = {}, {}, {}
    for h in w.habitants:
        if not h.vivant or h.domicile is None: continue
        z = h.domicile.marche.id
        pop_zone[z] = pop_zone.get(z, 0) + 1
        if h.role == "enfant": enfants_zone[z] = enfants_zone.get(z, 0) + 1
        if h.role in ("ministre", "chef_gouvernement", "policier", "enseignant", "infirmier", "medecin", "officier"):
            agents_zone[z] = agents_zone.get(z, 0) + 1
    for cap in sorted(w.marches):
        pz = pop_zone.get(cap, 0)
        lits = max(2, int(round(LITS_PAR_HABITANT * pz)))
        _nouveau(p, d, "hopital", g, cap, lits * M2_PAR_LIT, _tirer_annee(rng), "initial", 0)
        _nouveau(p, d, "ecole", g, cap, max(300.0, M2_PAR_ELEVE * enfants_zone.get(cap, 0)), _tirer_annee(rng), "initial", 0)
        _nouveau(p, d, "bureau_public", g, cap, max(200.0, M2_PAR_AGENT * agents_zone.get(cap, 0)), _tirer_annee(rng),
                 "initial", 0)
        n = max(1, int(round(pz / HABITANTS_PAR_COMMERCE)))
        parc.creer_cohorte(d.modele_parc["commerce"], w.marches[cap], cap, n, "initial", 0.4)
        d.nes["commerce"]["initial"] += n
        nab = max(1, int(round(ABRIS_PAR_MENAGE * sum(1 for mg in w.menages if mg.domicile is not None
                                                       and mg.domicile.marche.id == cap))))
        parc.creer_cohorte(d.modele_parc["abri_urgence"], g, cap, nab, "initial", 0.0)
        d.nes["abri_urgence"]["initial"] += nab
    for base in sorted(w.garnisons):
        soldats = sum(1 for h in w.habitants if h.vivant and h.travail is not None and h.travail.id == base)
        _nouveau(p, d, "caserne", g, base, max(200.0, M2_PAR_SOLDAT * soldats), _tirer_annee(rng), "initial", 0)
    for eid in sorted(w.entreprises):
        e = w.entreprises[eid]
        _nouveau(p, d, "atelier", e, e.lieu.id, SURFACE_ATELIER.get(e.type, 400.0), _tirer_annee(rng), "initial", 0)


def installer(p):
    w = p.w; L = p.socle.livre; parc = p.socle.parc
    d = Immobilier()
    p.domaines["immobilier"] = d
    for k, (nom, usage, surf, arma, kg, vie, src) in enumerate(MODELES):
        m = parc.declarer_modele(nom, "batiment", round(surf * cout_m2() * FACTEUR_COUT.get(nom, 1.0), 2),
                                 surf * kg, vie * JOURS_AN * 24.0, arma, None, src + " ; a calibrer")
        d.modele_parc[nom] = m; d.idx_modele[nom] = k
    for m, nat in (("loyer", "achat"), ("depot_garantie", "financier"), ("restitution_depot", "financier"),
                   ("vente_logement", "achat"), ("droits_mutation", "impot_production"), ("frais_transaction", "achat"),
                   ("vente_terrain", "achat"), ("travaux", "achat"), ("second_oeuvre", "achat"),
                   ("aide_reconstruction", "transfert_capital"), ("achat_abri", "achat"),
                   ("dividende_btp", "revenu_propriete"), ("import_materiaux", "achat")):
        L.declarer_motif(m, nat, "immobilier")
    J = p.socle.journal
    for t, champs in (("expulsion", ("bail", "menage", "arrieres", "motif")),
                      ("chantier_ouvert", ("chantier", "nature", "modele", "lieu", "devis")),
                      ("chantier_termine", ("chantier", "nature", "jours", "devis")),
                      ("seisme_dommages", ("lieu", "intensite", "touches", "inhabitables", "detruits")),
                      ("abri_importe", ("lieu", "surface"))):
        J.declarer(t, "immobilier", "individuel", champs)
    for t in ("bail_signe", "bail_renouvele", "depart_fin_bail", "loyer_paye", "loyer_impaye", "vente_logement",
              "enfia_percue", "enfia_reportee", "relogement_urgence", "heritage_logement", "candidat_refuse",
              "permis_depose", "emmenagement_proprietaire"):
        J.declarer(t, "immobilier", "compte")
    cm = p.colonnes["menage"]
    for nom, dt, defaut in (("im_logement", np.int32, -1), ("im_statut", np.int8, SANS), ("im_chef", np.int32, -1),
                            ("im_possede", np.int32, 0)):
        cm.ajouter(nom, dt, defaut)
    cm.assurer(len(w.menages))
    _lieux(p, d)
    reg = p.socle.registre
    reg.inscrire("entreprises_btp", "entreprises", _membres_btp, "caisse", "stock", "EntrepriseBTP")
    reg.inscrire("chantiers", "entreprises", _membres_chantiers, None, "stock", None)
    for cap in sorted(w.marches):
        lieu = w.carte.lieux[cap]
        patrons = sorted((h for h in w.habitants if h.vivant and h.role == "patron" and h.domicile is not None
                          and h.domicile.marche.id == cap), key=lambda h: h.id)
        riches = sorted((mg for mg in w.menages if mg.domicile is not None and mg.domicile.marche.id == cap
                         and _n_vivants(mg) > 0), key=lambda m: (-m.caisse, m.id))
        prop = patrons[0].menage if patrons else (riches[0] if riches else None)
        btp = EntrepriseBTP(lieu, prop)
        d.btp.append(btp); d.btp_de_zone[cap] = btp
        BQ.ouvrir_compte(p, btp)
    p.echeance("immobilier_terme", _terme)
    p.echeance("immobilier_fin_bail", _fin_de_bail)
    _recensement(p, d, p.hasard("immobilier_recensement"))
    d.decideur = p.decideur(POINT_LOYER)
    p.routine(10 / 60, 20, "immobilier", _seismes)
    p.routine(6.5, 60, "immobilier", _matin)
    p.routine(9.0, 60, "immobilier", _marche)
    p.routine(16 + 10 / 60, 60, "immobilier", _materiaux)
    p.routine(17 + 50 / 60, 20, "immobilier", _travail)
    p.routine(20 + 10 / 60, 60, "immobilier", _soir)
    p.routine(23 + 50 / 60, 95, "immobilier", _nuit)
    p.cloture("immobilier", _cloture)
    return d


# ================================================================== controles ( pour les portes )
def anomalies_logement(p):
    """Les manquements : un menage habite sans logement ou dont le lien est rompu, un logement surpeuple, un logement
    dont l occupant est dissous, deux menages sur un logement."""
    d = _dom(p); w = p.w; T = d.B
    n = len(w.menages)
    nv, _ = _vivants_par_menage(p)
    dis = p.col("menage", "dissous")[:n]; log = p.col("menage", "im_logement")[:n]
    out = []
    for i in np.nonzero((nv > 0) & (dis == 0))[0].tolist():
        b = int(log[i])
        if b < 0: out.append(("sans_logement", i)); continue
        if T["vivant"][b] != 1 or T["occupant"][b] != i: out.append(("lien_rompu", i, b)); continue
        if nv[i] > capacite(T["surface"][b]): out.append(("surpeuple", b, int(nv[i]), capacite(T["surface"][b])))
    for b in np.nonzero((T["vivant"][:T.n] == 1) & (T["occupant"][:T.n] >= 0))[0].tolist():
        o = int(T["occupant"][b])
        if log[o] != b: out.append(("occupant_ailleurs", b, o))
        elif dis[o] or nv[o] == 0: out.append(("occupant_disparu", b, o))
    return out


def part_proprietaires(p):
    """( part des personnes, part des menages ) logees chez leur menage proprietaire."""
    w = p.w; n = len(w.menages)
    nv, _ = _vivants_par_menage(p)
    dis = p.col("menage", "dissous")[:n]; st = p.col("menage", "im_statut")[:n]
    h = (nv > 0) & (dis == 0)
    pr = h & (st == PROPRIETAIRE)
    return float(nv[pr].sum() / max(1, nv[h].sum())), float(pr.sum() / max(1, h.sum()))


def audit_batiments(p):
    """L audit des objets du domaine : comptes du Parc = naissances et sorties faites par le domaine ( modele par
    modele, source par source ) ; individus du Parc = individus de la table ; Parc.verifier nul."""
    d = _dom(p); parc = p.socle.parc; T = d.B
    mes = {d.modele_parc[n].id: n for n in NOMS_MODELES}
    vus = {o.id for o in parc.objets.values() if o.modele in mes}
    table = {int(T["oid"][b]) for b in np.nonzero(T["vivant"][:T.n] == 1)[0].tolist()}
    ecarts = {}
    for mid, nom in mes.items():
        k = parc.comptes[mid]
        for s in O.SOURCES:
            if k[s] != d.nes[nom][s]: ecarts[(nom, s)] = k[s] - d.nes[nom][s]
        for s in O.PUITS:
            if k[s] != d.sortis[nom][s]: ecarts[(nom, s)] = k[s] - d.sortis[nom][s]
    ver = {nom: v for nom, v in parc.verifier().items() if nom in NOMS_MODELES and v != 0}
    return {"orphelins": sorted(vus - table), "fantomes": sorted(table - vus), "sources": ecarts, "parc": ver}


def audit_propre(a):
    return not a["orphelins"] and not a["fantomes"] and not a["sources"] and not a["parc"]


# ================================================================== API pour les autres domaines
def logement_de(p, menage):
    """Le rang du logement du menage ( -1 ), et son statut ( 0 sans, 1 proprietaire, 2 locataire, 3 abri )."""
    return int(p.col("menage", "im_logement")[menage.id]), int(p.col("menage", "im_statut")[menage.id])


def surface_logement(p, menage):
    """Domaine 12 ( taxe locale ) : la surface reelle du logement du menage, en m2 ; 0 sans logement."""
    b = int(p.col("menage", "im_logement")[menage.id])
    return float(_dom(p).B["surface"][b]) if b >= 0 else 0.0


def loyer_mensuel(p, menage):
    """Domaine 3 ( budget logement ) : le loyer mensuel du bail du menage, 0 s il n est pas locataire."""
    d = _dom(p); b = int(p.col("menage", "im_logement")[menage.id])
    if b < 0: return 0.0
    bid = int(d.B["bail"][b])
    return d.baux[bid].loyer if bid >= 0 and bid in d.baux and d.baux[bid].locataire is menage else 0.0


def loyers_du_jour(p):
    """Domaine 3 : { menage : loyer paye aujourd hui } se lit dans les comptes du grand livre ( motif loyer ) ; ici,
    l equivalent journalier de chaque bail ( loyer / 30 ), pour retirer la part servie du logement de la demande en
    attente."""
    d = _dom(p)
    return {b.locataire.id: b.loyer / MOIS_J for b in d.baux.values()}


def batiments(p, modele=None, lieu=None, proprietaire_=None):
    """Les rangs des batiments individuels vivants ( filtres par modele, lieu, proprietaire ) : domaines 17 ( hopital ),
    19 ( ecole ), 25 ( caserne ), 18 et 20 ( tous )."""
    d = _dom(p); T = d.B; n = T.n
    m = np.ones(n, bool) & (T["vivant"][:n] == 1)
    if modele is not None: m &= T["modele"][:n] == d.idx_modele[modele]
    if lieu is not None: m &= T["lieu"][:n] == d.k_lieu[lieu]
    idx = np.nonzero(m)[0].tolist()
    if proprietaire_ is not None: idx = [b for b in idx if b in d.par_proprio.get(cle(proprietaire_), ())]
    return idx


def fiche(p, b):
    """Ce qu un autre domaine lit d un batiment : modele, lieu, surface, annee, dommage, degats, habitable, occupant,
    proprietaire, valeur, valeur de reconstruction, classname Arma."""
    d = _dom(p); T = d.B
    nom = NOMS_MODELES[int(T["modele"][b])]
    return {"modele": nom, "lieu": d.lieux[int(T["lieu"][b])], "surface": float(T["surface"][b]),
            "annee": int(T["annee"][b]), "dommage": int(T["dommage"][b]), "degats": float(T["degats"][b]),
            "habitable": bool(_habitable(T, b)), "occupant": int(T["occupant"][b]), "proprietaire": proprietaire(p, b),
            "valeur": valeur(p, b), "valeur_reconstruction": valeur_reconstruction(p, b),
            "arma": d.modele_parc[nom].arma}


def lits(p, b):
    """Domaines 17 et 25 : les lits d un hopital ( 100 m2 bruts par lit ) ou d une caserne ( 20 m2 par soldat ), 0 si
    le batiment est inhabitable."""
    d = _dom(p); T = d.B
    nom = NOMS_MODELES[int(T["modele"][b])]
    if not _habitable(T, b) or T["vivant"][b] != 1: return 0
    return int(T["surface"][b] // {"hopital": M2_PAR_LIT, "caserne": M2_PAR_SOLDAT}.get(nom, math.inf))


def places_ecole(p, b):
    """Domaine 19 : les places d une ecole ( 8 m2 par eleve ), 0 si elle est inhabitable."""
    d = _dom(p); T = d.B
    if not _habitable(T, b) or T["vivant"][b] != 1: return 0
    return int(T["surface"][b] // M2_PAR_ELEVE)


def construire(p, maitre, lieu_id, modele, surface, unites=1, parcelle=-1, vendre_=False):
    """Domaines 17, 19, 25 ( et tous ) : un batiment neuf ; rend le Chantier ou None."""
    return ouvrir_chantier(p, maitre, lieu_id, modele, surface, NEUF, -1, unites, parcelle, vendre_)


def endommager(p, b, dommage, cause="incendie"):
    """Domaine 18 ( incendie ), 27 ( combat ) : un batiment passe a l etat de dommage EMS-98 `dommage` ( 1 a 5 ) :
    ses occupants sont reloges, il est repare ( D2, D3 ) ou detruit ( D4, D5 : puits detruit ) et reconstruit.
    Rend le cout de reparation estime ( drachmes )."""
    d = _dom(p); T = d.B
    if T["vivant"][b] != 1 or not 1 <= dommage <= 5 or dommage <= T["dommage"][b]: return 0.0
    T["dommage"][b] = dommage; T["degats"][b] = max(T["degats"][b], RATIO_DOMMAGE[dommage])
    cout = round(RATIO_DOMMAGE[dommage] * valeur_reconstruction(p, b), 2)
    d.sinistres.append((p.jour, b, dommage, cout))
    if dommage >= DS_DETRUIT: _detruire_seisme(p, d, b)
    elif dommage >= DS_INHABITABLE: _evacuer(p, d, b)
    elif dommage >= 2: _reparer(p, d, b, RENOVATION)
    offres = _offres(d, 1); ch = _chercheurs_par_lieu(p, d)
    _decider_loyers(p, d, offres, ch); _apparier(p, d, offres, ch); _loger_en_urgence(p, d)
    return cout


def occupants(p, b):
    """Domaine 18 : les habitants vivants d un logement ( a evacuer )."""
    d = _dom(p); occ = int(d.B["occupant"][b])
    return [h for h in p.w.menages[occ].membres if h.vivant] if occ >= 0 else []


def sinistres(p, depuis_j=0):
    """Domaine 20 ( assurance habitation ) : ( jour, rang, dommage, cout de reparation ) depuis `depuis_j`."""
    return [s for s in _dom(p).sinistres if s[0] >= depuis_j]


def baux_en_impaye(p):
    """Domaine 21 : les baux avec des loyers impayes : { bail : ( menage, bailleur, arrieres, termes impayes, litige ) }."""
    d = _dom(p); K = p.socle.creances
    out = {}
    for bid in sorted(d.baux):
        bail = d.baux[bid]
        act = [c for c in bail.impayes if K.actives.get(c.id) is c]
        if act: out[bid] = (bail.locataire, proprietaire(p, bail.b), sum(c.montant for c in act), len(act), bail.litige_j)
    return out


def rendre_la_justice(p):
    """Domaine 21 : prend la main sur les litiges de bail ( le domaine n expulse plus seul ; appeler `expulser` )."""
    _dom(p).justice_externe = True


def forcer_fins_de_bail(p, part, jours, rng):
    """Scenario ( portes, politique ) : une part des baux arrive a terme dans les `jours` jours ( mobilite forcee )."""
    d = _dom(p)
    for bid in sorted(d.baux):
        if rng.random() >= part: continue
        bail = d.baux[bid]
        bail.fin_j = p.jour + int(rng.integers(0, max(1, jours)))
        p.poser(max(0, _pas_a(bail.fin_j, 7.0) - p.w.pas), "immobilier_fin_bail", bid, (bail.fin_j,))
