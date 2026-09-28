"""DOMAINE 21 - JUSTICE, POLICE, CRIMINALITE, DROIT CIVIL.

FICHE
1. Classes. Les lois : TYPES ( chaque infraction : taux enregistre grec, part declaree, auteur connu de la victime,
   gravite, preuve de depart et sa demi-vie, rendement d une journee d enquete, flagrant delit, famille, crime ou delit,
   elucidation grecque ), PEINES ( fourchettes du code penal grec, amende, detention provisoire ), FILES ( les files des
   tribunaux : flux de fond, delai cible ). Les detenteurs : ServiceJustice ( le ministere de la Justice : une caisse,
   famille `justice`, secteur administrations : traitements des juges, soldes des gardiens, vivres des detenus ),
   Prison ( une par ile : son batiment du domaine 13, ses places, son stock de vivres du socle, famille `prisons` ).
   L etat : Affaire ( une infraction enregistree : victime, auteur VRAI ( cache ), suspect designe, preuve, effort,
   butin, tort et restitution ), Dossier ( une affaire portee au tribunal : penale, bail, injonction de payer, appel,
   militaire ; sa date d audience fixee au depot, comme la " dikasimos " grecque ), Jugement ( verdict, peine, sursis,
   appel ), Detention ( un detenu : titre - ordonnance de detention provisoire ou jugement -, fin, ce qu il avait
   avant : menage, domicile, emploi ), Tribunal ( un par ile : ses juges, ses files en charge de travail fluide ),
   ContexteEnquete, Jour ( la population du jour, lue en colonnes a 0 h 30 ), Justice ( l etat du domaine ).
   Colonnes par habitant : ju_casier ( condamnations definitives ou non ), ju_detenu ( 0 libre, 1 provisoire, 2 peine ),
   ju_libere ( drapeau : deja sorti de prison ) et ju_libere_j ( jour de sortie ). ~ 8 octets par habitant : tous en
   ont besoin pour tirer les auteurs chaque nuit ( recidive, casier ) et pour la porte des detenus. Tables eparses :
   affaires, dossiers, jugements, detentions, titres executoires, corruptions cachees.
2. Invariants et ce que le domaine detient. DETENUS : tout habitant marque detenu a un titre valide - une ordonnance
   de detention provisoire non echue, ou un jugement de condamnation a la prison ferme a son nom - ; il est ABSENT au
   sens du moteur ( il ne mange pas chez lui, `population.ABSENT` ), sans emploi ( travail = -1 ), domicilie a la
   prison ; `audit` le verifie chaque fois qu on le demande. PEINES : toute amende, toute peine de prison executee a un
   jugement de condamnation ( ou une decision de la douane ) a son nom. EXPULSIONS : le domaine 13 n expulse plus seul
   ( `rendre_la_justice` ) ; chaque expulsion comptee par le 13 depuis l installation a son jugement. ARGENT : tout
   par le grand livre ; le domaine DETIENT la caisse du ministere ( dotation de l Etat, traitements, soldes, vivres ).
   Vols, pots-de-vin et restitutions ont un motif de nature `illegal` : comptes, jamais dans l assiette. Les amendes
   vont au Tresor par `ET.infliger_amende` ; le reste devient une creance de l Etat que le domaine 6 recouvre. BIENS :
   vivres achetes au marche = manges + stock des prisons, au pas pres ( `bilan_vivres` ). INTERETS : interets de
   retard SIMPLES ( pas d anatocisme, code civil art. 296 ), en creances de motif `interet_moratoire` ( civil ) ou
   `interet_retard_fiscal` ( Etat ), nature revenu_propriete ; un paiement va d abord aux interets ( art. 423 ).
3. Decision `enquete` ( chaque jour a 10 h, chaque enqueteur de la police judiciaire present, quand son lot de dossiers
   ouverts de sa zone lui offre au moins deux choix distincts ) : quel critere suit-il - la plus grave et la plus
   recente, la plus grave, la plus recente, la plus ancienne, la mieux prouvee. Traits : pour chacune des cinq affaires
   designees, sa gravite ( le code penal ), son age sur le delai de classement, sa preuve au dossier ( temoins, traces,
   ce que la police a recueilli et qui se degrade ) ; la taille du lot ; la charge de la zone. Jamais l auteur vrai.
   Note ( horizon 7 jours : une affaire se resout dans les jours qui suivent, pas le soir meme ) : pour l affaire
   choisie, 1 si elle est elucidee dans l horizon, plus la part du tort reparee a sa victime ( butin saisi et rendu,
   vehicule retrouve ) ; la moyenne sur les 7 jours. Regle : la plus grave et la plus recente. Temoin : la plus
   ancienne d abord. Pourquoi des criteres et pas des dossiers : lecon du domaine 6 ( des actions interchangeables ne
   portent pas la note ).
4. Evenements. Individuels : delit, arrestation, jugement, incarceration, liberation, corruption_decouverte,
   expulsion_judiciaire. Comptes : plainte, delit_non_declare, elucidation, classement, pot_de_vin, restitution,
   amende_penale, saisie_civile, interet_moratoire, interet_fiscal, audience, report_audience, appel,
   erreur_judiciaire, faillite_jugee, succession_contestee, repas_detenu, detenu_affame, decision_enquete,
   sanction_douane.
5. Liens. Etat ( 6 ) : `infliger_amende`, `creances_de_l_etat`, `_saisissable`, `assurer` avant chaque dotation ; lit
   ses controles fiscaux ( fraude penale au-dela du seuil ) et la part des policiers au controle fiscal ( le domaine
   prend les autres ). Immobilier ( 13 ) : `rendre_la_justice`, `expulser`, les litiges, `logement_de`, `valeur`,
   `disponible`, batiments ( tribunal : bureau_public ; prison : caserne ). Banques ( 2 ) : les prets radies ( creances
   `recouvrement_pret` ) passent en injonction de payer ; le taux directeur fait le taux legal. Economie ( 3 ) :
   `licencier` a l incarceration, registre des chomeurs a la sortie, les faillites jugees. Population ( 1 ) : `deceder`
   ( homicide ; mortalite des detenus, que le domaine 1 ne tire pas pour un absent ), `nouveau_menage` et
   `deplacer_membre` a la sortie, deces ( successions contestees ). Optionnels ( p.a ) : medecine ( 16 ) `blesser`
   ( violences, cause violence ) ; securite civile ( 18 ) `allumer( cause = "criminelle" )` ; transport ( 14 ) `vols`,
   `retrouver`, `impayes_circulation` ; exterieur ( 7 ) `contrebande` ( la verite ; seules les saisies deviennent des
   affaires ) ; travail ( 4 ) `rompre_contrat` et son statut. Paie et recoit : Etat -> ministere ( dotation_justice ),
   ministere -> menages ( traitement_magistrat, solde_gardien ), ministere -> marche ( achat_penitentiaire, TVA ),
   victime -> auteur ( vol ), auteur -> victime ( restitution_vol ), suspect -> policier ou juge ( pot_de_vin ),
   condamne -> Etat ( amende ), debiteurs -> creanciers ( saisies, interets ). Ne remplace aucune methode du moteur.
   API en fin de fichier pour les domaines 20, 22, 24, 27.
   LIMITES DU MOTEUR : aucun role juge ni gardien ( config.ROLES ) : ils sont recrutes parmi les adultes hors metiers
   publics et GARDENT leur metier du moteur ( comme les pompiers du domaine 18 ) ; il faudrait deux roles ( Younes ).
   Le moteur a ~ 40 policiers pour 1 000 habitants ( Grece ~ 5 ) : la police judiciaire est prise a
   ENQUETEURS_PAR_1000, le reste patrouille.
6. Portes : tests_d21_justice.py.
7. Arma. Tribunal : Land_Offices_01_V1_F ( bureau_public du 13 ) ; prison : Land_i_Barracks_V1_F ( caserne du 13 ),
   faute d une prison au jeu de base ; policiers : le corps du moteur ; arma_preuve = None partout.
8. Cout. 0 h 30 : une passe numpy sur les habitants ( poids des auteurs, deux familles ), Poisson par type, une passe
   par victime tiree ; 10 h : les policiers presents par zone ( index du moteur ), un point de decision par enqueteur ;
   11 h : les files ( une addition par file ) ; le reste touche les seuls detenus, dossiers, creances en justice.
   Installation : une passe numpy par tirage ( juges, gardiens, detenus ), lineaire. Mesure : test_cout."""
import math
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D, biens as BI
from . import pays as PAYS, d01_population as POP, d03_economie as ECO, d06_etat as ET
from . import d13_immobilier as IM, d02_banques as BQ, d07_exterieur as EXT, d14_transport as TRA
from . import d16_medecine as MED, d18_securite_civile as SC, d04_travail as TRV

EUROS = PAYS.EUROS_PAR_DRACHME
JOURS_AN = 365.0
EPS = 1e-9
PAS_J = C.PAS_PAR_JOUR
MAISON_P = PO.CODE_POSTE["maison"]
TRAVAIL_P = PO.CODE_POSTE["travail"]
R_ENFANT, R_RETRAITE = PO.CODE_ROLE["enfant"], PO.CODE_ROLE["retraite"]
PUBLICS = tuple(PO.CODE_ROLE[r] for r in ("chef_gouvernement", "ministre", "officier", "soldat", "policier", "medecin",
                                          "infirmier", "enseignant") if r in PO.CODE_ROLE)

# ================================================================== les infractions ( Grece prise pour modele )
ACQ, VIO, AUT = 0, 1, 2            # familles : acquisitive, violente, autre ( lue dans les autres domaines )
# nom : ( enregistrees pour 100 000 habitants et par an, part declaree, auteur connu de la victime, gravite, preuve de
#         depart, demi-vie... tau de la preuve en jours, q : chance d elucider par journee d enquete a preuve 1,
#         flagrant delit a la densite de patrouille de l installation, famille, crime ( felonie ), elucidation grecque )
# Enregistrees : Eurostat crim_off_cat et police hellenique, Grece 2019 - vols ( hors vehicules et cambriolages )
# ~ 380, cambriolages de residences ~ 205, vols avec violence ~ 44 pour 100 000 ; homicides volontaires ~ 0,95
# ( ONUDC ) ; violences ~ 80 et incendies criminels ~ 4 : a calibrer ; tout a verifier. Parts declarees : ordres de
# grandeur des enquetes de victimation ( ICVS ) : a calibrer. Elucidations : ordres de grandeur de la police
# hellenique, a verifier. Les autres types viennent d autres domaines ( vols de vehicules du 14, fraude du 6,
# contrebande du 7, corruption decouverte ici, fraude a l assurance du 20, infractions militaires du 27 ).
TYPES = (
    ("vol_simple",        380.0, 0.35, 0.05, 0.15, 0.30,    4.0, 0.08, 0.04, ACQ, False, 0.15),
    ("cambriolage",       205.0, 0.80, 0.02, 0.30, 0.35,    6.0, 0.06, 0.02, ACQ, True,  0.12),
    ("vol_violence",       44.0, 0.60, 0.10, 0.55, 0.50,    8.0, 0.10, 0.05, ACQ, True,  0.35),
    ("violences",          80.0, 0.45, 0.60, 0.40, 0.60,   10.0, 0.20, 0.10, VIO, False, 0.70),
    ("homicide",           0.95, 1.00, 0.50, 1.00, 0.85,   30.0, 0.35, 0.10, VIO, True,  0.85),
    ("incendie_criminel",   4.0, 0.90, 0.05, 0.60, 0.25,    5.0, 0.04, 0.01, VIO, True,  0.10),
    ("vol_vehicule",        0.0, 1.00, 0.00, 0.35, 0.30,    7.0, 0.05, 0.01, ACQ, False, 0.10),
    ("fraude_fiscale",      0.0, 1.00, 1.00, 0.45, 0.90, 3650.0, 0.50, 0.00, AUT, True,  1.00),
    ("contrebande",         0.0, 1.00, 1.00, 0.35, 1.00, 3650.0, 0.50, 1.00, AUT, False, 1.00),
    ("corruption",          0.0, 1.00, 1.00, 0.60, 0.70,   60.0, 0.25, 0.00, AUT, True,  0.80),
    ("fraude_assurance",    0.0, 1.00, 1.00, 0.35, 0.60,   30.0, 0.08, 0.00, ACQ, False, 0.70),
    ("militaire",           0.0, 1.00, 1.00, 0.50, 0.80,   60.0, 0.25, 0.00, AUT, False, 1.00),
)
NOMS = tuple(t[0] for t in TYPES)
IDX = {n: k for k, n in enumerate(NOMS)}
NT = len(NOMS)
ENREGISTRES = np.array([t[1] for t in TYPES])
DECLAREE = np.array([t[2] for t in TYPES])
AUTEUR_CONNU = np.array([t[3] for t in TYPES])
GRAVITE = np.array([t[4] for t in TYPES])
PREUVE0 = np.array([t[5] for t in TYPES])
TAU = np.array([t[6] for t in TYPES])
Q_ENQUETE = np.array([t[7] for t in TYPES])
FLAGRANT = np.array([t[8] for t in TYPES])
FAMILLE = np.array([t[9] for t in TYPES])
FELONIE = np.array([t[10] for t in TYPES])
ELUC_GRECE = np.array([t[11] for t in TYPES])
VRAIS = ENREGISTRES / DECLAREE      # les infractions commises ( le chiffre noir compris ), pour 100 000 et par an
TIRES = ("vol_simple", "cambriolage", "vol_violence", "violences", "homicide", "incendie_criminel")   # tirees ici
BANDES = {"vol_simple": (250.0, 520.0), "cambriolage": (140.0, 280.0), "vol_violence": (28.0, 62.0),
          "violences": (50.0, 115.0)}   # enregistrees pour 100 000 et par an : la bande de la porte ( ecrite avant )
# le butin : ( part de la caisse de la victime, plafond en euros ) ( a calibrer : ~ 150 euros un vol a la tire, ~ 1 500
# un cambriolage de residence, en ordres de grandeur d assurance )
BUTIN = {"vol_simple": (0.05, 150.0), "cambriolage": (0.15, 1500.0), "vol_violence": (0.05, 200.0)}
PART_DEGATS_INCENDIE = 0.2        # tort d un incendie criminel, en part de la valeur du logement ( a calibrer )
FAMILIAL = {"violences": 0.35, "homicide": 0.40}   # part des victimes du meme menage ( violences conjugales, a calibrer )
ISS_VIOLENCES = ((1, 0.60), (4, 0.25), (9, 0.10), (16, 0.05))   # a calibrer
P_BLESSE_VOL_VIOLENCE = 0.3

