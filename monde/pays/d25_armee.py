"""DOMAINE 25 - ARMEE ( A ) : ORGANISATION, SOLDAT, EQUIPEMENT, ARMES, OPTIQUES, MUNITIONS, VEHICULES MILITAIRES.

FICHE
1. Classes. Les lois, chacune avec sa source ou « a calibrer » : CaracArme ( calibre, portee efficace, precision,
   cadence, vitesse et energie a la bouche, recul, masse, coups moyens entre incidents, vie en coups ), CaracOptique
   ( grossissement, portee utile ), CaracProtection ( niveau NIJ, zone, masse, multiplicateur de letalite par menace ),
   CaracRadio ( portee, masse, autonomie ), CaracVehicule ( blindage STANAG 4569, equipage, places, reservoir,
   autonomie donc consommation, vitesse, pannes, entretien, pieces ), et les munitions par calibre, declarees comme
   BIENS du catalogue ( famille munition ). Les detenteurs : Armurerie ( une par base : le Stock du socle des
   munitions et des pieces ; proprietaire de toutes les armes, optiques, protections, radios et vehicules de sa
   base ). L etat, en STRUCTURES DE TABLEAUX ( numpy aujourd hui, Vec<T> en Rust demain ) : Table ( les champs d une
   famille de lignes ), l organisation ( UNITES : niveau, type, parent, base, chef, et l ancetre a chaque niveau ), les
   EFFECTIFS ( une ligne par militaire : unite, grade, specialite, statut, conscrit, competences tir, perception,
   endurance, discipline, etat fatigue, stress, moral, dotation ), les VEHICULES ( modele, base, unite, compteurs,
   etat ), les ARMES COLLECTIVES ( mortiers ). ContexteCompagnie ( ce qu un commandant voit ), Armee ( l etat du
   domaine ), RemplacePatrouilles et RemplaceRavitaillement ( les methodes du moteur dont le domaine est proprietaire ).
   Par habitant, en COLONNES : ar_rang ( sa ligne aux effectifs, -1 civil ) et ar_appel ( conscription : -1 pas encore
   vu, -2 exempte, -3 appele ou servi, >= 0 le jour de son appel ). 8 octets par habitant ; le reste ne concerne que
   les militaires ( 1 a 9 % des habitants ) et vit dans les tables du domaine.
   ORGANISATION ( doctrine de l armee de terre grecque, ordres de grandeur OTAN ) : armee > brigade ( une par ile ) >
   bataillon ( un par base, jusqu a 4 compagnies ) > compagnie ( jusqu a 4 sections : 3 de combat et une d appui aux
   mortiers ) > section ( 3 groupes ) > groupe ( 8 a 10 hommes ) > binome ( deux voisins de rang dans le groupe ). Un
   peloton de chars est une section de 4 equipages de 4 ; les recrues forment la compagnie d instruction de leur base.
   Grades ( armee grecque ) : soldat ( stratiotis ), caporal ( dekaneas ), sergent ( lochias ), adjudant
   ( anthypaspistis ), sous-lieutenant ( anthypolochagos ), lieutenant ( ypolochagos ), capitaine ( lochagos ),
   commandant ( tagmatarchis ), lieutenant-colonel ( antisyntagmatarchis ), colonel ( syntagmatarchis ), general de
   brigade ( taxiarchos ). Chaine de commandement : le chef de chaque unite ( un officier quand il y en a, les
   compagnies d abord, puis les bataillons, puis les sections ; sinon le sous-officier le plus ancien de l unite ).
2. Invariants et ce que le domaine detient. BIENS : les munitions et les pieces de ses armureries ( famille
   `armureries` du registre, sans argent ) ; ils n entrent que par la dotation du jour de l installation ( importee
   sans paiement, comme les stocks de depart du moteur ), par import ( domaine 7, motif import_armement, paye par
   l Etat ) ou par livraison de l industrie ( pieces, domaine 10 ) ; ils ne sortent que CONSOMMES sous un motif du
   domaine ( tir_instruction, tir_combat, entretien_militaire ) ou perdus/detruits par le domaine 27 ; chaque sortie est
   comptee par le domaine, et stock des armureries = stock de depart + entrees - sorties comptees ( `anomalies` : une
   munition tiree hors consommation se voit ). OBJETS : armes, optiques, protections, radios, vehicules militaires au
   Parc du socle ( sources initial, importe ; puits detruit, rebut ), tous a une armurerie ; une arme ou une optique
   individuelle ( numero de serie ) est dotee a un seul militaire ; les protections et radios sont des cohortes de
   l armurerie, et les dotations d une base n en depassent jamais le nombre ( `anomalies` : une arme sans
   proprietaire se voit ). EFFECTIFS : chaque militaire actif ( metier soldat ou officier, en emploi, travaillant a une
   base ) a une ligne et une unite ; chaque unite compte ses membres directs et ceux de ses unites filles ; toute
   competence et tout etat sont dans [ 0 ; 1 ]. ARGENT : aucun. La solde est la paie du domaine 4 ( grille publique,
   l Etat paie ; le domaine se declare employeur de ses bases pour tenir ses effectifs vises ) ; munitions, pieces,
   vehicules et carburant des convois sont payes par l Etat par le grand livre ( domaines 7, 10, moteur ).
3. Decision `activite_compagnie` ( chaque commandant de compagnie, chaque matin a 6 h 30 ) : instruction_tir,
   marche, repos, maintenance, patrouille. Traits ( ce que le capitaine sait de SA compagnie : registre de tir, tests
   physiques, rapports des chefs de section, carnet d entretien, releves du depot et de l armurerie, journal de la
   base ) : tir moyen, endurance moyenne, perception moyenne, fatigue moyenne, stress moyen, moral moyen, part des
   vehicules en service, part des vehicules en retard d entretien, carburant de la garnison en jours de patrouille,
   munitions d instruction en jours de tir, patrouilles tenues hier a sa base. Effets du jour ( 16 h ) : le tir monte
   au champ de tir ( et brule des munitions ), l endurance a la marche, la perception en patrouille ; le repos fait
   tomber fatigue et stress ; la maintenance repare les vehicules en panne et remet a zero leurs compteurs d entretien
   ( elle brule des pieces ) ; la patrouille tient les patrouilles de 8 h et 20 h de sa base ( carburant de la
   garnison, un vehicule en service ). Note ( horizon 3 jours : une journee de tir se lit dans les jours qui suivent,
   la fatigue se recupere en deux ou trois nuits ) : chaque soir, pour CETTE compagnie, 0,30 x patrouilles tenues par
   elle sur 2 + 0,25 x aptitude au combat ( moyenne du tir, de l endurance et de la perception ) + 0,15 x ( 1 -
   fatigue ) + 0,15 x part des vehicules en service + 0,15 x moral. Regle ( la garde d abord ) : fatigue > 0,55 ->
   repos ; retard d entretien sur la moitie du parc ou moins de 75 % en service -> maintenance ; tir < 0,45 et des
   munitions -> instruction de tir ; endurance < 0,45 -> marche ; sinon patrouille. Temoin : toujours l instruction
   de tir.
4. Evenements. Individuels : incorporation, liberation_service. Comptes : decision_activite, tir_instruction, tir_combat,
   import_munitions, panne_militaire, reparation_militaire, maintenance_militaire, appel_differe, exemption_service,
   arme_manquante. Le moteur note toujours patrouille et patrouille_annulee ( avec leur cause ).
5. Liens. Travail ( 4 ) : `embaucher_contrat` ( les conscrits, en CDD de service ), `rompre_contrat` ( la liberation ),
   `fixer_taux`, `qualifier`, `declarer_employeur` et `ouvrir_postes` ( les effectifs vises des bases ), les colonnes
   tr_statut, tr_qualifs, tr_carriere_j. Education ( 19 ) : `declarer_programme` ( classe_recrues : instruction,
   exercice, debrief, qualification formation_militaire ), `inscrire_formation` ; `competences` ( technique ).
   Industrie ( 10 ) : `livrer` des pieces. Transport ( 14 ) : `emplacements` ( jamais deux vehicules au meme point ),
   le carburant en unites de 10 litres ( domaine 11 ). Exterieur ( 7 ) : `importer_au_port` ( munitions, pieces ) et
   `declarer_import` ( vehicules, armes ). Immobilier ( 13 ) : `batiments( p, "caserne" )`, `lits` ( la capacite
   d incorporation ). Population ( 1 ) : sexe, naissance ; ages. Optionnels : culture ( 23, le moral ), medecine
   ( 16, `blesser_soldat` ), roles.decider_armee ( le groupe d agents armee, s il est installe ). Remplace
   Monde.patrouilles et Monde.ravitailler_bases ( proprietaire ) : memes compteurs ( patrouilles_jour,
   patrouilles_faites, patrouilles_annulees ), memes notes du moteur, meme convoi du depot ; la patrouille part avec un
   vehicule reel et brule ce qu il consomme. API en fin de fichier pour les domaines 26 et 27.
6. Portes : tests_d25_armee.py.
7. Arma. Classnames du jeu de base, d Apex, de Contact ou de CUP, `arma_preuve = None` pour tous : personne ne les a
   vus vivre en jeu. Soldats par specialite ( B_Soldier_F, B_Soldier_SL_F, B_soldier_AR_F... ), armes ( G3A3, M4A1,
   HK416, MG3, Glock 17, Carl Gustaf de CUP ; mortier Mk6 ), optiques, gilets, radios, vehicules ( Leopard 2A6,
   M113, HMMWV M1114 de CUP ; HEMTT ). Lecons payees : la portee d un tireur est le MINIMUM de son arme et de son
   optique ( un ACO plafonne a 400 m, 13/09 ) ; `knowsAbout` est une connaissance de CAMP ( la detection d une unite
   est celle du meilleur de ses membres ) ; une destination posee AVANT l ordre de marche ( `ordre_de_mouvement` ) ;
   des emplacements distincts pour chaque vehicule ( `positions_du_parc` ).
8. Cout. Le matin : une passe vectorisee sur les effectifs ( morts, departs ), une sur les habitants pour les
   arrivees et la conscription ( colonnes ), un point de decision par compagnie. 8 h et 20 h : une boucle sur les bases.
   16 h : des vecteurs sur les effectifs, une boucle sur les compagnies et leurs vehicules, l usure des armes des
   tireurs du jour. Soir : des vecteurs, une note par compagnie. Installation lineaire : tris et comptes par base.
   Mesure : tests_d25_armee.test_cout."""
import math
import numpy as np
from .. import config as C, population as PO, roles as R
from ..socle import decision as D, biens as B, objets as O
from . import pays as P, d01_population as POP, d04_travail as TR, d07_exterieur as EXT, d10_industrie as IND
from . import d11_energie as ENE, d13_immobilier as IM, d14_transport as TP, d19_education as ED

DOMAINE = "armee"
EUROS = P.EUROS_PAR_DRACHME
JOURS_AN = 365.0
LITRES_UNITE = ENE.LITRES_UNITE          # une unite de carburant du moteur = 10 litres de gazole ( domaine 11 )
EPS = 1e-9


def _dr(euros): return euros / EUROS


# ================================================================== les armes
class CaracArme:
    """Un modele d arme. portee_m : portee efficace sur une cible de la taille d un homme ( point target ), ce que dit
    le constructeur ou le manuel ; precision_moa : dispersion ( minutes d angle ) ; cadence_cpm : coups par minute
    ( cadence pratique pour une arme semi-automatique ) ; v0_ms et energie_j : a la bouche ( 0 pour une charge creuse ou
    un obus : l effet n est pas cinetique ) ; recul_j : energie de recul libre ; mrbs : coups moyens entre incidents de
    tir ; vie_coups : ce que tire l arme avant d etre usee ( le Parc compte 1 heure pour 100 coups )."""
    __slots__ = ("nom", "calibre", "portee_m", "precision_moa", "cadence_cpm", "v0_ms", "energie_j", "recul_j",
                 "masse_kg", "mrbs", "vie_coups", "prix_eur", "menace", "arma", "source")

    def __init__(self, nom, calibre, portee_m, precision_moa, cadence_cpm, v0_ms, energie_j, recul_j, masse_kg, mrbs,
                 vie_coups, prix_eur, menace, arma, source):
        if not (portee_m > 0 and precision_moa >= 0 and cadence_cpm > 0 and masse_kg > 0 and mrbs > 0 and vie_coups > 0
                and prix_eur > 0 and energie_j >= 0 and recul_j >= 0):
            raise ValueError(f"arme {nom} : grandeur hors bornes")
        if menace not in MENACES: raise ValueError(f"arme {nom} : menace inconnue {menace!r}")
        self.nom, self.calibre, self.portee_m, self.precision_moa = nom, calibre, float(portee_m), float(precision_moa)
        self.cadence_cpm, self.v0_ms, self.energie_j, self.recul_j = float(cadence_cpm), float(v0_ms), float(energie_j), float(recul_j)
        self.masse_kg, self.mrbs, self.vie_coups, self.prix_eur = float(masse_kg), float(mrbs), float(vie_coups), float(prix_eur)
        self.menace, self.arma, self.source = menace, arma, source


MENACES = ("pistolet", "fusil", "perforant", "eclat")
ARMES = (
    CaracArme("g3a3", "mun_762", 400, 3.0, 550, 800, 3100, 14.0, 4.4, 1500, 20000, 1000, "fusil", "CUP_arifle_G3A3_ris",
              "Heckler & Koch G3A3, fabrique sous licence par EBO ( Grece ) : hausse reglee de 100 a 400 m, 500-600 coups "
              "par minute, 4,4 kg sans chargeur ; 7,62 x 51 M80 ( 9,5 g a ~ 810 m/s : ~ 3 100 J ) ; recul libre ~ 14 J, "
              "incidents, vie et prix a calibrer"),
    CaracArme("m4a1", "mun_556", 500, 4.0, 800, 880, 1700, 5.5, 3.0, 3600, 20000, 1000, "fusil", "CUP_arifle_M4A1",
              "Colt M4A1 : portee efficace 500 m sur cible ponctuelle ( US Army FM 3-22.9 ), 700-950 coups par minute, "
              "4 MOA ( specification ), 3,0 kg ; M855 ( 4 g a ~ 910 m/s : ~ 1 700 J ) ; 3 600 coups entre incidents "
              "( exigence de l US Army, a verifier ) ; prix a calibrer"),
    CaracArme("hk416", "mun_556", 500, 2.0, 850, 880, 1750, 5.5, 3.5, 5000, 20000, 2500, "fusil", "CUP_arifle_HK416_Black",
              "Heckler & Koch HK416 D14.5RS : 3,5 kg, ~ 850 coups par minute, portee efficace ~ 500 m ; precision, "
              "fiabilite et prix a calibrer"),
    CaracArme("mg3", "mun_762", 800, 6.0, 1100, 820, 3200, 16.0, 11.5, 5000, 50000, 6000, "fusil", "CUP_lmg_MG3",
              "Rheinmetall MG3 : 1 000-1 300 coups par minute, 11,5 kg, portee efficace 800 m sur bipied ( 1 200 m sur "
              "affut ) ; canon change tous les ~ 150 coups en tir soutenu ; vie, fiabilite et prix a calibrer"),
    CaracArme("glock17", "mun_9mm", 50, 4.0, 60, 375, 520, 3.0, 0.7, 5000, 40000, 500, "pistolet", "CUP_hgun_Glock17",
              "Glock 17 : 9 x 19 ( 8 g a ~ 360 m/s : ~ 520 J ), portee efficace 50 m, 0,7 kg charge, cadence pratique "
              "~ 60 coups par minute ; fiabilite et prix a calibrer"),
    CaracArme("carl_gustaf_m3", "roquette_84", 700, 3.4, 6, 255, 0, 0.0, 10.0, 1000, 1000, 20000, "eclat",
              "CUP_launch_MAAWS",
              "Saab Carl Gustaf M3 84 mm : 700 m sur cible fixe, 400 m mobile ( charge creuse FFV551 ), 10 kg, sans "
              "recul, 4 a 6 coups par minute, vie du tube 1 000 coups ( Saab ) ; prix a calibrer"),
    CaracArme("mortier_81", "obus_81", 5650, 0.0, 15, 250, 0, 0.0, 42.0, 2000, 10000, 30000, "eclat", "B_Mortar_01_F",
              "mortier de 81 mm ( type L16 / M252 ) : portee maximale 5 650 m, 15 coups par minute soutenus, 42 kg, "
              "trois servants ; tir indirect ( la portee n est pas celle d un tireur ) ; vie et prix a calibrer"),
)
ARME = {a.nom: a for a in ARMES}
IDX_ARME = {a.nom: k for k, a in enumerate(ARMES)}
COLLECTIVES = ("mortier_81",)                     # armes d une unite, pas d un homme
MORTIERS_PAR_SECTION_APPUI = 2
SERVANTS_MORTIER = 3


# ================================================================== les optiques
class CaracOptique:
    """Un organe de visee. portee_m : la distance au-dela de laquelle un tireur ne touche plus une cible humaine une
    fois sur deux avec cette optique, QUEL QUE SOIT son fusil. La portee utile d un tireur est le minimum de celle de
    son arme et de celle de son optique ( lecon payee dans Arma le 13/09 : MX + ACO, p >= 0,5 jusqu a 400 m seulement,
    alors que le fusil porte plus loin )."""
    __slots__ = ("nom", "grossissement", "portee_m", "masse_kg", "prix_eur", "arma", "source")

    def __init__(self, nom, grossissement, portee_m, masse_kg, prix_eur, arma, source):
        if not (grossissement >= 1 and portee_m > 0 and masse_kg >= 0 and prix_eur >= 0):
            raise ValueError(f"optique {nom} : grandeur hors bornes")
        self.nom, self.grossissement, self.portee_m, self.masse_kg = nom, float(grossissement), float(portee_m), float(masse_kg)
        self.prix_eur, self.arma, self.source = float(prix_eur), arma, source


