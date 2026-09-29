"""DOMAINE 19 - EDUCATION ET FORMATION : ECOLES, DIPLOMES, EXAMENS, APPRENTISSAGE, FORMATION DES ADULTES.

FICHE
1. Classes. Programme ( une formation au cycle instruction -> exercice -> debrief -> qualification : duree de chaque
   phase, competence exercee, qualification du domaine 4 et diplome delivres, seuil de l epreuve, allocation ),
   Stagiaire ( un adulte en formation : sa phase, ses jours, ses notes d exercice ), ContexteOrientation ( ce qu un
   eleve et sa famille voient en fin de gymnase ), EcoleQualifiante ( l ecole du moteur, monde/ecole.py, ETENDUE : un
   eleve a memoire ou LLM suit le meme cycle et sa qualification delivre un diplome du pays ), Education ( l etat du
   domaine ). Par habitant, en COLONNES ( p.colonnes["habitant"] ) : ed_cycle, ed_annee, ed_filiere ( ou il en est ),
   ed_annees ( annees de scolarite validees : la preuve d une scolarite ), ed_diplomes ( un bit par diplome ),
   ed_lecture, ed_calcul, ed_technique ( les competences, en annees d ecole equivalentes ), ed_aptitude et
   ed_habilete ( la vitesse d apprentissage, academique et technique : CACHEES, aucune decision ne les lit ),
   ed_absences et ed_classes ( jours manques et jours de classe de l annee ), ed_redoublements, ed_frontistirio,
   ed_note ( la note de l examen de juin, sur 20 ) et ed_resultat ( -1 aucun, 0 echec, 1 reussite ). ~ 32 octets par
   habitant. Colonnes plutot que tables eparses : 25 % des habitants sont scolarises et TOUS portent un niveau
   d etudes, que le travail, la culture et l armee lisent. Tables eparses : les stagiaires adultes, le suivi des choix
   d orientation en attente de note.
2. Invariants et ce que le domaine detient. Aucune qualification des metiers a titre ( medecin, infirmier, enseignant,
   officier, policier : QUALIFS_A_DIPLOME ) sans le diplome qui la donne ; aucun diplome sans les annees de scolarite
   qu il exige ( `anomalies` ). Un eleve inscrit de 16 ans et plus est etudiant pour le domaine 4 ( tr_fin_etudes
   dans l avenir ) ; un jeune de 16 ans et plus qui n est plus inscrit sort des etudes a l aube suivante. Le domaine ne
   DETIENT ni argent ni bien : les cours prives ( frontistiria ) vont du menage au marche de sa zone ( services
   marchands ), l allocation de formation de l Etat au menage du stagiaire ; tout passe par le grand livre. Les repas
   scolaires ( HMT-177 ) : l Etat paie le repas au marche de la zone, qui en consomme la nourriture ; le repas baisse
   le besoin du soir de l eleve par le crochet du moteur ( Monde.manger_dehors, lu par Monde.repas ).
3. Decision `orientation` ( chaque eleve qui obtient l apolytirio du gymnase, a la cloture de l annee, le 20 juin ) :
   lycee general, lycee professionnel, arret. Traits : sa moyenne de juin sur 20, son niveau technique, son taux
   d absence, ses redoublements, ce que la caisse du menage paierait de cours prives, le plus haut niveau d etudes des
   adultes du menage, son retard d age. Note ( horizon 365 jours : l orientation se lit en mois, jusqu aux examens de
   juin suivants, 355 jours plus tard ; 365 est le maximum du socle ) : chaque soir, pour CET eleve, la valeur des
   competences acquises ce jour ( rendement d une annee d etude sur une vie active, actualise ), plus son revenu net du
   jour, moins ce que son menage a paye pour lui, le tout en journees de deux SMIC nets, plus ou moins une prime le
   jour de son examen de juin ( reussi ou echoue ). Regle : general si la moyenne atteint 12, ou 10 avec un parent
   diplome du superieur ; arret si elle est sous 7 avec des absences ou un redoublement ; professionnel sinon.
   Temoin : toujours le lycee general. Le redoublement est une regle du conseil de classe ( note et absences ).
4. Evenements. Individuels : diplome_superieur, decrochage, qualification_formation. Comptes : passage, redoublement,
   diplome, panhellenies_candidat, panhellenies_admis, orientation_general, orientation_pro, orientation_arret,
   frontistirio_paye, frontistirio_arrete, formation_entree, formation_echec, allocation_formation, rentree,
   places_manquantes ; repas_scolaires, repas_scolaires_manques, repas_scolaires_sans_crochet ( declares au premier
   repas ).
5. Liens. Travail ( 4 ) : `qualifier` ( les diplomes donnent les qualifications de QUALIFICATIONS ), tr_fin_etudes
   ( le domaine dit qui etudie encore : le tirage TITRES_DE_SORTIE s eteint quand le domaine est installe ),
   tr_statut ( chomeurs en formation ), tr_net_jour ( la note ), `ouvrir_postes` ( enseignants a la rentree, au
   ratio grec ). Immobilier ( 13 ) : `batiments( p, "ecole" )`, `places_ecole`. Etat ( 6 ) : le Tresor paie
   l allocation de formation ; les enseignants sont payes par la paie du domaine 4 sur la grille publique ( ligne
   education ). Population ( 1 ) : ages, menages. Socle : calendrier ( feries grecs, Paques orthodoxe ). Ne remplace
   aucune methode du moteur. API en fin de fichier pour les domaines 4, 23, 25 et 27.
6. Portes : tests_d19_education.py.
7. Arma : aucun objet ( l ecole est un batiment du domaine 13, Land_School_01_F ; l eleve a le corps de l habitant ).
8. Cout. Chaque jour de classe : une passe vectorisee sur les inscrits ( presence, gains, absences ) ; hors classe, la
   meme passe pour l oubli. Le 10 juin ( examens ) et le 20 juin ( passage ) : des passes vectorisees et une boucle
   sur les seuls diplomes, admis et orientes ; la rentree : des comptes par zone et par menage ( bincount ). Chaque
   soir : les choix d orientation en attente ( une cohorte ) et la synchronisation de tr_fin_etudes ( une passe ).
   Lineaire en habitants. Mesure : tests_d19_education.test_cout."""
import datetime as dt, math
import numpy as np
from .. import config as C, population as PO, ecole as ECOLE_MOTEUR
from ..socle import decision as D, calendrier as CAL
from . import pays as P, d04_travail as TR, d13_immobilier as IM

JOURS_AN = 365.0
EUROS = P.EUROS_PAR_DRACHME
LOIN_J = 3650                     # tr_fin_etudes d un eleve inscrit : l avenir ( le domaine redit chaque soir qui etudie )

# ================================================================== le systeme scolaire grec ( la loi )
# Maternelle ( nipiagogeio ) : deux ans obligatoires des 4 ans ( loi 4521/2018, art. 33, generalisee en 2020-2021 ;
# entrent les enfants qui ont 4 ans au 31 decembre ). Primaire ( dimotiko ) : 6 ans, de 6 a 12 ans. Gymnase : 3 ans,
# de 12 a 15 ; la scolarite obligatoire finit avec lui ( loi 1566/1985, art. 2 ). Lycee general ( GEL ) ou
# professionnel ( EPAL, loi 4386/2016 ) : 3 ans, de 15 a 18, plus une annee d apprentissage facultative apres l EPAL
# ( loi 4763/2020 ). Examens panhelleniques a la fin du GEL : la note ouvre l universite ( AEI, 4 ans, 5 pour les
# ingenieurs, 6 pour la medecine ), les ecoles militaires ( ASEI, 4 ans ) et de police ( Scholi Astyfylakon, 2 ans ;
# a verifier ). IEK ( formation professionnelle post-secondaire, loi 4763/2020 ) : 4 semestres et un semestre de stage.
AUCUN, MATERNELLE, PRIMAIRE, GYMNASE, LYCEE_GENERAL, LYCEE_PRO, UNIVERSITE, IEK, ECOLE_MILITAIRE, ECOLE_POLICE = range(10)
CYCLES = ("aucun", "maternelle", "primaire", "gymnase", "lycee_general", "lycee_pro", "universite", "iek",
          "ecole_militaire", "ecole_police")
NC = len(CYCLES)
DUREE = np.array([0, 2, 6, 3, 3, 3, 4, 3, 4, 2], np.int64)          # annees ( IEK : 2 ans et le semestre de stage )
AGE_ENTREE = np.array([0, 4, 6, 12, 15, 15, 18, 18, 18, 18], np.float64)
SCOLAIRES = (MATERNELLE, PRIMAIRE, GYMNASE, LYCEE_GENERAL, LYCEE_PRO)    # dans les batiments ecole du domaine 13
SUPERIEURS = (UNIVERSITE, IEK, ECOLE_MILITAIRE, ECOLE_POLICE)
# annees de scolarite validees par annee reussie ( la maternelle ne compte pas ; le stage de l IEK non plus )
COMPTE = np.array([0, 0, 1, 1, 1, 1, 1, 1, 1, 1], np.int64)
ANNEE_APPRENTISSAGE = 4           # l annee de l EPAL apres le diplome
# groupes de calendrier : 0 maternelle et primaire, 1 secondaire, 2 superieur ; 3 formation des adultes
PRIM, SECOND, SUP, ADULTES = 0, 1, 2, 3
GROUPE = np.array([PRIM, PRIM, PRIM, SECOND, SECOND, SECOND, SUP, SUP, SUP, SUP], np.int64)

# filieres du superieur
GENERALE, MEDECINE, SOINS, PEDAGOGIE, TECHNIQUE = range(5)
FILIERES = ("generale", "medecine", "soins", "pedagogie", "technique")
DUREE_MEDECINE = 6

# ================================================================== les diplomes et les qualifications du domaine 4
DIPLOMES = ("primaire", "gymnase", "lycee", "epal", "iek", "universite", "medecine", "soins", "pedagogie", "militaire",
            "police", "poids_lourd", "formation")
BIT = {d: 1 << k for k, d in enumerate(DIPLOMES)}
# annees de scolarite validees qu un diplome exige : le falsificateur " diplome sans scolarite "
ANNEES_REQUISES = {"primaire": 6, "gymnase": 9, "lycee": 12, "epal": 12, "iek": 14, "universite": 16, "medecine": 18,
                   "soins": 14, "pedagogie": 16, "militaire": 16, "police": 14, "poids_lourd": 6, "formation": 6}
# les qualifications du domaine 4 que donne un diplome
QUALIF_DU_DIPLOME = {"medecine": "diplome_medecine", "soins": "diplome_infirmier", "pedagogie": "diplome_enseignant",
                     "militaire": "ecole_officiers", "police": "ecole_police", "poids_lourd": "permis_poids_lourd",
                     "epal": "securite_industrie"}
# les qualifications qui ne s obtiennent QUE par un diplome ( le permis s obtient aussi hors ecole, la formation
# militaire au service du domaine 25, la securite a l embauche )
QUALIFS_A_DIPLOME = {"diplome_medecine": "medecine", "diplome_infirmier": "soins", "diplome_enseignant": "pedagogie",
                     "ecole_officiers": "militaire", "ecole_police": "police"}
for _q in QUALIF_DU_DIPLOME.values():
    if _q not in TR.BIT: raise RuntimeError(f"education : qualification {_q!r} inconnue du domaine 4")
SUPERIEUR_BITS = BIT["universite"] | BIT["medecine"] | BIT["pedagogie"] | BIT["militaire"]
SECONDAIRE_BITS = BIT["lycee"] | BIT["epal"] | BIT["iek"] | SUPERIEUR_BITS | BIT["police"] | BIT["soins"]

# ================================================================== le calendrier scolaire
# PD 79/2017 ( maternelle et primaire ) : cours du 11 septembre au 15 juin ; vacances de Noel du 24 decembre au
# 7 janvier, de Paques du lundi saint au dimanche de Thomas ; fetes scolaires le 17 novembre ( Polytechneio ) et le
# 30 janvier ( Trois Hierarques ). Secondaire : memes vacances, cours jusqu a la fin mai puis examens de juin ( a
# verifier ). Superieur : semestres d octobre a janvier et de fevrier a juin, sessions d examens en janvier-fevrier
# ( a calibrer ). Formation des adultes : jours ouvres, hors aout et fetes de fin d annee ( a calibrer ).
FIN_COURS = {PRIM: (6, 15), SECOND: (5, 31), SUP: (6, 10)}
DEBUT_COURS = {PRIM: (9, 11), SECOND: (9, 11), SUP: (10, 1)}
SESSION_HIVER_SUP = ((1, 21), (2, 19))
FETES_SCOLAIRES = ((11, 17), (1, 30))
DATE_EXAMENS = (6, 10)            # les notes de l annee : examens de juin, panhelleniques comprises
DATE_PASSAGE = (6, 20)            # le conseil de classe, les diplomes, l orientation, les admissions
DATE_RENTREE = (9, 10)            # la veille des cours : inscriptions, cours prives, postes d enseignants
MOIS_FRONTISTIRIO = (10, 11, 12, 1, 2, 3, 4, 5)   # cours prives factures d octobre a mai

