"""DOMAINE 4 - TRAVAIL ET METIERS : CONTRATS, SALAIRES, QUALIFICATIONS, CARRIERES, CHOMAGE, SYNDICATS, GREVES, RETRAITE.

FICHE
1. Classes. CaisseSecuriteSociale ( la caisse unique, modele e-EFKA + DYPA : cotisations, pensions, indemnites ;
   tenue a la banque centrale, comme les reserves des caisses grecques ), Syndicat ( deux confederations, GSEE pour
   le prive, ADEDY pour le public : cotisations retenues sur la paie, allocations de greve ; comptes dans une banque
   commerciale ), Pension, Indemnite, Greve, Etablissement ( un employeur qui n est pas une entreprise du moteur : un
   service public en un lieu, ou un employeur declare par un autre domaine ), Offre et ContexteOffre ( ce qu un
   candidat voit ), Travail ( l etat du domaine ), RemplacePaie et RemplaceEmbaucher ( les methodes du moteur reprises,
   en objets picklables ). Par habitant, en COLONNES ( p.colonnes["habitant"] ) : tr_statut, tr_contrat, tr_debut_j,
   tr_fin_j, tr_taux, tr_heures_prevues, tr_carriere, tr_carriere_j, tr_echelon, tr_jours_cotises, tr_assiette,
   tr_qualifs, tr_syndique, tr_pointage, tr_solde_heures, tr_jours_mois, tr_imposable_an, tr_net_jour, tr_chomage_j,
   tr_fin_etudes. Colonnes plutot que table eparse : contrat, carriere, titres concernent tous les adultes ( 40 % des
   habitants ont un emploi, 80 % une carriere ) ; ~ 75 octets par habitant en colonnes contre ~ 250 par entree de
   dictionnaire, et la paie se calcule en vecteurs. Les dates ne valent que sous leur drapeau ( tr_carriere, le type de
   contrat, le statut ) : une carriere reconstituee commence a une date negative. Tables eparses pour ce que peu
   portent : pensions, indemnites, grevistes, employeurs declares, postes ouverts, effectifs vises.
2. Invariants. Pour chaque bulletin, au centime : brut = net verse + cotisation salariale + impot retenu + cotisation
   syndicale ; l argent qui bouge a la paie est celui des bulletins. Ce qui n est pas paye devient une creance nommee du
   socle ( salaire, cotisation, impot, cotisation syndicale ; pension en retard ), reglee d abord a la paie suivante :
   jamais un salaire qui n a pas existe. Caisse : variation = cotisations recues + financement de l Etat - prestations -
   reserves placees aupres de l Etat ( creance de la caisse sur l Etat, rappelee quand elle manque ). Heures payees =
   heures travaillees : a chaque pas le domaine pointe qui est a son poste ou au volant d un convoi ; une heure
   creditee sans pointage ( au-dela d un aller-retour de convoi ) est une anomalie vue. Un contrat qui finit dans la
   journee paie ses heures faites ( solde de tout compte ). Le domaine DETIENT de l argent ( familles
   `securite_sociale` et `syndicats` du registre, parties de zero ), aucun bien.
3. Decision `accepter_emploi` ( chaque matin a 6 h 20, pour chaque offre faite a un chomeur ou a un salarie qui
   cherche ; chaque poste vacant est offert aux 3 candidats titres les plus proches, un par un ) : refuser ou accepter.
   Traits : salaire net propose, revenu net actuel ( salaire ou indemnite ), distance, qualification ( son metier ou
   une reconversion ), jours de chomage, caisse du menage, stabilite offerte, stabilite actuelle, en emploi. Note
   ( horizon 7 jours : une semaine de travail, week-end compris - avec l agenda la paie ne tombe que les jours ouvres ) :
   chaque soir, ( revenu net de CE travailleur ce jour-la sur deux SMIC nets + son menage a mange + stabilite de sa
   situation ) / 3. Regle : un chomeur accepte ce qui paie plus que son indemnite a moins de 40 km ; un salarie change
   pour 10 % de plus a stabilite au moins egale, ou quand son CDD finit dans le mois. Temoin : tout accepter.
4. Evenements. Individuels : retraite_liquidee, greve_debut, greve_fin, fin_etudes, accident_mortel. Comptes :
   offre_emploi, offre_acceptee, offre_refusee, promotion, fin_cdd, cdd_renouvele, indemnite_ouverte, accident_travail,
   heures_non_travaillees, arrieres_salaire.
5. Liens. Lit la population ( sexe, naissance, conjoint : domaine 1 ), l economie ( embaucher, licencier, offres,
   comptes, capital par poste : domaine 3 ), l indice des prix et l avance au Tresor ( banques, domaine 2 ), l agenda
   s il est la ( replanifier ), la medecine si elle est la ( `blesser( p, h, cause, gravite )`, a confirmer par le
   domaine 16 ). Paie et recoit : salaires ( employeurs -> menages ), cotisations ( employeurs et independants ->
   caisse ), impot retenu a la source ( employeurs -> Etat, au taux du moteur tant que le domaine 6 ne pose pas son
   bareme ; l Etat se le retient a lui-meme en le montrant au grand livre ), cotisations syndicales, pensions et
   indemnites ( caisse -> menages ), part nationale des pensions et deficit ( Etat -> caisse ), reserves placees et
   rappelees ( caisse <-> Etat ), allocations de greve ( syndicats -> menages ), revenus des independants ( marches et
   cooperatives -> menages, comme le moteur ; dividendes au domaine 3 ). Remplace Monde.paie et Monde.embaucher
   ( proprietaire ) ; garde le contrat d appel `w.embaucher( h )` du domaine 1 ( a 16 ans et plus, au demenagement ).
   Neutralise par une donnee : l activite d un etablissement en greve ( 0, reposee apres la regle de l aube ). Une
   offre d emploi du domaine 3 n est pourvue que dans la limite des postes de travail de l entreprise ( son capital sur
   le capital d un poste ) : sans machine, un ouvrier de plus ne produit rien.
6. Portes : tests_d04_travail.py.
7. Arma : aucun objet. Un greviste reste chez lui ( horaire vide ) : la bulle ne le trouve pas a l usine.
8. Cout ( mesure du 23/09, test_cout, 10 004 habitants ) : routines propres ~ 95 ms par jour, 5 % d une journee du
   moteur, ~ 9,5 us par habitant ; le pays avec le travail coute autant que sans ( 1,66 s contre 1,66 s par jour : les
   inactifs allegent les boucles du moteur ). Pointage : une passe sur les salaries a chaque pas ( ~ 100 ns chacun,
   l essentiel du cout ) ; paie : une passe sur les habitants, des vecteurs, un paiement par salarie et trois par
   employeur ; marche du travail : une passe par jour pour les candidats, puis le nombre d offres ; carrieres :
   vecteurs. Lineaire en habitants : ~ 10 s par jour a 1 million, ~ 8 min a 50 millions avant portage en Rust."""
import importlib, math
from collections import deque
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D
from . import d01_population as POP, d02_banques as BQ, d03_economie as ECO

JOURS_AN = 365.0
MOIS_J = 30
TOL = 1e-9

# ================================================================== la conversion des euros en drachmes
# Deux ancres, qui s accordent : ( 1 ) la ration du moteur vaut 4 drachmes ( config.PRIX_MONDE ) ; un Grec depense
# pour se nourrir 1 685,28 euros par mois et par menage x 20,7 % / 2,5 personnes / 30,4 jours = 4,59 euros par jour
# ( ELSTAT, enquete budget des menages 2023 ) : 1 drachme = 1,15 euro ; ( 2 ) l ouvrier du moteur gagne 8 drachmes de
# l heure, soit 9,2 euros : l ordre du salaire brut moyen d un ouvrier grec, primes de Paques, de Noel et de conges
# comprises ( a calibrer ). Les deux disent 1 drachme = 1,15 euro.
EUROS_PAR_DRACHME = 1.15
# Salaire minimum grec : 830 euros par mois ( employes ) et 37,07 euros par jour ( ouvriers ) au 1er avril 2024,
# verses 14 fois par an ( OCDE, TaxBEN Grece 2024 ). Horaire : 830 x 14 / 12 / 173,33 h = 5,59 euros = 4,86 drachmes.
SMIC_MENSUEL_EUR = 830.0
SMIC_JOUR_OUVRIER_EUR = 37.07
HEURES_MOIS_LEGALES = 40.0 * 52.0 / 12.0
SMIC_HORAIRE = SMIC_MENSUEL_EUR * 14.0 / 12.0 / HEURES_MOIS_LEGALES / EUROS_PAR_DRACHME

# ================================================================== les cotisations sociales ( e-EFKA, 2024 )
# OCDE, TaxBEN Grece 2024, tableau des cotisations : salarie 13,87 % ( retraite principale 6,67 + complementaire 3,00
# + sante 2,55 + autres 1,65 ), employeur 22,29 % ( 13,33 + 3,00 + 4,55 + 1,41 ). Au 1er janvier 2025 : 13,37 % et
# 21,79 %. Plafond mensuel de 7 572,62 euros : aucun metier du moteur ne l atteint ( le chef du gouvernement gagne
# ~ 5 900 drachmes par mois ) ; non modelise tant qu il ne mord pas.
COTISATIONS_SALARIE = {"retraite": 0.0967, "sante": 0.0255, "autres": 0.0165}
COTISATIONS_EMPLOYEUR = {"retraite": 0.1633, "sante": 0.0455, "autres": 0.0141}
TAUX_SALARIE = sum(COTISATIONS_SALARIE.values())       # 0,1387
TAUX_EMPLOYEUR = sum(COTISATIONS_EMPLOYEUR.values())   # 0,2229
# Independants : une cotisation MENSUELLE fixe par categorie ( e-EFKA ). Ordres de grandeur 2024 : ~ 239 euros pour la
# premiere categorie des professions liberales et commercants, ~ 110 euros pour les agriculteurs ( ex-OGA ) : a
# calibrer. La part retraite ( ~ 65 %, a calibrer ) divisee par 0,20 donne le salaire de reference de la pension
# ( fiche Grece du rapport sur le vieillissement 2024, Commission europeenne ).
COTISATION_INDEPENDANT_MOIS = {"paysan": 110.0 / EUROS_PAR_DRACHME, "marchand": 238.87 / EUROS_PAR_DRACHME,
                               "patron": 238.87 / EUROS_PAR_DRACHME}
PART_RETRAITE_INDEPENDANT = 0.65
DIVISEUR_ASSIETTE_INDEPENDANT = 0.20

# ================================================================== les jours d assurance
# 25 jours d assurance font un mois, 300 une annee ; une semaine de 5 jours compte 6/5 ( regle grecque de conversion ),
# au plus 25 jours par mois.
JOURS_ASSURANCE_MOIS = 25.0
JOURS_ASSURANCE_AN = 300.0
CREDIT_JOUR_PAYE = 6.0 / 5.0

# ================================================================== la retraite ( loi 4387/2016, bareme de la loi 4670/2020 )
# Fiche Grece du rapport sur le vieillissement 2024 ( Commission europeenne, decembre 2023 ) : age legal 67 ans, ou 62
# ans avec 40 ans d assurance ( 12 000 jours ) ; minimum 15 ans ( 4 500 jours ) ; depart anticipe a 62 ans avec 15 ans,
# penalite de 1/200 par mois d avance ( au plus 60 mois ). Pension nationale 384 euros ( 413,76 au 1er janvier 2023 )
# pour 20 ans d assurance, moins 2 % par annee manquante jusqu a 15 ans ; financee par l Etat. Pension contributive :
# salaire de reference ( gains cotises / periode d assurance, en mois ) x taux marginaux par tranche d annees.
AGE_LEGAL = 67.0
AGE_ANTICIPE = 62.0
JOURS_CARRIERE_COMPLETE = 12000.0
JOURS_MINIMUM = 4500.0
JOURS_INVALIDITE = 1500.0          # une pension d invalidite demande 1 500 jours d assurance ( a verifier )
PENSION_NATIONALE = 413.76 / EUROS_PAR_DRACHME
ANNEES_NATIONALE_PLEINE = 20.0
BAISSE_NATIONALE_AN = 0.02
BAREME_ANNUITES = ((15.0, 0.0077), (18.0, 0.0084), (21.0, 0.0090), (24.0, 0.0096), (27.0, 0.0103), (30.0, 0.0121),
                   (33.0, 0.0198), (36.0, 0.0250), (40.0, 0.0255), (math.inf, 0.0050))
PENALITE_PAR_MOIS = 1.0 / 200.0
PENALITE_MOIS_MAX = 60
PART_INVALIDITE = 0.75             # invalidite de 67 a 79 % : 75 % de la pension ( a calibrer par degre )
ALLOCATION_NON_ASSURE = 387.90 / EUROS_PAR_DRACHME   # OPEKA, 67 ans et moins de 15 ans d assurance ( 2023 ), sous
                                                      # condition de ressources ( condition non modelisee ) ; sert aussi
                                                      # d allocation d invalidite non contributive ( a calibrer par degre )

# ================================================================== le chomage ( DYPA ; OCDE, TaxBEN Grece 2024, 2.1 )
# Indemnite de base : 55 % du salaire minimum journalier de l ouvrier, 25 jours par mois, + 10 % par personne a charge ;
# ouverte a qui a perdu son emploi contre son gre ; 125 jours de travail dans les 14 mois ( les 2 derniers exclus ) ;
# duree selon ces jours : 125-149 : 5 mois, 150-179 : 6, 180-219 : 8, 220-249 : 10, 250 et plus : 12. Carence de 6 jours.
INDEMNITE_JOUR = 0.55 * SMIC_JOUR_OUVRIER_EUR / EUROS_PAR_DRACHME * 25.0 * 12.0 / JOURS_AN   # par jour calendaire
MAJORATION_A_CHARGE = 0.10
CARENCE_J = 6
DUREES_INDEMNITE = ((125.0, 0), (150.0, 5), (180.0, 6), (220.0, 8), (250.0, 10), (math.inf, 12))
FENETRE_14_MOIS_J = 14 * MOIS_J
EXCLUS_2_MOIS_J = 2 * MOIS_J

# ================================================================== les carrieres
# Grille publique : loi 4354/2015, 19 echelons de 2 ans ( ~ +3,5 % chacun, a calibrer ). Prive : triennales de la
# convention collective nationale, +10 % par tranche de 3 ans, 3 au plus ( a calibrer ). Le salaire du moteur
# ( population.SALAIRE_HORAIRE ) est celui de l echelon 0 ; jamais sous le SMIC.
GRILLE_PUBLIQUE = (2.0, 0.035, 19)
GRILLE_PRIVEE = (3.0, 0.10, 3)
HEURES_HORAIRE = {"jour": 8.0, "bureau": 9.0, "garde": 8.0, "marche": 11.0, "nuit": 8.0, "ecole": 7.0}
# Contrats : 11 % des salaries grecs en contrat temporaire ( Eurostat, ordre de grandeur, a calibrer ) ; une embauche
# sur trois en CDD ( a calibrer ) ; des CDD successifs au-dela de 2 ans deviennent un CDI ( decret 81/2003 ).
PART_CDD_RECENSEMENT = 0.11
PART_CDD_EMBAUCHE = 0.35
DUREE_CDD_J = (90, 365)
RENOUVELLEMENT_CDD = 0.7
CDD_VERS_CDI_J = 730