OPTIQUES = (
    CaracOptique("fer", 1, 300, 0.0, 0.0, None,
                 "organes de visee metalliques : l instruction de tir de l US Army qualifie a 300 m ( FM 3-22.9 ) ; au-dela "
                 "une silhouette cache sous la guidon ( a calibrer ) ; pas d objet : c est le fusil nu"),
    CaracOptique("point_rouge", 1, 300, 0.34, 700, "CUP_optic_CompM4",
                 "Aimpoint CompM4 : collimateur sans grossissement, point de 2 MOA ; utile ~ 300 m comme le fer ( a "
                 "calibrer ), 0,34 kg avec son montage"),
    CaracOptique("aco", 1, 400, 0.30, 500, "optic_Aco",
                 "ACO du jeu : MESURE dans Arma le 13/09 ( B_Soldier_F, MX + ACO : p >= 0,5 jusqu a 400 m, sous 0,5 des "
                 "300 m ; les collimateurs ne portent aucun opticType ) ; masse et prix a calibrer"),
    CaracOptique("rco_x4", 4, 600, 0.45, 1500, "CUP_optic_RCO",
                 "Trijicon ACOG TA31 ( RCO de l US Army ) x 4 : reticule gradue jusqu a 800 m pour le 5,56 ; utile ~ 600 m "
                 "( a calibrer ), 0,45 kg"),
    CaracOptique("lunette_x10", 10, 1000, 0.60, 1800, "CUP_optic_LeupoldMk4_10x40_LRT",
                 "Leupold Mark 4 10 x 40 : lunette de tireur d elite, utile ~ 1 000 m ( a calibrer ), 0,6 kg"),
    CaracOptique("lunette_3x", 3, 700, 0.90, 3000, "CUP_optic_MAAWS_Scope",
                 "lunette 3 x du Carl Gustaf : la portee de la charge creuse sur cible fixe ( Saab, 700 m ) ; masse et prix "
                 "a calibrer"),
)
OPTIQUE = {o.nom: o for o in OPTIQUES}
IDX_OPTIQUE = {o.nom: k for k, o in enumerate(OPTIQUES)}
FER = IDX_OPTIQUE["fer"]
PORTEE_ARME = np.array([a.portee_m for a in ARMES])
PORTEE_OPTIQUE = np.array([o.portee_m for o in OPTIQUES])


def portee_utile_couple(arme, optique="fer"):
    """La portee utile d un tireur : le MINIMUM de son arme et de son optique ( metres )."""
    a = ARME[arme] if isinstance(arme, str) else ARMES[arme]
    o = OPTIQUE[optique] if isinstance(optique, str) else OPTIQUES[optique if optique is not None and optique >= 0 else FER]
    return min(a.portee_m, o.portee_m)


# ================================================================== les protections
class CaracProtection:
    """Une protection balistique. niveau : NIJ 0101.06 ( IIIA : arrete le 9 mm et le .44 Magnum ; III : six impacts de
    7,62 x 51 M80 ; IV : un impact de .30-06 M2 perforant ). zones : les regions ( domaine 16 ) qu elle couvre.
    mult : pour chaque menace, le multiplicateur de letalite d un impact sur une zone couverte ( 1 : aucune protection ).
    Lecon d Arma ( 13/09, decompile ) : l armure d un point de vie est un MULTIPLICATEUR, pas une valeur."""
    __slots__ = ("nom", "niveau", "zones", "masse_kg", "mult", "prix_eur", "arma", "source")

    def __init__(self, nom, niveau, zones, masse_kg, mult, prix_eur, arma, source):
        if set(mult) != set(MENACES) or any(not 0.0 < v <= 1.0 for v in mult.values()):
            raise ValueError(f"protection {nom} : un multiplicateur dans ] 0 ; 1 ] par menace")
        if masse_kg <= 0 or prix_eur <= 0: raise ValueError(f"protection {nom} : masse ou prix")
        self.nom, self.niveau, self.zones, self.masse_kg = nom, niveau, tuple(zones), float(masse_kg)
        self.mult, self.prix_eur, self.arma, self.source = dict(mult), float(prix_eur), arma, source


PROTECTIONS = (
    CaracProtection("casque", "IIIA", ("tete",), 1.5, {"pistolet": 0.2, "fusil": 1.0, "perforant": 1.0, "eclat": 0.4},
                    250, "H_HelmetB",
                    "casque composite ( type ACH ) : IIIA et eclats ( V50 ~ 600 m/s ), 1,5 kg ; multiplicateurs a calibrer"),
    CaracProtection("gilet_iiia", "IIIA", ("thorax", "abdomen"), 2.5,
                    {"pistolet": 0.1, "fusil": 1.0, "perforant": 1.0, "eclat": 0.5}, 400, "V_TacVest_oli",
                    "gilet souple NIJ IIIA : arrete les balles d arme de poing, pas celles de fusil ; 2,5 kg ; a calibrer"),
    CaracProtection("plaque_iii", "III", ("thorax", "abdomen"), 7.0,
                    {"pistolet": 0.1, "fusil": 0.15, "perforant": 1.0, "eclat": 0.3}, 900, "V_PlateCarrier1_rgr",
                    "porte-plaques et deux plaques NIJ III ( polyethylene ) : arrete le 7,62 x 51 M80 ; 7 kg ; a calibrer"),
    CaracProtection("plaque_iv", "IV", ("thorax", "abdomen"), 11.0,
                    {"pistolet": 0.1, "fusil": 0.1, "perforant": 0.15, "eclat": 0.25}, 1600, "V_PlateCarrier2_rgr",
                    "plaques ceramiques NIJ IV ( type ESAPI ) : un impact de .30-06 M2 AP ; 11 kg le systeme ; a calibrer"),
)
PROTECTION = {x.nom: x for x in PROTECTIONS}
IDX_PROTECTION = {x.nom: k for k, x in enumerate(PROTECTIONS)}
CASQUE = IDX_PROTECTION["casque"]


# ================================================================== les radios
class CaracRadio:
    __slots__ = ("nom", "portee_km", "masse_kg", "autonomie_h", "prix_eur", "arma", "source")

    def __init__(self, nom, portee_km, masse_kg, autonomie_h, prix_eur, arma, source):
        if not (portee_km > 0 and masse_kg > 0 and autonomie_h > 0 and prix_eur > 0): raise ValueError(f"radio {nom}")
        self.nom, self.portee_km, self.masse_kg, self.autonomie_h = nom, float(portee_km), float(masse_kg), float(autonomie_h)
        self.prix_eur, self.arma, self.source = float(prix_eur), arma, source


RADIOS = (
    CaracRadio("prc152", 5.0, 1.2, 12.0, 7000, "ItemRadio",
               "Harris AN/PRC-152, portative VHF/UHF : ~ 5 km en terrain degage ( a calibrer ), 1,2 kg, ~ 12 h de batterie "
               "au cycle 1:1:8 ; prix a calibrer"),
    CaracRadio("prc117g", 30.0, 5.4, 10.0, 35000, "B_RadioBag_01_mtp_F",
               "Harris AN/PRC-117G, sac a dos : ~ 30 km en VHF avec antenne fouet ( a calibrer ), 5,4 kg avec batterie ; "
               "classname de Contact"),
)
RADIO = {x.nom: x for x in RADIOS}
IDX_RADIO = {x.nom: k for k, x in enumerate(RADIOS)}


# ================================================================== les munitions ( biens du catalogue )
# ( nom, unite, euros l unite, masse kg, volume l emballe, source ). Prix 2024, apres la hausse de la guerre d Ukraine.
MUNITIONS = (
    ("mun_556", "cartouche 5,56 x 45 OTAN ( M855 / SS109 )", 0.60, 0.0123, 0.011,
     "~ 0,5 a 0,8 euro la cartouche en 2024 ( a calibrer ) ; 840 cartouches par caisse M2A1 de ~ 9 l"),
    ("mun_762", "cartouche 7,62 x 51 OTAN ( M80 )", 1.30, 0.025, 0.025, "~ 1 a 1,5 euro ( 2024, a calibrer )"),
    ("mun_9mm", "cartouche 9 x 19 Parabellum", 0.35, 0.012, 0.006, "~ 0,3 a 0,4 euro ( a calibrer )"),
    ("mun_127", "cartouche 12,7 x 99 OTAN ( M33 )", 5.0, 0.117, 0.07, "~ 4 a 6 euros ( a calibrer )"),
    ("roquette_84", "munition 84 mm a charge creuse ( FFV551 )", 2500.0, 3.2, 5.0, "a calibrer ( ordre de grandeur )"),
    ("obus_81", "obus explosif de mortier de 81 mm", 800.0, 4.2, 6.0, "a calibrer ( ordre de grandeur )"),
    ("obus_120", "obus flechette de 120 mm ( DM63 )", 7000.0, 21.0, 25.0, "a calibrer ( ordre de grandeur )"),
)
NOMS_MUNITIONS = tuple(m[0] for m in MUNITIONS)


# ================================================================== les vehicules militaires
class CaracVehicule:
    """Un modele de vehicule militaire. blindage : niveau de protection STANAG 4569 ( 0 aucun ; 1 : 7,62 x 51 ordinaire ;
    6 : 30 mm perforant ; un char est bien au-dela sur l avant ). La consommation se deduit du reservoir et de
    l autonomie sur route ( litres aux 100 km ). pieces_t_km : tonnes de pieces usees par km ( chenilles, filtres,
    pneus ) ; reparation_t : les pieces d une reparation apres panne ; mtbf_km : km moyens entre pannes, entretien a
    jour ; intervalle_km : l entretien au-dela duquel le risque de panne double."""
    __slots__ = ("nom", "categorie", "masse_t", "equipage", "places", "reservoir_l", "autonomie_km", "vitesse_kmh",
                 "blindage", "armement", "mtbf_km", "intervalle_km", "pieces_t_km", "reparation_t", "vie_km", "prix_eur",
                 "arma", "source")

    def __init__(self, nom, categorie, masse_t, equipage, places, reservoir_l, autonomie_km, vitesse_kmh, blindage,
                 armement, mtbf_km, intervalle_km, pieces_t_km, reparation_t, vie_km, prix_eur, arma, source):
        if not (masse_t > 0 and equipage >= 1 and places >= 0 and reservoir_l > 0 and autonomie_km > 0 and vitesse_kmh > 0
                and 0 <= blindage <= 6 and mtbf_km > 0 and intervalle_km > 0 and pieces_t_km >= 0 and reparation_t >= 0
                and vie_km > 0 and prix_eur > 0):
            raise ValueError(f"vehicule {nom} : grandeur hors bornes")
        self.nom, self.categorie, self.masse_t, self.equipage, self.places = nom, categorie, float(masse_t), int(equipage), int(places)
        self.reservoir_l, self.autonomie_km, self.vitesse_kmh, self.blindage = float(reservoir_l), float(autonomie_km), float(vitesse_kmh), int(blindage)
        self.armement, self.mtbf_km, self.intervalle_km = dict(armement), float(mtbf_km), float(intervalle_km)
        self.pieces_t_km, self.reparation_t, self.vie_km, self.prix_eur = float(pieces_t_km), float(reparation_t), float(vie_km), float(prix_eur)
        self.arma, self.source = arma, source

    @property
    def conso_l_100km(self): return 100.0 * self.reservoir_l / self.autonomie_km

    @property
    def unites_par_km(self): return self.conso_l_100km / 100.0 / LITRES_UNITE


VEHICULES = (
    CaracVehicule("leopard_2a6hel", "char", 62.5, 4, 0, 1160, 340, 68, 6, {"obus_120": 42, "mun_762": 4750},
                  1000, 250, 0.004, 0.2, 20000, 8.0e6, "CUP_B_Leopard2A6_GER",
                  "Leopard 2A6 HEL ( 170 livres a l armee grecque, 2006-2009 ) : 62,5 t, 4 hommes, 1 160 l, 340 km sur "
                  "route, 68 km/h, canon de 120 mm L55 ( 42 coups ) et deux MG3 ( 4 750 coups ) ; contrat de 2003 : "
                  "~ 1,7 Md euros pour 170 2A6HEL et 183 2A4 ; pannes, entretien et pieces ( chenilles ~ 20 euros/km ) a "
                  "calibrer"),
    CaracVehicule("m113a1", "vtt", 12.3, 2, 11, 360, 480, 64, 1, {"mun_127": 2000}, 2000, 1000, 0.001, 0.05, 50000,
                  4.0e5, "CUP_B_M113A3_USA",
                  "M113A1 : 12,3 t, 2 d equipage et 11 passagers ( un groupe ), 360 l, 480 km, 64 km/h, aluminium 5083 "
                  "( STANAG niveau 1, a verifier ), mitrailleuse M2HB ; pannes, entretien et prix a calibrer"),
    CaracVehicule("m1114", "blinde_leger", 5.5, 2, 2, 95, 443, 105, 1, {"mun_127": 1000}, 3000, 1500, 0.0003, 0.02,
                  150000, 2.2e5, "CUP_B_HMMWV_M1114_USMC",
                  "HMMWV M1114 blinde : ~ 5,5 t en charge, 95 l ( 25 gallons ), ~ 440 km, 105 km/h, protection 7,62 "
                  "ordinaire ; pannes, entretien et prix a calibrer"),
    CaracVehicule("steyr_12m18", "camion", 12.0, 1, 16, 180, 600, 85, 0, {}, 5000, 3000, 0.0003, 0.03, 300000, 1.5e5,
                  "B_Truck_01_transport_F",
                  "Steyr 12M18 ( construit sous licence par ELVO, le camion de l armee grecque ) : 12 t, 5 t de charge, "
                  "16 passagers ; reservoir, autonomie, pannes et prix a calibrer"),
)
VEHICULE = {v.nom: v for v in VEHICULES}
IDX_VEHICULE = {v.nom: k for k, v in enumerate(VEHICULES)}
VITESSE_USAGE_KMH = 30.0                 # le Parc compte l usure en heures : km / 30 km/h ( a calibrer )
PATROUILLEURS = ("m1114", "m113a1", "steyr_12m18")    # dans cet ordre de preference ; un char ne patrouille pas en ville
IDX_PATROUILLEURS = tuple(IDX_VEHICULE[v] for v in PATROUILLEURS)
SOLDATS_PAR_CHAR = 70                    # ~ 1 300 chars pour ~ 93 000 hommes de l armee de terre grecque ( IISS 2023,
#                                          a verifier ) ; le seul char modele est le 2A6HEL
EQUIPAGE_CHAR = 4


# ================================================================== l organisation
NIVEAUX = ("armee", "brigade", "bataillon", "compagnie", "section", "groupe")
ARMEE_N, BRIGADE, BATAILLON, COMPAGNIE, SECTION, GROUPE = range(6)
TYPES = ("etat_major", "infanterie", "appui", "chars", "instruction")
ETAT_MAJOR, INFANTERIE, APPUI, CHARS, INSTRUCTION = range(5)
# Effectifs ( ordres de grandeur OTAN, doctrine grecque a verifier ) : groupe 8 a 10, section 3 groupes ( ~ 30 avec son
# chef ), compagnie 3 sections de combat + 1 d appui ( ~ 120 ), bataillon 3 ou 4 compagnies ( 500 a 800 avec ses
# services ).
GROUPE_MIN, GROUPE_MAX, GROUPE_CIBLE = 8, 10, 9
GROUPES_PAR_SECTION = 3
SECTIONS_PAR_COMPAGNIE = 4
COMPAGNIES_PAR_BATAILLON = 4
GRADES = ("soldat", "caporal", "sergent", "adjudant", "sous_lieutenant", "lieutenant", "capitaine", "commandant",
          "lieutenant_colonel", "colonel", "general_de_brigade")
GRADES_GRECS = ("stratiotis", "dekaneas", "lochias", "anthypaspistis", "anthypolochagos", "ypolochagos", "lochagos",
                "tagmatarchis", "antisyntagmatarchis", "syntagmatarchis", "taxiarchos")
SOLDAT_G, CAPORAL, SERGENT, ADJUDANT, SOUS_LIEUTENANT = range(5)
# Anciennete des militaires de carriere ( annees ) pour caporal, sergent, adjudant ; age des officiers pour chaque grade
# a partir du sous-lieutenant ( sortie de l ecole des Evelpides vers 22 ans ) : a calibrer.
ANCIENNETE_SOUS_OFF = (3.0, 6.0, 15.0)
AGE_OFFICIER = (27.0, 31.0, 38.0, 44.0, 49.0, 54.0)
SPECIALITES = ("fusilier", "chef", "mitrailleur", "antichar", "tireur_elite", "radio", "secouriste", "conducteur",
               "mortier", "equipage", "officier")