# ================================================================== apprendre
# Les competences se comptent en ANNEES D ECOLE EQUIVALENTES : un eleve d aptitude 1 present tous les jours gagne, en un
# an, RYTHME[cycle] en lecture, calcul et technique. PISA : un ecart-type ( 100 points ) vaut environ trois annees
# d ecole ; l aptitude ( ecart-type 0,2 ) fait l ecart des eleves d une meme classe ( a calibrer ).
RYTHME = np.array([[0.0, 0.0, 0.0],        # aucun
                   [0.5, 0.5, 0.0],        # maternelle
                   [1.0, 1.0, 0.1],        # primaire
                   [1.0, 1.0, 0.2],        # gymnase
                   [1.0, 1.0, 0.1],        # lycee general
                   [0.5, 0.6, 1.0],        # lycee professionnel
                   [0.6, 0.6, 0.8],        # universite
                   [0.3, 0.3, 1.0],        # IEK
                   [0.5, 0.6, 1.0],        # ecole militaire
                   [0.5, 0.4, 1.0]])       # ecole de police
# le niveau attendu a l entree d un cycle : le chemin ordinaire ( maternelle, primaire, gymnase, lycee general )
BASE = np.zeros((NC, 3))
BASE[PRIMAIRE] = BASE[MATERNELLE] + DUREE[MATERNELLE] * RYTHME[MATERNELLE]
BASE[GYMNASE] = BASE[PRIMAIRE] + DUREE[PRIMAIRE] * RYTHME[PRIMAIRE]
BASE[LYCEE_GENERAL] = BASE[LYCEE_PRO] = BASE[GYMNASE] + DUREE[GYMNASE] * RYTHME[GYMNASE]
for _c in SUPERIEURS: BASE[_c] = BASE[LYCEE_GENERAL] + DUREE[LYCEE_GENERAL] * RYTHME[LYCEE_GENERAL]
# ce que pese chaque competence a l examen de chaque cycle
POIDS_EXAMEN = np.array([[0.5, 0.5, 0.0]] * 5 + [[0.25, 0.25, 0.5], [0.35, 0.35, 0.3], [0.2, 0.2, 0.6], [0.2, 0.2, 0.6],
                                                  [0.2, 0.2, 0.6]])
POIDS_EXAMEN[AUCUN] = (0.5, 0.5, 0.0)
P_ABSENCE = 0.04                  # un eleve manque ~ 4 % des jours ( maladie, famille ; a calibrer )
OUBLI_ABSENCE = 0.5               # un jour manque : sa lecon perdue, et la moitie d une lecon oubliee ( a calibrer )
OUBLI_VACANCES_AN = 0.10          # ce que les vacances font perdre en un an ( " summer slide " : ~ un mois d ecole ;
                                  # Cooper et al. 1996, a calibrer )
BONUS_FRONTISTIRIO = 0.15         # ce que les cours prives ajoutent au rythme en lecture et en calcul ( a calibrer : les
                                  # etudes grecques trouvent un effet modeste sur les notes panhelleniques )
APTITUDE_SD = 0.2
CORR_APTITUDES = 0.3
DECALAGE_CLASSE = np.array([0.08, 0.03, -0.03])   # aisee, moyenne, populaire ( codes du moteur ; gradient PISA, a calibrer )

# ================================================================== examiner, passer
# La note de juin sur 20 : 12 au niveau attendu, 12 points par ecart relatif de 1, bruit de copie d ecart-type 1,2.
NOTE_CENTRE, NOTE_PENTE, NOTE_BRUIT = 12.0, 12.0, 1.2
# Passage : la note minimale ( un rattrapage de septembre est compris ) et le taux d absence maximal. Gymnase et lycee :
# 114 heures d absence non justifiees, 164 justifiees, sur ~ 1 100 heures de cours ( a verifier ) : 15 %.
SEUIL_PASSAGE = np.array([0.0, 0.0, 4.0, 6.0, 6.0, 5.5, 7.0, 6.5, 8.0, 7.0])
LIMITE_ABSENCES = np.array([1.0, 1.0, 1.0, 0.15, 0.15, 0.15, 1.0, 1.0, 0.10, 0.10])
# Decrochage a la fin de l annee ( par an ; multiplie apres un echec ) ; pas avant 15 ans, fin de l obligation.
# Institut de politique educative ( IEP, etudes sur l abandon ) : quelques % au gymnase et au GEL, ~ 12 a 15 % d une
# cohorte d EPAL ( a verifier ) ; superieur et IEK : a calibrer.
P_DECROCHAGE = np.array([0.0, 0.0, 0.0, 0.01, 0.01, 0.04, 0.03, 0.06, 0.02, 0.02])
MULT_ECHEC = 4.0
AGE_FIN_OBLIGATION = 15.0
# Panhelleniques : la note minimale d admission ( Elachisti Vasi Eisagogis, loi 4777/2021 : ~ 10 sur 20 selon la
# filiere ; a calibrer ) ; les filieres par prestige, leur note minimale, leur part de places par candidat ( numerus
# clausus ; ordres de grandeur des admissions grecques : medecine ~ 1 400, ecoles militaires ~ 1 000, police ~ 1 500,
# pedagogie et disciplines enseignees ~ 8 %, soins infirmiers ~ 2 500, sur ~ 90 000 candidats : a calibrer ) et la part
# des candidats qui les demandent ( a calibrer ).
EBE = 10.0
FILIERES_ADMISSION = (   # ( cycle, filiere, note minimale, places par candidat, part qui la demande )
    (UNIVERSITE, MEDECINE, 18.0, 0.016, 0.5),
    (ECOLE_MILITAIRE, GENERALE, 16.0, 0.012, 0.25),
    (ECOLE_POLICE, GENERALE, 14.0, 0.020, 0.30),
    (UNIVERSITE, PEDAGOGIE, 13.0, 0.080, 0.40),
    (UNIVERSITE, SOINS, 11.0, 0.030, 0.35),
    (UNIVERSITE, GENERALE, EBE, math.inf, 1.0))
PART_FEMMES_MILITAIRE = 0.3       # une candidate demande une ecole militaire 0,3 fois moins ( a calibrer )
P_IEK_APRES_GEL = 0.35            # un recale du GEL entre en IEK ( a calibrer )
P_IEK_APRES_EPAL = 0.20
P_APPRENTISSAGE = 0.15            # diplomes de l EPAL qui font l annee d apprentissage ( a calibrer )
P_IEK_SANTE = 0.3                 # part des IEK en filiere sante ( aide-soignant : le moteur ne le distingue pas de
                                  # l infirmier, a calibrer )

# ================================================================== les cours prives ( frontistiria )
# Tres repandus : la plupart des lyceens grecs s y preparent aux panhelleniques ( enquetes KANEP-GSEE ; ~ 1 milliard
# d euros par an payes par les familles : a verifier ). Part des eleves inscrits et prix mensuel, en euros.
FRONTISTIRIO = {   # ( cycle, annee ou 0 pour toutes ) : ( part, euros par mois )
    (PRIMAIRE, 0): (0.15, 50.0), (GYMNASE, 0): (0.45, 110.0), (LYCEE_GENERAL, 1): (0.55, 170.0),
    (LYCEE_GENERAL, 2): (0.60, 190.0), (LYCEE_GENERAL, 3): (0.80, 280.0), (LYCEE_PRO, 0): (0.10, 60.0)}
FACTEUR_CLASSE_FRONT = np.array([1.25, 1.0, 0.7])   # aisee, moyenne, populaire ( a calibrer )
MOIS_DE_RESERVE_FRONT = 2.0       # la famille inscrit si sa caisse couvre deux mois de cours

# ================================================================== les repas scolaires ( HMT-177, 30/09 )
# « Sxolika Geymata » ( loi 4455/2017 art. 12, lois 4756/2020 et PD 77/2023 ; ministere de la Cohesion sociale et de la
# Famille, OPEKA ) : un repas chaud a midi, gratuit, dans les ecoles PRIMAIRES publiques choisies sur des criteres
# socio-economiques ( revenu par habitant, chomage, zones reculees, iles, frontiere ). 2025-2026 : 231 062 repas par
# jour, 1 918 ecoles, 45 % des ecoles et 47 % des eleves du primaire ; 115 millions d euros en 2025 ( ministere,
# declaration de D. Michailidou ). Dans le moteur : les lieux les plus pauvres d abord ( revenu par unite de
# consommation ), jusqu a 47 % des eleves du primaire, fixes a la rentree ( la KYA de l annee ).
REPAS_SCOLAIRES = True            # le bras C d une mesure l eteint ( les ecoles couvertes sont calculees quand meme )
PART_ELEVES_COUVERTS = 0.47       # ministere, 2025-2026
RATION_REPAS = 0.24               # CHOIX ( a calibrer ) : un dejeuner d enfant ~ un tiers de ses besoins, ~ 600 kcal
PRIX_REPAS_EUR = 2.8              # CHOIX ( a verifier ) : 115 M euros / ( 231 062 repas x ~ 175 jours de classe )
PRIX_REPAS_DR = PRIX_REPAS_EUR / EUROS

# ================================================================== le ratio eleves / enseignant
# OCDE, Regards sur l education 2023 ( donnees 2021 ) : Grece ~ 9 eleves par enseignant au primaire, ~ 8 au premier
# cycle du secondaire, ~ 9 au second ( a verifier ) ; la maternelle ~ 10. Cible du ministere a la rentree.
RATIO_CIBLE = 9.0

# ================================================================== la formation des adultes
P_FORMATION_CHOMEUR_AN = 0.05     # chomeurs inscrits entrant en formation dans l annee ( DYPA ; a calibrer )
ANCIENNETE_CHOMAGE_J = 60
P_FORMATION_CONTINUE_AN = 0.04    # salaries de 25 a 64 ans en formation ( Eurostat trng_lfse_01, Grece ~ 4 % ; a verifier )
ALLOCATION_FORMATION_J = 5.0 * 5.0 / EUROS    # DYPA : ~ 5 euros de l heure, 5 heures par jour ( a calibrer )
DEBRIEF_GAIN = 0.5                # le debrief rend la moitie de ce que l exercice a montre de manque ( a calibrer )
BRUIT_EPREUVE = 2.0

# ================================================================== la note de l orientation
# La valeur d une annee de competences : le rendement d une annee d etude ( ~ 7 % du salaire, Psacharopoulos et
# Patrinos 2018 ; a verifier pour la Grece ) sur un SMIC net annuel, pendant 45 ans actualises a 3 %, en journees de
# deux SMIC nets ( TR.NORME_REVENU_J ). Les poids des trois competences sur le marche du travail : a calibrer.
RENDEMENT_ANNEE = 0.07
SMIC_NET_AN = TR.SMIC_MENSUEL_EUR * 14.0 * (1.0 - TR.TAUX_SALARIE) / EUROS
ANNUITE_45_ANS = (1.0 - 1.03 ** -45) / 0.03
VALEUR_ANNEE = RENDEMENT_ANNEE * SMIC_NET_AN * ANNUITE_45_ANS / TR.NORME_REVENU_J
POIDS_VALEUR = np.array([0.30, 0.35, 0.35])
PRIME_EXAMEN = 5.0                # journees de deux SMIC : ce que vaut une annee reussie plutot que redoublee ( a calibrer )
HORIZON_ORIENTATION = 365
GENERAL, PRO, ARRET = range(3)
CYCLE_DU_CHOIX = (LYCEE_GENERAL, LYCEE_PRO, AUCUN)

# ================================================================== le niveau d etudes des adultes au recensement
# Eurostat edat_lfs_9903 ( Grece 2023, a verifier ) : part des niveaux CITE 0-2, 3-4, 5-8 par age. Dans 3-4 : lycee
# general, EPAL, IEK ( a calibrer ) ; dans 0-2 : gymnase ou primaire seul ( a calibrer ).
ATTEINT = ((18, (0.05, 0.60, 0.35)), (25, (0.08, 0.48, 0.44)), (35, (0.13, 0.47, 0.40)), (45, (0.22, 0.48, 0.30)),
           (55, (0.35, 0.40, 0.25)), (65, (0.60, 0.25, 0.15)))
PARTS_MOYEN = (0.55, 0.25, 0.20)  # lycee general, EPAL, IEK
P_GYMNASE_BAS = 0.6               # parmi les bas niveaux : le gymnase fini, sinon le primaire seul
P_ETUDIANT_SUP = ((UNIVERSITE, 0.72), (IEK, 0.20), (ECOLE_MILITAIRE, 0.03), (ECOLE_POLICE, 0.05))
P_FILIERE_ETUDIANT = ((MEDECINE, 0.05), (SOINS, 0.06), (PEDAGOGIE, 0.12))   # le reste : generale
P_HORS_ECOLE_15_17 = 0.05         # Eurostat : ~ 95 % des 15-17 ans scolarises en Grece ( a verifier )
P_EPAL = 0.30                     # part de l enseignement professionnel au second cycle ( Eurostat, ~ 29 % ; a verifier )
P_RETARD = 0.03                   # eleves en retard d un an au recensement ( PISA 2018 : ~ 4 % des 15 ans ; a verifier )