# ================================================================== la population active au recensement
# Eurostat : taux d emploi des 20-64 ans en Grece de 62,6 % en 2021 ( 67,4 % en 2023, ~ 71 % en 2025 ), ecart
# hommes-femmes de 18 a 21 points. Taux par sexe et par age ci-dessous : a calibrer, construits pour retrouver
# ~ 72,6 % chez les hommes et ~ 52,4 % chez les femmes de 20 a 64 ans ( 62,5 % a sexes egaux ). Colonnes : emploi,
# chomage, etudes, au foyer, invalidite, retraite anticipee ; le reste : decourages ( inactifs qui voudraient un emploi ).
HOMME, FEMME = POP.HOMME, POP.FEMME
STATUTS_RECENSEMENT = (
    (16, 20, {HOMME: (0.05, 0.03, 0.90, 0.00, 0.01, 0.00), FEMME: (0.03, 0.03, 0.92, 0.01, 0.01, 0.00)}),
    (20, 25, {HOMME: (0.38, 0.14, 0.42, 0.01, 0.01, 0.00), FEMME: (0.30, 0.14, 0.47, 0.04, 0.01, 0.00)}),
    (25, 35, {HOMME: (0.76, 0.14, 0.03, 0.01, 0.02, 0.00), FEMME: (0.60, 0.17, 0.03, 0.14, 0.02, 0.00)}),
    (35, 45, {HOMME: (0.85, 0.09, 0.00, 0.01, 0.03, 0.00), FEMME: (0.64, 0.12, 0.00, 0.19, 0.02, 0.00)}),
    (45, 55, {HOMME: (0.83, 0.09, 0.00, 0.01, 0.04, 0.00), FEMME: (0.60, 0.11, 0.00, 0.23, 0.03, 0.00)}),
    (55, 65, {HOMME: (0.62, 0.07, 0.00, 0.01, 0.08, 0.18), FEMME: (0.37, 0.06, 0.00, 0.31, 0.06, 0.18)}),
)
CIBLE_EMPLOI_20_64 = 0.626
# Fin des etudes : age de sortie et probabilite ( taux de diplomes du superieur de 30-34 ans ~ 44 %, a calibrer ).
SORTIE_ETUDES = ((17.0, 0.08), (18.5, 0.35), (22.0, 0.35), (24.0, 0.17), (27.0, 0.05))
# Carriere reconstituee : age d entree et densite de cotisation ( lacunes, travail non declare : a calibrer ).
ENTREE_CARRIERE = {"populaire": (18.0, 23.0), "moyenne": (21.0, 25.0), "aisee": (23.0, 28.0)}
DENSITE_COTISATION = {HOMME: (0.70, 0.95), FEMME: (0.55, 0.90)}
METIER_DE_CLASSE = {"populaire": "ouvrier", "moyenne": "enseignant", "aisee": "officier"}   # salaire des retraites
DUREE_CHOMAGE_RECENSEMENT_J = (0, 720)   # les chomeurs du recensement le sont depuis 0 a 2 ans ( ~ 60 % de longue duree )

# ================================================================== les qualifications
# Un medecin ou un officier ne s improvise pas : le metier exige un titre. Certaines formations se donnent a
# l embauche ( securite de la mine, de l industrie ). Le service militaire des hommes grecs donne la formation
# militaire ( ~ 85 % des hommes, a calibrer ). Le domaine 19 ( education ) accordera les titres ; en attendant, une
# sortie d etudes superieures en tire un au hasard ( TITRES_DE_SORTIE, a calibrer, a retirer quand le domaine 19 est la ).
QUALIFICATIONS = ("formation_militaire", "ecole_officiers", "ecole_police", "diplome_medecine", "diplome_infirmier",
                  "diplome_enseignant", "permis_poids_lourd", "securite_mine", "securite_industrie")
BIT = {q: 1 << k for k, q in enumerate(QUALIFICATIONS)}
EXIGE = {"soldat": "formation_militaire", "officier": "ecole_officiers", "policier": "ecole_police",
         "medecin": "diplome_medecine", "infirmier": "diplome_infirmier", "enseignant": "diplome_enseignant",
         "convoyeur": "permis_poids_lourd", "mineur": "securite_mine", "petrolier": "securite_industrie",
         "ouvrier": "securite_industrie"}
FORMEES_A_L_EMBAUCHE = ("securite_mine", "securite_industrie")
SERVICE_MILITAIRE = {HOMME: 0.85, FEMME: 0.02}
PERMIS_POIDS_LOURD = {HOMME: 0.06, FEMME: 0.005}
TITRES_DE_SORTIE = (("diplome_enseignant", 0.15), ("diplome_infirmier", 0.08), ("diplome_medecine", 0.04),
                    ("ecole_police", 0.03), ("ecole_officiers", 0.02))

# ================================================================== les syndicats et les greves
# Densite syndicale grecque : 13,4 % des salaries en 2020 ( OCDE/AIAS ICTWSS ), bien plus haute dans le public ; la
# demande d origine dit ~ 20 %. Public 35 %, prive 10 % : ~ 20 % sur les salaries du moteur ( a calibrer ).
ADHESION = {"public": 0.35, "prive": 0.10}
COTISATION_SYNDICALE = 0.005        # du brut, retenue sur la paie ( a calibrer )
ALLOCATION_GREVE = 0.30             # part du net perdu que le syndicat verse a ses membres grevistes ( a calibrer )
INTERDITS_DE_GREVE = ("soldat", "officier", "policier")   # Constitution grecque, art. 23 al. 2 ; forces armees
POLITIQUES = ("chef_gouvernement", "ministre")
HORS_MARCHE = POLITIQUES + ("patron", "marchand")
INDEPENDANTS = ("paysan", "marchand", "patron")
ARRIERES_GREVE_J = 3.0              # une greve eclate quand les salaires impayes atteignent 3 jours de paie
PERTE_POUVOIR_ACHAT = 0.05          # ... ou quand l indice des prix a pris 5 % depuis la derniere hausse
DUREE_GREVE_PA_J = 1                # la greve de 24 heures, forme grecque ordinaire
DUREE_GREVE_ARRIERES_MAX_J = 10
JOUR_DU_MOIS_GREVE = 15

# ================================================================== le marche du travail et la decision
TRAJET_MAX_KM = 40.0
RECHERCHE_EN_EMPLOI_J = 0.003       # part des salaries qui regardent une offre un jour donne ( a calibrer )
PROPOSITIONS_PAR_POSTE = 3
SEUIL_RECRUTEMENT = 0.75            # une entreprise remplace un depart si elle tourne au moins aux trois quarts
HORIZON_OFFRE = 7
NORME_REVENU_J = 2.0 * SMIC_HORAIRE * 8.0 * (1.0 - TAUX_SALARIE) * (1.0 - 0.15)    # deux SMIC nets par jour

# ================================================================== les accidents du travail
# Eurostat ( ESAW 2023, pour 100 000 personnes en emploi ) : mortels - mines 10,8, construction 6,3, agriculture 6,0,
# transport 4,9, sante 0,3 ; non mortels ( au moins 4 jours d arret ) - transport 2 366, administration publique 1 083.
# Le reste : a calibrer. Rapportes a 225 jours travailles par an ( a calibrer ).
ACCIDENTS = {"paysan": (1700.0, 6.0), "mineur": (1600.0, 10.8), "petrolier": (1600.0, 10.8), "ouvrier": (1900.0, 2.5),
             "convoyeur": (2366.0, 4.9), "soldat": (1083.0, 1.0), "officier": (1083.0, 1.0), "policier": (1083.0, 1.0),
             "medecin": (1300.0, 0.3), "infirmier": (1300.0, 0.3), "enseignant": (500.0, 0.2),
             "ministre": (300.0, 0.2), "chef_gouvernement": (300.0, 0.2)}
JOURS_TRAVAILLES_AN = 225.0

# ================================================================== les statuts et les contrats
HORS, SALARIE, FONCTIONNAIRE, INDEPENDANT, CHOMEUR, ETUDIANT, AU_FOYER, INVALIDE, DECOURAGE, RETRAITE = range(10)
STATUTS = ("hors", "salarie", "fonctionnaire", "independant", "chomeur", "etudiant", "au_foyer", "invalide",
           "decourage", "retraite")
EN_EMPLOI = (SALARIE, FONCTIONNAIRE, INDEPENDANT)
PAYES_A_L_HEURE = (SALARIE, FONCTIONNAIRE)
AUCUN, CDI, CDD, SAISONNIER, TITULAIRE, INDEP = range(6)
CONTRATS = ("aucun", "cdi", "cdd", "saisonnier", "fonctionnaire", "independant")
STABILITE = {AUCUN: 0.0, CDI: 1.0, CDD: 0.5, SAISONNIER: 0.25, TITULAIRE: 1.0, INDEP: 1.0}
RESERVE_CAISSE_J = 90             # la caisse garde trois mois de prestations ( a calibrer )
TOLERANCE_HEURES = 2.0              # heures : un aller-retour de convoi est credite au depart ( monde.py ), pointe en route


# ================================================================== fonctions pures ( testables seules )
def taux_de_remplacement(annees):
    """La somme des annuites marginales du bareme de la loi 4670/2020 pour `annees` d assurance ( 40 ans : 50,01 % )."""
    tot, prec = 0.0, 0.0
    for borne, t in BAREME_ANNUITES:
        if annees <= prec: break
        tot += (min(annees, borne) - prec) * t
        prec = borne
    return tot


def calculer_pension(jours, assiette, age, invalidite=False):
    """La pension mensuelle liquidee a `age` ans avec `jours` d assurance et `assiette` drachmes de gains cotises :
    rend ( totale, part nationale, part contributive, penalite ). Moins de 15 ans d assurance : aucune pension
    ( l allocation des non-assures viendra a 67 ans ). Invalidite : sans penalite d age, 1 500 jours suffisent."""
    if jours <= 0.0: return 0.0, 0.0, 0.0, 0.0
    annees = jours / JOURS_ASSURANCE_AN
    reference = assiette / (jours / JOURS_ASSURANCE_MOIS)
    if invalidite:
        if jours < JOURS_INVALIDITE: return 0.0, 0.0, 0.0, 0.0
        nat = PENSION_NATIONALE
        con = reference * taux_de_remplacement(annees) * PART_INVALIDITE
        return nat + con, nat, con, 0.0
    if jours < JOURS_MINIMUM: return 0.0, 0.0, 0.0, 0.0
    nat = PENSION_NATIONALE * (1.0 - BAISSE_NATIONALE_AN * max(0.0, ANNEES_NATIONALE_PLEINE - annees))
    con = reference * taux_de_remplacement(annees)
    pen = 0.0
    if age < AGE_LEGAL and jours < JOURS_CARRIERE_COMPLETE:
        mois = min(PENALITE_MOIS_MAX, math.ceil((AGE_LEGAL - age) * 12.0 - 1e-9))
        pen = PENALITE_PAR_MOIS * mois
    return (nat + con) * (1.0 - pen), nat * (1.0 - pen), con * (1.0 - pen), pen


def duree_indemnite_mois(jours_14_mois):
    for borne, mois in DUREES_INDEMNITE:
        if jours_14_mois < borne: return mois
    return 12