FUSILIER, CHEF, MITRAILLEUR, ANTICHAR, TIREUR_ELITE, RADIO_S, SECOURISTE, CONDUCTEUR, MORTIER, EQUIPAGE, OFFICIER = range(11)
# La place dans le groupe fait la specialite ( 0 le chef, sergent ; 1 le caporal, chef du second binome ) ; dans la
# section, un radio, un secouriste et un tireur d elite pris aux trois groupes ( a verifier contre l organigramme grec ).
POSTES_GROUPE = (CHEF, FUSILIER, MITRAILLEUR, ANTICHAR, CONDUCTEUR)
POSTE_SECTION = (RADIO_S, SECOURISTE, TIREUR_ELITE)
# Dotation par specialite : ( arme principale, optique, arme secondaire ). Le G3A3 est le fusil de l armee grecque ; le
# HK416 et le M4 sont ceux des chefs et des unites d elite ( a verifier ).
DOTATION = {
    FUSILIER: ("g3a3", None, None), CHEF: ("hk416", "rco_x4", "glock17"), MITRAILLEUR: ("mg3", None, None),
    ANTICHAR: ("carl_gustaf_m3", "lunette_3x", "glock17"), TIREUR_ELITE: ("g3a3", "lunette_x10", None),
    RADIO_S: ("g3a3", None, None), SECOURISTE: ("m4a1", "point_rouge", None), CONDUCTEUR: ("g3a3", None, None),
    MORTIER: ("g3a3", None, None), EQUIPAGE: ("glock17", None, None), OFFICIER: ("m4a1", "aco", "glock17")}
PROTECTION_DE = {EQUIPAGE: "gilet_iiia"}          # les autres : plaque_iii
RADIO_DE = {CHEF: "prc152", OFFICIER: "prc152", RADIO_S: "prc117g"}
ARMA_SOLDAT = {FUSILIER: "B_Soldier_F", CHEF: "B_Soldier_SL_F", MITRAILLEUR: "B_soldier_AR_F", ANTICHAR: "B_soldier_LAT_F",
               TIREUR_ELITE: "B_soldier_M_F", RADIO_S: "B_Soldier_TL_F", SECOURISTE: "B_medic_F", CONDUCTEUR: "B_Soldier_F",
               MORTIER: "B_support_Mort_F", EQUIPAGE: "B_crew_F", OFFICIER: "B_officer_F"}
RESERVE_EQUIPEMENT = 0.10                 # l armurerie garde 10 % de plus que ce qu elle dote ( a calibrer )
# Munitions : la dotation de combat de chaque arme en service ( chargeurs, bandes ) est gardee a l armurerie en temps
# de paix ( a calibrer ) ; l instruction de tir en brule en plus ( coups par tireur et par journee de tir, a calibrer :
# l armee grecque tire peu ).
DOTATION_COMBAT = {"g3a3": 140, "m4a1": 210, "hk416": 210, "mg3": 1000, "glock17": 51, "carl_gustaf_m3": 6,
                   "mortier_81": 60}
COUPS_INSTRUCTION = {"g3a3": 20, "m4a1": 30, "hk416": 30, "mg3": 100, "glock17": 20, "carl_gustaf_m3": 0.05,
                     "mortier_81": 2}
JOURS_TIR_RESERVE = 10                    # l armurerie commande sous 10 journees de tir d avance ...
JOURS_TIR_CIBLE = 30                      # ... de quoi tenir 30 journees ( a calibrer )
PART_JOURS_TIR = 0.2                      # une compagnie tire un jour sur cinq en moyenne ( pour dimensionner )
PIECES_CIBLE_KM = 2000.0                  # l armurerie garde les pieces de 2 000 km de son parc ( a calibrer )

# ================================================================== le dimensionnement et la conscription
# IISS, The Military Balance 2023 : ~ 142 700 militaires actifs pour 10,4 millions de Grecs, 1,37 % ( a verifier ) ;
# part des conscrits ~ 30 % ( a verifier ) ; officiers ~ 12 % des militaires de carriere ( a calibrer ).
PART_ACTIFS = 0.0137
PART_CONSCRITS = 0.30
PART_OFFICIERS = 0.12
# Service national ( loi 3421/2005 et loi 4361/2016, armee de terre 12 mois depuis 2021, a verifier ) : les hommes,
# a partir de 19 ans ; sursis d etudes jusqu a la fin des etudes ( au plus ~ 28 ans ) ; les femmes volontaires
# seulement. Exemptes ( sante, charge de famille ) : ~ 10 % d une classe ( a calibrer ).
AGE_APPEL = 19.0
AGE_MAX_SURSIS = 28.0
DUREE_SERVICE_J = 365
MARGE_CDD_J = 30                           # le CDD du conscrit court plus loin : c est le domaine qui le libere
P_EXEMPTE = 0.10
ETALEMENT_ARRIERE_J = 60                  # le jour de l installation, les appeles en retard sont incorpores en 60 jours
#                                           ( les incorporations de l armee grecque tombent tous les deux mois )
PAS_APPEL, EXEMPTE, APPELE = -1, -2, -3   # la colonne ar_appel ( >= 0 : le jour de l appel )
ROLES_NON_APPELES = ("soldat", "officier", "chef_gouvernement", "ministre")
PROGRAMME_RECRUES = "classe_recrues"
# L instruction de base ( ~ 5 semaines dans un centre d instruction grec, a verifier ) : 20 jours d instruction, 8
# d exercice, 2 de debrief, puis l epreuve ; competence technique, qualification formation_militaire.
RECRUES = (20, 8, 2, 2, 0.3, "formation", 10.0)

# ================================================================== le soldat
# Competences et etats dans [ 0 ; 1 ]. Tirages de depart ( moyenne, ecart-type ) et effets par journee : a calibrer
# ( la litterature du maintien des competences, US Army Research Institute : le tir se perd en quelques mois sans
# entrainement ; la privation de sommeil degrade la vigilance ).
DEPART = {"tir": (0.55, 0.12), "perception": (0.50, 0.12), "endurance": (0.60, 0.10), "discipline": (0.60, 0.10)}
DEPART_RECRUE = {"tir": (0.20, 0.08), "perception": (0.40, 0.10), "endurance": (0.45, 0.12), "discipline": (0.40, 0.10)}
ACTIONS = ("instruction_tir", "marche", "repos", "maintenance", "patrouille")
TIR_A, MARCHE, REPOS, MAINTENANCE, PATROUILLE = range(5)
BUREAU = -1                                 # l etat-major et ceux qui n ont pas de compagnie : pas d activite de troupe
# La semaine d une compagnie d instruction ( lundi .. dimanche ) : marche, ordre serre et entretien de l armement, tir
# le mercredi, repos le week-end ( a calibrer : ~ 100 a 200 cartouches par recrue en cinq semaines ).
CYCLE_INSTRUCTION = (MARCHE, MAINTENANCE, TIR_A, MAINTENANCE, MARCHE, REPOS, REPOS)
GAIN = {"tir": 0.05, "endurance": 0.04, "perception": 0.02, "discipline": 0.01}
FATIGUE = np.array([0.15, 0.40, -0.35, 0.10, 0.25])
STRESS = np.array([0.03, 0.05, -0.15, 0.0, 0.10])
MORAL_REPOS = 0.03
RECUP_NUIT, DETENTE_NUIT = 0.15, 0.05
OUBLI = {"tir": 0.004, "endurance": 0.003, "perception": 0.001}
DEMI_VIE_MORAL = 0.9                        # la part propre du moral s eteint de 10 % par nuit
FATIGUE_LOURDE, MORAL_EPUISE = 0.7, 0.03
MORAL_REF = 0.60                            # le moral d un pays ordinaire, quand la culture n est pas la ( domaine 23 )
K_STRESS_MORAL = 0.15
# Perception : l oeil fatigue voit moins ( -50 % a fatigue pleine, a calibrer ) ; de nuit, detection mediane a 36 m
# sans jumelles ( mesure dans Arma, 13/09 ) ; de jour, ~ 300 m ( a calibrer ). La detection d une unite est celle de
# son meilleur guetteur : `knowsAbout` est une connaissance de CAMP ( 02/08 ).
DETECTION_JOUR_M, DETECTION_NUIT_M = 300.0, 36.0

# ================================================================== la decision
HORIZON = 3
POIDS_NOTE = (0.30, 0.25, 0.15, 0.15, 0.15)      # patrouilles, aptitude, repos, materiel, moral
PATROUILLES_PAR_JOUR = 2
MINUTES_PATROUILLE = (8 * 60, 20 * 60)
RETARD_PANNE = 2.0                          # le risque de panne est multiplie par 1 + 2 x ( retard d entretien )

TRAITS = (("tir", "registre de tir de la compagnie"), ("endurance", "tests physiques de la compagnie"),
          ("perception", "rapports de patrouille des chefs de section"),
          ("fatigue", "rapport des chefs de section ( sommeil, visite medicale )"), ("stress", "rapport des chefs de section"),
          ("moral", "rapport sur le moral"), ("materiel_en_service", "etat du parc de la compagnie"),
          ("entretien_en_retard", "carnet d entretien des vehicules"),
          ("carburant", "releve du depot de la base, en jours de patrouille sur 10"),
          ("munitions", "releve de l armurerie, en journees de tir sur 10"),
          ("patrouilles_hier", "journal de la base"))
T_TIR, T_END, T_PER, T_FAT, T_STR, T_MOR, T_DISPO, T_RETARD, T_CARB, T_MUN, T_PATR = range(len(TRAITS))


class ContexteCompagnie:
    __slots__ = ("traits",)

    def __init__(self, traits): self.traits = traits


def _observer(ctx): return ctx.traits


def _regle(x, ctx):
    """La garde d abord : la patrouille est le service de la base ; on la quitte pour le repos d une troupe epuisee,
    pour un parc en mauvais etat, ou pour une competence tombee trop bas."""
    if x[T_FAT] > 0.55: return REPOS
    if x[T_RETARD] >= 0.5 or x[T_DISPO] < 0.75: return MAINTENANCE
    if x[T_TIR] < 0.45 and x[T_MUN] >= 0.1: return TIR_A
    if x[T_END] < 0.45: return MARCHE
    return PATROUILLE


def _temoin(x, ctx, rng): return TIR_A


POINT = D.PointDeDecision(
    "activite_compagnie", DOMAINE, TRAITS, ACTIONS, _observer, _regle, _temoin,
    "chaque soir, pour CETTE compagnie : 0,30 x patrouilles tenues sur 2 + 0,25 x aptitude ( tir, endurance, perception ) "
    "+ 0,15 x ( 1 - fatigue ) + 0,15 x part des vehicules en service + 0,15 x moral", HORIZON)


# ================================================================== les tables ( structures de tableaux )
class Table:
    """Des lignes en colonnes numpy ( Vec<T> en Rust ) : `champs` = ( nom, dtype, defaut ). Croissance par doublement ;
    une ligne n est jamais deplacee ( son numero est une reference ), une ligne morte garde ses valeurs."""
    __slots__ = ("n", "cap", "cols", "champs")

    def __init__(self, champs, cap=64):
        self.n, self.cap, self.champs = 0, cap, champs
        self.cols = {nom: np.full(cap, v, dt) for nom, dt, v in champs}

    def __getitem__(self, nom): return self.cols[nom]

    def ajouter(self, k=1):
        """Reserve k lignes, rend le numero de la premiere."""
        if self.n + k > self.cap:
            cap = max(self.n + k, 2 * self.cap)
            for nom, dt, v in self.champs:
                a = np.full(cap, v, dt); a[:self.n] = self.cols[nom][:self.n]; self.cols[nom] = a
            self.cap = cap
        d = self.n; self.n += k
        return d


CHAMPS_EFFECTIFS = (
    ("hid", np.int64, -1), ("base", np.int32, -1), ("unite", np.int32, -1), ("grade", np.int8, 0),
    ("spec", np.int8, FUSILIER), ("statut", np.int8, 2), ("conscrit", np.int8, 0), ("debut_j", np.int32, 0),
    ("fin_j", np.int32, -1), ("tir", np.float64, 0.0), ("perception", np.float64, 0.0), ("endurance", np.float64, 0.0),
    ("discipline", np.float64, 0.0), ("fatigue", np.float64, 0.0), ("stress", np.float64, 0.0),
    ("moral_u", np.float64, 0.0), ("moral", np.float64, MORAL_REF), ("arme", np.int64, -1), ("arme2", np.int64, -1),
    ("optique", np.int64, -1), ("arme_m", np.int8, -1), ("arme2_m", np.int8, -1), ("optique_m", np.int8, -1),
    ("protection", np.int8, -1), ("casque", np.int8, -1), ("radio", np.int8, -1))
STATUTS = ("actif", "instruction", "parti")
ACTIF, EN_INSTRUCTION, PARTI = range(3)
CHAMPS_UNITES = (("niveau", np.int8, 0), ("type", np.int8, 0), ("parent", np.int32, -1), ("base", np.int32, -1),
                 ("chef", np.int64, -1), ("numero", np.int32, 0)) + tuple((f"a{k}", np.int32, -1) for k in range(6))
CHAMPS_VEHICULES = (("oid", np.int64, -1), ("modele", np.int8, -1), ("base", np.int32, -1), ("unite", np.int32, -1),
                    ("km", np.float64, 0.0), ("km_entretien", np.float64, 0.0), ("km_jour", np.float64, 0.0),
                    ("etat", np.int8, O.SERVICE))
CHAMPS_COLLECTIVES = (("oid", np.int64, -1), ("modele", np.int8, -1), ("base", np.int32, -1), ("unite", np.int32, -1))


# ================================================================== les detenteurs et l etat
class Armurerie:
    """L armurerie et le magasin d une base : le Stock des munitions et des pieces ; proprietaire des armes, optiques,
    protections, radios et vehicules de la base. Elle ne detient pas d argent : l Etat paie."""
    __slots__ = ("base", "lieu", "stock")

    def __init__(self, base, lieu):
        self.base, self.lieu, self.stock = int(base), lieu, B.Stock()


class Armee:
    """L etat du domaine."""
    __slots__ = ("eff", "unites", "veh", "coll", "armureries", "par_base", "bases", "decideur", "activite", "imposee",
                 "compagnies", "patr_jour", "patr_hier", "ratelier", "mids", "idx_parc", "bids", "entrees", "sorties",
                 "stock0", "exemptes", "incorpores", "liberes", "depenses", "serie", "vise", "cmd_jour", "anomalies_vues",
                 "ctx", "brigades", "armee_u", "patr_base", "dotes")

    def __init__(self):
        self.eff = Table(CHAMPS_EFFECTIFS, 256)
        self.unites = Table(CHAMPS_UNITES, 64)
        self.veh = Table(CHAMPS_VEHICULES, 64)
        self.coll = Table(CHAMPS_COLLECTIVES, 16)
        self.armureries = []           # une par base, dans l ordre des bases
        self.par_base = {}             # numero de lieu de la base -> rang de son armurerie
        self.bases = []                # numeros de lieu des bases, tries
        self.decideur = None
        self.activite = {}             # compagnie -> action du jour ( instruction : TIR_A, sans decision )
        self.imposee = {}              # compagnie -> ( action, dernier jour ) : un ordre du domaine 27 ou d une porte
        self.compagnies = []           # les compagnies qui decident ( infanterie, chars ), triees
        self.patr_jour = {}            # compagnie -> patrouilles tenues aujourd hui
        self.patr_hier = {}            # numero de base -> ( faites, annulees ) hier
        self.ratelier = {}             # ( base, arme ou optique ) -> [ numeros d objets non dotes ]
        self.mids = {}                 # nom de modele -> identifiant au Parc
        self.idx_parc = {}             # identifiant au Parc -> ( famille, indice dans sa table )
        self.bids = {}                 # nom de bien -> identifiant au catalogue
        self.entrees = {}              # bien -> quantites entrees aux armureries ( dotation, import, livraison )
        self.sorties = {}              # ( bien, motif ) -> quantites sorties, comptees par le domaine
        self.stock0 = {}
        self.exemptes = 0
        self.incorpores = []           # ( jour, habitant, base, age )
        self.liberes = []              # ( jour, habitant )
        self.depenses = {"munitions": 0.0, "pieces": 0.0, "vehicules": 0.0, "armes": 0.0}
        self.serie = []
        self.vise = {}
        self.cmd_jour = {}             # compagnie -> action decidee ce matin ( pour la note )
        self.anomalies_vues = 0
        self.ctx = {}
        self.brigades = {}             # ile -> unite brigade
        self.armee_u = -1
        self.patr_base = {}            # numero de base -> ( faites, annulees ) aujourd hui
        self.dotes = {}                # ( base, modele ) -> exemplaires de protections et radios dotes


class RemplacePatrouilles:
    """Prend la place de Monde.patrouilles ( 8 h et 20 h ) : un objet, pour rester picklable."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self): _patrouilles(self.pays)


class RemplaceRavitaillement:
    """Prend la place de Monde.ravitailler_bases ( 7 h )."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self): _ravitailler(self.pays)


def _dom(p): return p.domaines[DOMAINE]
def _membres_armureries(w): return w.pays.domaines[DOMAINE].armureries


# ================================================================== l organisation : les unites
def _nouvelle_unite(d, niveau, type_, parent, base, numero):
    U = d.unites
    u = U.ajouter()
    U["niveau"][u], U["type"][u], U["parent"][u], U["base"][u], U["numero"][u] = niveau, type_, parent, base, numero
    for k in range(6): U[f"a{k}"][u] = U[f"a{k}"][parent] if parent >= 0 and k < niveau else -1
    U[f"a{niveau}"][u] = u
    return u