# ================================================================== le calendrier ( fonctions pures )
def annee_scolaire(d):
    """L annee de la rentree de l annee scolaire qui contient la date `d`."""
    return d.year if d.month >= 9 else d.year - 1


def jour_de_classe(cal, d, groupe):
    """`d` ( une date ) est-il un jour de cours pour le groupe ( PRIM, SECOND, SUP, ADULTES ) ?"""
    if d.weekday() >= 5 or cal.ferie(d) is not None: return False
    y = annee_scolaire(d)
    noel = dt.date(y, 12, 24) <= d <= dt.date(y + 1, 1, 7)
    if groupe == ADULTES: return d.month != 8 and not noel
    m, j = DEBUT_COURS[groupe]; mf, jf = FIN_COURS[groupe]
    if not dt.date(y, m, j) <= d <= dt.date(y + 1, mf, jf): return False
    if noel or (d.month, d.day) in FETES_SCOLAIRES: return False
    pq = CAL.paques_orthodoxe(y + 1)
    if pq - dt.timedelta(days=6) <= d <= pq + dt.timedelta(days=7): return False
    if groupe == SUP:
        (m1, j1), (m2, j2) = SESSION_HIVER_SUP
        if dt.date(y + 1, m1, j1) <= d <= dt.date(y + 1, m2, j2): return False
    return True


def jours_de_classe_annee(cal, y, groupe):
    """Le nombre de jours de cours de l annee scolaire qui commence en septembre de l annee `y`."""
    d, fin, n = dt.date(y, 9, 1), dt.date(y + 1, 8, 31), 0
    while d <= fin:
        n += jour_de_classe(cal, d, groupe); d += dt.timedelta(days=1)
    return n


# ================================================================== apprendre, examiner ( fonctions pures, vectorisees )
def attendu(cycle, annee):
    """Le niveau attendu ( n, 3 ) a la fin de l annee `annee` du cycle."""
    return BASE[cycle] + np.minimum(annee, DUREE[cycle])[:, None] * RYTHME[cycle]


def gains_du_jour(cycle, apt, hab, front, jours_an):
    """Ce qu un jour de cours apporte ( n, 3 ) a des eleves presents : le rythme du cycle sur les jours de cours de
    l annee, fois leur aptitude ( lecture, calcul ) ou leur habilete ( technique ), plus les cours prives."""
    g = RYTHME[cycle] / np.maximum(1.0, jours_an)[:, None]
    f = 1.0 + BONUS_FRONTISTIRIO * front
    return g * np.column_stack((apt * f, apt * f, hab))


def pas_d_ecole(comp, cycle, apt, hab, front, jours_an, present):
    """Un jour de cours : les presents gagnent, les absents perdent leur lecon et en oublient une part. Rend les
    competences nouvelles ( n, 3 ), jamais negatives."""
    g = gains_du_jour(cycle, apt, hab, front, jours_an)
    nominal = RYTHME[cycle] / np.maximum(1.0, jours_an)[:, None]
    return np.maximum(0.0, comp + np.where(present[:, None], g, -OUBLI_ABSENCE * nominal))


def pas_de_vacances(comp, jours_sans_classe):
    """Un jour sans cours pour un inscrit : l oubli des vacances, reparti sur les jours sans cours de l annee."""
    return np.maximum(0.0, comp - OUBLI_VACANCES_AN / max(1.0, float(jours_sans_classe)))


def niveau_relatif(comp, cycle, annee):
    """Le niveau de l eleve sur le niveau attendu, pondere par ce que l examen de son cycle regarde."""
    w = POIDS_EXAMEN[cycle]
    return (comp * w).sum(axis=1) / np.maximum(1e-9, (attendu(cycle, annee) * w).sum(axis=1))


def noter_examen(comp, cycle, annee, u_normal):
    """La note de juin sur 20 ( `u_normal` : des tirages normaux centres reduits, un par eleve )."""
    return np.clip(NOTE_CENTRE + NOTE_PENTE * (niveau_relatif(comp, cycle, annee) - 1.0) + NOTE_BRUIT * u_normal, 0.0, 20.0)


def reussite(note, cycle, absences, classes):
    """Le conseil de classe : la note atteint le seuil du cycle et les absences restent sous la limite."""
    taux = absences / np.maximum(1, classes)
    return (note >= SEUIL_PASSAGE[cycle]) & (taux <= LIMITE_ABSENCES[cycle])


def tirer_aptitudes(rng, n, classe):
    """Aptitude academique et habilete technique, correlees, decalees par la classe du menage ; bornees a [0,3 ; 2]."""
    z1 = rng.standard_normal(n); z2 = rng.standard_normal(n)
    z2 = CORR_APTITUDES * z1 + math.sqrt(1.0 - CORR_APTITUDES ** 2) * z2
    dec = DECALAGE_CLASSE[np.clip(classe, 0, 2)]
    return (np.clip(1.0 + dec + APTITUDE_SD * z1, 0.3, 2.0).astype(np.float32),
            np.clip(1.0 + APTITUDE_SD * z2, 0.3, 2.0).astype(np.float32))


def valeur_du_jour(delta, revenu_net, cout):
    """La note d un jour pour un eleve : competences acquises ( valeur actualisee ), revenu, cout pour son menage."""
    return VALEUR_ANNEE * float(np.dot(delta, POIDS_VALEUR)) + (revenu_net - cout) / TR.NORME_REVENU_J


# ================================================================== la formation des adultes
PHASES = ("instruction", "exercice", "debrief", "qualification")
INSTRUCTION, EXERCICE, DEBRIEF, QUALIFICATION, FINIE = range(5)


class Programme:
    """Une formation : jours d instruction, d exercice et de debrief ( jours de formation ), puis l epreuve.
      competence  0 lecture, 1 calcul, 2 technique : celle que la formation exerce
      gain        annees equivalentes que l instruction apporte a un stagiaire d habilete 1 present tous les jours
      diplome     le diplome delivre ( DIPLOMES ) ; la qualification du domaine 4 qui en decoule ( QUALIF_DU_DIPLOME )
                  ou `qualification` ( un programme d un autre domaine : formation_militaire... )
      seuil       la note sur 20 de l epreuve de qualification
      public      chomeurs, salaries, ou api ( seulement sur inscription par un autre domaine )
      allocation  drachmes par jour de presence, payees par l Etat au menage du stagiaire"""
    __slots__ = ("nom", "domaine", "instruction_j", "exercice_j", "debrief_j", "competence", "gain", "diplome",
                 "qualification", "seuil", "public", "allocation")

    def __init__(self, nom, domaine, instruction_j, exercice_j, debrief_j, competence, gain, diplome, seuil,
                 public="api", allocation=0.0, qualification=None):
        if not (instruction_j >= 1 and exercice_j >= 1 and debrief_j >= 1): raise ValueError(f"{nom} : chaque phase dure un jour au moins")
        if competence not in (0, 1, 2) or not 0.0 < gain <= 5.0: raise ValueError(f"{nom} : competence ou gain invalide")
        if diplome not in BIT or not 0.0 <= seuil <= 20.0 or allocation < 0.0: raise ValueError(f"{nom} : diplome, seuil ou allocation invalide")
        if public not in ("chomeurs", "salaries", "api"): raise ValueError(f"{nom} : public inconnu {public!r}")
        q = qualification if qualification is not None else QUALIF_DU_DIPLOME.get(diplome)
        if q is not None and q not in TR.BIT: raise ValueError(f"{nom} : qualification inconnue {q!r}")
        self.nom, self.domaine = nom, domaine
        self.instruction_j, self.exercice_j, self.debrief_j = int(instruction_j), int(exercice_j), int(debrief_j)
        self.competence, self.gain, self.diplome, self.qualification = competence, float(gain), diplome, q
        self.seuil, self.public, self.allocation = float(seuil), public, float(allocation)


class Stagiaire:
    __slots__ = ("hid", "programme", "debut_j", "phase", "jours", "depart", "notes", "externes", "absences")

    def __init__(self, hid, programme, debut_j, depart):
        self.hid, self.programme, self.debut_j = hid, programme, debut_j
        self.phase, self.jours, self.depart = INSTRUCTION, 0, float(depart)
        self.notes, self.externes, self.absences = [], [], 0


# Les programmes du domaine ( DYPA : permis poids lourd et requalification des chomeurs ; formation continue des
# salaries, le soir, sans quitter le poste ). Durees : a calibrer. Seuil du permis : ~ 60 % de reussite a l epreuve
# ( permis C, a calibrer ) ; un stagiaire d habilete 1 qui a tout suivi a une note de 12 +/- 2 : seuil 11,5.
SEUIL_PERMIS = 11.5
PROGRAMMES = (
    ("poids_lourd", 15, 10, 2, 2, 0.5, "poids_lourd", SEUIL_PERMIS, "chomeurs", ALLOCATION_FORMATION_J),
    ("requalification", 40, 20, 5, 2, 0.8, "formation", 10.0, "chomeurs", ALLOCATION_FORMATION_J),
    ("formation_continue", 20, 10, 2, 2, 0.3, "formation", 10.0, "salaries", 0.0),
    ("instruction_civique", 3, 3, 3, 0, 0.1, "formation", 10.0, "api", 0.0),
)


# ================================================================== la decision
class ContexteOrientation:
    """Ce qu un eleve et sa famille voient en juin, a la fin du gymnase : son bulletin, ses absences, sa caisse, ce
    que ses parents savent de l ecole. Jamais son aptitude."""
    __slots__ = ("traits", "hid")

    def __init__(self, traits, hid): self.traits, self.hid = traits, hid


def _observer_orientation(ctx): return ctx.traits


def _regle_orientation(x, ctx):
    note, tech, absences, redoubl, caisse, parents, retard = x
    if note * 20.0 >= 12.0 or (note * 20.0 >= 10.0 and parents >= 16.0 / 18.0): return GENERAL
    if note * 20.0 < 7.0 and (absences >= 0.5 or redoubl > 0.0): return ARRET
    return PRO


def _temoin_orientation(x, ctx, rng): return GENERAL


POINT_ORIENTATION = D.PointDeDecision(
    "orientation", "education",
    traits=(("moyenne", "sa moyenne de juin en fin de gymnase, sur 20 ( le bulletin )"),
            ("technique", "son niveau en technologie, en annees d ecole, sur 3 ( le bulletin )"),
            ("absences", "sa part de jours manques dans l annee, sur la limite legale de 15 %"),
            ("redoublements", "ses annees redoublees, sur 2 ( son dossier )"),
            ("caisse", "la caisse du menage sur une annee de cours prives de terminale, bornee a 1"),
            ("parents", "le plus haut nombre d annees d etudes des adultes de son menage, sur 18"),
            ("retard", "son age moins 15 ans, sur 3")),
    actions=("lycee_general", "lycee_pro", "arret"),
    observer=_observer_orientation, regle=_regle_orientation, temoin=_temoin_orientation,
    note=("pour CET eleve, chaque jour : la valeur actualisee des competences qu il a acquises, plus son revenu net, "
          "moins ce que son menage a paye pour lui, en journees de deux SMIC nets ; une prime le jour de son examen "
          "de juin, positive s il reussit, negative s il echoue"),
    horizon_j=HORIZON_ORIENTATION)


# ================================================================== l etat du domaine
class Education:
    __slots__ = ("programmes", "stagiaires", "decideur", "suivi", "cout_jour", "prime_jour", "zone_du_lieu",
                 "jours_an", "jours_sans", "places", "enseignants", "candidats", "admis", "passages", "diplomes_j",
                 "orientations", "decrochages", "redoublements", "paye_front", "qualifies", "echoues", "stats_passage",
                 "allocations", "repas")

    def __init__(self, decideur, zone_du_lieu):
        self.programmes = {}
        self.stagiaires = {}        # habitant -> Stagiaire
        self.decideur = decideur
        self.suivi = {}             # habitant -> competences d hier ( choix d orientation en attente de note )
        self.cout_jour = {}         # habitant -> drachmes payees pour lui aujourd hui
        self.prime_jour = {}        # habitant -> prime de l examen de juin, le jour de l examen
        self.zone_du_lieu = zone_du_lieu
        self.jours_an = {}          # ( annee scolaire, groupe ) -> jours de cours
        self.jours_sans = {}        # ( annee scolaire, groupe ) -> jours sans cours
        self.places = {}            # zone -> ( places, eleves, enseignants ) : la derniere mesure
        self.enseignants = {}
        self.candidats = self.admis = self.passages = self.diplomes_j = 0
        self.orientations = [0, 0, 0]
        self.decrochages = self.redoublements = 0
        self.paye_front = 0.0
        self.qualifies = self.echoues = 0
        self.stats_passage = {}     # annee -> { mesure : valeur } : ce que le dernier passage a produit
        self.allocations = 0.0      # drachmes d allocation de formation versees depuis l installation
        self.repas = _repas_neuf()  # les repas scolaires ( HMT-177 ) : lieux couverts, compteurs


def _dom(p): return p.domaines["education"]