# Les auteurs : le poids d un habitant selon son age ( hommes ; femmes x 0,2 : ~ 5 % des detenus grecs sont des femmes,
# ~ 15 a 20 % des mis en cause ; a calibrer ) et ses conditions. Elasticites ( a calibrer ; Raphael et Winter-Ebmer 2001 :
# le chomage pese sur les vols ; la faim est le levier du controle positif ) : faim ( soirs sans repas du menage sur 7 ),
# pauvrete ( caisse par personne sous la mediane ), chomage, recidive ( sorti de prison depuis moins de 2 ans ), casier.
AGES_AUTEUR = (15.0, 25.0, 35.0, 45.0, 55.0, 65.0)
POIDS_AGE = (4.0, 3.0, 1.8, 1.0, 0.5, 0.15)
FACTEUR_FEMMES = 0.2
ELASTICITES = {ACQ: (2.0, 1.0, 0.5, 4.0, 1.0), VIO: (0.5, 0.5, 0.5, 3.0, 1.0)}
RECIDIVE_J = 730
# La dissuasion ( Becker ) : le risque d etre pris que la zone a vu, lisse ; elasticite 0,4 ( Chalfin et McCrary 2017 :
# 0,3 a 0,7 ; a calibrer ), bornee a un facteur 2 dans chaque sens.
ELAST_DISSUASION = 0.4
PRIOR_DISSUASION = 20.0
BORNES_DISSUASION = (0.5, 2.0)
OUBLI_DISSUASION = 0.99           # par jour : la memoire du risque vu a une demi-vie de ~ 70 jours
ELUC_REF = {ACQ: 0.15, VIO: 0.65}
BITS7 = np.array([bin(i).count("1") for i in range(128)], np.float64)   # faim7 du domaine 1 : un bit par soir

# ================================================================== la police
ENQUETEURS_PAR_1000 = 0.8         # police judiciaire ( Asfaleia ) : ~ 15 % de ~ 5,3 policiers pour 1 000 ( a calibrer )
PRESENCE = 1.0 / 3.0              # part de service un jour donne ( gardes et repos, a calibrer )
LOT = 4                           # dossiers ouverts qu un enqueteur regarde le matin
CLASSEMENT_J = 60                 # une affaire sans suite apres deux mois est classee ( contre inconnu, a calibrer )
FRAICHEUR_J = 15.0                # l echelle de la regle : la plus grave ET la plus recente
P_ERREUR_ID = 0.04                # un suspect designe a tort ( a calibrer : 1 a 5 % des condamnations erronees )
P_SAISIE_BUTIN = 0.5              # part du butin retrouvee chez l auteur arrete ( a calibrer )
HORIZON_ENQUETE = 7
CRITERES = ("grave_recente", "plus_grave", "plus_recente", "plus_ancienne", "mieux_prouvee")
GRAVE_RECENTE, PLUS_GRAVE, PLUS_RECENTE, PLUS_ANCIENNE, MIEUX_PROUVEE = range(5)
# La corruption ( TI : Grece ~ 49/100 ; Eurobarometre 2019 : une petite part des Grecs dit avoir du payer ; a calibrer )
P_OFFRE_POT = 0.08                # un suspect qui en a les moyens offre au policier qui l arrete
P_ACCEPTE_POT = 0.25              # le policier accepte
P_OFFRE_JUGE = 0.02; P_ACCEPTE_JUGE = 0.10
P_ENTERRE = 0.9                   # l affaire est enterree
PART_POT = 0.2; POT_MAX_EUROS = 5000.0; POT_MIN_EUROS = 300.0
P_DETECTION_J = 1.0 / 730.0       # une corruption cachee est decouverte ( inspection, plainte ) : ~ 40 % en un an
MULT_AMENDE_DOUANE = 2.0          # loi 2960/2001 art. 150 : un multiple des droits elude ( 2 a 10, a calibrer )
SEUIL_FRAUDE_PENALE_EUROS = 100000.0   # loi 4174/2013 art. 66 : impot elude au-dela duquel la fraude est un crime ( a verifier )

# ================================================================== les tribunaux
# file : ( affaires de fond pour 100 habitants et par an, delai cible en jours, report moyen en jours ). Sources :
# CEPEJ ( donnees 2018 ) Grece, premier degre, civil et commercial contentieux ~ 559 jours ( a verifier ) ; les autres
# a calibrer ( penal : 1 a 3 ans ; baux : 4 a 12 mois ; injonction de payer : 1 a 3 mois ; appel : 1 a 2 ans ; les
# detenus sont juges avant la fin de la detention provisoire : Constitution art. 6 al. 4 ).
FILES = {"correctionnel": (2.0, 365.0, 90.0), "criminel": (0.05, 540.0, 120.0), "criminel_detenu": (0.01, 240.0, 30.0),
         "civil": (1.7, 559.0, 150.0), "baux": (0.15, 180.0, 60.0), "injonction": (0.6, 60.0, 0.0),
         "appel": (0.4, 600.0, 120.0)}
NOMS_FILES = tuple(FILES)
BANDES_DELAIS = {"correctionnel": (180.0, 1095.0), "criminel": (365.0, 1095.0), "criminel_detenu": (120.0, 548.0),
                 "civil": (400.0, 750.0), "baux": (90.0, 365.0), "injonction": (20.0, 120.0), "appel": (365.0, 900.0)}
P_REPORT = 0.25                   # une audience sur quatre est reportee ( " anavoli ", a calibrer )
AUTOPHORO_J = (1, 3)              # le flagrant delit est juge sous trois jours ( " aftoforo " )
DELAI_MILITAIRE_J = 120           # a calibrer
DELAI_MAX_J = 3650.0              # l audience la plus lointaine : dix ans ( au-dela, le calendrier grec s arrete en 2099 )
JUGES_PAR_100K = 26.0             # CEPEJ 2020 : ~ 26 juges professionnels pour 100 000 habitants ( a verifier )
TRAITEMENT_JUGE_EUROS_MOIS = 2800.0   # brut d un juge de premier degre ( a verifier )
HEURE_AUDIENCE = 11.0

# ================================================================== les peines ( code penal grec, loi 4619/2019 : ordres de grandeur, a calibrer )
# nom : ( prison min jours, prison max jours, part des condamnations a l amende seule, amende en euros, detention provisoire )
PEINES = {
    "vol_simple": (30, 365, 0.5, 400.0, 0.0), "cambriolage": (180, 1095, 0.0, 1000.0, 0.10),
    "vol_violence": (1825, 3650, 0.0, 0.0, 0.60), "violences": (30, 730, 0.4, 500.0, 0.05),
    "homicide": (3650, 7300, 0.0, 0.0, 0.90), "incendie_criminel": (730, 2555, 0.0, 0.0, 0.30),
    "vol_vehicule": (180, 1095, 0.2, 800.0, 0.05), "fraude_fiscale": (365, 1825, 0.0, 5000.0, 0.0),
    "contrebande": (0, 0, 1.0, 0.0, 0.0), "corruption": (365, 1825, 0.0, 3000.0, 0.10),
    "fraude_assurance": (90, 730, 0.5, 1500.0, 0.0), "militaire": (30, 1825, 0.3, 500.0, 0.10)}
AMENDE_ET_PRISON = ("fraude_fiscale", "corruption")
P_SURSIS = 0.8                    # sursis d une peine de 3 ans au plus, sans casier ( art. 99, a calibrer )
SURSIS_MAX_J = 1095
LIBERATION_CONDITIONNELLE = 0.6   # liberation aux 3/5 de la peine ( art. 105B, a verifier )
PROVISOIRE_MAX_J = 365            # Constitution art. 6 : un an ( 18 mois exceptionnellement )
P_APPEL = 0.35                    # a calibrer
FACTEUR_INNOCENT = 0.35           # la preuve apparente contre un innocent ( a calibrer )

# ================================================================== les prisons
DETENUS_PAR_100K = 99.0           # SPACE I 2020 : Grece ~ 11 000 detenus ( a verifier )
OCCUPATION = 1.07                 # detenus par place ( SPACE I : ~ 100 a 110 %, a verifier )
PART_PROVISOIRES = 0.25           # SPACE I : ~ un quart de prevenus ( a verifier )
GARDIENS_PAR_DETENU = 0.4         # a calibrer
GARDIENS_MIN = 2
SOLDE_GARDIEN_EUROS_MOIS = 1100.0     # a verifier
COMPOSITION_DETENUS = (("cambriolage", 0.30), ("vol_violence", 0.20), ("vol_simple", 0.10), ("violences", 0.15),
                       ("homicide", 0.12), ("incendie_criminel", 0.03), ("vol_vehicule", 0.07), ("fraude_fiscale", 0.03))
COUSSIN_J = 10

# ================================================================== le droit civil
SAISIE_PART = 0.25                # part du disponible saisie chaque jour ( KPolD art. 982 : un quart du salaire ; a calibrer )
TAUX_FISCAL_MOIS = 0.0073         # interet de retard sur les dettes envers l Etat : 0,73 % par mois ( loi 4174/2013 art. 53, a verifier )
MARGE_LEGALE = 0.08               # taux legal de retard = taux directeur + 8 points ( loi 4152/2013, directive 2011/7 ; a verifier )
MOTIFS_INTERET = ("interet_moratoire", "interet_retard_fiscal")
P_CONTESTATION = 0.03             # successions contestees en justice ( a calibrer )

# les etats
OUVERTE, ELUCIDEE, CLASSEE, JUGEE, ETEINTE, ENTERREE = range(6)
ETATS = ("ouverte", "elucidee", "classee", "jugee", "eteinte", "enterree")
EN_ATTENTE, JUGE, SANS_OBJET = range(3)
PROVISOIRE, PEINE = 1, 2


# ================================================================== la decision
class ContexteEnquete:
    """Ce qu un enqueteur voit de son lot : les dossiers que designe chaque critere, et leurs pieces."""
    __slots__ = ("traits", "cibles")

    def __init__(self, traits, cibles): self.traits, self.cibles = traits, cibles


def _observer_enquete(ctx): return ctx.traits


def _regle_enquete(x, ctx): return GRAVE_RECENTE


def _temoin_enquete(x, ctx, rng): return PLUS_ANCIENNE


def _traits_declares():
    tr = []
    for c in CRITERES:
        tr += [(f"{c}_gravite", f"la qualification de l affaire designee par {c} ( code penal )"),
               (f"{c}_age", f"les jours depuis la plainte de l affaire {c}, sur le delai de classement"),
               (f"{c}_preuve", f"les pieces au dossier de l affaire {c} ( temoins, traces ), degradees par le temps")]
    tr += [("lot", "le nombre de dossiers ouverts du lot, sur 4"),
           ("charge", "les dossiers ouverts de la zone par enqueteur du jour, sur 10")]
    return tuple(tr)


POINT_ENQUETE = D.PointDeDecision(
    "enquete", "justice", traits=_traits_declares(), actions=CRITERES,
    observer=_observer_enquete, regle=_regle_enquete, temoin=_temoin_enquete,
    note="pour l affaire suivie : 1 si elle est elucidee dans les 7 jours, plus la part du tort rendue a sa victime",
    horizon_j=HORIZON_ENQUETE)


# ================================================================== les classes
class ServiceJustice:
    """Le ministere de la Justice : la caisse qui paie juges, gardiens et vivres des detenus."""
    __slots__ = ("id", "caisse", "recu_etat", "traitements", "soldes", "vivres")

    def __init__(self):
        self.id = "ministere_justice"
        self.caisse = self.recu_etat = self.traitements = self.soldes = self.vivres = 0.0


class Prison:
    __slots__ = ("id", "ile", "lieu", "lieu_n", "b", "places", "stock", "gardiens")

    def __init__(self, id, ile, lieu, lieu_n, b, places):
        if places < 1: raise ValueError(f"prison sans place : {places!r}")
        self.id, self.ile, self.lieu, self.lieu_n, self.b, self.places = id, ile, lieu, lieu_n, b, int(places)
        self.stock = BI.Stock()
        self.gardiens = []


class Tribunal:
    """Un tribunal par ile. Chaque file est une charge de travail FLUIDE ( affaires en attente, en unites ) qui monte
    avec les depots et descend de la capacite du jour : la date d audience se fixe au depot ( la " dikasimos "
    grecque ), a la charge devant divisee par la capacite."""
    __slots__ = ("id", "ile", "lieu", "b", "juges", "juges0", "charge", "capacite", "fond", "pop")

    def __init__(self, id, ile, lieu, b, pop):
        self.id, self.ile, self.lieu, self.b, self.pop = id, ile, lieu, b, pop
        self.juges = []; self.juges0 = 0
        self.charge, self.capacite, self.fond = {}, {}, {}


class Affaire:
    """Une infraction enregistree. `auteur` est la verite ( cachee a toute decision ) ; `suspect` celui que la police
    designe ( un innocent parfois )."""
    __slots__ = ("id", "type", "jour", "jour_plainte", "zone", "ile", "victime_m", "victime_h", "victime_o", "auteur",
                 "auteur_o", "gravite", "tort", "butin", "restitue", "preuve0", "flagrant", "etat", "suspect",
                 "jour_elucide", "effort", "dossier", "ref", "corrompue")

    def __init__(self, id, type_, jour, zone, ile, auteur, gravite, preuve0):
        if not 0 <= type_ < NT: raise ValueError(f"type d infraction inconnu {type_!r}")
        if not 0.0 <= preuve0 <= 1.0: raise ValueError(f"preuve hors [0 ; 1] : {preuve0!r}")
        self.id, self.type, self.jour, self.jour_plainte, self.zone, self.ile = id, type_, jour, jour, zone, ile
        self.auteur, self.auteur_o, self.gravite, self.preuve0 = auteur, None, gravite, preuve0
        self.victime_m = self.victime_h = -1; self.victime_o = None
        self.tort = self.butin = self.restitue = 0.0
        self.flagrant = False; self.etat = OUVERTE; self.suspect = -1; self.jour_elucide = -1
        self.effort = 0; self.dossier = -1; self.ref = -1; self.corrompue = False


class Dossier:
    __slots__ = ("id", "nature", "file", "affaire", "prevenu", "coupable", "preuve", "demandeur", "defendeur", "ref",
                 "saisine", "audience", "etat", "jugement", "ile", "reports")

    def __init__(self, id, nature, file, ile, saisine):
        self.id, self.nature, self.file, self.ile, self.saisine = id, nature, file, ile, saisine
        self.affaire = self.prevenu = self.ref = self.jugement = -1
        self.coupable = False; self.preuve = 0.0
        self.demandeur = self.defendeur = None
        self.audience = -1; self.etat = EN_ATTENTE; self.reports = 0


