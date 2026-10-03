"""DOMAINE 27 - ARMEE ( C ) : LES TACTIQUES COMME OBJETS, REGLES D ENGAGEMENT, PERTES, EVACUATION, JUSTICE MILITAIRE,
FORMATION.

FICHE
1. Classes. Les LOIS DECLARATIVES, portables telles quelles ( des tuples et des nombres, aucune fonction dedans ) :
   Conduite ( ce que fait un element pendant une phase : mode de mouvement - fixe, simultane, bond, infiltration,
   repli -, but, posture, regard, regle de feu ), Phase ( un nom, l ORDRE du domaine 26 qui l ouvre - mouvement, tenir,
   ou la voix -, son echeance, sa duree, sa condition de fin, une Conduite par role ), Critere ( la mesure du succes,
   QUI la remplit, le seuil, le temps, les pertes admises ), Tactique ( preconditions : effectif, munitions, autonomie,
   connaissance de l adversaire, lumiere, radio ; roles : appui, guetteurs, le reste en manoeuvre ; phases ; couts :
   munitions portees, carburant du transport, activite imposee au domaine 25 donc sa fatigue ; risques declares :
   exposition et signature ; critere ; programme de formation ). NEUF instances : les sept demandees ( patrouille,
   reconnaissance, bond, appui_mutuel, embuscade, defense, exfiltration ) et deux variantes du choix d exfiltration
   ( contournement, attente ). RegleEngagement ( identification positive : sources admises, age et confiance de la
   connaissance du camp ; proportionnalite : pas de feu d appui pres d un lieu habite ; zones interdites ; legitime
   defense ). L ETAT : Element ( un element engage, pose au domaine 26 comme une ENTITE : c est par elle que
   l adversaire le voit ), Mission ( une tactique executee par une unite du domaine 25 : les hommes en colonnes numpy,
   les elements, la phase, les ordres, le flux de hasard propre ), Tactiques ( l etat du domaine ). ContexteExfiltration
   ( ce que voit le chef ). Les qualifications tactiques sont une table EPARSE ( habitant -> un bit par tactique ) :
   seuls les militaires ( ~ 1,4 % ) en portent.
2. Invariants et ce que le domaine detient. Le domaine ne DETIENT ni argent ni bien. MUNITIONS : chaque coup tire au
   combat sort de l armurerie de sa base par `A.tirer( ..., "tir_combat" )`, les munitions portees par un mort dont
   l arme est perdue par `A.tirer( ..., "perte_au_combat" )` ; le domaine tient le compte des coups demandes et des
   coups sortis par ( base, calibre ) : ils sont egaux ( `anomalies` : tir_sans_munition ) ; un homme ne tire jamais
   plus que ce qu il porte, et on ne lui donne que ce que l armurerie tient ( engagements concurrents deduits ). A
   l EXERCICE, le tir est SIMULE ( simulateur laser de type MILES ) : aucun coup ne sort. MATERIEL : une arme perdue
   sort du Parc par `A.perdre_objet` ( puits detruit ). CARBURANT : le transport vers un point de depart a plus de
   2 km brule le gazole de la garnison ( motif carburant_tactique ). MORTS : toute mort passe par `d01.deceder`, par
   le domaine 16 ( `blesser_soldat` : un AIS 6 tue sur le coup, la phase aigue tue plus tard ), cause combat ; aucun
   militaire engage n est mort sans date de deces ( `anomalies` : mort_sans_deceder ). BLESSES : tout impact que la
   protection n arrete pas met l homme hors de combat ; il est trie ( ISS decroissant ) puis EVACUE par
   `d26.evacuer` ( helicoptere, sinon ambulance ) AVANT que la lesion soit posee ( sinon le soin civil du moteur le
   prend ), et son tri d admission est recalcule ( domaine 17 ) ; une contusion ( la plaque arrete la balle ) ne
   l arrete pas ( `anomalies` : blesse_sans_evacuation ). JUSTICE : chaque violation des regles d engagement a son
   affaire au tribunal militaire ( `d21.juger_militaire` ; `anomalies` : violation_sans_affaire ). ARMA : toute suite
   d ordres de mouvement pose la destination d abord ( `anomalies` : marche_sans_destination ).
3. Decision `exfiltration` ( le chef de groupe, a chaque mission d exfiltration ; dans le monde par defaut aucune ;
   dans le scenario d exercices, 4 fois par jour et par groupe d infanterie contre une force adverse posee ) : direct,
   bond, appui_mouvement, contournement, attente. Traits ( ce que le chef sait : la connaissance de SON camp au
   domaine 26 - jamais la verite -, la carte, l ordre d operation, l appel, le livret des qualifications, le rapport
   de fatigue ) : adversaire connu, sa distance crue a l itineraire, sa place le long de l itineraire, l incertitude
   ( erreur a l observation et marche possible depuis ), s il marchait, sa taille, la nuit, la longueur, la fenetre
   d extraction, l effectif, la qualification, la fatigue. Note ( horizon 1 jour : la mission se clot dans l heure ;
   une cle par mission, pas par groupe, sinon les missions d un meme jour partageraient une note ) : pour CETTE
   mission, la part des hommes ENGAGES arrives au point de ramassage avant la fermeture ( les elements d appui
   comptent : lecon du 15/09, le critere ne doit pas etre rempli par des hommes hors du combat ), moins 0,15 par heure
   de mission : le temps a un PRIX ( lecon du 18/09, un monde sans horloge ne punit pas l attente ; ici la fenetre
   ferme et l heure coute ). Regle : inconnu -> direct la nuit, bond le jour ; une patrouille connue et du temps ->
   attente ; loin de l itineraire -> direct ; connu avec precision, de jour, assez d hommes -> appui_mouvement ; du
   temps -> contournement ; sinon bond. Temoin bete : toujours le bond ( le professeur de CHACAL ).
4. Evenements. Individuels : engagement ( mission, tactique, unite, issue, pertes, adverses ), violation_roe
   ( habitant, mission, motif ), tactique_refusee ( unite, tactique, raisons ). Comptes : mission_lancee,
   mission_reussie, exercice, coups_tires, coups_simules, impact, contusion, blesse_au_combat, mort_au_combat,
   evacuation_tactique, arme_perdue, ordre_tactique, ordre_reemis, rupture, decision_exfiltration, qualification_tactique,
   note_exercice, repli_impossible.
5. Liens. Armee ( 25 ) : `membres`, `competences` ( tir, perception, discipline, stress, moral ), `portee_utile`
   ( arme ET optique ), les dotations ( protection, casque, arme ) lues aux effectifs, `multiplicateur_letalite`,
   `blesser_soldat`, `tirer`, `perdre_objet`, `radios`, `imposer_activite` ( la fatigue d une journee de combat ou
   d exercice ), `perception`, `ordre_de_mouvement`, `classname`, DOTATION_COMBAT. Soutien ( 26, dependance dure ) :
   `poser_camp`, `poser_entite`, `deplacer_entite`, `retirer_entite`, `observer` ( TOUTE detection, des deux cotes ),
   `connaissance` ( None = absence ), `emettre_ordre` et `ordre` ( les phases ordonnees : delai, retard, ordre mal
   compris, estafette perdue ), `autonomie`, `evacuer`, `CAMP_NATIONAL`. Justice ( 21, dependance dure ) :
   `juger_militaire`. Education ( 19 ) : `declarer_programme` ( un programme par tactique ), `inscrire_formation`,
   `noter_exercice`, le journal qualification_formation. Medecine ( 16 ) : `ais_balistique`, `iss_depuis_ais` ( le
   tri ). Hopitaux ( 17 ) : `esi` ( le tri recalcule apres la lesion ). Population ( 1 ) : colonnes deces_j et
   cause_deces ( controle ). Exterieur ( 7 ) : StockE1 ( le gazole de la garnison ). Ne remplace aucune methode du
   moteur. ECRIT, faute d API, trois donnees d autres domaines : la TAILLE d une entite adverse au domaine 26 ( ses
   pertes ), la FATIGUE des hommes engages aux effectifs du domaine 25 ( le cout d une mission, au prorata d une
   journee de 8 h ; `imposer_activite` n agit qu avant 6 h 30 ), le TRI ( esi, iss ) du passage d un evacue au
   domaine 17 ( l admission est faite avant la lesion ).
6. Portes : tests_d27_armee_tactique.py ( 11 portes, 26/09 : toutes passent ). Preconditions ( 7 refus, rien ne
   part ) ; resolveur ( courbe 1 retrouvee a 25, 50, 100, 150 m a moins de 15 %, zero balle au but au-dela de 1,5 fois
   la portee, couvert x 0,14, plaques III 33 % des impacts arretes pour 39 % declares, risques declares = executes ) ;
   controles positifs ( appui mutuel : pertes 0,017 contre 0,177 au bond ; qualifies : 0,133 contre 0,177 ) ; regles
   d engagement ( tribunal militaire ) ; pertes et evacuation ( 33 blesses, 33 evacues, 5 morts des suites par
   deceder, 646 coups demandes = sortis ) ; monde sans combat ; falsificateurs ; decision ; formation ; porte commune ;
   cout. MESURE DU 26/09 ( scenario d exercices, 2 500 habitants, 5 jours, 400 decisions ) : part du choix 0,083,
   p 0,005 ; notes moyennes regle 0,718, temoin ( bond ) 0,702, hasard 0,664 ; l attente coute ( 0,39 ) quand le temps
   a un prix.
7. Arma. Les hommes ont le corps de l habitant ( `A.classname` ) ; `a_incarner` rend, par mission active, chaque homme
   a sa place ( jamais deux au meme point ), sa posture ( setUnitPos UP, MIDDLE, DOWN ), et les ordres dans l ordre
   paye : la DESTINATION avant la marche ( setDestination puis moveTo, 22/09 ), une attente est un ORDRE ( doStop,
   18/09 : sans ordre le detachement marche 818 m ), le regard pose par setDir AVANT doWatch ( 18/09 : doWatch seul
   pivote en 90 s ). arma_preuve = None : rien n a ete vu en jeu.
8. Cout. Rien ne suit la population. Chaque pas : les missions actives ( aucune en paix ), 20 sous-pas de 30 s par
   mission, une detection du domaine 26 par minute et par camp. Le matin du lundi : le plan d instruction ( une boucle
   sur les compagnies ). 10 h : les exercices de formation des compagnies en phase d exercice. Le soir : le journal du
   jour ( qualifications ). Installation : neuf programmes, un point de decision ; lineaire. Mesure du 26/09
   ( test_cout, coeur Rust, 10 002 habitants ) : ~ 30 ms par jour en moyenne sur un jour de paix, un jour de combat
   de deux sections et un jour d exercices de formation d une compagnie, ~ 9 % d une journee du moteur seul ( 0,32 s ) ;
   un exercice de groupe coute 10 a 60 ms ( 20 a 240 sous-pas ). Le scenario de decision ( 80 exercices par jour a
   2 500 habitants ) coute ~ 2,5 s par jour : il n est pas dans le monde par defaut."""
import math
from collections import deque
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D
from . import d07_exterieur as EXT, d16_medecine as MED, d17_hopitaux as HM, d19_education as ED
from . import d21_justice as JU, d25_armee as A, d26_armee_soutien as S

DOMAINE = "armee_tactique"
EPS = 1e-9
PAS_S = C.MINUTES_PAR_PAS * 60           # un pas du monde : 600 s
DT_S = 30.0                               # le sous-pas du combat ( 3,28 s dans CHACAL : 30 s agregent ~ 9 pas Arma )
DETECTION_S = 60.0                        # une detection du domaine 26 par minute de combat et par camp
SOUS_PAS = int(round(PAS_S / DT_S))
DUREE_MAX_S = 6 * 3600.0                  # une mission synchrone ( exercice ) ne dure jamais plus de 6 heures

# ================================================================== les mesures payees dans Arma ( CHACAL, LEVIATHAN )
# Courbe 1 ( 26/07, 2 414 balles, skill 0,5, plein jour, terrain nu ) : coups au but pour 100 tires, cible DEBOUT.
TOUCHER_D = np.array([25.0, 50.0, 75.0, 100.0, 150.0, 200.0])
TOUCHER_P = np.array([0.75, 0.57, 0.41, 0.30, 0.24, 0.26])
SOURCE_TOUCHER = ("courbe 1 mesuree dans Arma le 26/07 ( 2 414 balles, 6 distances x 3 postures, skill 0,5, jour, "
                  "terrain nu ) : 75 % a 25 m, 30 % a 100 m, 26 % a 200 m ; au-dela, palier jusqu a la portee utile "
                  "( a calibrer ) ; la portee utile est le MINIMUM de l arme et de l optique, puis la probabilite tombe "
                  "a zero a 1,5 fois la portee ( Arma 13/09 : MX + ACO, p >= 0,5 jusqu a 400 m, 0 coup a 600 m )")
POSTURES = ("debout", "accroupi", "couche")
DEBOUT, ACCROUPI, COUCHE = range(3)
F_POSTURE_TIR = np.array([1.0, 0.91, 0.72])      # courbe 1 : se coucher divise le risque par 1,4, pas par 5
COUVERTS = ("nu", "leger", "dur")
F_COUVERT = np.array([1.0, 0.20, 0.05])          # vegetation et micro-relief ; trou de combat : a calibrer
#                                                  ( la courbe 1 est mesuree sur terrain NU : se coucher y vaut x 0,72 ;
#                                                  le couche sert surtout a se glisser derriere le micro-relief, 26/07 )
F_NON_VU = 1.0 / 1.75                            # etre vu multiplie la mortalite par 1,75 ( Arma, 563 000 obs. )
F_TIR_EN_MARCHE = 0.3                            # tirer en marchant ( movingInfluence d Arma ) : a calibrer
F_CIBLE_COURT, F_CIBLE_MARCHE = 0.5, 0.8         # une cible qui court ( un bond ), qui marche : a calibrer
T_REACTION_S = 3.0            # surpris par le feu, un element se couche en ~ 3 s ( je cours, il me voit, je plonge )
SIGNATURE_FEU = "vehicule"    # un element qui tire se devoile ( bruit, lueur, poussiere ) : 3 fois la portee ( a calibrer )
CADENCE_VISEE_BPS = 0.35                         # l IA d Arma tire 0,35 balle/s quoi qu on fasse ( 26/07 )
CADENCE_APPUI_BPS = {"mg3": 1.7}                 # tir soutenu d une mitrailleuse, ~ 100 coups/min ( a calibrer )
CADENCE_APPUI_FUSIL_BPS = 0.5                    # tir rapide d un fusil, ~ 30 coups/min ( a calibrer )
SUPP_CADENCE, SUPP_PRECISION = 0.57, 0.14        # courbe 2 ( 28/07 ) : sous le feu, cadence x0,57, precision x0,14
SUPP_BPS_HOMME = 1.0                             # balles par seconde qui passent a moins de 6 m pour clouer un homme
#                                                  ( Arma : la suppression n est alimentee qu a moins de 6 m ; a calibrer )
# Vitesses ( Arma, mesurer_vitesse : debout 4,27 m/s en COMBAT, accroupi 2,63, couche 1,20 ) ; progressions moyennes
# d une TECHNIQUE ( a calibrer ; l exfiltration de CHACAL avancait a ~ 0,7 m/s de moyenne ) :
V_COURSE = 4.27
T_BOND_S = 10.0                                  # un bond : ~ 10 s de course par tour de 60 s ( 3 a 5 s par ruee )
VITESSE = {"fixe": 0.0, "simultane": 1.4, "bond": V_COURSE * T_BOND_S / (2 * DT_S), "infiltration": 0.6,
           "repli": V_COURSE * T_BOND_S / (2 * DT_S)}