def _cols(p): return p.colonnes["habitant"]


def _n(p):
    n = p.w.table.n
    _cols(p).assurer(n)
    return n


def date_du_jour(p):
    """La date civile de la journee du monde ( la journee commence a 6 h )."""
    return p.socle.calendrier.date(p.jour * C.PAS_PAR_JOUR).date()


def _ages(p, ids):
    return (p.jour - _cols(p)["naissance_j"][ids].astype(np.int64)) / JOURS_AN


def _jours_an(p, d, y, groupe):
    k = (y, groupe)
    v = d.jours_an.get(k)
    if v is None:
        v = d.jours_an[k] = jours_de_classe_annee(p.socle.calendrier, y, groupe)
        d.jours_sans[k] = 365 - v
    return v


def _tables_jours(p, d, y):
    """Les jours de cours de l annee, par cycle ( le calendrier de son groupe )."""
    return np.array([_jours_an(p, d, y, int(GROUPE[c])) for c in range(NC)], np.float64), \
        np.array([d.jours_sans[(y, int(GROUPE[c]))] for c in range(NC)], np.float64)


def _classe_menage(p, n):
    """Par menage : la meilleure classe de ses adultes ( code du moteur, 0 = aisee ) ; 2 sans adulte connu."""
    tb = p.w.table; nm = tb.menages.n
    out = np.full(max(1, nm), 2, np.int64)
    ids = np.nonzero((tb.vivant[:n] == 1) & (tb.menage[:n] >= 0) & (tb.role[:n] != PO.CODE_ROLE["enfant"]))[0]
    if len(ids): np.minimum.at(out, tb.menage[ids].astype(np.int64), tb.classe[ids].astype(np.int64))
    return out


def _etudes_menage(p, n):
    """Par menage : le plus haut nombre d annees d etudes validees de ses adultes."""
    tb = p.w.table; nm = tb.menages.n; col = _cols(p)
    out = np.zeros(max(1, nm), np.int64)
    ids = np.nonzero((tb.vivant[:n] == 1) & (tb.menage[:n] >= 0) & (tb.role[:n] != PO.CODE_ROLE["enfant"]))[0]
    if len(ids): np.maximum.at(out, tb.menage[ids].astype(np.int64), col["ed_annees"][ids].astype(np.int64))
    return out


def _competences(col, ids):
    return np.column_stack((col["ed_lecture"][ids], col["ed_calcul"][ids], col["ed_technique"][ids])).astype(np.float64)


def _poser_competences(col, ids, c):
    col["ed_lecture"][ids] = c[:, 0]; col["ed_calcul"][ids] = c[:, 1]; col["ed_technique"][ids] = c[:, 2]


# ================================================================== la journee d ecole
def _presents(p, ids, rng):
    """Presents en classe : vivants, dans l ile, pas hospitalises ( gravite > 0,3 ), pas epuises par la faim, et pas
    absents ce jour-la ( maladie benigne, famille )."""
    tb = p.w.table
    ok = (tb.vivant[ids] == 1) & (tb.statut[ids] != PO.ABSENT)
    ok &= ~((tb.etat[ids] == PO.CODE_ETAT["I"]) & (tb.gravite[ids] > 0.3))
    ok &= tb.faim[ids] <= C.ABSENCE_FAIM
    return ok & (rng.random(len(ids)) >= P_ABSENCE)


def _ecole(p, forcer=None):
    """15 h : la journee d ecole des inscrits. Jour de cours de leur groupe : presents et absents ; sinon l oubli
    des vacances. Le 10 juin, les examens ; le 20 juin, le passage ; la veille de la rentree, la rentree ; le premier
    jour de cours du mois ( octobre a mai ), la facture des cours prives. `forcer` ( trois booleens : primaire,
    secondaire, superieur ) : un jour de cours impose, pour mesurer le cout d un jour ordinaire en ete."""
    d = _dom(p); col = _cols(p); n = _n(p)
    jour = date_du_jour(p)
    y = annee_scolaire(jour)
    cyc = col["ed_cycle"]
    ids = np.nonzero((cyc[:n] > 0) & (p.w.table.vivant[:n] == 1))[0]
    if len(ids):
        cal = p.socle.calendrier
        classe = np.array(forcer if forcer is not None else [jour_de_classe(cal, jour, g) for g in (PRIM, SECOND, SUP)])
        ja, js = _tables_jours(p, d, y)
        c_ids = cyc[ids].astype(np.int64)
        en_classe = classe[GROUPE[c_ids]]
        comp = _competences(col, ids)
        if en_classe.any():
            k = ids[en_classe]; ck = c_ids[en_classe]
            pres = _presents(p, k, p.du_jour("education_presence"))
            if REPAS_SCOLAIRES and classe[PRIM]: _servir_repas(p, d, k, ck, pres)
            col["ed_classes"][k] += 1
            col["ed_absences"][k[~pres]] += 1
            comp[en_classe] = pas_d_ecole(comp[en_classe], ck, col["ed_aptitude"][k].astype(np.float64),
                                          col["ed_habilete"][k].astype(np.float64),
                                          col["ed_frontistirio"][k].astype(np.float64), ja[ck], pres)
            if jour.month in MOIS_FRONTISTIRIO and classe[SECOND] and _premier_jour_de_classe_du_mois(cal, jour):
                _facturer_frontistiria(p, d, n)
        if (~en_classe).any():
            comp[~en_classe] = np.maximum(0.0, comp[~en_classe] - OUBLI_VACANCES_AN / np.maximum(1.0, js[c_ids[~en_classe]])[:, None])
        _poser_competences(col, ids, comp)
    if (jour.month, jour.day) == DATE_EXAMENS: examiner(p)
    if (jour.month, jour.day) == DATE_PASSAGE: passer(p)
    if (jour.month, jour.day) == DATE_RENTREE: rentree(p)


def _premier_jour_de_classe_du_mois(cal, jour):
    x = jour.replace(day=1)
    while x < jour:
        if jour_de_classe(cal, x, SECOND): return False
        x += dt.timedelta(days=1)
    return True


def _front(cycle, annee):
    return FRONTISTIRIO.get((cycle, annee)) or FRONTISTIRIO.get((cycle, 0))


def _frais_mensuels(cyc, an):
    """Le prix mensuel des cours prives ( drachmes ) pour des eleves de cycle et d annee donnes."""
    out = np.zeros(len(cyc))
    for (c, a), (_, eur) in FRONTISTIRIO.items():
        m = (cyc == c) & ((an == a) if a else True)
        out[m] = eur / EUROS
    return out


def _facturer_frontistiria(p, d, n):
    """Le mois de cours prives, paye par chaque menage au marche de sa zone ( services marchands ). Un menage qui ne
    peut plus payer retire ses enfants des cours."""
    w = p.w; tb = w.table; col = _cols(p); L = p.socle.livre
    ids = np.nonzero((col["ed_frontistirio"][:n] == 1) & (tb.vivant[:n] == 1) & (tb.menage[:n] >= 0))[0]
    if not len(ids): return
    frais = _frais_mensuels(col["ed_cycle"][ids], col["ed_annee"][ids])
    mg = tb.menage[ids].astype(np.int64)
    ordre = np.argsort(mg, kind="stable"); ids, frais, mg = ids[ordre], frais[ordre], mg[ordre]
    coupes = np.flatnonzero(np.diff(mg)) + 1
    par_n = w.carte.par_n
    for a, b in zip(np.concatenate(([0], coupes)).tolist(), np.concatenate((coupes, [len(ids)])).tolist()):
        k = int(mg[a]); du = float(np.cumsum(frais[a:b])[-1])
        z = int(d.zone_du_lieu[int(tb.menages.domicile[k])]) if tb.menages.domicile[k] >= 0 else -1
        marche = w.marches.get(par_n[z].id) if z >= 0 else None
        if marche is None: continue
        paye = L.transferer(PO.Menage(k, tb.menages), marche, du, "frontistirio")
        d.paye_front += paye
        for i, f in zip(ids[a:b].tolist(), frais[a:b].tolist()):
            d.cout_jour[i] = d.cout_jour.get(i, 0.0) + f * (paye / du if du > 0 else 0.0)
        if paye < du - 1e-6:
            col["ed_frontistirio"][ids[a:b]] = 0; p.compter("frontistirio_arrete", float(b - a))
        else: p.compter("frontistirio_paye", paye)


# ================================================================== les examens de juin
def examiner(p, rng=None):
    """10 juin : la note de l annee de chaque inscrit, et le verdict du conseil de classe. Pour les eleves de
    terminale du lycee general, c est la note des examens panhelleniques."""
    col = _cols(p); n = _n(p)
    ids = np.nonzero((col["ed_cycle"][:n] > 0) & (p.w.table.vivant[:n] == 1))[0]
    if not len(ids): return
    rng = rng or p.du_jour("education_examens")
    c = col["ed_cycle"][ids].astype(np.int64); a = col["ed_annee"][ids].astype(np.int64)
    note = noter_examen(_competences(col, ids), c, a, rng.standard_normal(len(ids)))
    ok = reussite(note, c, col["ed_absences"][ids], col["ed_classes"][ids])
    col["ed_note"][ids] = note
    col["ed_resultat"][ids] = ok.astype(np.int8)
    d = _dom(p)
    for i, r in zip(ids.tolist(), ok.tolist()):
        if i in d.suivi: d.prime_jour[i] = PRIME_EXAMEN if r else -PRIME_EXAMEN


# ================================================================== le passage du 20 juin
def _quitter(p, i, cycle):
    """L eleve quitte l ecole : a 16 ans et plus, le domaine 4 le fait sortir des etudes a l aube."""
    col = _cols(p)
    col["ed_cycle"][i] = AUCUN; col["ed_annee"][i] = 0; col["ed_frontistirio"][i] = 0
    if p.w.table.role[i] == PO.CODE_ROLE["enfant"]: col["tr_fin_etudes"][i] = p.jour


def delivrer(p, i, diplome, note=None):
    """Un diplome, et la qualification du domaine 4 qu il donne. Refuse un diplome sans la scolarite qu il exige."""
    col = _cols(p)
    if int(col["ed_annees"][i]) < ANNEES_REQUISES[diplome]:
        raise ValueError(f"diplome {diplome} pour {i} : {int(col['ed_annees'][i])} annees de scolarite, "
                         f"{ANNEES_REQUISES[diplome]} exigees")
    col["ed_diplomes"][i] |= BIT[diplome]
    q = QUALIF_DU_DIPLOME.get(diplome)
    if q is not None: TR.qualifier(p, PO.Habitant(p.w.table, i), q)
    p.compter("diplome")


def _diplome_du_superieur(p, i, cycle, filiere, rng):
    if cycle == UNIVERSITE:
        delivrer(p, i, "universite")
        if filiere == MEDECINE: delivrer(p, i, "medecine")
        elif filiere == SOINS: delivrer(p, i, "soins")
        elif filiere == PEDAGOGIE: delivrer(p, i, "pedagogie")
    elif cycle == IEK:
        delivrer(p, i, "iek")
        if filiere == SOINS: delivrer(p, i, "soins")
    elif cycle == ECOLE_MILITAIRE: delivrer(p, i, "universite"); delivrer(p, i, "militaire")
    elif cycle == ECOLE_POLICE: delivrer(p, i, "police")
    p.noter("diplome_superieur", habitant=i, diplome=f"{CYCLES[cycle]}:{FILIERES[filiere]}",
            age=round(float(_ages(p, np.array([i]))[0]), 1))


def _traits_orientation(p, i, clm, etm):
    col = _cols(p); tb = p.w.table
    k = int(tb.menage[i])
    caisse = float(tb.menages.caisse[k]) if k >= 0 else 0.0
    an = 12.0 * FRONTISTIRIO[(LYCEE_GENERAL, 3)][1] / EUROS
    taux = float(col["ed_absences"][i]) / max(1, int(col["ed_classes"][i]))
    age = float(_ages(p, np.array([i]))[0])
    return (min(1.0, max(0.0, float(col["ed_note"][i]) / 20.0)), min(1.0, float(col["ed_technique"][i]) / 3.0),
            min(1.0, taux / 0.15), min(1.0, int(col["ed_redoublements"][i]) / 2.0), min(1.0, max(0.0, caisse) / an),
            min(1.0, (etm[k] if k >= 0 else 0) / 18.0), min(1.0, max(0.0, age - 15.0) / 3.0))