class Jugement:
    __slots__ = ("id", "dossier", "jour", "juridiction", "verdict", "personne", "prison_j", "sursis", "amende", "appel",
                 "definitif", "type")

    def __init__(self, id, dossier, jour, juridiction, verdict, personne=-1, type_=-1):
        self.id, self.dossier, self.jour, self.juridiction, self.verdict = id, dossier, jour, juridiction, verdict
        self.personne, self.type = personne, type_
        self.prison_j = 0; self.sursis = False; self.amende = 0.0; self.appel = False; self.definitif = True


class Detention:
    __slots__ = ("hid", "prison", "debut", "fin", "titre", "ref", "menage", "travail", "role")

    def __init__(self, hid, prison, debut, fin, titre, ref, menage, travail, role):
        if titre not in (PROVISOIRE, PEINE): raise ValueError(f"titre de detention inconnu {titre!r}")
        self.hid, self.prison, self.debut, self.fin, self.titre, self.ref = hid, prison, debut, fin, titre, ref
        self.menage, self.travail, self.role = menage, travail, role


class Jour:
    """La population du jour, lue en colonnes a 0 h 30 : les auteurs possibles et leurs poids, les zones."""
    __slots__ = ("jour", "ids", "poids", "zone_h", "zone_m", "nv", "adulte")

    def __init__(self, jour, ids, poids, zone_h, zone_m, nv, adulte):
        self.jour, self.ids, self.poids, self.zone_h, self.zone_m, self.nv, self.adulte = jour, ids, poids, zone_h, zone_m, nv, adulte


class Justice:
    """L etat du domaine."""
    __slots__ = ("service", "prisons", "prison_de_ile", "tribunaux", "tribunal_de_ile", "affaires", "prochaine_affaire",
                 "ouvertes", "dossiers", "prochain_dossier", "jugements", "prochain_jugement", "detentions",
                 "ordonnances", "prochaine_ordonnance", "peines", "titres", "interets_etat", "interet_j", "corruptions",
                 "decideur", "decisions", "dec_par_affaire", "prochaine_cle", "M0", "enr", "elu", "patrouille",
                 "patrouille_ref", "pop_zone", "facteur", "effort", "facteur_juges", "p_report", "ctx", "stats",
                 "vrais", "enregistres", "elucides", "expulsions0", "expulsions_jugees", "baux_en_justice", "vu_vols",
                 "vu_contrebande", "vu_faillites", "deces_vus", "dernier_controle", "a_radier", "delais", "vivres",
                 "interets_log", "actif", "juges_ids", "gardiens_ids", "amendes_de")

    def __init__(self):
        self.service = ServiceJustice()
        self.prisons, self.prison_de_ile, self.tribunaux, self.tribunal_de_ile = [], {}, [], {}
        self.affaires = {}; self.prochaine_affaire = 0
        self.ouvertes = {}                 # zone ( numero du lieu du marche ) -> [ affaires ouvertes ]
        self.dossiers = {}; self.prochain_dossier = 0
        self.jugements = {}; self.prochain_jugement = 0
        self.detentions = {}               # habitant -> Detention
        self.ordonnances = {}; self.prochaine_ordonnance = 0   # id -> ( habitant, jour, fin, dossier )
        self.peines = []                   # ( jugement, habitant ou -1, genre, montant ou jours ) : les peines executees
        self.titres = {}                   # creance -> [ creance, jour du titre, dernier jour d interet ]
        self.interets_etat = {}            # creance d interet de l Etat -> creance
        self.interet_j = {}                # creance de l Etat -> dernier jour d interet
        self.corruptions = []              # [ agent, suspect, montant, affaire, jour, decouverte ]
        self.decideur = None
        self.decisions = {}                # cle -> [ affaire, consequence en attente, jour du choix ]
        self.dec_par_affaire = {}
        self.prochaine_cle = 0
        self.M0 = {ACQ: 1.0, VIO: 1.0}
        self.enr = self.elu = None         # ( 2, lieux ) : ce que chaque zone a vu enregistrer et elucider ( lisse )
        self.patrouille, self.patrouille_ref, self.pop_zone = {}, {}, {}
        self.facteur = np.ones(NT)         # scenario : multiplicateur des infractions tirees
        self.effort = 1.0                  # scenario : multiplicateur des enqueteurs
        self.facteur_juges = 1.0
        self.p_report = P_REPORT
        self.ctx = None
        self.stats = {k: 0.0 for k in ("innocents_condamnes", "coupables_relaxes", "condamnations", "relaxes",
                                       "infirmations", "amendes", "amendes_payees", "restitutions", "pots_de_vin",
                                       "pots_montant", "expulsions", "titres", "saisies", "interets_civils",
                                       "interets_fiscaux", "faillites", "successions", "reports", "detenu_affame",
                                       "sanctions_douane", "morts_detention")}
        self.vrais = np.zeros(NT); self.enregistres = np.zeros(NT); self.elucides = np.zeros(NT)
        self.expulsions0 = 0; self.expulsions_jugees = 0
        self.baux_en_justice = {}
        self.vu_vols = self.vu_contrebande = self.vu_faillites = self.deces_vus = 0
        self.dernier_controle = -1
        self.a_radier = []
        self.delais = {n: [] for n in NOMS_FILES}   # ( jour du depot, delai fixe ) des dossiers simules
        self.vivres = {"achete": 0.0, "mange": 0.0, "rations": 0, "affames": 0}
        self.interets_log = []             # ( creance d origine, montant, taux annuel, jours, interet ) : la porte
        self.actif = True
        self.juges_ids = set(); self.gardiens_ids = set()
        self.amendes_de = {}               # jugement -> ( paye tout de suite, creance de l Etat ou None )


def _dom(p): return p.domaines["justice"]
def _membres_service(w): return (w.pays.domaines["justice"].service,)
def _membres_prisons(w): return w.pays.domaines["justice"].prisons


# ================================================================== lois pures ( testables seules )
def preuve(a, jour):
    """Les pieces au dossier : elles se degradent ( temoins qui oublient, traces effacees ) avec l age de l affaire."""
    return a.preuve0 * math.exp(-max(0, jour - a.jour) / TAU[a.type])


def p_elucider(q, preuve_, effort):
    """La chance qu une affaire soit elucidee aujourd hui : `effort` journees d enquete, chacune a q x preuve."""
    return 1.0 - (1.0 - min(1.0, q * preuve_)) ** effort


def p_condamnation(preuve_apparente):
    """La chance d une condamnation selon la preuve que voit le juge ( a calibrer : ~ 85 % a preuve forte )."""
    return min(0.97, 0.10 + 0.85 * max(0.0, preuve_apparente) ** 0.7)


def interet(montant, taux_an, jours):
    """L interet SIMPLE d une dette ( code civil grec art. 296 : pas d interet des interets )."""
    return montant * taux_an * jours / JOURS_AN


def taux_legal(p):
    """Le taux legal de retard ( taux directeur de la banque centrale + 8 points ) ."""
    return BQ.taux_directeur(p) + MARGE_LEGALE


def dissuasion(enr, elu, p_ref):
    """Le facteur de la dissuasion : le risque d etre pris que la zone a vu, lisse vers la reference."""
    vu = (elu + PRIOR_DISSUASION * p_ref) / (enr + PRIOR_DISSUASION)
    return np.clip((p_ref / np.maximum(vu, 1e-6)) ** ELAST_DISSUASION, *BORNES_DISSUASION)