F_JUMELLES = 2.5                                 # jumelles 7 x 50 de jour ( a calibrer ) ; la nuit, rien
# Zones touchees ( part de la surface exposee ; a calibrer - Owens 2008, blesses d Irak et d Afghanistan : membres
# ~ 54 %, tete et cou ~ 29 % chez des hommes deja proteges ) : un homme debout, un homme couche ou abrite.
ZONES = ("tete", "cou", "thorax", "abdomen", "membre")
P_ZONE_EXPOSE = np.array([0.09, 0.02, 0.27, 0.12, 0.50])
P_ZONE_ABRITE = np.array([0.30, 0.05, 0.35, 0.00, 0.30])
ARMES_LOURDES = ("carl_gustaf_m3", "mortier_81")    # hors du duel de fantassins ( a modeliser : le tir indirect )
ARME_ADVERSE = "m4a1"         # l AK adverse ( 7,62 x 39, ~ 2 000 J ) : meme AIS que le 5,56 ( 1 500 a 3 000 J ) - a calibrer
TIR_ADVERSE, PORTEE_ADVERSE = 0.5, 400.0         # skill 0,5 d Arma ; fusil d assaut et hausse, 400 m ( a calibrer )
MORAL_ADVERSE = 0.5
# ( 03/10, HMT-198 A1 ) LE TIR INDIRECT des mortiers de 81 mm ( arme collective du domaine 25 ) : cadence soutenue 16 coups
# par minute et par tube, 33 au plus ( M252 : GlobalSecurity, Wikipedia ) - CHOIX : la soutenue ; portee 80 m a la portee
# du domaine 25 ( 5 650 m ) ; rayon d effet 35 m ( « effective kill radius » des obus M821 et M889, Wikipedia ) ;
# dispersion CEP = 1,9 % de la distance ( CHOIX par analogie : 136 m a la portee maximale d un obus de 120 mm sans conduite
# de tir moderne, euro-sd, 2020 ) ; touche dans le rayon avec la chance P_ECLAT x ( 1 - ( r / R )^2 ) x la posture
# ( couche x F_COUCHE_ECLAT ) x le couvert ( dur x F_DUR_ECLAT ; la vegetation n arrete pas un eclat ) - CHOIX, a mesurer
# dans Arma ( B_Mortar_01_F ) ; on ne tire que sur une connaissance FRAICHE ( AGE_MAX_TIR_MIN : l observateur suit la
# cible ; 03/10, une sonde a montre qu une salve sur une position perimee ne touchait rien ) ; deux servants par tube au
# moins ( CHOIX ; cinq au M252 ).
TIR_INDIRECT = True
CADENCE_MORTIER_CPM = 16.0
PORTEE_MIN_MORTIER = 80.0
RAYON_ECLAT_M = 35.0
CEP_PART_PORTEE = 0.019
P_ECLAT = 0.5
SERVANTS_PAR_TUBE = 2
F_COUCHE_ECLAT = 0.3
F_DUR_ECLAT = 0.1
AGE_MAX_TIR_MIN = 2.0
# Rupture : une unite qui a perdu plus que ce seuil se replie ( 0,25 a 0,60 selon le moral et la discipline ; les
# breakpoints historiques vont de 10 a 50 % : a calibrer ).
RUPTURE_BASE, RUPTURE_PENTE = 0.25, 0.35
# Qualification tactique : une unite entrainee s expose moins, avance plus vite et viole moins ( a calibrer ).
Q_EXPOSITION, Q_VITESSE, Q_VIOLATION = 0.30, 0.20, 0.50
P_VIOLATION = 0.02            # par sous-pas, un homme indiscipline tire sur un contact non identifie ( a calibrer )
P_ARME_PERDUE = 0.8           # l arme d un homme hors de combat est perdue quand l unite ROMPT ( sinon on la ramasse )
VOIX_M = 150.0                # au-dela, deux elements ne se commandent plus a la voix : il faut une radio
RAYON_ARRIVE_M = 15.0
ZONE_EMBUSCADE_M = 120.0
DIST_APPUI_M = 350.0          # l appui s installe a ~ 350 m de l adversaire ( CHACAL : poster l appui a 250-550 m )
DEGAGEMENT_M = 400.0          # le contournement passe a 400 m de la position crue, plus son incertitude
KM_TRANSPORT = 2.0            # au-dela, l unite est portee en camion au point de depart
PLACES_CAMION = 16            # Steyr 12M18 ( domaine 25 )
T_ATTENTE_MIN = 30.0
HORIZON = 1
PRIX_HEURE = 0.15             # une heure de mission coute 15 % du groupe ( a calibrer : le prix du temps )

MODES_MVT = ("fixe", "simultane", "bond", "infiltration", "repli")
BUTS = ("sur_place", "objectif", "depart", "appui", "contournement", "op", "itineraire")
REGARDS = ("marche", "objectif", "adversaire", "arriere")
FEUX = ("libre", "appui", "riposte", "tenu", "aucun")
ROLES = ("manoeuvre", "appui", "guetteurs")
MESURES = ("arrives", "neutralises", "tenu", "renseigne", "itineraire")


# ================================================================== les tactiques comme objets
class Conduite:
    """Ce que fait un element pendant une phase. mode : fixe, simultane ( tous marchent debout ), bond ( deux moities
    alternent : l une court pendant que l autre couvre, couchee ), infiltration ( accroupi, lent, discret ), repli ;
    but : sur_place, objectif, depart, appui ( la position d appui ), contournement, op ( le point d observation ),
    itineraire ; posture a l arret ; regard ; feu : libre ( sur une cible identifiee ), appui ( feu de neutralisation ),
    riposte ( seulement si on nous tire dessus ou si l adversaire nous connait ), tenu ( jusqu au declenchement ),
    aucun."""
    __slots__ = ("mode", "but", "posture", "regard", "feu")

    def __init__(self, mode, but="sur_place", posture="couche", regard="objectif", feu="riposte"):
        if mode not in MODES_MVT or but not in BUTS or posture not in POSTURES or regard not in REGARDS or feu not in FEUX:
            raise ValueError(f"conduite invalide : {mode}, {but}, {posture}, {regard}, {feu}")
        self.mode, self.but, self.posture, self.regard, self.feu = mode, but, posture, regard, feu


class Phase:
    """Une phase : l ORDRE qui l ouvre ( mouvement, tenir - une attente est un ordre, 18/09 -, ou None : la voix ), son
    echeance ( minutes apres l emission de l ordre : au-dela, un ordre non recu est reemis ), sa duree maximale, sa fin
    ( arrive : l element `role_fin` est arrive ; duree ; zone : l adversaire entre dans la zone de destruction ;
    neutralise : l adversaire est hors de combat ), et une conduite par role."""
    __slots__ = ("nom", "ordre", "echeance_min", "duree_min", "fin", "role_fin", "conduites")

    def __init__(self, nom, ordre, echeance_min, duree_min, fin, role_fin, conduites):
        if ordre not in (None, "mouvement", "tenir") or fin not in ("arrive", "duree", "zone", "neutralise"):
            raise ValueError(f"phase {nom} : ordre ou fin invalide")
        if not (echeance_min > 0 and duree_min > 0) or role_fin not in ROLES or not set(conduites) <= set(ROLES):
            raise ValueError(f"phase {nom} : bornes")
        self.nom, self.ordre, self.echeance_min, self.duree_min = nom, ordre, float(echeance_min), float(duree_min)
        self.fin, self.role_fin, self.conduites = fin, role_fin, dict(conduites)


class Critere:
    """Le critere de succes, ECRIT et mesurable. mesure : arrives ( hommes au but avant la fin du temps ), neutralises
    ( part de l adversaire hors de combat ), tenu ( la position tenue ), renseigne ( l objectif connu sans etre vu ),
    itineraire ( part parcourue ). qui : les hommes qui remplissent le critere - manoeuvre ( l appui ne compte pas ),
    engages ( tous ), adversaire. Lecon du 15/09 : un critere rempli par des hommes hors du combat ne mesure rien."""
    __slots__ = ("mesure", "qui", "seuil", "temps_max_min", "pertes_max")

    def __init__(self, mesure, qui, seuil, temps_max_min, pertes_max=1.0):
        if mesure not in MESURES or qui not in ("manoeuvre", "engages", "adversaire", "guetteurs"):
            raise ValueError(f"critere : mesure ou qui invalide {mesure}, {qui}")
        if not (0.0 <= seuil <= 1.0 and temps_max_min > 0 and 0.0 <= pertes_max <= 1.0): raise ValueError("critere : bornes")
        self.mesure, self.qui, self.seuil = mesure, qui, float(seuil)
        self.temps_max_min, self.pertes_max = float(temps_max_min), float(pertes_max)


class Tactique:
    """Une tactique : donnees seulement. PRECONDITIONS : effectif minimal ( hommes presents et aptes ), munitions et
    autonomie ( carburant et vivres ) de la garnison en jours de combat ( domaine 26 ), connaissance de l adversaire ( aucune ; contact : sa
    position connue du camp ; identifiee : identification positive ), lumiere ( jour, nuit, toutes ), radio. ROLES :
    part des hommes a l appui et aux guetteurs, le reste en manoeuvre. COUTS : munitions ( la dotation de combat
    portee ; ce qui est tire sort du grand livre ), carburant ( le transport ), activite imposee au domaine 25 ( sa
    fatigue ). RISQUES declares : exposition ( part du temps debout a decouvert d un homme de manoeuvre ), signature
    ( posture vue par l adversaire, domaine 26 ). Le critere, et le programme de formation ( jours d instruction,
    d exercice, de debrief )."""
    __slots__ = ("nom", "but", "effectif_min", "munitions_min_j", "autonomie_min_j", "connaissance", "age_max_h",
                 "conf_min", "lumiere", "radio", "part_appui", "part_guetteurs", "phases", "activite", "exposition",
                 "signature", "critere", "formation")

    def __init__(self, nom, but, effectif_min, munitions_min_j, autonomie_min_j, connaissance, lumiere, radio,
                 part_appui, part_guetteurs, phases, activite, exposition, signature, critere, formation,
                 age_max_h=24.0, conf_min=0.9):
        if connaissance not in ("aucune", "contact", "identifiee") or lumiere not in ("jour", "nuit", "toutes"):
            raise ValueError(f"tactique {nom} : connaissance ou lumiere")
        if not (effectif_min >= 1 and munitions_min_j >= 0 and autonomie_min_j >= 0 and 0 <= part_appui < 1
                and 0 <= part_guetteurs < 1 and part_appui + part_guetteurs < 1 and phases and 0 <= exposition <= 1):
            raise ValueError(f"tactique {nom} : bornes")
        if activite not in A.ACTIONS or signature not in S.POSTURES_CIBLE:
            raise ValueError(f"tactique {nom} : activite, signature")
        if len(formation) != 3 or min(formation) < 1: raise ValueError(f"tactique {nom} : formation ( 3 durees >= 1 j )")
        self.nom, self.but, self.effectif_min = nom, but, int(effectif_min)
        self.munitions_min_j, self.autonomie_min_j = float(munitions_min_j), float(autonomie_min_j)
        self.connaissance, self.lumiere, self.radio = connaissance, lumiere, bool(radio)
        self.part_appui, self.part_guetteurs, self.phases = float(part_appui), float(part_guetteurs), tuple(phases)
        self.activite, self.exposition, self.signature, self.critere = activite, float(exposition), signature, critere
        self.formation, self.age_max_h, self.conf_min = tuple(int(x) for x in formation), float(age_max_h), float(conf_min)


def _c(*a, **k): return Conduite(*a, **k)


CRITERE_EXFIL = Critere("arrives", "engages", 0.6, 90.0)
TACTIQUES = (
    Tactique("patrouille", "parcourir un itineraire, voir et rendre compte, sans perdre plus d un homme sur dix",
             4, 0.3, 0.5, "aucune", "toutes", True, 0.0, 0.2,
             (Phase("parcours", "mouvement", 30, 180, "arrive", "manoeuvre",
                    {"manoeuvre": _c("simultane", "itineraire", regard="marche", feu="riposte"),
                     "guetteurs": _c("simultane", "itineraire", regard="marche", feu="riposte")}),),
             "patrouille", 1.0, "debout", Critere("itineraire", "engages", 0.9, 180.0, 0.1), (3, 2, 1)),
    Tactique("reconnaissance", "connaitre l objectif sans etre vu", 3, 0.1, 0.5, "aucune", "toutes", True, 0.0, 0.34,
             (Phase("approche", "mouvement", 30, 120, "arrive", "guetteurs",
                    {"manoeuvre": _c("infiltration", "op", regard="objectif", feu="riposte"),
                     "guetteurs": _c("infiltration", "op", regard="objectif", feu="riposte")}),
              Phase("observation", None, 10, 20, "duree", "guetteurs",
                    {"manoeuvre": _c("fixe", posture="couche", regard="arriere", feu="riposte"),
                     "guetteurs": _c("fixe", posture="couche", regard="objectif", feu="tenu")}),
              Phase("retour", None, 10, 120, "arrive", "guetteurs",
                    {"manoeuvre": _c("infiltration", "depart", regard="arriere", feu="riposte"),
                     "guetteurs": _c("infiltration", "depart", regard="arriere", feu="riposte")})),
             "patrouille", 0.0, "accroupi", Critere("renseigne", "guetteurs", 1.0, 240.0), (4, 3, 1)),
    Tactique("bond", "gagner l objectif sous le feu par bonds alternes", 4, 0.3, 0.5, "aucune", "toutes", False, 0.0, 0.0,
             (Phase("bonds", "mouvement", 30, 120, "arrive", "manoeuvre",
                    {"manoeuvre": _c("bond", "objectif", regard="objectif", feu="libre")}),),
             "marche", 1.0 / 6.0, "debout", Critere("arrives", "manoeuvre", 0.6, 90.0), (3, 3, 1)),
    Tactique("appui_mutuel", "un element fixe et neutralise l adversaire pendant que l autre progresse par bonds",
             6, 0.5, 0.5, "contact", "jour", True, 0.34, 0.0,
             (Phase("mise_en_place", "mouvement", 30, 60, "arrive", "appui",
                    {"appui": _c("infiltration", "appui", regard="adversaire", feu="riposte"),
                     "manoeuvre": _c("fixe", posture="couche", regard="adversaire", feu="riposte")}),
              Phase("appui_et_mouvement", None, 10, 120, "arrive", "manoeuvre",
                    {"appui": _c("fixe", posture="couche", regard="adversaire", feu="appui"),
                     "manoeuvre": _c("bond", "objectif", regard="objectif", feu="libre")}),
              Phase("ralliement", None, 10, 120, "arrive", "appui",
                    {"appui": _c("bond", "objectif", regard="objectif", feu="libre"),
                     "manoeuvre": _c("fixe", posture="couche", regard="adversaire", feu="libre")})),
             "marche", 1.0 / 6.0, "debout", Critere("arrives", "manoeuvre", 0.6, 120.0), (4, 3, 1)),
    Tactique("embuscade", "detruire l adversaire dans la zone de destruction puis decrocher", 6, 0.5, 1.0, "identifiee",
             "toutes", True, 0.34, 0.2,
             (Phase("mise_en_place", "mouvement", 30, 90, "arrive", "manoeuvre",
                    {"manoeuvre": _c("infiltration", "objectif", regard="adversaire", feu="riposte"),
                     "appui": _c("infiltration", "objectif", regard="adversaire", feu="riposte"),
                     "guetteurs": _c("infiltration", "objectif", regard="adversaire", feu="riposte")}),
              Phase("attente", "tenir", 30, 360, "zone", "manoeuvre",
                    {"manoeuvre": _c("fixe", posture="couche", regard="adversaire", feu="tenu"),
                     "appui": _c("fixe", posture="couche", regard="adversaire", feu="tenu"),
                     "guetteurs": _c("fixe", posture="couche", regard="adversaire", feu="riposte")}),
              Phase("declenchement", None, 5, 5, "neutralise", "manoeuvre",
                    {"manoeuvre": _c("fixe", posture="couche", regard="adversaire", feu="libre"),
                     "appui": _c("fixe", posture="couche", regard="adversaire", feu="appui"),
                     "guetteurs": _c("fixe", posture="couche", regard="adversaire", feu="libre")}),
              Phase("decrochage", None, 5, 60, "arrive", "manoeuvre",
                    {"manoeuvre": _c("bond", "depart", regard="arriere", feu="riposte"),
                     "appui": _c("bond", "depart", regard="arriere", feu="riposte"),
                     "guetteurs": _c("bond", "depart", regard="arriere", feu="riposte")})),
             "marche", 0.08, "accroupi", Critere("neutralises", "adversaire", 0.5, 480.0, 0.1), (5, 3, 1)),
    Tactique("defense", "tenir la position jusqu a l echeance", 4, 0.5, 1.0, "aucune", "toutes", True, 0.34, 0.2,
             (Phase("occupation", "mouvement", 30, 60, "arrive", "manoeuvre",
                    {"manoeuvre": _c("simultane", "objectif", regard="adversaire", feu="libre"),
                     "appui": _c("simultane", "objectif", regard="adversaire", feu="libre"),
                     "guetteurs": _c("simultane", "objectif", regard="adversaire", feu="libre")}),
              Phase("tenir", "tenir", 30, 120, "duree", "manoeuvre",
                    {"manoeuvre": _c("fixe", posture="couche", regard="adversaire", feu="libre"),
                     "appui": _c("fixe", posture="couche", regard="adversaire", feu="libre"),
                     "guetteurs": _c("fixe", posture="couche", regard="adversaire", feu="libre")})),
             "patrouille", 1.0, "debout", Critere("tenu", "engages", 0.5, 240.0), (4, 2, 1)),
    Tactique("exfiltration", "rejoindre le point de ramassage avant sa fermeture, droit et vite", 2, 0.0, 0.0, "aucune",
             "toutes", False, 0.0, 0.0,
             (Phase("exfiltration", "mouvement", 30, 120, "arrive", "manoeuvre",
                    {"manoeuvre": _c("simultane", "objectif", regard="marche", feu="riposte")}),),
             "marche", 1.0, "debout", CRITERE_EXFIL, (3, 2, 1)),
    Tactique("contournement", "rejoindre l objectif en passant loin de l adversaire connu, accroupi", 2, 0.0, 0.0,
             "aucune", "toutes", False, 0.0, 0.0,
             (Phase("contournement", "mouvement", 30, 180, "arrive", "manoeuvre",
                    {"manoeuvre": _c("infiltration", "contournement", regard="marche", feu="riposte")}),),
             "marche", 0.0, "accroupi", CRITERE_EXFIL, (3, 2, 1)),
    Tactique("attente", "tenir sur place ( un ORDRE ) le temps que l adversaire passe, puis rejoindre", 2, 0.0, 0.0,
             "aucune", "toutes", False, 0.0, 0.0,
             (Phase("attente", "tenir", 30, T_ATTENTE_MIN, "duree", "manoeuvre",
                    {"manoeuvre": _c("fixe", posture="couche", regard="adversaire", feu="riposte")}),
              Phase("exfiltration", None, 10, 120, "arrive", "manoeuvre",
                    {"manoeuvre": _c("simultane", "objectif", regard="marche", feu="riposte")})),
             "marche", 1.0, "debout", CRITERE_EXFIL, (3, 2, 1)),
)
TACTIQUE = {t.nom: t for t in TACTIQUES}
IDX_TACTIQUE = {t.nom: k for k, t in enumerate(TACTIQUES)}
PROGRAMME = {t.nom: "tactique_" + t.nom for t in TACTIQUES}
GAIN_FORMATION, SEUIL_FORMATION = 0.3, 10.0      # annees de technique ; note sur 20 ( domaine 19 ) : a calibrer