def _admettre_panhellenies(p, d, cand, rng):
    """Les candidats par note decroissante choisissent leur filiere : la plus prestigieuse qu ils demandent, qui a
    encore des places et dont ils ont la note. Sous la note minimale : un IEK ou la vie active."""
    col = _cols(p)
    if not cand: return
    notes = col["ed_note"][cand].astype(np.float64)
    ordre = sorted(range(len(cand)), key=lambda k: (-notes[k], cand[k]))
    nc = len(cand)
    places = [int(math.floor(pl * nc + rng.random())) if pl != math.inf else 10 ** 9 for _, _, _, pl, _ in FILIERES_ADMISSION]
    sexe = col["sexe"]
    u = rng.random((nc, len(FILIERES_ADMISSION)))
    u_iek = rng.random(nc); u_sante = rng.random(nc)
    for r, k in enumerate(ordre):
        i = cand[k]; note = notes[k]
        choisi = None
        for f, (cy, fil, mini, _, veut) in enumerate(FILIERES_ADMISSION):
            if cy == ECOLE_MILITAIRE and sexe[i] == 0: veut *= PART_FEMMES_MILITAIRE
            if note >= mini and places[f] > 0 and u[r, f] < veut: choisi = f; break
        d.candidats += 1; p.compter("panhellenies_candidat")
        if choisi is not None:
            places[choisi] -= 1
            cy, fil = FILIERES_ADMISSION[choisi][:2]
            col["ed_cycle"][i] = cy; col["ed_annee"][i] = 1; col["ed_filiere"][i] = fil
            d.admis += 1; p.compter("panhellenies_admis")
        elif u_iek[r] < P_IEK_APRES_GEL:
            col["ed_cycle"][i] = IEK; col["ed_annee"][i] = 1; col["ed_filiere"][i] = SOINS if u_sante[r] < P_IEK_SANTE else TECHNIQUE
        else: _quitter(p, i, LYCEE_GENERAL)


def passer(p, rng=None):
    """20 juin : le conseil de classe. Reussite : l annee suivante, ou le diplome du cycle et la suite ( orientation
    apres le gymnase, panhelleniques apres le lycee general, IEK ou apprentissage apres l EPAL, vie active apres le
    superieur ). Echec : redoubler ( ou, au-dela de 15 ans, decrocher plus souvent ). Chaque eleve dans l ordre des
    numeros ; les tirages en vecteurs."""
    d = _dom(p); col = _cols(p); n = _n(p); tb = p.w.table
    ids = np.nonzero((col["ed_cycle"][:n] > 0) & (tb.vivant[:n] == 1))[0]
    if not len(ids): return
    rng = rng or p.du_jour("education_passage")
    u_dec = rng.random(len(ids)); u_suite = rng.random(len(ids)); u_sante = rng.random(len(ids))
    ages = _ages(p, ids)
    clm = _classe_menage(p, n); etm = _etudes_menage(p, n)
    candidats = []
    stats = {"eleves": len(ids), "reussites": 0, "echecs": 0, "decrochages": 0, "diplomes_gymnase": 0,
             "inscrits_gymnase_3": 0, "inscrits_primaire": 0, "reussites_primaire": 0}
    for r, i in enumerate(ids.tolist()):
        c = int(col["ed_cycle"][i]); a = int(col["ed_annee"][i]); fil = int(col["ed_filiere"][i])
        ok = col["ed_resultat"][i] == 1
        stats["reussites" if ok else "echecs"] += 1
        if c == PRIMAIRE: stats["inscrits_primaire"] += 1; stats["reussites_primaire"] += int(ok)
        if c == GYMNASE and a == 3: stats["inscrits_gymnase_3"] += 1
        col["ed_resultat"][i] = -1
        if c == LYCEE_PRO and a == ANNEE_APPRENTISSAGE:          # l annee d apprentissage finie : la vie active
            _quitter(p, i, c); continue
        pd = P_DECROCHAGE[c] * (1.0 if ok else MULT_ECHEC)
        if ages[r] >= AGE_FIN_OBLIGATION and u_dec[r] < pd:
            d.decrochages += 1; stats["decrochages"] += 1
            p.noter("decrochage", habitant=i, cycle=CYCLES[c], age=round(float(ages[r]), 1))
            _quitter(p, i, c); continue
        if not ok:
            col["ed_redoublements"][i] += 1; d.redoublements += 1; p.compter("redoublement"); continue
        d.passages += 1; p.compter("passage")
        col["ed_annees"][i] += 0 if (c == IEK and a == DUREE[IEK]) else int(COMPTE[c])
        duree = DUREE_MEDECINE if (c == UNIVERSITE and fil == MEDECINE) else int(DUREE[c])
        if a < duree:
            col["ed_annee"][i] = a + 1; continue
        # fin de cycle
        if c == MATERNELLE: col["ed_cycle"][i] = PRIMAIRE; col["ed_annee"][i] = 1
        elif c == PRIMAIRE:
            delivrer(p, i, "primaire"); col["ed_cycle"][i] = GYMNASE; col["ed_annee"][i] = 1
        elif c == GYMNASE:
            delivrer(p, i, "gymnase"); stats["diplomes_gymnase"] += 1
            a_ = d.decideur.decider(i, ContexteOrientation(_traits_orientation(p, i, clm, etm), i))
            d.orientations[a_] += 1
            p.compter(("orientation_general", "orientation_pro", "orientation_arret")[a_])
            d.suivi[i] = _competences(col, np.array([i]))[0]
            if a_ == ARRET: _quitter(p, i, c)
            else: col["ed_cycle"][i] = CYCLE_DU_CHOIX[a_]; col["ed_annee"][i] = 1
        elif c == LYCEE_GENERAL:
            delivrer(p, i, "lycee"); candidats.append(i)
        elif c == LYCEE_PRO:
            delivrer(p, i, "epal")
            if u_suite[r] < P_APPRENTISSAGE: col["ed_annee"][i] = ANNEE_APPRENTISSAGE
            elif u_suite[r] < P_APPRENTISSAGE + P_IEK_APRES_EPAL:
                col["ed_cycle"][i] = IEK; col["ed_annee"][i] = 1
                col["ed_filiere"][i] = SOINS if u_sante[r] < P_IEK_SANTE else TECHNIQUE
            else: _quitter(p, i, c)
        else:
            _diplome_du_superieur(p, i, c, fil, rng); d.diplomes_j += 1
            _quitter(p, i, c)
    _admettre_panhellenies(p, d, candidats, rng)
    stats["candidats"] = len(candidats)
    d.stats_passage[annee_scolaire(date_du_jour(p))] = stats


# ================================================================== la rentree
def rentree(p):
    """La veille des cours : les enfants de 4 ans ( au 31 decembre ) entrent en maternelle, les enfants d age
    scolaire jamais scolarises en primaire ; les compteurs de l annee repartent ; les familles inscrivent aux cours
    prives ; le ministere demande ses enseignants au ratio grec et mesure ses places."""
    d = _dom(p); col = _cols(p); n = _n(p); tb = p.w.table
    jour = date_du_jour(p)
    rng = p.du_jour("education_rentree")
    viv = np.nonzero((tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT))[0]
    fin_annee = (dt.date(jour.year, 12, 31) - jour).days / JOURS_AN
    age_dec = _ages(p, viv) + fin_annee
    jamais = (col["ed_cycle"][viv] == AUCUN) & (col["ed_annees"][viv] == 0) & (col["ed_diplomes"][viv] == 0) \
        & (tb.role[viv] == PO.CODE_ROLE["enfant"])
    mat = viv[jamais & (age_dec >= 4.0) & (age_dec < 6.0)]
    prim = viv[jamais & (age_dec >= 6.0) & (age_dec < 12.0)]
    nouveaux = np.concatenate((mat, prim))
    if len(nouveaux):
        a_neuf = nouveaux[col["ed_aptitude"][nouveaux] < 0]
        if len(a_neuf):
            clm = _classe_menage(p, n)
            k = np.maximum(tb.menage[a_neuf].astype(np.int64), 0)
            apt, hab = tirer_aptitudes(p.du_jour("education_aptitude"), len(a_neuf), clm[k])
            col["ed_aptitude"][a_neuf] = apt; col["ed_habilete"][a_neuf] = hab
        col["ed_cycle"][mat] = MATERNELLE; col["ed_annee"][mat] = np.where(age_dec[jamais & (age_dec >= 4.0) & (age_dec < 6.0)] >= 5.0, 2, 1)
        col["ed_cycle"][prim] = PRIMAIRE; col["ed_annee"][prim] = 1
        p.compter("rentree", float(len(nouveaux)))
    ins = np.nonzero((col["ed_cycle"][:n] > 0) & (tb.vivant[:n] == 1))[0]
    col["ed_absences"][ins] = 0; col["ed_classes"][ins] = 0; col["ed_frontistirio"][ins] = 0
    # les cours prives : la part du cycle, selon la classe du menage, si la caisse couvre deux mois
    if len(ins):
        clm = _classe_menage(p, n)
        k = tb.menage[ins].astype(np.int64)
        cyc = col["ed_cycle"][ins].astype(np.int64); an = col["ed_annee"][ins].astype(np.int64)
        part = np.zeros(len(ins))
        for (c, a), (pp, _) in FRONTISTIRIO.items():
            part[(cyc == c) & ((an == a) if a else True)] = pp
        part = np.minimum(0.95, part * FACTEUR_CLASSE_FRONT[clm[np.maximum(k, 0)]])
        caisse = np.where(k >= 0, tb.menages.caisse[np.maximum(k, 0)], 0.0)
        ok = (rng.random(len(ins)) < part) & (caisse >= MOIS_DE_RESERVE_FRONT * _frais_mensuels(cyc, an)) & (k >= 0)
        col["ed_frontistirio"][ins[ok]] = 1
    mesurer_places(p)
    choisir_ecoles(p)
    if p.a("travail"):
        for z, (pl, el, ens) in sorted(d.places.items()):
            TR.ouvrir_postes(p, p.w.carte.par_n[z].id, "enseignant", int(math.ceil(el / RATIO_CIBLE)))


# ================================================================== les repas scolaires ( HMT-177 )
def _repas_neuf():
    return {"couverts": None, "part": 0.0, "servis": 0, "manques": 0, "sans_crochet": 0, "paye": 0.0, "jours": 0}


def _repas(d):
    """L etat des repas scolaires ; un domaine relu d un instantane d avant HMT-177 le recoit neuf."""
    try: return d.repas
    except AttributeError:
        d.repas = _repas_neuf(); return d.repas


def unites_de_consommation(ages, menage, nm):
    """( fonction pure ) L echelle OCDE modifiee ( Eurostat, ELSTAT ) : 1 pour le premier adulte ( 14 ans et plus ),
    0,5 pour chaque autre personne de 14 ans et plus, 0,3 pour chaque enfant de moins de 14 ans ; un menage sans adulte
    compte 1 pour son premier enfant. Rend les unites par menage ( 0 sans personne )."""
    menage = np.asarray(menage, np.int64); ages = np.asarray(ages, float)
    ad = np.bincount(menage[ages >= 14.0], minlength=nm).astype(float)
    en = np.bincount(menage[ages < 14.0], minlength=nm).astype(float)
    return np.where(ad > 0, 1.0 + 0.5 * (ad - 1.0) + 0.3 * en, np.where(en > 0, 1.0 + 0.3 * (en - 1.0), 0.0))


def ecoles_couvertes(revenu_uc, eleves, part=PART_ELEVES_COUVERTS):
    """( fonction pure ) Les lieux dont les ecoles primaires servent le repas : les plus pauvres d abord ( revenu moyen
    par unite de consommation croissant, puis rang du lieu ), jusqu a ce que leurs eleves du primaire fassent au moins
    `part` de tous ; un lieu est couvert en entier ( toutes ses ecoles ), un lieu sans eleve ne l est jamais. Rend un
    masque par lieu."""
    revenu_uc = np.asarray(revenu_uc, float); eleves = np.asarray(eleves, float)
    out = np.zeros(len(eleves), bool)
    tot = float(eleves.sum())
    if tot <= 0.0 or part <= 0.0: return out
    ordre = np.lexsort((np.arange(len(eleves)), revenu_uc))
    ordre = ordre[eleves[ordre] > 0]
    k = int(np.searchsorted(np.cumsum(eleves[ordre]), part * tot - 1e-9)) + 1
    out[ordre[:k]] = True
    return out


def revenu_et_eleves_des_lieux(p):
    """Par lieu : le revenu moyen, sur ses menages habites, de leur revenu lisse ( eco_revenu, domaine 3 ) par unite de
    consommation ( sans le domaine 3 : zero partout ), et les eleves du primaire qui y habitent. Lecture seule."""
    col = _cols(p); n = _n(p); tb = p.w.table; w = p.w
    nl = len(w.carte.par_n); nm = tb.menages.n
    viv = np.nonzero((tb.vivant[:n] == 1) & (tb.menage[:n] >= 0))[0]
    uc = unites_de_consommation(_ages(p, viv), tb.menage[viv], nm)
    rev = np.zeros(nm); cm = p.colonnes["menage"]
    if "eco_revenu" in cm:
        m_ = min(nm, len(cm["eco_revenu"])); rev[:m_] = cm["eco_revenu"][:m_]
    dom = tb.menages.domicile[:nm].astype(np.int64)
    ok = (uc > 0) & (dom >= 0)
    somme = np.bincount(dom[ok], weights=rev[ok] / uc[ok], minlength=nl); nb = np.bincount(dom[ok], minlength=nl)
    revenu_uc = np.divide(somme, nb, out=np.zeros(nl), where=nb > 0)
    prim = np.nonzero((col["ed_cycle"][:n] == PRIMAIRE) & (tb.vivant[:n] == 1) & (tb.domicile[:n] >= 0))[0]
    return revenu_uc, np.bincount(tb.domicile[prim].astype(np.int64), minlength=nl)