def echelon(annees, grille):
    pas, _, maxi = grille
    return int(min(maxi, max(0.0, annees) // pas))


def decomposer(brut, taux_ir, syndique):
    """Un bulletin, au centime : ( cotisation salariale, cotisation patronale, impot retenu, cotisation syndicale,
    net verse ). brut = net imposable + cotisation salariale ; net imposable = impot + syndicale + net verse."""
    cs = round(brut * TAUX_SALARIE, 2)
    cp = round(brut * TAUX_EMPLOYEUR, 2)
    imposable = brut - cs
    ir = round(imposable * taux_ir, 2)
    sy = round(brut * COTISATION_SYNDICALE, 2) if syndique else 0.0
    return cs, cp, ir, sy, imposable - ir - sy


# ================================================================== les classes
class CaisseSecuriteSociale:
    """La caisse unique ( e-EFKA pour les pensions et la sante, DYPA pour le chomage ) : elle recoit les cotisations et
    le financement de l Etat, elle verse pensions et indemnites. Ses comptes par branche servent la porte et le
    domaine 6 ( statistique publique ). Elle tient son argent a la banque centrale : en Grece, les reserves des caisses
    sont deposees a la Banque de Grece ( loi 2469/1997, capital commun ), pas dans une banque commerciale.
      caisse                      drachmes
      recu, verse                 { motif : drachmes } depuis l installation"""
    __slots__ = ("caisse", "recu", "verse")

    def __init__(self):
        self.caisse = 0.0
        self.recu = {}
        self.verse = {}


class Syndicat:
    """Une confederation : ses membres cotisent sur leur paie, elle verse une allocation a ses grevistes."""
    __slots__ = ("nom", "secteur", "caisse", "cotisations", "allocations")

    def __init__(self, nom, secteur):
        if secteur not in ADHESION: raise ValueError(f"secteur syndical inconnu {secteur!r}")
        self.nom, self.secteur = nom, secteur
        self.caisse = 0.0
        self.cotisations = self.allocations = 0.0


class Pension:
    """Une pension liquidee : mensuelle ( drachmes, 12 versements par an ), sa part nationale ( payee par l Etat a la
    caisse ), sa penalite, les annees d assurance, l age et le jour de la liquidation, sa nature."""
    __slots__ = ("mensuelle", "nationale", "penalite", "annees", "age", "jour", "nature")

    def __init__(self, mensuelle, nationale, penalite, annees, age, jour, nature):
        if not mensuelle >= 0.0 or not 0.0 <= nationale <= mensuelle + TOL: raise ValueError("pension invalide")
        if nature not in ("vieillesse", "invalidite", "non_assure"): raise ValueError(f"nature de pension {nature!r}")
        self.mensuelle, self.nationale, self.penalite = mensuelle, nationale, penalite
        self.annees, self.age, self.jour, self.nature = annees, age, jour, nature

    def par_jour(self): return self.mensuelle * 12.0 / JOURS_AN

    def nationale_par_jour(self): return self.nationale * 12.0 / JOURS_AN


class Indemnite:
    """Une indemnite de chomage ouverte : montant par jour calendaire, premier et dernier jour payes."""
    __slots__ = ("jour", "debut", "fin")

    def __init__(self, jour, debut, fin):
        if not jour > 0.0 or fin < debut: raise ValueError("indemnite invalide")
        self.jour, self.debut, self.fin = jour, debut, fin


class Greve:
    """Une greve : un etablissement ( lieu, metier ) ou une branche publique ( None, metier ). Les grevistes restent
    chez eux ( horaire garde ici, rendu a la fin ) ; l etablissement ne produit pas ; personne n est paye."""
    __slots__ = ("id", "lieu", "role", "motif", "debut", "fin_prevue", "fin", "horaires", "salaires_perdus",
                 "production_perdue", "allocations", "hausse")

    def __init__(self, id, lieu, role, motif, debut, fin_prevue):
        self.id, self.lieu, self.role, self.motif, self.debut, self.fin_prevue = id, lieu, role, motif, debut, fin_prevue
        self.fin = -1
        self.horaires = {}          # habitant -> horaire a lui rendre
        self.salaires_perdus = self.production_perdue = self.allocations = self.hausse = 0.0


class Etablissement:
    """Un employeur qui n est pas une entreprise du moteur : un service public en un lieu ( ecole, hopital, base,
    ministere ), ou un employeur declare par un autre domaine. Il ne detient rien : son payeur ( l Etat, ou l objet
    declare ) paie."""
    __slots__ = ("id", "lieu", "role")

    def __init__(self, lieu, role): self.id, self.lieu, self.role = f"{role}@{lieu.id}", lieu, role


class Offre:
    """Une offre d emploi faite a un candidat : metier, contrat ( et duree d un CDD ), taux horaire brut, net par jour
    qu il en attend ( au taux d impot du jour ), km de route depuis chez lui."""
    __slots__ = ("role", "contrat", "duree_j", "taux", "net_jour", "km")

    def __init__(self, role, contrat, duree_j, taux, net_jour, km):
        if contrat not in range(1, len(CONTRATS)) or not km >= 0.0: raise ValueError("offre invalide")
        self.role, self.contrat, self.duree_j, self.taux, self.net_jour, self.km = role, contrat, duree_j, taux, net_jour, km


class ContexteOffre:
    """Ce qu un candidat voit : ses traits, et les jours qui restent a son CDD ( que seule la regle lit )."""
    __slots__ = ("traits", "fin_cdd_j")

    def __init__(self, traits, fin_cdd_j): self.traits, self.fin_cdd_j = traits, fin_cdd_j


class Travail:
    """L etat du domaine."""
    __slots__ = ("caisse", "syndicats", "pensions", "indemnites", "etablissements", "employeurs", "cible",
                 "postes_ouverts", "greves", "en_greve", "grevistes", "indice_ref", "pointes", "decideur", "anomalies",
                 "bulletins", "garder_bulletins", "jour", "cumul", "serie", "accidents", "revenu_coop", "offres_jour",
                 "par_eid", "bareme_ir", "inactifs", "km_cache", "retraites_sans_pension", "tolerance_heures",
                 "hors_paie", "placements")

    def __init__(self):
        self.caisse = CaisseSecuriteSociale()
        self.syndicats = {"prive": Syndicat("GSEE", "prive"), "public": Syndicat("ADEDY", "public")}
        self.pensions = {}          # habitant -> Pension
        self.indemnites = {}        # habitant -> Indemnite
        self.etablissements = {}    # ( lieu, metier ) -> Etablissement ( services publics, employeurs declares )
        self.employeurs = {}        # ( lieu, metier ) -> payeur declare par un autre domaine
        self.cible = {}             # ( lieu, metier ) -> effectif vise
        self.postes_ouverts = {}    # ( lieu, metier ) -> postes ouverts par un autre domaine ( a pourvoir )
        self.greves = []            # toutes les greves, finies ou non
        self.en_greve = {}          # ( lieu ou None, metier ) -> Greve en cours
        self.grevistes = {}         # habitant -> Greve
        self.indice_ref = {}        # ( lieu ou None, metier ) -> indice des prix a la derniere hausse de salaire
        self.pointes = []           # les salaries a pointer ( Habitant ), refaits chaque matin
        self.decideur = None
        self.anomalies = deque(maxlen=2000)    # ( jour, habitant, heures payees, heures pointees, statut )
        self.bulletins = []         # les bulletins du jour ( si garder_bulletins ) : pour les portes
        self.garder_bulletins = False
        self.jour = {}              # les agregats de la derniere paie
        self.cumul = {}             # les agregats depuis l installation
        self.serie = deque(maxlen=400)
        self.accidents = {}         # metier -> [ non mortels, mortels ]
        self.revenu_coop = {}       # id de ferme -> revenu agricole lisse par paysan et par jour
        self.offres_jour = []       # ( habitant, cle, action ) des offres du matin
        self.par_eid = {}           # id d entreprise du moteur -> Entreprise
        self.bareme_ir = None       # objet appelable ( p, h, imposable_jour ) -> impot retenu ; None : taux du moteur
        self.inactifs = True
        self.km_cache = {}
        self.retraites_sans_pension = 0
        self.tolerance_heures = TOLERANCE_HEURES
        self.hors_paie = {k: 0.0 for k in AGREGATS}   # agregats des bulletins payes hors de la paie ( solde de tout compte )
        self.placements = 0.0       # reserves de la caisse pretees a l Etat ( encours )


class RemplacePaie:
    """Prend la place de Monde.paie ( 18 h ) : un objet, pour rester picklable."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self): _paie(self.pays)


class RemplaceEmbaucher:
    """Prend la place de Monde.embaucher( h ) : le domaine 1 l appelle a 16 ans et quand un menage demenage."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self, h): _embaucher_moteur(self.pays, h)


# ================================================================== le registre
def _membres_caisse(w): return (w.pays.domaines["travail"].caisse,)
def _membres_syndicats(w): return tuple(w.pays.domaines["travail"].syndicats.values())


# ================================================================== le point de decision
def _observer_offre(ctx): return ctx.traits


def _regle_offre(x, ctx):
    propose, actuel, distance, _, _, _, stab_off, stab_act, en_emploi = x
    if distance > TRAJET_MAX_KM / 60.0: return 0
    if en_emploi < 0.5: return 1 if propose > actuel else 0
    if propose >= 1.10 * actuel and stab_off >= stab_act: return 1
    if 0 <= ctx.fin_cdd_j <= MOIS_J and propose >= 0.9 * actuel: return 1
    return 0


def _temoin_offre(x, ctx, rng): return 1


POINT_OFFRE = D.PointDeDecision(
    "accepter_emploi", "travail",
    traits=(("salaire_propose", "le salaire net par jour de l offre ( taux affiche x heures prevues, cotisations et impot "
                                "au taux du jour deduits ), sur deux SMIC nets"),
            ("revenu_actuel", "son net par jour : son contrat, ou son indemnite de chomage ( lettre de la caisse ), sur "
                              "deux SMIC nets"),
            ("distance", "les km de route de son domicile au lieu de l offre, sur 60"),
            ("qualification", "1 si l offre est dans son metier, 0,5 si c est une reconversion ( il a le titre exige )"),
            ("jours_chomage", "les jours depuis la perte de son emploi, sur 365"),
            ("caisse", "la caisse de son menage sur 30 jours de nourriture du menage au prix affiche, bornee a 1"),
            ("stabilite_offerte", "1 CDI ou titulaire, 0,5 CDD, 0,25 saisonnier ( ecrit dans l offre )"),
            ("stabilite_actuelle", "la meme echelle pour sa situation ; 0,25 s il est indemnise, 0 sans rien"),
            ("en_emploi", "1 s il a un emploi")),
    actions=("refuser", "accepter"),
    observer=_observer_offre, regle=_regle_offre, temoin=_temoin_offre,
    note="chaque soir, pour CE travailleur : ( son revenu net du jour sur deux SMIC nets + son menage a mange + la "
         "stabilite de sa situation ) / 3, moyenne sur 7 jours",
    horizon_j=HORIZON_OFFRE)


# ================================================================== petits outils
def _age(p, h):
    return (p.jour - int(p.col("habitant", "naissance_j")[h.id])) / JOURS_AN


def _ages(p, n):
    return (p.jour - p.col("habitant", "naissance_j")[:n]) / JOURS_AN


def _public(role): return role in C.ROLES and C.ROLES[role][2]
PUBLIC_DU_MOTEUR = np.array([False] + [bool(_public(r)) for r in PO.ROLES])      # code du moteur + 1 ( -1 : aucun )


def _secteur(role): return "public" if _public(role) else "prive"


def _grille(role): return GRILLE_PUBLIQUE if _public(role) else GRILLE_PRIVEE


def taux_de_base(role):
    """Le salaire horaire brut de l echelon 0 d un metier : celui du moteur, jamais sous le SMIC."""
    return max(SMIC_HORAIRE, float(PO.SALAIRE_HORAIRE.get(role, 0)))


def taux_du_metier(role, annees):
    g = _grille(role)
    return taux_de_base(role) * (1.0 + g[1] * echelon(annees, g))


def _heures_prevues(role):
    return HEURES_HORAIRE.get(PO.TRAVAIL[role][1], 8.0) if role in PO.TRAVAIL else 0.0


def _taux_ir(p): return p.w.gouv.impot_revenu


def _net_jour(p, taux, heures, role):
    f = p.w.gouv.facteur_salaire_public if _public(role) else 1.0
    return taux * heures * f * (1.0 - TAUX_SALARIE) * (1.0 - _taux_ir(p))


def _km(p, d, a, b):
    """km de route entre deux lieux ( cache ) ; l infini d une ile a l autre."""
    if a is b: return 0.0
    k = (a.id, b.id) if a.id < b.id else (b.id, a.id)
    v = d.km_cache.get(k)
    if v is None:
        v = p.w.carte.km_route(a, b) if a.ile == b.ile else math.inf
        d.km_cache[k] = v
    return v


def _payeur(p, d, h):
    """Qui paie `h` : l Etat pour un metier public, un employeur declare, le marche pour un convoyeur ( comme
    Monde.paie ), l entreprise du moteur de son lieu sinon."""
    w = p.w; t = h.travail
    if t is None: return None
    r = h.role
    x = d.employeurs.get((t.id, r))
    if x is not None: return x
    if _public(r): return w.gouv
    if r in ("convoyeur", "marchand"): return w.marches.get(t.id)
    e = w.entreprises.get(t.id)
    return e if e is not None and e.role == r else None


def _cle_payeur(x):
    n = type(x).__name__
    if n == "Gouvernement": return "etat"
    if n == "Marche": return "marche@" + x.lieu.id
    return getattr(x, "id", n)


def _unite(p, d, lid, role):
    """L unite a passer a economie.embaucher pour un poste ( lieu, metier )."""
    w = p.w
    if (lid, role) in d.employeurs or _public(role):
        e = d.etablissements.get((lid, role))
        if e is None: e = d.etablissements[(lid, role)] = Etablissement(w.carte.lieux[lid], role)
        return e
    if role in ("convoyeur", "marchand"): return w.marches[lid]
    e = w.entreprises.get(lid)
    if e is None or e.role != role: raise ValueError(f"aucun employeur {role} a {lid}")
    return e


def _a(qualifs, role):
    q = EXIGE.get(role)
    return q is None or q in FORMEES_A_L_EMBAUCHE or bool(qualifs & BIT[q])


def _ajouter(dico, k, v): dico[k] = dico.get(k, 0.0) + v


def _cote(p, d, motif, montant, recu=True):
    _ajouter(d.caisse.recu if recu else d.caisse.verse, motif, montant)


def _payer(p, de, vers, montant, motif):
    """Paie ce qui peut l etre ; le reste devient une creance de `vers` sur `de`. Rend ( paye, du )."""
    if montant <= 0.0: return 0.0, 0.0
    paye = p.socle.livre.transferer(de, vers, montant, motif)
    du = montant - paye
    if du > TOL: p.socle.creances.constater(vers, de, du, motif, p.jour)
    else: du = 0.0
    return paye, du


# ================================================================== les contrats ( API )
def embaucher_contrat(p, h, unite, role=None, contrat=CDI, duree_j=None, taux=None, equipe=None):
    """`h` entre chez `unite` ( entreprise du moteur, marche, Etablissement ) sous `contrat` : economie.embaucher tient
    l index, le registre des chomeurs et l agenda ; ici le contrat, le taux ( la grille de son metier a son anciennete,
    ou `taux` ), les heures prevues, la qualification donnee a l embauche. Rend le taux horaire brut."""
    w = p.w; d = p.domaine("travail"); col = p.colonnes["habitant"]
    role = role or (unite.role if type(unite).__name__ != "Marche" else "marchand")
    if contrat not in range(1, len(CONTRATS)): raise ValueError(f"contrat inconnu {contrat!r}")
    if role in INDEPENDANTS: contrat = INDEP
    elif _public(role) and contrat in (CDI,): contrat = TITULAIRE
    if equipe is None and PO.TRAVAIL[role][1] == "garde":
        n_eq = [0, 0, 0]
        for x in w.au_travail_de(unite.lieu, role):
            if x.vivant and x.travail is unite.lieu: n_eq[x.equipe % 3] += 1
        equipe = min(range(3), key=lambda k: (n_eq[k], k))
    if h.id in d.grevistes: _sortir_de_greve(p, d, h)
    if h.travail is not None: _solde_de_tout_compte(p, d, h)
    ECO.embaucher(p, h, unite, role, equipe)
    i = h.id
    q = EXIGE.get(role)
    if q in FORMEES_A_L_EMBAUCHE: col["tr_qualifs"][i] |= BIT[q]
    _ouvrir_carriere(col, i, p.jour)
    annees = (p.jour - int(col["tr_carriere_j"][i])) / JOURS_AN
    col["tr_statut"][i] = INDEPENDANT if contrat == INDEP else FONCTIONNAIRE if contrat == TITULAIRE else SALARIE
    col["tr_contrat"][i] = contrat
    col["tr_debut_j"][i] = p.jour
    col["tr_fin_j"][i] = p.jour + int(duree_j) if contrat in (CDD, SAISONNIER) and duree_j else -1
    col["tr_echelon"][i] = echelon(annees, _grille(role))
    col["tr_taux"][i] = 0.0 if contrat == INDEP else (taux if taux is not None else taux_du_metier(role, annees))
    col["tr_heures_prevues"][i] = _heures_prevues(role)
    col["tr_chomage_j"][i] = -1
    d.indemnites.pop(i, None)
    if contrat in (CDI, CDD, SAISONNIER, TITULAIRE): d.pointes.append(h)
    return float(col["tr_taux"][i])


def rompre_contrat(p, h, motif="economique", involontaire=True):
    """Le contrat de `h` prend fin : il perd son poste ( economie.licencier ) et devient chomeur ; une perte involontaire
    ouvre ses droits a l indemnite ( jours travailles dans les 14 mois ). Rend l indemnite ouverte ou None."""
    d = p.domaine("travail")
    if h.travail is not None:
        _solde_de_tout_compte(p, d, h)
        ECO.licencier(p, h, motif, inscrire=True)
    return _devenir_chomeur(p, d, h, involontaire)


def _solde_de_tout_compte(p, d, h):
    """Un contrat qui finit dans la journee : les heures deja faites sont payees tout de suite par l employeur qu il
    quitte ( le nouvel employeur ne paie pas le travail fait pour l ancien ), et son pointage est remis a zero."""
    col = p.colonnes["habitant"]; i = h.id
    if h.heures_jour > 0.0 and col["tr_statut"][i] in PAYES_A_L_HEURE and i not in d.grevistes:
        x = _payeur(p, d, h)
        if x is not None:
            f = p.w.gouv.facteur_salaire_public if _public(h.role) else 1.0
            brut = round(float(col["tr_taux"][i]) * h.heures_jour * f, 2)
            if brut > 0.0: _payer_employeur(p, d, x, [(h, brut)], d.hors_paie)
    h.heures_jour = 0.0
    col["tr_pointage"][i] = 0; col["tr_solde_heures"][i] = 0.0


def _ouvrir_carriere(col, i, jour):
    """La carriere commence au premier emploi. Un drapeau, pas une date sentinelle : une carriere reconstituee au
    recensement commence a une date negative ( la lecon du domaine 1, 23/09 )."""
    if not col["tr_carriere"][i]: col["tr_carriere_j"][i] = jour; col["tr_carriere"][i] = 1


def _fermer_contrat(col, i):
    col["tr_contrat"][i] = AUCUN; col["tr_taux"][i] = 0.0; col["tr_fin_j"][i] = -1; col["tr_heures_prevues"][i] = 0.0


def _jours_14_mois(p, col, i):
    """Les jours d assurance dans les 14 mois qui precedent, les 2 derniers exclus ( contrat en cours seulement :
    un contrat anterieur n est pas retrouve - approximation ecrite )."""
    debut = int(col["tr_debut_j"][i])
    a, b = p.jour - FENETRE_14_MOIS_J, p.jour - EXCLUS_2_MOIS_J
    return max(0, b - max(a, debut)) * JOURS_ASSURANCE_MOIS / MOIS_J


def _a_charge(p, h):
    return sum(1 for x in h.menage.membres if x.vivant and x is not h and POP.age_de(p, x) < POP.AGE_MAJEUR)


def _devenir_chomeur(p, d, h, involontaire):
    col = p.colonnes["habitant"]; i = h.id
    ouverte = None
    if involontaire and col["tr_contrat"][i] in (CDI, CDD, SAISONNIER, TITULAIRE):
        mois = duree_indemnite_mois(_jours_14_mois(p, col, i))
        if mois > 0:
            debut = p.jour + CARENCE_J
            ouverte = d.indemnites[i] = Indemnite(INDEMNITE_JOUR * (1.0 + MAJORATION_A_CHARGE * _a_charge(p, h)),
                                                  debut, debut + mois * MOIS_J - 1)
            p.compter("indemnite_ouverte")
    _fermer_contrat(col, i)
    col["tr_statut"][i] = CHOMEUR
    col["tr_chomage_j"][i] = p.jour
    return ouverte


# ================================================================== qualifications ( API du domaine 19 )
def qualifier(p, h, nom):
    if nom not in BIT: raise ValueError(f"qualification inconnue {nom!r} : {QUALIFICATIONS}")
    p.col("habitant", "tr_qualifs")[h.id] |= BIT[nom]


def qualifications(p, h):
    q = int(p.col("habitant", "tr_qualifs")[h.id])
    return tuple(n for n in QUALIFICATIONS if q & BIT[n])


def peut_exercer(p, h, role):
    return _a(int(p.col("habitant", "tr_qualifs")[h.id]), role)


# ================================================================== le recensement du travail ( installation )
def _tirer_sortie_etudes(rng, age):
    """L age de sortie des etudes, au-dela de l age atteint."""
    cands = [(a, pr) for a, pr in SORTIE_ETUDES if a > age]
    if not cands: return age + 0.5
    tot = sum(pr for _, pr in cands)
    u = rng.random() * tot
    for a, pr in cands:
        u -= pr
        if u <= 0: return a + rng.random() * 0.9
    return cands[-1][0]


def _carriere(p, h, rng, age, sexe, role_ref, age_fin=None):
    """Une carriere reconstituee : debut, jours d assurance, gains cotises. `age_fin` : l age ou elle s est arretee."""
    col = p.colonnes["habitant"]; i = h.id
    a0, a1 = ENTREE_CARRIERE.get(h.classe, ENTREE_CARRIERE["populaire"])
    debut = a0 + (a1 - a0) * rng.random()
    d0, d1 = DENSITE_COTISATION[sexe]
    dens = d0 + (d1 - d0) * rng.random()
    fin = age if age_fin is None else min(age, age_fin)
    annees = max(0.0, fin - debut)
    jours = annees * dens * JOURS_ASSURANCE_AN
    col["tr_carriere_j"][i] = p.jour - int(round((age - debut) * JOURS_AN)) if age > debut else p.jour
    col["tr_carriere"][i] = 1
    col["tr_jours_cotises"][i] = jours
    g = _grille(role_ref)
    moyen = taux_de_base(role_ref) * (1.0 + g[1] * echelon(annees, g) / 2.0)
    col["tr_assiette"][i] = jours / JOURS_ASSURANCE_MOIS * moyen * _heures_prevues(role_ref) * 22.0
    return annees


def _liquider(p, d, h, age, nature="vieillesse", ecrire=True):
    """Liquide la pension de `h` ; rend la Pension ( ou None sans droit : moins de 15 ans d assurance ). Sans droit a
    62-66 ans, il attend 67 ans et l allocation des non-assures."""
    col = p.colonnes["habitant"]; i = h.id
    jours, assiette = float(col["tr_jours_cotises"][i]), float(col["tr_assiette"][i])
    tot, nat, _, pen = calculer_pension(jours, assiette, age, invalidite=nature == "invalidite")
    pn = None
    if tot > 0.0:
        pn = Pension(tot, nat, pen, jours / JOURS_ASSURANCE_AN, age, p.jour, nature)
    elif age >= AGE_LEGAL and nature == "vieillesse":
        pn = Pension(ALLOCATION_NON_ASSURE, ALLOCATION_NON_ASSURE, 0.0, jours / JOURS_ASSURANCE_AN, age, p.jour, "non_assure")
    elif nature == "invalidite":           # moins de 1 500 jours : l allocation d invalidite non contributive ( OPEKA )
        pn = Pension(ALLOCATION_NON_ASSURE, ALLOCATION_NON_ASSURE, 0.0, jours / JOURS_ASSURANCE_AN, age, p.jour, "invalidite")
    if pn is not None:
        d.pensions[i] = pn
        if ecrire: p.noter("retraite_liquidee", habitant=i, age=round(age, 2), pension=round(pn.mensuelle, 2),
                           annees=round(pn.annees, 1), nature=pn.nature)
    elif nature == "vieillesse":
        d.retraites_sans_pension += 1
    return pn


def _recensement(p, d, rng):
    """Le jour de l installation : le moteur fait travailler tous les adultes de 16 a 65 ans. Le recensement du travail
    donne a chacun son statut selon son sexe et son age ( taux grecs ), son contrat, sa carriere, ses titres, son
    syndicat ; les retraites recoivent la pension de leur carriere reconstituee. Un poste que personne n occupe plus
    disparait : l effectif vise d un etablissement est celui du recensement."""
    w = p.w; H = w.habitants; col = p.colonnes["habitant"]
    sexe_c = col["sexe"]
    for h in H:
        if not h.vivant: continue
        i = h.id
        age = POP.age_de(p, h)
        sexe = int(sexe_c[i]) if sexe_c[i] >= 0 else HOMME
        q = 0
        if age >= 21 and rng.random() < SERVICE_MILITAIRE[sexe]: q |= BIT["formation_militaire"]
        if age >= 21 and rng.random() < PERMIS_POIDS_LOURD[sexe]: q |= BIT["permis_poids_lourd"]
        if h.role in EXIGE: q |= BIT[EXIGE[h.role]]
        col["tr_qualifs"][i] = q
        if h.role == "enfant":
            if age >= C.AGE_TRAVAIL:
                col["tr_statut"][i] = ETUDIANT
                col["tr_fin_etudes"][i] = p.jour + int(round((_tirer_sortie_etudes(rng, age) - age) * JOURS_AN))
            continue
        if h.role == "retraite":
            ref = METIER_DE_CLASSE.get(h.classe, "ouvrier")
            _carriere(p, h, rng, age, sexe, ref, age_fin=min(age, C.AGE_RETRAITE))
            col["tr_statut"][i] = RETRAITE
            _liquider(p, d, h, min(age, C.AGE_RETRAITE), ecrire=False)
            continue
        annees = _carriere(p, h, rng, age, sexe, h.role)
        statut = SALARIE
        if d.inactifs and h.role not in POLITIQUES + ("patron",) and C.AGE_TRAVAIL <= age < 65:
            ligne = next((t for a0, a1, t in STATUTS_RECENSEMENT if a0 <= age < a1), None)
            if ligne is not None:
                e_, u_, s_, f_, i_, r_ = ligne[sexe]
                autre_adulte = any(x.vivant and x is not h and POP.age_de(p, x) >= POP.AGE_MAJEUR for x in h.menage.membres)
                if not autre_adulte or h.role == "paysan": e_, f_ = e_ + f_, 0.0
                # au foyer suppose un autre revenu dans le menage ; sur une exploitation familiale, le conjoint qui y
                # travaille est un aide familial, en emploi au sens du BIT ( la Grece en compte la part la plus forte de
                # l Union, surtout dans l agriculture : Eurostat, a calibrer )
                x = rng.random()
                for st, pr in ((SALARIE, e_), (CHOMEUR, u_), (ETUDIANT, s_), (AU_FOYER, f_), (INVALIDE, i_), (RETRAITE, r_)):
                    if x < pr: statut = st; break
                    x -= pr
                else: statut = DECOURAGE
        if statut == SALARIE:
            _contrat_recensement(p, d, h, rng, annees)
            continue
        ECO.licencier(p, h, "recensement", inscrire=statut == CHOMEUR)
        col["tr_statut"][i] = statut
        if statut == CHOMEUR:
            duree = int(rng.integers(*DUREE_CHOMAGE_RECENSEMENT_J))
            col["tr_chomage_j"][i] = p.jour - duree
            reste = 12 * MOIS_J - duree
            if reste > 0: d.indemnites[i] = Indemnite(INDEMNITE_JOUR * (1.0 + MAJORATION_A_CHARGE * _a_charge(p, h)),
                                                       p.jour, p.jour + reste - 1)
        elif statut == ETUDIANT:
            h.role, h.horaire, h.travail = "enfant", "ecole", h.domicile.marche
            col["tr_fin_etudes"][i] = p.jour + int(round((_tirer_sortie_etudes(rng, age) - age) * JOURS_AN))
        elif statut in (INVALIDE, RETRAITE):
            h.role, h.horaire = "retraite", None
            _liquider(p, d, h, age, "invalidite" if statut == INVALIDE else "vieillesse", ecrire=False)
    # les syndiques, parmi les salaries ; l effectif vise de chaque etablissement
    stat = col["tr_statut"]
    for h in H:
        if not h.vivant or stat[h.id] not in PAYES_A_L_HEURE: continue
        if rng.random() < ADHESION[_secteur(h.role)]: col["tr_syndique"][h.id] = 1
    d.cible = {}
    for h in H:
        if h.vivant and h.travail is not None and stat[h.id] in EN_EMPLOI:
            k = (h.travail.id, h.role); d.cible[k] = d.cible.get(k, 0) + 1


def _contrat_recensement(p, d, h, rng, annees):
    col = p.colonnes["habitant"]; i = h.id
    r = h.role
    if r in INDEPENDANTS: contrat = INDEP
    elif _public(r): contrat = TITULAIRE
    else: contrat = CDD if rng.random() < PART_CDD_RECENSEMENT else CDI
    col["tr_contrat"][i] = contrat
    col["tr_statut"][i] = INDEPENDANT if contrat == INDEP else FONCTIONNAIRE if contrat == TITULAIRE else SALARIE
    anc = min(annees, 0.0 + annees * rng.random()) if contrat != CDD else 0.0
    col["tr_debut_j"][i] = p.jour - int(round(anc * JOURS_AN))
    col["tr_fin_j"][i] = p.jour + int(rng.integers(*DUREE_CDD_J)) if contrat == CDD else -1
    g = _grille(r)
    col["tr_echelon"][i] = echelon(annees, g)
    col["tr_taux"][i] = 0.0 if contrat == INDEP else taux_du_metier(r, annees)
    col["tr_heures_prevues"][i] = _heures_prevues(r)


# ================================================================== Monde.embaucher repris
def _metier_vise(p, d, h):
    """Le metier d un jeune qui sort des etudes : son titre s il en a un, sinon le metier libre le plus depeuple
    ( la regle du moteur, sur l index du jour )."""
    col = p.colonnes["habitant"]; q = int(col["tr_qualifs"][h.id])
    for role in ("medecin", "infirmier", "enseignant", "policier", "officier"):
        if q & BIT[EXIGE[role]]: return role
    w = p.w
    libres = ("paysan", "mineur", "ouvrier", "petrolier") + (("soldat",) if q & BIT["formation_militaire"] else ())
    manque = {r: w._compte_role.get(r, 0) / max(1, C.ROLES[r][0]) for r in libres}
    return min(manque, key=lambda r: (manque[r], r))


def _sortir_des_etudes(p, d, h, rng):
    col = p.colonnes["habitant"]; i = h.id
    age = POP.age_de(p, h)
    sexe = int(col["sexe"][i])
    if age >= 19 and rng.random() < SERVICE_MILITAIRE.get(sexe, 0.0): col["tr_qualifs"][i] |= BIT["formation_militaire"]
    if age >= 21.5 and not p.a("education"):      # en attendant le domaine 19
        u = rng.random()
        for titre, pr in TITRES_DE_SORTIE:
            if titre == "diplome_medecine" and age < 23.5: continue
            if u < pr: col["tr_qualifs"][i] |= BIT[titre]; break
            u -= pr
    role = _metier_vise(p, d, h)
    ECO.licencier(p, h, "fin_etudes", inscrire=False) if h.travail is not None and h.role != "enfant" else None
    h.role, h.classe, h.travail, h.horaire = role, C.ROLES[role][1], None, None
    if h.poste in ("travail",): h.lieu, h.poste = h.domicile, "maison"
    col["tr_statut"][i] = CHOMEUR
    col["tr_chomage_j"][i] = p.jour
    _fermer_contrat(col, i)
    ECO_d = p.domaine("economie")
    ECO_d.chomeurs[i] = [p.jour, None, role, "primo_demandeur"]     # le registre du domaine 3 ( pas d API d inscription )
    if p.a("agenda"): importlib.import_module(".d05_agenda", __package__).replanifier(p, h, rentrer=True)
    p.noter("fin_etudes", habitant=i, age=round(age, 2), metier=role)


def _embaucher_moteur(p, h):
    """Le contrat d appel du domaine 1 : a 16 ans et plus ( role enfant ), le jeune poursuit ses etudes jusqu a son age
    de sortie, puis cherche un emploi ( chomeur primo-demandeur : le marche du matin lui fera des offres ). Au
    demenagement d un menage, un actif dont le travail est desormais a plus de 40 km le quitte et cherche sur place."""
    d = p.domaine("travail"); col = p.colonnes["habitant"]; i = h.id
    if not h.vivant: return
    if h.role == "enfant":
        if col["tr_statut"][i] != ETUDIANT:
            col["tr_statut"][i] = ETUDIANT
            col["tr_fin_etudes"][i] = p.jour + int(round((_tirer_sortie_etudes(p.hasard("travail_etudes"),
                                                                                POP.age_de(p, h)) - POP.age_de(p, h)) * JOURS_AN))
        if p.jour >= col["tr_fin_etudes"][i]: _sortir_des_etudes(p, d, h, p.hasard("travail_etudes"))
        return
    st = col["tr_statut"][i]
    if st in EN_EMPLOI and h.travail is not None and _km(p, d, h.domicile, h.travail) > TRAJET_MAX_KM:
        _solde_de_tout_compte(p, d, h)
        ECO.licencier(p, h, "demenagement", inscrire=True)
        _devenir_chomeur(p, d, h, involontaire=False)


# ================================================================== le pointage ( chaque pas )
def _pointer(p, pas=None):
    """Qui est a son poste ( ou au volant d un convoi ) au pas qui vient d etre joue : la preuve des heures payees. Un
    convoi part au pas L et rend son chauffeur libre a L + 2 x duree : il conduit les pas L a L + 2 x duree - 1, ceux
    que le moteur lui credite au depart. Une routine tombe apres le pas ( w.pas vaut deja L + 1 ) ; la paie, pendant."""
    d = p.domaine("travail"); w = p.w
    libre = w.conducteur_libre
    if pas is None: pas = w.pas - 1
    # EN COLONNES ( 24/09 ) : la liste des salaries est lue une fois en numeros, puis le test se fait sur la table
    ids = _ids_pointes(d)
    if not len(ids): return
    tb = w.table
    tr = tb.travail[ids]
    ok = (tb.poste[ids] == PO.CODE_POSTE["travail"]) & (tb.lieu[ids] == tr) & (tr >= 0)
    if libre:
        au_volant = np.fromiter((k for k, v in libre.items() if v > pas), np.int64)
        if len(au_volant): ok |= np.isin(ids, au_volant)
    ids = ids[ok]
    if len(ids): p.col("habitant", "tr_pointage")[ids] += 1


_POINTES = {}          # id( etat du domaine ) -> ( la liste d.pointes, sa longueur lue, ses numeros )


def _ids_pointes(d):
    """Les numeros de `d.pointes`, dans son ordre : relus seulement quand la liste est remplacee ( chaque matin ) ;
    les embauches du jour, ajoutees a la fin, sont lues a leur tour."""
    lst = d.pointes
    c = _POINTES.get(id(d))
    if c is None or c[0] is not lst or c[1] > len(lst):
        c = (lst, 0, np.zeros(0, np.int64))
    if c[1] < len(lst):
        c = (lst, len(lst), np.concatenate([c[2], np.fromiter((h.id for h in lst[c[1]:]), np.int64)]))
    _POINTES[id(d)] = c
    return c[2]


def _refaire_pointes(p, d):
    w = p.w; st = p.col("habitant", "tr_statut")
    d.pointes = [h for h in w.habitants if h.vivant and h.travail is not None and st[h.id] in PAYES_A_L_HEURE]


# ================================================================== la paie ( 18 h )
AGREGATS = ("brut", "cot_sal", "cot_pat", "ir", "syndicale", "net", "net_paye", "salaires_dus", "cotisations_dues",
            "ir_du", "syndicale_due", "arrieres_payes", "heures", "pensions", "indemnites", "prestations_dues",
            "financement_etat", "revenu_independants", "cotisations_independants", "allocations_greve")


def _paie(p):
    """Monde.paie repris. Heures payees = heures creditees par la production, l agenda et le moteur ( fonctionnaires ),
    confrontees au pointage. Puis les revenus des independants ( comme le moteur ), les pensions et les indemnites
    ( la caisse, financee par l Etat pour la part nationale et son deficit ), les cotisations des independants en fin de
    mois, les accidents du travail."""
    w = p.w; d = p.domaine("travail"); L = p.socle.livre; g = w.gouv
    H = w.habitants; n = len(H)
    col = p.colonnes["habitant"]; col.assurer(n)
    _pointer(p, w.pas)                                   # le pas de 18 h, joue en ce moment
    heures = w.table.heures[:n].copy()
    statut = col["tr_statut"][:n]
    pt = col["tr_pointage"][:n].astype(np.float64) / 6.0
    net_j = col["tr_net_jour"]; net_j[:n] = 0.0
    agg = {k: 0.0 for k in AGREGATS}
    if d.garder_bulletins: d.bulletins = []
    # --- 1. le controle des heures : un salarie paye doit avoir ete pointe ; personne d autre n a d heures
    solde = col["tr_solde_heures"]
    payes = np.isin(statut, PAYES_A_L_HEURE)
    s = np.where(statut != INDEPENDANT, np.maximum(0.0, solde[:n] + heures - pt), 0.0)
    solde[:n] = s
    suspects = np.nonzero(s > d.tolerance_heures)[0]
    for i in suspects.tolist():
        d.anomalies.append((p.jour, i, float(heures[i]), float(pt[i]), STATUTS[int(statut[i])]))
        p.compter("heures_non_travaillees", float(heures[i]))
        solde[i] = 0.0
    # --- 2. les salaires, employeur par employeur ( ordre des identifiants : deterministe )
    parts = {}
    taux = col["tr_taux"]; syn = col["tr_syndique"]
    for i in np.nonzero(payes & (heures > 0.0))[0].tolist():
        h = H[i]
        if not h.vivant or i in d.grevistes: continue
        x = _payeur(p, d, h)
        if x is None: continue
        f = g.facteur_salaire_public if _public(h.role) else 1.0
        brut = round(float(taux[i]) * float(heures[i]) * f, 2)
        if brut <= 0.0: continue
        k = _cle_payeur(x)
        if k not in parts: parts[k] = (x, [])
        parts[k][1].append((h, brut))
    for k, (x, lignes) in parts.items():
        _payer_employeur(p, d, x, lignes, agg)
    # --- 3. les independants, comme le moteur : benefice des marchands, revenu des cooperatives agricoles
    _independants(p, d, agg)
    # --- 4. les prestations de la caisse
    _prestations(p, d, agg)
    # --- 5. fin de mois : cotisations des independants, placement des reserves de la caisse
    if p.jour % MOIS_J == MOIS_J - 1:
        _cotisations_independants(p, d, agg)
        _placer_reserves(p, d, agg)
    # --- 6. accidents du travail, sur les jours travailles
    _accidents(p, d, heures)
    agg["heures"] = float(heures.sum())
    for h in H: h.heures_jour = 0.0
    col["tr_pointage"][:n] = 0
    d.jour = agg
    for kk, v in agg.items(): _ajouter(d.cumul, kk, v)


MOTIFS_SALAIRE = ("salaire", "salaire public")
MOTIFS_RETENUES = ("cotisation_salariale", "cotisation_patronale", "impot sur le revenu", "cotisation_syndicale")


def _regler_arrieres(p, d, x, agg):
    """L employeur regle d abord ses arrieres, les plus anciens en premier : les salaires, puis ce qu il doit a la
    caisse, a l Etat et aux syndicats ( sous le motif d origine : un salaire paye en retard reste un salaire )."""
    K = p.socle.creances; L = p.socle.livre
    for motifs in (MOTIFS_SALAIRE, MOTIFS_RETENUES):
        for cr in list(K.de(x)):
            if x.caisse <= TOL: return
            if cr.motif not in motifs: continue
            creancier = cr.creancier
            v = K.regler(cr, L)
            agg["arrieres_payes"] += v
            if creancier is d.caisse: _cote(p, d, cr.motif, v)
            elif type(creancier) is Syndicat: creancier.cotisations += v


def _payer_employeur(p, d, x, lignes, agg, credit_jours=True):
    """Un employeur paie ses bulletins du jour. S il ne peut pas tout payer, chaque part est payee au marc le franc et
    le reste devient une creance nommee : salaire du menage, cotisations de la caisse, impot de l Etat, cotisation du
    syndicat. L Etat qui paie ses agents retient l impot pour lui-meme : un mouvement nul en caisse, ecrit au grand
    livre pour que la statistique publique voie l impot ( D.5 )."""
    w = p.w; L = p.socle.livre; g = w.gouv; col = p.colonnes["habitant"]; K = p.socle.creances
    etat = x is g
    motif = "salaire public" if etat else "salaire"
    b = []
    tot = 0.0
    for h, brut in lignes:
        syndique = bool(col["tr_syndique"][h.id])
        if d.bareme_ir is None: cs, cp, ir, sy, net = decomposer(brut, _taux_ir(p), syndique)
        else:
            cs, cp, _, sy, _ = decomposer(brut, 0.0, syndique)
            ir = round(float(d.bareme_ir(p, h, brut - cs)), 2)
            net = brut - cs - ir - sy
        b.append((h, brut, cs, cp, ir, sy, net))
        tot += brut + cp - (ir if etat else 0.0)
    _regler_arrieres(p, d, x, agg)
    if etat and BQ.AVANCE_AUTOMATIQUE and g.caisse < tot: BQ.avance_a_l_etat(p, tot - max(0.0, g.caisse))
    k = 1.0 if x.caisse >= tot else max(0.0, x.caisse) / tot
    s_cs = s_cp = s_ir = 0.0
    s_sy = {"public": 0.0, "prive": 0.0}
    for h, brut, cs, cp, ir, sy, net in b:
        i = h.id
        paye = L.transferer(x, h.menage, net * k, motif)
        du = net - paye
        if du > 1e-7:
            K.constater(h.menage, x, du, motif, p.jour); agg["salaires_dus"] += du
            p.compter("arrieres_salaire", du)
        s_cs += cs; s_cp += cp; s_ir += ir; s_sy[_secteur(h.role)] += sy
        col["tr_net_jour"][i] += paye
        if credit_jours:
            credit = min(CREDIT_JOUR_PAYE * k, max(0.0, JOURS_ASSURANCE_MOIS - float(col["tr_jours_mois"][i])))
            col["tr_jours_mois"][i] += credit; col["tr_jours_cotises"][i] += credit
        col["tr_assiette"][i] += brut * k
        col["tr_imposable_an"][i] += brut - cs
        for kk, v in (("brut", brut), ("cot_sal", cs), ("cot_pat", cp), ("ir", ir), ("syndicale", sy), ("net", net),
                      ("net_paye", paye)):
            agg[kk] += v
        if d.garder_bulletins: d.bulletins.append((i, _cle_payeur(x), brut, cs, cp, ir, sy, net, paye, k))
    for motif_c, m in (("cotisation_salariale", s_cs), ("cotisation_patronale", s_cp)):
        paye, du = _payer(p, x, d.caisse, m * k, motif_c)
        if m * (1.0 - k) > TOL: K.constater(d.caisse, x, m * (1.0 - k), motif_c, p.jour); du += m * (1.0 - k)
        _cote(p, d, motif_c, paye); agg["cotisations_dues"] += du
    if etat:
        L.transferer(g, g, s_ir, "impot sur le revenu")         # retenu par l Etat sur lui-meme : rien ne bouge
    else:
        paye, du = _payer(p, x, g, s_ir * k, "impot sur le revenu")
        if s_ir * (1.0 - k) > TOL: K.constater(g, x, s_ir * (1.0 - k), "impot sur le revenu", p.jour); du += s_ir * (1.0 - k)
        agg["ir_du"] += du
    for sect, m in s_sy.items():
        if m <= 0.0: continue
        s = d.syndicats[sect]
        paye, du = _payer(p, x, s, m * k, "cotisation_syndicale")
        if m * (1.0 - k) > TOL: K.constater(s, x, m * (1.0 - k), "cotisation_syndicale", p.jour); du += m * (1.0 - k)
        s.cotisations += paye; agg["syndicale_due"] += du


def _independants(p, d, agg):
    """Monde.paie, pour ceux qui ne sont pas payes a l heure : les marchands se partagent la moitie du benefice de leur
    marche au-dela de 20 000 drachmes, les paysans la caisse de leur cooperative ; l impot du moteur est preleve.
    Les dividendes des patrons sont au domaine 3 ( fin de mois )."""
    w = p.w; L = p.socle.livre; g = w.gouv; col = p.colonnes["habitant"]
    for m in w.marches.values():
        marchands = [x for x in w.au_travail_de(m.lieu, "marchand") if x.vivant and x.travail is m.lieu]
        exces = m.caisse - 20000.0
        if exces > 0 and marchands:
            for x in marchands:
                brut = L.transferer(m, x.menage, 0.5 * exces / len(marchands), "benefice marchand")
                L.transferer(x.menage, g, brut * g.impot_revenu, "impot")
                col["tr_imposable_an"][x.id] += brut; col["tr_net_jour"][x.id] += brut * (1.0 - g.impot_revenu)
                agg["revenu_independants"] += brut
    for e in w.entreprises.values():
        if e.type != "ferme": continue
        paysans = [x for x in w.au_travail_de(e.lieu, "paysan") if x.vivant and x.travail is e.lieu]
        part = e.caisse / len(paysans) if paysans and e.caisse > 0 else 0.0
        r = d.revenu_coop.get(e.id)
        d.revenu_coop[e.id] = part if r is None else r + (part - r) / 30.0
        if part <= 0.0: continue
        for x in paysans:
            brut = L.transferer(e, x.menage, part, "revenu agricole")
            L.transferer(x.menage, g, brut * g.impot_revenu, "impot")
            col["tr_imposable_an"][x.id] += brut; col["tr_net_jour"][x.id] += brut * (1.0 - g.impot_revenu)
            agg["revenu_independants"] += brut


def _prestations(p, d, agg):
    """Pensions et indemnites du jour. L Etat verse d abord la part nationale des pensions ( et les allocations des
    non-assures ), puis couvre le deficit de la caisse s il y en a un : les prestations sont garanties par la loi."""
    w = p.w; L = p.socle.livre; g = w.gouv; col = p.colonnes["habitant"]; H = w.habitants
    c = d.caisse
    dues = []
    nat = 0.0
    for i, pn in d.pensions.items():
        h = H[i]
        if not h.vivant: continue
        dues.append((h, pn.par_jour(), "pension_invalidite" if pn.nature == "invalidite" else "pension_vieillesse"))
        nat += pn.nationale_par_jour()
    for i, ind in d.indemnites.items():
        h = H[i]
        if not h.vivant or not ind.debut <= p.jour <= ind.fin: continue
        dues.append((h, ind.jour, "indemnite_chomage"))
    for h, g_, mot in _allocations_greve(p, d): dues.append((h, g_, mot))
    total = math.fsum(m for _, m, mot in dues if mot != "allocation_greve")
    K = p.socle.creances
    arr = math.fsum(cr.montant for cr in K.de(c))
    besoin = nat + max(0.0, total + arr - c.caisse - nat)
    if BQ.AVANCE_AUTOMATIQUE and besoin > 0.0 and g.caisse < besoin: BQ.avance_a_l_etat(p, besoin - max(0.0, g.caisse))
    if nat > 0.0:
        paye, _ = _payer(p, g, c, nat, "financement_etat_securite_sociale")
        _cote(p, d, "financement_etat_securite_sociale", paye); agg["financement_etat"] += paye
    if c.caisse < total + arr:                                   # la caisse rappelle d abord ses reserves placees
        for cr in [cr for cr in K.de(g) if cr.creancier is c and cr.motif == "placement_reserves"]:
            x = K.regler(cr, L, total + arr - c.caisse); d.placements -= x
            if c.caisse >= total + arr: break
    if c.caisse < total + arr:
        paye = L.transferer(g, c, total + arr - c.caisse, "financement_etat_securite_sociale")
        _cote(p, d, "financement_etat_securite_sociale", paye); agg["financement_etat"] += paye
    for cr in list(K.de(c)):                                     # les prestations en retard d abord
        if c.caisse <= TOL: break
        x = K.regler(cr, L); _cote(p, d, cr.motif, x, recu=False)
    for h, m, mot in dues:
        if mot == "allocation_greve":
            s = d.syndicats[_secteur(h.role)]
            x = L.transferer(s, h.menage, m, mot); s.allocations += x; agg["allocations_greve"] += x
            gv = d.grevistes.get(h.id)
            if gv is not None: gv.allocations += x
        else:
            x, du = _payer(p, c, h.menage, m, mot)
            _cote(p, d, mot, x, recu=False)
            agg["indemnites" if mot == "indemnite_chomage" else "pensions"] += x
            agg["prestations_dues"] += du
        col["tr_net_jour"][h.id] += x


def _allocations_greve(p, d):
    """Ce que chaque syndicat doit a ses grevistes aujourd hui ( une part du net perdu, dans la limite de sa caisse )."""
    col = p.colonnes["habitant"]; w = p.w
    voulu = {}
    for i, gv in d.grevistes.items():
        h = w.habitants[i]
        if not h.vivant or not col["tr_syndique"][i]: continue
        perdu = _net_jour(p, float(col["tr_taux"][i]), float(col["tr_heures_prevues"][i]), h.role)
        voulu.setdefault(_secteur(h.role), []).append((h, ALLOCATION_GREVE * perdu))
    out = []
    for sect, lst in voulu.items():
        tot = math.fsum(m for _, m in lst)
        k = min(1.0, d.syndicats[sect].caisse / tot) if tot > 0 else 0.0
        out.extend((h, m * k, "allocation_greve") for h, m in lst if m * k > TOL)
    return out


def _cotisations_independants(p, d, agg):
    """Fin de mois : chaque independant en activite paie sa categorie ; un impaye est une dette envers la caisse, et le
    mois n est credite qu a proportion de ce qui est paye."""
    w = p.w; col = p.colonnes["habitant"]; st = col["tr_statut"]
    for h in w.habitants:
        if not h.vivant or st[h.id] != INDEPENDANT or h.travail is None: continue
        m = COTISATION_INDEPENDANT_MOIS.get(h.role)
        if m is None: continue
        paye, du = _payer(p, h.menage, d.caisse, m, "cotisation_independant")
        _cote(p, d, "cotisation_independant", paye)
        f = paye / m
        col["tr_jours_cotises"][h.id] += JOURS_ASSURANCE_MOIS * f
        col["tr_assiette"][h.id] += paye * PART_RETRAITE_INDEPENDANT / DIVISEUR_ASSIETTE_INDEPENDANT
        agg["cotisations_independants"] += paye; agg["cotisations_dues"] += du


def _placer_reserves(p, d, agg):
    """Fin de mois : ce que la caisse a au-dela de trois mois de prestations est prete a l Etat ( en Grece, les reserves
    des caisses vont au capital commun de la Banque de Grece, place en titres de l Etat ). Sans cela, l excedent des
    cotisations sortirait l argent de la circulation : la population du moteur a quatre fois moins de retraites que la
    Grece. Une creance de la caisse sur l Etat, rappelee quand la caisse manque ; sans interet ( a calibrer )."""
    L = p.socle.livre; g = p.w.gouv; c = d.caisse
    cumul = d.cumul
    jours = max(1, p.jour + 1)
    prest = (cumul.get("pensions", 0.0) + cumul.get("indemnites", 0.0) + agg["pensions"] + agg["indemnites"]) / jours
    x = c.caisse - RESERVE_CAISSE_J * prest
    if x <= 1.0: return
    paye = L.transferer(c, g, x, "placement_reserves")
    p.socle.creances.constater(c, g, paye, "placement_reserves", p.jour)
    d.placements += paye


def _accidents(p, d, heures):
    """Un tirage par jour travaille, au taux de son secteur. La medecine ( domaine 16 ) blesse si elle est la ;
    sinon on compte."""
    w = p.w
    idx = np.nonzero(heures > 0.0)[0]
    if not len(idx): return
    H = w.habitants
    roles = [H[i].role for i in idx.tolist()]
    pm = np.array([ACCIDENTS.get(r, (0.0, 0.0))[1] for r in roles]) / 1e5 / JOURS_TRAVAILLES_AN
    pb = np.array([ACCIDENTS.get(r, (0.0, 0.0))[0] for r in roles]) / 1e5 / JOURS_TRAVAILLES_AN
    u = p.du_jour("travail_accidents").random(len(idx))
    med = importlib.import_module(".d16_medecine", __package__) if p.a("medecine") else None
    for k in np.nonzero(u < pm + pb)[0].tolist():
        h = H[int(idx[k])]; mortel = bool(u[k] < pm[k])
        t = d.accidents.setdefault(h.role, [0, 0]); t[1 if mortel else 0] += 1
        p.compter("accident_travail")
        if mortel: p.noter("accident_mortel", habitant=h.id, metier=h.role)
        if med is not None and hasattr(med, "blesser"): med.blesser(p, h, "accident_travail", 1.0 if mortel else 0.3)


# ================================================================== les carrieres ( 6 h 10 )
def _carrieres(p):
    """Chaque matin, apres l aube : ce que d autres domaines ont change ( morts, retraites du domaine 1, embauches et
    licenciements du domaine 3 ) est repris ; puis les retraites volontaires ( 62 ans et 40 ans d assurance, 67 ans
    et 15 ans ), les fins de CDD, les echelons, le mois et l annee."""
    w = p.w; d = p.domaine("travail"); col = p.colonnes["habitant"]; H = w.habitants; n = len(H)
    col.assurer(n)
    st = col["tr_statut"]; ct = col["tr_contrat"]
    cal = p.socle.calendrier
    if p.jour % MOIS_J == 0: col["tr_jours_mois"][:n] = 0.0
    date = cal.date(w.pas).date()
    if date.month == 1 and date.day == 1: col["tr_imposable_an"][:n] = 0.0
    ages = _ages(p, n)
    for h in H:
        i = h.id
        if not h.vivant:
            if st[i] != HORS:
                st[i] = HORS; _fermer_contrat(col, i); d.pensions.pop(i, None); d.indemnites.pop(i, None)
            continue
        s = int(st[i])
        if h.role == "retraite" and s not in (RETRAITE, INVALIDE):         # le domaine 1 l a mis a la retraite
            _fermer_contrat(col, i); st[i] = RETRAITE; col["tr_syndique"][i] = 0
            _liquider(p, d, h, float(ages[i]))
            continue
        if s == RETRAITE and i not in d.pensions and ages[i] >= AGE_LEGAL:
            _liquider(p, d, h, float(ages[i]))
            continue
        if s in EN_EMPLOI and h.travail is None:                           # licencie par un autre domaine ( faillite )
            _devenir_chomeur(p, d, h, involontaire=i in p.domaine("economie").chomeurs)
            continue
        if s not in EN_EMPLOI and h.travail is not None and h.role not in ("enfant", "retraite"):
            _contrat_par_defaut(p, d, h)                                    # embauche par un autre domaine
    # les retraites volontaires
    jc = col["tr_jours_cotises"][:n]
    cand = np.nonzero(np.isin(st[:n], (SALARIE, FONCTIONNAIRE, INDEPENDANT, CHOMEUR, DECOURAGE, AU_FOYER))
                      & (((ages >= AGE_ANTICIPE) & (jc >= JOURS_CARRIERE_COMPLETE)) | ((ages >= AGE_LEGAL) & (jc >= JOURS_MINIMUM))))[0]
    for i in cand.tolist():
        h = H[i]
        if not h.vivant or h.role in POLITIQUES: continue
        prendre_retraite(p, h)
    # fins de CDD
    fin = col["tr_fin_j"][:n]
    rng = p.du_jour("travail_cdd")                      # un flux par jour, tire pour chaque contrat dans l ordre
    for i in np.nonzero(np.isin(ct[:n], (CDD, SAISONNIER)) & (fin <= p.jour))[0].tolist():
        _fin_cdd(p, d, H[i], rng)
    # echelons : l anciennete de carriere fait monter le taux ( une hausse negociee est gardee : on multiplie )
    car = col["tr_carriere_j"][:n]
    idx = np.nonzero(np.isin(st[:n], PAYES_A_L_HEURE) & (col["tr_carriere"][:n] == 1))[0]
    if len(idx):
        pub = PUBLIC_DU_MOTEUR[w.table.role[idx].astype(np.int64) + 1]
        ann = (p.jour - car[idx]) / JOURS_AN
        pas = np.where(pub, GRILLE_PUBLIQUE[0], GRILLE_PRIVEE[0]); hausse = np.where(pub, GRILLE_PUBLIQUE[1], GRILLE_PRIVEE[1])
        e = np.minimum(np.where(pub, GRILLE_PUBLIQUE[2], GRILLE_PRIVEE[2]), np.maximum(0.0, ann) // pas).astype(np.int64)
        e0 = col["tr_echelon"][idx].astype(np.int64)
        up = e > e0
        if up.any():
            j = idx[up]
            col["tr_taux"][j] *= (1.0 + hausse[up] * e[up]) / (1.0 + hausse[up] * e0[up])
            col["tr_echelon"][j] = e[up]
            p.compter("promotion", float(up.sum()))


def prendre_retraite(p, h):
    """`h` part a la retraite : il quitte son poste, sa pension est liquidee. Rend la Pension ( ou None )."""
    d = p.domaine("travail"); col = p.colonnes["habitant"]; i = h.id
    if h.id in d.grevistes: _sortir_de_greve(p, d, h)
    if h.travail is not None:
        _solde_de_tout_compte(p, d, h)
        ECO.licencier(p, h, "retraite", inscrire=False)
    h.role, h.horaire, h.travail = "retraite", None, None
    _fermer_contrat(col, i)
    col["tr_statut"][i] = RETRAITE; col["tr_syndique"][i] = 0
    d.indemnites.pop(i, None)
    return _liquider(p, d, h, POP.age_de(p, h))


def _contrat_par_defaut(p, d, h):
    """Un emploi donne par un autre domaine sans passer par embaucher_contrat : un contrat a duree indeterminee."""
    col = p.colonnes["habitant"]; i = h.id
    r = h.role
    contrat = INDEP if r in INDEPENDANTS else TITULAIRE if _public(r) else CDI
    _ouvrir_carriere(col, i, p.jour)
    annees = (p.jour - int(col["tr_carriere_j"][i])) / JOURS_AN
    col["tr_contrat"][i] = contrat
    col["tr_statut"][i] = INDEPENDANT if contrat == INDEP else FONCTIONNAIRE if contrat == TITULAIRE else SALARIE
    col["tr_debut_j"][i] = p.jour; col["tr_fin_j"][i] = -1
    col["tr_echelon"][i] = echelon(annees, _grille(r))
    col["tr_taux"][i] = 0.0 if contrat == INDEP else taux_du_metier(r, annees)
    col["tr_heures_prevues"][i] = _heures_prevues(r)
    col["tr_chomage_j"][i] = -1
    d.indemnites.pop(i, None)
    if contrat != INDEP: d.pointes.append(h)


def _besoin(p, d, lid, role):
    """L employeur remplace-t-il un depart ? L Etat oui ; une entreprise si elle tourne aux trois quarts au moins, n est
    ni liquidee ni en greve ; un marche garde ses convoyeurs ; un employeur declare decide par `ouvrir_postes`."""
    w = p.w
    if (lid, role) in d.employeurs: return False
    if _public(role): return role not in POLITIQUES
    if (lid, role) in d.en_greve: return False
    if role == "convoyeur": return True
    if role == "marchand": return False
    e = w.entreprises.get(lid)
    if e is None or e.role != role: return False
    c = p.domaine("economie").comptes.get(e.id)
    if c is not None and c.liquidee: return False
    return e.activite >= SEUIL_RECRUTEMENT or e.id in p.repris


def _fin_cdd(p, d, h, rng):
    col = p.colonnes["habitant"]; i = h.id
    if h.travail is None: _fermer_contrat(col, i); return
    lid, role = h.travail.id, h.role
    if _besoin(p, d, lid, role) and rng.random() < RENOUVELLEMENT_CDD:
        if p.jour - int(col["tr_debut_j"][i]) >= CDD_VERS_CDI_J:
            col["tr_contrat"][i] = CDI; col["tr_fin_j"][i] = -1
        else:
            col["tr_fin_j"][i] = p.jour + int(rng.integers(*DUREE_CDD_J))
        p.compter("cdd_renouvele"); return
    if not _besoin(p, d, lid, role): d.cible[(lid, role)] = max(0, d.cible.get((lid, role), 1) - 1)
    p.compter("fin_cdd")
    rompre_contrat(p, h, "fin_cdd", involontaire=True)


# ================================================================== le marche du travail ( 6 h 20 )
def _effectifs(p):
    out = {}
    for (lid, r), lst in p.w._par_travail.items():
        k = sum(1 for x in lst if x.vivant and x.travail is not None and x.travail.id == lid and x.role == r)
        if k: out[(lid, r)] = k
    return out


def _postes_vacants(p, d):
    """{ ( lieu, metier ) : postes } : les departs a remplacer, les offres du domaine 3 ( entreprise a plein dont la
    region manque ), les postes ouverts par d autres domaines."""
    eff = _effectifs(p)
    vac = {}
    for k in sorted(d.cible):
        c = d.cible[k]; e = eff.get(k, 0)
        if c <= e: d.cible[k] = e if c < e else c; continue
        if _besoin(p, d, *k): vac[k] = c - e
        else: d.cible[k] = e                            # le poste ne sera pas remplace : il disparait
    for eid, nb in sorted(ECO.offres_d_emploi(p).items()):
        e = d.par_eid.get(eid)
        if e is None or (e.lieu.id, e.role) in d.en_greve: continue
        k = (e.lieu.id, e.role)
        place = postes_de_travail(p, e) - eff.get(k, 0) - vac.get(k, 0)
        if place > 0: vac[k] = vac.get(k, 0) + min(int(nb), place)
    for k in sorted(d.postes_ouverts):
        nb = d.postes_ouverts[k] - eff.get(k, 0)
        if nb > 0: vac[k] = max(vac.get(k, 0), nb)
    return vac


def postes_de_travail(p, e):
    """Les postes de travail d une entreprise du moteur : son capital fixe brut sur le capital d un poste ( domaine 3 ).
    Une offre d emploi au-dela suppose un investissement ( economie.investir ) : sans machine, un ouvrier de plus ne
    produit rien de plus."""
    c = p.domaine("economie").comptes.get(e.id)
    val = ECO.CAPITAL_PAR_POSTE.get(e.type, (40000.0, 20))[0]
    return int(round(c.capital_brut / val)) if c is not None and val > 0 else 0


def _offre_pour(p, d, h, lid, role, rng):
    w = p.w; col = p.colonnes["habitant"]; i = h.id
    lieu = w.carte.lieux[lid]
    car = int(col["tr_carriere_j"][i])
    annees = (p.jour - car) / JOURS_AN if col["tr_carriere"][i] else 0.0
    if role in INDEPENDANTS:
        contrat, duree, taux = INDEP, None, 0.0
        e = w.entreprises.get(lid)
        net = d.revenu_coop.get(e.id, 0.0) * (1.0 - _taux_ir(p)) if e is not None else 0.0
    else:
        contrat = TITULAIRE if _public(role) else (CDD if rng.random() < PART_CDD_EMBAUCHE else CDI)
        duree = int(rng.integers(*DUREE_CDD_J)) if contrat == CDD else None
        taux = taux_du_metier(role, annees)
        net = _net_jour(p, taux, _heures_prevues(role), role)
    return Offre(role, contrat, duree, taux, net, _km(p, d, h.domicile, lieu))


def _revenu_actuel(p, d, h):
    col = p.colonnes["habitant"]; i = h.id
    st = int(col["tr_statut"][i])
    if st in PAYES_A_L_HEURE: return _net_jour(p, float(col["tr_taux"][i]), float(col["tr_heures_prevues"][i]), h.role), STABILITE[int(col["tr_contrat"][i])]
    if st == INDEPENDANT:
        e = p.w.entreprises.get(h.travail.id) if h.travail is not None else None
        return (d.revenu_coop.get(e.id, 0.0) * (1.0 - _taux_ir(p)) if e is not None else 0.0), 1.0
    ind = d.indemnites.get(i)
    if ind is not None and p.jour <= ind.fin: return ind.jour, 0.25
    return 0.0, 0.0


def _traits_offre(p, d, h, o):
    col = p.colonnes["habitant"]; i = h.id; w = p.w
    actuel, stab = _revenu_actuel(p, d, h)
    st = int(col["tr_statut"][i])
    cj = int(col["tr_chomage_j"][i])
    mg = h.menage
    vivants = sum(1 for x in mg.membres if x.vivant)
    prix = w.marches[mg.domicile.marche.id].prix["nourriture"] * (1.0 + w.gouv.tva)
    x = (min(1.0, o.net_jour / NORME_REVENU_J), min(1.0, actuel / NORME_REVENU_J), min(1.0, o.km / 60.0),
         1.0 if o.role == h.role else 0.5, min(1.0, max(0, p.jour - cj) / 365.0) if st == CHOMEUR else 0.0,
         min(1.0, max(0.0, mg.caisse) / max(1e-6, 30.0 * vivants * prix)), STABILITE[o.contrat], stab,
         1.0 if st in EN_EMPLOI else 0.0)
    fin = int(col["tr_fin_j"][i])
    return x, (fin - p.jour if st == SALARIE and col["tr_contrat"][i] in (CDD, SAISONNIER) else -1)


def _marche_du_travail(p):
    """6 h 20 : chaque poste vacant est offert aux candidats les plus proches qui ont le titre exige ( chomeurs, et les
    salaries qui regardent les offres ce jour-la ), trois au plus par poste ; chacun decide ( point accepter_emploi ).
    Une offre acceptee est une embauche immediate : il travaille des aujourd hui si son horaire le permet."""
    w = p.w; d = p.domaine("travail"); col = p.colonnes["habitant"]; H = w.habitants; n = len(H)
    d.offres_jour = []
    vac = _postes_vacants(p, d)
    if not vac: _refaire_pointes(p, d); return
    st = col["tr_statut"][:n]; ages = _ages(p, n)
    rng = p.du_jour("travail_marche")
    cherche = rng.random(n) < RECHERCHE_EN_EMPLOI_J
    fin = col["tr_fin_j"][:n]
    a_terme = np.isin(col["tr_contrat"][:n], (CDD, SAISONNIER)) & (fin - p.jour <= MOIS_J)
    ok = (((st == CHOMEUR) | (np.isin(st, PAYES_A_L_HEURE) & (cherche | a_terme)))
          & (ages >= C.AGE_TRAVAIL) & (ages < AGE_LEGAL))
    par_lieu = {}
    for i in np.nonzero(ok)[0].tolist():
        h = H[i]
        if h.vivant and h.role not in HORS_MARCHE and i not in d.grevistes and h.domicile is not None:
            par_lieu.setdefault(h.domicile.id, []).append(h)
    if not par_lieu: _refaire_pointes(p, d); return
    lieux_cands = [w.carte.lieux[k] for k in sorted(par_lieu)]
    dec = d.decideur
    for k in sorted(vac):
        lid, role = k
        lieu = w.carte.lieux[lid]
        proches = [l for l in sorted((l for l in lieux_cands if l.ile == lieu.ile), key=lambda l: (_km(p, d, l, lieu), l.id))
                   if _km(p, d, l, lieu) <= TRAJET_MAX_KM]
        for _ in range(vac[k]):
            faites, pourvu = 0, False
            for l in proches:
                reste = par_lieu[l.id]
                j = 0
                while j < len(reste) and faites < PROPOSITIONS_PAR_POSTE and not pourvu:
                    h = reste[j]
                    if not h.vivant or (h.travail is lieu and h.role == role) or not _a(int(col["tr_qualifs"][h.id]), role):
                        j += 1; continue
                    reste.pop(j); faites += 1                      # une offre par candidat et par jour
                    o = _offre_pour(p, d, h, lid, role, rng)
                    x, fin_cdd = _traits_offre(p, d, h, o)
                    a = dec.decider(h.id, ContexteOffre(x, fin_cdd))
                    p.compter("offre_emploi")
                    d.offres_jour.append((h.id, k, a))
                    if a == 1:
                        p.compter("offre_acceptee")
                        embaucher_contrat(p, h, _unite(p, d, lid, role), role, o.contrat, o.duree_j,
                                          o.taux if o.taux > 0 else None)
                        d.cible[k] = max(d.cible.get(k, 0), _effectif(p, lid, role))
                        pourvu = True
                    else: p.compter("offre_refusee")
                if pourvu or faites >= PROPOSITIONS_PAR_POSTE: break
            if faites == 0: break                                  # plus aucun candidat pour ce poste
    _refaire_pointes(p, d)


def _effectif(p, lid, role):
    return sum(1 for x in p.w._par_travail.get((lid, role), ()) if x.vivant and x.travail is not None and x.travail.id == lid)


# ================================================================== les greves ( 6 h 20, apres le marche )
def _membres(p, lid, role):
    """Les travailleurs d un etablissement ( lieu, metier ), ou d une branche publique ( lieu None )."""
    w = p.w
    if lid is None:
        return [x for (l, r), lst in sorted(w._par_travail.items()) if r == role for x in lst
                if x.vivant and x.travail is not None and x.travail.id == l]
    return [x for x in w._par_travail.get((lid, role), ()) if x.vivant and x.travail is not None and x.travail.id == lid]


def declencher_greve(p, lid, role, jours, motif="decision"):
    """Une greve de `jours` jours a l etablissement ( lid, role ), ou dans la branche publique `role` si lid est None.
    Les grevistes restent chez eux ; l etablissement ne produit pas. Rend la Greve ( None si la greve est interdite ou
    sans personne )."""
    w = p.w; d = p.domaine("travail")
    if role in INTERDITS_DE_GREVE or role in HORS_MARCHE or (lid, role) in d.en_greve: return None
    gens = [x for x in _membres(p, lid, role) if x.id not in d.grevistes]
    if not gens: return None
    gv = Greve(len(d.greves), lid, role, motif, p.jour, p.jour + int(jours) - 1)
    d.greves.append(gv); d.en_greve[(lid, role)] = gv
    ag = importlib.import_module(".d05_agenda", __package__) if p.a("agenda") else None
    col = p.colonnes["habitant"]
    for h in gens:
        gv.horaires[h.id] = h.horaire
        h.horaire = None
        if h.poste == "travail": h.lieu, h.poste = h.domicile, "maison"
        d.grevistes[h.id] = gv
        if ag is not None: ag.replanifier(p, h, rentrer=True)
    _arreter_etablissement(p, gv)
    p.noter("greve_debut", greve=gv.id, lieu=lid, metier=role, motif=motif, grevistes=len(gens))
    return gv


def _arreter_etablissement(p, gv):
    if gv.lieu is None: return
    e = p.w.entreprises.get(gv.lieu)
    if e is not None and e.role == gv.role: e.activite = 0.0


def _sortir_de_greve(p, d, h):
    gv = d.grevistes.pop(h.id, None)
    if gv is None: return
    hor = gv.horaires.pop(h.id, None)
    if h.vivant and h.travail is not None and h.horaire is None and (gv.lieu is None or h.travail.id == gv.lieu):
        h.horaire = hor
        if p.a("agenda"): importlib.import_module(".d05_agenda", __package__).replanifier(p, h)


def _finir_greve(p, d, gv):
    col = p.colonnes["habitant"]; w = p.w
    for i in list(gv.horaires):
        h = w.habitants[i]
        _sortir_de_greve(p, d, h)
    gv.fin = p.jour
    d.en_greve.pop((gv.lieu, gv.role), None)
    if gv.motif == "pouvoir_achat": _negocier(p, d, gv)
    p.noter("greve_fin", greve=gv.id, jours=gv.fin - gv.debut, salaires_perdus=round(gv.salaires_perdus, 2),
            production_perdue=round(gv.production_perdue, 2), allocations=round(gv.allocations, 2), hausse=round(gv.hausse, 4))


def _negocier(p, d, gv):
    """Une greve pour le pouvoir d achat : un employeur prive qui en a les moyens ( capitaux propres positifs et un mois
    de salaires en caisse ) rattrape la hausse des prix ; l Etat, lui, decide ses salaires au domaine 6."""
    if gv.lieu is None: return
    w = p.w; col = p.colonnes["habitant"]
    k = (gv.lieu, gv.role)
    ref = d.indice_ref.get(k, 100.0)
    ind = BQ.indice_des_prix(p)
    x = _payeur_de(p, d, gv.lieu, gv.role)
    if x is None or type(x).__name__ == "Gouvernement": return
    gens = _membres(p, gv.lieu, gv.role)
    masse = math.fsum(float(col["tr_taux"][h.id]) * float(col["tr_heures_prevues"][h.id]) for h in gens) * (1.0 + TAUX_EMPLOYEUR)
    cp = ECO.comptes(p, x).cp if (type(x).__name__ in ("Entreprise", "Marche")) else 0.0
    if cp > 0.0 and x.caisse >= MOIS_J * masse and ind > ref:
        hausse = ind / ref - 1.0
        for h in gens: col["tr_taux"][h.id] *= 1.0 + hausse
        gv.hausse = hausse
        d.indice_ref[k] = ind


def _payeur_de(p, d, lid, role):
    x = d.employeurs.get((lid, role))
    if x is not None: return x
    if _public(role): return p.w.gouv
    if role in ("convoyeur", "marchand"): return p.w.marches.get(lid)
    e = p.w.entreprises.get(lid)
    return e if e is not None and e.role == role else None


def _greves(p):
    """6 h 20 : les greves en cours comptent leur jour ( salaires et production perdus ) et s arretent a leur terme ou
    quand les arrieres sont payes ; puis la regle : un etablissement syndique debraye quand ses arrieres de salaire
    atteignent 3 jours de paie, ou, le 15 du mois, quand les prix ont pris 5 % depuis sa derniere hausse."""
    w = p.w; d = p.domaine("travail"); col = p.colonnes["habitant"]
    for k in sorted(d.en_greve, key=lambda k: d.en_greve[k].id):
        gv = d.en_greve[k]
        gens = [w.habitants[i] for i in gv.horaires]
        gv.salaires_perdus += math.fsum(float(col["tr_taux"][h.id]) * float(col["tr_heures_prevues"][h.id]) for h in gens)
        if gv.lieu is not None:
            e = w.entreprises.get(gv.lieu)
            if e is not None and e.role == gv.role:
                gv.production_perdue += len(gens) * 8.0 * sum(q * C.PRIX_MONDE[b] for b, q in e.produits.items())
        fini = p.jour > gv.fin_prevue
        if gv.motif == "arrieres" and _arrieres(p, d, gv.lieu, gv.role)[0] < 1.0: fini = True
        if fini: _finir_greve(p, d, gv)
        else: _arreter_etablissement(p, gv)
    # la regle
    etabs = {}
    for (lid, r), lst in w._par_travail.items():
        if r in INTERDITS_DE_GREVE or r in HORS_MARCHE or r in ("enfant", "retraite"): continue
        if not any(x.vivant and x.travail is not None and x.travail.id == lid and col["tr_syndique"][x.id] for x in lst): continue
        etabs[(None if _public(r) else lid, r)] = True
    ind = BQ.indice_des_prix(p)
    for k in sorted(etabs, key=lambda k: (k[0] or "", k[1])):
        if k in d.en_greve: continue
        d.indice_ref.setdefault(k, ind)
        jours_arr, _ = _arrieres(p, d, *k)
        if jours_arr >= ARRIERES_GREVE_J:
            declencher_greve(p, k[0], k[1], DUREE_GREVE_ARRIERES_MAX_J, "arrieres")
        elif p.jour % MOIS_J == JOUR_DU_MOIS_GREVE and ind >= (1.0 + PERTE_POUVOIR_ACHAT) * d.indice_ref[k]:
            declencher_greve(p, k[0], k[1], DUREE_GREVE_PA_J, "pouvoir_achat")


def _arrieres(p, d, lid, role):
    """( arrieres en jours de paie nette, en drachmes ) des travailleurs d un etablissement ( ou d une branche
    publique, lid None ) sur leur employeur : les creances de salaire du socle."""
    col = p.colonnes["habitant"]
    gens = _membres(p, lid, role)
    if not gens: return 0.0, 0.0
    x = p.w.gouv if lid is None else _payeur_de(p, d, lid, role)
    if x is None: return 0.0, 0.0
    menages = {h.menage for h in gens}
    du = math.fsum(cr.montant for cr in p.socle.creances.de(x) if cr.creancier in menages and cr.motif in MOTIFS_SALAIRE)
    paie = math.fsum(_net_jour(p, float(col["tr_taux"][h.id]), float(col["tr_heures_prevues"][h.id]), h.role) for h in gens)
    return (du / paie if paie > 0 else 0.0), du


# ================================================================== la note des offres ( 20 h 10 )
def _noter_offres(p):
    """Apres le repas : chaque choix en attente encaisse la journee de CE travailleur - son revenu net du jour, si son
    menage a mange, la stabilite de sa situation."""
    w = p.w; d = p.domaine("travail"); dec = d.decideur; col = p.colonnes["habitant"]
    nourri = w.nourri_menage
    for cle in [k for k, a in dec.attentes.items() if a.choix]:
        h = w.habitants[cle]
        if not h.vivant: r = 0.0
        else:
            _, stab = _revenu_actuel(p, d, h)
            mange = 1.0 if nourri.get(h.menage.id, True) else 0.0
            r = (min(1.0, float(col["tr_net_jour"][cle]) / NORME_REVENU_J) + mange + stab) / 3.0
        dec.noter(cle, r, p.jour)
    for cle in [k for k, a in dec.attentes.items() if not a.choix]: del dec.attentes[cle]


# ================================================================== la mesure ( 23 h 50 )
def mesurer_emploi(p):
    """L emploi au sens du BIT, par le statut du domaine : en emploi ( salarie, fonctionnaire, independant, y compris
    en greve ), chomeurs ( sans emploi, qui cherchent ), inactifs ( etudes, foyer, invalidite, decourages, retraite ).
    Taux d emploi des 20-64 ans, brut et standardise sur une population a moitie feminine ( la structure par sexe de la
    population est celle du domaine 1 : le taux standardise mesure les comportements, pas la composition )."""
    w = p.w; H = w.habitants; n = len(H)
    col = p.colonnes["habitant"]
    viv = w.table.vivant[:n] == 1
    age = _ages(p, n); st = col["tr_statut"][:n]; sx = col["sexe"][:n]
    m = viv & (age >= 20) & (age < 65)
    emp = np.isin(st, EN_EMPLOI); cho = st == CHOMEUR
    out = {"jour": p.jour, "pop_20_64": int(m.sum()), "emploi_20_64": int((m & emp).sum()),
           "chomeurs_20_64": int((m & cho).sum())}
    par = {}
    for s, nom in ((HOMME, "hommes"), (FEMME, "femmes")):
        ms = m & (sx == s)
        par[nom] = (m & emp & (sx == s)).sum() / ms.sum() if ms.sum() else 0.0
        out[f"taux_{nom}"] = float(par[nom])
    out["taux_emploi"] = out["emploi_20_64"] / out["pop_20_64"] if out["pop_20_64"] else 0.0
    out["taux_standardise"] = 0.5 * (par["hommes"] + par["femmes"])
    actifs = out["emploi_20_64"] + out["chomeurs_20_64"]
    out["taux_chomage"] = out["chomeurs_20_64"] / actifs if actifs else 0.0
    out["part_hommes"] = float((m & (sx == HOMME)).sum() / max(1, m.sum()))
    out["statuts"] = {STATUTS[k]: int((viv & (st == k)).sum()) for k in range(len(STATUTS))}
    pay = np.isin(st, PAYES_A_L_HEURE) & viv
    out["syndiques"] = float(col["tr_syndique"][:n][pay].sum() / max(1, pay.sum()))
    return out


def _bilan_du_jour(p):
    d = p.domaine("travail")
    d.serie.append(mesurer_emploi(p))


# ================================================================== API pour les autres domaines
def declarer_employeur(p, lieu_id, role, payeur):
    """Un domaine ( 9, 10, 11, 25... ) declare qui paie les travailleurs de metier `role` au lieu `lieu_id` : un
    detenteur inscrit au registre, avec une caisse. La paie le fait payer ; un impaye devient une creance sur lui."""
    if not hasattr(payeur, "caisse"): raise ValueError("un payeur a une caisse")
    d = p.domaine("travail")
    d.employeurs[(lieu_id, role)] = payeur


def ouvrir_postes(p, lieu_id, role, effectif):
    """Un domaine demande `effectif` travailleurs de metier `role` au lieu `lieu_id` : le marche du matin les cherche."""
    if not 0 <= effectif < 10 ** 7: raise ValueError(f"effectif invalide {effectif!r}")
    p.domaine("travail").postes_ouverts[(lieu_id, role)] = int(effectif)


def cout_horaire(p, h):
    """Ce que coute une heure de `h` a son employeur : brut ( et facteur public ) + cotisation patronale."""
    col = p.colonnes["habitant"]
    f = p.w.gouv.facteur_salaire_public if _public(h.role) else 1.0
    return float(col["tr_taux"][h.id]) * f * (1.0 + TAUX_EMPLOYEUR)


def cout_salarial_du_jour(p, payeur):
    """Ce que la paie de 18 h demandera a `payeur` pour les heures deja creditees aujourd hui ( la tresorerie de paie
    des domaines 2 et 3 devrait lire ceci plutot que population.SALAIRE_HORAIRE )."""
    d = p.domaine("travail")
    return math.fsum(cout_horaire(p, h) * h.heures_jour for h in d.pointes
                     if h.vivant and h.heures_jour > 0 and _payeur(p, d, h) is payeur)


def payer_prime(p, h, brut, payeur, motif=None):
    """Une prime ( solde d operation, heures supplementaires ) de `brut` drachmes a `h`, par `payeur`, avec ses
    cotisations et son impot, comme un salaire. Rend le net verse."""
    d = p.domaine("travail")
    if not 0.0 < brut < 1e9: raise ValueError(f"prime invalide {brut!r}")
    agg = {k: 0.0 for k in AGREGATS}
    _payer_employeur(p, d, payeur, [(h, round(brut, 2))], agg, credit_jours=False)
    for k, v in agg.items(): _ajouter(d.cumul, k, v)
    return agg["net_paye"]


def fixer_taux(p, h, taux):
    """Le domaine 25 ( soldes ) ou 6 ( grille publique ) pose le taux horaire brut du contrat de `h`."""
    if not SMIC_HORAIRE - 1e-9 <= taux < 1e4: raise ValueError(f"taux hors [SMIC ; 10 000] : {taux!r}")
    p.col("habitant", "tr_taux")[h.id] = taux


def en_greve(p, h): return h.id in p.domaine("travail").grevistes


def assiette_ir(p):
    """{ habitant : revenu imposable de l annee civile ( salaires nets de cotisations, revenus des independants ) }."""
    col = p.colonnes["habitant"]; n = len(p.w.habitants)
    a = col["tr_imposable_an"][:n]
    return {int(i): float(a[i]) for i in np.nonzero(a > 0)[0]}


def bilan_caisse(p):
    """Les comptes de la caisse lus dans le grand livre ( ses propres compteurs a cote, pour le recoupement )."""
    d = p.domaine("travail")
    return {"caisse": d.caisse.caisse, "recu": dict(d.caisse.recu), "verse": dict(d.caisse.verse),
            "pensions": len(d.pensions), "indemnises": sum(1 for x in d.indemnites.values() if x.fin >= p.jour)}


def masse_salariale_brute(p):
    return {k: d_ for k, d_ in p.domaine("travail").jour.items()}


# ================================================================== installation
MOTIFS = (("cotisation_salariale", "cotisation"), ("cotisation_patronale", "cotisation"),
          ("cotisation_independant", "cotisation"), ("pension_vieillesse", "prestation"),
          ("pension_invalidite", "prestation"), ("indemnite_chomage", "prestation"),
          ("financement_etat_securite_sociale", "transfert_courant"), ("cotisation_syndicale", "transfert_courant"),
          ("allocation_greve", "transfert_courant"), ("placement_reserves", "financier"))
COLONNES = (("tr_statut", np.int8, HORS), ("tr_contrat", np.int8, AUCUN), ("tr_debut_j", np.int32, 0),
            ("tr_fin_j", np.int32, -1), ("tr_taux", np.float64, 0.0), ("tr_heures_prevues", np.float32, 0.0),
            ("tr_carriere_j", np.int32, 0), ("tr_carriere", np.int8, 0), ("tr_echelon", np.int8, 0), ("tr_jours_cotises", np.float64, 0.0),
            ("tr_assiette", np.float64, 0.0), ("tr_qualifs", np.int32, 0), ("tr_syndique", np.int8, 0),
            ("tr_pointage", np.int16, 0), ("tr_solde_heures", np.float32, 0.0), ("tr_jours_mois", np.float32, 0.0),
            ("tr_imposable_an", np.float64, 0.0), ("tr_net_jour", np.float64, 0.0), ("tr_chomage_j", np.int32, -1),
            ("tr_fin_etudes", np.int32, -1))
def _tolerance_convois(p):
    """Le plus long aller-retour de convoi d une capitale a un lieu de son ile, en heures, plus un pas : le moteur
    credite ces heures au depart ( Monde.lancer_convoi ), le pointage les voit passer en route."""
    w = p.w; km = 0.0
    for c in w.carte.capitales:
        for l in w.carte.lieux.values():
            if l.ile == c.ile and l is not c: km = max(km, w.carte.km_route(c, l))
    pas = math.ceil(km / C.VITESSE_CONVOI_KMH * 60.0 / C.MINUTES_PAR_PAS)
    return max(TOLERANCE_HEURES, (2 * pas + 1) * C.MINUTES_PAR_PAS / 60.0)


RECENSER_INACTIFS = True           # faux : le monde du moteur, ou tous les adultes travaillent ( porte test_inactifs )


def installer(p):
    w = p.w; L = p.socle.livre
    for m, nature in MOTIFS: L.declarer_motif(m, nature, "travail")
    J = p.socle.journal
    for t, champs in (("retraite_liquidee", ("habitant", "age", "pension", "annees", "nature")),
                      ("greve_debut", ("greve", "lieu", "metier", "motif", "grevistes")),
                      ("greve_fin", ("greve", "jours", "salaires_perdus", "production_perdue", "allocations", "hausse")),
                      ("fin_etudes", ("habitant", "age", "metier")), ("accident_mortel", ("habitant", "metier"))):
        J.declarer(t, "travail", "individuel", champs)
    for t in ("offre_emploi", "offre_acceptee", "offre_refusee", "promotion", "fin_cdd", "cdd_renouvele",
              "indemnite_ouverte", "accident_travail", "heures_non_travaillees", "arrieres_salaire"):
        J.declarer(t, "travail", "compte")
    ch = p.colonnes["habitant"]
    for nom, dt, defaut in COLONNES: ch.ajouter(nom, dt, defaut)
    ch.assurer(len(w.habitants))
    d = Travail()
    d.inactifs = RECENSER_INACTIFS
    d.par_eid = {e.id: e for e in w.entreprises.values()}
    d.tolerance_heures = _tolerance_convois(p)
    p.domaines["travail"] = d
    reg = p.socle.registre
    reg.inscrire("securite_sociale", "administrations", _membres_caisse, "caisse", None, "CaisseSecuriteSociale")
    reg.inscrire("syndicats", "associations", _membres_syndicats, "caisse", None, "Syndicat")
    for s in d.syndicats.values(): BQ.ouvrir_compte(p, s)
    _recensement(p, d, p.hasard("travail_recensement"))
    ind = BQ.indice_des_prix(p)
    for (lid, r) in d.cible:
        d.indice_ref[(None if _public(r) else lid, r)] = ind
    _refaire_pointes(p, d)
    d.decideur = p.decideur(POINT_OFFRE)
    w.paie = RemplacePaie(p)
    w.embaucher = RemplaceEmbaucher(p)
    for minute in range(0, 24 * 60, C.MINUTES_PAR_PAS):
        if minute != C.HEURE_PAIE * 60: p.routine(minute / 60.0, 99, "travail", _pointer)
    p.routine(6 + 10 / 60, 50, "travail", _carrieres)
    p.routine(6 + 20 / 60, 40, "travail", _marche_du_travail)
    p.routine(6 + 20 / 60, 60, "travail", _greves)
    p.routine(20 + 10 / 60, 40, "travail", _noter_offres)
    p.routine(23 + 50 / 60, 99, "travail", _bilan_du_jour)
    return d


# ================================================================== controles ( pour les portes )
def verifier_bulletins(p):
    """Les bulletins gardes du dernier jour, au centime : ( pire ecart brut - ( net + retenues ), pire ecart d un
    montant au centime pres - brut, cotisations, impot, syndicale -, nombre de bulletins ), en drachmes. Le net est
    le reste : ce controle voit un bulletin dont une ligne a ete touchee apres coup."""
    d = p.domaine("travail")
    e1 = e2 = 0.0
    for i, k, brut, cs, cp, ir, sy, net, paye, f in d.bulletins:
        e1 = max(e1, abs(brut - (net + ir + sy + cs)))
        for x in (brut, cs, cp, ir, sy): e2 = max(e2, abs(x * 100.0 - round(x * 100.0)) / 100.0)
    return e1, e2, len(d.bulletins)


def anomalies_heures(p, depuis=0):
    return [a for a in p.domaine("travail").anomalies if a[0] >= depuis]