# ================================================================== les regles d engagement
class RegleEngagement:
    """Les regles d engagement d une mission. IDENTIFICATION POSITIVE : on ne tire que sur une cible que le camp connait
    d une source admise ( observation, patrouille ), vue il y a moins de `age_max_min` minutes, avec une confiance d au
    moins `conf_min` ; un contact de rumeur, de medias ou d interception radio n est pas une cible. LEGITIME DEFENSE :
    un element qui recoit le feu d une cible connue ( sauf rumeur ) peut riposter. PROPORTIONNALITE : pas de feu d appui
    ( neutralisation ) sur une cible a moins de `dist_civils_m` d un lieu habite ( le tir vise reste permis ). ZONES
    INTERDITES : ( x, y, ile, rayon m ) ou aucun tir n est permis. Une violation va au tribunal militaire."""
    __slots__ = ("sources", "age_max_min", "conf_min", "dist_civils_m", "zones")

    def __init__(self, sources=("observation", "patrouille"), age_max_min=10.0, conf_min=0.9, dist_civils_m=300.0,
                 zones=()):
        if not sources or any(s not in S.SOURCES for s in sources): raise ValueError("roe : sources inconnues")
        if not (age_max_min > 0 and 0 <= conf_min <= 1 and dist_civils_m >= 0): raise ValueError("roe : bornes")
        self.sources, self.age_max_min, self.conf_min = tuple(sources), float(age_max_min), float(conf_min)
        self.dist_civils_m, self.zones = float(dist_civils_m), tuple(tuple(float(v) for v in z) for z in zones)


ROE_DEFAUT = RegleEngagement()
GRAVITE_VIOLATION = {"sans_identification": 0.4, "zone_interdite": 0.6, "disproportion": 0.5}
PREUVE_VIOLATION = 0.8        # le journal de tir et les temoins de la section ( a calibrer )


# ================================================================== la loi du tir ( fonctions pures )
def p_courbe(d):
    """La probabilite qu une balle touche une cible debout a decouvert, a d metres ( courbe 1 d Arma )."""
    return np.interp(np.asarray(d, np.float64), TOUCHER_D, TOUCHER_P)


def f_portee(d, portee):
    """1 jusqu a la portee utile, puis une pente jusqu a zero a 1,5 fois la portee ( ACO : 400 m, 0 coup a 600 m )."""
    d = np.asarray(d, np.float64); portee = np.maximum(np.asarray(portee, np.float64), 1.0)
    return np.clip(1.0 - (d - portee) / (0.5 * portee), 0.0, 1.0)


def f_tir(tir):
    """La competence de tir du domaine 25 ( 0,5 : le skill 0,5 de la courbe ) : x0,7 a 0,2 ; x1,4 a 0,9 ( a calibrer )."""
    return 0.5 + np.asarray(tir, np.float64)


def p_toucher(d, tir=0.5, portee=500.0, posture=DEBOUT, couvert=0, vu=True, en_marche=False):
    """Probabilite qu une balle touche : distance ( courbe 1 ), competence, portee utile ( arme ET optique ), posture et
    couvert de la cible, cible vue ou seulement connue ( x 1 / 1,75 ), tireur en marche. Bornee a 0,95."""
    p = (p_courbe(d) * f_tir(tir) * f_portee(d, portee) * F_POSTURE_TIR[np.asarray(posture)]
         * F_COUVERT[np.asarray(couvert)] * np.where(vu, 1.0, F_NON_VU) * np.where(en_marche, F_TIR_EN_MARCHE, 1.0))
    return np.minimum(p, 0.95)


def lesion(zone, arme, prot, casque):
    """( AIS, arrete ) d un impact de `arme` ( domaine 25 ) sur `zone`, selon les protections ( indices de
    A.PROTECTIONS, -1 aucune ) : la loi de `A.blesser_soldat` ( multiplicateur <= 0,2 : la protection arrete, contusion
    AIS 1 ; sinon l AIS balistique du domaine 16 ). Sert au tri et a l adversaire, qui n a pas de corps."""
    a = A.ARME[arme]
    m = 1.0
    for k in (prot, casque):
        if k >= 0 and zone in A.PROTECTIONS[k].zones: m *= A.PROTECTIONS[k].mult[a.menace]
    if m <= A.SEUIL_ARRET: return A.AIS_CONTUSION, True
    return MED.ais_balistique(zone, a.energie_j if a.energie_j > 0 else 3000.0), False


# ================================================================== l etat
CHAMPS_HOMMES = (("side", np.int8, 0), ("elt", np.int16, 0), ("hid", np.int64, -1), ("dx", np.float64, 0.0),
                 ("dy", np.float64, 0.0), ("actif", np.int8, 1), ("tir", np.float64, TIR_ADVERSE),
                 ("portee", np.float64, PORTEE_ADVERSE), ("prot", np.int8, -1), ("casque", np.int8, -1),
                 ("coups", np.float64, 1e9), ("cal", np.int8, -1), ("base", np.int32, -1), ("arme", np.int8, -1),
                 ("disc", np.float64, MORAL_ADVERSE), ("stress", np.float64, 0.0), ("moral", np.float64, MORAL_ADVERSE),
                 ("moitie", np.int8, 0), ("contus", np.int8, 0), ("tires", np.float64, 0.0), ("arrive_s", np.float64, -1.0),
                 ("viole", np.int8, 0))


class Element:
    """Un element engage ( un role d une unite, ou l adversaire ). Il est pose au domaine 26 comme une entite de son
    camp : c est elle que l autre camp observe ( la detection d un groupe est tout ou rien, 04/08 )."""
    __slots__ = ("side", "role", "camp", "ent", "x", "y", "chemin", "cond", "supp", "feu_recu", "tireurs_de", "vu",
                 "n0", "arrive", "regard", "v_propre", "posture_sig", "unite", "fait_feu", "couvert", "voulu")

    def __init__(self, side, role, camp, x, y, n0, unite=-1):
        self.side, self.role, self.camp, self.x, self.y, self.n0 = side, role, camp, float(x), float(y), int(n0)
        self.ent, self.chemin, self.cond, self.supp, self.feu_recu = -1, [], None, 0.0, 0.0
        self.tireurs_de, self.vu, self.arrive, self.regard, self.v_propre = set(), set(), False, None, None
        self.posture_sig, self.unite, self.fait_feu, self.couvert, self.voulu = "debout", int(unite), False, 1, None


class Mission:
    """Une tactique executee. mode : combat ( balles reelles : munitions, blessures, morts ) ou exercice ( tir simule,
    neutralisations fictives ). voix : les ordres de phase a la voix ( exercice ) ou par le domaine 26 ( delais,
    frictions ). Les hommes en colonnes ( `h` ), les elements, la phase, le hasard propre ( un sous-flux par mission :
    deux variantes d une meme mission restent appariees )."""
    __slots__ = ("id", "tactique", "unite", "camp", "adverse", "mode", "voix", "debut_pas", "ile", "depart", "objectif",
                 "itineraire", "adv_cru", "roe", "critere", "rng", "k", "t_s", "t_max_s", "t_phase_s", "ordre",
                 "ordre_emis_s", "ordres", "fini", "issue", "resultat", "rupture", "h", "elts", "pendants", "tirs",
                 "violations", "feu_sur_contact", "couvert_poste", "base_lid", "chef", "compagnie", "qual", "nuit",
                 "fenetre_s", "cibles", "t_det", "zone_emb", "morts", "blesses", "neutr_adv", "detecte_par_adv", "pts", "axe",
                 "compromis", "n_impacts", "n_arretes", "expo_debout", "expo_marche", "sig_debout", "sig_n",
                 "lesions_adverses", "mortiers", "mortiers_adverses")

    def __init__(self, id, tactique, unite, mode, voix, ile, depart, objectif, roe, critere, rng):
        self.id, self.tactique, self.unite, self.mode, self.voix = id, tactique, unite, mode, voix
        self.ile, self.depart, self.objectif = int(ile), tuple(depart), tuple(objectif)
        self.roe, self.critere, self.rng = roe, critere, rng
        self.camp = S.CAMP_NATIONAL; self.adverse = None
        self.itineraire, self.adv_cru, self.k, self.t_s, self.t_phase_s = [], None, 0, 0.0, 0.0
        self.t_max_s = critere.temps_max_min * 60.0
        self.ordre, self.ordre_emis_s, self.ordres, self.fini, self.issue = -1, 0.0, [], False, None
        self.resultat, self.rupture, self.h, self.elts, self.pendants = None, False, None, [], []
        self.tirs, self.violations, self.feu_sur_contact, self.couvert_poste = {}, [], False, 1
        self.base_lid, self.chef, self.compagnie, self.qual, self.nuit = None, -1, -1, 0.0, False
        self.fenetre_s, self.cibles, self.t_det, self.zone_emb = None, [], -1e9, None
        self.morts, self.blesses, self.neutr_adv, self.detecte_par_adv, self.debut_pas = [], [], 0, False, 0
        self.pts, self.axe, self.compromis = {}, None, [False, False]
        self.n_impacts, self.n_arretes = [0, 0], [0, 0]
        self.expo_debout = self.expo_marche = 0.0      # homme-secondes debout et en marche de la manoeuvre
        self.sig_debout = self.sig_n = 0               # sous-pas de marche de la manoeuvre vus debout, et en tout
        self.lesions_adverses = []                     # ( 03/10, HMT-197 4b ) ( homme, zone, arme, AIS, arretee )
        self.mortiers = None                           # ( 03/10, HMT-198 A1 ) les mortiers de l unite et leurs servants
        self.mortiers_adverses = None                  # ( 03/10, HMT-198 A1-bis ) ceux de l adversaire ( guerre/expedition )


class Tactiques:
    """L etat du domaine."""
    __slots__ = ("missions", "actives", "prochaine", "decideur", "qualifs", "formations", "tirs", "tirs_sortis",
                 "engages", "blesses", "morts", "contusions", "violations", "armes_perdues", "scenario", "camps",
                 "serie", "vus_journal", "refus", "ordres_arma", "en_mission", "reserve", "bilans", "exercices",
                 "notes_formation", "habites", "notes_par_compagnie")

    def __init__(self):
        self.missions = {}            # id -> Mission ( les actives, et les dernieres finies )
        self.actives = []             # ids des missions asynchrones en cours
        self.prochaine = 0
        self.decideur = None
        self.qualifs = {}             # habitant -> bits des tactiques qualifiees
        self.formations = {}          # compagnie -> ( tactique, jour de debut, [ habitants inscrits ] )
        self.tirs, self.tirs_sortis = {}, {}      # ( base, calibre ) -> coups demandes par le combat ; sortis du livre
        self.engages = set()          # habitants engages au combat reel ( controle des morts )
        self.blesses = []             # ( pas, mission, habitant, zone, ISS, evacuation ( moyen ) ou None )
        self.morts = []               # ( pas, mission, habitant, zone )
        self.contusions = []
        self.violations = []          # ( pas, mission, habitant, motif, affaire )
        self.armes_perdues = []
        self.scenario = None          # le scenario d exercices ( decision ) : { par_jour }
        self.camps = {}               # role de camp ( adverse, plastron ) -> nom au domaine 26
        self.serie = []
        self.vus_journal = 0
        self.refus = []
        self.ordres_arma = deque(maxlen=2000)
        self.en_mission = set()       # unites engagees dans une mission asynchrone
        self.reserve = {}             # ( base, calibre ) -> coups portes par les missions en cours
        self.bilans = deque(maxlen=5000)
        self.exercices = 0
        self.notes_formation = 0
        self.habites = None           # ( x, y, ile ) des lieux habites ( villages, villes, capitales )
        self.notes_par_compagnie = {}


def _dom(p): return p.domaines[DOMAINE]


# ================================================================== la connaissance et les regles d engagement
def _connaissance(p, camp, ent):
    return S.connaissance(p, camp, ent) if ent >= 0 else None


def identifiee(c, roe):
    """Identification positive : une connaissance d une source admise, recente et sure."""
    return (c is not None and c["source"] in roe.sources and c["age_h"] * 60.0 <= roe.age_max_min + 1e-9
            and c["confiance"] >= roe.conf_min)


def _pres_d_un_lieu_habite(p, x, y, ile, dist):
    H = _dom(p).habites
    m = H[:, 2] == ile
    return bool(m.any() and (np.hypot(H[m, 0] - x, H[m, 1] - y) <= dist).any())


def _en_zone_interdite(roe, x, y, ile):
    return any(int(zi) == ile and math.hypot(x - zx, y - zy) <= r for zx, zy, zi, r in roe.zones)


# ================================================================== les preconditions
def _aptes(p, u):
    """Les hommes presents et aptes d une unite : actifs au domaine 25, vivants, ni hospitalises ni detenus."""
    ids = A.membres(p, u, actifs_seulement=True)
    if not len(ids): return ids
    tb = p.w.table
    ok = tb.vivant[ids] == 1
    if p.a("hopitaux"):
        act = HM._dom(p).actifs
        ok &= np.array([int(h) not in act for h in ids.tolist()], bool)
    if "ju_detenu" in p.colonnes["habitant"]: ok &= p.col("habitant", "ju_detenu")[ids] == 0
    return ids[ok]


def verifier(p, tactique, u, cible=-1, camp=S.CAMP_NATIONAL, roe=ROE_DEFAUT):
    """Les preconditions d une tactique pour l unite u ( domaine 25 ) : [ raisons de refus ], vide si elle peut partir."""
    t = TACTIQUE[tactique] if isinstance(tactique, str) else tactique
    raisons = []
    n = len(_aptes(p, u))
    if n < t.effectif_min: raisons.append(f"effectif {n} < {t.effectif_min}")
    if t.munitions_min_j > 0 or t.autonomie_min_j > 0:
        au = S.autonomie(p, int(u))
        if au["munitions"] < t.munitions_min_j: raisons.append(f"munitions {au['munitions']:.2f} j < {t.munitions_min_j}")
        # 28/09 : l autonomie est la tenue de la garnison en carburant et en vivres ; les munitions ont leur seuil a elles
        # ( munitions_min_j, ci-dessus ). Comptees aussi dans l autonomie, une dotation de combat pleine ( 1 jour, domaine
        # 25 ) tombait pile sur le seuil de l embuscade et de la defense ( 1 jour ) : un tir d instruction les refusait,
        # alors que leur seuil de munitions ( 0,5 jour ) etait tenu.
        tenue = min(au["carburant"], au["vivres"])
        if tenue < t.autonomie_min_j: raisons.append(f"autonomie {tenue:.2f} j < {t.autonomie_min_j}")
    if t.connaissance != "aucune":
        c = _connaissance(p, camp, cible)
        if c is None: raisons.append("adversaire inconnu du camp")
        elif t.connaissance == "identifiee" and not (c["source"] in roe.sources and c["age_h"] <= t.age_max_h
                                                     and c["confiance"] >= t.conf_min):
            raisons.append(f"adversaire non identifie ( {c['source']}, {c['age_h']:.1f} h, confiance {c['confiance']:.2f} )")
    nuit = p.w.nuit()
    if t.lumiere == "jour" and nuit: raisons.append("il fait nuit")
    if t.lumiere == "nuit" and not nuit: raisons.append("il fait jour")
    if t.radio and (A.radios(p, u)[1] <= 0 or (S._camp(S._dom(p), camp), int(u)) in S._dom(p).radio_hs):
        raisons.append("pas de radio")
    return raisons


# ================================================================== la construction d une mission
def _repartir_roles(p, t, ids, n_adv=0):
    """Les roles : l appui prend d abord les mitrailleurs et le tireur d elite, les guetteurs le tireur d elite puis
    les fusiliers, le chef reste a la manoeuvre. Rend un tableau de roles ( indices de ROLES ) dans l ordre de ids."""
    n = len(ids)
    role = np.zeros(n, np.int64)
    if n < 3: return role
    E = A._dom(p).eff; r = A._rangs(p, ids); spec = E["spec"][r]
    na = int(round(t.part_appui * n)) if t.part_appui > 0 else 0
    ng = int(round(t.part_guetteurs * n)) if t.part_guetteurs > 0 else 0
    if t.part_appui > 0: na = max(1, na)
    if t.part_guetteurs > 0: ng = max(1, ng)
    pref_a = {A.MITRAILLEUR: 0, A.TIREUR_ELITE: 1, A.FUSILIER: 2, A.ANTICHAR: 3}
    pref_g = {A.TIREUR_ELITE: 0, A.RADIO_S: 1, A.FUSILIER: 2}
    libres = [i for i in range(n) if spec[i] not in (A.CHEF, A.OFFICIER)]
    for i in sorted(libres, key=lambda i: (pref_a.get(int(spec[i]), 9), i))[:na]: role[i] = 1
    libres = [i for i in libres if role[i] == 0]
    for i in sorted(libres, key=lambda i: (pref_g.get(int(spec[i]), 9), i))[:ng]: role[i] = 2
    return role