def choisir_ecoles(p):
    """A l installation et a chaque rentree : les lieux couverts de l annee ( la KYA ), les plus pauvres d abord
    ( revenu_et_eleves_des_lieux ; sans le domaine 3, dans l ordre de leur rang ). Lecture seule du monde : le bras sans
    repas calcule les memes lieux. Rend le masque."""
    revenu_uc, eleves = revenu_et_eleves_des_lieux(p)
    R = _repas(_dom(p))
    R["couverts"] = ecoles_couvertes(revenu_uc, eleves)
    R["part"] = float(eleves[R["couverts"]].sum() / max(1, eleves.sum()))
    return R["couverts"]


def _assurer_repas(p):
    L = p.socle.livre
    if "repas_scolaire" not in L.motifs:
        L.declarer_motif("repas_scolaire", "achat", "education")
        for t in ("repas_scolaires", "repas_scolaires_manques", "repas_scolaires_sans_crochet"):
            p.socle.journal.declarer(t, "education", "compte")


def _servir_repas(p, d, k, ck, pres):
    """15 h, un jour de cours du primaire : le repas de MIDI des eleves du primaire PRESENTS ( le tirage de presence du
    jour, un seul ) dont le lieu est couvert. Par zone de marche : l Etat paie le repas au marche ( PRIX_REPAS_DR,
    motif repas_scolaire ) et la nourriture du repas ( RATION_REPAS ) y est consommee. Un marche sans assez de
    nourriture sert les repas entiers qu il peut, par ordre d identifiant ; un Tresor qui ne paie pas tout aussi ; les
    autres sont comptes manques. Le repas baisse le besoin du soir de l eleve ( Monde.manger_dehors, crochet de
    Monde.repas a 20 h ) : sans ce crochet, AUCUN repas n est servi ( compte a part ), pour ne pas payer une nourriture
    qui ne nourrirait personne."""
    R = _repas(d); cv = R["couverts"]
    if cv is None: return
    w = p.w; tb = w.table
    dom = tb.domicile[k].astype(np.int64)
    sel = (ck == PRIMAIRE) & pres & (dom >= 0)
    sel[sel] = cv[dom[sel]]
    ids = k[sel]
    if not len(ids): return
    _assurer_repas(p)
    R["jours"] += 1
    if not hasattr(w, "manger_dehors"):
        R["sans_crochet"] += len(ids); p.compter("repas_scolaires_sans_crochet", float(len(ids))); return
    L = p.socle.livre; par_n = w.carte.par_n
    zones = d.zone_du_lieu[tb.domicile[ids].astype(np.int64)]
    ordre = np.lexsort((ids, zones)); ids, zones = ids[ordre], zones[ordre]
    servis, manques = [], 0
    for z in np.unique(zones).tolist():
        eux = ids[zones == z]
        m = w.marches.get(par_n[z].id) if z >= 0 else None
        nb = 0
        if m is not None:
            nb = min(len(eux), int(math.floor(m.stocks.get("nourriture", 0.0) / RATION_REPAS + 1e-9)))
            if nb > 0:
                paye = L.transferer(w.gouv, m, nb * PRIX_REPAS_DR, "repas_scolaire")
                R["paye"] += paye
                nb = min(nb, int(math.floor(paye / PRIX_REPAS_DR + 1e-9)))
            if nb > 0:
                q = nb * RATION_REPAS
                m.stocks["nourriture"] -= q; m.demande["nourriture"] += q
                L.flux["consomme"]["nourriture"] += q
                servis.append(eux[:nb])
        manques += len(eux) - nb
    if manques:
        R["manques"] += manques; p.compter("repas_scolaires_manques", float(manques))
    if servis:
        s = np.concatenate(servis)
        w.manger_dehors(s, RATION_REPAS)
        R["servis"] += len(s); p.compter("repas_scolaires", float(len(s)))


def repas_scolaires(p):
    """Les compteurs des repas scolaires depuis l installation : lieux couverts, part des eleves du primaire couverts,
    repas servis, manques, sans crochet, drachmes payees par l Etat, jours de service."""
    R = _repas(_dom(p))
    return {k: (None if v is None else (int(v.sum()) if k == "couverts" else v)) for k, v in R.items()}


def mesurer_places(p):
    """{ zone : ( places, eleves, enseignants ) } : les places des ecoles du domaine 13 de chaque zone de marche, les
    eleves de la maternelle au lycee qui y habitent, les enseignants qui y travaillent. Garde la mesure."""
    d = _dom(p); col = _cols(p); n = _n(p); tb = p.w.table; w = p.w
    places = {}
    for b in IM.batiments(p, "ecole"):
        lid = IM.fiche(p, b)["lieu"]
        z = int(d.zone_du_lieu[w.carte.lieux[lid].n])
        places[z] = places.get(z, 0) + IM.places_ecole(p, b)
    ids = np.nonzero(np.isin(col["ed_cycle"][:n], SCOLAIRES) & (tb.vivant[:n] == 1) & (tb.domicile[:n] >= 0))[0]
    zones = d.zone_du_lieu[tb.domicile[ids].astype(np.int64)]
    nl = len(d.zone_du_lieu)
    eleves = np.bincount(zones[zones >= 0], minlength=nl)
    ens = np.nonzero((tb.vivant[:n] == 1) & (tb.role[:n] == PO.CODE_ROLE["enseignant"]) & (tb.travail[:n] >= 0))[0]
    ze = d.zone_du_lieu[tb.travail[ens].astype(np.int64)]
    n_ens = np.bincount(ze[ze >= 0], minlength=nl)
    out = {}
    for z in sorted(set(places) | set(np.nonzero(eleves)[0].tolist())):
        out[z] = (int(places.get(z, 0)), int(eleves[z]), int(n_ens[z]))
        manque = out[z][1] - out[z][0]
        if manque > 0: p.compter("places_manquantes", float(manque))
    d.places = out
    return out


# ================================================================== la formation des adultes
def declarer_programme(p, nom, domaine, instruction_j, exercice_j, debrief_j, competence, gain, diplome, seuil,
                       public="api", allocation=0.0, qualification=None):
    """Domaines 25 et 27 : une formation a eux ( ecole militaire des recrues, instruction tactique ), vecue au cycle
    instruction -> exercice -> debrief -> qualification. Rend le Programme."""
    d = _dom(p)
    if nom in d.programmes: raise ValueError(f"programme {nom!r} deja declare")
    pr = Programme(nom, domaine, instruction_j, exercice_j, debrief_j, competence, gain, diplome, seuil, public,
                   allocation, qualification)
    d.programmes[nom] = pr
    return pr


def inscrire_formation(p, h, nom):
    """Inscrit l habitant `h` au programme `nom` ; rend le Stagiaire ( ou None s il est deja en formation )."""
    d = _dom(p); col = _cols(p)
    if h.id in d.stagiaires or not h.vivant: return None
    pr = d.programmes[nom]
    if col["ed_aptitude"][h.id] < 0:
        apt, hab = tirer_aptitudes(p.hasard("education_aptitude_adulte"), 1, np.array([int(p.w.table.classe[h.id])]))
        col["ed_aptitude"][h.id] = apt[0]; col["ed_habilete"][h.id] = hab[0]
    comp = _competences(col, np.array([h.id]))[0]
    s = Stagiaire(h.id, pr, p.jour, comp[pr.competence])
    d.stagiaires[h.id] = s
    p.compter("formation_entree")
    return s


def noter_exercice(p, hid, note):
    """Domaine 27 : la note ( 0 a 1 ) d un exercice reel ( une manoeuvre, un combat simule ) du stagiaire `hid` ; elle
    remplace la note tiree le jour de l exercice."""
    if not 0.0 <= note <= 1.0: raise ValueError(f"note d exercice hors [0 ; 1] : {note!r}")
    s = _dom(p).stagiaires.get(hid)
    if s is None or s.phase != EXERCICE: raise ValueError(f"{hid} n est pas en exercice")
    s.externes.append(float(note))


def _inscrire_formations(p):
    """Le lundi, 9 h : des chomeurs de plus de deux mois entrent en formation DYPA ( le permis poids lourd s ils ne
    l ont pas, sinon une requalification ) ; des salaries entrent en formation continue ( le soir )."""
    if date_du_jour(p).weekday() != 0: return
    d = _dom(p); col = _cols(p); n = _n(p); tb = p.w.table
    rng = p.du_jour("education_inscription")
    ages = _ages(p, np.arange(n))
    viv = (tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT)
    st = col["tr_statut"][:n]
    ch = viv & (st == TR.CHOMEUR) & (p.jour - col["tr_chomage_j"][:n] >= ANCIENNETE_CHOMAGE_J) & (ages < 60)
    sal = viv & np.isin(st, (TR.SALARIE, TR.FONCTIONNAIRE)) & (ages >= 25) & (ages < 65)
    u = rng.random(n)
    semaine = 7.0 / JOURS_AN
    for i in np.nonzero(ch & (u < P_FORMATION_CHOMEUR_AN * semaine))[0].tolist():
        if i in d.stagiaires: continue
        nom = "poids_lourd" if not col["tr_qualifs"][i] & TR.BIT["permis_poids_lourd"] else "requalification"
        inscrire_formation(p, PO.Habitant(tb, i), nom)
    for i in np.nonzero(sal & (u < P_FORMATION_CONTINUE_AN * semaine))[0].tolist():
        if i not in d.stagiaires: inscrire_formation(p, PO.Habitant(tb, i), "formation_continue")


def _formations(p, rng=None):
    """17 h, les jours de formation : chaque stagiaire vit un jour de sa phase. Instruction : la competence monte.
    Exercice : une note ( tiree de sa maitrise, ou donnee par un autre domaine ). Debrief : il rattrape une part de ce
    que l exercice a montre de manque. Qualification : l epreuve ; reussie, le diplome et la qualification du
    domaine 4. L Etat verse l allocation des jours de presence."""
    d = _dom(p)
    if not d.stagiaires or not jour_de_classe(p.socle.calendrier, date_du_jour(p), ADULTES): return
    col = _cols(p); tb = p.w.table; L = p.socle.livre
    rng = rng or p.du_jour("education_formation")
    ids = np.array(sorted(d.stagiaires), np.int64)
    pres = _presents(p, ids, rng)
    u = rng.standard_normal(len(ids))
    allocs = {}
    for r, i in enumerate(ids.tolist()):
        s = d.stagiaires[i]; pr = s.programme
        if not tb.vivant[i]: del d.stagiaires[i]; continue
        if not pres[r]:
            s.absences += 1; continue
        c = _competences(col, np.array([i]))[0]
        hab = float(col["ed_habilete"][i]) if pr.competence == 2 else float(col["ed_aptitude"][i])
        maitrise = (c[pr.competence] - s.depart) / pr.gain
        if pr.allocation > 0 and tb.menage[i] >= 0:
            allocs[int(tb.menage[i])] = allocs.get(int(tb.menage[i]), 0.0) + pr.allocation
        if s.phase == INSTRUCTION:
            c[pr.competence] += pr.gain * hab / pr.instruction_j
            s.jours += 1
            if s.jours >= pr.instruction_j: s.phase, s.jours = EXERCICE, 0
        elif s.phase == EXERCICE:
            note = s.externes.pop(0) if s.externes else float(np.clip(maitrise + 0.15 * u[r], 0.0, 1.0))
            s.notes.append(note); s.jours += 1
            if s.jours >= pr.exercice_j: s.phase, s.jours = DEBRIEF, 0
        elif s.phase == DEBRIEF:
            manque = 1.0 - (sum(s.notes) / len(s.notes) if s.notes else 0.0)
            c[pr.competence] += DEBRIEF_GAIN * max(0.0, manque) * pr.gain * hab / pr.debrief_j
            s.jours += 1
            if s.jours >= pr.debrief_j: s.phase, s.jours = QUALIFICATION, 0
        else:
            note20 = float(np.clip(NOTE_CENTRE + NOTE_PENTE * (maitrise - 1.0) + BRUIT_EPREUVE * u[r], 0.0, 20.0))
            del d.stagiaires[i]
            if note20 >= pr.seuil:
                _qualifier_stagiaire(p, i, pr, note20)
            else:
                d.echoues += 1; p.compter("formation_echec")
        _poser_competences(col, np.array([i]), c[None, :])
    for k in sorted(allocs):
        paye = L.transferer(p.w.gouv, PO.Menage(k, tb.menages), allocs[k], "allocation_formation")
        d.allocations += paye; p.compter("allocation_formation", paye)


def _qualifier_stagiaire(p, i, pr, note20):
    col = _cols(p)
    col["ed_diplomes"][i] |= BIT[pr.diplome]
    if int(col["ed_annees"][i]) < ANNEES_REQUISES[pr.diplome]:
        col["ed_annees"][i] = ANNEES_REQUISES[pr.diplome]    # la formation d adulte vaut la scolarite qu elle exige
    if pr.qualification is not None: TR.qualifier(p, PO.Habitant(p.w.table, i), pr.qualification)
    _dom(p).qualifies += 1
    p.noter("qualification_formation", habitant=i, programme=pr.nom, note=round(note20, 1))