def _enfants(d, u, niveau=None):
    U = d.unites; n = U.n
    m = U["parent"][:n] == u
    if niveau is not None: m &= U["niveau"][:n] == niveau
    return np.nonzero(m)[0].tolist()


def nom_unite(p, u):
    """Un nom lisible : « 2e groupe / 1re section / 1re compagnie / bataillon de military01 »."""
    d = _dom(p); U = d.unites
    parts = []
    while u >= 0:
        niv = int(U["niveau"][u])
        if niv == BATAILLON:
            parts.append(f"bataillon {int(U['numero'][u]) + 1} de {p.w.carte.par_n[int(U['base'][u])].id}")
        elif niv in (BRIGADE, ARMEE_N):
            parts.append(NIVEAUX[niv] + (f" {int(U['numero'][u]) + 1}" if niv == BRIGADE else ""))
        else:
            parts.append(f"{int(U['numero'][u]) + 1}e {NIVEAUX[niv]} ( {TYPES[int(U['type'][u])]} )")
        u = int(U["parent"][u])
    return " / ".join(parts)


def _anc(d, rows, niveau):
    """L unite de niveau `niveau` de chaque ligne ( -1 si l unite de la ligne est au-dessus )."""
    U = d.unites
    un = d.eff["unite"][rows]
    return np.where(un >= 0, U[f"a{niveau}"][np.maximum(un, 0)], -1)


def _lignes(d):
    """Les lignes des militaires presents ( actifs et recrues ), dans l ordre."""
    E = d.eff
    return np.nonzero(E["statut"][:E.n] != PARTI)[0]


def _lignes_actives(d):
    E = d.eff
    return np.nonzero(E["statut"][:E.n] == ACTIF)[0]


# ================================================================== l installation : recensement militaire
def _anciennete(p, ids):
    col = p.colonnes["habitant"]
    car = col["tr_carriere"][ids] > 0
    return np.where(car, (p.jour - col["tr_carriere_j"][ids]) / JOURS_AN, 0.0)


def _ages(p, ids):
    return (p.jour - p.col("habitant", "naissance_j")[np.asarray(ids, np.int64)]) / POP.JOURS_AN


def _grade(p, ids, officier):
    """Le grade de chacun : sous-officiers par anciennete, officiers par age ( a calibrer )."""
    ids = np.asarray(ids, np.int64)
    g = np.zeros(len(ids), np.int8)
    if not len(ids): return g
    anc = _anciennete(p, ids); age = _ages(p, ids)
    sous = np.searchsorted(np.array(ANCIENNETE_SOUS_OFF), anc, side="right").astype(np.int8)
    off = (SOUS_LIEUTENANT + np.searchsorted(np.array(AGE_OFFICIER), age, side="right")).astype(np.int8)
    return np.where(officier, off, sous).astype(np.int8)


def _tirer_competences(rng, n, depart, ages=None):
    out = {}
    for k in ("tir", "perception", "endurance", "discipline"):
        m, s = depart[k]
        x = m + s * rng.standard_normal(n)
        if k == "endurance" and ages is not None: x -= 0.01 * np.maximum(0.0, ages - 30.0)   # a calibrer
        out[k] = np.clip(x, 0.05, 0.95)
    return out


def _ajouter_militaires(p, d, ids, base_de, officier, conscrit, statut, depart, rng):
    """Des lignes aux effectifs pour les habitants `ids` ( tries ), sans unite encore."""
    E = d.eff; col_r = p.col("habitant", "ar_rang")
    k = len(ids)
    if not k: return np.zeros(0, np.int64)
    r0 = E.ajouter(k); rows = np.arange(r0, r0 + k)
    E["hid"][rows] = ids; E["base"][rows] = base_de; E["statut"][rows] = statut; E["conscrit"][rows] = conscrit
    E["grade"][rows] = np.where(conscrit, SOLDAT_G, _grade(p, ids, officier))
    E["spec"][rows] = np.where(officier, OFFICIER, FUSILIER)
    E["debut_j"][rows] = p.jour
    comp = _tirer_competences(rng, k, depart, _ages(p, ids))
    for nom, v in comp.items(): E[nom][rows] = v
    E["fatigue"][rows] = 0.2; E["stress"][rows] = 0.1; E["moral_u"][rows] = 0.0
    col_r[ids] = rows
    return rows