def _offsets(n, rng):
    """Les places des hommes autour du point de l element : jamais deux au meme point ( 8 a 16 m )."""
    k = np.arange(n); a = 2.0 * math.pi * k / max(1, n) + 0.3 * rng.random()
    r = 8.0 * (1.0 + (k % 2))
    return r * np.cos(a), r * np.sin(a)


def _table_hommes(n):
    return {nom: np.full(n, v, dt) for nom, dt, v in CHAMPS_HOMMES}


def _concat(h1, h2):
    return {k: np.concatenate((h1[k], h2[k])) for k in h1}


def _hommes_bleus(p, ids, roles, exercice, reserve):
    """Les colonnes de nos hommes : competences, portee utile ( arme ET optique ), protections, arme, munitions portees
    ( la dotation de combat de l arme, dans la limite de ce que l armurerie tient, engagements en cours deduits )."""
    a = A._dom(p); E = a.eff; r = A._rangs(p, ids); n = len(ids)
    h = _table_hommes(n)
    comp = A.competences(p, ids)
    h["hid"][:] = ids; h["tir"][:] = comp["tir"]; h["portee"][:] = A.portee_utile(p, ids)
    h["prot"][:] = E["protection"][r]; h["casque"][:] = E["casque"][r]; h["arme"][:] = E["arme_m"][r]
    # le tireur antichar ne tire pas ses roquettes sur des fantassins : il se bat a son arme de poing ( domaine 25 )
    lourd = np.isin(h["arme"], [A.IDX_ARME[n] for n in ARMES_LOURDES])
    h["arme"][lourd] = E["arme2_m"][r][lourd]
    h["portee"][lourd] = np.where(h["arme"][lourd] >= 0, A.PORTEE_ARME[np.maximum(h["arme"][lourd], 0)], 0.0)
    h["disc"][:] = comp["discipline"]; h["stress"][:] = comp["stress"]; h["moral"][:] = comp["moral"]
    h["base"][:] = E["base"][r]; h["elt"][:] = roles; h["moitie"][:] = np.arange(n) % 2
    cal = np.array([A.NOMS_MUNITIONS.index(A.ARMES[k].calibre) if k >= 0 else -1 for k in h["arme"].tolist()], np.int64)
    h["cal"][:] = cal
    dot = np.array([A.DOTATION_COMBAT.get(A.ARMES[k].nom, 0) if k >= 0 else 0 for k in h["arme"].tolist()], np.float64)
    if exercice:
        h["coups"][:] = dot
        return h
    lid = {b: p.w.carte.par_n[b].id for b in set(h["base"].tolist())}
    for (b, c) in sorted({(int(b), int(c)) for b, c in zip(h["base"].tolist(), cal.tolist()) if c >= 0}):
        m = (h["base"] == b) & (h["cal"] == c)
        stock = A.armurerie(p, lid[b]).stock[A._dom(p).bids[A.NOMS_MUNITIONS[c]]]
        dispo = max(0.0, stock - reserve.get((lid[b], c), 0.0))
        f = min(1.0, dispo / max(EPS, dot[m].sum()))
        h["coups"][m] = np.floor(dot[m] * f)
        reserve[(lid[b], c)] = reserve.get((lid[b], c), 0.0) + float(h["coups"][m].sum())
    h["coups"][cal < 0] = 0.0
    return h


def _hommes_rouges(n, tir=TIR_ADVERSE, portee=PORTEE_ADVERSE, prot=-1, casque=-1, moral=MORAL_ADVERSE):
    h = _table_hommes(int(n))
    h["side"][:] = 1; h["tir"][:] = tir; h["portee"][:] = portee; h["prot"][:] = prot; h["casque"][:] = casque
    h["disc"][:] = moral; h["moral"][:] = moral
    return h


def _points(m, p):
    """Les buts nommes d une mission ( m, dans le repere de son ile )."""
    x0, y0 = m.depart; x1, y1 = m.objectif
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = ((x1 - x0) / L, (y1 - y0) / L) if L > EPS else (1.0, 0.0)
    nx, ny = -uy, ux
    pts = {"depart": (x0, y0), "objectif": (x1, y1)}
    if m.adv_cru is not None:
        ax, ay, ray = m.adv_cru
        dd = math.hypot(ax - x0, ay - y0)
        k = max(0.0, dd - DIST_APPUI_M) / max(dd, EPS)
        pts["appui"] = (x0 + k * (ax - x0), y0 + k * (ay - y0))
        cote = (ax - x0) * nx + (ay - y0) * ny
        sgn = -1.0 if cote > 0 else 1.0
        proj = (ax - x0) * ux + (ay - y0) * uy
        dg = DEGAGEMENT_M + ray
        pts["contournement"] = (x0 + proj * ux + sgn * max(0.0, dg - abs(cote)) * nx,
                                y0 + proj * uy + sgn * max(0.0, dg - abs(cote)) * ny)
        pts["op"] = (ax - 300.0 * (ax - x0) / max(dd, EPS), ay - 300.0 * (ay - y0) / max(dd, EPS))
    else:
        s = 1.0 if m.rng.random() < 0.5 else -1.0
        pts["appui"] = (x0, y0)
        pts["contournement"] = (x0 + 0.5 * L * ux + s * DEGAGEMENT_M * nx, y0 + 0.5 * L * uy + s * DEGAGEMENT_M * ny)
        pts["op"] = (x1 - 300.0 * ux, y1 - 300.0 * uy)
    return pts


def _chemin(m, p, but):
    pts = m.pts
    if but == "sur_place": return []
    if but == "itineraire": return [tuple(q) for q in m.itineraire] or [pts["objectif"]]
    if but == "contournement": return [pts["contournement"], pts["objectif"]]
    return [pts[but]]


def nouvelle_mission(p, tactique, u, depart, objectif, adverses=(), mode="combat", voix=None, roe=ROE_DEFAUT,
                     critere=None, itineraire=(), seed=None, cible=-1, couvert_poste="leger", feu_sur_contact=False,
                     fenetre_min=None, ile=None, exercice_rouge=None, axe=None):
    """Construit une mission SANS la lancer ( les portes et le scenario s en servent ; `lancer` verifie d abord les
    preconditions ). adverses : [ ( entite du domaine 26, taille, conduite, chemin, regard ) ] ; exercice_rouge : les
    habitants d une unite plastron ( exercice entre deux compagnies ). Rend la Mission."""
    d = _dom(p); w = p.w
    t = TACTIQUE[tactique] if isinstance(tactique, str) else tactique
    mid = d.prochaine; d.prochaine += 1
    cle = seed if isinstance(seed, tuple) else (mid if seed is None else seed,)
    rng = p.socle.hasard.sous_flux("armee_tactique_mission", *cle)
    if ile is None: ile = S.position(p, S.CAMP_NATIONAL, u)[2]
    exo = mode == "exercice"
    m = Mission(mid, t, int(u), mode, exo if voix is None else voix, ile, depart, objectif, roe, critere or t.critere, rng)
    m.itineraire = [tuple(q) for q in itineraire]
    m.feu_sur_contact = bool(feu_sur_contact); m.couvert_poste = COUVERTS.index(couvert_poste)
    m.nuit = w.nuit(); m.debut_pas = w.pas
    m.fenetre_s = None if fenetre_min is None else 60.0 * float(fenetre_min)
    if m.fenetre_s is not None: m.t_max_s = max(m.t_max_s, m.fenetre_s)
    U = A._dom(p).unites
    m.chef = int(U["chef"][u])
    m.compagnie = int(U["a3"][u]) if int(U["niveau"][u]) >= A.COMPAGNIE else -1
    b = int(U["base"][u]) if int(U["base"][u]) >= 0 else int(A._dom(p).eff["base"][A._rangs(p, [m.chef])[0]])
    m.base_lid = w.carte.par_n[b].id
    ids = _aptes(p, u)
    roles = _repartir_roles(p, t, ids)
    h = _hommes_bleus(p, ids, roles, exo, d.reserve)
    m.qual = qualification(p, ids, t.nom)
    # l adversaire cru ( ce que le camp sait : jamais la verite )
    c = _connaissance(p, S.CAMP_NATIONAL, cible)
    if c is not None: m.adv_cru = (c["x"], c["y"], c["sigma_m"] + min(c["rayon_m"], 500.0))
    elif adverses:
        for ent, *_ in adverses:
            c = _connaissance(p, S.CAMP_NATIONAL, ent)
            if c is not None: m.adv_cru = (c["x"], c["y"], c["sigma_m"] + min(c["rayon_m"], 500.0)); break
    m.axe = axe
    m.pts = _points(m, p)
    x0, y0 = m.depart
    for k, role in enumerate(ROLES):
        sel = np.nonzero(roles == k)[0]
        if not len(sel): continue
        e = Element(0, role, S.CAMP_NATIONAL, x0, y0, len(sel), u)
        e.couvert = m.couvert_poste
        m.elts.append(e)
        h["elt"][sel] = len(m.elts) - 1
    dx, dy = _offsets(len(ids), rng); h["dx"][:] = dx; h["dy"][:] = dy
    # l adversaire ( ou le plastron )
    for ent, taille, cond, chemin, regard in adverses:
        E26 = S._dom(p).ent
        e = Element(1, "adversaire", S._dom(p).camps[int(E26["camp"][ent])].nom, float(E26["x"][ent]), float(E26["y"][ent]),
                    int(taille))
        e.ent, e.cond, e.chemin, e.regard = int(ent), cond, [tuple(q) for q in chemin], regard
        e.v_propre = float(E26["vitesse"][ent])
        m.elts.append(e)
        if exercice_rouge is not None and len(exercice_rouge):
            ids_r = np.asarray(exercice_rouge, np.int64)[:int(taille)]
            hr = _hommes_bleus(p, ids_r, np.zeros(len(ids_r), np.int64), True, d.reserve)
            hr["side"][:] = 1; hr["hid"][:] = -1         # le plastron est simule : ni blessure ni munition
        else:
            hr = _hommes_rouges(taille)
            hr["arme"][:] = A.IDX_ARME[ARME_ADVERSE]
        hr["elt"][:] = len(m.elts) - 1
        rx, ry = _offsets(len(hr["hid"]), rng); hr["dx"][:] = rx; hr["dy"][:] = ry
        h = _concat(h, hr)
    m.h = h
    m.cibles = [e.ent for e in m.elts if e.side == 1]
    if mode == "combat" and TIR_INDIRECT: m.mortiers = _mortiers_mission(p, m, u, ids)     # ( HMT-198 A1 )
    for e in m.elts:
        if e.side == 0:
            e.ent = S.poser_entite(p, S.CAMP_NATIONAL, e.x, e.y, m.ile, posture="accroupi",
                                   taille=int((h["elt"] == m.elts.index(e)).sum()), vitesse_ms=0.0, unite=u)
    d.missions[mid] = m
    return m


# ================================================================== l execution
def lancer(p, tactique, u, depart, objectif, cible=-1, **kw):
    """Lance une tactique pour l unite u ( domaine 25 ) : les preconditions d abord ( refus : ( None, raisons ) ), puis
    la mission, le transport s il faut, l activite imposee au domaine 25, la premiere phase et son ORDRE ( domaine 26 ).
    La mission avance a chaque pas ( echeance du socle ). Rend ( Mission, [] )."""
    d = _dom(p)
    t = TACTIQUE[tactique] if isinstance(tactique, str) else tactique
    roe = kw.get("roe", ROE_DEFAUT)
    raisons = verifier(p, t, u, cible, roe=roe)
    if int(u) in d.en_mission: raisons.append("unite deja engagee")
    if raisons:
        d.refus.append((p.w.pas, int(u), t.nom, tuple(raisons)))
        p.noter("tactique_refusee", unite=int(u), tactique=t.nom, raisons="; ".join(raisons))
        return None, raisons
    m = nouvelle_mission(p, t, u, depart, objectif, cible=cible, **kw)
    if m.mode == "combat":
        d.engages.update(int(x) for x in m.h["hid"][m.h["hid"] >= 0].tolist())
        if not _transporter(p, m):
            _clore(p, m, "sans_carburant"); return None, ["pas assez de gazole pour le transport"]
    d.en_mission.add(int(u))
    p.compter("mission_lancee")
    _ouvrir_phase(p, m)
    d.actives.append(m.id)
    p.poser(0, "armee_tactique_pas", m.id)
    return m, []


def _transporter(p, m):
    """Au-dela de KM_TRANSPORT, l unite est portee en camion ( aller et retour ) : le gazole de la garnison brule."""
    w = p.w; base = w.carte.lieux[m.base_lid]
    km = math.hypot(m.depart[0] - base.pos[0], m.depart[1] - base.pos[1]) / 1000.0
    if km <= KM_TRANSPORT: return True
    n = int((m.h["side"] == 0).sum())
    q = math.ceil(n / PLACES_CAMION) * 2.0 * 1.3 * km * A.VEHICULE["steyr_12m18"].unites_par_km
    cat = p.socle.catalogue
    g = w.garnisons[m.base_lid]
    if g.get("carburant", 0.0) < q: return False
    p.socle.livre.puits(EXT.StockE1(g, cat), cat.id("carburant"), q, "brule", "carburant_tactique")
    return True


def _chef_de(p, u):
    U = A._dom(p).unites; par = int(U["parent"][u])
    return par if par >= 0 else int(u)


def _ouvrir_phase(p, m):
    """La phase k commence : chaque element recoit sa conduite et son chemin ; si la phase a un ordre et que la mission
    n est pas a la voix, l ordre part par le domaine 26 et la phase attend sa reception."""
    ph = m.tactique.phases[m.k]
    for e in m.elts:
        if e.side != 0: continue
        e.cond = ph.conduites.get(e.role) or Conduite("fixe", regard="adversaire", feu="riposte")
        e.chemin = _chemin(m, p, e.cond.but) if e.cond.mode != "fixe" else []
        e.arrive = not e.chemin
        e.voulu = e.chemin[-1] if e.chemin else None
        seq = []
        if e.chemin:
            for q in e.chemin: seq += A.ordre_de_mouvement(p, m.unite, q)
        elif ph.ordre == "tenir":
            seq.append(("doStop", m.unite, None))
        _dom(p).ordres_arma.append((p.w.pas, m.id, e.role, seq))
    m.t_phase_s = m.t_s
    m.ordre = -1
    if ph.ordre is not None and not m.voix:
        dest = next((e.chemin[-1] for e in m.elts if e.side == 0 and e.role == ph.role_fin and e.chemin), m.objectif)
        if ph.ordre == "mouvement":
            k = S.emettre_ordre(p, _chef_de(p, m.unite), m.unite, "mouvement", a=dest[0], b=dest[1],
                                echeance=p.w.pas + int(math.ceil(ph.echeance_min / C.MINUTES_PAR_PAS)))
        else:
            k = S.emettre_ordre(p, _chef_de(p, m.unite), m.unite, "tenir", a=ph.duree_min / 60.0,
                                echeance=p.w.pas + int(math.ceil(ph.echeance_min / C.MINUTES_PAR_PAS)))
        m.ordre = k; m.ordre_emis_s = m.t_s; m.ordres.append(k)
        p.compter("ordre_tactique")


def _ordre_attendu(p, m):
    """Vrai tant que l ordre de la phase n est pas recu. Un ordre recu MAL COMPRIS deplace la destination ( le domaine 26
    l a tire ) ; un ordre perdu ou en retard au-dela de son echeance est reemis."""
    if m.ordre < 0: return False
    o = S.ordre(p, m.ordre)
    if o["etat"] == "recu":
        ph = m.tactique.phases[m.k]
        if o["contenu"] == "mouvement" and not o["bien_compris"]:
            for e in m.elts:
                if e.side == 0 and e.role == ph.role_fin and e.chemin: e.chemin[-1] = (o["compris"][0], o["compris"][1])
        m.ordre = -1; m.t_phase_s = m.t_s
        return False
    ph = m.tactique.phases[m.k]
    if o["etat"] == "perdu" or m.t_s - m.ordre_emis_s > 60.0 * ph.echeance_min + 1e-6:
        p.compter("ordre_reemis")
        dest = o["voulu"]
        m.ordre = S.emettre_ordre(p, _chef_de(p, m.unite), m.unite, o["contenu"], a=dest[0], b=dest[1],
                                  echeance=p.w.pas + int(math.ceil(ph.echeance_min / C.MINUTES_PAR_PAS)))
        m.ordre_emis_s = m.t_s; m.ordres.append(m.ordre)
    return True


def _pas_mission(p, mid, donnees=()):
    """L echeance de chaque pas : la mission vit 10 minutes."""
    d = _dom(p); m = d.missions.get(mid)
    if m is None or m.fini: return
    _avancer(p, m, PAS_S)
    if not m.fini: p.poser(1, "armee_tactique_pas", mid)


def executer(p, m):
    """Une mission SYNCHRONE ( exercice, porte ) : elle vit jusqu a sa fin dans l appel ( ordres a la voix ). Rend son
    resultat."""
    if all(e.cond is None for e in m.elts if e.side == 0): _ouvrir_phase(p, m)
    while not m.fini:
        _avancer(p, m, PAS_S)
        if m.t_s >= DUREE_MAX_S and not m.fini: _clore(p, m, "temps")
    return m.resultat


def _actifs(m, e_idx):
    h = m.h
    return np.nonzero((h["elt"] == e_idx) & (h["actif"] == 1))[0]