class EcoleQualifiante(ECOLE_MOTEUR.Ecole):
    """L ecole du moteur ( un eleve, sans memoire, a memoire ou LLM : monde/ecole.py ) ETENDUE au pays : ses journees
    sont l instruction, l exercice et le debrief du cycle ; sa qualification, notee contre la verite du monde, delivre
    le diplome d un Programme a l habitant que l eleve incarne ( domaine 27 : un officier LLM )."""

    def __init__(self, p, hid, eleve, programme, seuil=0.5):
        super().__init__(p.w, eleve)
        self.hid, self.programme, self.seuil, self.delivre = hid, programme, float(seuil), False

    def journee(self):
        self.instruction(); self.exercice_du_jour(); self.debrief()

    def qualifier(self, p):
        score = self.qualification()
        if score >= self.seuil and not self.delivre:
            pr = _dom(p).programmes[self.programme]
            _qualifier_stagiaire(p, self.hid, pr, 20.0 * score); self.delivre = True
        return score


def former_agent(p, hid, eleve, programme="instruction_civique", jours=3, seuil=0.5):
    """Un agent ( eleve de monde/ecole.py ) suit `jours` journees du cycle puis passe la qualification ; rend
    ( score, diplome delivre )."""
    e = EcoleQualifiante(p, hid, eleve, programme, seuil)
    for _ in range(int(jours)): e.journee()
    s = e.qualifier(p)
    return s, e.delivre


# ================================================================== le soir
def _noter(p):
    """22 h 30 : chaque choix d orientation en attente recoit la note du jour de son eleve."""
    d = _dom(p); dec = d.decideur; col = _cols(p); tb = p.w.table
    for i in sorted(k for k, a in dec.attentes.items() if a.choix):
        c = _competences(col, np.array([i]))[0]
        avant = d.suivi.get(i, c)
        net = float(col["tr_net_jour"][i]) if tb.vivant[i] else 0.0
        v = valeur_du_jour(c - avant, net, d.cout_jour.get(i, 0.0)) + d.prime_jour.get(i, 0.0)
        d.suivi[i] = c
        dec.noter(i, v, p.jour)
    for i in [k for k, a in dec.attentes.items() if not a.choix]:
        del dec.attentes[i]; d.suivi.pop(i, None)
    d.cout_jour.clear(); d.prime_jour.clear()


def _nuit(p):
    """23 h 40 : le domaine dit au domaine 4 qui etudie encore. Un inscrit de 16 ans et plus reste etudiant ; un
    jeune de 16 ans et plus qui n est plus inscrit sort des etudes a l aube."""
    col = _cols(p); n = _n(p); tb = p.w.table
    ids = np.nonzero((tb.vivant[:n] == 1) & (tb.role[:n] == PO.CODE_ROLE["enfant"]))[0]
    if not len(ids): return
    ids = ids[_ages(p, ids) >= C.AGE_TRAVAIL - 1.0 / JOURS_AN]
    ins = col["ed_cycle"][ids] > 0
    col["tr_fin_etudes"][ids[ins]] = p.jour + LOIN_J
    hors = ids[~ins]
    col["tr_fin_etudes"][hors] = np.minimum(col["tr_fin_etudes"][hors], p.jour)


# ================================================================== le recensement ( installation )
def _tirer(rng, n, parts):
    """Un indice par tirage, selon des parts ( somme 1 )."""
    return np.searchsorted(np.cumsum(parts), rng.random(n) * float(np.sum(parts)), side="right").clip(0, len(parts) - 1)


def _recensement(p, d, rng):
    """Le 15 juin de l installation, apres les examens : chaque enfant dans son cycle et son annee ( selon son age ), un
    eleve sur 30 en retard d un an ; les etudiants du domaine 4 dans le superieur ; chaque adulte avec son niveau
    d etudes ( parts grecques par age ) et les diplomes que son metier exige ; les competences au niveau de son chemin,
    fois son aptitude ; les notes de juin. Tout en vecteurs, dans l ordre des numeros."""
    w = p.w; tb = w.table; col = _cols(p); n = _n(p)
    viv = np.nonzero(tb.vivant[:n] == 1)[0]
    ages = _ages(p, viv)
    clm = _classe_menage(p, n)
    k = np.maximum(tb.menage[viv].astype(np.int64), 0)
    apt, hab = tirer_aptitudes(rng, len(viv), np.where(tb.menage[viv] >= 0, clm[k], tb.classe[viv].astype(np.int64)))
    col["ed_aptitude"][viv] = apt; col["ed_habilete"][viv] = hab
    enfant = tb.role[viv] == PO.CODE_ROLE["enfant"]
    cyc = np.zeros(len(viv), np.int64); an = np.zeros(len(viv), np.int64); fil = np.zeros(len(viv), np.int64)
    annees = np.zeros(len(viv), np.int64); dip = np.zeros(len(viv), np.int64)
    u = rng.random((len(viv), 6))
    # 1. les enfants scolarises, par age
    for c in (MATERNELLE, PRIMAIRE, GYMNASE):
        m = enfant & (ages >= AGE_ENTREE[c]) & (ages < AGE_ENTREE[c] + DUREE[c])
        cyc[m] = c; an[m] = np.floor(ages[m] - AGE_ENTREE[c]).astype(np.int64) + 1
    lyc = enfant & (ages >= 15.0) & (ages < 18.0)
    cyc[lyc] = np.where(u[lyc, 0] < P_EPAL, LYCEE_PRO, LYCEE_GENERAL)
    an[lyc] = np.floor(ages[lyc] - 15.0).astype(np.int64) + 1
    hors = lyc & (u[:, 1] < P_HORS_ECOLE_15_17)
    retard = (cyc > MATERNELLE) & (ages >= 8.0) & (u[:, 2] < P_RETARD) & (an > 1)
    an[retard] -= 1
    col["ed_redoublements"][viv[retard]] = 1
    # 2. les etudiants du superieur ( enfants de 18 ans et plus : les etudiants du domaine 4 )
    sup = enfant & (ages >= 18.0)
    cyc[sup] = np.array([c for c, _ in P_ETUDIANT_SUP])[_tirer(rng, int(sup.sum()), [q for _, q in P_ETUDIANT_SUP])]
    fs = _tirer(rng, int(sup.sum()), [q for _, q in P_FILIERE_ETUDIANT] + [1.0 - sum(q for _, q in P_FILIERE_ETUDIANT)])
    fil_sup = np.array([f for f, _ in P_FILIERE_ETUDIANT] + [GENERALE])[fs]
    fil_sup = np.where(cyc[sup] == UNIVERSITE, fil_sup, np.where((cyc[sup] == IEK) & (fs == 1), SOINS,
                                                                  np.where(cyc[sup] == IEK, TECHNIQUE, GENERALE)))
    fil[sup] = fil_sup
    dur = np.where((cyc == UNIVERSITE) & (fil == MEDECINE), DUREE_MEDECINE, DUREE[cyc])
    # chaque annee du cursus a la meme part des etudiants ( un flux stationnaire : ~ 1 / duree sortent chaque juin ) ;
    # l age n y suffit pas, le domaine 4 fait etudiants des adultes de 20 a 27 ans ( les etudiants grecs finissent tard )
    an[sup] = 1 + np.floor(rng.random(int(sup.sum())) * dur[sup]).astype(np.int64)
    # annees validees et diplomes des scolarises ( l annee en cours n est pas encore validee )
    ec = cyc > 0
    annees[ec & (cyc >= PRIMAIRE)] = 0
    for c in (PRIMAIRE, GYMNASE, LYCEE_GENERAL, LYCEE_PRO):
        m = cyc == c
        annees[m] = {PRIMAIRE: 0, GYMNASE: 6, LYCEE_GENERAL: 9, LYCEE_PRO: 9}[c] + an[m] - 1
    annees[sup] = 12 + np.where(cyc[sup] == IEK, np.minimum(an[sup] - 1, 2), an[sup] - 1)
    dip[cyc >= GYMNASE] |= BIT["primaire"]
    dip[cyc >= LYCEE_GENERAL] |= BIT["gymnase"]
    dip[sup] |= BIT["lycee"]
    # 3. les adultes ( et les jeunes hors ecole ) : un niveau par age, puis ce que leur metier exige
    adulte = ~ec | hors
    niv = np.zeros(len(viv), np.int64)
    for a0, parts in ATTEINT:
        m = adulte & (ages >= a0)
        niv[m] = _tirer(rng, int(m.sum()), parts)
    m_hors = hors
    niv[m_hors] = 0
    sous = _tirer(rng, len(viv), PARTS_MOYEN)
    bas_gym = u[:, 3] < P_GYMNASE_BAS
    q = col["tr_qualifs"][viv].astype(np.int64)
    a_q = {nom: (q & TR.BIT[nom]) > 0 for nom in QUALIFS_A_DIPLOME}
    # le metier a titre impose son chemin
    force_sup = adulte & (a_q["diplome_medecine"] | a_q["diplome_enseignant"] | a_q["ecole_officiers"])
    force_soins = adulte & a_q["diplome_infirmier"] & ~force_sup
    force_pol = adulte & a_q["ecole_police"] & ~force_sup & ~force_soins
    niv[force_sup] = 2
    niv[(force_soins | force_pol) & (niv == 0)] = 1
    b = adulte & (niv == 0)
    annees[b] = np.where(bas_gym[b], 9, 6)
    dip[b] = np.where(bas_gym[b], BIT["primaire"] | BIT["gymnase"], BIT["primaire"])
    m1 = adulte & (niv == 1)
    base_moy = BIT["primaire"] | BIT["gymnase"]
    annees[m1] = np.where(sous[m1] == 2, 14, 12)
    dip[m1] = base_moy | np.where(sous[m1] == 1, BIT["epal"], BIT["lycee"]) | np.where(sous[m1] == 2, BIT["iek"], 0)
    s2 = adulte & (niv == 2)
    annees[s2] = 16
    dip[s2] = base_moy | BIT["lycee"] | BIT["universite"]
    med = adulte & a_q["diplome_medecine"]; annees[med] = 18; dip[med] |= BIT["medecine"]
    ped = adulte & a_q["diplome_enseignant"]; dip[ped] |= BIT["pedagogie"]
    off = adulte & a_q["ecole_officiers"]; dip[off] |= BIT["militaire"]
    inf = adulte & a_q["diplome_infirmier"]
    annees[inf] = np.maximum(annees[inf], 14); dip[inf] |= BIT["soins"] | np.where(annees[inf] >= 16, 0, BIT["iek"])
    pol = adulte & a_q["ecole_police"]
    annees[pol] = np.maximum(annees[pol], 14); dip[pol] |= BIT["police"] | BIT["lycee"]
    # un titre du domaine 4 est un diplome deja obtenu, meme chez qui etudie de nouveau ( le domaine 4 fait etudiants
    # des adultes du recensement, qui gardent le titre de leur metier )
    for qual, nom in QUALIFS_A_DIPLOME.items():
        m = a_q[qual]
        dip[m] |= BIT[nom] | BIT["primaire"] | BIT["gymnase"] | BIT["lycee"]
        if nom in ("medecine", "pedagogie", "militaire"): dip[m] |= BIT["universite"]
        annees[m] = np.maximum(annees[m], ANNEES_REQUISES[nom])
    # un titre d EPAL donne la securite industrielle ( deja donnee a l embauche aux metiers qui l exigent )
    epal = adulte & ((dip & BIT["epal"]) > 0)
    col["tr_qualifs"][viv[epal]] |= TR.BIT["securite_industrie"]
    # 4. les competences : le niveau du chemin, fois l aptitude, plus un bruit
    comp = np.zeros((len(viv), 3))
    if ec.any():
        comp[ec] = attendu(cyc[ec], an[ec])
    ad = adulte
    comp[ad, 0] = comp[ad, 1] = np.minimum(annees[ad], 12) + np.maximum(0, annees[ad] - 12) * 0.6
    comp[ad, 2] = 0.6 + np.where((dip[ad] & (BIT["epal"] | BIT["iek"])) > 0, 3.0, 0.3) \
        + np.maximum(0, annees[ad] - 12) * 0.8
    bruit = 1.0 + 0.1 * rng.standard_normal((len(viv), 3))
    comp *= np.column_stack((apt, apt, hab)).astype(np.float64) * bruit
    comp = np.maximum(0.0, comp)
    cyc[hors] = AUCUN; an[hors] = 0
    col["ed_cycle"][viv] = cyc; col["ed_annee"][viv] = an; col["ed_filiere"][viv] = fil
    col["ed_annees"][viv] = annees; col["ed_diplomes"][viv] = dip
    _poser_competences(col, viv, comp.astype(np.float32))
    # 5. l annee qui finit : jours de classe, absences, notes de juin
    y = annee_scolaire(date_du_jour(p)); ja, _ = _tables_jours(p, d, y)
    ins = viv[cyc > 0]
    if len(ins):
        jc = ja[col["ed_cycle"][ins].astype(np.int64)].astype(np.int64)
        col["ed_classes"][ins] = jc
        col["ed_absences"][ins] = rng.binomial(jc, P_ABSENCE)
        examiner(p, rng)
    # 6. les jeunes hors ecole de 16 ans et plus sortent des etudes a la premiere aube ; les inscrits restent etudiants
    _nuit(p)