def _pas_a(jour, heure):
    return int((jour * 1440 + heure * 60 - (C.DATE_DEPART[3] * 60 + C.DATE_DEPART[4])) // C.MINUTES_PAR_PAS)


def _jour_ouvre(p, jour):
    """Le premier jour ouvre ( du lundi au vendredi, hors feries grecs ) a partir de `jour`."""
    cal = p.socle.calendrier
    for k in range(15):
        if cal.ouvre(cal.date(_pas_a(jour + k, 12.0)).date()): return jour + k
    return jour


# ================================================================== la population du jour ( colonnes )
def _poids(p, S):
    """Les poids des auteurs possibles ( une passe numpy ) : age et sexe, puis faim, pauvrete, chomage, recidive, casier,
    dissuasion de la zone. Rend le Jour."""
    w = p.w; tb = w.table; n = tb.n; mt = tb.menages; M = mt.n
    p.colonnes["habitant"].assurer(n); p.colonnes["menage"].assurer(M)
    ch = p.colonnes["habitant"]
    viv = (tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT)
    age = (p.jour - ch["naissance_j"][:n]) / JOURS_AN
    k = tb.menage[:n].astype(np.int64); a_m = k >= 0; kk = np.maximum(k, 0)
    mdl = w._marche_du_lieu
    dom = tb.domicile[:n].astype(np.int64)
    zone_h = np.where(dom >= 0, mdl[np.maximum(dom, 0)], -1)
    nv = np.bincount(k[viv & a_m], minlength=M)[:M]
    dm = mt.domicile[:M].astype(np.int64)
    zone_m = np.where(dm >= 0, mdl[np.maximum(dm, 0)], -1)
    idx = np.searchsorted(AGES_AUTEUR, age, side="right") - 1
    base = np.where(idx >= 0, np.asarray(POIDS_AGE)[np.maximum(idx, 0)], 0.0)
    base = base * np.where(ch["sexe"][:n] == POP.HOMME, 1.0, FACTEUR_FEMMES)
    adulte = viv & (age >= 15.0) & a_m & (zone_h >= 0)
    faim = BITS7[p.col("menage", "faim7")[:M].astype(np.int64) & 0x7F][kk] / 7.0
    cpm = mt.caisse[:M] / np.maximum(nv, 1)
    habite = nv > 0
    med = float(np.median(cpm[habite])) if habite.any() else 1.0
    pauvre = np.clip(1.0 - cpm[kk] / max(med, 1e-6), 0.0, 1.0)
    role = tb.role[:n]
    chom = ((tb.travail[:n] < 0) & (age >= 18.0) & (age < 65.0) & (role != R_ENFANT) & (role != R_RETRAITE)).astype(float)
    rec = ((ch["ju_libere"][:n] == 1) & (p.jour - ch["ju_libere_j"][:n] <= RECIDIVE_J)).astype(float)
    cas = (ch["ju_casier"][:n] > 0).astype(float)
    ids = np.nonzero(adulte & (base > 0))[0]
    z = zone_h[ids]
    poids = {}
    for fam in (ACQ, VIO):
        ef, ep, ec, er, ek = ELASTICITES[fam]
        dis = dissuasion(S.enr[fam], S.elu[fam], ELUC_REF[fam])
        poids[fam] = (base[ids] * (1.0 + ef * faim[ids]) * (1.0 + ep * pauvre[ids]) * (1.0 + ec * chom[ids])
                      * (1.0 + er * rec[ids]) * (1.0 + ek * cas[ids]) * dis[z])
    return Jour(p.jour, ids, poids, zone_h, zone_m, nv, adulte)


def intensites(p, S, J):
    """Les infractions attendues aujourd hui, par type tire ici ( l esperance du Poisson ) : le taux vrai grec, recale par
    la somme des poids du jour sur celle de l installation ( la faim, le chomage, la dissuasion la font bouger )."""
    lam = np.zeros(NT)
    for nom in TIRES:
        t = IDX[nom]
        if nom == "incendie_criminel" and not p.a("securite_civile"): continue
        fam = int(FAMILLE[t])
        lam[t] = VRAIS[t] / 1e5 / JOURS_AN * float(J.poids[fam].sum()) / S.M0[fam] * S.facteur[t]
    return lam


def tirer_delits(p, S, J, rng):
    """Les infractions de la nuit : ( type, auteur ), dans l ordre des types. Sans effet sur le monde ( la porte les
    tire des milliers de fois )."""
    lam = intensites(p, S, J)
    out = []
    for nom in TIRES:
        t = IDX[nom]
        if lam[t] <= 0.0: continue
        k = int(rng.poisson(lam[t]))
        if k <= 0: continue
        wv = J.poids[int(FAMILLE[t])]
        s = float(wv.sum())
        if s <= 0.0: continue
        for j in rng.choice(len(J.ids), k, p=wv / s).tolist(): out.append((t, int(J.ids[j])))
    return out


# ================================================================== les victimes
def _victime_menage(J, z, sauf, rng):
    cand = np.nonzero((J.zone_m == z) & (J.nv > 0))[0]
    if sauf >= 0: cand = cand[cand != sauf]
    return int(cand[int(rng.integers(0, len(cand)))]) if len(cand) else -1


def _victime_habitant(p, J, z, auteur, familial, rng):
    tb = p.w.table
    if familial:
        k = int(tb.menage[auteur])
        fam = [i for i in tb.menages.membres_ids(k) if i != auteur and i < len(J.adulte) and J.adulte[i]] if k >= 0 else []
        if fam: return int(fam[int(rng.integers(0, len(fam)))])
    cand = np.nonzero(J.adulte & (J.zone_h == z))[0]
    cand = cand[cand != auteur]
    return int(cand[int(rng.integers(0, len(cand)))]) if len(cand) else -1


def _blesser(p, hid, type_, iss):
    h = PO.Habitant(p.w.table, hid)
    if not h.vivant: return
    if p.a("medecine"): MED.blesser(p, h, type_, int(iss), cause="violence")
    elif iss >= 75: POP.deceder(p, h, "violence")


# ================================================================== les infractions : commission, plainte
def _nouvelle_affaire(p, S, t, zone, ile, auteur, rng):
    m = PREUVE0[t]
    p0 = float(m) if m >= 0.99 else float(rng.beta(4.0 * m, 4.0 * (1.0 - m)))
    a = Affaire(S.prochaine_affaire, t, p.jour, zone, ile, auteur, float(GRAVITE[t]), p0)
    S.prochaine_affaire += 1
    return a


def _commettre(p, S, J, t, auteur, rng):
    """Une infraction : ses effets sur le monde ( argent, blessure, mort, feu ), puis la plainte ( ou le chiffre noir )."""
    w = p.w; tb = w.table; L = p.socle.livre; nom = NOMS[t]
    z = int(J.zone_h[auteur])
    if z < 0: return None
    ile = w.carte.par_n[z].ile
    a = _nouvelle_affaire(p, S, t, z, ile, auteur, rng)
    ka = int(tb.menage[auteur])
    if nom in BUTIN:
        v = _victime_menage(J, z, ka, rng)
        if v < 0: return None
        a.victime_m = v
        part, plafond = BUTIN[nom]
        vm = w.menages[v]
        x = L.transferer(vm, w.menages[ka], min(part * max(0.0, vm.caisse), plafond / EUROS), "vol") if ka >= 0 else 0.0
        a.butin = a.tort = x
        if nom == "vol_violence" and rng.random() < P_BLESSE_VOL_VIOLENCE:
            hv = _victime_habitant(p, J, z, auteur, False, rng)
            if hv >= 0: a.victime_h = hv; _blesser(p, hv, "chute", 1 + int(rng.integers(0, 4)))
    elif nom in ("violences", "homicide"):
        hv = _victime_habitant(p, J, z, auteur, rng.random() < FAMILIAL[nom], rng)
        if hv < 0: return None
        a.victime_h = hv; a.victime_m = int(tb.menage[hv])
        if nom == "homicide":
            _blesser(p, hv, "balistique" if rng.random() < 0.3 else "arme_blanche", 75)
        else:
            u = rng.random(); acc = 0.0; iss = 1
            for g, q in ISS_VIOLENCES:
                acc += q
                if u < acc: iss = g; break
            _blesser(p, hv, "arme_blanche" if rng.random() < 0.3 else "chute", iss)
    elif nom == "incendie_criminel":
        v = _victime_menage(J, z, ka, rng)
        if v < 0: return None
        b = IM.logement_de(p, w.menages[v])[0]
        if b < 0: return None
        a.victime_m = v; a.tort = PART_DEGATS_INCENDIE * IM.valeur(p, b)
        a.ref = SC.allumer(p, "habitation", b=b, cause="criminelle")
    S.vrais[t] += 1
    flag = rng.random() < FLAGRANT[t] * _patrouille(S, z)
    declare = flag or rng.random() < DECLAREE[t]
    p.noter("delit", affaire=a.id, nature=nom, lieu=w.carte.par_n[z].id, declare=bool(declare))
    if not declare:
        p.compter("delit_non_declare"); return None
    return _enregistrer(p, S, a, rng, flagrant=flag)


def _patrouille(S, z):
    """La densite de patrouille de la zone, sur celle de l installation ( le flagrant delit en depend )."""
    ref = S.patrouille_ref.get(z, 0)
    if ref <= 0: return 1.0
    return float(np.clip(S.patrouille.get(z, ref) / ref, 0.2, 3.0))


def _enregistrer(p, S, a, rng, flagrant=False, auteur_connu=None):
    """La plainte : l affaire entre au registre de la police ; flagrant delit ou auteur connu : elucidee d emblee."""
    S.affaires[a.id] = a
    a.jour_plainte = p.jour
    t = a.type; fam = int(FAMILLE[t])
    S.enregistres[t] += 1
    if fam != AUT and a.zone >= 0: S.enr[fam][a.zone] += 1.0
    p.compter("plainte")
    connu = (rng.random() < AUTEUR_CONNU[t]) if auteur_connu is None else auteur_connu
    if flagrant:
        a.flagrant = True; _elucider(p, S, a, "flagrant", rng)
    elif connu:
        _elucider(p, S, a, "victime", rng)
    else:
        S.ouvertes.setdefault(a.zone, []).append(a.id)
    return a


def _delits(p):
    """0 h 30 : la population du jour, puis les infractions de la nuit et leurs plaintes."""
    S = _dom(p)
    if not S.actif: return
    rng = p.du_jour("justice_delits")
    J = S.ctx = _poids(p, S)
    for t, auteur in tirer_delits(p, S, J, rng):
        if p.w.table.vivant[auteur] and p.w.table.statut[auteur] != PO.ABSENT: _commettre(p, S, J, t, auteur, rng)


# ================================================================== l elucidation, l arrestation
def _innocent(p, S, a, rng):
    """Un homme adulte de la zone, libre, qui n est pas l auteur : la designation erronee."""
    w = p.w; tb = w.table; n = tb.n
    ch = p.colonnes["habitant"]
    age = (p.jour - ch["naissance_j"][:n]) / JOURS_AN
    mdl = w._marche_du_lieu; dom = tb.domicile[:n].astype(np.int64)
    zone = np.where(dom >= 0, mdl[np.maximum(dom, 0)], -1)
    cand = np.nonzero((tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT) & (zone == a.zone) & (age >= 18.0)
                      & (age < 60.0) & (ch["sexe"][:n] == POP.HOMME) & (tb.menage[:n] >= 0))[0]
    cand = cand[cand != a.auteur]
    return int(cand[int(rng.integers(0, len(cand)))]) if len(cand) else a.auteur


def _crediter(S, aid, valeur):
    """La consequence d une affaire revient aux choix d enquete qui l ont suivie ( horizon en cours )."""
    for cle in S.dec_par_affaire.get(aid, ()):
        d = S.decisions.get(cle)
        if d is not None: d[1] += valeur


def _elucider(p, S, a, voie, rng, agent=-1):
    """L affaire a un suspect : la police l arrete ou le convoque. Corruption possible, restitution, poursuite."""
    w = p.w; tb = w.table; L = p.socle.livre
    a.etat = ELUCIDEE; a.jour_elucide = p.jour
    t = a.type; nom = NOMS[t]
    S.elucides[t] += 1
    fam = int(FAMILLE[t])
    if fam != AUT and a.zone >= 0: S.elu[fam][a.zone] += 1.0
    p.compter("elucidation")
    _crediter(S, a.id, 1.0)
    if a.auteur_o is not None: return _poursuivre(p, S, a, rng)
    if a.auteur >= 0 and not tb.vivant[a.auteur]:
        a.etat = ETEINTE; return a                       # la mort de l auteur eteint l action publique
    if a.auteur < 0:                                     # pas d auteur : une fausse alerte designe l assure, sinon rien
        if nom == "fraude_assurance" and a.ref >= 0 and tb.vivant[a.ref]: suspect = a.ref
        else: a.etat = ETEINTE; return a
    else: suspect = a.auteur
    if voie == "enquete" and a.auteur >= 0 and rng.random() < P_ERREUR_ID: suspect = _innocent(p, S, a, rng)
    a.suspect = suspect
    p.noter("arrestation", affaire=a.id, suspect=suspect, flagrant=bool(a.flagrant))
    ks = int(tb.menage[suspect])
    if voie == "enquete" and agent >= 0 and ks >= 0 and tb.vivant[agent]:
        dispo = IM.disponible(p, w.menages[ks])
        if dispo >= POT_MIN_EUROS / EUROS and rng.random() < P_OFFRE_POT and rng.random() < P_ACCEPTE_POT:
            ka = int(tb.menage[agent])
            if ka >= 0:
                x = L.transferer(w.menages[ks], w.menages[ka], min(PART_POT * dispo, POT_MAX_EUROS / EUROS), "pot_de_vin")
                S.corruptions.append([agent, suspect, x, a.id, p.jour, False])
                S.stats["pots_de_vin"] += 1; S.stats["pots_montant"] += x; p.compter("pot_de_vin", x)
                if rng.random() < P_ENTERRE:
                    a.etat = ENTERREE; a.corrompue = True; return a
    if suspect == a.auteur and ks >= 0 and a.butin - a.restitue > EPS and a.victime_m >= 0:
        x = min(a.butin - a.restitue, IM.disponible(p, w.menages[ks])) * P_SAISIE_BUTIN
        if x > EPS:
            x = L.transferer(w.menages[ks], w.menages[a.victime_m], x, "restitution_vol")
            a.restitue += x; S.stats["restitutions"] += x; p.compter("restitution", x)
            _crediter(S, a.id, x / max(a.tort, EPS))
    if nom == "vol_vehicule" and suspect == a.auteur and a.ref >= 0 and p.a("transport"):
        if TRA.retrouver(p, a.ref):
            a.restitue = a.tort; _crediter(S, a.id, 1.0)
    return _poursuivre(p, S, a, rng)


# ================================================================== les dossiers et les audiences
def _nouveau_dossier(p, S, nature, file, ile):
    d = Dossier(S.prochain_dossier, nature, file, ile, p.jour)
    S.prochain_dossier += 1
    S.dossiers[d.id] = d
    return d


def _tribunal(S, ile):
    return S.tribunaux[S.tribunal_de_ile.get(ile, 0)]


def _capacite(p, S, t, file):
    tb = p.w.table
    vivants = sum(1 for j in t.juges if tb.vivant[j] and p.col("habitant", "ju_detenu")[j] == 0)
    return t.capacite[file] * S.facteur_juges * (vivants / t.juges0 if t.juges0 else 1.0)


def delai_prevu(p, file, ile=None):
    """Le delai d un dossier depose aujourd hui ( jours ) : la charge devant, sur la capacite du jour."""
    S = _dom(p); t = _tribunal(S, ile) if ile is not None else S.tribunaux[0]
    cap = _capacite(p, S, t, file)
    return t.charge[file] / cap if cap > EPS else math.inf


def _saisir(p, S, d, file=None, delai=None):
    """Le depot : la date d audience est fixee tout de suite ( charge devant / capacite ), au premier jour ouvre."""
    t = _tribunal(S, d.ile)
    if file is not None: d.file = file
    if delai is None:
        if d.file in t.charge:
            cap = _capacite(p, S, t, d.file)
            # ( 28/09, HMT-126 ) borne a dix ans, comme un tribunal sans juge : une file qui deborde ( loyers impayes du
            # chomage de masse ) donnait des audiences au-dela de 2099, ou le calendrier grec s arrete ( ValueError )
            delai = min(t.charge[d.file] / cap, DELAI_MAX_J) if cap > EPS else DELAI_MAX_J
            t.charge[d.file] += 1.0
            S.delais[d.file].append((p.jour, delai))
        else: delai = 0.0
    jour = _jour_ouvre(p, p.jour + max(1, int(math.ceil(delai))))
    d.audience = jour
    p.poser(max(0, _pas_a(jour, HEURE_AUDIENCE) - p.w.pas), "justice_audience", d.id)
    return d


def _poursuivre(p, S, a, rng):
    """Le parquet poursuit : flagrant delit ( juge sous trois jours ), correctionnelle ou cour criminelle ; detention
    provisoire pour les crimes selon leur gravite."""
    w = p.w; tb = w.table; nom = NOMS[a.type]
    if nom == "contrebande": return _sanction_douane(p, S, a)
    d = _nouveau_dossier(p, S, "penal", "correctionnel", a.ile)
    d.affaire = a.id; d.prevenu = a.suspect; d.coupable = a.suspect == a.auteur
    d.preuve = 0.9 if a.flagrant else min(1.0, 0.3 + preuve(a, p.jour))
    a.dossier = d.id
    felonie = bool(FELONIE[a.type])
    if nom == "militaire":
        return _saisir(p, S, d, "militaire", DELAI_MILITAIRE_J)
    if a.flagrant and not felonie:
        return _saisir(p, S, d, "autophoro", int(rng.integers(AUTOPHORO_J[0], AUTOPHORO_J[1] + 1)))
    file = "criminel" if felonie else "correctionnel"
    if felonie and tb.vivant[d.prevenu] and d.prevenu not in S.detentions and rng.random() < PEINES[nom][4]:
        o = S.prochaine_ordonnance; S.prochaine_ordonnance += 1
        S.ordonnances[o] = (d.prevenu, p.jour, p.jour + PROVISOIRE_MAX_J, d.id)
        _incarcerer(p, S, d.prevenu, PROVISOIRE, o, p.jour + PROVISOIRE_MAX_J)
        file = "criminel_detenu"
    return _saisir(p, S, d, file)


def _jugement(p, S, d, juridiction, verdict, personne=-1, type_=-1):
    J = Jugement(S.prochain_jugement, d.id if d is not None else -1, p.jour, juridiction, verdict, personne, type_)
    S.prochain_jugement += 1
    S.jugements[J.id] = J
    if d is not None: d.jugement = J.id; d.etat = JUGE
    return J


def _audience(p, did, donnees):
    """Le jour d audience : report ( une fois sur quatre ), ou jugement."""
    S = _dom(p); d = S.dossiers.get(did)
    if d is None or d.etat != EN_ATTENTE: return
    rng = p.hasard("justice_audiences")
    p.compter("audience")
    if d.file not in ("autophoro",) and d.reports < 3 and rng.random() < S.p_report:
        d.reports += 1; S.stats["reports"] += 1; p.compter("report_audience")
        rep = FILES[d.file][2] if d.file in FILES else 30.0
        jour = _jour_ouvre(p, p.jour + max(1, int(rep)))
        d.audience = jour
        p.poser(max(0, _pas_a(jour, HEURE_AUDIENCE) - p.w.pas), "justice_audience", d.id)
        return
    if d.nature in ("penal", "appel"): _juger_penal(p, S, d, rng)
    elif d.nature == "bail": _juger_bail(p, S, d)
    elif d.nature == "injonction": _juger_injonction(p, S, d)


def _juger_penal(p, S, d, rng):
    w = p.w; tb = w.table
    a = S.affaires[d.affaire]; h = d.prevenu; nom = NOMS[a.type]
    juri = "appel" if d.nature == "appel" else d.file
    if h < 0 or not tb.vivant[h]:
        J = _jugement(p, S, d, juri, "eteinte", h, a.type); a.etat = ETEINTE
        if h in S.detentions: _liberer(p, S, h, "deces")
        return J
    app = d.preuve * (1.0 if d.coupable else FACTEUR_INNOCENT)
    cond = rng.random() < p_condamnation(app)
    k = int(tb.menage[h])
    if cond and k >= 0 and rng.random() < P_OFFRE_JUGE and rng.random() < P_ACCEPTE_JUGE:   # un juge achete
        dispo = IM.disponible(p, w.menages[k])
        t = _tribunal(S, d.ile); juges = [j for j in t.juges if tb.vivant[j] and tb.menage[j] >= 0]
        if dispo >= POT_MIN_EUROS / EUROS and juges:
            j = juges[int(rng.integers(0, len(juges)))]
            x = p.socle.livre.transferer(w.menages[k], w.menages[int(tb.menage[j])], min(PART_POT * dispo, POT_MAX_EUROS / EUROS), "pot_de_vin")
            S.corruptions.append([j, h, x, a.id, p.jour, False])
            S.stats["pots_de_vin"] += 1; S.stats["pots_montant"] += x; p.compter("pot_de_vin", x)
            cond = False
    a.etat = JUGEE
    if not cond:
        J = _jugement(p, S, d, juri, "relaxe", h, a.type)
        S.stats["relaxes"] += 1
        if d.coupable: S.stats["coupables_relaxes"] += 1
        if d.nature == "appel":
            S.stats["infirmations"] += 1; p.compter("erreur_judiciaire")
            J0 = S.jugements.get(d.ref)
            if J0 is not None: J0.definitif = False
            _rembourser_amende(p, S, J0, h)
        det = S.detentions.get(h)
        if det is not None and (det.titre == PROVISOIRE or (d.nature == "appel" and det.ref == d.ref)):
            _liberer(p, S, h, "relaxe")
        p.noter("jugement", dossier=d.id, nature=nom, prevenu=h, verdict="relaxe", peine=0, instance=juri)
        return J
    pmin, pmax, p_amende, amende_eur, _ = PEINES[nom]
    J = _jugement(p, S, d, juri, "condamne", h, a.type)
    S.stats["condamnations"] += 1
    if not d.coupable: S.stats["innocents_condamnes"] += 1; p.compter("erreur_judiciaire")
    ch = p.colonnes["habitant"]
    if d.nature == "appel":
        J0 = S.jugements.get(d.ref)
        if J0 is not None: J.prison_j, J.sursis, J.amende = J0.prison_j, J0.sursis, J0.amende
        if J0 is not None and J0.id in S.amendes_de: J.amende = 0.0     # deja payee en premiere instance
    else:
        seule = rng.random() < p_amende
        J.prison_j = 0 if seule or pmax <= 0 else int(rng.integers(pmin, pmax + 1))
        J.amende = amende_eur / EUROS if (seule or nom in AMENDE_ET_PRISON) else 0.0
        J.sursis = 0 < J.prison_j <= SURSIS_MAX_J and ch["ju_casier"][h] == 0 and rng.random() < P_SURSIS
        ch["ju_casier"][h] = min(100, int(ch["ju_casier"][h]) + 1)
        J.appel = d.nature == "penal" and d.file != "autophoro" and rng.random() < P_APPEL
        if J.appel:
            J.definitif = False
            da = _nouveau_dossier(p, S, "appel", "appel", d.ile)
            da.affaire, da.prevenu, da.coupable, da.preuve, da.ref = d.affaire, h, d.coupable, d.preuve, J.id
            _saisir(p, S, da); p.compter("appel")
        _dommages(p, S, a, h)
    execute = not J.appel or J.prison_j > SURSIS_MAX_J
    if execute: _executer(p, S, J, h, a)
    elif h in S.detentions and S.detentions[h].titre == PROVISOIRE: _liberer(p, S, h, "appel_suspensif")
    if nom == "corruption" and d.coupable and tb.vivant[h] and PO.Habitant(tb, h).travail is not None and \
            tb.role[h] == PO.CODE_ROLE["policier"]:
        ECO.licencier(p, PO.Habitant(tb, h), "revocation", inscrire=True)
    p.noter("jugement", dossier=d.id, nature=nom, prevenu=h, verdict="condamne", peine=int(J.prison_j), instance=juri)
    return J


def _executer(p, S, J, h, a):
    """L execution : l amende au Tresor ( le reste en creance de l Etat ), la prison ferme ( la detention provisoire
    s impute ), liberation conditionnelle aux 3/5."""
    w = p.w; tb = w.table
    k = int(tb.menage[h])
    if J.amende > EPS and k >= 0:
        paye, cr = ET.infliger_amende(p, w.menages[k], J.amende)
        S.amendes_de[J.id] = (paye, cr)
        S.peines.append((J.id, h, "amende", J.amende))
        S.stats["amendes"] += J.amende; S.stats["amendes_payees"] += paye; p.compter("amende_penale", paye)
    if J.prison_j > 0 and not J.sursis:
        det = S.detentions.get(h)
        debut = det.debut if det is not None and det.titre == PROVISOIRE else p.jour
        fin = debut + int(round(LIBERATION_CONDITIONNELLE * J.prison_j))
        S.peines.append((J.id, h, "prison", J.prison_j))
        if det is not None and det.titre == PEINE: fin = max(fin, det.fin)
        if fin <= p.jour:
            if det is not None: _liberer(p, S, h, "peine_purgee")
        else: _incarcerer(p, S, h, PEINE, J.id, fin)
    elif h in S.detentions and S.detentions[h].titre == PROVISOIRE:
        _liberer(p, S, h, "sursis")


def _rembourser_amende(p, S, J0, h):
    """Relaxe en appel : l Etat rend ce qui a ete paye de l amende ( la creance restante est abandonnee )."""
    if J0 is None or J0.id not in S.amendes_de: return
    w = p.w; K = p.socle.creances
    paye, cr = S.amendes_de.pop(J0.id)
    if cr is not None and K.actives.get(cr.id) is cr:
        K.abandonner(cr, "relaxe")
    k = int(w.table.menage[h])
    if k >= 0 and paye > EPS:
        ET.assurer(p, paye)
        p.socle.livre.transferer(w.gouv, w.menages[k], paye, "remboursement_amende")
    S.peines = [x for x in S.peines if not (x[0] == J0.id and x[2] == "amende")]


def _dommages(p, S, a, h):
    """La partie civile : le tort non rendu devient une creance de la victime sur le condamne, sous titre executoire."""
    w = p.w; tb = w.table
    reste = a.tort - a.restitue
    k = int(tb.menage[h])
    if reste <= 1.0 or k < 0: return
    vict = w.menages[a.victime_m] if a.victime_m >= 0 else a.victime_o
    if vict is None or vict is w.menages[k]: return
    c = p.socle.creances.constater(vict, w.menages[k], reste, "dommages_interets", p.jour)
    _titre(S, c, p.jour)


def _sanction_douane(p, S, a):
    """Une saisie de contrebande : la douane inflige l amende ( un multiple de la valeur ) au reseau, sans tribunal ; sa
    decision est le titre de la peine."""
    d = _nouveau_dossier(p, S, "douane", "douane", a.ile)
    d.affaire = a.id; a.dossier = d.id
    J = _jugement(p, S, d, "douane", "sanction_administrative", -1, a.type)
    a.etat = JUGEE
    montant = MULT_AMENDE_DOUANE * a.tort
    if montant > EPS and a.auteur_o is not None and hasattr(a.auteur_o, "caisse"):
        paye, _ = ET.infliger_amende(p, a.auteur_o, montant)
        J.amende = montant
        S.peines.append((J.id, -1, "amende", montant))
        S.stats["sanctions_douane"] += 1; S.stats["amendes"] += montant; S.stats["amendes_payees"] += paye
        p.compter("sanction_douane", paye)
    return a


# ================================================================== la detention
def _incarcerer(p, S, hid, titre, ref, fin):
    """Un habitant entre en prison : il perd son emploi, il ne mange plus chez lui ( ABSENT ), il est domicilie a la
    prison de son ile. Un detenu deja la change seulement de titre."""
    w = p.w; tb = w.table; ch = p.colonnes["habitant"]
    det = S.detentions.get(hid)
    if det is not None:
        det.titre, det.ref, det.fin = titre, ref, fin
        ch["ju_detenu"][hid] = titre
        return det
    dom = int(tb.domicile[hid])
    ile = w.carte.par_n[dom].ile if dom >= 0 else w.carte.iles[0]
    pr = S.prisons[S.prison_de_ile.get(ile, 0)]
    h = PO.Habitant(tb, hid)
    trav = int(tb.travail[hid]); role = int(tb.role[hid])
    if h.travail is not None:
        if p.a("travail"):
            TRV.rompre_contrat(p, h, "incarceration", involontaire=False)
            p.col("habitant", "tr_statut")[hid] = TRV.HORS
        else: ECO.licencier(p, h, "incarceration", inscrire=False)
    p.domaine("economie").chomeurs.pop(hid, None)
    det = Detention(hid, pr.id, p.jour, fin, titre, ref, int(tb.menage[hid]), trav, role)
    S.detentions[hid] = det
    tb.statut[hid] = PO.ABSENT
    tb.domicile[hid] = pr.lieu_n; tb.lieu[hid] = pr.lieu_n; tb.poste[hid] = MAISON_P
    ch["ju_detenu"][hid] = titre
    p.noter("incarceration", habitant=hid, prison=pr.id, titre="provisoire" if titre == PROVISOIRE else "peine", fin=int(fin))
    return det


def _liberer(p, S, hid, motif):
    """La sortie : retour au menage ( un menage neuf s il a ete dissous ), au registre des chomeurs s il avait un emploi."""
    w = p.w; tb = w.table; ch = p.colonnes["habitant"]
    det = S.detentions.pop(hid, None)
    ch["ju_detenu"][hid] = 0
    if det is None: return
    p.noter("liberation", habitant=hid, prison=det.prison, motif=motif)
    if not tb.vivant[hid]: return
    tb.statut[hid] = PO.RESIDENT
    ch["ju_libere"][hid] = 1; ch["ju_libere_j"][hid] = p.jour
    k = int(tb.menage[hid])
    h = PO.Habitant(tb, hid)
    if k < 0 or p.col("menage", "dissous")[k]:
        pr = S.prisons[det.prison]
        mg = POP.nouveau_menage(p, w.carte.lieux[pr.lieu])
        if k >= 0: POP.deplacer_membre(p, h, mg, garde_manger=False)
        k = mg.id
    dm = int(tb.menages.domicile[k])
    tb.domicile[hid] = dm; tb.lieu[hid] = dm; tb.poste[hid] = MAISON_P
    age = (p.jour - ch["naissance_j"][hid]) / JOURS_AN
    if det.travail >= 0 and 18.0 <= age < 65.0:
        p.domaine("economie").chomeurs[hid] = [p.jour, w.carte.par_n[det.travail].id, PO.ROLES[det.role], "liberation"]
        if p.a("travail"):
            p.col("habitant", "tr_statut")[hid] = TRV.CHOMEUR; p.col("habitant", "tr_chomage_j")[hid] = p.jour


def _prisons_matin(p):
    """0 h 40 : fins de peine et de detention provisoire, morts en detention ( la table du domaine 1, qui ne tire pas un
    absent ), le domicile de chaque detenu tenu a la prison."""
    S = _dom(p); w = p.w; tb = w.table
    if not S.detentions: return
    rng = p.du_jour("justice_prison")
    d1 = p.domaine("population")
    ch = p.colonnes["habitant"]
    for hid in sorted(S.detentions):
        det = S.detentions[hid]
        if not tb.vivant[hid]: _liberer(p, S, hid, "deces"); continue
        if det.fin <= p.jour:
            _liberer(p, S, hid, "fin_de_peine" if det.titre == PEINE else "delai_provisoire"); continue
        age = int(min(POP.AGE_MAX, max(0, (p.jour - ch["naissance_j"][hid]) // 365)))
        q = float(d1.mortalite.q_jour(np.array([int(ch["sexe"][hid])]), np.array([age]))[0])
        if rng.random() < q:
            POP.deceder(p, PO.Habitant(tb, hid), "naturelle"); S.stats["morts_detention"] += 1
            _liberer(p, S, hid, "deces"); continue
        pr = S.prisons[det.prison]
        if tb.domicile[hid] != pr.lieu_n or tb.statut[hid] != PO.ABSENT:
            tb.domicile[hid] = pr.lieu_n; tb.lieu[hid] = pr.lieu_n; tb.statut[hid] = PO.ABSENT


def _vivres_achat(p):
    """19 h 30 : chaque prison achete au marche de sa zone la ration du jour de ses detenus ( et la TVA a l Etat )."""
    S = _dom(p); w = p.w; L = p.socle.livre; cat = p.socle.catalogue
    b = cat.id("nourriture")
    par = _detenus_par_prison(S, w)
    for pr in S.prisons:
        besoin = par[pr.id] * C.NOURRITURE_PAR_JOUR - pr.stock[b]
        if besoin <= EPS: continue
        m = w.marches[w.carte.par_n[int(w._marche_du_lieu[pr.lieu_n])].id]
        prix = m.prix["nourriture"]
        q = min(besoin, max(0.0, m.stocks.get("nourriture", 0.0)), S.service.caisse / max(prix * 1.2, EPS))
        if q <= EPS: continue
        q = L.deplacer(EXT.StockE1(m.stocks, cat), pr.stock, b, q, "achat_penitentiaire")
        x = L.transferer(S.service, m, q * prix, "achat_penitentiaire")
        x += ET.percevoir_tva(p, S.service, "nourriture", q * prix)
        S.service.vivres += x; S.vivres["achete"] += q


def _vivres_repas(p):
    """20 h 10 : les detenus mangent le stock de la prison ; un detenu sans ration a faim."""
    S = _dom(p); w = p.w; tb = w.table; L = p.socle.livre
    b = p.socle.catalogue.id("nourriture")
    parp = {}
    for hid in sorted(S.detentions):
        if tb.vivant[hid]: parp.setdefault(S.detentions[hid].prison, []).append(hid)
    for pr in S.prisons:
        ids = parp.get(pr.id, [])
        if not ids: continue
        besoin = len(ids) * C.NOURRITURE_PAR_JOUR
        q = L.consommer(pr.stock, b, min(besoin, pr.stock[b]), "repas_detenus")
        S.vivres["mange"] += q
        servis = int(math.floor(q / C.NOURRITURE_PAR_JOUR + 1e-9))
        S.vivres["rations"] += servis; p.compter("repas_detenu", servis)
        a = np.asarray(ids, np.int64)
        tb.faim[a[:servis]] = np.maximum(0.0, tb.faim[a[:servis]] - 1.0)
        if servis < len(ids):
            tb.faim[a[servis:]] += 1.0
            S.vivres["affames"] += len(ids) - servis; S.stats["detenu_affame"] += len(ids) - servis
            p.compter("detenu_affame", len(ids) - servis)


def _detenus_par_prison(S, w):
    par = [0] * len(S.prisons)
    tb = w.table
    for hid, det in S.detentions.items():
        if tb.vivant[hid]: par[det.prison] += 1
    return par


def bilan_vivres(p):
    """( achete, mange, en stock ) : ce qui est entre dans les prisons est mange ou y est encore."""
    S = _dom(p); b = p.socle.catalogue.id("nourriture")
    return S.vivres["achete"], S.vivres["mange"], math.fsum(pr.stock[b] for pr in S.prisons)


# ================================================================== la police : l enquete du matin
def _policiers_presents(p):
    w = p.w; tb = w.table; out = []
    for cap in w.carte.capitales:
        ids = w.ids_au_travail(cap, "policier")
        if not ids: continue
        a = np.asarray(ids, dtype=np.int64)
        out.append(a[(tb.vivant[a] != 0) & (tb.poste[a] == TRAVAIL_P)])
    return np.sort(np.concatenate(out)) if out else np.zeros(0, np.int64)


def _designer(S, lot, crit, jour):
    As = [S.affaires[i] for i in lot]
    if crit == GRAVE_RECENTE: a = max(As, key=lambda x: (x.gravite * math.exp(-(jour - x.jour_plainte) / FRAICHEUR_J), x.id))
    elif crit == PLUS_GRAVE: a = max(As, key=lambda x: (x.gravite, x.jour_plainte, x.id))
    elif crit == PLUS_RECENTE: a = max(As, key=lambda x: (x.jour_plainte, x.id))
    elif crit == PLUS_ANCIENNE: a = min(As, key=lambda x: (x.jour_plainte, x.id))
    else: a = max(As, key=lambda x: (preuve(x, jour), x.id))
    return a.id


def _enquetes(p):
    """10 h, apres le controle fiscal : la police judiciaire du jour ( une part des policiers presents que le fisc n a
    pas pris ) ; chaque enqueteur choisit son affaire ; les journees d enquete elucident ; les affaires trop vieilles
    sont classees ; le reste des presents patrouille."""
    S = _dom(p); w = p.w; tb = w.table; jour = p.jour
    if not S.actif: return
    rng = p.du_jour("justice_enquete")
    pres = _policiers_presents(p)
    k = int(math.ceil(ET._etat(p).fisc.part_controleurs * len(pres)))
    dispo = pres[k:]
    zone = w._marche_du_lieu[tb.travail[dispo].astype(np.int64)] if len(dispo) else np.zeros(0, np.int64)
    enq = {}; S.patrouille = {}
    for z in sorted(set(zone.tolist())):
        ids = dispo[zone == z]
        voulu = ENQUETEURS_PAR_1000 * PRESENCE * S.pop_zone.get(z, 0) / 1000.0 * S.effort
        n = int(voulu); n += 1 if rng.random() < voulu - n else 0
        n = min(n, len(ids))
        enq[z] = ids[:n].tolist(); S.patrouille[z] = len(ids) - n
        if z not in S.patrouille_ref: S.patrouille_ref[z] = max(1, len(ids) - n)
    dec = S.decideur
    effort, premier = {}, {}
    for z in sorted(enq):
        ouv = [i for i in S.ouvertes.get(z, []) if S.affaires[i].etat == OUVERTE]
        if not ouv: continue
        charge = min(1.0, len(ouv) / (10.0 * max(1, len(enq[z]))))
        for ag in enq[z]:
            lot = ouv if len(ouv) <= LOT else [ouv[j] for j in sorted(rng.choice(len(ouv), LOT, replace=False).tolist())]
            cibles = [_designer(S, lot, c, jour) for c in range(len(CRITERES))]
            if len(set(cibles)) >= 2:
                traits = []
                for aid in cibles:
                    a = S.affaires[aid]
                    traits += [a.gravite, min(1.0, (jour - a.jour_plainte) / CLASSEMENT_J), min(1.0, preuve(a, jour))]
                traits += [len(lot) / LOT, charge]
                cle = S.prochaine_cle; S.prochaine_cle += 1
                choix = dec.decider(cle, ContexteEnquete(traits, cibles))
                aid = cibles[choix]
                S.decisions[cle] = [aid, 0.0, jour]
                S.dec_par_affaire.setdefault(aid, []).append(cle)
                p.compter("decision_enquete")
            else: aid = cibles[0]
            effort[aid] = effort.get(aid, 0) + 1
            premier.setdefault(aid, ag)
    for aid in sorted(effort):
        a = S.affaires[aid]
        a.effort += effort[aid]
        if rng.random() < p_elucider(Q_ENQUETE[a.type], preuve(a, jour), effort[aid]):
            _elucider(p, S, a, "enquete", rng, premier[aid])
    for z in sorted(S.ouvertes):
        garde = []
        for i in S.ouvertes[z]:
            a = S.affaires[i]
            if a.etat != OUVERTE: continue
            if jour - a.jour_plainte > CLASSEMENT_J: a.etat = CLASSEE; p.compter("classement"); continue
            garde.append(i)
        S.ouvertes[z] = garde


def _noter_enquetes(p):
    """23 h 50 : chaque choix d enquete d avant aujourd hui recoit ce qui est arrive a son affaire depuis la veille."""
    S = _dom(p); dec = S.decideur
    for cle in sorted(S.decisions):
        aid, val, j = S.decisions[cle]
        if j >= p.jour: continue
        dec.noter(cle, val, p.jour)
        S.decisions[cle][1] = 0.0
        att = dec.attentes.get(cle)
        if att is None or not att.choix:
            dec.attentes.pop(cle, None); del S.decisions[cle]
            lst = S.dec_par_affaire.get(aid)
            if lst is not None:
                lst.remove(cle)
                if not lst: del S.dec_par_affaire[aid]


# ================================================================== les autres domaines : ce qui devient une affaire
def _auteur_de_zone(p, S, z, fam, rng):
    """L auteur cache d une infraction qu un autre domaine a tiree ( un vol de vehicule ) : un habitant de la zone, au
    poids du jour."""
    J = S.ctx
    if J is None: J = S.ctx = _poids(p, S)
    sel = J.zone_h[J.ids] == z
    wv = J.poids[fam] * sel
    s = float(wv.sum())
    return int(J.ids[int(rng.choice(len(J.ids), p=wv / s))]) if s > 0 else -1


def _du_soir(p):
    """23 h : les vols de vehicules du jour ( domaine 14 ), les incendies criminels poses par d autres, les faillites
    du domaine 3, les successions contestees, les corruptions decouvertes."""
    S = _dom(p); w = p.w
    rng = p.du_jour("justice_soir")
    if p.a("transport"):
        vols = TRA._tr(p).vols
        for v in vols[S.vu_vols:]:
            vict = v.victime
            if type(vict).__name__ != "Menage": continue
            dm = int(p.w.table.menages.domicile[vict.id])
            z = int(w._marche_du_lieu[dm]) if dm >= 0 else -1
            if z < 0: continue
            t = IDX["vol_vehicule"]
            a = _nouvelle_affaire(p, S, t, z, w.carte.par_n[z].ile, _auteur_de_zone(p, S, z, ACQ, rng), rng)
            a.victime_m = vict.id; a.tort = float(v.valeur); a.ref = v.id
            S.vrais[t] += 1
            _enregistrer(p, S, a, rng, auteur_connu=False)
        S.vu_vols = len(vols)
    eco = p.domaine("economie")
    for r in eco.faillites[S.vu_faillites:]:
        d = _nouveau_dossier(p, S, "faillite", "civil", w.carte.iles[0])
        _jugement(p, S, d, "faillite", "faillite"); S.stats["faillites"] += 1; p.compter("faillite_jugee")
    S.vu_faillites = len(eco.faillites)
    d1 = p.domaine("population")
    nouveaux = d1.deces - S.deces_vus; S.deces_vus = d1.deces
    for _ in range(max(0, nouveaux)):
        if rng.random() < P_CONTESTATION:
            t = S.tribunaux[int(rng.integers(0, len(S.tribunaux)))]
            t.charge["civil"] += 1.0; S.stats["successions"] += 1; p.compter("succession_contestee")
    tb = w.table
    for c in S.corruptions:
        if c[5] or rng.random() >= P_DETECTION_J: continue
        c[5] = True
        agent = c[0]
        p.noter("corruption_decouverte", agent=agent, montant=round(c[2], 2))
        if not tb.vivant[agent]: continue
        dom = int(tb.domicile[agent]); z = int(w._marche_du_lieu[dom]) if dom >= 0 else -1
        t = IDX["corruption"]
        a = _nouvelle_affaire(p, S, t, z, w.carte.par_n[dom].ile if dom >= 0 else w.carte.iles[0], agent, rng)
        a.victime_o = w.gouv; a.tort = c[2]
        S.vrais[t] += 1
        _enregistrer(p, S, a, rng, auteur_connu=True)


def _fraudes_fiscales(p):
    """10 h 20, apres le controle fiscal : un redressement au-dela du seuil penal devient une affaire de fraude."""
    S = _dom(p); w = p.w; tb = w.table
    f = ET._etat(p).fisc
    rng = p.du_jour("justice_fraude")
    seuil = SEUIL_FRAUDE_PENALE_EUROS / EUROS
    for cle in sorted(k for k in f.controles if k > S.dernier_controle):
        S.dernier_controle = max(S.dernier_controle, cle)
        o = f.controles[cle]
        genre, cid = o.cible
        if genre != "menage" or o.redressement < seuil: continue
        adultes = [i for i in tb.menages.membres_ids(cid) if tb.vivant[i] and tb.statut[i] != PO.ABSENT
                   and (p.jour - p.col("habitant", "naissance_j")[i]) / JOURS_AN >= 18.0]
        if not adultes: continue
        dm = int(tb.menages.domicile[cid]); z = int(w._marche_du_lieu[dm]) if dm >= 0 else -1
        t = IDX["fraude_fiscale"]
        a = _nouvelle_affaire(p, S, t, z, w.carte.par_n[dm].ile, adultes[0], rng)
        a.victime_o = w.gouv; a.tort = 0.0; a.ref = cle
        S.vrais[t] += 1
        _enregistrer(p, S, a, rng, auteur_connu=True)


def _contrebande(p):
    """22 h, apres les passages du domaine 7 : une saisie est une affaire elucidee ( le reseau ), sanctionnee par la
    douane ; un passage non saisi reste au chiffre noir."""
    if not p.a("exterieur"): return
    S = _dom(p); w = p.w
    e = EXT._ext(p); lst = e.contrebande
    rng = p.du_jour("justice_contrebande")
    t = IDX["contrebande"]
    for jour, lieu, bien, q, valeur, saisi in lst[S.vu_contrebande:]:
        S.vrais[t] += 1
        if not saisi: p.compter("delit_non_declare"); continue
        l = w.carte.lieux[lieu]
        a = _nouvelle_affaire(p, S, t, l.n, l.ile, -1, rng)
        a.auteur_o = e.contrebandiers.get(l.ile); a.victime_o = w.gouv; a.tort = float(valeur)
        _enregistrer(p, S, a, rng, auteur_connu=True)
    S.vu_contrebande = len(lst)


# ================================================================== le droit civil
def _baux(p):
    """7 h, apres le matin du domaine 13 : chaque litige de bail ( trois termes impayes ) est porte au tribunal."""
    S = _dom(p); d13 = IM._dom(p)
    for bid in sorted(d13.litiges):
        if bid in S.baux_en_justice: continue
        bail = d13.baux.get(bid)
        if bail is None: continue
        dom = bail.locataire.domicile
        d = _nouveau_dossier(p, S, "bail", "baux", dom.ile if dom is not None else p.w.carte.iles[0])
        d.ref = bid; d.demandeur = IM.proprietaire(p, bail.b); d.defendeur = bail.locataire
        S.baux_en_justice[bid] = d.id
        _saisir(p, S, d)


def _juger_bail(p, S, d):
    """Le litige de bail : s il reste des loyers dus, expulsion ( par le domaine 13 ) et titre executoire sur les
    arrieres ; sinon l affaire est sans objet."""
    d13 = IM._dom(p); K = p.socle.creances
    S.baux_en_justice.pop(d.ref, None)
    loc, bailleur = d.defendeur, d.demandeur
    dus = [c for c in K.de(loc) if c.motif == "loyer" and c.creancier == bailleur] if bailleur is not None else []
    bail = d13.baux.get(d.ref)
    if not dus:
        _jugement(p, S, d, "baux", "sans_objet"); d.etat = SANS_OBJET
        if bail is not None and bail.litige_j >= 0: bail.litige_j = -1; d13.litiges.pop(d.ref, None)
        return
    _jugement(p, S, d, "baux", "expulsion")
    arr = math.fsum(c.montant for c in dus)
    if bail is not None and bail.locataire == loc and IM.expulser(p, d.ref, "jugement"):
        S.expulsions_jugees += 1; S.stats["expulsions"] += 1
        p.noter("expulsion_judiciaire", bail=d.ref, menage=loc.id, arrieres=round(arr, 2))
    for c in dus: _titre(S, c, p.jour)


def _titre(S, c, jour):
    if c.id not in S.titres:
        S.titres[c.id] = [c, jour, jour]; S.stats["titres"] += 1


def _radiations_avant(p):
    """18 h 10, avant la banque : les prets qui seront radies ce soir ( pour retrouver leur creance ) ."""
    S = _dom(p); bq = p.domaine("banques")
    S.a_radier = []
    for pid in sorted(bq.en_retard):
        pr = bq.prets.get(pid)
        if pr is not None and pr.defaut_j >= 0 and p.jour - pr.defaut_j >= BQ.RADIATION_J:
            S.a_radier.append((bq.banques[pr.banque], pr.emprunteur))


def _radiations_apres(p):
    """18 h 10, apres la banque : la creance d un pret radie ( motif recouvrement_pret ) passe en injonction de payer."""
    S = _dom(p); K = p.socle.creances
    for banque, emp in S.a_radier:
        for c in K.de(emp):
            if c.motif != "recouvrement_pret" or c.creancier is not banque or c.id in S.titres: continue
            dom = getattr(emp, "domicile", None) or getattr(emp, "lieu", None)
            d = _nouveau_dossier(p, S, "injonction", "injonction", dom.ile if dom is not None else p.w.carte.iles[0])
            d.ref = c.id; d.demandeur = banque; d.defendeur = emp
            S.titres[c.id] = None                      # en cours : pas deux fois
            _saisir(p, S, d)
    S.a_radier = []


def _juger_injonction(p, S, d):
    K = p.socle.creances
    c = K.actives.get(d.ref)
    S.titres.pop(d.ref, None)
    if c is None: _jugement(p, S, d, "injonction", "sans_objet"); d.etat = SANS_OBJET; return
    _jugement(p, S, d, "injonction", "titre")
    _titre(S, c, p.jour)


def _saisissable(p, deb):
    if type(deb).__name__ == "Menage":
        if p.col("menage", "dissous")[deb.id]: return 0.0
        return SAISIE_PART * IM.disponible(p, deb)
    return SAISIE_PART * max(0.0, float(getattr(deb, "caisse", 0.0)))


def _recouvrer_etat(p):
    """18 h 10, avant le fisc ( 18 h 20 ) : les interets de retard dus a l Etat, saisis d abord ( code civil art. 423 )."""
    S = _dom(p); K = p.socle.creances; L = p.socle.livre
    for cid in sorted(S.interets_etat):
        c = S.interets_etat[cid]
        if K.actives.get(cid) is not c: del S.interets_etat[cid]; continue
        deb = c.debiteur
        if type(deb).__name__ == "Menage" and p.col("menage", "dissous")[deb.id]:
            K.abandonner(c, "dissolution"); del S.interets_etat[cid]; continue
        x = min(c.montant, ET._saisissable(p, deb))
        if x > EPS: K.regler(c, L, x)


def _recouvrer(p):
    """18 h 30 : les creances sous titre executoire sont saisies ( un quart du disponible ), les interets d abord."""
    S = _dom(p); K = p.socle.creances; L = p.socle.livre
    reste = {}
    for passe in (0, 1):
        for cid in sorted(S.titres):
            e = S.titres[cid]
            if e is None: continue
            c = e[0]
            if K.actives.get(cid) is not c: del S.titres[cid]; continue
            if (c.motif in MOTIFS_INTERET) != (passe == 0): continue
            deb = c.debiteur
            if type(deb).__name__ == "Menage" and p.col("menage", "dissous")[deb.id]:
                K.abandonner(c, "dissolution"); del S.titres[cid]; continue
            cle = (type(deb).__name__, getattr(deb, "id", id(deb)))
            r = reste.get(cle)
            if r is None: r = reste[cle] = _saisissable(p, deb)
            x = min(r, c.montant)
            if x <= EPS: continue
            x = K.regler(c, L, x)
            reste[cle] = r - x
            S.stats["saisies"] += x; p.compter("saisie_civile", x)


def _interets(p):
    """0 h 50 : un trentieme des creances en justice chaque jour, les jours ecoules depuis leur dernier calcul :
    interet legal de retard ( civil ) et 0,73 % par mois ( Etat ). Interet simple, sur le principal restant."""
    S = _dom(p); K = p.socle.creances; j = p.jour; w = p.w
    tl = taux_legal(p); tf = TAUX_FISCAL_MOIS * 12.0
    for cid in sorted(S.titres):
        e = S.titres[cid]
        if e is None or cid % 30 != j % 30: continue
        c = e[0]
        if K.actives.get(cid) is not c or c.motif in MOTIFS_INTERET: continue
        jours = j - e[2]
        if jours <= 0: continue
        x = interet(c.montant, tl, jours)
        e[2] = j
        if x < 0.005: continue
        ci = K.constater(c.creancier, c.debiteur, x, "interet_moratoire", j)
        _titre(S, ci, j)
        S.interets_log.append((cid, c.montant, tl, jours, x))
        S.stats["interets_civils"] += x; p.compter("interet_moratoire", x)
    etat = ET.creances_de_l_etat(p)
    if p.a("transport"): etat += TRA.impayes_circulation(p)
    for c in sorted(etat, key=lambda x: x.id):
        if c.id % 30 != j % 30 or c.motif in MOTIFS_INTERET or c.creancier is not w.gouv: continue
        dernier = S.interet_j.get(c.id, c.nee)
        jours = j - dernier
        if jours <= 0: continue
        x = interet(c.montant, tf, jours)
        S.interet_j[c.id] = j
        if x < 0.005: continue
        ci = K.constater(w.gouv, c.debiteur, x, "interet_retard_fiscal", j)
        S.interets_etat[ci.id] = ci
        S.interets_log.append((c.id, c.montant, tf, jours, x))
        S.stats["interets_fiscaux"] += x; p.compter("interet_fiscal", x)
    if j % 30 == 0:
        S.interet_j = {k: v for k, v in S.interet_j.items() if k in K.actives}
        if len(S.interets_log) > 20000: del S.interets_log[:10000]


# ================================================================== le tribunal : la charge du jour
def _tribunaux(p):
    """11 h, avant les audiences : chaque file recoit son flux de fond ( les affaires que le pays ne simule pas une a
    une ) et perd la capacite du jour."""
    S = _dom(p)
    for t in S.tribunaux:
        for f in NOMS_FILES:
            t.charge[f] = max(0.0, t.charge[f] + t.fond[f] - _capacite(p, S, t, f))


# ================================================================== l argent du ministere
def _cout_jour(S):
    return ((len(S.juges_ids) * TRAITEMENT_JUGE_EUROS_MOIS + len(S.gardiens_ids) * SOLDE_GARDIEN_EUROS_MOIS)
            / EUROS / 30.4 + len(S.detentions) * C.NOURRITURE_PAR_JOUR * 10.0)


def _doter(p):
    """6 h : la dotation de l Etat remonte la caisse du ministere a dix jours de depenses."""
    S = _dom(p); sv = S.service; w = p.w
    manque = COUSSIN_J * _cout_jour(S) - sv.caisse
    if manque <= EPS: return
    ET.assurer(p, manque)
    sv.recu_etat += p.socle.livre.transferer(w.gouv, sv, manque, "dotation_justice")


def _paie(p):
    """23 h 40 : traitements des juges, soldes des gardiens, a leurs menages ( un detenu n est pas paye )."""
    S = _dom(p); w = p.w; tb = w.table; L = p.socle.livre; sv = S.service
    det = p.col("habitant", "ju_detenu")
    for ids, eur, motif, champ in ((S.juges_ids, TRAITEMENT_JUGE_EUROS_MOIS, "traitement_magistrat", "traitements"),
                                   (S.gardiens_ids, SOLDE_GARDIEN_EUROS_MOIS, "solde_gardien", "soldes")):
        x = eur / EUROS / 30.4
        for i in sorted(ids):
            if not tb.vivant[i] or det[i] or tb.menage[i] < 0: continue
            setattr(sv, champ, getattr(sv, champ) + L.transferer(sv, w.menages[int(tb.menage[i])], x, motif))


# ================================================================== la note et la cloture
def _cloture(p, comptes):
    S = _dom(p)
    S.ctx = None
    S.enr *= OUBLI_DISSUASION; S.elu *= OUBLI_DISSUASION


# ================================================================== installation
def _recruter(p, cand_mask, n, rng):
    ids = np.nonzero(cand_mask)[0]
    if n <= 0 or not len(ids): return []
    return sorted(int(i) for i in rng.choice(ids, min(n, len(ids)), replace=False))


def _detenus_initiaux(p, S, rng, J):
    """Le recensement penitentiaire : ~ 99 detenus pour 100 000 habitants, des hommes surtout, tires au poids des
    auteurs ; un quart en detention provisoire ( dossier en file des detenus ), les autres condamnes ( jugement ancien,
    reste de peine )."""
    w = p.w; tb = w.table; ch = p.colonnes["habitant"]
    n_res = int(((tb.vivant[:tb.n] == 1) & (tb.statut[:tb.n] != PO.ABSENT)).sum())
    n0 = int(round(DETENUS_PAR_100K * n_res / 1e5))
    wv = J.poids[ACQ] * (ch["sexe"][J.ids] == POP.HOMME)
    wv = wv * ~np.isin(J.ids, np.fromiter(S.juges_ids | S.gardiens_ids, np.int64, len(S.juges_ids | S.gardiens_ids)))
    s = float(wv.sum())
    if n0 <= 0 or s <= 0: return
    choisis = sorted(int(J.ids[j]) for j in rng.choice(len(J.ids), min(n0, int((wv > 0).sum())), replace=False, p=wv / s))
    noms = [c for c, _ in COMPOSITION_DETENUS]; pc = np.array([q for _, q in COMPOSITION_DETENUS]); pc /= pc.sum()
    for hid in choisis:
        nom = noms[int(rng.choice(len(noms), p=pc))]; t = IDX[nom]
        z = int(J.zone_h[hid]); ile = w.carte.par_n[z].ile
        a = _nouvelle_affaire(p, S, t, z, ile, hid, rng)
        a.jour = a.jour_plainte = p.jour - int(rng.integers(30, 400)); a.suspect = hid; a.etat = ELUCIDEE
        a.jour_elucide = a.jour
        S.affaires[a.id] = a
        d = Dossier(S.prochain_dossier, "penal", "criminel", ile, a.jour); S.prochain_dossier += 1
        S.dossiers[d.id] = d; d.affaire = a.id; d.prevenu = hid; d.coupable = True; d.preuve = min(1.0, 0.3 + a.preuve0)
        a.dossier = d.id
        if rng.random() < PART_PROVISOIRES:
            debut = p.jour - int(rng.integers(0, 300))
            o = S.prochaine_ordonnance; S.prochaine_ordonnance += 1
            S.ordonnances[o] = (hid, debut, debut + PROVISOIRE_MAX_J, d.id)
            det = _incarcerer(p, S, hid, PROVISOIRE, o, debut + PROVISOIRE_MAX_J); det.debut = debut
            cible = FILES["criminel_detenu"][1] - P_REPORT * FILES["criminel_detenu"][2]
            _saisir(p, S, d, "criminel_detenu", max(1.0, cible - (p.jour - debut)))
        else:
            pmin, pmax = PEINES[nom][0], PEINES[nom][1]
            duree = int(rng.integers(max(pmin, 180), max(pmin, 180, pmax) + 1))
            cond = int(round(LIBERATION_CONDITIONNELLE * duree))
            fait = int(rng.integers(0, max(1, cond)))
            d.etat = JUGE; a.etat = JUGEE
            J0 = Jugement(S.prochain_jugement, d.id, p.jour - fait, "criminel", "condamne", hid, t)
            S.prochain_jugement += 1; S.jugements[J0.id] = J0; d.jugement = J0.id
            J0.prison_j = duree
            S.peines.append((J0.id, hid, "prison", duree))
            ch["ju_casier"][hid] = 1
            det = _incarcerer(p, S, hid, PEINE, J0.id, p.jour + max(1, cond - fait)); det.debut = p.jour - fait


def installer(p):
    w = p.w; L = p.socle.livre; tb = w.table
    S = Justice()
    p.domaines["justice"] = S
    for m, nat in (("vol", "illegal"), ("restitution_vol", "illegal"), ("pot_de_vin", "illegal"),
                   ("dotation_justice", "transfert_courant"), ("dommages_interets", "transfert_courant"),
                   ("remboursement_amende", "transfert_courant"), ("traitement_magistrat", "remuneration"),
                   ("solde_gardien", "remuneration"), ("achat_penitentiaire", "achat"),
                   ("interet_moratoire", "revenu_propriete"), ("interet_retard_fiscal", "revenu_propriete")):
        L.declarer_motif(m, nat, "justice")
    Jn = p.socle.journal
    for t, champs in (("delit", ("affaire", "nature", "lieu", "declare")), ("arrestation", ("affaire", "suspect", "flagrant")),
                      ("jugement", ("dossier", "nature", "prevenu", "verdict", "peine", "instance")),
                      ("incarceration", ("habitant", "prison", "titre", "fin")), ("liberation", ("habitant", "prison", "motif")),
                      ("corruption_decouverte", ("agent", "montant")), ("expulsion_judiciaire", ("bail", "menage", "arrieres"))):
        Jn.declarer(t, "justice", "individuel", champs)
    for t in ("plainte", "delit_non_declare", "elucidation", "classement", "pot_de_vin", "restitution", "amende_penale",
              "saisie_civile", "interet_moratoire", "interet_fiscal", "audience", "report_audience", "appel",
              "erreur_judiciaire", "faillite_jugee", "succession_contestee", "repas_detenu", "detenu_affame",
              "decision_enquete", "sanction_douane"):
        Jn.declarer(t, "justice", "compte")
    ch = p.colonnes["habitant"]
    for nom, dt_, defaut in (("ju_casier", np.int16, 0), ("ju_detenu", np.int8, 0), ("ju_libere", np.uint8, 0),
                             ("ju_libere_j", np.int32, 0)):
        ch.ajouter(nom, dt_, defaut)
    ch.assurer(tb.n)
    p.socle.registre.inscrire("justice", "administrations", _membres_service, "caisse", None, "ServiceJustice")
    p.socle.registre.inscrire("prisons", "administrations", _membres_prisons, None, "stock", None)
    nl = len(w.carte.par_n)
    S.enr = np.zeros((2, nl)); S.elu = np.zeros((2, nl))
    rng = p.hasard("justice_installation")
    J = _poids(p, S)
    n_res = int(((tb.vivant[:tb.n] == 1) & (tb.statut[:tb.n] != PO.ABSENT)).sum())
    for fam in (ACQ, VIO): S.M0[fam] = max(EPS, float(J.poids[fam].sum()) / max(1, n_res))
    zh = J.zone_h
    pz = np.bincount(zh[(zh >= 0) & (tb.vivant[:tb.n] == 1)], minlength=nl)
    S.pop_zone = {int(z): int(pz[z]) for z in np.nonzero(pz)[0]}
    # un tribunal et une prison par ile, a la capitale la plus peuplee
    d13 = IM._dom(p)
    age = (p.jour - ch["naissance_j"][:tb.n]) / JOURS_AN
    libre = (tb.vivant[:tb.n] == 1) & (tb.statut[:tb.n] != PO.ABSENT) & ~np.isin(tb.role[:tb.n], PUBLICS) & (tb.menage[:tb.n] >= 0)
    ile_h = np.where(zh >= 0, w._ile_du_lieu[np.maximum(zh, 0)], -1)
    for k, ile in enumerate(w.carte.iles):
        caps = [c for c in w.carte.capitales if c.ile == ile]
        if not caps: continue
        cap = max(caps, key=lambda c: (pz[c.n], c.id))
        pop = int(pz[[c.n for c in caps]].sum())
        b = IM._nouveau(p, d13, "bureau_public", w.gouv, cap.id, 800.0, IM.annee(p) - 30, "initial", 0)
        t = Tribunal(len(S.tribunaux), ile, cap.id, b, pop)
        t.juges = _recruter(p, libre & (ile_h == k) & (age >= 30.0) & (age < 65.0), max(1, int(round(JUGES_PAR_100K * pop / 1e5))), rng)
        t.juges0 = max(1, len(t.juges)); S.juges_ids.update(t.juges)
        for f, (fond, cible, rep) in FILES.items():
            t.fond[f] = fond / 100.0 * pop / JOURS_AN
            simule = DETENUS_PAR_100K * PART_PROVISOIRES * pop / 1e5 / cible if f == "criminel_detenu" else 0.0
            for nom in NOMS:
                ti = IDX[nom]
                if f == ("criminel" if FELONIE[ti] else "correctionnel"):
                    simule += ENREGISTRES[ti] / 1e5 * pop / JOURS_AN * ELUC_GRECE[ti] * (1.0 - FLAGRANT[ti])
            t.capacite[f] = t.fond[f] + simule
            base = max(0.0, cible - P_REPORT * rep)
            t.charge[f] = t.capacite[f] * base
        S.tribunaux.append(t); S.tribunal_de_ile[ile] = t.id
        n_det = int(round(DETENUS_PAR_100K * pop / 1e5))
        places = max(1, int(round(n_det / OCCUPATION)))
        bp = IM._nouveau(p, d13, "caserne", w.gouv, cap.id, float(places * IM.M2_PAR_SOLDAT), IM.annee(p) - 40, "initial", 0)
        pr = Prison(len(S.prisons), ile, cap.id, cap.n, bp, IM.lits(p, bp) or places)
        pr.gardiens = _recruter(p, libre & (ile_h == k) & (age >= 22.0) & (age < 55.0) & ~np.isin(np.arange(tb.n), t.juges),
                                max(GARDIENS_MIN, int(round(GARDIENS_PAR_DETENU * n_det))), rng)
        S.gardiens_ids.update(pr.gardiens)
        S.prisons.append(pr); S.prison_de_ile[ile] = pr.id
    S.decideur = p.decideur(POINT_ENQUETE)
    p.echeance("justice_audience", _audience)
    _detenus_initiaux(p, S, rng, J)
    IM.rendre_la_justice(p)
    S.expulsions0 = int(d13.stats["expulsions"])
    S.deces_vus = p.domaine("population").deces
    S.vu_faillites = len(p.domaine("economie").faillites)
    S.dernier_controle = max(ET._etat(p).fisc.controles, default=-1)
    if p.a("transport"): S.vu_vols = len(TRA._tr(p).vols)
    if p.a("exterieur"): S.vu_contrebande = len(EXT._ext(p).contrebande)
    p.routine(0.5, 50, "justice", _delits)
    p.routine(40 / 60, 50, "justice", _prisons_matin)
    p.routine(50 / 60, 50, "justice", _interets)
    p.routine(6.0, 70, "justice", _doter)
    p.routine(7.0, 50, "justice", _baux)
    p.routine(10.0, 50, "justice", _enquetes)
    p.routine(10 + 20 / 60, 50, "justice", _fraudes_fiscales)
    p.routine(HEURE_AUDIENCE - 10 / 60, 50, "justice", _tribunaux)
    p.routine(18 + 10 / 60, 10, "justice", _radiations_avant)
    p.routine(18 + 10 / 60, 30, "justice", _radiations_apres)
    p.routine(18 + 10 / 60, 50, "justice", _recouvrer_etat)
    p.routine(18.5, 50, "justice", _recouvrer)
    p.routine(19.5, 50, "justice", _vivres_achat)
    p.routine(20 + 10 / 60, 50, "justice", _vivres_repas)
    p.routine(22.0, 50, "justice", _contrebande)
    p.routine(23.0, 50, "justice", _du_soir)
    p.routine(23 + 40 / 60, 50, "justice", _paie)
    p.routine(23 + 50 / 60, 50, "justice", _noter_enquetes)
    p.cloture("justice", _cloture)
    _doter(p)
    return S


# ================================================================== controles ( pour les portes )
def audit(p):
    """Les anomalies : detenu sans titre valide, titre echu, detenu au travail ou chez lui, peine executee sans
    condamnation a son nom, expulsion du domaine 13 sans jugement. Vide : tout est en ordre."""
    S = _dom(p); w = p.w; tb = w.table; n = tb.n
    col = p.col("habitant", "ju_detenu")
    out = {"detenu_sans_titre": [], "titre_echu": [], "detenu_au_travail": [], "detenu_chez_lui": [],
           "peine_sans_jugement": [], "expulsion_sans_jugement": 0, "fiche_sans_detenu": []}
    for i in np.nonzero(col[:n] > 0)[0].tolist():
        det = S.detentions.get(i)
        if det is None: out["detenu_sans_titre"].append(i); continue
        if det.titre == PEINE:
            J = S.jugements.get(det.ref)
            if J is None or J.verdict != "condamne" or J.personne != i or J.prison_j <= 0 or J.sursis:
                out["detenu_sans_titre"].append(i)
        else:
            o = S.ordonnances.get(det.ref)
            if o is None or o[0] != i: out["detenu_sans_titre"].append(i)
            elif p.jour > o[2]: out["titre_echu"].append(i)
        if tb.vivant[i]:
            if tb.travail[i] >= 0: out["detenu_au_travail"].append(i)
            if tb.statut[i] != PO.ABSENT or tb.domicile[i] != S.prisons[det.prison].lieu_n: out["detenu_chez_lui"].append(i)
    for hid in S.detentions:
        if col[hid] == 0: out["fiche_sans_detenu"].append(hid)
    for jid, hid, genre, x in S.peines:
        J = S.jugements.get(jid)
        if J is None or J.verdict not in ("condamne", "sanction_administrative") or (hid >= 0 and J.personne != hid):
            out["peine_sans_jugement"].append((jid, hid, genre))
    out["expulsion_sans_jugement"] = int(IM._dom(p).stats["expulsions"]) - S.expulsions0 - S.expulsions_jugees
    return out


def audit_propre(a): return not any(a.values())


# ================================================================== API pour les autres domaines
def scenario(p, **facteurs):
    """Scenarios et portes : `crime` ( tous les types tires ), un nom de type, `police` ( enqueteurs ), `juges`,
    `reports` ( part des audiences reportees )."""
    S = _dom(p)
    for k, v in facteurs.items():
        if not 0.0 <= v < 1e6: raise ValueError(f"facteur invalide {k}={v!r}")
        if k == "crime": S.facteur[:] = float(v)
        elif k in IDX: S.facteur[IDX[k]] = float(v)
        elif k == "police": S.effort = float(v)
        elif k == "juges": S.facteur_juges = float(v)
        elif k == "reports": S.p_report = min(1.0, float(v))
        else: raise ValueError(f"facteur inconnu {k!r}")


def vider_les_files(p):
    """Scenario : une justice sans arriere ( les dossiers deposes sont juges au premier jour ouvre ) ."""
    for t in _dom(p).tribunaux:
        for f in t.charge: t.charge[f] = 0.0


def deposer_plainte(p, type_, auteur=-1, victime_menage=-1, victime=None, gravite=None, preuve_=None, tort=0.0,
                    flagrant=False, auteur_connu=True, auteur_objet=None):
    """Domaines 20 ( fraude a l assurance ), 27 ( infraction militaire ), scenarios et portes : une infraction
    enregistree maintenant. L auteur est la verite ; `auteur_connu` : la victime le designe ( elucidee d emblee ).
    Rend l Affaire."""
    S = _dom(p); w = p.w; tb = w.table
    if type_ not in IDX: raise ValueError(f"type inconnu {type_!r}")
    rng = p.hasard("justice_plaintes")
    t = IDX[type_]
    dom = int(tb.domicile[auteur]) if auteur >= 0 else -1
    if dom < 0 and victime_menage >= 0: dom = int(tb.menages.domicile[victime_menage])
    z = int(w._marche_du_lieu[dom]) if dom >= 0 else w.carte.capitales[0].n
    a = _nouvelle_affaire(p, S, t, z, w.carte.par_n[z].ile, auteur, rng)
    if gravite is not None: a.gravite = float(gravite)
    if preuve_ is not None: a.preuve0 = float(preuve_)
    a.victime_m = victime_menage; a.victime_o = victime; a.tort = float(tort); a.auteur_o = auteur_objet
    S.vrais[t] += 1
    return _enregistrer(p, S, a, rng, flagrant=flagrant, auteur_connu=auteur_connu)


def juger_militaire(p, habitant, infraction="militaire", gravite=0.5, preuve_=0.8):
    """Domaine 27 : un militaire poursuivi devant le tribunal militaire ( delai DELAI_MILITAIRE_J ) ; les peines de
    prison s executent dans les prisons du pays. Rend l Affaire."""
    return deposer_plainte(p, "militaire", auteur=habitant, gravite=gravite, preuve_=preuve_, auteur_connu=True)


def signaler_fraude_assurance(p, assure, assureur, montant, preuve_=0.6, vraie=True):
    """Domaine 20 : un sinistre suspect. `assure` : l habitant qui a declare ; `vraie` : la verite ( une fausse alerte
    designe un innocent ). Le tort est dommageable a l assureur ( partie civile ). Rend l Affaire."""
    S = _dom(p); w = p.w; tb = w.table
    rng = p.hasard("justice_plaintes")
    t = IDX["fraude_assurance"]
    dom = int(tb.domicile[assure])
    z = int(w._marche_du_lieu[dom]) if dom >= 0 else w.carte.capitales[0].n
    a = _nouvelle_affaire(p, S, t, z, w.carte.par_n[z].ile, assure if vraie else -1, rng)
    a.preuve0 = float(preuve_); a.victime_o = assureur; a.tort = float(montant); a.ref = assure
    if vraie: S.vrais[t] += 1
    return _enregistrer(p, S, a, rng, auteur_connu=False)


def affaires(p, depuis_j=0, type_=None, etat=None):
    """Les affaires enregistrees depuis `depuis_j` ( sans l auteur vrai ) : dictionnaires."""
    S = _dom(p); t = IDX.get(type_, -1) if type_ is not None else None
    return [{"id": a.id, "type": NOMS[a.type], "jour": a.jour_plainte, "zone": a.zone, "ile": a.ile, "gravite": a.gravite,
             "tort": a.tort, "restitue": a.restitue, "etat": ETATS[a.etat], "flagrant": a.flagrant,
             "suspect": a.suspect, "victime_menage": a.victime_m, "dossier": a.dossier}
            for a in S.affaires.values() if a.jour_plainte >= depuis_j and (t is None or a.type == t)
            and (etat is None or ETATS[a.etat] == etat)]


def sinistres_criminels(p, depuis_j=0):
    """Domaine 20 ( assurances ) : les infractions qui touchent un bien assurable - cambriolages, vols, vols de
    vehicules, incendies criminels - avec leur victime, leur tort, ce qui a ete rendu, le sinistre du domaine 18."""
    S = _dom(p)
    types = {IDX[n] for n in ("vol_simple", "cambriolage", "vol_violence", "vol_vehicule", "incendie_criminel")}
    return [{"affaire": a.id, "type": NOMS[a.type], "jour": a.jour, "victime_menage": a.victime_m, "tort": a.tort,
             "restitue": a.restitue, "sinistre_18" if NOMS[a.type] == "incendie_criminel" else "vol_14": a.ref,
             "etat": ETATS[a.etat]}
            for a in S.affaires.values() if a.type in types and a.jour_plainte >= depuis_j]


def affaires_publiables(p, depuis_j=0):
    """Domaine 22 ( medias ) : ce que la presse peut savoir - plaintes, arrestations, jugements, corruptions
    decouvertes, relaxes en appel. Jamais le chiffre noir ni l auteur vrai."""
    S = _dom(p); out = []
    for a in S.affaires.values():
        if a.jour_plainte >= depuis_j:
            out.append({"jour": a.jour_plainte, "quoi": "plainte", "affaire": a.id, "type": NOMS[a.type], "zone": a.zone,
                        "gravite": a.gravite})
        if a.jour_elucide >= depuis_j and a.suspect >= 0:
            out.append({"jour": a.jour_elucide, "quoi": "arrestation", "affaire": a.id, "type": NOMS[a.type],
                        "suspect": a.suspect, "flagrant": a.flagrant})
    for J in S.jugements.values():
        if J.jour >= depuis_j and J.personne >= 0:
            out.append({"jour": J.jour, "quoi": "jugement", "dossier": J.dossier, "instance": J.juridiction,
                        "verdict": J.verdict, "prison_j": J.prison_j, "sursis": J.sursis, "amende": J.amende,
                        "personne": J.personne, "infirme_en_appel": not J.definitif and not J.appel})
    for c in S.corruptions:
        if c[5] and c[4] >= depuis_j:
            out.append({"jour": c[4], "quoi": "corruption", "agent": c[0], "montant": c[2]})
    return sorted(out, key=lambda e: (e["jour"], e["quoi"]))


def indicateurs(p, fenetre_j=365):
    """Domaine 24 ( confiance, opinion ) : ce que la statistique judiciaire publie - infractions enregistrees ( pour
    100 000 et par an, sur la fenetre ), elucidation par type, delais prevus par file, detenus et surpopulation,
    corruptions decouvertes, condamnations infirmees en appel. Pas le chiffre noir."""
    S = _dom(p); w = p.w; tb = w.table
    j0 = p.jour - fenetre_j
    n = max(1, int((tb.vivant[:tb.n] == 1).sum()))
    enr = np.zeros(NT); elu = np.zeros(NT)
    for a in S.affaires.values():
        if a.jour_plainte >= j0:
            enr[a.type] += 1
            if a.etat in (ELUCIDEE, JUGEE) or (a.etat == ENTERREE): elu[a.type] += 1
    duree = max(1, min(fenetre_j, p.jour - (min((a.jour_plainte for a in S.affaires.values()), default=p.jour)) + 1))
    places = sum(pr.places for pr in S.prisons)
    return {"enregistrees_100k_an": {NOMS[t]: enr[t] / n * 1e5 * JOURS_AN / duree for t in range(NT)},
            "elucidation": {NOMS[t]: (elu[t] / enr[t] if enr[t] else None) for t in range(NT)},
            "delais": {f: round(delai_prevu(p, f), 1) for f in NOMS_FILES},
            "detenus": len(S.detentions), "places": places, "surpopulation": len(S.detentions) / max(1, places),
            "provisoires": sum(1 for d in S.detentions.values() if d.titre == PROVISOIRE),
            "corruptions_decouvertes": sum(1 for c in S.corruptions if c[5]),
            "infirmations": S.stats["infirmations"], "condamnations": S.stats["condamnations"]}


def verite(p):
    """Pour les portes seulement : infractions commises ( chiffre noir compris ), enregistrees, elucidees, par type ;
    corruptions cachees ; erreurs judiciaires."""
    S = _dom(p)
    return {"vrais": {NOMS[t]: int(S.vrais[t]) for t in range(NT)},
            "enregistres": {NOMS[t]: int(S.enregistres[t]) for t in range(NT)},
            "elucides": {NOMS[t]: int(S.elucides[t]) for t in range(NT)},
            "corruptions_cachees": sum(1 for c in S.corruptions if not c[5]),
            "innocents_condamnes": S.stats["innocents_condamnes"], "coupables_relaxes": S.stats["coupables_relaxes"]}


def casier(p, habitant):
    """Domaines 4 ( embauche ), 25 ( recrutement ) : condamnations inscrites, detenu ou non."""
    return int(p.col("habitant", "ju_casier")[habitant]), int(p.col("habitant", "ju_detenu")[habitant])


def detenus(p):
    """Le pont, les domaines 24 et 27 : ( habitant, prison, titre, fin ) ."""
    S = _dom(p)
    return [(h, d.prison, "provisoire" if d.titre == PROVISOIRE else "peine", d.fin) for h, d in sorted(S.detentions.items())]


def titre_executoire(p, creance):
    """Un creancier qui a deja un titre ( un jugement d un autre domaine ) : la creance entre au recouvrement force."""
    _titre(_dom(p), creance, p.jour)