def _tailles(n, cible, mini, maxi):
    """n hommes en groupes de mini a maxi ( au plus pres de `cible` ) ; si c est impossible ( 11 a 15 ), en groupes
    plus petits. Tailles egales a un pres, les plus grands d abord."""
    if n <= 0: return []
    lo, hi = math.ceil(n / maxi), max(1, n // mini)
    g = min(max(int(round(n / cible)), lo), hi) if lo <= hi else lo
    q, r = divmod(n, g)
    return [q + 1] * r + [q] * (g - r)


def _organiser(p, d):
    """L ordre de bataille : une brigade par ile, un bataillon par base ( ou plus ), des compagnies de 4 sections dont
    la 4e est l appui, des sections de 3 groupes, des groupes de 8 a 10 ; un peloton de chars a la base la plus
    peuplee ; les officiers commandent d abord les compagnies, puis les bataillons, puis les sections."""
    E = d.eff; U = d.unites; w = p.w
    d.armee_u = _nouvelle_unite(d, ARMEE_N, ETAT_MAJOR, -1, -1, 0)
    iles = sorted({w.carte.par_n[b].ile for b in d.bases}, key=lambda i: w.carte.iles.index(i))
    for k, ile in enumerate(iles): d.brigades[ile] = _nouvelle_unite(d, BRIGADE, ETAT_MAJOR, d.armee_u, -1, k)
    rows = _lignes(d)
    tot_soldats = int(((E["spec"][rows] != OFFICIER) & (E["statut"][rows] == ACTIF)).sum())
    n_chars = int(round(tot_soldats / SOLDATS_PAR_CHAR))
    comptes = {b: int(((E["base"][rows] == b) & (E["spec"][rows] != OFFICIER) & (E["statut"][rows] == ACTIF)).sum())
               for b in d.bases}
    base_chars = max(d.bases, key=lambda b: (comptes[b], -b)) if d.bases else -1
    for b in d.bases:
        ile = w.carte.par_n[b].ile
        rb = rows[E["base"][rows] == b]
        # les soldats, par grade puis anciennete ( debut de carriere ), puis numero
        sold = rb[(E["spec"][rb] != OFFICIER) & (E["statut"][rb] == ACTIF)]
        hids = E["hid"][sold]
        anc = _anciennete(p, hids)
        sold = sold[np.lexsort((hids, -anc, -E["grade"][sold].astype(np.int64)))]
        offs = rb[E["spec"][rb] == OFFICIER]
        offs = offs[np.lexsort((E["hid"][offs], -E["grade"][offs].astype(np.int64)))]
        recrues = rb[E["statut"][rb] == EN_INSTRUCTION]
        bat = _nouvelle_unite(d, BATAILLON, INFANTERIE, d.brigades[ile], b, 0)
        # le peloton de chars
        crews = []
        if b == base_chars and n_chars > 0:
            n_eq = min(n_chars, len(sold) // (EQUIPAGE_CHAR * 3))     # au plus un tiers de la base dans les chars
            if n_eq > 0:
                pris = sold[:n_eq * EQUIPAGE_CHAR]
                sold = sold[n_eq * EQUIPAGE_CHAR:]
                crews = [pris[k::n_eq] for k in range(n_eq)]            # chaque equipage a un ancien a sa tete
        groupes = []
        k = 0
        for t in _tailles(len(sold), GROUPE_CIBLE, GROUPE_MIN, GROUPE_MAX):
            groupes.append(sold[k:k + t]); k += t
        sections = [groupes[i:i + GROUPES_PAR_SECTION] for i in range(0, len(groupes), GROUPES_PAR_SECTION)]
        compagnies = [sections[i:i + SECTIONS_PAR_COMPAGNIE] for i in range(0, len(sections), SECTIONS_PAR_COMPAGNIE)]
        unites_c = []
        n_bat, n_comp_bat = 0, 0
        for ci, secs in enumerate(compagnies):
            if n_comp_bat >= COMPAGNIES_PAR_BATAILLON:
                n_bat += 1; n_comp_bat = 0
                bat = _nouvelle_unite(d, BATAILLON, INFANTERIE, d.brigades[ile], b, n_bat)
            c = _nouvelle_unite(d, COMPAGNIE, INFANTERIE, bat, b, n_comp_bat); n_comp_bat += 1
            unites_c.append(c)
            for si, gs in enumerate(secs):
                appui = si == SECTIONS_PAR_COMPAGNIE - 1
                s = _nouvelle_unite(d, SECTION, APPUI if appui else INFANTERIE, c, b, si)
                for gi, g in enumerate(gs):
                    gu = _nouvelle_unite(d, GROUPE, APPUI if appui else INFANTERIE, s, b, gi)
                    E["unite"][g] = gu
                    for pos, r in enumerate(g.tolist()):
                        if appui: sp = CHEF if pos == 0 else CONDUCTEUR if pos == 4 else MORTIER
                        elif pos < len(POSTES_GROUPE): sp = POSTES_GROUPE[pos]
                        elif pos == 5 and gi < len(POSTE_SECTION): sp = POSTE_SECTION[gi]
                        else: sp = FUSILIER
                        E["spec"][r] = sp
                    U["chef"][gu] = E["hid"][g[0]] if len(g) else -1
        if crews:
            if n_comp_bat >= COMPAGNIES_PAR_BATAILLON:
                n_bat += 1; n_comp_bat = 0
                bat = _nouvelle_unite(d, BATAILLON, INFANTERIE, d.brigades[ile], b, n_bat)
            c = _nouvelle_unite(d, COMPAGNIE, CHARS, bat, b, n_comp_bat); n_comp_bat += 1
            unites_c.append(c)
            for si in range(0, len(crews), 4):
                s = _nouvelle_unite(d, SECTION, CHARS, c, b, si // 4)
                for gi, g in enumerate(crews[si:si + 4]):
                    gu = _nouvelle_unite(d, GROUPE, CHARS, s, b, gi)
                    g = g[np.lexsort((E["hid"][g], -E["grade"][g].astype(np.int64)))]
                    E["unite"][g] = gu; E["spec"][g] = EQUIPAGE
                    U["chef"][gu] = E["hid"][g[0]]
        if len(recrues):
            c = _nouvelle_unite(d, COMPAGNIE, INSTRUCTION, bat, b, n_comp_bat)
            E["unite"][recrues] = c
        # les officiers : compagnies, bataillons, sections ; les autres a l etat-major du bataillon
        bats = [u for u in range(U.n) if U["niveau"][u] == BATAILLON and U["base"][u] == b]
        secs_b = [u for u in range(U.n) if U["niveau"][u] == SECTION and U["base"][u] == b]
        places = unites_c + bats + secs_b
        for k, r in enumerate(offs.tolist()):
            u = places[k] if k < len(places) else bats[0]
            E["unite"][r] = u
            if k < len(places): U["chef"][u] = E["hid"][r]
    _chefs_par_defaut(d)
    _refaire_compagnies(d)


def _chefs_par_defaut(d):
    """Une unite sans officier est commandee par le chef de sa premiere fille ( le plus ancien sous-officier ) ; une
    brigade ou l armee, par le plus haut grade de ses chefs de bataillon."""
    U = d.unites; E = d.eff
    for niv in (SECTION, COMPAGNIE, BATAILLON, BRIGADE, ARMEE_N):
        for u in range(U.n):
            if U["niveau"][u] != niv or U["chef"][u] >= 0: continue
            filles = [f for f in _enfants(d, u) if U["chef"][f] >= 0]
            if not filles: continue
            if niv in (BRIGADE, ARMEE_N):
                hid_rang = {int(E["hid"][r]): r for r in _lignes(d).tolist()}
                cands = [int(U["chef"][f]) for f in filles]
                U["chef"][u] = max(cands, key=lambda h: (int(E["grade"][hid_rang[h]]) if h in hid_rang else -1, -h))
            else:
                U["chef"][u] = U["chef"][filles[0]]


def _recommander(d):
    """Un chef parti ( mort, mute, libere ) : son unite est reprise par le plus ancien de ses membres ( groupe ), ou par
    le chef de sa premiere fille ( au-dessus )."""
    U = d.unites; E = d.eff; rows = _lignes(d)
    pres = set(E["hid"][rows].tolist())
    vac = [u for u in range(U.n) if U["chef"][u] >= 0 and int(U["chef"][u]) not in pres]
    if not vac: return
    for u in vac: U["chef"][u] = -1
    for u in vac:
        m = rows[E["unite"][rows] == u]
        if U["niveau"][u] == GROUPE and len(m):
            U["chef"][u] = E["hid"][m[np.lexsort((E["hid"][m], -E["grade"][m].astype(np.int64)))][0]]
    _chefs_par_defaut(d)


def _refaire_compagnies(d):
    U = d.unites; n = U.n
    m = (U["niveau"][:n] == COMPAGNIE) & np.isin(U["type"][:n], (INFANTERIE, CHARS))
    d.compagnies = np.nonzero(m)[0].tolist()


# ================================================================== l equipement
def _declarer_modeles(p, d):
    parc = p.socle.parc
    for a in ARMES:
        m = parc.declarer_modele(a.nom, "arme", _dr(a.prix_eur), a.masse_kg, a.vie_coups / 100.0, a.arma, None, a.source)
        d.mids[a.nom] = m.id; d.idx_parc[m.id] = ("arme", IDX_ARME[a.nom])
    for o in OPTIQUES:
        if o.arma is None: continue
        m = parc.declarer_modele(o.nom, "optique", _dr(o.prix_eur), o.masse_kg, 10000.0, o.arma, None, o.source)
        d.mids[o.nom] = m.id; d.idx_parc[m.id] = ("optique", IDX_OPTIQUE[o.nom])
    for x in PROTECTIONS:
        m = parc.declarer_modele(x.nom, "equipement", _dr(x.prix_eur), x.masse_kg, 5 * 365 * 8.0, x.arma, None, x.source)
        d.mids[x.nom] = m.id; d.idx_parc[m.id] = ("protection", IDX_PROTECTION[x.nom])
    for x in RADIOS:
        m = parc.declarer_modele(x.nom, "equipement", _dr(x.prix_eur), x.masse_kg, 10 * 365 * 8.0, x.arma, None, x.source)
        d.mids[x.nom] = m.id; d.idx_parc[m.id] = ("radio", IDX_RADIO[x.nom])
    for v in VEHICULES:
        m = parc.declarer_modele(v.nom, "vehicule", _dr(v.prix_eur), v.masse_t * 1000.0, v.vie_km / VITESSE_USAGE_KMH,
                                 v.arma, None, v.source)
        d.mids[v.nom] = m.id; d.idx_parc[m.id] = ("vehicule", IDX_VEHICULE[v.nom])


def _importer_objets(p, d, nom, n, famille="produit_fini"):
    """Un achat a l etranger ( domaine 7 ), paye par l Etat : rend le nombre paye ( 0 si la caisse ou les devises
    manquent ). Les objets entrent au Parc par l appelant, source importe."""
    prix = {**{a.nom: a.prix_eur for a in ARMES}, **{o.nom: o.prix_eur for o in OPTIQUES}, **{x.nom: x.prix_eur for x in PROTECTIONS},
            **{x.nom: x.prix_eur for x in RADIOS}, **{v.nom: v.prix_eur for v in VEHICULES}}[nom]
    paye = EXT.declarer_import(p, p.w.gouv, n * _dr(prix), famille, "import_armement")
    if paye <= 0.0: return 0
    d.depenses["vehicules" if nom in VEHICULE else "armes"] += paye
    return n


def _tirer_objet(p, d, base, nom, source="initial"):
    """Un individu de la base : du ratelier, sinon de la reserve ( cohorte ), sinon cree ( installation ) ou achete a
    l etranger ( ensuite ). -1 si rien."""
    lst = d.ratelier.get((base, nom))
    if lst: return lst.pop(0)
    parc = p.socle.parc; arm = d.armureries[d.par_base[base]]
    c = parc.cohortes.get((d.mids[nom], arm, arm.lieu))
    if c is not None and c.nombre > 0: return parc.materialiser(c, p.pas).id
    if source == "importe" and not _importer_objets(p, d, nom, 1): return -1
    return parc.creer(d.mids[nom], arm, arm.lieu, source, p.pas).id


def _equiper(p, d, base, nom, source):
    """Un exemplaire de protection ou de radio pour un militaire de la base : pris dans la cohorte de l armurerie s il
    en reste un non dote, sinon cree ( installation ) ou achete. Rend vrai s il est dote."""
    parc = p.socle.parc; arm = d.armureries[d.par_base[base]]
    c = parc.cohortes.get((d.mids[nom], arm, arm.lieu))
    dotes = d.dotes.get((base, nom), 0)
    if c is None or c.nombre <= dotes:
        if source == "importe" and not _importer_objets(p, d, nom, 1): return False
        parc.creer_cohorte(d.mids[nom], arm, arm.lieu, 1, source, 0.0)
    d.dotes[(base, nom)] = dotes + 1
    return True


def _doter(p, d, rows, source="initial"):
    """La dotation de chaque ligne selon sa specialite : arme, optique, arme secondaire ( individus, numeros de serie ) ;
    protection, casque, radio ( des exemplaires des cohortes de l armurerie, comptes par base )."""
    E = d.eff
    for r in rows.tolist():
        b = int(E["base"][r]); sp = int(E["spec"][r])
        a, o, a2 = DOTATION[sp]
        for champ, nom, table in (("arme", a, IDX_ARME), ("optique", o, IDX_OPTIQUE), ("arme2", a2, IDX_ARME)):
            if nom is None or E[champ][r] >= 0: continue
            oid = _tirer_objet(p, d, b, nom, source)
            E[champ][r] = oid
            E[champ + "_m"][r] = table[nom] if oid >= 0 else -1
            if oid < 0: p.compter("arme_manquante")
        rd = RADIO_DE.get(sp)
        for champ, nom, k in (("protection", PROTECTION_DE.get(sp, "plaque_iii"), IDX_PROTECTION),
                              ("casque", "casque", IDX_PROTECTION), ("radio", rd, IDX_RADIO)):
            if nom is None or E[champ][r] >= 0: continue
            if _equiper(p, d, b, nom, source): E[champ][r] = k[nom]


def _rendre(p, d, r):
    """Un militaire qui part ( ou change de specialite ) rend ses armes au ratelier de sa base et son equipement a
    l armurerie : tout reste a l armurerie."""
    E = d.eff; b = int(E["base"][r])
    parc = p.socle.parc
    for champ in ("arme", "optique", "arme2"):
        oid = int(E[champ][r])
        if oid >= 0 and oid in parc.objets:
            d.ratelier.setdefault((b, parc.modeles[parc.objets[oid].modele].nom), []).append(oid)
        E[champ][r] = -1; E[champ + "_m"][r] = -1
    for champ, table in (("protection", PROTECTIONS), ("casque", PROTECTIONS), ("radio", RADIOS)):
        k = int(E[champ][r])
        if k >= 0: d.dotes[(b, table[k].nom)] -= 1
        E[champ][r] = -1


def _equipement_initial(p, d):
    """Les cohortes de protections et de radios ( dotation + reserve ), la reserve d armes, les vehicules et les
    armes collectives de chaque unite, les munitions ( dotation de combat + 30 journees de tir ) et les pieces."""
    E = d.eff; U = d.unites; parc = p.socle.parc; L = p.socle.livre
    rows = _lignes(d)
    for b in d.bases:
        arm = d.armureries[d.par_base[b]]
        rb = rows[E["base"][rows] == b]
        for (bb, nom), x in sorted(d.dotes.items()):
            if bb != b: continue
            n = int(math.ceil(x * RESERVE_EQUIPEMENT))
            if n > 0: parc.creer_cohorte(d.mids[nom], arm, arm.lieu, n, "initial", 0.2)
        armes = {}
        for champ in ("arme_m", "arme2_m"):
            for k in E[champ][rb].tolist():
                if k >= 0: armes[ARMES[k].nom] = armes.get(ARMES[k].nom, 0) + 1
        for nom in sorted(armes):
            n = int(math.ceil(armes[nom] * RESERVE_EQUIPEMENT))
            if n > 0: parc.creer_cohorte(d.mids[nom], arm, arm.lieu, n, "initial", 0.2)
    # les vehicules et les armes collectives, par unite
    V = d.veh; K = d.coll
    for u in range(U.n):
        niv, ty, b = int(U["niveau"][u]), int(U["type"][u]), int(U["base"][u])
        if b < 0: continue
        dot = []
        if niv == GROUPE and ty == INFANTERIE: dot = ["m113a1"]
        elif niv == GROUPE and ty == CHARS: dot = ["leopard_2a6hel"]
        elif niv == SECTION and ty == INFANTERIE: dot = ["m1114"]
        elif niv == SECTION and ty == APPUI: dot = ["steyr_12m18"]
        elif niv == COMPAGNIE and ty in (INFANTERIE, INSTRUCTION): dot = ["steyr_12m18"] * (2 if ty == INFANTERIE else 1)
        for nom in dot: _ajouter_vehicule(p, d, nom, b, u, "initial", usure_km=0.0)
        if niv == SECTION and ty == APPUI:
            for _ in range(MORTIERS_PAR_SECTION_APPUI):
                arm = d.armureries[d.par_base[b]]
                o = parc.creer(d.mids["mortier_81"], arm, arm.lieu, "initial", p.pas)
                k = K.ajouter()
                K["oid"][k], K["modele"][k], K["base"][k], K["unite"][k] = o.id, IDX_ARME["mortier_81"], b, u
    # usure de depart des vehicules ( compteurs tires ) : a calibrer
    rng = p.hasard("armee_parc")
    nv = V.n
    if nv:
        mod = V["modele"][:nv]
        inter = np.array([VEHICULES[m].intervalle_km for m in mod.tolist()])
        V["km_entretien"][:nv] = inter * rng.random(nv)
        V["km"][:nv] = np.array([VEHICULES[m].vie_km for m in mod.tolist()]) * 0.3 * rng.random(nv)
        for k in range(nv):
            o = parc.objets[int(V["oid"][k])]
            parc.user(o, float(V["km"][k]) / VITESSE_USAGE_KMH)
    # munitions et pieces
    for b in d.bases:
        arm = d.armureries[d.par_base[b]]
        for bien, q in sorted(_cible_munitions(p, d, b, JOURS_TIR_CIBLE).items()):
            if q > 0: _entrer(p, d, arm, bien, q, "dotation_initiale_armee", importe=True)
        q = _besoin_pieces(p, d, b)
        if q > 0: _entrer(p, d, arm, "pieces", q, "dotation_initiale_armee", importe=True)
    for bien in NOMS_MUNITIONS + ("pieces",):
        d.stock0[bien] = math.fsum(a.stock[d.bids[bien]] for a in d.armureries)
    d.entrees = {}; d.sorties = {}           # la dotation du jour est dans stock0 ; on compte a partir d ici


def _ajouter_vehicule(p, d, nom, base, unite, source, usure_km=0.0):
    parc = p.socle.parc; arm = d.armureries[d.par_base[base]]; V = d.veh
    o = parc.creer(d.mids[nom], arm, arm.lieu, source, p.pas, min(1.0, usure_km / VEHICULES[IDX_VEHICULE[nom]].vie_km))
    k = V.ajouter()
    V["oid"][k], V["modele"][k], V["base"][k], V["unite"][k] = o.id, IDX_VEHICULE[nom], base, unite
    V["km"][k] = usure_km; V["etat"][k] = O.SERVICE
    return k


def _entrer(p, d, arm, bien, q, motif, importe=False):
    """Une entree comptee a l armurerie : la dotation du jour de l installation ( importee sans paiement )."""
    L = p.socle.livre
    q = L.importer(arm.stock, d.bids[bien], q, motif) if importe else q
    d.entrees[bien] = d.entrees.get(bien, 0.0) + q
    return q


def _sortir(p, d, arm, bien, q, motif, nature="consomme"):
    """Une sortie comptee : consommee ( tir, entretien ), perdue ou detruite ( domaine 27 ). Rend la quantite sortie."""
    L = p.socle.livre
    q = L.puits(arm.stock, d.bids[bien], q, nature, motif)
    if q > 0: d.sorties[(bien, motif)] = d.sorties.get((bien, motif), 0.0) + q
    return q


COUPS_ARR = np.array([COUPS_INSTRUCTION[a.nom] for a in ARMES])
DOTATION_ARR = np.array([DOTATION_COMBAT[a.nom] for a in ARMES], np.float64)
CALIBRE_ARR = np.array([NOMS_MUNITIONS.index(a.calibre) for a in ARMES], np.int64)
PART_ARME2 = 0.2                 # l arme de poing d un porteur de fusil tire peu ( a calibrer )


def _par_calibre(par_arme):
    """{ bien : quantite } a partir d un tableau par modele d arme."""
    q = np.bincount(CALIBRE_ARR, weights=par_arme, minlength=len(NOMS_MUNITIONS))
    return {NOMS_MUNITIONS[k]: float(q[k]) for k in np.nonzero(q > 0)[0].tolist()}


def _armes_par_modele(d, rows, collectives_de=None):
    """Le nombre d armes de chaque modele des lignes ( les armes de poing secondaires comptent pour PART_ARME2 ) et les
    armes collectives des unites designees."""
    E = d.eff
    a = E["arme_m"][rows]; a2 = E["arme2_m"][rows]
    n = np.bincount(a[a >= 0], minlength=len(ARMES)).astype(np.float64)
    n += PART_ARME2 * np.bincount(a2[a2 >= 0], minlength=len(ARMES))
    if collectives_de is not None:
        K = d.coll; k = np.nonzero(K["oid"][:K.n] >= 0)[0]
        k = k[collectives_de(K, k)]
        if len(k): n += np.bincount(K["modele"][k], minlength=len(ARMES))
    return n


def _instruction_par_jour(p, d, rows, c=None):
    """Les coups d une journee de tir des lignes `rows` ( et des mortiers de la compagnie c ), par bien."""
    U = d.unites
    f = None
    if c is not None:
        def f(K, k): return U["a3"][np.maximum(K["unite"][k], 0)] == c
    return _par_calibre(_armes_par_modele(d, rows, f) * COUPS_ARR)


def _cible_munitions(p, d, b, jours_tir):
    """Ce que l armurerie de la base doit tenir : la dotation de combat de chaque arme en service ( et des vehicules ),
    plus `jours_tir` journees de tir a la frequence moyenne."""
    E = d.eff
    rows = _lignes(d); rb = rows[E["base"][rows] == b]
    def f(K, k): return K["base"][k] == b
    n = _armes_par_modele(d, rb, f)
    out = _par_calibre(n * (DOTATION_ARR + jours_tir * PART_JOURS_TIR * COUPS_ARR))
    V = d.veh
    for k in np.nonzero((V["base"][:V.n] == b) & (V["oid"][:V.n] >= 0))[0].tolist():
        for bien, q in VEHICULES[int(V["modele"][k])].armement.items(): out[bien] = out.get(bien, 0.0) + q
    return out


def _besoin_pieces(p, d, b):
    V = d.veh
    t = 0.0
    for k in range(V.n):
        if V["base"][k] == b and V["oid"][k] >= 0:
            c = VEHICULES[int(V["modele"][k])]
            t += c.pieces_t_km * PIECES_CIBLE_KM + c.reparation_t
    return t


# ================================================================== la conscription
def _eligibles(p, d, n):
    """Les hommes de 19 a 28 ans, vivants, residents, sans formation militaire, hors etudes ( sursis ), pas deja
    appeles ni exemptes, qui ne sont pas eux-memes militaires ou ministres."""
    tb = p.w.table; col = p.colonnes["habitant"]
    viv = (tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT)
    age = (p.jour - col["naissance_j"][:n]) / POP.JOURS_AN
    fm = (col["tr_qualifs"][:n] & TR.BIT["formation_militaire"]) > 0
    etud = col["tr_statut"][:n] == TR.ETUDIANT
    exclus = np.isin(tb.role[:n], [PO.CODE_ROLE[r] for r in ROLES_NON_APPELES])
    exclus |= np.isin(col["tr_statut"][:n], (TR.INVALIDE, TR.RETRAITE))      # reformes : invalidite, retraite
    return (viv & (col["sexe"][:n] == POP.HOMME) & (age >= AGE_APPEL) & (age < AGE_MAX_SURSIS) & ~fm & ~etud & ~exclus
            & (col["ar_rang"][:n] < 0))


def _appeler(p, d, installation=False):
    """Chaque matin : les nouveaux eligibles tirent leur exemption ; les autres recoivent leur jour d appel ( le jour
    meme ; le jour de l installation, les retards sont etales sur une periode d incorporation ). Puis ceux dont le jour
    est venu sont incorpores, dans la limite des lits des casernes."""
    tb = p.w.table; n = tb.n; col = p.colonnes["habitant"]
    el = _eligibles(p, d, n)
    ap = col["ar_appel"]
    nouveaux = np.nonzero(el & (ap[:n] == PAS_APPEL))[0]
    if len(nouveaux):
        rng = p.hasard("armee_installation") if installation else p.du_jour("armee_appel")
        u = rng.random(len(nouveaux))
        ex = nouveaux[u < P_EXEMPTE]; ok = nouveaux[u >= P_EXEMPTE]
        ap[ex] = EXEMPTE; d.exemptes += len(ex); p.compter("exemption_service", len(ex))
        ap[ok] = p.jour + (rng.integers(0, ETALEMENT_ARRIERE_J, len(ok)) if installation else 0)
    dus = np.nonzero(el & (ap[:n] >= 0) & (ap[:n] <= p.jour))[0]
    if not len(dus): return 0
    libres = _lits_libres(p, d)
    fait = 0
    for i in dus.tolist():
        b = max(libres, key=lambda x: (libres[x], -x)) if libres else -1
        if b < 0 or libres[b] <= 0:
            p.compter("appel_differe"); continue
        _incorporer(p, d, i, b)
        libres[b] -= 1; fait += 1
    return fait


def _lits_libres(p, d):
    """Les lits de caserne de chaque base ( domaine 13 ) moins ses conscrits presents : les militaires de carriere
    grecs logent chez eux, les appeles a la caserne."""
    E = d.eff; rows = _lignes(d)
    rows = rows[E["conscrit"][rows] == 1]
    pres = np.bincount(E["base"][rows], minlength=len(p.w.carte.par_n)) if len(rows) else np.zeros(len(p.w.carte.par_n), np.int64)
    out = {}
    for b in d.bases:
        lits = sum(IM.lits(p, x) for x in IM.batiments(p, "caserne", lieu=p.w.carte.par_n[b].id))
        out[b] = int(lits) - int(pres[b])
    return out


def _incorporer(p, d, i, b):
    """L appele entre au service : CDD de service ( le domaine le liberera au bout de 12 mois ), au plus bas taux que
    permet le domaine 4 ( le SMIC ; la solde reelle d un conscrit grec est ~ 9 euros par mois ), la compagnie
    d instruction de sa base, le programme des recrues du domaine 19."""
    tb = p.w.table; col = p.colonnes["habitant"]; w = p.w
    h = PO.Habitant(tb, i)
    lieu = w.carte.par_n[b]
    age = float((p.jour - col["naissance_j"][i]) / POP.JOURS_AN)
    TR.embaucher_contrat(p, h, TR.Etablissement(lieu, "soldat"), "soldat", TR.CDD, DUREE_SERVICE_J + MARGE_CDD_J)
    TR.fixer_taux(p, h, TR.SMIC_HORAIRE)
    col["ar_appel"][i] = APPELE
    rows = _ajouter_militaires(p, d, np.array([i], np.int64), b, False, 1, EN_INSTRUCTION, DEPART_RECRUE,
                               p.hasard("armee_recrues"))
    r = int(rows[0])
    d.eff["fin_j"][r] = p.jour + DUREE_SERVICE_J
    _affecter(p, d, r)
    ED.inscrire_formation(p, h, PROGRAMME_RECRUES)
    d.incorpores.append((p.jour, i, b, round(age, 2)))
    p.noter("incorporation", habitant=i, base=lieu.id, age=round(age, 2))


def _liberer(p, d, r):
    """Fin du service : la formation militaire est acquise ( si l epreuve du domaine 19 ne l a pas deja donnee ), le
    contrat prend fin ( chomeur, sans indemnite : il retrouve le marche du travail )."""
    E = d.eff; i = int(E["hid"][r]); tb = p.w.table
    h = PO.Habitant(tb, i)
    TR.qualifier(p, h, "formation_militaire")
    _quitter(p, d, r)
    if h.vivant and h.travail is not None: TR.rompre_contrat(p, h, "fin_service", involontaire=False)
    d.liberes.append((p.jour, i))
    p.noter("liberation_service", habitant=i, jours=int(p.jour - E["debut_j"][r]))


def _quitter(p, d, r):
    E = d.eff
    _rendre(p, d, r)
    i = int(E["hid"][r])
    if i >= 0: p.col("habitant", "ar_rang")[i] = -1
    E["statut"][r] = PARTI; E["unite"][r] = -1


# ================================================================== l affectation d un nouveau venu
def _affecter(p, d, r):
    """Une place pour la ligne r : une recrue a la compagnie d instruction de sa base ; un officier au commandement
    d une unite qui n a pas d officier ( compagnie, bataillon, section ), sinon a l etat-major du bataillon ; un soldat
    au groupe d infanterie le moins plein ( moins de 10 ), sinon dans un nouveau groupe, une nouvelle section, une
    nouvelle compagnie, un nouveau bataillon."""
    E = d.eff; U = d.unites; b = int(E["base"][r])
    n = U.n
    ub = np.nonzero(U["base"][:n] == b)[0]
    bats = [u for u in ub.tolist() if U["niveau"][u] == BATAILLON]
    if not bats:
        ile = p.w.carte.par_n[b].ile
        if ile not in d.brigades:
            d.brigades[ile] = _nouvelle_unite(d, BRIGADE, ETAT_MAJOR, d.armee_u, -1, len(d.brigades))
        bats = [_nouvelle_unite(d, BATAILLON, INFANTERIE, d.brigades[ile], b, 0)]
    if E["statut"][r] == EN_INSTRUCTION:
        ci = [u for u in ub.tolist() if U["niveau"][u] == COMPAGNIE and U["type"][u] == INSTRUCTION]
        if not ci:
            ci = [_nouvelle_unite(d, COMPAGNIE, INSTRUCTION, bats[0], b, len(_enfants(d, bats[0], COMPAGNIE)))]
        E["unite"][r] = ci[0]; E["spec"][r] = FUSILIER
        _doter(p, d, np.array([r]), "importe")
        return
    hids = E["hid"]
    if E["spec"][r] == OFFICIER:
        rows = _lignes(d)
        officiers = set(hids[rows[E["spec"][rows] == OFFICIER]].tolist())
        for niv in (COMPAGNIE, BATAILLON, SECTION):
            for u in ub.tolist():
                if U["niveau"][u] != niv or U["type"][u] == INSTRUCTION: continue
                if int(U["chef"][u]) not in officiers:
                    E["unite"][r] = u; U["chef"][u] = hids[r]
                    _doter(p, d, np.array([r]), "importe"); return
        E["unite"][r] = bats[0]
        _doter(p, d, np.array([r]), "importe"); return
    rows = _lignes_actives(d)
    rows = rows[(E["base"][rows] == b) & (E["unite"][rows] >= 0)]
    taille = np.bincount(E["unite"][rows], minlength=n) if len(rows) else np.zeros(n, np.int64)
    groupes = [u for u in ub.tolist() if U["niveau"][u] == GROUPE and U["type"][u] == INFANTERIE and taille[u] < GROUPE_MAX]
    if groupes:
        g = min(groupes, key=lambda u: (taille[u], u))
    else:
        secs = [u for u in ub.tolist() if U["niveau"][u] == SECTION and U["type"][u] == INFANTERIE
                and len(_enfants(d, u, GROUPE)) < GROUPES_PAR_SECTION]
        if secs: s = secs[0]
        else:
            comps = [u for u in ub.tolist() if U["niveau"][u] == COMPAGNIE and U["type"][u] == INFANTERIE
                     and len(_enfants(d, u, SECTION)) < SECTIONS_PAR_COMPAGNIE - 1]
            if comps: c = comps[0]
            else:
                bat = next((x for x in bats if len(_enfants(d, x, COMPAGNIE)) < COMPAGNIES_PAR_BATAILLON), None)
                if bat is None:
                    ile = p.w.carte.par_n[b].ile
                    bat = _nouvelle_unite(d, BATAILLON, INFANTERIE, d.brigades[ile], b, len(bats))
                c = _nouvelle_unite(d, COMPAGNIE, INFANTERIE, bat, b, len(_enfants(d, bat, COMPAGNIE)))
                _refaire_compagnies(d)
            s = _nouvelle_unite(d, SECTION, INFANTERIE, c, b, len(_enfants(d, c, SECTION)))
        g = _nouvelle_unite(d, GROUPE, INFANTERIE, s, b, len(_enfants(d, s, GROUPE)))
    E["unite"][r] = g
    membres = rows[E["unite"][rows] == g]
    pris = set(E["spec"][membres].tolist())
    sp = next((x for x in POSTES_GROUPE if x not in pris), FUSILIER)
    E["spec"][r] = sp
    if U["chef"][g] < 0 or sp == CHEF: U["chef"][g] = hids[r]
    _doter(p, d, np.array([r]), "importe")


# ================================================================== le matin ( 6 h 30 )
def _synchroniser(p, d):
    """Les morts et les departs ( metier change, plus a sa base, plus en emploi ) quittent les effectifs ; les
    arrivees ( embauches du domaine 4 ) y entrent ; les recrues qualifiees rejoignent un groupe ; les conscrits au
    terme de leurs 12 mois sont liberes."""
    E = d.eff; tb = p.w.table; col = p.colonnes["habitant"]
    rows = _lignes(d)
    if len(rows):
        h = E["hid"][rows]
        ro = tb.role[h]
        militaire = (ro == PO.CODE_ROLE["soldat"]) | (ro == PO.CODE_ROLE["officier"])
        reste = ((tb.vivant[h] == 1) & militaire & (tb.travail[h] == E["base"][rows])
                 & np.isin(col["tr_statut"][h], TR.EN_EMPLOI))
        for r in rows[~reste].tolist(): _quitter(p, d, r)
        rows = rows[reste]
        fin = rows[(E["conscrit"][rows] == 1) & (E["fin_j"][rows] >= 0) & (E["fin_j"][rows] <= p.jour)]
        for r in fin.tolist(): _liberer(p, d, r)
        rec = rows[(E["statut"][rows] == EN_INSTRUCTION)]
        if len(rec):
            q = (col["tr_qualifs"][E["hid"][rec]] & TR.BIT["formation_militaire"]) > 0
            for r in rec[q].tolist():
                E["statut"][r] = ACTIF
                _rendre(p, d, r)
                _affecter(p, d, r)
    n = tb.n
    base_de = np.full(len(p.w.carte.par_n), False)
    base_de[d.bases] = True
    tr = tb.travail[:n]
    ro = tb.role[:n]
    arr = np.nonzero((tb.vivant[:n] == 1) & (col["ar_rang"][:n] < 0) & (tr >= 0) & base_de[np.maximum(tr, 0)]
                     & ((ro == PO.CODE_ROLE["soldat"]) | (ro == PO.CODE_ROLE["officier"]))
                     & np.isin(col["tr_statut"][:n], TR.EN_EMPLOI))[0]
    if len(arr):
        off = tb.role[arr] == PO.CODE_ROLE["officier"]
        rows = _ajouter_militaires(p, d, arr, tr[arr], off, 0, ACTIF, DEPART, p.du_jour("armee_arrivees"))
        for r in rows.tolist(): _affecter(p, d, r)
    _recommander(d)


def effectifs_vises(p, population=None):
    """Le dimensionnement sur la population ( ratios grecs, IISS 2023 ) : { actifs, conscrits, carriere, officiers }."""
    tb = p.w.table
    pop = int((tb.vivant[:tb.n] == 1).sum()) if population is None else int(population)
    actifs = pop * PART_ACTIFS
    carriere = actifs * (1.0 - PART_CONSCRITS)
    return {"population": pop, "actifs": actifs, "conscrits": actifs * PART_CONSCRITS, "carriere": carriere,
            "officiers": carriere * PART_OFFICIERS, "soldats_carriere": carriere * (1.0 - PART_OFFICIERS)}


def _postes(p, d):
    """Les postes ouverts au domaine 4 pour chaque base : la part de la base dans les effectifs vises de carriere,
    plus ses conscrits. Au-dessus, personne n est remplace ( l armee du moteur E1 est ~ 7 fois l armee grecque : elle
    decroit par les departs, sans licenciement )."""
    v = effectifs_vises(p)
    E = d.eff; rows = _lignes(d)
    nb = max(1, len(d.bases))
    for b in d.bases:
        rb = rows[E["base"][rows] == b]
        conscrits = int((E["conscrit"][rb] == 1).sum())
        lid = p.w.carte.par_n[b].id
        TR.ouvrir_postes(p, lid, "soldat", int(round(v["soldats_carriere"] / nb)) + conscrits)
        TR.ouvrir_postes(p, lid, "officier", int(round(v["officiers"] / nb)))
    d.vise = v


def _matin(p):
    d = _dom(p)
    _synchroniser(p, d)
    _appeler(p, d)
    _postes(p, d)
    d.patr_hier = d.patr_base; d.patr_base = {}
    d.activite = {}; d.patr_jour = {}; d.cmd_jour = {}
    U = d.unites
    a_instr = CYCLE_INSTRUCTION[p.socle.calendrier.date(p.w.pas).weekday()]
    for c in range(U.n):
        if U["niveau"][c] == COMPAGNIE and U["type"][c] == INSTRUCTION: d.activite[c] = a_instr
    E = d.eff; rows = _lignes(d)
    comp = _anc(d, rows, COMPAGNIE)
    for c in d.compagnies:
        rc = rows[comp == c]
        if not len(rc): continue
        imp = d.imposee.get(c)
        if imp is not None and imp[1] >= p.jour:
            d.activite[c] = imp[0]; continue
        ctx = ContexteCompagnie(_traits_monde(p, d, c, rc))
        a = d.decideur.decider(c, ctx)
        d.activite[c] = a; d.cmd_jour[c] = a
        p.compter("decision_activite")


# ================================================================== les fonctions de la journee ( monde et scenario )
def _efficacite(E, rows): return 1.0 - 0.5 * E["fatigue"][rows]


def _effets(E, rows, action, f_mun=1.0):
    """Les effets d une journee d activite sur les lignes `rows` ( une compagnie ). f_mun : la part des munitions de tir
    obtenues ( le tir ne monte qu a proportion )."""
    if not len(rows): return
    e = _efficacite(E, rows)
    if action == TIR_A:
        E["tir"][rows] += GAIN["tir"] * f_mun * (1.0 - E["tir"][rows]) * e
        E["discipline"][rows] += GAIN["discipline"] * (1.0 - E["discipline"][rows])
    elif action == MARCHE:
        E["endurance"][rows] += GAIN["endurance"] * (1.0 - E["endurance"][rows]) * e
        E["discipline"][rows] += GAIN["discipline"] * (1.0 - E["discipline"][rows])
    elif action == PATROUILLE:
        E["perception"][rows] += GAIN["perception"] * (1.0 - E["perception"][rows]) * e
    elif action == MAINTENANCE:
        E["discipline"][rows] += GAIN["discipline"] * (1.0 - E["discipline"][rows])
    elif action == REPOS:
        E["moral_u"][rows] += MORAL_REPOS
    if action >= 0:
        E["fatigue"][rows] = np.clip(E["fatigue"][rows] + FATIGUE[action], 0.0, 1.0)
        E["stress"][rows] = np.clip(E["stress"][rows] + STRESS[action], 0.0, 1.0)


def _nuit(E, rows, moral_base):
    """La nuit de tous : sommeil ( fatigue et stress baissent ), oubli des competences non exercees, part propre du
    moral qui s eteint, fatigue lourde qui le mine ; moral = base ( la culture ) + part propre - stress ; la
    discipline suit le moral."""
    if not len(rows): return
    for k, v in OUBLI.items(): E[k][rows] *= (1.0 - v)
    lourd = E["fatigue"][rows] > FATIGUE_LOURDE
    E["moral_u"][rows] = E["moral_u"][rows] * DEMI_VIE_MORAL - MORAL_EPUISE * lourd
    E["fatigue"][rows] = np.clip(E["fatigue"][rows] - RECUP_NUIT, 0.0, 1.0)
    E["stress"][rows] = np.clip(E["stress"][rows] - DETENTE_NUIT, 0.0, 1.0)
    E["moral"][rows] = np.clip(moral_base + E["moral_u"][rows] - K_STRESS_MORAL * E["stress"][rows], 0.0, 1.0)
    cible = np.clip(0.5 + 1.5 * (E["moral"][rows] - MORAL_REF), 0.0, 1.0)
    E["discipline"][rows] = np.clip(E["discipline"][rows] + 0.05 * (cible - E["discipline"][rows]), 0.0, 1.0)
    for k in ("tir", "perception", "endurance"): E[k][rows] = np.clip(E[k][rows], 0.0, 1.0)


def _dispo(V, vk):
    """Part des vehicules en service, et part en retard d entretien."""
    if not len(vk): return 1.0, 0.0
    inter = np.array([VEHICULES[m].intervalle_km for m in V["modele"][vk].tolist()])
    return float((V["etat"][vk] == O.SERVICE).mean()), float((V["km_entretien"][vk] > inter).mean())


def _traits(E, rows, V, vk, carb_jours, mun_jours, patr_hier):
    dispo, retard = _dispo(V, vk)
    m = [float(E[k][rows].mean()) for k in ("tir", "endurance", "perception", "fatigue", "stress", "moral")]
    return m + [dispo, retard, float(np.clip(carb_jours / 10.0, 0.0, 1.0)), float(np.clip(mun_jours / 10.0, 0.0, 1.0)),
                float(np.clip(patr_hier, 0.0, 1.0))]


def _note(E, rows, V, vk, patrouilles):
    if not len(rows): return 0.0
    apt = float((E["tir"][rows].mean() + E["endurance"][rows].mean() + E["perception"][rows].mean()) / 3.0)
    dispo, _ = _dispo(V, vk)
    a, b, c, dd, e = POIDS_NOTE
    return (a * min(1.0, patrouilles / PATROUILLES_PAR_JOUR) + b * apt + c * (1.0 - float(E["fatigue"][rows].mean()))
            + dd * dispo + e * float(E["moral"][rows].mean()))


def _pannes(V, vk, rng):
    """Les vehicules qui ont roule aujourd hui tombent en panne selon leurs km et leur retard d entretien. Rend les
    lignes tombees en panne."""
    if not len(vk): return []
    u = rng.random(len(vk))
    out = []
    for j, k in enumerate(vk.tolist()):
        km = float(V["km_jour"][k])
        if km <= 0 or V["etat"][k] != O.SERVICE: continue
        c = VEHICULES[int(V["modele"][k])]
        retard = max(0.0, float(V["km_entretien"][k]) / c.intervalle_km - 1.0)
        if u[j] < min(1.0, km / c.mtbf_km * (1.0 + RETARD_PANNE * retard)):
            V["etat"][k] = O.PANNE; out.append(k)
    return out


def _maintenir(V, vk, pieces):
    """La journee de maintenance d une compagnie : chaque vehicule, dans l ordre, est repare s il est en panne et
    remis a zero de son entretien, tant que les pieces suffisent. Rend ( pieces brulees en tonnes, vehicules repares )."""
    brule, rep = 0.0, []
    for k in vk.tolist():
        c = VEHICULES[int(V["modele"][k])]
        besoin = c.pieces_t_km * float(V["km_entretien"][k]) + (c.reparation_t if V["etat"][k] != O.SERVICE else 0.0)
        if brule + besoin > pieces + EPS: continue
        brule += besoin
        if V["etat"][k] != O.SERVICE: V["etat"][k] = O.SERVICE; rep.append(k)
        V["km_entretien"][k] = 0.0
    return brule, rep


def _rouler(V, k, km):
    V["km_jour"][k] += km; V["km"][k] += km; V["km_entretien"][k] += km


def _vehicule_de_patrouille(V, vk):
    """Le premier vehicule en service de la compagnie, dans l ordre de preference ( M1114, M113, camion ). -1 aucun."""
    for m in IDX_PATROUILLEURS:
        for k in vk.tolist():
            if V["modele"][k] == m and V["etat"][k] == O.SERVICE: return k
    return -1


# ================================================================== le monde : traits, patrouilles, journee, soir
def _vehicules_de(d, c):
    V = d.veh; U = d.unites; n = V.n
    un = V["unite"][:n]
    ok = (V["oid"][:n] >= 0) & (un >= 0)
    comp = np.where(ok, U["a3"][np.maximum(un, 0)], -1)
    return np.nonzero(comp == c)[0]


def _km_patrouille(p, b):
    """Aller et retour de la base a la ville la plus proche ( la patrouille du moteur )."""
    w = p.w; base = w.carte.par_n[b]
    ville = w.carte.plus_proche(base, ("ville", "capitale"))
    return 2.0 * w.carte.km_route(base, ville), ville


def besoin_carburant(p, base):
    """Unites de carburant ( 10 l ) que brule une base par jour : deux patrouilles avec le vehicule de patrouille
    ( M1114 )."""
    b = base if isinstance(base, (int, np.integer)) else base.n
    km, _ = _km_patrouille(p, b)
    return PATROUILLES_PAR_JOUR * km * VEHICULE["m1114"].unites_par_km


def _traits_monde(p, d, c, rc):
    E = d.eff; w = p.w
    b = int(d.unites["base"][c])
    vk = _vehicules_de(d, c)
    carb = w.garnisons[w.carte.par_n[b].id]["carburant"] / max(EPS, besoin_carburant(p, b))
    arm = d.armureries[d.par_base[b]]
    besoin = _instruction_par_jour(p, d, rc, c)
    mun = min((arm.stock[d.bids[bien]] / q for bien, q in besoin.items() if q > 0), default=10.0)
    f, a = d.patr_hier.get(b, (0, 0))
    patr = f / max(1, f + a) if f + a else 1.0
    return _traits(E, rc, d.veh, vk, carb, mun, patr)


def _patrouilles(p):
    """8 h et 20 h ( remplace Monde.patrouilles ) : chaque base patrouille vers sa ville la plus proche si une de ses
    compagnies a pour activite la patrouille, si un de leurs vehicules est en service et si la garnison a le carburant
    qu il brule. Memes compteurs et memes notes que le moteur ; la cause d une annulation est dite."""
    w = p.w; d = _dom(p); V = d.veh
    for base in w.carte.de_type("base"):
        b = base.n
        g = w.garnisons[base.id]
        comps = [c for c in d.compagnies if d.unites["base"][c] == b and d.activite.get(c) == PATROUILLE]
        km, ville = _km_patrouille(p, b)
        k = -1
        for c in comps:
            k = _vehicule_de_patrouille(V, _vehicules_de(d, c))
            if k >= 0: break
        carb = km * VEHICULES[int(V["modele"][k])].unites_par_km if k >= 0 else 0.0
        cause = "aucune_troupe" if not comps else "vehicule" if k < 0 else "carburant" if g["carburant"] < carb else None
        f0, a0 = d.patr_base.get(b, (0, 0))
        if cause is None:
            g["carburant"] -= carb; w.flux["brule"]["carburant"] += carb
            _rouler(V, k, km)
            parc = p.socle.parc
            parc.user(parc.objets[int(V["oid"][k])], km / VITESSE_USAGE_KMH)
            f, a = w.patrouilles_jour.get(base.id, (0, 0)); w.patrouilles_jour[base.id] = (f + 1, a)
            w.patrouilles_faites = getattr(w, "patrouilles_faites", 0) + 1
            w.noter("patrouille", base=base.id, vers=ville.id, carburant=round(carb, 2))
            for c in comps: d.patr_jour[c] = d.patr_jour.get(c, 0) + 1
            d.patr_base[b] = (f0 + 1, a0)
        else:
            f, a = w.patrouilles_jour.get(base.id, (0, 0)); w.patrouilles_jour[base.id] = (f, a + 1)
            w.patrouilles_annulees = getattr(w, "patrouilles_annulees", 0) + 1
            w.noter("patrouille_annulee", base=base.id, cause=cause)
            d.patr_base[b] = (f0, a0 + 1)


def _ravitailler(p):
    """7 h ( remplace Monde.ravitailler_bases ) : le depot national alimente chaque garnison par convoi ; le seuil et la
    cible se comptent en jours de SON besoin reel ( ce que brulent ses vehicules de patrouille ). Le groupe d agents
    armee, s il est installe, decide comme dans le moteur."""
    w = p.w
    ga = w.agents.get("armee")
    for base in w.carte.de_type("base"):
        g = w.garnisons[base.id]
        if ga:
            besoin = w.besoin_patrouille(base)
            vise = R.decider_armee(w, ga, base)
            if g["carburant"] >= vise * besoin: continue
            q = min(C.CAPACITE_CAMION, w.publics["armee"]["carburant"], vise * besoin - g["carburant"])
        else:
            besoin = besoin_carburant(p, base)
            if g["carburant"] >= 3 * besoin: continue
            q = min(C.CAPACITE_CAMION, w.publics["armee"]["carburant"], 5 * besoin - g["carburant"])
        if q < 1: continue
        if w.lancer_convoi(w.depot_armee, base, {"carburant": q}, w.gouv, "ravitaillement_base",
                           w.marches[w.depot_armee.marche.id]):
            w.publics["armee"]["carburant"] -= q
            w.livraison_ratee[base.id] = False
            w.noter("ravitaillement_base", base=base.id, carburant=round(q, 1))
        else:
            w.livraison_ratee[base.id] = True


def _journee(p):
    """16 h : les effets de l activite de chaque compagnie. Le tir brule les munitions de l armurerie ( une journee de
    tir de chaque tireur, au prorata de ce qui reste ) et use les armes ; la maintenance brule des pieces ; les
    vehicules qui ont roule risquent la panne."""
    d = _dom(p); E = d.eff; V = d.veh; parc = p.socle.parc
    rows = _lignes(d)
    comp = _anc(d, rows, COMPAGNIE)
    rng = p.du_jour("armee_pannes")
    for c in sorted(d.activite):
        a = d.activite[c]
        rc = rows[comp == c]
        if not len(rc): continue
        b = int(d.unites["base"][c]); arm = d.armureries[d.par_base[b]]
        f = 1.0
        if a == TIR_A:
            besoin = _instruction_par_jour(p, d, rc, c)
            parts = []
            for bien in sorted(besoin):
                q = besoin[bien]
                if q <= 0: continue
                pris = _sortir(p, d, arm, bien, q, "tir_instruction")
                parts.append(pris / q)
                p.compter("tir_instruction", pris)
            f = min(parts) if parts else 0.0
            for oid, m in zip(E["arme"][rc].tolist(), E["arme_m"][rc].tolist()):
                if oid >= 0: parc.user(parc.objets[oid], f * COUPS_ARR[m] / 100.0)
        elif a == MAINTENANCE:
            vk = _vehicules_de(d, c)
            dispo = arm.stock[d.bids["pieces"]]
            brule, rep = _maintenir(V, vk, dispo)
            if brule > 0: _sortir(p, d, arm, "pieces", brule, "entretien_militaire")
            for k in rep:
                parc.mettre_en_etat(parc.objets[int(V["oid"][k])], O.SERVICE)
                p.compter("reparation_militaire")
            p.compter("maintenance_militaire", len(vk))
        _effets(E, rc, a, f)
    vk = np.nonzero((V["oid"][:V.n] >= 0) & (V["km_jour"][:V.n] > 0))[0]
    for k in _pannes(V, vk, rng):
        parc.mettre_en_etat(parc.objets[int(V["oid"][k])], O.PANNE)
        p.compter("panne_militaire")


def _moral_base(p, d, rows):
    if p.a("culture"): return p.col("habitant", "cul_moral")[d.eff["hid"][rows]].astype(np.float64)
    return np.full(len(rows), MORAL_REF)


def _soir(p):
    """22 h 40 : le moral du jour ( avant la nuit ), la note de chaque compagnie qui a decide, puis la nuit de tous."""
    d = _dom(p); E = d.eff; V = d.veh
    rows = _lignes(d)
    E["moral"][rows] = np.clip(_moral_base(p, d, rows) + E["moral_u"][rows] - K_STRESS_MORAL * E["stress"][rows], 0.0, 1.0)
    comp = _anc(d, rows, COMPAGNIE)
    notes = {}
    for c in d.compagnies:
        rc = rows[comp == c]
        if not len(rc): continue
        v = _note(E, rc, V, _vehicules_de(d, c), d.patr_jour.get(c, 0))
        notes[c] = v
        d.decideur.noter(c, v, p.jour)
    _nuit(E, rows, _moral_base(p, d, rows))
    V["km_jour"][:V.n] = 0.0
    d.serie.append({"jour": p.jour, "notes": notes, "activite": dict(d.activite), "patrouilles": dict(d.patr_jour)})
    if len(d.serie) > 400: del d.serie[0]


def _approvisionner(p):
    """9 h : une armurerie sous 10 journees de tir d avance commande de quoi en tenir 30 ( import, paye par l Etat ) ;
    ses pieces se commandent a l industrie du pays, et a l etranger pour le reste."""
    d = _dom(p); w = p.w
    for b in d.bases:
        arm = d.armureries[d.par_base[b]]
        seuil = _cible_munitions(p, d, b, JOURS_TIR_RESERVE)
        cible = _cible_munitions(p, d, b, JOURS_TIR_CIBLE)
        for bien in sorted(cible):
            s = arm.stock[d.bids[bien]]
            if s >= seuil.get(bien, 0.0): continue
            q, paye = EXT.importer_au_port(p, w.gouv, arm.stock, bien, cible[bien] - s, "import_armement", droits=False)
            if q > 0:
                d.entrees[bien] = d.entrees.get(bien, 0.0) + q
                d.depenses["munitions"] += paye; p.compter("import_munitions", q)
        besoin = _besoin_pieces(p, d, b)
        s = arm.stock[d.bids["pieces"]]
        if s < 0.5 * besoin:
            q = IND.livrer(p, "pieces", besoin - s, arm.stock, w.gouv)
            if q > 0:
                d.entrees["pieces"] = d.entrees.get("pieces", 0.0) + q
                d.depenses["pieces"] += q * IND.BIENS["pieces"][2]
            reste = besoin - arm.stock[d.bids["pieces"]]
            if reste > EPS:
                q, paye = EXT.importer_au_port(p, w.gouv, arm.stock, "pieces", reste, "import_armement", droits=False)
                if q > 0: d.entrees["pieces"] = d.entrees.get("pieces", 0.0) + q; d.depenses["pieces"] += paye


# ================================================================== l installation
MOTIFS = (("dotation_initiale_armee", "achat"), ("tir_instruction", "achat"), ("tir_combat", "achat"),
          ("entretien_militaire", "achat"), ("transfert_munitions", "achat"), ("perte_au_combat", "achat"))
COLONNES_HABITANT = (("ar_rang", np.int32, -1), ("ar_appel", np.int32, PAS_APPEL))


def installer(p):
    w = p.w; L = p.socle.livre; tb = w.table; cat = p.socle.catalogue
    d = Armee()
    p.domaines[DOMAINE] = d
    for nom, unite, eur, masse, vol, src in MUNITIONS:
        cat.declarer(nom, "munition", unite, _dr(eur), categorie_tva="normale", masse_kg=masse, volume_l=vol, source=src)
    for nom in NOMS_MUNITIONS + ("pieces",): d.bids[nom] = cat.id(nom)
    for m, nature in MOTIFS: L.declarer_motif(m, nature, DOMAINE)
    J = p.socle.journal
    J.declarer("incorporation", DOMAINE, "individuel", ("habitant", "base", "age"))
    J.declarer("liberation_service", DOMAINE, "individuel", ("habitant", "jours"))
    for t in ("decision_activite", "tir_instruction", "tir_combat", "import_munitions", "panne_militaire",
              "reparation_militaire", "maintenance_militaire", "appel_differe", "exemption_service", "arme_manquante"):
        J.declarer(t, DOMAINE, "compte")
    ch = p.colonnes["habitant"]
    for nom, dt, v in COLONNES_HABITANT: ch.ajouter(nom, dt, v)
    ch.assurer(tb.n)
    _declarer_modeles(p, d)
    d.bases = sorted(b.n for b in w.carte.de_type("base"))
    for k, b in enumerate(d.bases):
        d.armureries.append(Armurerie(b, w.carte.par_n[b].id)); d.par_base[b] = k
        lid = w.carte.par_n[b].id
        TR.declarer_employeur(p, lid, "soldat", w.gouv)
        TR.declarer_employeur(p, lid, "officier", w.gouv)
    p.socle.registre.inscrire("armureries", "administrations", _membres_armureries, None, "stock")
    ED.declarer_programme(p, PROGRAMME_RECRUES, DOMAINE, *RECRUES, public="api", allocation=0.0,
                          qualification="formation_militaire")
    # le recensement militaire : les soldats et officiers en emploi a une base
    n = tb.n; col = p.colonnes["habitant"]
    base_de = np.zeros(len(w.carte.par_n), bool); base_de[d.bases] = True
    tr = tb.travail[:n]; ro = tb.role[:n]
    ids = np.nonzero((tb.vivant[:n] == 1) & (tr >= 0) & base_de[np.maximum(tr, 0)]
                     & ((ro == PO.CODE_ROLE["soldat"]) | (ro == PO.CODE_ROLE["officier"]))
                     & np.isin(col["tr_statut"][:n], TR.EN_EMPLOI))[0]
    rng = p.hasard("armee_recensement")
    _ajouter_militaires(p, d, ids, tr[ids], ro[ids] == PO.CODE_ROLE["officier"], 0, ACTIF, DEPART, rng)
    _organiser(p, d)
    _doter(p, d, _lignes(d))
    _equipement_initial(p, d)
    d.decideur = p.decideur(POINT)
    _appeler(p, d, installation=True)
    _postes(p, d)
    w.patrouilles = RemplacePatrouilles(p)
    w.ravitailler_bases = RemplaceRavitaillement(p)
    p.routine(6.5, 60, DOMAINE, _matin)
    p.routine(9.0, 60, DOMAINE, _approvisionner)
    p.routine(16.0, 60, DOMAINE, _journee)
    p.routine(22 + 40 / 60, 60, DOMAINE, _soir)
    return d


# ================================================================== les controles
def anomalies(p):
    """Les incoherences du domaine : [ ( type, detail ) ].
      militaire_sans_unite, militaire_mort, unite_inconnue : les effectifs ;
      arme_sans_proprietaire : une arme, une optique, un vehicule du domaine dont le proprietaire n est pas une
      armurerie ; arme_inconnue : une dotation qui ne designe aucun objet vivant ; arme_doublee : un meme numero dote
      deux fois ; equipement_depasse : plus de protections ou de radios dotees que l armurerie n en a ;
      munition_hors_consommation : un stock qui n est pas depart + entrees - sorties comptees ;
      competence_hors_bornes."""
    d = _dom(p); E = d.eff; U = d.unites; parc = p.socle.parc; tb = p.w.table
    out = []
    rows = _lignes(d)
    h = E["hid"][rows]
    for r in rows[E["unite"][rows] < 0].tolist(): out.append(("militaire_sans_unite", int(E["hid"][r])))
    for r in rows[tb.vivant[h] != 1].tolist(): out.append(("militaire_mort", int(E["hid"][r])))
    for r in rows[E["unite"][rows] >= U.n].tolist(): out.append(("unite_inconnue", int(E["hid"][r])))
    arms = set(id(a) for a in d.armureries)
    mes = set(d.idx_parc)
    for o in parc.objets.values():
        if o.modele in mes and id(o.proprietaire) not in arms: out.append(("arme_sans_proprietaire", o.id))
    for (m, prop, lieu), c in parc.cohortes.items():
        if m in mes and id(prop) not in arms: out.append(("arme_sans_proprietaire", f"cohorte {parc.modeles[m].nom}"))
    vus = {}
    for champ in ("arme", "optique", "arme2"):
        for r in rows.tolist():
            oid = int(E[champ][r])
            if oid < 0: continue
            if oid not in parc.objets: out.append(("arme_inconnue", oid)); continue
            if oid in vus: out.append(("arme_doublee", oid))
            vus[oid] = r
            k = int(E[champ + "_m"][r])
            if d.idx_parc.get(parc.objets[oid].modele, (None, -2))[1] != k: out.append(("arme_inconnue", oid))
    for b in d.bases:
        arm = d.armureries[d.par_base[b]]
        rb = rows[E["base"][rows] == b]
        for champ, table in (("protection", PROTECTIONS), ("casque", PROTECTIONS), ("radio", RADIOS)):
            ks, nb = np.unique(E[champ][rb][E[champ][rb] >= 0], return_counts=True)
            for k, x in zip(ks.tolist(), nb.tolist()):
                c = parc.cohortes.get((d.mids[table[k].nom], arm, arm.lieu))
                if (c.nombre if c is not None else 0) < x: out.append(("equipement_depasse", (b, table[k].nom)))
    for bien in NOMS_MUNITIONS + ("pieces",):
        s = math.fsum(a.stock[d.bids[bien]] for a in d.armureries)
        att = (d.stock0.get(bien, 0.0) + d.entrees.get(bien, 0.0)
               - math.fsum(v for (bb, m), v in sorted(d.sorties.items()) if bb == bien))
        if abs(s - att) > 1e-6 * max(1.0, abs(att)): out.append(("munition_hors_consommation", (bien, s - att)))
    for k in ("tir", "perception", "endurance", "discipline", "fatigue", "stress", "moral"):
        x = E[k][rows]
        if len(x) and (x.min() < 0.0 or x.max() > 1.0): out.append(("competence_hors_bornes", k))
    return out


# ================================================================== le scenario de la decision
def scenario_compagnies(n=60, jours=21, mode="hasard", graine=7, taille=120):
    """La porte de decision : `n` compagnies de `taille` hommes, chacune avec son parc ( 9 M113, 3 M1114, 2 camions ),
    sa garnison et son armurerie, vivent `jours` jours avec les fonctions du domaine ( effets de l activite, pannes,
    maintenance, patrouilles, nuit, note ). Etats de depart tires ( fatigue, retards d entretien, pannes ) pour que
    chaque action puisse compter. Un scenario et pas le monde : le monde E1 n a que 6 bases, donc 6 a 12 compagnies.
    Rend le Decideur."""
    rng = np.random.default_rng(graine)
    E = Table(CHAMPS_EFFECTIFS, n * taille); r0 = E.ajouter(n * taille)
    rows_c = [np.arange(r0 + c * taille, r0 + (c + 1) * taille) for c in range(n)]
    N = n * taille
    for k, (m, s) in DEPART.items(): E[k][:N] = np.clip(m + s * rng.standard_normal(N), 0.05, 0.95)
    fat0 = rng.random(n) * 0.7
    for c in range(n):
        E["fatigue"][rows_c[c]] = np.clip(fat0[c] + 0.05 * rng.standard_normal(taille), 0.0, 1.0)
        E["stress"][rows_c[c]] = 0.1
    E["moral"][:N] = MORAL_REF; E["statut"][:N] = ACTIF
    parc_c = ["m113a1"] * 9 + ["m1114"] * 3 + ["steyr_12m18"] * 2
    V = Table(CHAMPS_VEHICULES, n * len(parc_c)); V.ajouter(n * len(parc_c))
    vk_c = []
    for c in range(n):
        ks = np.arange(c * len(parc_c), (c + 1) * len(parc_c))
        vk_c.append(ks)
        for j, nom in zip(ks.tolist(), parc_c):
            V["oid"][j] = j; V["modele"][j] = IDX_VEHICULE[nom]
            V["km_entretien"][j] = VEHICULE[nom].intervalle_km * 1.6 * rng.random()
            V["etat"][j] = O.PANNE if rng.random() < 0.15 else O.SERVICE
    km_patr = 30.0 + 40.0 * rng.random(n)
    carb = 2 * PATROUILLES_PAR_JOUR * km_patr * VEHICULE["m1114"].unites_par_km * (3.0 + 7.0 * rng.random(n))
    mun = np.full(n, 20.0)
    pieces = np.full(n, 2.0)
    patr_hier = np.ones(n)
    point = POINT
    dec = D.Decideur(point, mode, rng=np.random.default_rng(graine + 1), graine=graine)
    for jour in range(jours):
        act = np.zeros(n, np.int64)
        for c in range(n):
            x = _traits(E, rows_c[c], V, vk_c[c], carb[c] / (PATROUILLES_PAR_JOUR * km_patr[c] * VEHICULE["m1114"].unites_par_km),
                        mun[c], patr_hier[c])
            act[c] = dec.decider(c, ContexteCompagnie(x))
        prng = np.random.default_rng((graine, jour))
        for c in range(n):
            a = int(act[c]); patr = 0
            if a == PATROUILLE:
                for _ in range(PATROUILLES_PAR_JOUR):
                    k = _vehicule_de_patrouille(V, vk_c[c])
                    besoin = km_patr[c] * VEHICULES[int(V["modele"][k])].unites_par_km if k >= 0 else 0.0
                    if k >= 0 and carb[c] >= besoin:
                        carb[c] -= besoin; _rouler(V, k, km_patr[c]); patr += 1
            f = 1.0
            if a == TIR_A:
                f = min(1.0, mun[c]); mun[c] = max(0.0, mun[c] - 1.0)
            if a == MAINTENANCE:
                brule, _ = _maintenir(V, vk_c[c], pieces[c]); pieces[c] -= brule
            _effets(E, rows_c[c], a, f)
            _pannes(V, vk_c[c], prng)
            patr_hier[c] = patr / PATROUILLES_PAR_JOUR
            E["moral"][rows_c[c]] = np.clip(MORAL_REF + E["moral_u"][rows_c[c]] - K_STRESS_MORAL * E["stress"][rows_c[c]], 0.0, 1.0)
            dec.noter(c, _note(E, rows_c[c], V, vk_c[c], patr), jour)
            _nuit(E, rows_c[c], MORAL_REF)
        V["km_jour"][:V.n] = 0.0
        carb += PATROUILLES_PAR_JOUR * km_patr * VEHICULE["m1114"].unites_par_km * 0.8      # le convoi du jour
        mun = np.minimum(mun + 0.2, 20.0); pieces = np.minimum(pieces + 0.05, 2.0)
    return dec


# ================================================================== ce que le domaine donne aux autres ( 26, 27 )
def unites(p, niveau=None, base=None, type_=None):
    """Les numeros des unites, filtres par niveau ( NIVEAUX ou indice ), base ( identifiant de lieu ), type."""
    d = _dom(p); U = d.unites; n = U.n
    m = np.ones(n, bool)
    if niveau is not None: m &= U["niveau"][:n] == (NIVEAUX.index(niveau) if isinstance(niveau, str) else niveau)
    if base is not None: m &= U["base"][:n] == p.w.carte.lieux[base].n
    if type_ is not None: m &= U["type"][:n] == (TYPES.index(type_) if isinstance(type_, str) else type_)
    return np.nonzero(m)[0].tolist()


def membres(p, u, actifs_seulement=False):
    """Les habitants d une unite et de ses filles ( les officiers qui la commandent compris )."""
    d = _dom(p); E = d.eff
    rows = _lignes_actives(d) if actifs_seulement else _lignes(d)
    niv = int(d.unites["niveau"][u])
    return E["hid"][rows[_anc(d, rows, niv) == u]]


def effectif(p, u): return len(membres(p, u))


def unite(p, u):
    """Ce qu un autre domaine lit d une unite."""
    d = _dom(p); U = d.unites
    b = int(U["base"][u])
    return {"numero": u, "nom": nom_unite(p, u), "niveau": NIVEAUX[int(U["niveau"][u])], "type": TYPES[int(U["type"][u])],
            "parent": int(U["parent"][u]), "base": p.w.carte.par_n[b].id if b >= 0 else None, "chef": int(U["chef"][u]),
            "effectif": effectif(p, u), "activite": ACTIONS[d.activite[u]] if u in d.activite else None}


def unite_de(p, hid):
    r = int(p.col("habitant", "ar_rang")[hid])
    return int(_dom(p).eff["unite"][r]) if r >= 0 else -1


def chaine_de_commandement(p, hid):
    """[ ( niveau, unite, chef ) ] de l unite de `hid` jusqu a l armee."""
    d = _dom(p); U = d.unites
    u = unite_de(p, hid); out = []
    while u >= 0:
        out.append((NIVEAUX[int(U["niveau"][u])], u, int(U["chef"][u]))); u = int(U["parent"][u])
    return out


def _rangs(p, ids):
    r = p.col("habitant", "ar_rang")[np.asarray(ids, np.int64)]
    if (r < 0).any(): raise ValueError("un habitant n est pas militaire")
    return r


def grade(p, hid):
    r = _rangs(p, [hid])[0]; g = int(_dom(p).eff["grade"][r])
    return GRADES[g], GRADES_GRECS[g]


def competences(p, ids):
    """Domaine 27 : { tir, perception, endurance, discipline, fatigue, stress, moral } par habitant ( tableaux )."""
    E = _dom(p).eff; r = _rangs(p, ids)
    return {k: E[k][r].copy() for k in ("tir", "perception", "endurance", "discipline", "fatigue", "stress", "moral")}


def moral(p, ids): return _dom(p).eff["moral"][_rangs(p, ids)].copy()


def discipline_unite(p, u):
    """Le moral et la discipline d une unite : la mesure de la culture ( domaine 23 ) si elle est la, et la discipline
    propre du domaine ( instruction, fatigue )."""
    d = _dom(p); ids = membres(p, u)
    if not len(ids): return {"moral": 0.0, "discipline": 0.0, "n": 0}
    r = _rangs(p, ids)
    propre = float(d.eff["discipline"][r].mean())
    if p.a("culture"):
        from . import d23_culture as CU
        x = CU.discipline(p, ids)
        return {"moral": x["moral"], "discipline": 0.5 * (x["discipline"] + propre), "n": x["n"]}
    return {"moral": float(d.eff["moral"][r].mean()), "discipline": propre, "n": len(ids)}


def armes_de(p, hid):
    """( arme principale, optique, arme secondaire ) : noms de modeles et numeros d objets."""
    d = _dom(p); E = d.eff; parc = p.socle.parc; r = _rangs(p, [hid])[0]
    out = []
    for champ in ("arme", "optique", "arme2"):
        oid = int(E[champ][r])
        out.append((parc.modeles[parc.objets[oid].modele].nom, oid) if oid >= 0 and oid in parc.objets else (None, -1))
    return tuple(out)


def portee_utile(p, ids):
    """La portee utile de chaque tireur ( metres ) : min( portee de son arme, portee de son optique ) ; le fer sans
    optique, 0 sans arme."""
    E = _dom(p).eff; r = _rangs(p, ids)
    a = E["arme_m"][r].astype(np.int64); o = E["optique_m"][r].astype(np.int64)
    return np.where(a >= 0, np.minimum(PORTEE_ARME[np.maximum(a, 0)], PORTEE_OPTIQUE[np.where(o >= 0, o, FER)]), 0.0)


def protection(p, hid):
    """( protection du torse, casque ) : noms de modeles."""
    E = _dom(p).eff; r = _rangs(p, [hid])[0]
    k, c = int(E["protection"][r]), int(E["casque"][r])
    return (PROTECTIONS[k].nom if k >= 0 else None, PROTECTIONS[c].nom if c >= 0 else None)


def multiplicateur_letalite(p, hid, zone, menace):
    """Le multiplicateur de letalite d un impact sur `zone` ( regions du domaine 16 ) par une `menace` ( MENACES ) : le
    produit de ce que portent les protections qui couvrent la zone ( 1 : rien )."""
    if menace not in MENACES: raise ValueError(f"menace inconnue {menace!r}")
    E = _dom(p).eff; r = _rangs(p, [hid])[0]
    m = 1.0
    for champ in ("protection", "casque"):
        k = int(E[champ][r])
        if k >= 0 and zone in PROTECTIONS[k].zones: m *= PROTECTIONS[k].mult[menace]
    return m


SEUIL_ARRET = 0.2                # un multiplicateur de 0,2 ou moins : la protection ARRETE le projectile
AIS_CONTUSION = 1                # ce qui reste derriere le blindage ( contusion, « behind armour blunt trauma » ) :
#                                  AIS 1 ( a calibrer : AIS 2 pour les fortes energies )


def blesser_soldat(p, hid, zone, arme):
    """Domaine 27 : un impact de `arme` sur `zone`. Une protection qui couvre la zone et arrete la menace ( multiplicateur
    <= 0,2 ) laisse une contusion ( AIS 1 ) ; sinon l energie a la bouche ( la perte en vol est a calibrer ; 3 000 J pour
    un eclat ) donne l AIS du domaine 16, qui soigne. Rend ( cle de l affection, ISS ), ou ( None, 0 ) sans medecine."""
    if not p.a("medecine"): return None, 0
    from . import d16_medecine as MED
    a = ARME[arme]
    mult = multiplicateur_letalite(p, hid, zone, a.menace)
    if mult <= SEUIL_ARRET: ais = AIS_CONTUSION
    else: ais = MED.ais_balistique(zone, a.energie_j if a.energie_j > 0 else 3000.0)
    iss = MED.iss_depuis_ais({zone: ais})
    return MED.blesser(p, PO.Habitant(p.w.table, hid), "balistique", iss, "combat"), iss


def perception(p, ids, nuit=False):
    """Domaine 26 : la perception effective de chaque soldat ( la fatigue la reduit de moitie au plus ) et sa distance
    de detection en metres ( de jour ~ 300 m, de nuit 36 m sans jumelles : mesure Arma, a calibrer )."""
    E = _dom(p).eff; r = _rangs(p, ids)
    eff = E["perception"][r] * (1.0 - 0.5 * E["fatigue"][r])
    return eff, eff * 2.0 * (DETECTION_NUIT_M if nuit else DETECTION_JOUR_M)


def detection_unite(p, u, nuit=False):
    """La detection d une unite est celle de son meilleur guetteur : `knowsAbout` est une connaissance de camp ( Arma,
    02/08 ). Rend la distance en metres."""
    ids = membres(p, u, actifs_seulement=True)
    if not len(ids): return 0.0
    return float(perception(p, ids, nuit)[1].max())


def radios(p, u):
    """Domaine 26 : { modele : nombre } des radios dotees dans l unite, et sa portee ( km, la meilleure )."""
    d = _dom(p); E = d.eff
    ids = membres(p, u)
    r = _rangs(p, ids) if len(ids) else np.zeros(0, np.int64)
    ks = E["radio"][r]; ks = ks[ks >= 0]
    out = {RADIOS[k].nom: int(c) for k, c in zip(*np.unique(ks, return_counts=True))}
    return out, max((RADIOS[k].portee_km for k in set(ks.tolist())), default=0.0)


def armurerie(p, base):
    """L Armurerie d une base ( identifiant de lieu ) : son `stock` est un Stock du socle ( domaine 26 : les convois
    de munitions y deposent et y prennent par le grand livre )."""
    d = _dom(p); return d.armureries[d.par_base[p.w.carte.lieux[base].n]]


def stocks_munitions(p, base=None):
    """{ base : { bien : quantite } } des armureries."""
    d = _dom(p); out = {}
    for a in d.armureries:
        if base is not None and a.lieu != base: continue
        out[a.lieu] = {b: a.stock[d.bids[b]] for b in NOMS_MUNITIONS + ("pieces",)}
    return out


def depot_national(p):
    """Domaine 26 : ( lieu du depot de l armee, carburant qu il tient ) - le stock public du moteur d ou partent les
    convois des garnisons."""
    w = p.w
    return w.depot_armee.id, w.publics["armee"]["carburant"]


def carburant(p, base):
    """( unites de carburant de la garnison, besoin par jour, jours d autonomie )."""
    w = p.w; g = w.garnisons[base]["carburant"]; bz = besoin_carburant(p, w.carte.lieux[base])
    return g, bz, g / max(EPS, bz)


def tirer(p, base, bien, q, motif="tir_combat"):
    """Domaine 27 : des munitions tirees ( ou perdues, motif perte_au_combat, nature perdu ) a l armurerie d une base :
    une sortie comptee, jamais un stock ecrit a la main. Rend ce qui a ete tire."""
    if motif not in ("tir_combat", "tir_instruction", "perte_au_combat"): raise ValueError(f"motif {motif!r}")
    d = _dom(p)
    q = _sortir(p, d, armurerie(p, base), bien, q, motif, "perdu" if motif == "perte_au_combat" else "consomme")
    if motif == "tir_combat": p.compter("tir_combat", q)
    return q


def transferer_munitions(p, de, vers, bien, q):
    """Domaine 26 : d une armurerie a une autre ( un convoi livre ) : un deplacement du grand livre."""
    d = _dom(p)
    return p.socle.livre.deplacer(armurerie(p, de).stock, armurerie(p, vers).stock, d.bids[bien], q, "transfert_munitions")


def perdre_objet(p, oid, puits="detruit"):
    """Domaine 27 : une arme, une optique ou un vehicule detruit ( ou mis au rebut ). Le soldat qui la portait n en a
    plus ; un vehicule sort du parc de son unite."""
    d = _dom(p); E = d.eff; V = d.veh; parc = p.socle.parc
    o = parc.objets[oid]
    for champ in ("arme", "optique", "arme2"):
        m = E[champ][:E.n] == oid
        E[champ][:E.n][m] = -1; E[champ + "_m"][:E.n][m] = -1
    V["oid"][:V.n][V["oid"][:V.n] == oid] = -1
    K = d.coll; K["oid"][:K.n][K["oid"][:K.n] == oid] = -1
    for lst in d.ratelier.values():
        if oid in lst: lst.remove(oid)
    parc.sortir(o, puits)


def monter_optique(p, hid, nom):
    """Domaine 27 : change l optique de l arme principale de `hid` ( « fer » la demonte ). L ancienne retourne au
    ratelier ; la nouvelle vient du ratelier, de la reserve ou d un achat. Rend la portee utile qui en resulte."""
    d = _dom(p); E = d.eff; r = int(_rangs(p, [hid])[0]); b = int(E["base"][r]); parc = p.socle.parc
    oid = int(E["optique"][r])
    if oid >= 0 and oid in parc.objets:
        d.ratelier.setdefault((b, parc.modeles[parc.objets[oid].modele].nom), []).append(oid)
    E["optique"][r] = -1; E["optique_m"][r] = -1
    if nom != "fer":
        oid = _tirer_objet(p, d, b, nom, "importe")
        if oid >= 0: E["optique"][r] = oid; E["optique_m"][r] = IDX_OPTIQUE[nom]
    return float(portee_utile(p, [hid])[0])


def imposer_activite(p, compagnie, action, jours=1):
    """Un ordre ( domaine 27, ou une porte ) : l activite de la compagnie pour `jours` jours, sans decision ni note."""
    a = ACTIONS.index(action) if isinstance(action, str) else int(action)
    _dom(p).imposee[compagnie] = (a, p.jour + int(jours) - 1)


def compagnies(p):
    return list(_dom(p).compagnies)


def vehicules(p, base=None, u=None):
    """[ ( numero d objet, modele, base, unite, km, etat ) ] des vehicules militaires vivants."""
    d = _dom(p); V = d.veh; out = []
    for k in range(V.n):
        if V["oid"][k] < 0: continue
        b = int(V["base"][k])
        if base is not None and p.w.carte.par_n[b].id != base: continue
        if u is not None and d.unites["a" + str(int(d.unites["niveau"][u]))][int(V["unite"][k])] != u: continue
        out.append((int(V["oid"][k]), VEHICULES[int(V["modele"][k])].nom, p.w.carte.par_n[b].id, int(V["unite"][k]),
                    float(V["km"][k]), O.ETATS[int(V["etat"][k])]))
    return out


def acheter_vehicules(p, base, modele, n, u=-1):
    """Domaines 26 et 27 : `n` vehicules militaires neufs achetes a l etranger par l Etat ( domaine 7, declarer_import ;
    le domaine 14 ne vend que des modeles civils ), au parc de la base, affectes a l unite `u`. Rend le nombre achete."""
    d = _dom(p); b = p.w.carte.lieux[base].n
    fait = 0
    for _ in range(int(n)):
        if not _importer_objets(p, d, modele, 1): break
        _ajouter_vehicule(p, d, modele, b, u, "importe"); fait += 1
    return fait


def positions_du_parc(p, base):
    """Les decalages ( dx, dy ) en metres des vehicules d une base au parc : jamais deux au meme point ( lecon payee :
    deux vehicules crees au meme point se detruisent ; domaine 14 )."""
    n = len(vehicules(p, base=base))
    return TP.emplacements(n)


def ordre_de_mouvement(p, u, destination):
    """Pour le pont vers Arma : la destination est posee AVANT l ordre de marche ( `moveTo` seul ne bouge pas un agent,
    22/09 ). Rend la suite d ordres a envoyer, dans l ordre."""
    return [("setDestination", u, destination), ("moveTo", u, destination)]


def classname(p, hid):
    """Le classname Arma d un militaire, selon sa specialite ( arma_preuve = None )."""
    r = _rangs(p, [hid])[0]
    return ARMA_SOLDAT[int(_dom(p).eff["spec"][r])]


def conscrits(p):
    """( en service, en instruction, exemptes, incorpores depuis l installation, liberes )."""
    d = _dom(p); E = d.eff; rows = _lignes(d)
    return (int((E["conscrit"][rows] == 1).sum()), int((E["statut"][rows] == EN_INSTRUCTION).sum()), d.exemptes,
            len(d.incorpores), len(d.liberes))


def depenses(p):
    """Ce que l armee a fait depenser a l Etat depuis l installation ( drachmes ), hors solde ( domaine 4 ) et carburant
    des convois ( moteur )."""
    return dict(_dom(p).depenses)