# ================================================================== installation
COLONNES = (("ed_cycle", np.int8, AUCUN), ("ed_annee", np.int8, 0), ("ed_filiere", np.int8, GENERALE),
            ("ed_annees", np.int8, 0), ("ed_diplomes", np.int32, 0), ("ed_lecture", np.float32, 0.0),
            ("ed_calcul", np.float32, 0.0), ("ed_technique", np.float32, 0.0), ("ed_aptitude", np.float32, -1.0),
            ("ed_habilete", np.float32, -1.0), ("ed_absences", np.int16, 0), ("ed_classes", np.int16, 0),
            ("ed_redoublements", np.int8, 0), ("ed_frontistirio", np.int8, 0), ("ed_note", np.float32, 0.0),
            ("ed_resultat", np.int8, -1))


def installer(p):
    w = p.w
    ch = p.colonnes["habitant"]
    for nom, dtyp, defaut in COLONNES: ch.ajouter(nom, dtyp, defaut)
    ch.assurer(w.table.n)
    L = p.socle.livre
    L.declarer_motif("frontistirio", "achat", "education")
    L.declarer_motif("allocation_formation", "prestation", "education")
    J = p.socle.journal
    for t, champs in (("diplome_superieur", ("habitant", "diplome", "age")), ("decrochage", ("habitant", "cycle", "age")),
                      ("qualification_formation", ("habitant", "programme", "note"))):
        J.declarer(t, "education", "individuel", champs)
    for t in ("passage", "redoublement", "diplome", "panhellenies_candidat", "panhellenies_admis", "orientation_general",
              "orientation_pro", "orientation_arret", "frontistirio_paye", "frontistirio_arrete", "formation_entree",
              "formation_echec", "allocation_formation", "rentree", "places_manquantes"):
        J.declarer(t, "education", "compte")
    par_n = w.carte.par_n
    zone = np.array([l.marche.n if getattr(l, "marche", None) is not None else -1 for l in par_n], np.int64)
    d = Education(p.decideur(POINT_ORIENTATION), zone)
    for nom, i_, e_, b_, comp, gain, dipl, seuil, public, alloc in PROGRAMMES:
        d.programmes[nom] = Programme(nom, "education", i_, e_, b_, comp, gain, dipl, seuil, public, alloc)
    p.domaines["education"] = d
    _recensement(p, d, p.hasard("education_recensement"))
    mesurer_places(p)
    choisir_ecoles(p)
    p.routine(9.0, 50, "education", _inscrire_formations)
    p.routine(15.0, 50, "education", _ecole)
    p.routine(17.0, 50, "education", _formations)
    p.routine(22.5, 50, "education", _noter)
    p.routine(23 + 40 / 60, 50, "education", _nuit)
    return d


# ================================================================== ce que le domaine donne aux autres
def anomalies(p):
    """Les incoherences des titres : une qualification a titre ( QUALIFS_A_DIPLOME ) sans son diplome ; un diplome sans
    les annees de scolarite qu il exige. Rend [ ( type, habitant, nom ) ], vivants seulement."""
    col = _cols(p); n = _n(p)
    viv = p.w.table.vivant[:n] == 1
    q = col["tr_qualifs"][:n].astype(np.int64); dip = col["ed_diplomes"][:n].astype(np.int64)
    an = col["ed_annees"][:n].astype(np.int64)
    out = []
    for qual, nom in QUALIFS_A_DIPLOME.items():
        for i in np.nonzero(viv & ((q & TR.BIT[qual]) > 0) & ((dip & BIT[nom]) == 0))[0].tolist():
            out.append(("qualification_sans_diplome", i, qual))
    for nom in DIPLOMES:
        for i in np.nonzero(viv & ((dip & BIT[nom]) > 0) & (an < ANNEES_REQUISES[nom]))[0].tolist():
            out.append(("diplome_sans_scolarite", i, nom))
    return out


def scolarisation(p, bandes=((4, 6), (6, 12), (12, 15), (15, 18), (18, 25))):
    """{ ( age min, age max ) : ( inscrits, habitants ) } : les vivants residents de chaque bande d age, et ceux qui
    sont inscrits dans un cycle."""
    col = _cols(p); n = _n(p); tb = p.w.table
    ids = np.nonzero((tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT))[0]
    ages = _ages(p, ids); ins = col["ed_cycle"][ids] > 0
    return {(a, b): (int((ins & (ages >= a) & (ages < b)).sum()), int(((ages >= a) & (ages < b)).sum())) for a, b in bandes}


def niveau_etudes(p, ids):
    """Domaines 4, 23, 24 : les annees d etudes validees ( un tableau, pour des numeros d habitants )."""
    return _cols(p)["ed_annees"][np.asarray(ids, np.int64)].astype(np.int64)


def competences(p, ids):
    """Domaines 23, 25, 27 : ( lecture, calcul, technique ) en annees d ecole equivalentes, par habitant."""
    return _competences(_cols(p), np.asarray(ids, np.int64))


def diplomes(p, h):
    d = int(_cols(p)["ed_diplomes"][h.id])
    return tuple(nom for nom in DIPLOMES if d & BIT[nom])


def cycle_de(p, h):
    """( cycle, annee, filiere ) de l habitant : ou il en est."""
    col = _cols(p)
    return CYCLES[int(col["ed_cycle"][h.id])], int(col["ed_annee"][h.id]), FILIERES[int(col["ed_filiere"][h.id])]


def admettre(p, h, cycle, filiere=GENERALE, annee=1):
    """Domaine 25 : un jeune entre directement dans un cycle du superieur ( ecole militaire des officiers, ecole de
    police ) - un concours propre, une admission sur titre. Exige le lycee ( 12 ans de scolarite ) ; l habitant doit
    etre un jeune en etudes ( role enfant du moteur ). Il sortira diplome au passage de sa derniere annee."""
    col = _cols(p)
    if cycle not in SUPERIEURS: raise ValueError(f"admettre : cycle du superieur attendu, pas {cycle!r}")
    if int(col["ed_annees"][h.id]) < 12: raise ValueError(f"{h.id} : {int(col['ed_annees'][h.id])} annees d etudes, 12 exigees")
    if h.role != "enfant": raise ValueError(f"{h.id} : un {h.role} ne reprend pas ses etudes ( un Programme )")
    col["ed_cycle"][h.id] = cycle; col["ed_annee"][h.id] = annee; col["ed_filiere"][h.id] = filiere
    col["tr_fin_etudes"][h.id] = p.jour + LOIN_J


def en_formation(p, h):
    s = _dom(p).stagiaires.get(h.id)
    return None if s is None else (s.programme.nom, PHASES[s.phase], s.jours)


def jour_de_classe_du_pays(p, groupe=PRIM):
    """Domaines 5 ( agenda : l horaire ecole ferme l ete et les vacances ) et 23 ( culture ) : aujourd hui est-il un
    jour de cours ?"""
    return jour_de_classe(p.socle.calendrier, date_du_jour(p), groupe)


def places(p):
    """{ zone : ( places, eleves, enseignants ) } de la derniere mesure ( rentree, installation )."""
    return dict(_dom(p).places)


# ================================================================== le scenario de l orientation ( porte de decision )
def scenario_orientation(n=1600, jours=4, graine=7, mode="hasard"):
    """Les passages de fin de gymnase de `jours` etablissements, un par jour a partir du 20 juin 2035, `n` eleves en
    tout : chacun est oriente par le decideur ( mode donne ), puis vit 365 jours avec les fonctions du domaine
    ( jours de classe, presence, gains, cours prives factures chaque mois, examen de juin ; hors ecole : un emploi
    trouve au hasard apres 16 ans, au SMIC ). La note de chaque jour est celle du domaine ( valeur_du_jour ). Rend le
    Decideur. Un scenario et pas le monde : il faudrait sinon 365 jours de pays pour chaque note."""
    rng = np.random.default_rng(graine)
    dec = D.Decideur(POINT_ORIENTATION, mode, rng=np.random.default_rng(graine + 1))
    cal = CAL.Calendrier()
    classe = rng.choice(3, n, p=(0.15, 0.35, 0.50))
    apt, hab = tirer_aptitudes(rng, n, classe)
    apt = apt.astype(np.float64); hab = hab.astype(np.float64)
    fin_gym = np.full(n, GYMNASE); trois = np.full(n, 3)
    comp = attendu(fin_gym, trois) * np.column_stack((apt, apt, hab)) * (1.0 + 0.1 * rng.standard_normal((n, 3)))
    note = noter_examen(comp, fin_gym, trois, rng.standard_normal(n))
    absences = rng.binomial(165, P_ABSENCE, n); redoubl = (rng.random(n) < P_RETARD).astype(int)
    age = 15.0 + rng.random(n) + redoubl
    caisse = rng.lognormal(math.log(3000.0), 1.0, n) * np.array([2.0, 1.0, 0.5])[classe]
    parents = np.array([16, 12, 9])[classe] + rng.integers(-3, 3, n)
    jour_dec = rng.integers(0, jours, n)
    an_front = 12.0 * FRONTISTIRIO[(LYCEE_GENERAL, 3)][1] / EUROS
    choix = np.zeros(n, np.int64)
    ordre = np.lexsort((np.arange(n), jour_dec))
    for i in ordre.tolist():
        x = (min(1.0, note[i] / 20.0), min(1.0, comp[i, 2] / 3.0), min(1.0, absences[i] / 165.0 / 0.15),
             min(1.0, redoubl[i] / 2.0), min(1.0, caisse[i] / an_front), min(1.0, max(0, parents[i]) / 18.0),
             min(1.0, (age[i] - 15.0) / 3.0))
        choix[i] = dec.decider(i, ContexteOrientation(x, i))
    cyc = np.array(CYCLE_DU_CHOIX)[choix]
    ins = cyc > 0
    an = np.where(ins, 1, 0)
    front_part = np.where(cyc == LYCEE_GENERAL, FRONTISTIRIO[(LYCEE_GENERAL, 1)][0],
                          np.where(cyc == LYCEE_PRO, FRONTISTIRIO[(LYCEE_PRO, 0)][0], 0.0))
    front = (rng.random(n) < np.minimum(0.95, front_part * FACTEUR_CLASSE_FRONT[classe])).astype(np.float64)
    frais = _frais_mensuels(cyc, an) * front
    emploi = np.zeros(n, bool)
    net_smic = TR.SMIC_HORAIRE * 8.0 * (1.0 - TR.TAUX_SALARIE) * 5.0 / 7.0
    p_emploi = 1.0 / 150.0        # un jeune sans diplome trouve un emploi en ~ 5 mois ( chomage grec des 15-24 ans : a calibrer )
    d0 = dt.date(2035, *DATE_PASSAGE)
    y = annee_scolaire(d0 + dt.timedelta(days=90))
    ja = jours_de_classe_annee(cal, y, SECOND); js = 365 - ja
    abs_an = np.zeros(n, np.int64); cls_an = np.zeros(n, np.int64)
    for t in range(HORIZON_ORIENTATION + jours):
        s = t - jour_dec
        actifs = (s >= 0) & (s < HORIZON_ORIENTATION)
        if not actifs.any(): continue
        avant = comp.copy()
        revenu = np.zeros(n); cout = np.zeros(n); prime = np.zeros(n)
        for g in range(jours):
            m = actifs & (jour_dec == g)
            if not m.any(): continue
            date = d0 + dt.timedelta(days=int(t - g))
            mi = m & ins
            if jour_de_classe(cal, date, SECOND):
                pres = rng.random(n) >= P_ABSENCE
                cls_an[mi] += 1; abs_an[mi & ~pres] += 1
                comp[mi] = pas_d_ecole(comp[mi], cyc[mi], apt[mi], hab[mi], front[mi], np.full(int(mi.sum()), float(ja)), pres[mi])
                if date.month in MOIS_FRONTISTIRIO and _premier_jour_de_classe_du_mois(cal, date):
                    cout[mi] += frais[mi]
            else:
                comp[mi] = pas_de_vacances(comp[mi], js)
            if (date.month, date.day) == DATE_EXAMENS and mi.any():
                nt = noter_examen(comp[mi], cyc[mi], an[mi], rng.standard_normal(int(mi.sum())))
                prime[mi] = np.where(reussite(nt, cyc[mi], abs_an[mi], cls_an[mi]), PRIME_EXAMEN, -PRIME_EXAMEN)
            mh = m & ~ins & (age + s / JOURS_AN >= C.AGE_TRAVAIL)
            emploi |= mh & (rng.random(n) < p_emploi)
            revenu[m & emploi] = net_smic
        delta = comp - avant
        for i in np.nonzero(actifs)[0].tolist():
            dec.noter(i, valeur_du_jour(delta[i], revenu[i], cout[i]) + prime[i], t)
    return dec