def _avancer(p, m, budget_s):
    """La mission vit `budget_s` secondes par sous-pas de 30 s : ordres, mouvements, detection ( domaine 26 ), feu,
    impacts, suppression, rupture, fin de phase. Les blessures du bloc sont traitees a la fin ( tri, evacuation )."""
    t_fin = m.t_s + budget_s
    while m.t_s < t_fin - 1e-6 and not m.fini:
        attend = _ordre_attendu(p, m)
        _sous_pas(p, m, DT_S, attend)
        m.t_s += DT_S
        if m.fini: break
        if not attend: _fin_de_phase(p, m)
        if not m.fini and (m.t_s >= m.t_max_s or not len(np.nonzero((m.h["side"] == 0) & (m.h["actif"] == 1))[0])):
            _clore(p, m, "temps" if m.t_s >= m.t_max_s else "aneanti")
    _traiter_pertes(p, m)
    _payer_tirs(p, m)


def _fin_de_phase(p, m):
    ph = m.tactique.phases[m.k]
    t = m.t_s - m.t_phase_s
    if m.rupture:
        if all(e.arrive for e in m.elts if e.side == 0): _clore(p, m, "rupture")
        return
    fin = False
    if t >= 60.0 * ph.duree_min - 1e-6: fin = True
    elif ph.fin == "arrive":
        fin = all(e.arrive or not len(_actifs(m, i)) for i, e in enumerate(m.elts) if e.side == 0 and e.role == ph.role_fin)
    elif ph.fin == "zone":
        fin = _adverse_en_zone(p, m)
    elif ph.fin == "neutralise":
        fin = not any(len(_actifs(m, i)) for i, e in enumerate(m.elts) if e.side == 1)
    if not fin: return
    if m.k + 1 >= len(m.tactique.phases): _clore(p, m, "fin"); return
    m.k += 1
    _ouvrir_phase(p, m)


def _adverse_en_zone(p, m):
    """Le declenchement : un element adverse CONNU du camp ( vu par les guetteurs, domaine 26 ) dont la position crue
    est dans la zone de destruction. Jamais la verite : de nuit, sans vision nocturne, un homme accroupi n est vu qu a
    ~ 126 m ( domaines 25 et 26 )."""
    bx, by = m.elts[0].x, m.elts[0].y
    for e in m.elts:
        if e.side != 1: continue
        c = _connaissance(p, S.CAMP_NATIONAL, e.ent)
        if c is not None and c["age_h"] * 60.0 <= 2.0 and math.hypot(c["x"] - bx, c["y"] - by) <= ZONE_EMBUSCADE_M:
            return True
    return False


# ------------------------------------------------------------------ le sous-pas
def _regard(m, e, pts):
    """L azimut du regard d un element ( radians ) : dans le sens de la marche, vers l objectif, vers l adversaire cru,
    vers l arriere ; None : il balaie."""
    if e.side == 1:
        if e.chemin: return S.azimut(e.x, e.y, *e.chemin[0])
        return e.regard
    if e.tireurs_de:                                   # on nous tire dessus : les hommes tournent la tete vers le bruit
        j = min(e.tireurs_de); t = m.elts[j]
        return S.azimut(e.x, e.y, t.x, t.y)
    r = e.cond.regard if e.cond is not None else "objectif"
    if r == "marche" and e.chemin: return S.azimut(e.x, e.y, *e.chemin[0])
    if r == "adversaire" and m.adv_cru is not None: return S.azimut(e.x, e.y, m.adv_cru[0], m.adv_cru[1])
    if r == "adversaire" and m.axe is not None: return m.axe
    if r == "arriere": return S.azimut(e.x, e.y, *pts["depart"])
    return S.azimut(e.x, e.y, *pts["objectif"]) if math.hypot(e.x - pts["objectif"][0], e.y - pts["objectif"][1]) > 1 \
        else S.azimut(pts["depart"][0], pts["depart"][1], *pts["objectif"])


def _bouger(m, e, i, dt, attend):
    """Un element avance le long de son chemin ; la suppression le cloue ( moins s il est discipline ) ; un element en
    simultane sous le feu se couche et riposte ( il ne bouge pas ce sous-pas )."""
    c = e.cond
    if attend or c is None or c.mode == "fixe" or not e.chemin:
        e.posture_sig = "debout" if (c is not None and c.mode == "fixe" and c.posture == "debout") else "accroupi"
        return False
    act = _actifs(m, i)
    if not len(act): return False
    v = e.v_propre if (e.side == 1 and e.v_propre) else VITESSE[c.mode]
    disc = float(m.h["disc"][act].mean())
    if e.side == 0 and c.mode in ("bond", "infiltration", "repli"): v *= 1.0 + Q_VITESSE * m.qual
    v *= 1.0 - e.supp * (1.0 - 0.5 * disc)
    if c.mode == "simultane" and e.feu_recu > 0: v = 0.0
    reste = v * dt
    while reste > EPS and e.chemin:
        tx, ty = e.chemin[0]
        dd = math.hypot(tx - e.x, ty - e.y)
        if dd <= reste + RAYON_ARRIVE_M:
            e.x, e.y = tx, ty; reste -= dd; e.chemin.pop(0)
        else:
            e.x += reste * (tx - e.x) / dd; e.y += reste * (ty - e.y) / dd; reste = 0.0
    if not e.chemin:
        if e.side == 0 and e.voulu is not None and math.hypot(e.x - e.voulu[0], e.y - e.voulu[1]) > 50.0:
            e.chemin = [e.voulu]                             # un ordre mal compris : le chef corrige a la carte
        else:
            e.arrive = True
            if e.side == 0 and math.hypot(e.x - m.objectif[0], e.y - m.objectif[1]) <= RAYON_ARRIVE_M + 1.0:
                h = m.h; h["arrive_s"][act] = np.where(h["arrive_s"][act] < 0, m.t_s + dt, h["arrive_s"][act])
    e.posture_sig = "accroupi" if c.mode == "infiltration" else "debout"
    return v > 0


def _detecter(p, m, pts):
    """Une detection par minute et par camp, par le domaine 26 : nos hommes regardent ( leur perception du domaine 25,
    le regard de leur element ), l adversaire regarde par ses entites ; qui voit qui ce sous-pas ( e.vu )."""
    E26 = S._dom(p).ent
    for e in m.elts:
        e.vu = set()
        if e.ent >= 0 and E26["vivant"][e.ent]:
            # nos elements a l arret se montrent dans la posture de leur conduite ( couches en embuscade, en defense ) ;
            # en marche, dans celle de leur mode ( 27/09 : a l arret ils gardaient la signature de leur derniere marche -
            # debout apres une occupation, accroupis apres une infiltration - et l embuscade couchee se voyait a 231 m de
            # jour ; les postes adverses gardent la posture ou ils sont poses, accroupie comme les menaces d Arma )
            fixe = e.side == 0 and e.cond is not None and e.cond.mode == "fixe"
            S.deplacer_entite(p, e.ent, e.x, e.y, SIGNATURE_FEU if e.fait_feu else (e.cond.posture if fixe else e.posture_sig))
    bleus = [i for i, e in enumerate(m.elts) if e.side == 0]
    rouges = [i for i, e in enumerate(m.elts) if e.side == 1 and len(_actifs(m, i)) and E26["vivant"][e.ent]]
    if not rouges or not bleus: return
    h = m.h
    obs, pos, reg, jum = [], [], [], []
    for i in bleus:
        act = _actifs(m, i)
        if not len(act): continue
        e = m.elts[i]; az = _regard(m, e, pts)
        obs.append(h["hid"][act]); pos.append(np.column_stack((e.x + h["dx"][act], e.y + h["dy"][act])))
        reg.append(np.full(len(act), az if az is not None else 0.0))
        jum.append(np.full(len(act), F_JUMELLES if (e.role == "guetteurs" and not m.nuit) else 1.0))
    if obs:
        obs = np.concatenate(obs)
        port = A.perception(p, obs, m.nuit)[1] * np.concatenate(jum)
        vus = S.observer(p, S.CAMP_NATIONAL, obs, np.concatenate(pos), np.concatenate(reg), m.nuit, portees=port,
                         cibles=[m.elts[i].ent for i in rouges], ile=m.ile,
                         source="patrouille" if m.tactique.nom == "patrouille" else "observation")
        vues = {c for c, _, _ in vus}
        for i in bleus:
            m.elts[i].vu = {j for j in rouges if m.elts[j].ent in vues}
    cibles_b = [m.elts[i].ent for i in bleus if len(_actifs(m, i))]
    if not cibles_b: return
    par_camp = {}
    for j in rouges: par_camp.setdefault(m.elts[j].camp, []).append(j)
    for camp, js in sorted(par_camp.items()):
        for avec_regard in (True, False):
            sel = [j for j in js if (_regard(m, m.elts[j], pts) is not None) == avec_regard]
            if not sel: continue
            regs = np.array([_regard(m, m.elts[j], pts) for j in sel], np.float64) if avec_regard else None
            vus = S.observer(p, camp, [m.elts[j].ent for j in sel], None, regs, m.nuit, cibles=cibles_b, ile=m.ile)
            vues = {c for c, _, _ in vus}
            for j in sel:
                m.elts[j].vu = {i for i in bleus if m.elts[i].ent in vues}
            if vues: m.detecte_par_adv = True


def _connu_de(p, m, e_obs, e_cible):
    """Ce que le camp de l element observateur sait de l element cible ( domaine 26 ), ou None."""
    return _connaissance(p, e_obs.camp, e_cible.ent)


def _peut_tirer(p, m, i, j, c_cible):
    """Les regles d engagement de NOTRE element i sur l element adverse j : ( permis, motif de violation si on tire
    quand meme )."""
    e, t = m.elts[i], m.elts[j]
    if _en_zone_interdite(m.roe, t.x, t.y, m.ile): return False, "zone_interdite"
    hostile = j in e.tireurs_de and c_cible is not None and c_cible["source"] not in ("population", "medias")
    if not (identifiee(c_cible, m.roe) or hostile): return False, "sans_identification"
    if e.cond.feu == "appui" and _pres_d_un_lieu_habite(p, t.x, t.y, m.ile, m.roe.dist_civils_m):
        return False, "disproportion"
    return True, None


def _sous_pas(p, m, dt, attend):
    h = m.h; rng = m.rng
    pts = m.pts
    par = int(round(m.t_s / DT_S)) % 2
    bouge = [_bouger(m, e, i, dt, attend) for i, e in enumerate(m.elts)]
    if m.t_s - m.t_det >= DETECTION_S - 1e-6:
        _detecter(p, m, pts); m.t_det = m.t_s
    # l exposition de chaque homme ( ce qui rend la balle plus ou moins probable ) et sa posture pour la zone touchee
    n = len(h["hid"])
    expo = np.zeros(n); debout = np.zeros(n)
    for i, e in enumerate(m.elts):
        sel = np.nonzero(h["elt"] == i)[0]
        if not len(sel): continue
        c = e.cond
        up = np.zeros(len(sel))
        if bouge[i] and c.mode == "simultane":                     # debout, a decouvert, tout le sous-pas
            up[:] = 1.0; ex = np.full(len(sel), F_CIBLE_MARCHE)
        elif bouge[i] and c.mode in ("bond", "repli"):             # une moitie court ~ 10 s, l autre couvre, couchee
            up = np.where(h["moitie"][sel] == par, T_BOND_S / dt, 0.0)
            ex = up * F_CIBLE_COURT + (1.0 - up) * F_POSTURE_TIR[COUCHE] * F_COUVERT[1]
        elif bouge[i]:                                             # infiltration : accroupi, a couvert leger
            ex = np.full(len(sel), F_POSTURE_TIR[ACCROUPI] * F_COUVERT[1])
        else:                                                      # a l arret : sa posture, le couvert de sa position
            pst = COUCHE if c is None else POSTURES.index(c.posture)
            cv = e.couvert if (c is not None and c.mode == "fixe") else 1
            ex = np.full(len(sel), F_POSTURE_TIR[pst] * F_COUVERT[cv])
        if bouge[i] and e.side == 0 and e.role == "manoeuvre" and not m.rupture:   # le risque MESURE ( hors deroute )
            m.expo_debout += float(up.sum()) * dt; m.expo_marche += len(sel) * dt
            m.sig_n += 1; m.sig_debout += int(e.posture_sig == "debout")
        if bouge[i] and e.feu_recu <= 0.0:                         # surpris : il se couche apres T_REACTION_S
            fr = T_REACTION_S / dt
            ex = fr * ex + (1.0 - fr) * F_POSTURE_TIR[COUCHE] * F_COUVERT[1]
            up = up * fr
        if e.side == 0: ex = ex * (1.0 - Q_EXPOSITION * m.qual)
        expo[sel] = ex; debout[sel] = up
    # le feu
    impacts = {}          # ( element cible ) -> [ ( balles, p ) ] ; et les tireurs
    recu = np.zeros(len(m.elts))
    for i, e in enumerate(m.elts):
        e.fait_feu = False
        c = e.cond
        if c is None or c.feu == "aucun": continue
        tireurs = _actifs(m, i)
        if not len(tireurs): continue
        adverses = [j for j, t in enumerate(m.elts) if t.side != e.side and len(_actifs(m, j))]
        if not adverses: continue
        connus = []
        for j in adverses:
            cc = _connu_de(p, m, e, m.elts[j])
            if cc is not None: connus.append((math.hypot(m.elts[j].x - e.x, m.elts[j].y - e.y), j, cc))
        if not connus: continue
        dist, j, cc = min(connus, key=lambda x: (x[0], x[1]))
        compromis = e.feu_recu > 0 or bool(e.tireurs_de) or m.compromis[e.side]
        if c.feu == "tenu" and not compromis: continue
        if c.feu == "riposte" and not compromis: continue
        if e.side == 0:
            ok, motif = _peut_tirer(p, m, i, j, cc)
            if m.feu_sur_contact and not ok:
                _violation(p, m, m.chef, motif); ok = True
            if not ok:
                ind = tireurs[np.argsort(h["disc"][tireurs], kind="stable")[:1]]
                pv = (P_VIOLATION * (1.0 - float(h["disc"][ind[0]])) * (1.0 + float(h["stress"][ind[0]]))
                      * (1.0 - Q_VIOLATION * m.qual))
                if not h["viole"][ind[0]] and rng.random() < pv:
                    _violation(p, m, int(h["hid"][ind[0]]), motif); h["viole"][ind[0]] = 1
                    tireurs = ind
                else:
                    continue
        tgt = m.elts[j]
        dd = np.hypot(tgt.x - (e.x + h["dx"][tireurs]), tgt.y - (e.y + h["dy"][tireurs]))
        statique = np.ones(len(tireurs), bool)
        if bouge[i] and c.mode in ("bond", "repli"): statique = h["moitie"][tireurs] != par
        elif bouge[i] and c.mode == "infiltration": statique[:] = False
        en_marche = bouge[i] & (c.mode == "simultane")
        if c.feu == "appui":
            cad = np.array([CADENCE_APPUI_BPS.get(A.ARMES[k].nom, CADENCE_APPUI_FUSIL_BPS) if k >= 0 else 0.0
                            for k in h["arme"][tireurs].tolist()])
        else: cad = np.full(len(tireurs), CADENCE_VISEE_BPS)
        cap_c = 1.0 - e.supp * (1.0 - SUPP_CADENCE); cap_p = 1.0 - e.supp * (1.0 - SUPP_PRECISION)
        balles = cad * dt * cap_c * (statique | en_marche)
        balles = np.minimum(np.floor(balles + rng.random(len(tireurs))), h["coups"][tireurs])
        if not balles.sum(): continue
        act_t = _actifs(m, j)
        ex_t = float(expo[act_t].mean()) if len(act_t) else 0.0
        vu = j in e.vu
        pb = p_toucher(dd, h["tir"][tireurs], h["portee"][tireurs], DEBOUT, 0, vu, en_marche) * ex_t * cap_p
        hits = rng.binomial(balles.astype(np.int64), np.clip(pb, 0.0, 1.0))
        h["coups"][tireurs] -= balles; h["tires"][tireurs] += balles
        e.fait_feu = True
        if m.mode == "combat" and e.side == 0:
            for k2, q in zip(tireurs.tolist(), balles.tolist()):
                if q <= 0: continue
                key = (p.w.carte.par_n[int(h["base"][k2])].id, int(h["cal"][k2]))
                m.tirs[key] = m.tirs.get(key, 0.0) + q
        p.compter("coups_tires" if m.mode == "combat" else "coups_simules", float(balles.sum()))
        recu[j] += float(balles.sum()) / dt
        tgt.tireurs_de.add(i)
        if hits.sum(): impacts.setdefault(j, []).extend((int(k2), int(x)) for k2, x in zip(tireurs.tolist(), hits.tolist()) if x)
    _tir_indirect(p, m, debout, rng, dt)                       # ( 03/10, HMT-198 A1 ) les mortiers
    _tir_indirect_adverse(p, m, debout, rng, dt)               # ( 03/10, HMT-198 A1-bis ) ceux de l adversaire
    # les impacts : chacun sur un homme actif de l element cible, au prorata de son exposition
    for j in sorted(impacts):
        for tireur, nh in impacts[j]:
            for _ in range(nh):
                act = _actifs(m, j)
                if not len(act): break
                w_ = expo[act] / max(EPS, expo[act].sum())
                v = int(act[min(len(act) - 1, int(np.searchsorted(np.cumsum(w_), rng.random())))])
                pz = debout[v] * P_ZONE_EXPOSE + (1 - debout[v]) * P_ZONE_ABRITE
                z = ZONES[min(4, int(np.searchsorted(np.cumsum(pz), rng.random())))]
                _impact(p, m, v, z, int(h["arme"][tireur]))
    # la suppression du sous-pas suivant, la rupture
    for j, e in enumerate(m.elts):
        act = _actifs(m, j)
        e.feu_recu = recu[j]
        if recu[j] > 0: m.compromis[e.side] = True          # un element sous le feu : tout son camp riposte
        e.supp = min(1.0, recu[j] / (SUPP_BPS_HOMME * len(act))) if len(act) else 0.0
        if not recu[j]: e.tireurs_de = set()
    _rupture(p, m)


def _mortiers_mission(p, m, u, ids):
    """( 03/10, HMT-198 A1 ) Les mortiers de l unite u ( ses sections d appui, a sa base ) et leurs servants dans la
    mission ( les hommes de specialite MORTIER au domaine 25 : le mortier est une arme collective, ses servants gardent
    leur fusil ). None s il n y en a pas."""
    a = A._dom(p); U = a.unites; K = a.coll; im = A.IDX_ARME["mortier_81"]
    tubes = []
    for k in range(K.n):
        if int(K["oid"][k]) < 0 or int(K["modele"][k]) != im: continue
        x = int(K["unite"][k])
        while x >= 0 and x != int(u): x = int(U["parent"][x])
        if x == int(u): tubes.append(k)
    if not tubes: return None
    r = A._rangs(p, ids)
    serv = [v for v, rr in enumerate(r.tolist()) if int(a.eff["spec"][rr]) == A.MORTIER]   # les servants ( specialite )
    if not serv: return None
    return {"tubes": tubes, "servants": serv, "base": m.base_lid, "tires": 0.0,
            "dotation": float(A.DOTATION_COMBAT.get("mortier_81", 0)) * len(tubes)}


def _tir_indirect(p, m, debout, rng, dt):
    """( 03/10, HMT-198 A1 ) Le tir des mortiers de la mission pendant un sous-pas ( voir la fiche du correctif ). Rend
    les obus tires."""
    M = getattr(m, "mortiers", None)
    if not TIR_INDIRECT or not M or m.mode != "combat" or m.rupture: return 0
    h = m.h
    serv = [v for v in M["servants"] if h["actif"][v] == 1]
    tubes = min(len(M["tubes"]), len(serv) // SERVANTS_PAR_TUBE)
    if tubes <= 0: return 0
    e0 = m.elts[int(h["elt"][serv[0]])]; x0, y0 = e0.x, e0.y
    cal = A.NOMS_MUNITIONS.index("obus_81"); cle = (M["base"], cal)
    stock = float(A.armurerie(p, M["base"]).stock[A._dom(p).bids["obus_81"]]) - m.tirs.get(cle, 0.0) - _dom(p).reserve.get(cle, 0.0)
    cibles = []
    for j, t in enumerate(m.elts):
        if t.side != 1 or not len(_actifs(m, j)): continue
        c = _connaissance(p, S.CAMP_NATIONAL, t.ent)
        if c is None or c["age_h"] * 60.0 > AGE_MAX_TIR_MIN: continue          # une connaissance FRAICHE ( l observateur )
        dd = math.hypot(c["x"] - x0, c["y"] - y0)
        if PORTEE_MIN_MORTIER <= dd <= A.ARME["mortier_81"].portee_m: cibles.append((dd, j, c))
    if not cibles: return 0
    dd, j, c = min(cibles, key=lambda x: (x[0], x[1]))
    n = int(math.floor(CADENCE_MORTIER_CPM * dt / 60.0 * tubes + rng.random()))
    n = int(min(n, max(0.0, math.floor(stock)), max(0.0, M["dotation"] - M["tires"])))
    if n <= 0: return 0
    t = m.elts[j]; act = _actifs(m, j)
    sig = math.sqrt(float(c["sigma_m"]) ** 2 + (CEP_PART_PORTEE * dd / 1.1774) ** 2)
    cz = np.cumsum(P_ZONE_EXPOSE)
    for _ in range(n):
        act = _actifs(m, j)
        if not len(act): break
        ix, iy = float(c["x"]) + rng.normal(0.0, sig), float(c["y"]) + rng.normal(0.0, sig)
        r = np.hypot(t.x + h["dx"][act] - ix, t.y + h["dy"][act] - iy)
        f_eclat = (debout[act] + (1.0 - debout[act]) * F_COUCHE_ECLAT) * (F_DUR_ECLAT if t.couvert == 2 else 1.0)
        pr = P_ECLAT * np.clip(1.0 - (r / RAYON_ECLAT_M) ** 2, 0.0, 1.0) * f_eclat
        for v in act[rng.random(len(act)) < pr].tolist():
            if h["actif"][v] != 1: continue
            z = ZONES[min(4, int(np.searchsorted(cz, rng.random())))]
            _impact(p, m, int(v), z, A.IDX_ARME["mortier_81"])
    m.tirs[cle] = m.tirs.get(cle, 0.0) + n; M["tires"] += n
    t.feu_recu += n / dt
    p.compter("coups_tires", float(n))
    return n


def _tir_indirect_adverse(p, m, debout, rng, dt):
    """( 03/10, HMT-198 A1-bis ) Le tir des mortiers de l adversaire ( m.mortiers_adverses ) sur notre element que son
    camp connait. Rend les obus tires."""
    M = getattr(m, "mortiers_adverses", None)
    if not TIR_INDIRECT or not M or m.mode != "combat": return 0
    h = m.h
    serv = [v for v in M["servants"] if h["actif"][v] == 1]
    tubes = min(int(M["tubes"]), len(serv) // SERVANTS_PAR_TUBE)
    if tubes <= 0 or M["obus"] - M["tires"] < 1: return 0
    e0 = m.elts[int(h["elt"][serv[0]])]; x0, y0 = e0.x, e0.y
    cibles = []
    for j, t in enumerate(m.elts):
        if t.side != 0 or not len(_actifs(m, j)) or t.ent < 0: continue
        c = _connaissance(p, e0.camp, t.ent)
        if c is None or c["age_h"] * 60.0 > AGE_MAX_TIR_MIN: continue
        dd = math.hypot(c["x"] - x0, c["y"] - y0)
        if PORTEE_MIN_MORTIER <= dd <= A.ARME["mortier_81"].portee_m: cibles.append((dd, j, c))
    if not cibles: return 0
    dd, j, c = min(cibles, key=lambda x: (x[0], x[1]))
    n = int(math.floor(CADENCE_MORTIER_CPM * dt / 60.0 * tubes + rng.random()))
    n = int(min(n, math.floor(M["obus"] - M["tires"])))
    if n <= 0: return 0
    t = m.elts[j]
    sig = math.sqrt(float(c["sigma_m"]) ** 2 + (CEP_PART_PORTEE * dd / 1.1774) ** 2)
    cz = np.cumsum(P_ZONE_EXPOSE)
    for _ in range(n):
        act = _actifs(m, j)
        if not len(act): break
        ix, iy = float(c["x"]) + rng.normal(0.0, sig), float(c["y"]) + rng.normal(0.0, sig)
        r = np.hypot(t.x + h["dx"][act] - ix, t.y + h["dy"][act] - iy)
        f_eclat = (debout[act] + (1.0 - debout[act]) * F_COUCHE_ECLAT) * (F_DUR_ECLAT if t.couvert == 2 else 1.0)
        pr = P_ECLAT * np.clip(1.0 - (r / RAYON_ECLAT_M) ** 2, 0.0, 1.0) * f_eclat
        for v in act[rng.random(len(act)) < pr].tolist():
            if h["actif"][v] != 1: continue
            z = ZONES[min(4, int(np.searchsorted(cz, rng.random())))]
            _impact(p, m, int(v), z, A.IDX_ARME["mortier_81"])
    M["tires"] += n
    t.feu_recu += n / dt
    return n


def _impact(p, m, v, zone, arme_tireur):
    """Un impact sur l homme v. Arrete par la protection : contusion ( il reste ). Sinon il est hors de combat ; au
    combat, sa blessure attend la fin du bloc ( tri, evacuation ) ; a l exercice, il est neutralise ( simule )."""
    h = m.h
    arme = A.ARMES[arme_tireur].nom if arme_tireur >= 0 else ARME_ADVERSE
    ais, arrete = lesion(zone, arme, int(h["prot"][v]), int(h["casque"][v]))
    if int(h["side"][v]) == 1 and hasattr(m, "lesions_adverses"):     # ( 03/10, HMT-197 4b ) le sort de l adversaire
        m.lesions_adverses.append((int(v), zone, arme, int(ais), bool(arrete)))
    p.compter("impact")
    sd = int(h["side"][v]); m.n_impacts[sd] += 1; m.n_arretes[sd] += int(arrete)
    if arrete:
        if m.mode == "combat" and h["hid"][v] >= 0 and not h["contus"][v]:
            m.pendants.append((int(v), zone, arme, 1))
        h["contus"][v] = 1
        return
    h["actif"][v] = 0
    if h["side"][v] == 1: m.neutr_adv += 1
    if m.mode == "combat" and h["hid"][v] >= 0: m.pendants.append((int(v), zone, arme, ais))


def _rupture(p, m):
    """Le moral et la discipline : une unite qui a perdu plus que son seuil rompt et se replie ; un adversaire qui rompt
    decroche ( son element se retire )."""
    h = m.h
    for side in (0, 1):
        sel = np.nonzero(h["side"] == side)[0]
        if not len(sel): continue
        pertes = 1.0 - h["actif"][sel].mean()
        seuil = RUPTURE_BASE + RUPTURE_PENTE * 0.5 * float(h["moral"][sel].mean() + h["disc"][sel].mean())
        if pertes <= seuil: continue
        if side == 0 and not m.rupture:
            m.rupture = True; p.compter("rupture")
            for e in m.elts:
                if e.side == 0:
                    e.cond = Conduite("repli", "depart", regard="arriere", feu="riposte")
                    e.chemin = [m.depart]; e.arrive = False
        elif side == 1:
            for i, e in enumerate(m.elts):
                if e.side == 1 and len(_actifs(m, i)):
                    h["actif"][_actifs(m, i)] = 0          # l adversaire decroche : hors de l engagement ( pas des pertes )
                    e.chemin = []


def _violation(p, m, hid, motif):
    """Une violation des regles d engagement, une fois par homme et par mission. Au COMBAT, le tribunal militaire
    ( domaine 21 ) ; a l exercice ( tir simule ), une faute notee par l arbitre, sans poursuite."""
    if any(v[1] == m.id and v[2] == hid for v in _dom(p).violations): return
    af = None
    if m.mode == "combat" and hid >= 0:
        af = JU.juger_militaire(p, hid, "militaire", GRAVITE_VIOLATION.get(motif, 0.5), PREUVE_VIOLATION)
    _dom(p).violations.append((p.w.pas, m.id, int(hid), motif, af.id if af is not None else None, m.mode))
    m.violations.append((int(hid), motif))
    p.noter("violation_roe", habitant=int(hid), mission=m.id, motif=motif)


# ------------------------------------------------------------------ les pertes, l evacuation, le grand livre
def _traiter_pertes(p, m):
    """Les blesses du bloc, tries par ISS decroissant ( START : les plus graves d abord, l helicoptere est rare ) :
    un AIS 6 meurt sur le coup ( domaine 16, deceder ) ; un blesse est EVACUE ( domaine 26 ) avant que sa lesion soit
    posee ( sinon le soin civil du moteur le prendrait ), puis son tri d admission est recalcule ( domaine 17 ) ; une
    contusion reste une lesion legere. Les morts de l unite qui ROMPT perdent leur arme et leurs munitions."""
    if not m.pendants: return
    d = _dom(p); w = p.w; h = m.h
    d26 = S._dom(p)
    lst = []
    for v, zone, arme, ais in m.pendants:
        lst.append((-MED.iss_depuis_ais({zone: ais}), v, zone, arme, ais))
    m.pendants = []
    for miss, v, zone, arme, ais in sorted(lst):
        hid = int(h["hid"][v]); iss = -miss
        if not w.table.vivant[hid]: continue
        e = m.elts[int(h["elt"][v])]
        if ais == A.AIS_CONTUSION and iss <= 1:
            A.blesser_soldat(p, hid, zone, arme); d.contusions.append((w.pas, m.id, hid, zone)); p.compter("contusion")
            continue
        if iss >= 75:
            A.blesser_soldat(p, hid, zone, arme)
            d.morts.append((w.pas, m.id, hid, zone)); m.morts.append(hid); p.compter("mort_au_combat")
            continue
        lieu = w.carte.par_n[S._lieu_proche(p, d26, e.x, e.y, m.ile)].id
        ev = S.evacuer(p, hid, lieu=lieu)
        A.blesser_soldat(p, hid, zone, arme)
        if ev is not None and w.table.vivant[hid]:
            ps = ev["passage"]; hab = PO.Habitant(w.table, hid)
            ps.esi = HM.esi(p, hab); ps.iss = HM._iss(p, hab)
            p.compter("evacuation_tactique")
        d.blesses.append((w.pas, m.id, hid, zone, iss, ev["moyen"] if ev else None))
        m.blesses.append(hid); p.compter("blesse_au_combat")
        if not w.table.vivant[hid]: d.morts.append((w.pas, m.id, hid, zone)); m.morts.append(hid); p.compter("mort_au_combat")


def _payer_tirs(p, m):
    """Les coups tires au combat sortent de l armurerie de leur base ( domaine 25, tir_combat ) ; le domaine compte
    ce qu il demande et ce qui sort."""
    if not m.tirs: return
    d = _dom(p)
    for (lid, c), q in sorted(m.tirs.items()):
        bien = A.NOMS_MUNITIONS[c]
        sortis = A.tirer(p, lid, bien, q, "tir_combat")
        d.tirs[(lid, bien)] = d.tirs.get((lid, bien), 0.0) + q
        d.tirs_sortis[(lid, bien)] = d.tirs_sortis.get((lid, bien), 0.0) + sortis
        d.reserve[(lid, c)] = max(0.0, d.reserve.get((lid, c), 0.0) - q)
    m.tirs = {}


def _perdre_materiel(p, m):
    """L unite qui rompt abandonne sur le terrain l arme de ses hommes hors de combat ( morts ou blesses emportes
    sans elle ) : elle sort du Parc ( detruit ), et les munitions qu ils portaient sont perdues ( perte_au_combat )."""
    d = _dom(p); h = m.h
    for v in np.nonzero((h["side"] == 0) & (h["actif"] == 0) & (h["hid"] >= 0))[0].tolist():
        hid = int(h["hid"][v])
        if m.rng.random() >= P_ARME_PERDUE: continue
        rg = int(p.col("habitant", "ar_rang")[hid])
        if rg >= 0:
            oid = int(A._dom(p).eff["arme"][rg])
            if oid >= 0 and oid in p.socle.parc.objets:
                A.perdre_objet(p, oid, "detruit"); d.armes_perdues.append((p.w.pas, m.id, hid, oid)); p.compter("arme_perdue")
        if h["cal"][v] >= 0 and h["coups"][v] > 0:
            lid = p.w.carte.par_n[int(h["base"][v])].id; bien = A.NOMS_MUNITIONS[int(h["cal"][v])]
            porte = float(h["coups"][v])
            q = A.tirer(p, lid, bien, porte, "perte_au_combat")
            d.reserve[(lid, int(h["cal"][v]))] = max(0.0, d.reserve.get((lid, int(h["cal"][v])), 0.0) - porte)
            h["coups"][v] = 0.0
            d.tirs[(lid, bien + ":perte")] = d.tirs.get((lid, bien + ":perte"), 0.0) + porte
            d.tirs_sortis[(lid, bien + ":perte")] = d.tirs_sortis.get((lid, bien + ":perte"), 0.0) + q


# ------------------------------------------------------------------ la cloture et le critere
def _clore(p, m, issue):
    d = _dom(p)
    if m.fini: return
    m.fini = True; m.issue = issue
    _traiter_pertes(p, m); _payer_tirs(p, m)
    if m.mode == "combat" and m.rupture: _perdre_materiel(p, m)
    if m.mode == "combat":
        h = m.h
        bl = h["side"] == 0
        for (lid, c) in sorted({(p.w.carte.par_n[int(b)].id, int(c))
                                for b, c in zip(h["base"][bl].tolist(), h["cal"][bl].tolist()) if c >= 0 and b >= 0}):
            sel = (h["side"] == 0) & (h["cal"] == c)
            d.reserve[(lid, c)] = max(0.0, d.reserve.get((lid, c), 0.0) - float(h["coups"][sel].sum()))
    for e in m.elts:
        if e.side == 0 and e.ent >= 0: S.retirer_entite(p, e.ent)
        if e.side == 1 and e.ent >= 0:
            vivants = len(_actifs(m, m.elts.index(e)))
            if m.mode == "combat":
                if vivants == 0: S.retirer_entite(p, e.ent)
                else: S._dom(p).ent["taille"][e.ent] = vivants      # les pertes de l adversaire ( voir la fiche, point 5 )
    _fatiguer(p, m)
    if not m.voix:                          # l unite rentre au quartier : un ordre, sinon elle se disloque ( 18/09 )
        bx, by, _ = S._position_base(p, m.unite)
        m.ordres.append(S.emettre_ordre(p, _chef_de(p, m.unite), m.unite, "mouvement", a=bx, b=by))
    m.resultat = evaluer(p, m)
    d.en_mission.discard(m.unite)
    if m.id in d.actives: d.actives.remove(m.id)
    if m.resultat["succes"]: p.compter("mission_reussie")
    if m.mode == "combat":
        p.noter("engagement", mission=m.id, tactique=m.tactique.nom, unite=m.unite, issue=issue,
                pertes=len(m.morts) + len(m.blesses), adverses=int(m.neutr_adv))
    else:
        d.exercices += 1; p.compter("exercice")
    d.bilans.append((p.w.pas, m.id, m.tactique.nom, m.mode, issue, m.resultat["succes"], m.resultat["part"]))
    if len(d.missions) > 400:
        for k in sorted(d.missions)[:len(d.missions) - 400]:
            if d.missions[k].fini: del d.missions[k]


def _fatiguer(p, m):
    """Le cout en fatigue : les hommes engages encaissent la fatigue de l activite de la tactique au domaine 25, au
    prorata de la duree sur une journee de 8 heures ( ce que le domaine 25 compte pour une journee d activite )."""
    h = m.h; w = p.w
    ids = h["hid"][(h["side"] == 0) & (h["hid"] >= 0)]
    ids = ids[w.table.vivant[ids] == 1]
    if not len(ids): return
    rg = p.col("habitant", "ar_rang")[ids]; rg = rg[rg >= 0]
    E = A._dom(p).eff
    f = A.FATIGUE[A.ACTIONS.index(m.tactique.activite)] * min(1.0, m.t_s / (8 * 3600.0))
    E["fatigue"][rg] = np.clip(E["fatigue"][rg] + f, 0.0, 1.0)


def evaluer(p, m):
    """Le critere de CETTE mission, mesure par l arbitre ( ici la verite est permise : c est la consequence ). Rend
    { succes, part, pertes, minutes, qui, n_qui, remplis }."""
    cr = m.critere; h = m.h
    bleus = np.nonzero(h["side"] == 0)[0]; rouges = np.nonzero(h["side"] == 1)[0]
    pertes = float(1.0 - h["actif"][bleus].mean()) if len(bleus) else 1.0
    minutes = m.t_s / 60.0
    lim = min(cr.temps_max_min * 60.0, m.fenetre_s if m.fenetre_s is not None else math.inf)
    if cr.qui == "manoeuvre":
        qui = np.array([v for v in bleus.tolist() if m.elts[int(h["elt"][v])].role == "manoeuvre"], np.int64)
    elif cr.qui == "guetteurs":
        qui = np.array([v for v in bleus.tolist() if m.elts[int(h["elt"][v])].role == "guetteurs"], np.int64)
    elif cr.qui == "adversaire": qui = rouges
    else: qui = bleus
    ok = np.zeros(len(qui), bool)
    if cr.mesure == "arrives":
        ok = (h["actif"][qui] == 1) & (h["arrive_s"][qui] >= 0) & (h["arrive_s"][qui] <= lim + 1e-6)
        if m.rupture: ok[:] = False
        part = float(ok.mean()) if len(qui) else 0.0
        succes = part >= cr.seuil
    elif cr.mesure == "neutralises":
        part = float(1.0 - h["actif"][qui].mean()) if len(qui) else 0.0
        part = min(part, m.neutr_adv / max(1, len(qui)))
        succes = part >= cr.seuil and pertes <= cr.pertes_max
    elif cr.mesure == "tenu":
        part = float(h["actif"][qui].mean()) if len(qui) else 0.0
        succes = part >= cr.seuil and not m.rupture and m.issue == "fin"
    elif cr.mesure == "renseigne":
        connu = any(identifiee(_connaissance(p, S.CAMP_NATIONAL, e.ent), RegleEngagement(age_max_min=120.0))
                    for e in m.elts if e.side == 1 and e.ent >= 0)
        part = 1.0 if (connu and not m.detecte_par_adv) else 0.0
        succes = part >= cr.seuil and m.issue == "fin"
    else:
        tot = max(1.0, _longueur([m.depart] + list(m.itineraire)))
        e0 = next((e for e in m.elts if e.side == 0 and e.role == "manoeuvre"), m.elts[0])
        reste = _longueur([(e0.x, e0.y)] + list(e0.chemin)) if e0.chemin else 0.0
        part = float(np.clip(1.0 - reste / tot, 0.0, 1.0))
        succes = part >= cr.seuil and pertes <= cr.pertes_max and not m.rupture
    return {"succes": bool(succes and minutes <= cr.temps_max_min + 1e-6), "part": part, "pertes": pertes,
            "minutes": minutes, "qui": cr.qui, "n_qui": int(len(qui)),
            "remplis": int(ok.sum()) if cr.mesure == "arrives" else None,
            "mesure": cr.mesure, "rupture": m.rupture, "issue": m.issue, "violations": len(m.violations),
            "adverses_neutralises": int(m.neutr_adv),
            "exposition": m.expo_debout / m.expo_marche if m.expo_marche > 0 else None,
            "signature": (("debout" if m.sig_debout * 2 > m.sig_n else "accroupi") if m.sig_n else None)}


def _longueur(pts):
    return math.fsum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


# ================================================================== la formation
def qualification(p, ids, tactique):
    """La part des hommes `ids` qualifies pour la tactique ( livret des qualifications )."""
    d = _dom(p); bit = 1 << IDX_TACTIQUE[tactique]
    if not len(ids): return 0.0
    return float(np.mean([bool(d.qualifs.get(int(h), 0) & bit) for h in np.asarray(ids).tolist()]))


def qualifier(p, ids, tactique, oui=True):
    """Scenario et portes : pose ( ou retire ) la qualification tactique ; dans le monde, elle vient du domaine 19."""
    d = _dom(p); bit = 1 << IDX_TACTIQUE[tactique]
    for h in np.asarray(ids).tolist():
        d.qualifs[int(h)] = (d.qualifs.get(int(h), 0) | bit) if oui else (d.qualifs.get(int(h), 0) & ~bit)


def qualifies(p, hid):
    d = _dom(p); b = d.qualifs.get(int(hid), 0)
    return [t.nom for k, t in enumerate(TACTIQUES) if b & (1 << k)]


def former(p, compagnie, tactique):
    """Inscrit les hommes presents d une compagnie au programme de la tactique ( domaine 19 : instruction, exercice,
    debrief, qualification ). Les jours d exercice, un exercice REEL contre une autre compagnie ( plastron ) donne la
    note de chacun ( `noter_exercice` ). Rend le nombre d inscrits."""
    d = _dom(p); tb = p.w.table
    ids = _aptes(p, compagnie)
    ins = [int(h) for h in ids.tolist() if ED.inscrire_formation(p, PO.Habitant(tb, int(h)), PROGRAMME[tactique]) is not None]
    if ins: d.formations[int(compagnie)] = (tactique, p.jour, ins)
    return len(ins)


def _plastron(p, compagnie):
    """Une autre compagnie de la meme base ( a defaut, de l armee ) sert de plastron : ses hommes presents."""
    U = A._dom(p).unites; b = int(U["base"][compagnie])
    autres = [c for c in A.compagnies(p) if c != compagnie and int(U["base"][c]) == b] or \
             [c for c in A.compagnies(p) if c != compagnie]
    for c in autres:
        ids = _aptes(p, c)
        if len(ids) >= 3: return c, ids
    return -1, np.zeros(0, np.int64)


def _camp(p, role):
    """Les camps d exercice et d adversaire, poses une fois au domaine 26 ( invisibles de la population )."""
    d = _dom(p)
    nom = d.camps.get(role)
    if nom is None:
        nom = {"plastron": "plastron", "adverse": "force_adverse"}[role]
        S.poser_camp(p, nom, None, 30, cote="EAST", visible=False)
        d.camps[role] = nom
    return nom


def situation_exercice(p, tactique, u, rng, rouge=None, taille=None, reperer=False, camp_role=None):
    """La situation d un exercice de `tactique` pour l unite u, a son terrain d exercice ( pres de sa base ) : depart,
    objectif, et l element adverse ( pose au domaine 26 ) avec sa conduite. Rend ( depart, objectif, itineraire,
    adverses, cible, couvert, axe de la menace )."""
    w = p.w
    x0, y0, ile = S.position(p, S.CAMP_NATIONAL, u)
    th = 2.0 * math.pi * rng.random(); L = 500.0 + 400.0 * rng.random()
    ux, uy = math.cos(th), math.sin(th); nx, ny = -uy, ux
    dep = (x0 + L * ux, y0 + L * uy); obj = (x0, y0)
    camp = _camp(p, camp_role or ("plastron" if rouge is not None else "adverse"))
    n_r = int(taille if taille is not None else 2 + int(4 * rng.random()))
    if rouge is not None: n_r = min(n_r, len(rouge))
    f = 0.35 + 0.3 * rng.random(); lat = (rng.random() - 0.5) * 200.0
    rx, ry = dep[0] + f * (obj[0] - dep[0]) + lat * nx, dep[1] + f * (obj[1] - dep[1]) + lat * ny
    iti, couvert, axe, cible = (), "leger", None, -1
    if tactique in ("embuscade",):
        # une patrouille adverse passe par le point d embuscade, venant de l objectif ; on l a reperee ( patrouille )
        px, py = rx + 1500.0 * nx, ry + 1500.0 * ny
        ent = S.poser_entite(p, camp, px, py, ile, "debout", n_r, 1.2)
        chemin = [(rx - 600.0 * nx, ry - 600.0 * ny)]
        cond = Conduite("simultane", "itineraire", regard="marche", feu="riposte")
        amb = (rx - 60.0 * ux, ry - 60.0 * uy)
        adv = [(ent, n_r, cond, chemin, None)]
        # la patrouille a ete reperee : l embuscade connait son axe d arrivee et le regarde ( 27/09 : sans axe, les
        # guetteurs regardaient dans le sens de leur marche et tournaient le dos a la route ; seule la vision
        # peripherique, trop genereuse avant la mesure d Arma, les faisait voir la patrouille passer )
        axe = S.azimut(amb[0], amb[1], px, py)
        return dep, amb, iti, adv, ent, "dur", axe
    if tactique == "defense":
        ent = S.poser_entite(p, camp, dep[0], dep[1], ile, "debout", n_r, 0.0)
        cond = Conduite("bond", "objectif", regard="objectif", feu="libre")
        adv = [(ent, n_r, cond, [obj], None)]
        return obj, obj, iti, adv, -1, "dur", S.azimut(obj[0], obj[1], *dep)
    if tactique == "patrouille":
        iti = (((dep[0] + obj[0]) / 2 + 150 * nx, (dep[1] + obj[1]) / 2 + 150 * ny), dep)
        ent = S.poser_entite(p, camp, rx, ry, ile, "accroupi", n_r, 0.0)
        adv = [(ent, n_r, Conduite("fixe", regard="objectif", feu="libre"), [], S.azimut(rx, ry, *obj))]
        return obj, dep, iti, adv, -1, "leger", axe
    ent = S.poser_entite(p, camp, rx, ry, ile, "accroupi", n_r, 0.0)
    adv = [(ent, n_r, Conduite("fixe", regard="objectif", feu="libre"), [], S.azimut(rx, ry, *dep))]
    if tactique == "reconnaissance":
        return dep, (rx, ry), iti, adv, -1, couvert, axe            # l objectif a reconnaitre est le poste adverse
    if tactique == "appui_mutuel" or reperer:
        # le plastron est repere avant l exercice ( l arbitre le montre : une observation d un guetteur )
        _reperer(p, u, ent, rx, ry, ile)
        cible = ent
    return dep, obj, iti, adv, cible, couvert, axe


def _reperer(p, u, ent, x, y, ile):
    """Un guetteur de l unite, a 150 m de l element adverse et le regardant, l observe ( domaine 26 )."""
    ids = _aptes(p, u)[:1]
    if not len(ids): return
    x0, y0, _ = S.position(p, S.CAMP_NATIONAL, u)
    dd = max(1.0, math.hypot(x - x0, y - y0))
    ox, oy = x - 150.0 * (x - x0) / dd, y - 150.0 * (y - y0) / dd
    S.observer(p, S.CAMP_NATIONAL, ids, np.array([[ox, oy]]), np.array([S.azimut(ox, oy, x, y)]), False,
               portees=np.full(1, 1000.0), cibles=[ent], ile=ile)


def exercice(p, tactique, u, rng, rouge=None, qual=None, taille=None, reperer=False, camp_role=None):
    """Un exercice de `tactique` pour l unite u contre un plastron ( habitants `rouge` ) ou une force adverse posee ;
    tir simule, ordres a la voix. Rend la Mission close."""
    dep, obj, iti, adv, cible, couvert, axe = situation_exercice(p, tactique, u, rng, rouge, taille, reperer, camp_role)
    m = nouvelle_mission(p, tactique, u, dep, obj, adverses=adv, mode="exercice", itineraire=iti, cible=cible,
                         couvert_poste=couvert, seed=(int(rng.integers(0, 2 ** 31)),), exercice_rouge=rouge, axe=axe)
    if qual is not None: m.qual = float(qual)
    executer(p, m)
    for e in adv: S.retirer_entite(p, e[0])
    return m


def _exercices_formation(p):
    """10 h : pour chaque compagnie en formation dont des hommes sont en phase d exercice, un exercice par section
    contre la compagnie plastron ; chaque stagiaire en exercice recoit la note de SA section ( la moitie pour le
    succes du critere, la moitie pour la part des hommes de la section restes aptes )."""
    d = _dom(p)
    if not d.formations: return
    sta = ED._dom(p).stagiaires
    for c in sorted(d.formations):
        tac, j0, ins = d.formations[c]
        en_ex = [h for h in ins if h in sta and sta[h].phase == ED.EXERCICE and sta[h].programme.nom == PROGRAMME[tac]]
        if not en_ex:
            if not any(h in sta for h in ins): del d.formations[c]
            continue
        _, rouge = _plastron(p, c)
        U = A._dom(p).unites
        sections = [g for g in A.unites(p, "section") if int(U["a3"][g]) == c and int(U["type"][g]) == A.INFANTERIE]
        for g in sections:
            ids = set(_aptes(p, g).tolist())
            concernes = [h for h in en_ex if h in ids]
            if not concernes or len(ids) < TACTIQUE[tac].effectif_min: continue
            rng = p.socle.hasard.sous_flux("armee_tactique_formation", p.jour, int(g))
            m = exercice(p, tac, g, rng, rouge if len(rouge) else None, camp_role="plastron")
            r = m.resultat
            h = m.h; bleus = np.nonzero(h["side"] == 0)[0]
            apte = float(h["actif"][bleus].mean()) if len(bleus) else 0.0
            note = float(np.clip(0.5 * float(r["succes"]) + 0.5 * apte, 0.0, 1.0))
            for hid in concernes:
                ED.noter_exercice(p, hid, note); d.notes_formation += 1; p.compter("note_exercice")
                d.notes_par_compagnie[c] = d.notes_par_compagnie.get(c, 0) + 1


def _plan_instruction(p):
    """Le lundi, 9 h 40 : dans chaque brigade sans compagnie en formation ( un centre d instruction, des instructeurs
    et un plastron par brigade : a calibrer ), la compagnie d infanterie la moins qualifiee commence le programme de la
    tactique ou elle l est le moins ( ordre des tactiques : celui de TACTIQUES, variantes d exfiltration exclues )."""
    if p.socle.calendrier.date(p.w.pas).weekday() != 0 or p.jour < 1: return
    d = _dom(p); U = A._dom(p).unites
    for c in sorted(list(d.formations)):
        if not any(h in ED._dom(p).stagiaires for h in d.formations[c][2]): del d.formations[c]
    occupees = {int(U["a1"][c]) for c in d.formations}
    cands = {}
    for c in A.compagnies(p):
        b = int(U["a1"][c])
        if b in occupees or int(U["type"][c]) != A.INFANTERIE: continue
        ids = _aptes(p, c)
        if len(ids) < 6: continue
        scores = [(qualification(p, ids, t.nom), k, t.nom) for k, t in enumerate(TACTIQUES[:7])]
        s, _, tac = min(scores)
        if s >= 0.5: continue
        cands.setdefault(b, []).append((s, c, tac))
    for b in sorted(cands):
        s, c, tac = min(cands[b])
        former(p, c, tac)


def _qualifications_du_jour(p):
    """Le soir : les qualifications delivrees aujourd hui par le domaine 19 ( journal qualification_formation ) aux
    programmes du domaine deviennent des qualifications tactiques."""
    d = _dom(p)
    inverse = {v: k for k, v in PROGRAMME.items()}
    for e in reversed(p.socle.journal.recents):
        if e["jour"] < p.jour: break
        if e["type"] == "qualification_formation" and e["programme"] in inverse:
            qualifier(p, [e["habitant"]], inverse[e["programme"]]); p.compter("qualification_tactique")


# ================================================================== la decision : le choix d exfiltration
ACTIONS = ("direct", "bond", "appui_mouvement", "contournement", "attente")
DIRECT, BOND, APPUI, CONTOURNEMENT, ATTENTE = range(5)
TACTIQUE_DE_L_ACTION = ("exfiltration", "bond", "appui_mutuel", "contournement", "attente")
TRAITS = (("adversaire_connu", "connaissance du camp ( domaine 26 ) : un element adverse connu"),
          ("distance_route", "position crue de l adversaire : sa distance a l itineraire, sur 500 m"),
          ("position_route", "position crue projetee sur l itineraire : 0 au depart, 1 au point de ramassage"),
          ("incertitude", "rayon de la connaissance ( erreur d observation et marche possible depuis ), sur 500 m"),
          ("mobile", "vitesse crue de l adversaire quand on l a vu ( une patrouille marche ), sur 1,5 m/s"),
          ("taille", "taille crue de l adversaire, sur 10"),
          ("nuit", "calendrier : il fait nuit"),
          ("longueur", "carte : longueur de l itineraire, sur 1 500 m"),
          ("fenetre", "ordre d operation : minutes avant la fermeture du point de ramassage, sur 90"),
          ("effectif", "appel du chef de groupe : hommes presents et aptes, sur 10"),
          ("qualification", "livret des qualifications tactiques des hommes presents ( bond et appui mutuel )"),
          ("fatigue", "rapport du chef ( domaine 25 ) : fatigue moyenne"))
T_CONNU, T_DIST, T_POS, T_INC, T_MOB, T_TAILLE, T_NUIT, T_LONG, T_FEN, T_EFF, T_QUAL, T_FAT = range(len(TRAITS))


class ContexteExfiltration:
    __slots__ = ("traits",)

    def __init__(self, traits): self.traits = traits


def _observer(ctx): return ctx.traits


def _regle(x, ctx):
    """Ce que dit la doctrine : sans rien savoir, droit la nuit ( un homme accroupi n y est vu qu a ~ 126 m ), par bonds le jour ; une
    patrouille qui passe, on l attend si la fenetre le permet ; loin de l itineraire, droit ; connu avec precision, de
    jour, a six au moins : l appui et le mouvement ; sinon le contournement si le temps le permet ; sinon le bond."""
    if x[T_CONNU] < 0.5: return DIRECT if x[T_NUIT] >= 0.5 else BOND
    if x[T_MOB] >= 0.5 and x[T_FEN] * 90.0 >= 45.0: return ATTENTE
    if x[T_DIST] * 500.0 > 350.0: return DIRECT
    if x[T_NUIT] < 0.5 and x[T_EFF] >= 0.6 and x[T_INC] * 500.0 < 150.0: return APPUI
    if x[T_FEN] * 90.0 >= 45.0: return CONTOURNEMENT
    return BOND


def _temoin(x, ctx, rng): return BOND


POINT = D.PointDeDecision(
    "exfiltration", DOMAINE, TRAITS, ACTIONS, _observer, _regle, _temoin,
    "pour CETTE mission : part des hommes engages arrives au point de ramassage avant sa fermeture ( l appui compte ), "
    "moins 0,15 par heure de mission ( le temps a un prix )", HORIZON)


def traits_exfiltration(p, u, ids, depart, objectif, cible, fenetre_min):
    """Ce que voit le chef de groupe ( jamais la verite du domaine 26 ) : la connaissance de son camp sur `cible`."""
    x0, y0 = depart; x1, y1 = objectif
    L = max(1.0, math.hypot(x1 - x0, y1 - y0)); ux, uy = (x1 - x0) / L, (y1 - y0) / L
    c = _connaissance(p, S.CAMP_NATIONAL, cible)
    comp = A.competences(p, ids) if len(ids) else {"fatigue": np.zeros(1)}
    q = 0.5 * (qualification(p, ids, "bond") + qualification(p, ids, "appui_mutuel"))
    base = [0.0, 1.0, 0.5, 1.0, 0.0, 0.0]
    if c is not None:
        rx, ry = c["x"] - x0, c["y"] - y0
        proj = rx * ux + ry * uy; lat = abs(rx * uy - ry * ux)
        base = [1.0, min(1.0, lat / 500.0), float(np.clip(proj / L, 0.0, 1.0)),
                min(1.0, (c["sigma_m"] + min(c["rayon_m"], 500.0)) / 500.0), min(1.0, _vitesse_crue(p, cible) / 1.5),
                min(1.0, c["taille"] / 10.0)]
    return base + [float(p.w.nuit()), min(1.0, L / 1500.0), min(1.0, fenetre_min / 90.0), min(1.0, len(ids) / 10.0),
                   float(q), float(np.clip(comp["fatigue"].mean(), 0.0, 1.0))]


def _vitesse_crue(p, cible, camp=S.CAMP_NATIONAL):
    """La vitesse que le camp a notee a l observation ( une patrouille marche ; domaine 26 ), 0 sans connaissance."""
    d26 = S._dom(p); r = d26.conn_idx.get((S._camp(d26, camp), int(cible)))
    return float(d26.conn["vitesse"][r]) if r is not None else 0.0


def note_exfiltration(m):
    r = m.resultat
    return float(r["part"]) - PRIX_HEURE * r["minutes"] / 60.0


# ================================================================== le scenario de la decision
SLOTS = (8.0, 12.0, 16.0, 22.0)


def _exercices_scenario(p):
    """Le scenario d exercices ( porte de decision ) : a chaque creneau, chaque groupe d infanterie de 5 hommes aptes
    au moins fait une exfiltration contre la force adverse posee - poste ou patrouille, taille, place et regard tires ;
    un guetteur du groupe observe d abord depuis un point d observation ( domaine 26, jumelles de jour ) ; le chef
    decide ( point exfiltration ) ; la tactique choisie est executee, en exercice ( tir simule ), a la voix ; la note est
    celle de CETTE mission. Une tactique dont les preconditions manquent ( l appui sans adversaire connu ou de nuit )
    retombe sur le bond."""
    d = _dom(p)
    if d.scenario is None: return
    slot = min(range(len(SLOTS)), key=lambda k: abs(SLOTS[k] - p.w.heure))
    camp = _camp(p, "adverse")
    U = A._dom(p).unites
    for g in A.unites(p, "groupe"):
        if int(U["type"][g]) != A.INFANTERIE or g in d.en_mission: continue
        ids = _aptes(p, g)
        if len(ids) < 5: continue
        rng = p.socle.hasard.sous_flux("armee_tactique_scenario", p.jour, slot, int(g))
        x0, y0, ile = S.position(p, S.CAMP_NATIONAL, g)
        th = 2.0 * math.pi * rng.random(); L = 500.0 + 600.0 * rng.random()
        ux, uy = math.cos(th), math.sin(th); nx, ny = -uy, ux
        dep = (x0 + L * ux, y0 + L * uy); obj = (x0, y0)
        f = 0.25 + 0.5 * rng.random(); lat = (rng.random() - 0.5) * 500.0
        rx, ry = dep[0] + f * (obj[0] - dep[0]) + lat * nx, dep[1] + f * (obj[1] - dep[1]) + lat * ny
        n_r = 2 + int(5 * rng.random())
        fen = 20.0 + 55.0 * rng.random()
        if rng.random() < 0.35:
            s = 1.0 if rng.random() < 0.5 else -1.0
            ex, ey = rx - s * (250.0 + 350.0 * rng.random()) * nx, ry - s * (250.0 + 350.0 * rng.random()) * ny
            ent = S.poser_entite(p, camp, ex, ey, ile, "debout", n_r, 1.2)
            adv = [(ent, n_r, Conduite("simultane", "itineraire", regard="marche", feu="libre"),
                    [(rx + s * 2500.0 * nx, ry + s * 2500.0 * ny)], None)]
        else:
            ent = S.poser_entite(p, camp, rx, ry, ile, "accroupi", n_r, 0.0)
            reg = None if rng.random() < 0.3 else S.azimut(rx, ry, *dep) + (rng.random() - 0.5) * math.pi / 2.0
            adv = [(ent, n_r, Conduite("fixe", regard="objectif", feu="libre"), [], reg)]
        # la reconnaissance avant la decision : un guetteur au point d observation, 250 m vers l objectif
        ox, oy = dep[0] - 250.0 * ux, dep[1] - 250.0 * uy
        nuit = p.w.nuit()
        port = A.perception(p, ids[:2], nuit)[1] * (1.0 if nuit else F_JUMELLES)
        S.observer(p, S.CAMP_NATIONAL, ids[:2], np.tile([ox, oy], (2, 1)), np.full(2, S.azimut(ox, oy, *obj)), nuit,
                   portees=port, cibles=[ent], ile=ile)
        x = traits_exfiltration(p, g, ids, dep, obj, ent, fen)
        a = d.decideur.decider(("ex", p.jour, slot, int(g)), ContexteExfiltration(x))
        p.compter("decision_exfiltration")
        tac = TACTIQUE_DE_L_ACTION[a]
        if verifier(p, tac, g, ent):
            tac = "bond"; p.compter("repli_impossible")
        m = nouvelle_mission(p, tac, g, dep, obj, adverses=adv, mode="exercice", critere=CRITERE_EXFIL, cible=ent,
                             fenetre_min=fen, seed=(p.jour, slot, int(g)))
        executer(p, m)
        S.retirer_entite(p, ent)
        cle = ("ex", p.jour, slot, int(g))
        d.decideur.noter(cle, note_exfiltration(m), p.jour)
        d.decideur.attentes.pop(cle, None)
        d.serie.append((p.jour, slot, int(g), ACTIONS[a], tac, round(note_exfiltration(m), 3), m.resultat["succes"]))
        if len(d.serie) > 5000: del d.serie[0]


def scenario_exercices(jours=6, graine=11, echelle=5, mode="hasard"):
    """La porte de decision : un pays de `echelle` x 500 habitants, une force adverse posee, et 4 exfiltrations par
    jour et par groupe d infanterie ( `_exercices_scenario` ). Rend ( w, p )."""
    from . import essais as T
    w, p = T.monde([DOMAINE], graine, echelle, modes={POINT.nom: mode})
    _dom(p).scenario = {"slots": SLOTS}
    T.jours(w, jours)
    return w, p


# ================================================================== les routines
def _soir(p):
    """22 h 50 : les qualifications du jour ; la serie."""
    _qualifications_du_jour(p)


MOTIFS = (("carburant_tactique", "achat"),)
LIEUX_HABITES = ("village", "ville", "capitale")


def installer(p):
    d = Tactiques()
    p.domaines[DOMAINE] = d
    L = p.socle.livre
    for m, nature in MOTIFS: L.declarer_motif(m, nature, DOMAINE)
    J = p.socle.journal
    J.declarer("engagement", DOMAINE, "individuel", ("mission", "tactique", "unite", "issue", "pertes", "adverses"))
    J.declarer("violation_roe", DOMAINE, "individuel", ("habitant", "mission", "motif"))
    J.declarer("tactique_refusee", DOMAINE, "individuel", ("unite", "tactique", "raisons"))
    for t in ("mission_lancee", "mission_reussie", "exercice", "coups_tires", "coups_simules", "impact", "contusion",
              "blesse_au_combat", "mort_au_combat", "evacuation_tactique", "arme_perdue", "ordre_tactique", "ordre_reemis",
              "rupture", "decision_exfiltration", "qualification_tactique", "note_exercice", "repli_impossible"):
        J.declarer(t, DOMAINE, "compte")
    for t in TACTIQUES:
        ED.declarer_programme(p, PROGRAMME[t.nom], DOMAINE, *t.formation, 2, GAIN_FORMATION, "formation",
                              SEUIL_FORMATION, public="api")
    w = p.w
    hab = [l for l in w.carte.par_n if l.type in LIEUX_HABITES]
    d.habites = np.array([(l.pos[0], l.pos[1], w.carte.iles.index(l.ile)) for l in hab], np.float64).reshape(-1, 3)
    d.decideur = p.decideur(POINT)
    p.echeance("armee_tactique_pas", _pas_mission)
    p.routine(9 + 40 / 60, 80, DOMAINE, _plan_instruction)
    p.routine(10.0, 80, DOMAINE, _exercices_formation)
    for h in SLOTS: p.routine(h + 20 / 60, 80, DOMAINE, _exercices_scenario)
    p.routine(22 + 50 / 60, 80, DOMAINE, _soir)
    return d


# ================================================================== les controles
def anomalies(p):
    """Les incoherences du domaine : [ ( type, detail ) ].
      tir_sans_munition        des coups demandes par le combat qui ne sont pas sortis du grand livre
      mort_sans_deceder        un militaire engage mort sans date de deces ( d01.deceder )
      mort_hors_combat         un mort du combat dont la cause n est pas combat
      blesse_sans_evacuation   un blesse ( hors contusion et mort sur le coup ) sans evacuation
      violation_sans_affaire   une violation des regles d engagement sans affaire au tribunal militaire
      marche_sans_destination  une suite d ordres Arma qui ne pose pas la destination d abord"""
    d = _dom(p); out = []
    for k in sorted(set(d.tirs) | set(d.tirs_sortis)):
        if abs(d.tirs.get(k, 0.0) - d.tirs_sortis.get(k, 0.0)) > 1e-6: out.append(("tir_sans_munition", k))
    tb = p.w.table; dj = p.col("habitant", "deces_j"); cause = p.col("habitant", "cause_deces")
    combat = _cause_combat()
    for h in sorted(d.engages):
        if not tb.vivant[h] and dj[h] < 0: out.append(("mort_sans_deceder", h))
    for _, _, h, _ in d.morts:
        if dj[h] >= 0 and cause[h] != combat: out.append(("mort_hors_combat", h))
    for pas, mid, h, zone, iss, ev in d.blesses:
        if ev is None: out.append(("blesse_sans_evacuation", h))
    for v in d.violations:
        if v[5] == "combat" and v[2] >= 0 and v[4] is None: out.append(("violation_sans_affaire", v[2]))
    for _, _, _, seq in d.ordres_arma:
        for a, b in zip(seq, seq[1:]):
            if b[0] == "moveTo" and a[0] != "setDestination": out.append(("marche_sans_destination", b))
        if seq and seq[0][0] == "moveTo": out.append(("marche_sans_destination", seq[0]))
    return out


def _cause_combat():
    from . import d01_population as POP
    return POP.CAUSES.index("combat")


# ================================================================== ce que le domaine donne ( pont Arma, autres domaines )
def mission(p, mid):
    m = _dom(p).missions.get(mid)
    if m is None: return None
    return {"id": m.id, "tactique": m.tactique.nom, "unite": m.unite, "mode": m.mode,
            "phase": m.tactique.phases[min(m.k, len(m.tactique.phases) - 1)].nom,
            "minutes": m.t_s / 60.0, "fini": m.fini, "issue": m.issue, "resultat": m.resultat, "ordres": list(m.ordres),
            "violations": list(m.violations), "morts": list(m.morts), "blesses": list(m.blesses)}


UNITPOS = {"debout": "UP", "accroupi": "MIDDLE", "couche": "DOWN"}


def a_incarner(p):
    """Le pont : pour chaque mission active, chaque homme a SA place ( jamais deux au meme point ), sa posture
    ( setUnitPos ), son classname ; les ordres de l element dans l ordre paye ( setDestination avant moveTo ; doStop
    pour une attente ordonnee ; setDir avant doWatch ) ; l adversaire ( entites du domaine 26 )."""
    d = _dom(p); out = []
    for mid in list(d.actives):
        m = d.missions[mid]; h = m.h; pts = m.pts
        hommes, ordres = [], []
        for i, e in enumerate(m.elts):
            sel = np.nonzero(h["elt"] == i)[0]
            if e.side == 0:
                az = _regard(m, e, pts)
                pos = "DOWN" if e.cond is None or e.cond.mode == "fixe" else \
                    ("MIDDLE" if e.cond.mode == "infiltration" else "UP")
                for v in sel.tolist():
                    hid = int(h["hid"][v])
                    hommes.append({"habitant": hid, "classname": A.classname(p, hid), "x": e.x + float(h["dx"][v]),
                                   "y": e.y + float(h["dy"][v]), "setUnitPos": pos, "actif": bool(h["actif"][v]),
                                   "role": e.role})
                seq = []
                for q in e.chemin: seq += [("setDestination", e.role, q), ("moveTo", e.role, q)]
                if e.cond is not None and e.cond.mode == "fixe": seq.append(("doStop", e.role, None))
                if az is not None:
                    tx, ty = e.x + 100.0 * math.cos(az), e.y + 100.0 * math.sin(az)
                    seq += [("setDir", e.role, math.degrees(math.pi / 2 - az) % 360.0), ("doWatch", e.role, (tx, ty))]
                ordres.append({"role": e.role, "ordres": seq})
        out.append({"mission": mid, "tactique": m.tactique.nom, "phase": m.tactique.phases[m.k].nom, "unite": m.unite,
                    "hommes": hommes, "ordres": ordres,
                    "adversaires": [e.ent for e in m.elts if e.side == 1], "arma_preuve": None})
    return out


def bilan(p):
    """{ missions, reussies, exercices, coups tires, blesses, morts, contusions, violations, armes perdues,
    qualifies par tactique }."""
    d = _dom(p)
    par_t = {t.nom: 0 for t in TACTIQUES}
    for b in d.qualifs.values():
        for k, t in enumerate(TACTIQUES):
            if b & (1 << k): par_t[t.nom] += 1
    return {"bilans": len(d.bilans), "reussies": sum(1 for b in d.bilans if b[5]), "exercices": d.exercices,
            "coups_tires": math.fsum(v for k, v in d.tirs.items() if not k[1].endswith(":perte")),
            "blesses": len(d.blesses), "morts": len(d.morts), "contusions": len(d.contusions),
            "morts_des_suites": sum(1 for b in d.blesses if not p.w.table.vivant[b[2]]),
            "violations": len(d.violations), "armes_perdues": len(d.armes_perdues), "qualifies": par_t,
            "notes_formation": d.notes_formation, "refus": len(d.refus)}
