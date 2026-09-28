"""DOMAINE 26 - ARMEE ( B ) : LOGISTIQUE MILITAIRE, RENSEIGNEMENT, COMMANDEMENT.

FICHE
1. Classes. LOGISTIQUE : Depot ( un depot militaire, national ou de brigade : un Stock du socle - munitions, pieces,
   rations, carburant de brigade, kerosene ; famille `depots_militaires` du registre, sans argent ), Demande ( une
   expedition a faire : origine, destination, cargaison, moyen, echeance ), Soutien ( l etat du domaine ). Les trois
   lignes de soutien de l OTAN : la GARNISON ( premiere ligne : l armurerie du domaine 25 pour les munitions, les pieces
   et les rations ; la garnison du moteur pour le gazole ), la BRIGADE ( deuxieme ligne : un Depot par ile, a la base
   la plus peuplee, qui est son etat-major ), la NATION ( troisieme ligne : un Depot au depot de l armee du moteur,
   storage01 a Altis ; son gazole est le stock public w.publics["armee"] du moteur, d ou partent deja les convois des
   garnisons ). Le bien ration_combat ( declare ici : le domaine 25 ne l a pas fait ). RENSEIGNEMENT : Camp ( un camp :
   nom, sa cellule de croyance au domaine 22, ses stations d ecoute, la portee radio de ses hommes quand ce ne sont
   pas ceux du domaine 25 ), ENTITES ( une table en colonnes : les elements poses d un camp - position, ile, posture,
   taille, vitesse ; le domaine 27 y pose l adversaire ), CONNAISSANCE ( une table en colonnes : ce qu un CAMP sait
   d une cible - position crue, erreur a l observation, date, source, confiance, observateur ), `vus` ( la memoire
   bornee de QUI a vu QUOI : soldat, cible, pas, distance ). COMMANDEMENT : ORDRES ( une table : emetteur, destinataire,
   contenu, parametres voulus et compris, heure d emission, heure prevue, heure de reception, moyen, etat, plan,
   echeance ), les PLANS ( suites d ordres dates avec echeances ), les brouillages, les mouvements et la dislocation
   des unites deployees sans ordre. SANTE : l hopital militaire ( domaine 17 ), les helicopteres d evacuation et les
   ambulances militaires ( objets du Parc ).
   Un JOUR DE COMBAT est l unite des dotations : par garnison, une dotation de combat du domaine 25 ( armes et
   armement de bord ), KM_COMBAT km par vehicule, une ration par homme ( a calibrer : les taux de planification varient
   avec l intensite ).
2. Invariants et ce que le domaine detient. BIENS : les stocks de ses depots ( munitions, pieces, rations,
   carburant, kerosene ), qui n entrent que par la dotation du jour de l installation ( importee sans paiement, comme
   les stocks de depart du moteur et du domaine 25 ), par achat ( energie : gazole et kerosene ; industrie : pieces ;
   exterieur : munitions et rations, payes par l Etat ), par requisition ( agriculture, indemnisee ) ; ils ne sortent
   que CONSOMMES sous un motif du domaine ( consommation_campagne, rotation_rations, carburant_convoi_militaire,
   vol_evasan ) ou tires par l API du domaine 25 ( tir_combat ). Tout deplacement passe par le grand livre, et le
   domaine tient son propre livre de flux par bien : sur le PERIMETRE militaire ( depots, armureries, garnisons, stock
   public de l armee, convois militaires et lots en route ), chaque routine du domaine change le perimetre d exactement
   ses flux comptes ( porte test_conservation ) ; une livraison a une armurerie est comptee aux entrees du domaine 25,
   dont les anomalies restent vides. CONNAISSANCE : une ligne a toujours une source, une date passee, un observateur
   quand elle vient d une observation ; un camp ne sait rien de lui-meme ; ZERO EST UNE ABSENCE ( `connaissance` rend
   None, jamais un « vu a 0 » : lecon d Arma, 13/09 ). ORDRES : aucun n est recu avant son emission ; un ordre perdu
   n est jamais recu. ARGENT : aucune caisse ; l Etat paie achats, fret et indemnites par le grand livre.
3. Decision `ravitaillement_garnison` ( le commandant logistique de chaque garnison - l officier S4 du bataillon -
   chaque matin a 6 h 40 ) : attendre, ou demander a la brigade un camion de 5 t par la route ou par la mer, charge
   d abord de carburant, de munitions, de vivres, ou a parts egales ( mixte ). Traits ( ce que voit le S4 : le compte
   rendu logistique LOGREP de sa garnison, l ordre d operation, le bulletin des itineraires, la capitainerie, l etat du
   depot de brigade, le suivi des mouvements ) : autonomie en carburant, en munitions et en vivres sur leur dotation,
   posture, route ouverte, mer ouverte, garnison sur une autre ile, remplissage du depot de brigade par classe, convoi
   deja en route. La demande part comme un ORDRE ( radio, telephone ou estafette : delai, frictions ) ; le convoi part
   a sa reception. Note ( horizon 3 jours : un convoi arrive dans le jour par la route, en deux jours par la mer, et
   sa charge se consomme ensuite ) : chaque soir, pour CETTE garnison, la moyenne du remplissage des trois classes
   ( borne a 1 ) moins, par classe en rupture ce jour ( besoin du jour non couvert ), un tiers ; moins le cout du
   convoi le jour du choix ( 0,05 la route, 0,10 la mer ). Regle ( la plus faible autonomie d abord ) : rien sous 80 %
   de sa dotation, ou en paix un convoi deja en route -> attendre ; sinon la classe de plus faible autonomie EN JOURS
   que la brigade peut fournir, par la route sur la meme ile ( coupee : attendre ), par la mer ailleurs, meme fermee
   ( le lot attend a quai : prepositionner ). Temoin bete : tout ravitailler a parts egales ( mixte ), par la route ou
   par la mer. MESURE DU 26/09 ( scenario, graines 7, 8, 9 ) : regle -0,044, -0,025, -0,062 contre temoin -0,052,
   -0,027, -0,068 ; la premiere regle, qui attendait la reouverture de la mer, perdait ( -0,063, -0,038, -0,086 ) :
   le temoin prepositionnait au port sans le savoir. Mer ouverte : regle 0,067 contre temoin 0,063 ( graine 7 ). Le
   28/09, carburant de garnison a 3 jours ( CIBLE_GARNISON ) : porte test_decision, regle 0,168 contre temoin 0,157,
   hasard -0,186 ( part du choix 0,053, p 0,005 ; avant : -0,044, -0,052, -0,368 ). La
   porte de decision est un SCENARIO ( scenario_ravitaillement : 120 garnisons, 12 brigades, crise, mer fermee dix
   jours, routes coupees au hasard ) : le monde E1 n a que 6 bases.
4. Evenements. Individuels : convoi_militaire ( de, vers, tonnes ), evacuation ( habitant, moyen, minutes ),
   presence_militaire ( lieu, camp, taille : ce que la population voit passer, une NOUVELLE du domaine 22 ).
   Comptes : decision_ravitaillement, demande_ravitaillement, convoi_militaire_refuse, livraison_militaire,
   rupture_ravitaillement, achat_militaire, rotation_rations, ordre_emis, ordre_recu, ordre_perdu, ordre_mal_compris,
   observation, contact, interception, dislocation_h.
5. Liens. Armee ( 25, dependance dure ) : effectifs, unites, vehicules ( ses camions Steyr et ses conducteurs font
   les convois militaires ), armureries ( `armurerie`, les entrees comptees ), `tirer` ( la consommation de munitions
   au combat ), `perception` ( la portee de chaque guetteur ), `radios` ( la portee d une unite ), `membres`,
   `imposer_activite` ( un ordre ACTIVITE recu ), `ordre_de_mouvement` ( la destination avant la marche ). Logistique
   ( 15, dure ) : `recevoir_convoi` ( motif convoi_militaire, arrivee par son `_arrivees` ), `route_praticable`,
   `duree_convoi_pas`, `lancer_convoi` ( un transporteur civil quand aucun camion militaire n est libre ), `envoyer` et
   `recevoir_lot` ( la mer ), `fermer_la_mer` lu par `_lg( p ).mer_ouverte`. Hopitaux ( 17, dure ) :
   `hopital_militaire`, `affecter_personnel`, `admettre( ..., delai_pas= )`. Medias ( 22, dure ) : `inscrire_groupe`
   ( une cellule par camp ), `constater` et `informer` ( ce qu un camp sait, avec SON lieu : une erreur de position ),
   `croyance` ( ce que la population et les medias font savoir a un camp ), `declarer_nouvelle` ( presence_militaire ),
   `telecom_ok` ( le telephone ). Energie ( 11 ) : `vendre_produit` ( gazole au stock public de l armee, kerosene au
   depot national ). Industrie ( 10 ) : `livrer` ( pieces ). Exterieur ( 7 ) : `importer_au_port` ( munitions,
   rations ). Agriculture ( 9, optionnelle ) : `stocks_vivres`, `requisitionner` ( vivres de crise ). Politique ( 24,
   optionnelle ) : `politique_de_defense` n est pas lue ( la posture est un ordre, pas un vote ). Ne remplace aucune
   methode du moteur. API en fin de fichier pour le domaine 27.
6. Portes : tests_d26_armee_soutien.py ( 11 portes, 26/09 : toutes passent en ~ 1 min 40 ). Grand livre du
   perimetre sonde autour de chaque routine ( 0 ecart sur ~ 1 000 appels, falsificateurs vus ) ; base isolee par une
   route coupee : rupture en gazole et en vivres au jour predit ( 0 ecart ), mer fermee dans le scenario ( 0 ecart sur
   17 garnisons d ile ) ; transmission radio 1 pas, telephone 2, estafette au delai recalcule ; connaissance de camp
   ( un guetteur, tout le camp ; pas l autre camp ; None hors du cone ou de la portee ) ; erreur de position croissante
   avec la distance ( 7,7 m a 25 m, 31,7 m a 250 m ) ; decision ( part du choix 0,036, p 0,005 ) ; evacuation ;
   requisition ; porte commune ; cout.
7. Arma. Convois militaires : le camion du domaine 25 ( B_Truck_01_transport_F ), la DESTINATION posee avant l ordre de
   marche et un decalage de depart par vehicule ( `a_incarner`, domaine 14 `emplacements` ) ; les departs d une meme
   origine sont etales d un pas ( 10 min ). Helicoptere d evacuation : UH-1H de CUP ( CUP_B_UH1D_GER_KSK, a verifier ) ;
   ambulance : CUP_B_HMMWV_Ambulance_USA ( a verifier ) ; arma_preuve = None partout. Lecons payees : `knowsAbout` est
   une connaissance de CAMP ( 02/08 ) - la detection d un seul guetteur fait la connaissance de tout son camp, et la
   memoire de qui a vu quoi reste a part ; un zero de `knowsAbout` est une ABSENCE d entree ( 13/09 ) - ici None ; le
   cone du regard domine la distance ( 02/08 : rien a 50 m sur le flanc, vu a 300 m devant ) ; la detection d un
   groupe est tout ou rien ( 04/08 ) ; `moveTo` seul ne bouge pas un agent ( 22/09 ) - `ordre_de_mouvement` ; une
   attente sans ordre disloque le detachement ( 18/09 ) - une unite deployee sans ordre TENIR compte ses heures de
   dislocation.
8. Cout. Le matin : les besoins de chaque garnison ( une passe vectorisee sur les vehicules et les effectifs, puis les
   munitions de chaque base par le domaine 25 ), un point de decision par garnison. Chaque heure : les demandes en
   attente, les mouvements, les unites deployees ( vides en temps de paix ). A 12 h : la consommation des garnisons
   en posture. A 18 h 30 : les croyances des camps au domaine 22 ( un sujet ). Le soir : une note par garnison, les achats
   de la nation, la rotation des rations. Rien ne suit la population ; le cout suit les bases, les ordres et les
   entites posees. Installation lineaire. Mesure du 26/09 ( test_cout, coeur Rust, 10 001 habitants ) : routines
   propres 2 ms par jour ( une journee de paix et une journee avec deux garnisons au combat ), 0,6 % d une journee du
   moteur seul ( 0,30 s ) ; installation 0,002 s a 10 000 habitants, 0,006 s a 100 000 ( x2,8 : elle suit les bases,
   pas les habitants ). A 50 millions : les besoins du matin passent sur les vehicules et les effectifs ( ~ 1 % des
   habitants ), le reste suit les bases et les ordres."""
import math
from collections import deque
import numpy as np
from .. import config as C, population as PO, economie as E1
from ..socle import decision as D, objets as O, biens as B
from . import pays as P, d07_exterieur as EXT, d10_industrie as IND, d11_energie as ENE, d14_transport as TP
from . import d15_logistique as LG, d17_hopitaux as HM, d22_medias as MED, d25_armee as A

DOMAINE = "armee_soutien"
EUROS = P.EUROS_PAR_DRACHME
EPS = 1e-9
PAS_H = 60 // C.MINUTES_PAR_PAS
PAS_JOUR = C.PAS_PAR_JOUR
MIN_PAS = C.MINUTES_PAR_PAS
AUTONOMIE_MAX_J = 99.0


def _dr(euros): return euros / EUROS


# ================================================================== la logistique : classes, jour de combat, dotations
CLASSES = ("carburant", "munitions", "vivres")          # classes III, V et I de l OTAN
CARB, MUN, VIV = range(3)
MIXTE = 3                                                # un chargement a parts egales ( le temoin )
RATION = "ration_combat"
KCAL_RATION = 3600.0
MASSE_RATION_KG, VOLUME_RATION_L = 1.6, 3.0
PRIX_RATION_EUR = 12.0
CONSERVATION_RATION_J = 3 * 365.0
SOURCE_RATION = ("ration de combat individuelle ( type MRE de l armee americaine : trois repas, ~ 3 600 kcal, 1,6 a "
                 "1,9 kg emballee, trois ans a 27 degres, Defense Logistics Agency ) ; prix et masse de la ration grecque "
                 "a calibrer")
# Le jour de combat ( a calibrer ; ordres de grandeur des taux de planification ) : chaque vehicule roule KM_COMBAT km,
# chaque arme tire MUN_PAR_JOUR dotation de combat, chaque homme mange RATIONS_PAR_JOUR ration.
KM_COMBAT = {"char": 60.0, "vtt": 80.0, "blinde_leger": 120.0, "camion": 150.0}
MUN_PAR_JOUR = 1.0
RATIONS_PAR_JOUR = 1.0
UPK = np.array([v.unites_par_km for v in A.VEHICULES])          # unites de gazole ( 10 l ) par km, par modele
KMJ = np.array([KM_COMBAT[v.categorie] for v in A.VEHICULES])
# Les dotations reglementaires en jours de combat ( lignes de soutien de l OTAN : premiere ligne a l unite, deuxieme a
# la brigade, reserve de guerre nationale ; l OTAN demandait 30 jours de soutien en reserve - a verifier ) : a calibrer.
# 28/09 : la premiere ligne garde plusieurs jours AU-DESSUS du minimum pour operer - « un bataillon se deploie avec trois
# jours d approvisionnement de combat » ( vivres, carburant, munitions : J. Auran, « Combat supply operations »,
# European Security & Defence, 8 mars 2024 ; les « jours d approvisionnement », days of supply, de la doctrine ). Le
# carburant etait a 1 jour, pile sur le seuil d autonomie de l embuscade et de la defense ( domaine 27 : 1 jour ) : une
# garnison pleine y etait au bord, et le premier litre consomme refusait la tactique ( test_preconditions, 4 variantes
# sur 7 du tronc 24ac15d ). Carburant et vivres a 3 jours ; les munitions restent la dotation de combat de l armurerie
# du domaine 25 ( 1 jour ; 3 jours au reel, a calibrer avec lui ) : le domaine 27 lit leur seuil a part.
#   https://euro-sd.com/2024/03/articles/36994/combat-supply-operations/
CIBLE_GARNISON = (3.0, 1.0, 3.0)                         # carburant, munitions ( la dotation de combat ), vivres
JOURS_BRIGADE = 3.0
JOURS_NATIONAL = 30.0
SEUIL_DEMANDE = 0.8                                      # une classe sous 80 % de sa dotation se redemande
PIECES_NATIONAL = 2.0                                    # la nation garde deux fois les pieces de toutes les bases
POSTURES = ("paix", "alerte", "combat")
TAUX_POSTURE = (0.0, 0.25, 1.0)                          # jours de combat consommes par jour ( a calibrer )
# Le convoi militaire : un camion Steyr 12M18 du domaine 25, 5 t de charge ( sa FICHE ) ; une demande de garnison est un
# camion, une demande de depot un convoi d au plus CONVOI_MAX camions.
CAMION = "steyr_12m18"
IDX_CAMION = A.IDX_VEHICULE[CAMION]
CHARGE_CAMION_KG = 5000.0
CONVOI_MAX = 6
EXPIRATION_J = 1                                         # une demande qui n a pas trouve de camion en un jour tombe
CONDUCTEURS = (A.CONDUCTEUR, A.FUSILIER)                 # le conducteur, a defaut un fusilier de la base

# ================================================================== la sante militaire
LITS_PAR_MILITAIRE = 0.01            # ~ 1 lit pour 100 militaires ( hopital general militaire grec, ordre de grandeur )
LITS_MIN = 10
HELICOS_PAR_BRIGADE = 2
VITESSE_HELICO_KMH = 180.0           # UH-1H en croisiere ( ~ 200 km/h au plus )
CONSO_HELICO_U_H = 32.0              # ~ 320 l/h de Jet A-1 ( unites de 10 l ), a calibrer
HEURES_VOL_RESERVE = 60.0            # par helicoptere, a la nation ( 30 jours x 2 h )
PREPARATION_HELICO_MIN = 15.0
CHARGEMENT_MIN = 10.0
VITESSE_AMBULANCE_KMH = 50.0
PREPARATION_AMBULANCE_MIN = 20.0
HEURE_DOREE_MIN = 60.0               # la « golden hour » : un blesse grave soigne dans l heure

# ================================================================== le commandement
MOYENS = ("radio", "telephone", "estafette")
RADIO_M, TELEPHONE_M, ESTAFETTE_M = range(3)
DELAI_RADIO_MIN = 10.0               # chiffrer, emettre, accuser reception ( a calibrer )
DELAI_TELEPHONE_MIN = 20.0           # standards du reseau civil ( a calibrer )
PREPARATION_ESTAFETTE_MIN = 15.0
VITESSE_ESTAFETTE_KMH = (45.0, 25.0)  # jour, nuit ( motocycliste ; a calibrer )
KM_MER_ESTAFETTE = 120.0             # un pli vers une autre ile ( la traversee du moteur )
VITESSE_MER_KMH = 25.0
P_RETARD = (0.05, 0.08, 0.15)        # frictions ( a calibrer ) : un retard de 1 a RETARD_MAX_PAS pas
RETARD_MAX_PAS = (3, 3, 12)
P_MAL = (0.04, 0.03, 0.01)           # un ordre mal compris ( la voix pire que l ecrit ), accru par la fatigue du chef
P_PERTE = (0.0, 0.0, 0.01)           # une estafette qui n arrive pas
DECALAGE_MAL_M = 500.0
CONTENUS = ("mouvement", "activite", "tenir", "demande", "demande_depot")
MOUVEMENT, ACTIVITE, TENIR, DEMANDE, DEMANDE_DEPOT = range(5)
ETATS_ORDRE = ("en_route", "recu", "perdu")
EN_ROUTE, RECU, PERDU = range(3)
VITESSE_MARCHE_KMH, VITESSE_MOTORISEE_KMH = 4.0, 30.0
RAYON_BASE_M = 300.0                 # une unite revenue a moins de 300 m de sa base est rentree au quartier

# ================================================================== le renseignement
SOURCES = ("aucune", "observation", "patrouille", "radio", "population", "medias")
AUCUNE, OBSERVATION, PATROUILLE, RADIO_S, POPULATION, MEDIAS = range(6)
POSTURES_CIBLE = ("debout", "accroupi", "vehicule", "couche")
# La portee d un guetteur ( domaine 25 `perception` : 550 m de jour, 300 m de nuit, moins avec la fatigue ) vaut pour
# un homme DEBOUT REGARDE ; accroupi ~ 0,42 ( nuit du 19/09 : fiable sous 125 m contre ~ 300 debout ), un vehicule
# ~ 3 fois ( a calibrer ). Hors du cone du regard ( 70 degres, le banc P2 ), un dixieme ( 02/08 : rien a 50 m sur le
# flanc ) ; un guetteur qui balaie sans regard impose, la moitie ( a calibrer : le levier est ou regarder et combien de
# temps balayer, 18/09 ). La detection est binaire ( 04/08 : tout ou rien ), sans hasard.
# Couche : 0,105 ( 27/09 ). Le moteur d Arma donne a l animation couchee une taille visible de 0,15, contre 0,6
# accroupi et 0,9 debout ( `visibleSize`, CfgMovesMaleSdr : AmovPpneMstpSrasWrflDnon, AmovPknlMwlkSrasWrflDf,
# AmovPercMwlkSrasWrflDf ) ; on garde le 0,42 MESURE de l accroupi et le rapport d Arma couche / accroupi, 0,25 :
# un homme couche est vu a ~ 58 m de jour par un guetteur moyen, ~ 32 m de nuit ( la doctrine place l embuscade a
# 25-100 m de sa zone de destruction ).
F_POSTURE = np.array([1.0, 0.42, 3.0, 0.42 * 0.15 / 0.6])
DEMI_CONE = math.radians(35.0)
F_PERIPHERIE = 0.04   # 27/09 : avec la portee d Arma ( 550 m de jour, 1 100 m au meilleur guetteur ), 0,1 voyait a 55-110 m
                      # sur le flanc ; 0,04 garde la mesure du 02/08 ( rien a 50 m ) pour tout guetteur : 44 m au plus
F_BALAYAGE = 0.5
# L erreur de position ( a calibrer ) : 5 m, plus 10 % de la distance dans l axe ( l oeil estime mal les distances ),
# 2 % en travers ; une goniometrie radio ~ 3 degres ( 5 % de la distance ) ; une rumeur donne un lieu ( ~ 1,5 km ).
SIGMA0_M = 5.0
K_DISTANCE = 0.10
K_LATERAL = 0.02
K_GONIO = 0.05
SIGMA_LIEU_M = 1500.0
CONF_SOURCE = {OBSERVATION: 0.95, PATROUILLE: 0.9, RADIO_S: 0.6}
OUBLI_J = 7                          # une connaissance de plus de 7 jours est oubliee
VUS_MAX = 50000
RAYON_TEMOINS_M = 2000.0             # la population d un lieu voit passer ce qui passe a moins de 2 km
PORTEE_ENTITE_M = (550.0, 300.0)     # la portee d un homme d un autre camp : celle d un soldat du domaine 25 moyen
CAMP_NATIONAL = "armee_nationale"
SUJET_PRESENCE = "presence_militaire"
SPEC_PRESENCE = (-0.6, True, 0.35, 0.10, "log", 20, "somme")   # sujet du domaine 22 ( valence ... ), a calibrer
CIBLE_UNITE0 = 1 << 40               # une cible qui est une unite du domaine 25 : CIBLE_UNITE0 + numero d unite

# ================================================================== la decision
HORIZON = 3
ACTIONS = ("attendre", "route_carburant", "route_munitions", "route_vivres", "route_mixte", "mer_carburant",
           "mer_munitions", "mer_vivres", "mer_mixte")
ATTENDRE = 0
ROUTE0, MER0 = 1, 5
COUT_ROUTE, COUT_MER = 0.05, 0.10
POIDS_RUPTURE = 1.0
TRAITS = (("carburant", "LOGREP de la garnison : jours de combat de gazole, sur la dotation"),
          ("munitions", "LOGREP : jours de combat de munitions a l armurerie ( le calibre le plus court ), sur la dotation"),
          ("vivres", "LOGREP : jours de vivres, sur la dotation"),
          ("posture", "ordre d operation de la brigade : 0 paix, 0,25 alerte, 1 combat"),
          ("route_ouverte", "bulletin des itineraires de la police militaire"),
          ("mer_ouverte", "avis de la capitainerie : les navires partent-ils"),
          ("autre_ile", "carte : la garnison est sur une autre ile que son depot"),
          ("depot_carburant", "etat du depot de brigade : gazole sur sa dotation"),
          ("depot_munitions", "etat du depot de brigade : munitions sur leur dotation"),
          ("depot_vivres", "etat du depot de brigade : vivres sur leur dotation"),
          ("convoi_en_route", "suivi des mouvements : un convoi deja parti vers la garnison"))
T_CARB, T_MUN, T_VIV, T_POST, T_ROUTE, T_MER, T_ILE, T_DC, T_DM, T_DV, T_CONV = range(len(TRAITS))


class ContexteGarnison:
    __slots__ = ("traits",)

    def __init__(self, traits): self.traits = traits


def _observer(ctx): return ctx.traits


def _regle(x, ctx):
    """La plus faible autonomie ( en jours ) d abord, parmi ce que la brigade peut fournir ; la route sur l ile, la mer
    ailleurs, MEME FERMEE : le lot attend a quai et part au premier navire ( prepositionner au port ; premiere mesure,
    une regle qui attendait la reouverture perdait contre le temoin, qui prepositionne sans le savoir ). En paix, on
    attend le convoi deja en route ; au combat, on garde le flux plein."""
    if x[T_CONV] >= 0.5 and x[T_POST] < 0.5: return ATTENDRE
    rempli = [x[T_CARB], x[T_MUN], x[T_VIV]]
    dispo = [x[T_DC], x[T_DM], x[T_DV]]
    cands = [c for c in range(3) if rempli[c] < SEUIL_DEMANDE and dispo[c] > 0.05]
    if not cands: return ATTENDRE
    c = min(cands, key=lambda k: (rempli[k] * CIBLE_GARNISON[k], k))       # l autonomie en JOURS, pas le remplissage
    if x[T_ILE] < 0.5: return ROUTE0 + c if x[T_ROUTE] >= 0.5 else ATTENDRE
    return MER0 + c


def _temoin(x, ctx, rng):
    """Tout ravitailler a parts egales, par le seul moyen possible."""
    return ROUTE0 + MIXTE if x[T_ILE] < 0.5 else MER0 + MIXTE


POINT = D.PointDeDecision(
    "ravitaillement_garnison", DOMAINE, TRAITS, ACTIONS, _observer, _regle, _temoin,
    "chaque soir, pour CETTE garnison : moyenne du remplissage des trois classes ( borne a 1 ) moins un tiers par classe "
    "en rupture ce jour ; moins le cout du convoi le jour du choix ( 0,05 route, 0,10 mer )", HORIZON)


def _action(a):
    """( moyen : None, route ou mer ; classe premiere : 0 a 2, ou MIXTE )."""
    if a == ATTENDRE: return None, None
    return ("route", a - ROUTE0) if a < MER0 else ("mer", a - MER0)


def _repartir(deficits_kg, cap_kg, premiere, ordre):
    """Les kg de chaque classe dans un camion de `cap_kg` : a parts egales ( MIXTE ), ou la classe `premiere` d abord puis
    les autres dans `ordre` ( la plus faible autonomie d abord ). Jamais plus que le deficit."""
    out = [0.0, 0.0, 0.0]
    if premiere == MIXTE:
        for c in range(3): out[c] = min(max(0.0, deficits_kg[c]), cap_kg / 3.0)
        return out
    reste = cap_kg
    for c in [premiere] + [k for k in ordre if k != premiere]:
        q = min(max(0.0, deficits_kg[c]), reste)
        out[c] = q; reste -= q
        if reste <= EPS: break
    return out


def _note_jour(rempli, ruptures):
    return float(np.mean(np.clip(rempli, 0.0, 1.0))) - POIDS_RUPTURE * ruptures / 3.0


# ================================================================== les tables ( structures de tableaux )
CHAMPS_ENTITES = (("camp", np.int16, -1), ("x", np.float64, 0.0), ("y", np.float64, 0.0), ("ile", np.int16, 0),
                  ("posture", np.int8, 0), ("taille", np.int32, 1), ("vitesse", np.float64, 1.4),
                  ("vivant", np.int8, 1), ("unite", np.int32, -1), ("lieu", np.int32, -1))
CHAMPS_CONNAISSANCE = (("camp", np.int16, -1), ("cible", np.int64, -1), ("x", np.float64, 0.0), ("y", np.float64, 0.0),
                       ("ile", np.int16, 0), ("sigma", np.float64, 0.0), ("vitesse", np.float64, 0.0),
                       ("t", np.int64, -1), ("source", np.int8, AUCUNE), ("conf", np.float64, 0.0),
                       ("observateur", np.int64, -1), ("n_obs", np.int32, 0), ("taille", np.float64, 0.0),
                       ("fait", np.int64, -1), ("actif", np.int8, 0))
CHAMPS_ORDRES = (("camp", np.int16, -1), ("emetteur", np.int64, -1), ("de", np.int64, -1), ("vers", np.int64, -1),
                 ("contenu", np.int8, 0), ("a", np.float64, 0.0), ("b", np.float64, 0.0), ("c", np.float64, 0.0),
                 ("xa", np.float64, 0.0), ("xb", np.float64, 0.0), ("xc", np.float64, 0.0),
                 ("t_emis", np.int64, -1), ("t_prevu", np.int64, -1), ("t_recu", np.int64, -1), ("moyen", np.int8, 0),
                 ("etat", np.int8, EN_ROUTE), ("compris", np.int8, 1), ("retard", np.int32, 0), ("km", np.float64, 0.0),
                 ("plan", np.int32, -1), ("echeance", np.int64, -1))


# ================================================================== les detenteurs et l etat
class Depot:
    """Un depot militaire : un Stock du socle. `cible` : { identifiant de bien : quantite } de sa dotation. Il ne detient
    pas d argent : l Etat paie. Le depot national est aussi le proprietaire des helicopteres d evacuation ; son gazole
    est le stock public de l armee du moteur ( w.publics["armee"] ), d ou partent deja les convois des garnisons."""
    __slots__ = ("k", "niveau", "lieu", "ile", "brigade", "base", "stock", "cible")

    def __init__(self, k, niveau, lieu, ile, brigade, base):
        self.k, self.niveau, self.lieu, self.ile, self.brigade, self.base = k, niveau, lieu, ile, brigade, base
        self.stock = B.Stock()
        self.cible = {}


class Demande:
    """Une expedition : de ( type, cle ) a ( type, cle ), par route ou mer. type : depot ( numero ) ou base ( numero de
    lieu ). cargo : { nom de bien : quantite voulue }."""
    __slots__ = ("id", "origine", "dest", "cargo", "src", "dst", "moyen", "pas", "expire", "cle", "camions")

    def __init__(self, id, origine, dest, cargo, src, dst, moyen, pas, expire, cle, camions=1):
        self.id, self.origine, self.dest, self.cargo, self.src, self.dst = id, origine, dest, cargo, src, dst
        self.moyen, self.pas, self.expire, self.cle, self.camions = moyen, pas, expire, cle, camions


class Camp:
    """Un camp : sa cellule de croyance au domaine 22 ( son etat-major ), ses stations d ecoute ( x, y, ile, portee en
    m ), la portee radio de ses hommes s ils ne sont pas du domaine 25, et s il est vu par la population."""
    __slots__ = ("nom", "cellule", "national", "cote", "portee_radio_km", "ecoutes", "visible")

    def __init__(self, nom, cellule, national, cote, portee_radio_km, visible):
        self.nom, self.cellule, self.national, self.cote = nom, cellule, national, cote
        self.portee_radio_km, self.ecoutes, self.visible = float(portee_radio_km), [], bool(visible)


class Soutien:
    """L etat du domaine."""
    __slots__ = ("depots", "national", "depot_de_base", "bases", "bataillon_de", "brigade_de_base", "ile_de_base",
                 "besoins", "posture", "demandes", "prochaine_demande", "en_route", "lots", "camion_libre",
                 "chauffeur_libre", "flux", "ruptures", "rupt_jour", "livraisons", "serie", "decideur", "cmd",
                 "ids", "vivres", "camps", "ent", "conn", "conn_idx", "vus", "ordres", "plans", "brouillages",
                 "radio_hs", "portees", "pos_unite", "mouvements", "deployes", "sans_ordre_h", "tenir", "ordres_arma",
                 "hopital", "helicos", "helico_libre", "ambulances", "amb_libre", "evacuations", "mids",
                 "pos_lieux", "ile_lieu", "cibles_carb", "presence", "requisitions", "dernier_depart")

    def __init__(self):
        self.depots, self.national = [], None
        self.depot_de_base, self.bases, self.bataillon_de, self.brigade_de_base, self.ile_de_base = {}, [], {}, {}, {}
        self.besoins = {}            # base -> ( gazole, { munition : q }, rations ) par jour de combat
        self.posture = {}            # base -> ( posture, dernier jour )
        self.demandes = []           # Demande en attente
        self.prochaine_demande = 0
        self.en_route = {}           # numero de convoi -> ( destination ( type, cle ), demande, camion ou -1 )
        self.lots = {}               # numero de lot du domaine 15 -> ( destination, depot d origine )
        self.camion_libre, self.chauffeur_libre = {}, {}
        self.flux = {}               # ( bien, entree | sortie, motif ) -> quantite : le livre du domaine
        self.ruptures = []           # ( jour, base, classe )
        self.rupt_jour = {}          # base -> classes en rupture aujourd hui
        self.livraisons = {}         # base -> ( jour, kg ) livres
        self.serie = []
        self.decideur = None
        self.cmd = {}
        self.ids = {}
        self.vivres = []             # ( identifiant de bien, jours-homme par unite )
        self.camps = []
        self.ent = A.Table(CHAMPS_ENTITES, 16)
        self.conn = A.Table(CHAMPS_CONNAISSANCE, 64)
        self.conn_idx = {}           # ( camp, cible ) -> ligne
        self.vus = deque(maxlen=VUS_MAX)   # ( pas, camp, observateur, cible, distance m )
        self.ordres = A.Table(CHAMPS_ORDRES, 64)
        self.plans = []
        self.brouillages = []        # ( camp brouilleur, x, y, ile, rayon m, jusqu au pas )
        self.radio_hs = set()        # ( camp, unite ) sans radio
        self.portees = {}            # ( camp, unite ) -> km, le jour
        self.pos_unite = {}          # ( camp, unite ) -> ( x, y, ile ) quand elle a quitte sa base
        self.mouvements = {}         # ( camp, unite ) -> ( x0, y0, x1, y1, ile, pas depart, pas arrivee )
        self.deployes = set()
        self.sans_ordre_h = {}
        self.tenir = {}              # ( camp, unite ) -> jusqu au pas
        self.ordres_arma = deque(maxlen=2000)
        self.hopital = None
        self.helicos, self.helico_libre, self.ambulances, self.amb_libre = [], {}, {}, {}
        self.evacuations = []
        self.mids = {}
        self.pos_lieux = None
        self.ile_lieu = None
        self.cibles_carb = 0.0       # le gazole vise au stock public de l armee
        self.presence = False        # une nouvelle presence_militaire a-t-elle ete notee
        self.requisitions = []
        self.dernier_depart = {}     # lieu d origine -> pas du dernier depart ( etaler les departs : un pas d ecart )


def _dom(p): return p.domaines[DOMAINE]
def _membres_depots(w): return w.pays.domaines[DOMAINE].depots


def _compter_flux(d, bien, sens, motif, q):
    if q > 0.0:
        k = (bien, sens, motif); d.flux[k] = d.flux.get(k, 0.0) + q


# ================================================================== les stocks : qui tient quoi
def _contenant(p, d, genre, cle, bien):
    """Le stock ( Stock du socle ou dictionnaire du moteur vu par le grand livre ) qui tient `bien` chez ce detenteur."""
    w = p.w
    if genre == "depot":
        dep = d.depots[cle]
        if dep.niveau == "national" and bien == "carburant": return EXT.StockE1(w.publics["armee"], p.socle.catalogue)
        return dep.stock
    lid = w.carte.par_n[cle].id
    if bien == "carburant": return EXT.StockE1(w.garnisons[lid], p.socle.catalogue)
    return A.armurerie(p, lid).stock


def _quantite(p, d, genre, cle, bien):
    w = p.w
    if genre == "depot":
        dep = d.depots[cle]
        if dep.niveau == "national" and bien == "carburant": return w.publics["armee"].get("carburant", 0.0)
        return dep.stock[d.ids[bien]]
    lid = w.carte.par_n[cle].id
    if bien == "carburant": return w.garnisons[lid].get("carburant", 0.0)
    return A.armurerie(p, lid).stock[d.ids[bien]]


def _jours_vivres(d, stock):
    """Les jours-homme de vivres d un Stock : rations, et vivres requisitionnes comptes en calories."""
    return math.fsum(stock[b] * j for b, j in d.vivres)


def _entrer(p, d, genre, cle, bien, q, motif):
    """Une entree dans le perimetre ( dotation, achat ) : le grand livre l importe, le domaine la compte."""
    L = p.socle.livre
    q = L.importer(_contenant(p, d, genre, cle, bien), d.ids[bien], q, motif)
    _compter_flux(d, bien, "entree", motif, q)
    if genre == "base" and bien in A.NOMS_MUNITIONS + ("pieces",): _entree_armurerie(p, bien, q)
    return q


def _entree_armurerie(p, bien, q):
    """Le domaine 25 compte les entrees de ses armureries ( sa porte munition_hors_consommation )."""
    a = A._dom(p)
    a.entrees[bien] = a.entrees.get(bien, 0.0) + q


def _sortir(p, d, genre, cle, bien, q, motif, nature="consomme"):
    L = p.socle.livre
    q = L.puits(_contenant(p, d, genre, cle, bien), d.ids[bien], q, nature, motif)
    _compter_flux(d, bien, "sortie", motif, q)
    return q


def _deplacer(p, d, de, vers, bien, q, motif):
    """Un deplacement entre deux detenteurs du perimetre ( ( genre, cle ) ) : le grand livre ; une armurerie qui recoit le
    compte au domaine 25."""
    L = p.socle.livre
    q = L.deplacer(_contenant(p, d, de[0], de[1], bien), _contenant(p, d, vers[0], vers[1], bien), d.ids[bien], q, motif)
    if vers[0] == "base" and bien in A.NOMS_MUNITIONS + ("pieces",): _entree_armurerie(p, bien, q)
    return q


# ================================================================== les besoins et l autonomie
def _besoins(p, d):
    """Par garnison : ce que consomme un jour de combat - gazole ( unites de 10 l ) de ses vehicules, munitions ( une
    dotation de combat par arme et l armement de bord ), rations ( une par militaire present )."""
    a = A._dom(p); E = a.eff; V = a.veh
    nlieux = len(p.w.carte.par_n)
    rows = A._lignes(a)
    eff = np.bincount(E["base"][rows], minlength=nlieux)
    nv = V.n
    ok = V["oid"][:nv] >= 0
    mod = np.maximum(V["modele"][:nv], 0)
    carb = np.bincount(V["base"][:nv][ok], weights=(KMJ[mod] * UPK[mod])[ok], minlength=nlieux) if nv else np.zeros(nlieux)
    for b in d.bases:
        mun = A._cible_munitions(p, a, b, 0)
        d.besoins[b] = (float(carb[b]), {k: v * MUN_PAR_JOUR for k, v in sorted(mun.items()) if v > 0},
                        float(eff[b]) * RATIONS_PAR_JOUR)


def _stocks_base(p, d, b):
    """( gazole, { munition : q }, jours-homme de vivres ) de la garnison."""
    w = p.w; lid = w.carte.par_n[b].id
    arm = A.armurerie(p, lid)
    return (w.garnisons[lid].get("carburant", 0.0), {k: arm.stock[d.ids[k]] for k in A.NOMS_MUNITIONS},
            _jours_vivres(d, arm.stock))


def _autonomie_classes(besoins, stocks):
    """Jours de combat de chaque classe ( bornes a AUTONOMIE_MAX_J ; un besoin nul : le maximum )."""
    nc, nm, nv = besoins; sc, sm, sv = stocks
    ac = sc / nc if nc > EPS else AUTONOMIE_MAX_J
    am = min((sm.get(k, 0.0) / q for k, q in nm.items() if q > EPS), default=AUTONOMIE_MAX_J)
    av = sv / nv if nv > EPS else AUTONOMIE_MAX_J
    return np.minimum(np.array([ac, am, av]), AUTONOMIE_MAX_J)


def autonomie(p, base):
    """Jours de combat de carburant, de munitions et de vivres d une garnison ( identifiant de lieu de sa base, ou
    numero d une unite du domaine 25 : celle de sa base ), et le minimum."""
    d = _dom(p)
    b = _base_n(p, base)
    a = _autonomie_classes(d.besoins[b], _stocks_base(p, d, b))
    return {"carburant": float(a[CARB]), "munitions": float(a[MUN]), "vivres": float(a[VIV]), "min": float(a.min())}


def _base_n(p, base):
    if isinstance(base, str): return p.w.carte.lieux[base].n
    u = int(base)
    return int(A._dom(p).unites["base"][u])


def _remplissage_depot(p, d, k):
    """La part de sa dotation que tient un depot, par classe."""
    dep = d.depots[k]
    out = []
    for c, biens in ((CARB, ("carburant",)), (MUN, A.NOMS_MUNITIONS), (VIV, (RATION,))):
        cib = [(b, dep.cible.get(d.ids[b], 0.0)) for b in biens]
        cib = [(b, q) for b, q in cib if q > EPS]
        if not cib: out.append(1.0); continue
        out.append(min(min(1.0, _quantite(p, d, "depot", k, b) / q) for b, q in cib))
    return out


# ================================================================== l installation des depots et des dotations
def _cible_garnison(d, b):
    nc, nm, nv = d.besoins[b]
    return nc * CIBLE_GARNISON[CARB], {k: q * CIBLE_GARNISON[MUN] for k, q in nm.items()}, nv * CIBLE_GARNISON[VIV]


def _poser_cibles(p, d):
    """Les dotations des depots : la brigade tient JOURS_BRIGADE jours de ses garnisons, la nation JOURS_NATIONAL jours de
    toutes, les pieces du domaine 25, le kerosene des helicopteres."""
    a = A._dom(p)
    tot = {}
    for dep in d.depots:
        if dep.niveau != "brigade": continue
        acc = {}
        for b in d.bases:
            if d.depot_de_base[b] != dep.k: continue
            nc, nm, nv = d.besoins[b]
            acc["carburant"] = acc.get("carburant", 0.0) + nc
            for k, q in nm.items(): acc[k] = acc.get(k, 0.0) + q
            acc[RATION] = acc.get(RATION, 0.0) + nv
            acc["pieces"] = acc.get("pieces", 0.0) + A._besoin_pieces(p, a, b)
        dep.cible = {d.ids[k]: q * (JOURS_BRIGADE if k != "pieces" else 1.0) for k, q in sorted(acc.items())}
        for k, q in acc.items(): tot[k] = tot.get(k, 0.0) + q
    nat = d.national
    nat.cible = {d.ids[k]: q * (JOURS_NATIONAL if k != "pieces" else PIECES_NATIONAL) for k, q in sorted(tot.items())}
    nat.cible[d.ids["kerosene"]] = len(d.helicos) * HEURES_VOL_RESERVE * CONSO_HELICO_U_H
    d.cibles_carb = nat.cible.get(d.ids["carburant"], 0.0)


def _dotation_initiale(p, d):
    """Le jour de l installation : chaque detenteur est porte a sa dotation, importee sans paiement ( comme les stocks
    de depart du moteur et du domaine 25 )."""
    motif = "dotation_initiale_soutien"
    for b in d.bases:
        cc, cm, cv = _cible_garnison(d, b)
        sc, sm, sv = _stocks_base(p, d, b)
        if cc - sc > EPS: _entrer(p, d, "base", b, "carburant", cc - sc, motif)
        if cv - sv > EPS: _entrer(p, d, "base", b, RATION, cv - sv, motif)
    for dep in d.depots:
        for bid, q in sorted(dep.cible.items()):
            nom = p.socle.catalogue[bid].nom
            s = _quantite(p, d, "depot", dep.k, nom)
            if q - s > EPS: _entrer(p, d, "depot", dep.k, nom, q - s, motif)


# ================================================================== la consommation et la rotation
def poser_posture(p, base, posture, jours=None):
    """Domaine 27, portes : la posture d une garnison ( paix, alerte, combat ) pour `jours` jours ( sans fin par defaut ).
    En alerte ou au combat, la garnison consomme chaque jour a 12 h la part d un jour de combat de sa posture."""
    d = _dom(p); b = _base_n(p, base)
    k = POSTURES.index(posture) if isinstance(posture, str) else int(posture)
    d.posture[b] = (k, p.jour + int(jours) - 1 if jours is not None else 10 ** 9)


def _posture(p, d, b):
    k, fin = d.posture.get(b, (0, -1))
    return k if fin >= p.jour else 0


def _consommer_vivres(p, d, genre, cle, jours_homme, motif):
    """Consomme `jours_homme` de vivres, rations d abord, puis les vivres requisitionnes. Rend ce qui a ete consomme."""
    reste = jours_homme; fait = 0.0
    for bid, j in d.vivres:
        if reste <= EPS: break
        nom = p.socle.catalogue[bid].nom
        s = _quantite(p, d, genre, cle, nom)
        if s <= 0.0: continue
        q = _sortir(p, d, genre, cle, nom, min(s, reste / j), motif)
        fait += q * j; reste -= q * j
    return fait


def _consommer(p):
    """12 h : chaque garnison en alerte ou au combat consomme sa part d un jour de combat ; une classe dont le besoin du
    jour n est pas couvert est en RUPTURE ce jour."""
    d = _dom(p); w = p.w
    for b in d.bases:
        k = _posture(p, d, b)
        f = TAUX_POSTURE[k]
        if f <= 0.0: continue
        nc, nm, nv = d.besoins[b]
        lid = w.carte.par_n[b].id
        manque = set()
        q = f * nc
        if q > EPS and _sortir(p, d, "base", b, "carburant", q, "consommation_campagne", "brule") < q * (1 - 1e-9):
            manque.add(CARB)
        for bien, n in nm.items():
            q = f * n
            s = _quantite(p, d, "base", b, bien)
            pris = A.tirer(p, lid, bien, min(q, s), "tir_combat")
            _compter_flux(d, bien, "sortie", "tir_combat", pris)
            if pris < q * (1 - 1e-9): manque.add(MUN)
        q = f * nv
        if q > EPS and _consommer_vivres(p, d, "base", b, q, "consommation_campagne") < q * (1 - 1e-9): manque.add(VIV)
        if manque:
            d.rupt_jour.setdefault(b, set()).update(manque)
            for c in sorted(manque):
                d.ruptures.append((p.jour, b, c))
                p.compter("rupture_ravitaillement")


def _rotation(p, d):
    """Le soir : une ration se garde trois ans ; l armee consomme chaque jour 1 / 1 095 de son stock a l exercice pour ne
    jamais le laisser perimer ( a calibrer )."""
    r = d.ids[RATION]
    for b in d.bases:
        s = _quantite(p, d, "base", b, RATION)
        if s > 0:
            p.compter("rotation_rations", _sortir(p, d, "base", b, RATION, s / CONSERVATION_RATION_J, "rotation_rations"))
    for dep in d.depots:
        s = dep.stock[r]
        if s > 0:
            p.compter("rotation_rations",
                      _sortir(p, d, "depot", dep.k, RATION, s / CONSERVATION_RATION_J, "rotation_rations"))


def _approvisionner_nation(p, d):
    """Le soir : le depot national sous SEUIL_DEMANDE de sa dotation achete de quoi la retrouver ( l Etat paie ) : gazole
    et kerosene a la raffinerie, pieces a l industrie, munitions et rations a l etranger."""
    w = p.w; nat = d.national; motif = "achat_militaire"
    for bid, cib in sorted(nat.cible.items()):
        nom = p.socle.catalogue[bid].nom
        s = _quantite(p, d, "depot", nat.k, nom)
        if s >= SEUIL_DEMANDE * cib: continue
        manque = cib - s
        if nom in ("carburant", "kerosene"):
            q = ENE.vendre_produit(p, w.gouv, nom, manque, w.publics["armee"] if nom == "carburant" else nat)
        elif nom == "pieces":
            q = IND.livrer(p, "pieces", manque, nat.stock, w.gouv)
            if manque - q > EPS:
                q += EXT.importer_au_port(p, w.gouv, nat.stock, "pieces", manque - q, "import_armement", droits=False)[0]
        else:
            q = EXT.importer_au_port(p, w.gouv, nat.stock, nom, manque, "import_armement", droits=False)[0]
        _compter_flux(d, nom, "entree", motif, q)
        if q > 0: p.compter("achat_militaire", q)


# ================================================================== les convois militaires
def _nouvelle_demande(p, d, origine, dest, cargo, src, dst, moyen, cle, camions=1):
    dem = Demande(d.prochaine_demande, origine, dest, cargo, src, dst, moyen, p.w.pas, p.w.pas + EXPIRATION_J * PAS_JOUR,
                  cle, camions)
    d.prochaine_demande += 1
    d.demandes.append(dem)
    p.compter("demande_ravitaillement")
    return dem


def _masse(p, bien): return LG.masse_kg(p, bien)


def _demande_garnison(p, d, b, classe, moyen):
    """La brigade recoit la demande d une garnison : un camion charge d abord de `classe` ( MIXTE : a parts egales ), le
    reste de la place pour les autres classes, la plus faible d abord ; jamais plus que le deficit a la dotation ni que
    ce que tient le depot."""
    k = d.depot_de_base[b]
    cc, cm, cv = _cible_garnison(d, b)
    sc, sm, sv = _stocks_base(p, d, b)
    dispo = {nom: _quantite(p, d, "depot", k, nom) for nom in ("carburant", RATION) + A.NOMS_MUNITIONS}
    q_carb = min(max(0.0, cc - sc), dispo["carburant"])
    q_mun = {nom: min(max(0.0, q - sm.get(nom, 0.0)), dispo[nom]) for nom, q in cm.items()}
    q_viv = min(max(0.0, cv - sv), dispo[RATION])
    kg = [q_carb * _masse(p, "carburant"), math.fsum(q * _masse(p, nom) for nom, q in sorted(q_mun.items())),
          q_viv * _masse(p, RATION)]
    a = _autonomie_classes(d.besoins[b], (sc, sm, sv))
    ordre = sorted(range(3), key=lambda c: (a[c], c))
    alloue = _repartir(kg, CHARGE_CAMION_KG, classe, ordre)
    cargo = {}
    if alloue[CARB] > EPS: cargo["carburant"] = q_carb * alloue[CARB] / kg[CARB]
    if alloue[MUN] > EPS:
        for nom, q in sorted(q_mun.items()):
            if q > EPS: cargo[nom] = q * alloue[MUN] / kg[MUN]
    if alloue[VIV] > EPS: cargo[RATION] = q_viv * alloue[VIV] / kg[VIV]
    if not cargo: return None
    dep = d.depots[k]
    return _nouvelle_demande(p, d, dep.lieu, p.w.carte.par_n[b].id, cargo, ("depot", k), ("base", b), moyen, b)


def _demande_depot(p, d, k, classe):
    """La nation recoit la demande d un depot de brigade : un convoi d au plus CONVOI_MAX camions, de quoi remettre la
    classe a sa dotation ( MIXTE : toutes )."""
    dep = d.depots[k]; nat = d.national
    biens = {CARB: ("carburant",), MUN: A.NOMS_MUNITIONS + ("pieces",), VIV: (RATION,)}
    classes = (CARB, MUN, VIV) if classe == MIXTE else (classe,)
    cargo = {}
    for c in classes:
        for nom in biens[c]:
            cib = dep.cible.get(d.ids[nom], 0.0)
            q = min(max(0.0, cib - dep.stock[d.ids[nom]]), _quantite(p, d, "depot", nat.k, nom))
            if q > EPS: cargo[nom] = q
    if not cargo: return None
    kg = math.fsum(q * _masse(p, n) for n, q in sorted(cargo.items()))
    n = min(CONVOI_MAX, max(1, math.ceil(kg / CHARGE_CAMION_KG - 1e-9)))
    f = min(1.0, n * CHARGE_CAMION_KG / max(EPS, kg))
    cargo = {nom: q * f for nom, q in cargo.items()}
    return _nouvelle_demande(p, d, nat.lieu, dep.lieu, cargo, ("depot", nat.k), ("depot", k), "route", -1 - k, n)


def _camions_libres(p, d, b):
    """Les camions Steyr en service de la base `b` qui ne roulent pas, dans l ordre."""
    V = A._dom(p).veh; n = V.n; pas = p.w.pas
    ks = np.nonzero((V["base"][:n] == b) & (V["modele"][:n] == IDX_CAMION) & (V["oid"][:n] >= 0)
                    & (V["etat"][:n] == O.SERVICE))[0].tolist()
    return [k for k in ks if d.camion_libre.get(k, -1) <= pas]


def _chauffeur(p, d, b):
    """Un conducteur de la base, present et libre ( a defaut un fusilier ), ou -1."""
    a = A._dom(p); E = a.eff; pas = p.w.pas
    rows = A._lignes_actives(a)
    rb = rows[E["base"][rows] == b]
    for sp in CONDUCTEURS:
        for r in rb[E["spec"][rb] == sp].tolist():
            h = int(E["hid"][r])
            if d.chauffeur_libre.get(h, -1) <= pas: return h
    return -1


def _base_des_camions(p, d, dem):
    """Les camions d un convoi viennent de la base du depot de brigade concerne ( son bataillon logistique )."""
    if dem.src[0] == "depot" and d.depots[dem.src[1]].base >= 0: return d.depots[dem.src[1]].base
    if dem.dst[0] == "depot": return d.depots[dem.dst[1]].base
    return d.depots[d.depot_de_base[dem.dst[1]]].base


def _depart(d, origine, pas):
    """Le pas de depart d un vehicule : jamais le meme pas qu un autre vehicule de la meme origine ( etaler les departs :
    le cout d un monde incarne est le mouvement simultane ; deux vehicules crees au meme point se detruisent )."""
    t = max(int(pas), d.dernier_depart.get(origine, -1) + 1)
    d.dernier_depart[origine] = t
    return t


def _lancer_militaire(p, d, dem):
    """Un convoi de camions militaires pour la demande : route ouverte, camion et conducteur libres, gazole du depot
    d origine ( ou de la garnison des camions ). Les camions partent un pas apres l autre. Rend vrai s il est parti."""
    w = p.w; carte = w.carte; L = p.socle.livre; cat = p.socle.catalogue
    o, t = carte.lieux[dem.origine], carte.lieux[dem.dest]
    if not LG.route_praticable(p, o, t):
        p.compter("convoi_militaire_refuse"); return False
    cargo = {}
    for nom, q in sorted(dem.cargo.items()):
        q = min(q, _quantite(p, d, dem.src[0], dem.src[1], nom))
        if q > EPS: cargo[nom] = q
    if not cargo: return True                    # plus rien a porter : la demande tombe
    bc = _base_des_camions(p, d, dem)
    camions = _camions_libres(p, d, bc)[:dem.camions]
    km = carte.km_route(o, t)
    if not camions:
        return _lancer_civil(p, d, dem, cargo, o, t)
    kg = math.fsum(q * _masse(p, n) for n, q in sorted(cargo.items()))
    f = min(1.0, len(camions) * CHARGE_CAMION_KG / max(EPS, kg))
    parts = [{n: q * f / len(camions) for n, q in cargo.items()} for _ in camions]
    aller, retour = LG.duree_convoi_pas(p, o, t, km)
    gaz = 2.0 * km * A.VEHICULE[CAMION].unites_par_km
    V = A._dom(p).veh; parc = p.socle.parc
    parti = False
    for j, (k, part) in enumerate(zip(camions, parts)):
        h = _chauffeur(p, d, bc)
        if h < 0: break
        src_gaz = dem.src if _quantite(p, d, dem.src[0], dem.src[1], "carburant") >= gaz else ("base", bc)
        if gaz > EPS and _quantite(p, d, src_gaz[0], src_gaz[1], "carburant") < gaz: break
        if gaz > EPS: _sortir(p, d, src_gaz[0], src_gaz[1], "carburant", gaz, "carburant_convoi_militaire", "brule")
        depart = _depart(d, o.id, w.pas)
        w.n_convoi += 1
        cv = E1.Convoi(w.n_convoi, o, t, {}, depart, depart + aller, w.gouv, MOTIF_CONVOI, h)
        w.convois.append(cv)
        src = EXT.StockE1(cv.cargaison, cat)
        for nom, q in sorted(part.items()):
            L.deplacer(_contenant(p, d, dem.src[0], dem.src[1], nom), src, d.ids[nom], q, "chargement_militaire")
        d.en_route[cv.id] = (dem.dst, dem.id, k)
        d.camion_libre[k] = depart + aller + retour
        d.chauffeur_libre[h] = depart + aller + retour
        A._rouler(V, k, 2.0 * km)
        parc.user(parc.objets[int(V["oid"][k])], 2.0 * km / A.VITESSE_USAGE_KMH)
        t_ = math.fsum(q * _masse(p, n) for n, q in sorted(part.items())) / 1000.0
        p.noter("convoi_militaire", de=o.id, vers=t.id, tonnes=round(t_, 3))
        parti = True
    if not parti: p.compter("convoi_militaire_refuse")
    return parti


def _lancer_civil(p, d, dem, cargo, o, t):
    """A defaut de camion militaire : un transporteur civil du domaine 15 ( chauffeur a son poste, camion, gazole de la
    station, fret paye par l Etat ). Sa cargaison ne sert qu a choisir le camion : elle est videe puis chargee par le
    grand livre."""
    w = p.w; cat = p.socle.catalogue; L = p.socle.livre
    kg, m3 = LG.charge(p, cargo)
    tr = LG._lg(p).par_capitale.get(o.marche.id)
    if tr is None: p.compter("convoi_militaire_refuse"); return False
    ck, cm = LG.capacite_libre(p, tr)
    f = min(1.0, ck / max(EPS, kg), cm / max(EPS, m3) if m3 > EPS else 1.0) * (1.0 - 1e-9)
    if f <= EPS: p.compter("convoi_militaire_refuse"); return False
    part = {n: q * f for n, q in cargo.items()}
    cv = LG.lancer_convoi(p, o, t, dict(part), w.gouv, MOTIF_CONVOI, w.marches[o.marche.id])
    if cv is None: p.compter("convoi_militaire_refuse"); return False
    cv.cargaison.clear()
    dt = _depart(d, o.id, w.pas) - w.pas              # etale comme un camion militaire
    cv.depart += dt; cv.arrivee += dt
    src = EXT.StockE1(cv.cargaison, cat)
    for nom, q in sorted(part.items()):
        L.deplacer(_contenant(p, d, dem.src[0], dem.src[1], nom), src, d.ids[nom], q, "chargement_militaire")
    d.en_route[cv.id] = (dem.dst, dem.id, -1)
    p.noter("convoi_militaire", de=o.id, vers=t.id, tonnes=round(kg * f / 1000.0, 3))
    return True


def _quai(p, d, dep):
    """Le quai d ou partent les lots par mer d un depot : le port de son ile, sinon le marche de son lieu."""
    w = p.w; lg = LG._lg(p)
    lieu = w.carte.lieux[dep.lieu]
    port = w.carte.port(lieu.ile)
    if port is not None and port.id in lg.quai_marche: return port.id
    return lieu.marche.id


def _envoyer_mer(p, d, dem):
    """Par la mer ( domaine 15 : ferry ou caboteur, lots ) : un lot par bien. Le premier bout, du depot au quai, est
    fait sans convoi ( limite : a remplacer par un convoi militaire vers le port ). Rend vrai si un lot est parti."""
    w = p.w; dep = d.depots[dem.src[1]]
    quai = _quai(p, d, dep)
    parti = False
    for nom, q in sorted(dem.cargo.items()):
        q = min(q, _quantite(p, d, dem.src[0], dem.src[1], nom))
        if q <= EPS: continue
        lid = LG.envoyer(p, w.gouv, _contenant(p, d, dem.src[0], dem.src[1], nom), nom, q, quai, dem.dest, RECEPTEUR)
        if lid >= 0:
            d.lots[lid] = (dem.dst, dep.k); parti = True
    if not parti: p.compter("convoi_militaire_refuse")
    return parti


def _traiter_demandes(p, d):
    """Chaque heure : les demandes en attente partent si elles le peuvent, celles des garnisons ( le front ) avant celles
    des depots ; une demande echue tombe."""
    if not d.demandes: return
    w = p.w; restent = []
    for dem in sorted(d.demandes, key=lambda x: (x.dst[0] == "depot", x.id)):
        if dem.expire < w.pas:
            p.compter("convoi_militaire_refuse"); continue
        ok = _envoyer_mer(p, d, dem) if dem.moyen == "mer" else _lancer_militaire(p, d, dem)
        if not ok: restent.append(dem)
    d.demandes = restent


def _arrivee_convoi(p, c):
    """Le recepteur des convois militaires ( domaine 15, motif convoi_militaire ) : la cargaison entre chez son
    destinataire par le grand livre."""
    d = _dom(p); L = p.socle.livre; cat = p.socle.catalogue
    info = d.en_route.pop(c.id, None)
    if info is None: raise KeyError(f"convoi militaire {c.id} inconnu du domaine 26")
    dst, _, _ = info
    src = EXT.StockE1(c.cargaison, cat)
    kg = 0.0
    for nom in sorted(c.cargaison):
        q = c.cargaison[nom]
        if q <= 0.0: continue
        q = L.deplacer(src, _contenant(p, d, dst[0], dst[1], nom), d.ids[nom], q, "livraison_militaire")
        if dst[0] == "base" and nom in A.NOMS_MUNITIONS + ("pieces",): _entree_armurerie(p, nom, q)
        kg += q * _masse(p, nom)
    if dst[0] == "base":
        j, x = d.livraisons.get(dst[1], (p.jour, 0.0))
        d.livraisons[dst[1]] = (p.jour, x + kg if j == p.jour else kg)
    p.compter("livraison_militaire", kg)


def _recevoir_lot(p, lot, src):
    """Le recepteur des lots par mer ( domaine 15 ) : le lot entre a la garnison ( ou au depot ) de sa destination."""
    d = _dom(p); L = p.socle.livre
    dst, _ = d.lots.pop(lot.id, (None, None))
    if dst is None: raise KeyError(f"lot {lot.id} inconnu du domaine 26")
    q = L.deplacer(src, _contenant(p, d, dst[0], dst[1], lot.bien), d.ids[lot.bien], lot.q, "livraison_militaire")
    if dst[0] == "base" and lot.bien in A.NOMS_MUNITIONS + ("pieces",): _entree_armurerie(p, lot.bien, q)
    p.compter("livraison_militaire", q * _masse(p, lot.bien))


def _retour_lot(p, lot, src):
    """Un lot annule revient a son depot d origine."""
    d = _dom(p)
    _, k = d.lots.pop(lot.id, (None, d.national.k))
    p.socle.livre.deplacer(src, _contenant(p, d, "depot", k, lot.bien), d.ids[lot.bien], lot.q, "retour_lot_militaire")


def _convoi_vers(d, b):
    """Vrai si un convoi ou un lot est deja en route vers la garnison b, ou une demande en attente."""
    for dst, _, _ in d.en_route.values():
        if dst == ("base", b): return True
    for dst, _ in d.lots.values():
        if dst == ("base", b): return True
    return any(dem.dst == ("base", b) for dem in d.demandes)


# ================================================================== le point de decision dans le monde
def _contexte(p, d, b):
    w = p.w; lg = LG._lg(p)
    k = d.depot_de_base[b]; dep = d.depots[k]
    a = _autonomie_classes(d.besoins[b], _stocks_base(p, d, b))
    rem = [float(min(1.0, a[c] / CIBLE_GARNISON[c])) for c in range(3)]
    o, t = w.carte.lieux[dep.lieu], w.carte.par_n[b]
    autre = o.ile != t.ile
    route = 0.0 if autre else float(LG.route_praticable(p, o, t))
    dr = _remplissage_depot(p, d, k)
    return ContexteGarnison(rem + [TAUX_POSTURE[_posture(p, d, b)], route, float(lg.mer_ouverte), float(autre)]
                            + [float(np.clip(x, 0.0, 1.0)) for x in dr] + [float(_convoi_vers(d, b))])


def _matin(p):
    """6 h 40 : les besoins du jour ; chaque depot de brigade sous sa dotation demande a la nation ; chaque S4 decide, et
    sa demande part vers la brigade comme un ordre."""
    d = _dom(p); w = p.w
    _besoins(p, d)
    d.portees = {}; d.rupt_jour = {}; d.cmd = {}
    nat_u = A._dom(p).armee_u
    for dep in d.depots:
        if dep.niveau != "brigade": continue
        dr = _remplissage_depot(p, d, dep.k)
        manque = [c for c in range(3) if dr[c] < SEUIL_DEMANDE]
        en_cours = any(dem.dst == ("depot", dep.k) for dem in d.demandes) or \
            any(dst == ("depot", dep.k) for dst, _, _ in d.en_route.values())
        if manque and not en_cours:
            emettre_ordre(p, dep.brigade, nat_u, "demande_depot", a=dep.k, b=MIXTE if len(manque) > 1 else manque[0])
    for b in d.bases:
        ctx = _contexte(p, d, b)
        a = d.decideur.decider(b, ctx)
        d.cmd[b] = a
        p.compter("decision_ravitaillement")
        moyen, classe = _action(a)
        if moyen is None: continue
        d.decideur.ajouter(b, -(COUT_ROUTE if moyen == "route" else COUT_MER))
        dep = d.depots[d.depot_de_base[b]]
        emettre_ordre(p, d.bataillon_de[b], dep.brigade, "demande", a=b, b=classe, c=0 if moyen == "route" else 1)


def _soir(p):
    """22 h 50 : la note de chaque garnison, la serie du jour, la rotation des rations, les achats de la nation, l oubli."""
    d = _dom(p)
    notes = {}; autos = {}
    for b in d.bases:
        a = _autonomie_classes(d.besoins[b], _stocks_base(p, d, b))
        rem = np.array([a[c] / CIBLE_GARNISON[c] for c in range(3)])
        v = _note_jour(rem, len(d.rupt_jour.get(b, ())))
        d.decideur.noter(b, v, p.jour)
        notes[b] = v; autos[b] = tuple(float(x) for x in a)
    d.serie.append({"jour": p.jour, "notes": notes, "autonomie": autos, "action": dict(d.cmd),
                    "ruptures": {b: sorted(c) for b, c in d.rupt_jour.items()},
                    "depots": {dep.k: _remplissage_depot(p, d, dep.k) for dep in d.depots}})
    if len(d.serie) > 400: del d.serie[0]
    _rotation(p, d)
    _approvisionner_nation(p, d)
    _oublier(p, d)


# ================================================================== le commandement : ordres, transmission, plans
def _camp(d, camp):
    if isinstance(camp, (int, np.integer)): return int(camp)
    for k, c in enumerate(d.camps):
        if c.nom == camp: return k
    raise KeyError(f"camp inconnu {camp!r}")


def _lieu_proche(p, d, x, y, ile):
    """Le lieu de la carte le plus proche d un point d une ile ( numero )."""
    m = d.ile_lieu == ile
    idx = np.nonzero(m)[0]
    k = int(np.argmin(np.hypot(d.pos_lieux[idx, 0] - x, d.pos_lieux[idx, 1] - y)))
    return int(idx[k])


def position(p, camp, u):
    """( x, y, ile ) d une unite : une unite du domaine 25 ( camp national ) - sa base, ou la ou ses ordres l ont menee ;
    une entite d un autre camp - sa position. Un mouvement en cours est interpole."""
    d = _dom(p); ci = _camp(d, camp); u = int(u)
    m = d.mouvements.get((ci, u))
    if m is not None:
        x0, y0, x1, y1, ile, t0, t1 = m
        f = min(1.0, max(0.0, (p.w.pas - t0) / max(1, t1 - t0)))
        return (x0 + f * (x1 - x0), y0 + f * (y1 - y0), ile)
    if not d.camps[ci].national:
        E = d.ent; return (float(E["x"][u]), float(E["y"][u]), int(E["ile"][u]))
    x = d.pos_unite.get((ci, u))
    if x is not None: return x
    return _position_base(p, u)


def _position_base(p, u):
    """Le quartier d une unite du domaine 25 : sa base ; une brigade, son depot ; l armee, le gouvernement."""
    d = _dom(p); a = A._dom(p); U = a.unites; w = p.w
    b = int(U["base"][u])
    if b >= 0: l = w.carte.par_n[b]
    elif U["niveau"][u] == A.BRIGADE:
        dep = next((x for x in d.depots if x.brigade == u), d.national)
        l = w.carte.lieux[dep.lieu]
    else: l = w.carte.gouvernement
    return (float(l.pos[0]), float(l.pos[1]), w.carte.iles.index(l.ile))


def _portee_radio(p, d, ci, u):
    """La portee radio ( km ) d une unite : la meilleure radio de ses membres ( domaine 25 ), ou celle de son camp ;
    zero sans radio."""
    if (ci, u) in d.radio_hs: return 0.0
    cp = d.camps[ci]
    if not cp.national: return cp.portee_radio_km
    k = (ci, u)
    if k not in d.portees: d.portees[k] = float(A.radios(p, u)[1])
    return d.portees[k]


def _brouille(d, ci, x, y, ile, pas):
    for cb, bx, by, bi, r, fin in d.brouillages:
        if cb != ci and bi == ile and fin >= pas and math.hypot(x - bx, y - by) <= r: return True
    return False


def delai_transmission(p, de, vers, camp=CAMP_NATIONAL):
    """( moyen, delai en pas, km ) d un ordre de l unite `de` a l unite `vers` : la RADIO si les deux en ont une qui
    porte jusque-la et que personne ne brouille ; sinon le TELEPHONE du reseau civil si les deux lieux ont le reseau
    ( domaine 22 ; camp national seulement ) ; sinon une ESTAFETTE, a la vitesse de la route, plus lente la nuit."""
    d = _dom(p); ci = _camp(d, camp); w = p.w
    xe, ye, ie = position(p, ci, de); xr, yr, ir = position(p, ci, vers)
    meme = ie == ir
    km = math.hypot(xe - xr, ye - yr) / 1000.0 if meme else KM_MER_ESTAFETTE
    portee = min(_portee_radio(p, d, ci, int(de)), _portee_radio(p, d, ci, int(vers)))
    if meme and km <= portee and not _brouille(d, ci, xe, ye, ie, w.pas) and not _brouille(d, ci, xr, yr, ir, w.pas):
        return RADIO_M, max(1, math.ceil(DELAI_RADIO_MIN / MIN_PAS - 1e-9)), km
    if d.camps[ci].national:
        le = w.carte.par_n[_lieu_proche(p, d, xe, ye, ie)].id; lr = w.carte.par_n[_lieu_proche(p, d, xr, yr, ir)].id
        if MED.telecom_ok(p, le) and MED.telecom_ok(p, lr):
            return TELEPHONE_M, max(1, math.ceil(DELAI_TELEPHONE_MIN / MIN_PAS - 1e-9)), km
    v = VITESSE_ESTAFETTE_KMH[1 if w.nuit() else 0]
    minutes = PREPARATION_ESTAFETTE_MIN + (1.3 * km / v if meme else km / VITESSE_MER_KMH) * 60.0
    return ESTAFETTE_M, max(1, math.ceil(minutes / MIN_PAS - 1e-9)), km


def _fatigue_chef(p, d, ci, u):
    if not d.camps[ci].national: return 0.0
    a = A._dom(p); h = int(a.unites["chef"][u])
    if h < 0 or int(p.col("habitant", "ar_rang")[h]) < 0: return 0.0
    return float(A.competences(p, [h])["fatigue"][0])


def emettre_ordre(p, de, vers, contenu, a=0.0, b=0.0, c=0.0, camp=CAMP_NATIONAL, echeance=-1, plan=-1, emetteur=-1,
                  frictions=True):
    """Un ordre de l unite `de` a l unite `vers` ( unites du domaine 25 pour le camp national, entites pour un autre
    camp ). contenu : mouvement ( a, b : destination en m ), activite ( a : action du domaine 25, b : jours ), tenir
    ( a : heures ), demande ( a : base, b : classe ou MIXTE, c : 0 route, 1 mer ), demande_depot ( a : depot, b : classe ).
    Le moyen et le delai viennent de `delai_transmission` ; les frictions ( un retard, un ordre mal compris - plus souvent
    a la voix et quand le chef est fatigue -, une estafette perdue ) sont tirees a l emission. Une emission radio peut
    etre interceptee par un autre camp. Rend le numero de l ordre."""
    d = _dom(p); w = p.w; ci = _camp(d, camp); Od = d.ordres
    kc = CONTENUS.index(contenu) if isinstance(contenu, str) else int(contenu)
    mo, delai, km = delai_transmission(p, de, vers, ci)
    u = p.hasard("armee_soutien_friction").random(5)
    retard = 1 + int(u[1] * RETARD_MAX_PAS[mo]) if frictions and u[0] < P_RETARD[mo] else 0
    mal = bool(frictions and u[2] < P_MAL[mo] * (1.0 + _fatigue_chef(p, d, ci, int(vers))))
    perdu = bool(frictions and u[3] < P_PERTE[mo])
    xa, xb, xc = float(a), float(b), float(c)
    if mal:
        if kc == MOUVEMENT:
            ang = 2.0 * math.pi * u[4]; xa += DECALAGE_MAL_M * math.cos(ang); xb += DECALAGE_MAL_M * math.sin(ang)
        elif kc == ACTIVITE: xa = float((int(a) + 1 + int(u[4] * (len(A.ACTIONS) - 1))) % len(A.ACTIONS))
        elif kc in (DEMANDE, DEMANDE_DEPOT): xb = float((int(b) + 1 + int(u[4] * 3)) % 4)
        elif kc == TENIR: xa = 0.5 * float(a)
    k = Od.ajouter()
    for champ, v in (("camp", ci), ("emetteur", emetteur), ("de", int(de)), ("vers", int(vers)), ("contenu", kc),
                     ("a", a), ("b", b), ("c", c), ("xa", xa), ("xb", xb), ("xc", xc), ("t_emis", w.pas),
                     ("t_prevu", w.pas + delai), ("t_recu", -1), ("moyen", mo), ("etat", PERDU if perdu else EN_ROUTE),
                     ("compris", 0 if mal else 1), ("retard", retard), ("km", km), ("plan", plan), ("echeance", echeance)):
        Od[champ][k] = v
    if not perdu: p.poser(delai + retard - 1, "armee_soutien_ordre", k)
    if mo == RADIO_M: _intercepter(p, d, ci, int(de))
    p.compter("ordre_emis")
    if mal: p.compter("ordre_mal_compris")
    if perdu: p.compter("ordre_perdu")
    return k


def _ordre_recu(p, k, donnees=()):
    d = _dom(p); Od = d.ordres
    if Od["etat"][k] != EN_ROUTE: return
    Od["t_recu"][k] = p.w.pas; Od["etat"][k] = RECU
    p.compter("ordre_recu")
    _executer(p, d, k)


def _executer(p, d, k):
    """Ce que fait l unite qui recoit l ordre, tel qu elle l a COMPRIS."""
    Od = d.ordres; w = p.w
    ci, u, kc = int(Od["camp"][k]), int(Od["vers"][k]), int(Od["contenu"][k])
    xa, xb, xc = float(Od["xa"][k]), float(Od["xb"][k]), float(Od["xc"][k])
    d.sans_ordre_h[(ci, u)] = 0
    if kc == MOUVEMENT: _mouvoir(p, d, ci, u, xa, xb)
    elif kc == ACTIVITE:
        if d.camps[ci].national and u in A._dom(p).compagnies:
            A.imposer_activite(p, u, int(xa), max(1, int(Od["b"][k])))
    elif kc == TENIR: d.tenir[(ci, u)] = w.pas + int(round(xa * PAS_H))
    elif kc == DEMANDE: _demande_garnison(p, d, int(Od["a"][k]), int(xb), "route" if xc < 0.5 else "mer")
    elif kc == DEMANDE_DEPOT: _demande_depot(p, d, int(Od["a"][k]), int(xb))


def _motorisee(p, d, ci, u):
    if not d.camps[ci].national: return int(d.ent["posture"][u]) == 2
    a = A._dom(p); V = a.veh; U = a.unites; n = V.n
    if not n: return False
    un = V["unite"][:n]; niv = int(U["niveau"][u])
    anc = np.where(un >= 0, U[f"a{niv}"][np.maximum(un, 0)], -1)
    return bool(((anc == u) & (V["oid"][:n] >= 0) & (V["etat"][:n] == O.SERVICE)).any())


def _mouvoir(p, d, ci, u, x, y):
    """Un ordre de mouvement recu : l unite part vers ( x, y ) sur son ile, a pied ou motorisee. Pour Arma, la
    destination est posee AVANT l ordre de marche ( `ordre_de_mouvement` : `moveTo` seul ne bouge pas un agent )."""
    w = p.w
    x0, y0, ile = position(p, ci, u)
    v = VITESSE_MOTORISEE_KMH if _motorisee(p, d, ci, u) else VITESSE_MARCHE_KMH
    km = 1.3 * math.hypot(x - x0, y - y0) / 1000.0
    t1 = w.pas + max(1, math.ceil(km / v * PAS_H - 1e-9))
    d.mouvements[(ci, u)] = (x0, y0, float(x), float(y), ile, w.pas, t1)
    d.deployes.add((ci, u))
    seq = A.ordre_de_mouvement(p, u, (float(x), float(y))) if d.camps[ci].national else \
        [("setDestination", u, (float(x), float(y))), ("moveTo", u, (float(x), float(y)))]
    d.ordres_arma.append((w.pas, ci, u, seq))


def _heure(p):
    """Chaque heure : les mouvements arrives, la dislocation des unites deployees sans ordre ( une attente est un ordre
    TENIR, sinon l unite derive : 18/09 ), la population qui voit passer les entites, les demandes de convoi."""
    d = _dom(p); w = p.w
    for key in sorted(d.mouvements):
        m = d.mouvements[key]
        if w.pas >= m[6]:
            d.pos_unite[key] = (m[2], m[3], m[4]); del d.mouvements[key]
            if not d.camps[key[0]].national:
                E = d.ent; E["x"][key[1]], E["y"][key[1]] = m[2], m[3]
            else:
                bx, by, bi = _position_base(p, key[1])
                if bi == m[4] and math.hypot(m[2] - bx, m[3] - by) <= RAYON_BASE_M:      # rentree au quartier
                    del d.pos_unite[key]; d.deployes.discard(key); d.sans_ordre_h.pop(key, None)
        elif not d.camps[key[0]].national:
            x, y, _ = position(p, key[0], key[1]); d.ent["x"][key[1]], d.ent["y"][key[1]] = x, y
    for key in sorted(d.deployes):
        if key in d.mouvements or d.tenir.get(key, -1) >= w.pas: continue
        d.sans_ordre_h[key] = d.sans_ordre_h.get(key, 0) + 1
        p.compter("dislocation_h")
    _temoins_population(p, d)
    _traiter_demandes(p, d)


def poser_plan(p, de, etapes, camp=CAMP_NATIONAL):
    """Un plan : une suite d ordres [ ( vers, contenu, ( a, b, c ), pas d emission, echeance en pas ) ]. Chaque etape part
    a son pas ( une echeance du socle ) ; `etat_plan` dit si elle a ete recue avant son echeance. Rend le numero."""
    d = _dom(p); w = p.w; ci = _camp(d, camp)
    k = len(d.plans)
    d.plans.append({"de": int(de), "camp": ci, "etapes": [[int(v), c, tuple(float(x) for x in prm), int(t), int(e), -1]
                                                         for v, c, prm, t, e in etapes]})
    for j, e in enumerate(d.plans[k]["etapes"]):
        if e[3] <= w.pas: _etape(p, k, (j,))
        else: p.poser(e[3] - w.pas - 1, "armee_soutien_plan", k, (j,))
    return k


def _etape(p, k, donnees):
    d = _dom(p); pl = d.plans[k]; j = donnees[0]; e = pl["etapes"][j]
    a, b, c = (tuple(e[2]) + (0.0, 0.0, 0.0))[:3]
    e[5] = emettre_ordre(p, pl["de"], e[0], e[1], a, b, c, camp=pl["camp"], echeance=e[4], plan=k)


def etat_plan(p, k):
    """[ { ordre, contenu, emis, recu, echeance, a_temps, moyen } ] des etapes d un plan."""
    d = _dom(p); Od = d.ordres; out = []
    for e in d.plans[k]["etapes"]:
        o = e[5]
        if o < 0: out.append({"ordre": -1, "contenu": e[1], "emis": None, "recu": None, "echeance": e[4], "a_temps": None,
                              "moyen": None}); continue
        r = int(Od["t_recu"][o])
        out.append({"ordre": o, "contenu": e[1], "emis": int(Od["t_emis"][o]), "recu": r if r >= 0 else None,
                    "echeance": e[4], "a_temps": (0 <= r <= e[4]) if r >= 0 else False, "moyen": MOYENS[int(Od["moyen"][o])]})
    return out


def ordre(p, k):
    """Ce qu un autre domaine lit d un ordre."""
    Od = _dom(p).ordres
    return {"camp": _dom(p).camps[int(Od["camp"][k])].nom, "de": int(Od["de"][k]), "vers": int(Od["vers"][k]),
            "contenu": CONTENUS[int(Od["contenu"][k])], "voulu": (float(Od["a"][k]), float(Od["b"][k]), float(Od["c"][k])),
            "compris": (float(Od["xa"][k]), float(Od["xb"][k]), float(Od["xc"][k])), "bien_compris": bool(Od["compris"][k]),
            "emis": int(Od["t_emis"][k]), "prevu": int(Od["t_prevu"][k]),
            "recu": int(Od["t_recu"][k]) if Od["t_recu"][k] >= 0 else None, "moyen": MOYENS[int(Od["moyen"][k])],
            "etat": ETATS_ORDRE[int(Od["etat"][k])], "retard_pas": int(Od["retard"][k]), "km": float(Od["km"][k]),
            "plan": int(Od["plan"][k]), "echeance": int(Od["echeance"][k])}


def brouiller(p, camp_brouilleur, x, y, rayon_km, heures, ile=0):
    """Domaine 27 : un brouilleur du camp `camp_brouilleur` empeche toute radio d un AUTRE camp dans ce rayon."""
    d = _dom(p)
    d.brouillages.append((_camp(d, camp_brouilleur), float(x), float(y), int(ile), 1000.0 * float(rayon_km),
                          p.w.pas + int(round(heures * PAS_H))))


def couper_radios(p, u, camp=CAMP_NATIONAL, coupe=True):
    """Scenario, domaine 27 : l unite n a plus de radio ( panne, batteries, perte )."""
    d = _dom(p); key = (_camp(d, camp), int(u))
    if coupe: d.radio_hs.add(key)
    else: d.radio_hs.discard(key)


def tenir(p, de, u, heures, camp=CAMP_NATIONAL):
    """Un ordre TENIR ( une attente imposee est un ordre, 18/09 ) : rend le numero de l ordre."""
    return emettre_ordre(p, de, u, "tenir", a=heures, camp=camp)


def unites_sans_ordre(p):
    """{ ( camp, unite ) : heures deployee sans ordre } : la dislocation qui menace ( 18/09 : 818 m de marche )."""
    d = _dom(p)
    return {(d.camps[c].nom, u): h for (c, u), h in sorted(d.sans_ordre_h.items()) if h > 0}


# ================================================================== le renseignement : camps, entites, connaissance
def poser_camp(p, nom, poids=None, taille=100, cote="EAST", portee_radio_km=5.0, visible=True, national=False):
    """Un camp ( scenario, domaine 27 ) : une cellule de croyance au domaine 22 ( son etat-major, qui apprend de ceux
    qu il cotoie : `poids` { lieu : poids } ), sa cote Arma ( WEST, EAST, GUER ), la portee radio de ses hommes. Aucun
    adversaire n existe dans le monde par defaut ( decision de Younes du 22/09 ). Rend son numero."""
    d = _dom(p)
    if any(c.nom == nom for c in d.camps): raise ValueError(f"camp {nom!r} deja pose")
    cell = MED.inscrire_groupe(p, nom, poids, max(1, int(taille)), suit_medias=True)
    d.camps.append(Camp(nom, cell, national, cote, portee_radio_km, visible))
    return len(d.camps) - 1


def poser_entite(p, camp, x, y, ile=0, posture="debout", taille=1, vitesse_ms=1.4, unite=-1):
    """Un element d un camp a une position ( m, dans le repere de son ile ) : un groupe ennemi, un vehicule, une unite du
    domaine 25 que l adversaire peut voir ( `unite` ). Rend son numero."""
    d = _dom(p); ci = _camp(d, camp); E = d.ent
    k = E.ajouter()
    E["camp"][k] = ci; E["x"][k] = float(x); E["y"][k] = float(y); E["ile"][k] = int(ile)
    E["posture"][k] = POSTURES_CIBLE.index(posture) if isinstance(posture, str) else int(posture)
    E["taille"][k] = int(taille); E["vitesse"][k] = float(vitesse_ms); E["vivant"][k] = 1; E["unite"][k] = int(unite)
    E["lieu"][k] = -1
    _temoins_population(p, d, [k])
    return k


def deplacer_entite(p, k, x, y, posture=None):
    d = _dom(p); E = d.ent
    E["x"][k] = float(x); E["y"][k] = float(y)
    if posture is not None: E["posture"][k] = POSTURES_CIBLE.index(posture) if isinstance(posture, str) else int(posture)
    _temoins_population(p, d, [k])


def retirer_entite(p, k):
    _dom(p).ent["vivant"][k] = 0


def _temoins_population(p, d, ks=None):
    """La population voit passer les entites des camps visibles a moins de RAYON_TEMOINS_M d un lieu habite : une
    nouvelle presence_militaire ( domaine 22 : temoins, bouche a oreille, medias ) a chaque changement de lieu."""
    E = d.ent
    if E.n == 0: return
    idx = range(E.n) if ks is None else ks
    for k in idx:
        if not E["vivant"][k] or not d.camps[int(E["camp"][k])].visible: continue
        x, y, ile = float(E["x"][k]), float(E["y"][k]), int(E["ile"][k])
        n = _lieu_proche(p, d, x, y, ile)
        if math.hypot(d.pos_lieux[n, 0] - x, d.pos_lieux[n, 1] - y) > RAYON_TEMOINS_M: n = -1
        if n == int(E["lieu"][k]): continue
        E["lieu"][k] = n
        if n >= 0:
            p.noter(SUJET_PRESENCE, lieu=p.w.carte.par_n[n].id, camp=d.camps[int(E["camp"][k])].nom,
                    taille=int(E["taille"][k]))
            d.presence = True


def azimut(x0, y0, x1, y1):
    """L angle ( radians, est = 0, nord = pi/2 ) de ( x0, y0 ) vers ( x1, y1 )."""
    return math.atan2(y1 - y0, x1 - x0)


def _connaitre(p, d, ci, cible, x, y, ile, sigma, vitesse, source, conf, observateur, taille):
    K = d.conn; key = (ci, int(cible))
    r = d.conn_idx.get(key)
    if r is None:
        r = K.ajouter(); d.conn_idx[key] = r
        K["camp"][r] = ci; K["cible"][r] = int(cible); K["n_obs"][r] = 0; K["fait"][r] = -1
    K["x"][r] = x; K["y"][r] = y; K["ile"][r] = ile; K["sigma"][r] = sigma; K["vitesse"][r] = vitesse
    K["t"][r] = p.w.pas; K["source"][r] = source; K["conf"][r] = conf; K["observateur"][r] = observateur
    K["n_obs"][r] += 1; K["taille"][r] = taille; K["actif"][r] = 1
    return r


def _publier(p, d, ci, r, lieu_vrai):
    """Ce que le camp sait devient la croyance de SA cellule au domaine 22 ( informer ), avec le lieu CRU."""
    K = d.conn
    fid = int(K["fait"][r])
    if fid < 0 or MED.fait(p, fid) is None:
        fid = MED.constater(p, SUJET_PRESENCE, p.w.carte.par_n[lieu_vrai].id, valeur=max(1.0, float(K["taille"][r])),
                            temoins=0, officiel=False)
        K["fait"][r] = fid
    lc = _lieu_proche(p, d, float(K["x"][r]), float(K["y"][r]), int(K["ile"][r]))
    MED.informer(p, d.camps[ci].nom, fid, part=1.0, valeur=max(1.0, float(K["taille"][r])), lieu=p.w.carte.par_n[lc].id,
                 confiance=float(K["conf"][r]), source=MED.RENSEIGNEMENT)


def observer(p, camp, observateurs, positions=None, regards=None, nuit=None, portees=None, cibles=None,
             source="observation", ile=None):
    """Des guetteurs d un camp regardent. `observateurs` : des habitants militaires ( camp national ) ou des entites ;
    `positions` ( n, 2 ) en m ( defaut : leur lieu, ou leur position d entite ) ; `regards` : l azimut de chacun
    ( radians ; None : ils balaient ) ; `portees` : en m ( defaut : `perception` du domaine 25, jour ou nuit, fatigue ).
    Une cible est VUE par un guetteur si elle est dans son cone et a sa portee ( posture de la cible comprise ), ou tout
    pres hors du cone ; la detection est binaire. Des qu un guetteur la voit, TOUT le camp la connait ( knowsAbout est
    de camp ), avec la position estimee par le plus proche ( erreur croissante avec la distance ) ; chaque guetteur qui
    l a vue est note ( qui a vu quoi ). Rend [ ( cible, observateur, distance m ) ]."""
    d = _dom(p); w = p.w; ci = _camp(d, camp); cp = d.camps[ci]; E = d.ent
    src = SOURCES.index(source) if isinstance(source, str) else int(source)
    obs = np.asarray(observateurs, np.int64)
    if not len(obs) or E.n == 0: return []
    if nuit is None: nuit = w.nuit()
    if cp.national:
        n = w.table.lieu[obs].astype(np.int64)
        pos = d.pos_lieux[n] if positions is None else np.asarray(positions, np.float64)
        ile_o = np.full(len(obs), int(d.ile_lieu[n[0]]) if ile is None else int(ile))
        if portees is None: portees = A.perception(p, obs, nuit)[1]
    else:
        pos = np.column_stack((E["x"][obs], E["y"][obs])) if positions is None else np.asarray(positions, np.float64)
        ile_o = E["ile"][obs].astype(np.int64) if ile is None else np.full(len(obs), int(ile))
        if portees is None: portees = np.full(len(obs), PORTEE_ENTITE_M[1 if nuit else 0])
    portees = np.asarray(portees, np.float64)
    t = np.nonzero((E["vivant"][:E.n] == 1) & (E["camp"][:E.n] != ci))[0]
    if cibles is not None: t = np.intersect1d(t, np.asarray(cibles, np.int64))
    if not len(t): return []
    tx, ty = E["x"][t], E["y"][t]
    dx = tx[None, :] - pos[:, 0][:, None]; dy = ty[None, :] - pos[:, 1][:, None]
    D = np.hypot(dx, dy)
    fp = F_POSTURE[E["posture"][t].astype(np.int64)][None, :]
    if regards is None: reach = portees[:, None] * F_BALAYAGE * fp
    else:
        reg = np.asarray(regards, np.float64)
        dth = np.abs((np.arctan2(dy, dx) - reg[:, None] + math.pi) % (2.0 * math.pi) - math.pi)
        reach = portees[:, None] * fp * np.where(dth <= DEMI_CONE, 1.0, F_PERIPHERIE)
    vu = (D <= reach) & (ile_o[:, None] == E["ile"][t][None, :])
    rng = p.hasard("armee_soutien_renseignement")
    out = []
    for j in np.nonzero(vu.any(axis=0))[0].tolist():
        k = int(t[j])
        qui = np.nonzero(vu[:, j])[0]
        i = int(qui[np.argmin(D[qui, j])]); dist = float(D[i, j])
        ux, uy = (dx[i, j] / dist, dy[i, j] / dist) if dist > EPS else (1.0, 0.0)
        z = rng.standard_normal(2)
        er = (SIGMA0_M + K_DISTANCE * dist) * z[0]; el = (SIGMA0_M + K_LATERAL * dist) * z[1]
        xc = float(tx[j] + er * ux - el * uy); yc = float(ty[j] + er * uy + el * ux)
        r = _connaitre(p, d, ci, k, xc, yc, int(E["ile"][k]), SIGMA0_M + K_DISTANCE * dist, float(E["vitesse"][k]), src,
                       CONF_SOURCE.get(src, 0.9), int(obs[i]), float(E["taille"][k]))
        for i2 in qui.tolist(): d.vus.append((w.pas, ci, int(obs[i2]), k, float(D[i2, j])))
        _publier(p, d, ci, r, _lieu_proche(p, d, float(tx[j]), float(ty[j]), int(E["ile"][k])))
        out.append((k, int(obs[i]), dist))
    p.compter("observation", len(obs))
    if out: p.compter("contact", len(out))
    return out


def patrouille(p, u, itineraire, nuit=None, camp=CAMP_NATIONAL, ile=None):
    """Une patrouille de l unite u ( domaine 25 ) le long d `itineraire` [ ( x, y ) ] : a chaque point, ses membres
    presents regardent dans le sens de la marche ( source patrouille ). Pour Arma, la suite de destinations est posee
    avant les ordres de marche. Rend les detections."""
    d = _dom(p); w = p.w; ci = _camp(d, camp)
    ids = A.membres(p, u, actifs_seulement=True)
    if not len(ids) or not itineraire: return []
    if nuit is None: nuit = w.nuit()
    portees = A.perception(p, ids, nuit)[1]
    if ile is None: ile = position(p, ci, u)[2]
    out = []
    pts = [(float(x), float(y)) for x, y in itineraire]
    for k, (x, y) in enumerate(pts):
        if k + 1 < len(pts): reg = azimut(x, y, *pts[k + 1])
        elif k > 0: reg = azimut(*pts[k - 1], x, y)
        else: reg = 0.0
        out += observer(p, ci, ids, np.tile([x, y], (len(ids), 1)), np.full(len(ids), reg), nuit, portees,
                        source="patrouille", ile=ile)
    d.ordres_arma.append((w.pas, ci, int(u), [c for pt in pts for c in A.ordre_de_mouvement(p, u, pt)]))
    return out


def poser_ecoute(p, camp, x, y, portee_km, ile=0):
    """Une station d ecoute et de goniometrie d un camp : elle localise toute emission radio d un autre camp a sa portee."""
    d = _dom(p); d.camps[_camp(d, camp)].ecoutes.append((float(x), float(y), int(ile), 1000.0 * float(portee_km)))


def _intercepter(p, d, ci, de):
    """Une emission radio de l unite `de` du camp ci : les stations d ecoute des autres camps la localisent ( source
    radio, erreur de goniometrie croissante avec la distance )."""
    if not any(c.ecoutes for k, c in enumerate(d.camps) if k != ci): return
    x, y, ile = position(p, ci, de)
    cible = int(de) if not d.camps[ci].national else CIBLE_UNITE0 + int(de)
    rng = p.hasard("armee_soutien_renseignement")
    for cj, cp in enumerate(d.camps):
        if cj == ci: continue
        for sx, sy, si, portee in cp.ecoutes:
            dist = math.hypot(x - sx, y - sy)
            if si != ile or dist > portee: continue
            z = rng.standard_normal(2); s = SIGMA0_M + K_GONIO * dist
            _connaitre(p, d, cj, cible, x + s * z[0], y + s * z[1], ile, s, 0.0, RADIO_S, CONF_SOURCE[RADIO_S], -1, 0.0)
            p.compter("interception")
            break


def _ecouter(p):
    """18 h : ce que la population et les medias ont fait savoir a chaque camp ( sa cellule au domaine 22 ) devient une
    connaissance : un CONTACT non identifie, au lieu cru, d erreur celle d un lieu. Le renseignement du camp lui-meme
    ( source renseignement ) n est pas relu."""
    d = _dom(p)
    if not d.presence: return
    for ci, cp in enumerate(d.camps):
        for e in MED.croyance(p, cp.nom, SUJET_PRESENCE):
            s = e["source"]
            if s in ("renseignement", "etat") or e["lieu"] is None: continue
            src = POPULATION if s in ("temoin", "bouche_a_oreille", "telephone", "origine_rumeur") else MEDIAS
            cible = -(int(e["fait"]) + 1)
            t = int(round(e["appris"] * PAS_JOUR))
            r = d.conn_idx.get((ci, cible))
            if r is not None and d.conn["t"][r] >= t: continue
            l = p.w.carte.lieux[e["lieu"]]
            r = _connaitre(p, d, ci, cible, float(l.pos[0]), float(l.pos[1]), p.w.carte.iles.index(l.ile), SIGMA_LIEU_M,
                           0.0, src, float(e["confiance"]), -1, float(e["valeur"]))
            d.conn["t"][r] = min(t, p.w.pas)


def _oublier(p, d):
    K = d.conn; lim = p.w.pas - OUBLI_J * PAS_JOUR
    for key, r in sorted(d.conn_idx.items()):
        if K["t"][r] < lim:
            K["actif"][r] = 0; del d.conn_idx[key]


def connaissance(p, camp, cible):
    """Ce que le camp sait d une cible ( entite, CIBLE_UNITE0 + unite, ou contact de rumeur ) : None s il n en sait RIEN
    ( zero est une absence, 13/09 ). { x, y, ile, age_h, sigma_m ( erreur a l observation ), rayon_m ( ce que l age y
    ajoute : la cible a pu marcher ), source, confiance, observateur, observations, taille }."""
    d = _dom(p); ci = _camp(d, camp)
    r = d.conn_idx.get((ci, int(cible)))
    if r is None: return None
    K = d.conn
    age_h = (p.w.pas - int(K["t"][r])) / PAS_H
    return {"x": float(K["x"][r]), "y": float(K["y"][r]), "ile": int(K["ile"][r]), "age_h": age_h,
            "sigma_m": float(K["sigma"][r]), "rayon_m": float(K["sigma"][r] + K["vitesse"][r] * age_h * 3600.0),
            "source": SOURCES[int(K["source"][r])], "confiance": float(K["conf"][r]),
            "observateur": int(K["observateur"][r]), "observations": int(K["n_obs"][r]), "taille": float(K["taille"][r])}


def connaissances(p, camp):
    """{ cible : connaissance } de tout ce que le camp sait."""
    d = _dom(p); ci = _camp(d, camp)
    return {c: connaissance(p, ci, c) for (k, c) in sorted(d.conn_idx) if k == ci}


def a_vu(p, hid, camp=CAMP_NATIONAL):
    """La connaissance INDIVIDUELLE : les cibles que ce soldat ( ou cette entite ) a lui-meme vues [ ( pas, cible,
    distance ) ], dans la memoire bornee."""
    d = _dom(p); ci = _camp(d, camp)
    return [(t, c, dist) for t, k, o, c, dist in d.vus if k == ci and o == int(hid)]


def erreur_position(p, camp, cible):
    """La VERITE ( pour les portes, jamais pour une decision ) : l ecart en m entre la position crue et la vraie."""
    d = _dom(p); r = d.conn_idx.get((_camp(d, camp), int(cible)))
    if r is None or cible < 0 or cible >= CIBLE_UNITE0: return None
    E = d.ent
    return float(math.hypot(d.conn["x"][r] - E["x"][cible], d.conn["y"][r] - E["y"][cible]))


# ================================================================== la sante : l hopital militaire et l evacuation
def _installer_sante(p, d):
    """L hopital militaire a la base de l etat-major de la premiere brigade ; des officiers de la base comme medecins,
    ses secouristes comme infirmiers ( le moteur n a pas de corps de sante militaire : a calibrer ) ; les helicopteres
    a la nation, une ambulance par base."""
    a = A._dom(p); E = a.eff; w = p.w; parc = p.socle.parc
    brig = [x for x in d.depots if x.niveau == "brigade"]
    if not brig: return
    b = brig[0].base
    rows = A._lignes(a)
    lits = max(LITS_MIN, int(round(LITS_PAR_MILITAIRE * len(rows))))
    e = HM.hopital_militaire(p, w.carte.par_n[b].id, lits, rea=max(1, lits // 20), blocs=1)
    rb = rows[E["base"][rows] == b]
    offs = E["hid"][rb[E["spec"][rb] == A.OFFICIER]].tolist()
    inf = E["hid"][rb[E["spec"][rb] == A.SECOURISTE]].tolist()
    HM.affecter_personnel(p, e, medecins=offs[:max(1, lits // 10)], infirmiers=inf)
    d.hopital = e
    mh = parc.declarer_modele("uh1h_evasan", "aeronef", _dr(6.0e6), 4300.0, 30000.0, "CUP_B_UH1D_GER_KSK", None,
                              "Bell UH-1H ( l aviation de l armee de terre grecque en a eu une centaine, a verifier ) : "
                              "~ 200 km/h, ~ 320 l/h ; prix a calibrer ; classname de CUP a verifier")
    ma = parc.declarer_modele("ambulance_militaire", "vehicule", _dr(1.5e5), 3500.0, 20000.0, "CUP_B_HMMWV_Ambulance_USA",
                              None, "HMMWV M997 ambulance ( ou Steyr sanitaire, a verifier ) ; prix a calibrer")
    d.mids = {"helico": mh.id, "ambulance": ma.id}
    for _ in range(HELICOS_PAR_BRIGADE * len(brig)):
        d.helicos.append(parc.creer(mh.id, d.national, w.carte.par_n[b].id, "initial", p.w.pas).id)
    for bb in d.bases:
        dep = d.depots[d.depot_de_base[bb]]
        d.ambulances[bb] = parc.creer(ma.id, dep, w.carte.par_n[bb].id, "initial", p.w.pas).id


def evacuer(p, hid, lieu=None, moyen="auto"):
    """Domaine 27 : l evacuation sanitaire d un militaire vers l hopital militaire. Par HELICOPTERE s il y en a un libre
    et le kerosene du vol aller-retour au depot national ( qu il brule ), sinon par AMBULANCE militaire de sa base.
    Le transport est fait ici ; le domaine 17 recoit le patient au pas d arrivee ( `admettre`, delai_pas ). Rend
    { moyen, minutes, pas, passage } ou None ( deja pris en charge, pas d hopital )."""
    d = _dom(p); w = p.w; a = A._dom(p)
    if d.hopital is None: return None
    r = int(p.col("habitant", "ar_rang")[hid])
    if lieu is None:
        lieu = w.carte.par_n[int(a.eff["base"][r])].id if r >= 0 else w.carte.par_n[int(w.table.lieu[hid])].id
    o, h_ = w.carte.lieux[lieu], w.carte.lieux[d.hopital.lieu]
    km = o.distance(h_) / 1000.0 if o.ile == h_.ile else KM_MER_ESTAFETTE
    libre = [x for x in d.helicos if d.helico_libre.get(x, -1) <= w.pas]
    vol_h = km / VITESSE_HELICO_KMH
    kero = 2.0 * vol_h * CONSO_HELICO_U_H
    if moyen in ("auto", "helicoptere") and libre and d.national.stock[d.ids["kerosene"]] >= kero:
        minutes = PREPARATION_HELICO_MIN + 2.0 * vol_h * 60.0 + CHARGEMENT_MIN
        m = "helicoptere"
    elif moyen == "helicoptere":
        return None
    else:
        km_r = w.carte.km_route(o, h_) if o.ile == h_.ile else km
        minutes = PREPARATION_AMBULANCE_MIN + km_r / VITESSE_AMBULANCE_KMH * 60.0
        m = "ambulance"
    pas = max(1, math.ceil(minutes / MIN_PAS - 1e-9))
    ps = HM.admettre(p, PO.Habitant(w.table, int(hid)), destination=d.hopital, origine=lieu, delai_pas=pas - 1)   # arrive a +pas
    if ps is None: return None
    if m == "helicoptere":
        _sortir(p, d, "depot", d.national.k, "kerosene", kero, "vol_evasan", "brule")
        d.helico_libre[libre[0]] = w.pas + pas
    d.evacuations.append((w.pas, int(hid), m, minutes))
    p.noter("evacuation_sanitaire", habitant=int(hid), moyen=m, minutes=round(minutes, 1))
    return {"moyen": m, "minutes": minutes, "pas": pas, "passage": ps}


# ================================================================== les vivres de crise
def requisitionner_vivres(p, vers, kcal):
    """En crise ( agriculture installee ) : des vivres stockables des fermes de l ile entrent chez `vers` - une
    garnison ( identifiant de lieu de sa base : la troupe les prend sur place et les mange, `_consommer_vivres` ) ou un
    depot ( numero ) -, par le grand livre ( domaine 9, `requisitionner` ), les fermes les plus fournies d abord ;
    l Etat indemnise la ferme au prix du domaine 9 ( la loi grecque de requisition ouvre droit a indemnite ). Rend les
    jours-homme obtenus ( 3 600 kcal ). Les vivres requisitionnes d un depot ne sont pas encore expedies aux garnisons
    ( seules les rations le sont )."""
    if not p.a("agriculture"): return 0.0
    from . import d09_agriculture as AG
    d = _dom(p); w = p.w
    if isinstance(vers, str):
        b = w.carte.lieux[vers].n; genre, cle, lieu_ile = "base", b, w.carte.par_n[b].ile
    else:
        genre, cle = "depot", int(vers); lieu_ile = d.depots[cle].ile
    cible = _contenant(p, d, genre, cle, RATION)
    stocks, _ = AG.stocks_vivres(p, lieu_ile)
    reste = float(kcal); jours = 0.0
    for lieu in sorted(stocks, key=lambda l: (-math.fsum(stocks[l].values()), l)):
        for bien in ("cereales", "farine", "huile", "fromage"):
            if reste <= EPS: break
            kg = min(stocks[lieu].get(bien, 0.0), reste / AG.KCAL[bien])
            if kg <= EPS: continue
            if bien not in d.ids:
                d.ids[bien] = p.socle.catalogue.id(bien); d.vivres.append((d.ids[bien], AG.KCAL[bien] / KCAL_RATION))
            q = AG.requisitionner(p, lieu, bien, kg, cible, "requisition_militaire")
            ex = AG.exploitation_de(p, lieu)
            if q > 0 and ex is not None:
                p.socle.livre.transferer(w.gouv, ex.ferme, q * AG.BIENS[bien][2] / EUROS, "indemnite_requisition")
            _compter_flux(d, bien, "entree", "requisition_militaire", q)
            reste -= q * AG.KCAL[bien]; jours += q * AG.KCAL[bien] / KCAL_RATION
    d.requisitions.append((p.jour, genre, cle, jours))
    return jours


# ================================================================== l installation
MOTIFS = (("dotation_initiale_soutien", "achat"), ("achat_militaire", "achat"), ("consommation_campagne", "achat"),
          ("rotation_rations", "achat"), ("chargement_militaire", "achat"), ("livraison_militaire", "achat"),
          ("carburant_convoi_militaire", "achat"), ("vol_evasan", "achat"), ("requisition_militaire", "achat"),
          ("indemnite_requisition", "achat"), ("retour_lot_militaire", "achat"))
MOTIF_CONVOI = "convoi_militaire"
RECEPTEUR = "armee_soutien"


def installer(p):
    w = p.w; L = p.socle.livre; cat = p.socle.catalogue; a = A._dom(p)
    d = Soutien()
    p.domaines[DOMAINE] = d
    cat.declarer(RATION, "aliment", "une ration de combat : les repas d un homme pour un jour ( ~ 3 600 kcal )",
                 _dr(PRIX_RATION_EUR), categorie_tva="reduite", masse_kg=MASSE_RATION_KG, volume_l=VOLUME_RATION_L,
                 conservation_j=CONSERVATION_RATION_J, source=SOURCE_RATION)
    d.ids = {n: cat.id(n) for n in ("carburant", "kerosene", "pieces", RATION) + A.NOMS_MUNITIONS}
    d.vivres = [(d.ids[RATION], 1.0)]
    for m, nature in MOTIFS: L.declarer_motif(m, nature, DOMAINE)
    J = p.socle.journal
    J.declarer("convoi_militaire", DOMAINE, "individuel", ("de", "vers", "tonnes"))
    J.declarer("evacuation_sanitaire", DOMAINE, "individuel", ("habitant", "moyen", "minutes"))
    J.declarer(SUJET_PRESENCE, DOMAINE, "individuel", ("lieu", "camp", "taille"))
    for t in ("decision_ravitaillement", "demande_ravitaillement", "convoi_militaire_refuse", "livraison_militaire",
              "rupture_ravitaillement", "achat_militaire", "rotation_rations", "ordre_emis", "ordre_recu", "ordre_perdu",
              "ordre_mal_compris", "observation", "contact", "interception", "dislocation_h"):
        J.declarer(t, DOMAINE, "compte")
    d.pos_lieux = np.array([l.pos for l in w.carte.par_n], np.float64)
    d.ile_lieu = np.array([w.carte.iles.index(l.ile) for l in w.carte.par_n], np.int64)
    # les garnisons, leurs bataillons, leurs brigades
    d.bases = list(a.bases)
    U = a.unites
    for b in d.bases:
        bats = [u for u in A.unites(p, "bataillon") if int(U["base"][u]) == b]
        d.bataillon_de[b] = bats[0] if bats else a.armee_u
        d.brigade_de_base[b] = int(U["a1"][d.bataillon_de[b]]) if bats else -1
        d.ile_de_base[b] = w.carte.par_n[b].ile
    # les depots : la nation, puis une brigade par ile a sa base la plus peuplee ( son etat-major )
    rows = A._lignes(a)
    eff = np.bincount(a.eff["base"][rows], minlength=len(w.carte.par_n))
    d.national = Depot(0, "national", w.depot_armee.id, w.depot_armee.ile, a.armee_u, -1)
    d.depots.append(d.national)
    for ile, bu in sorted(a.brigades.items(), key=lambda x: w.carte.iles.index(x[0])):
        bs = [b for b in d.bases if w.carte.par_n[b].ile == ile]
        if not bs: continue
        hq = max(bs, key=lambda b: (int(eff[b]), -b))
        dep = Depot(len(d.depots), "brigade", w.carte.par_n[hq].id, ile, bu, hq)
        d.depots.append(dep)
        for b in bs: d.depot_de_base[b] = dep.k
    for b in d.bases:
        if b not in d.depot_de_base: d.depot_de_base[b] = d.national.k
    p.socle.registre.inscrire("depots_militaires", "administrations", _membres_depots, None, "stock")
    _besoins(p, d)
    _installer_sante(p, d)
    _poser_cibles(p, d)
    _dotation_initiale(p, d)
    # le renseignement : le camp national, sa cellule au domaine 22, la nouvelle de presence
    # sa cellule apprend la ou vivent et travaillent ses militaires ( la rumeur court dans les lieux habites )
    dom = w.table.domicile[a.eff["hid"][rows]].astype(np.int64)
    pd = np.bincount(dom[dom >= 0], minlength=len(w.carte.par_n)) + eff
    poids = {w.carte.par_n[k].id: float(pd[k]) for k in np.nonzero(pd)[0].tolist()}
    poser_camp(p, CAMP_NATIONAL, poids, max(1, len(rows)), cote="WEST", visible=False, national=True)
    MED.declarer_nouvelle(p, SUJET_PRESENCE, SUJET_PRESENCE, champ="taille", spec=SPEC_PRESENCE)
    # le commandement et la decision
    d.decideur = p.decideur(POINT)
    p.echeance("armee_soutien_ordre", _ordre_recu)
    p.echeance("armee_soutien_plan", _etape)
    LG.recevoir_convoi(p, MOTIF_CONVOI, _arrivee_convoi)
    LG.recevoir_lot(p, RECEPTEUR, _recevoir_lot, _retour_lot)
    p.routine(6 + 40 / 60, 70, DOMAINE, _matin)
    for h in range(24): p.routine(h + 20 / 60, 70, DOMAINE, _heure)
    p.routine(12.0, 70, DOMAINE, _consommer)
    p.routine(18.0 + 30 / 60, 70, DOMAINE, _ecouter)
    p.routine(22 + 50 / 60, 70, DOMAINE, _soir)
    return d


# ================================================================== les controles
def perimetre(p):
    """{ bien : quantite } du PERIMETRE militaire : depots, armureries ( munitions, pieces, vivres ), garnisons et stock
    public de l armee ( gazole ), convois militaires en route ( motifs convoi_militaire et ravitaillement_base ) et lots
    par mer du domaine. C est ce que le livre du domaine doit expliquer."""
    d = _dom(p); w = p.w; cat = p.socle.catalogue
    noms = ("carburant", "kerosene", "pieces") + tuple(cat[b].nom for b, _ in d.vivres) + A.NOMS_MUNITIONS
    out = {n: [] for n in noms}
    ids = {n: cat.id(n) for n in noms}
    for dep in d.depots:
        for n in noms: out[n].append(dep.stock[ids[n]])
    for arm in A._dom(p).armureries:
        for n in noms:
            if n != "carburant": out[n].append(arm.stock[ids[n]])
    for g in w.garnisons.values(): out["carburant"].append(g.get("carburant", 0.0))
    out["carburant"].append(w.publics["armee"].get("carburant", 0.0))
    for c in w.convois:
        if c.motif in (MOTIF_CONVOI, "ravitaillement_base"):
            for n, q in c.cargaison.items():
                if n in out: out[n].append(q)
    lots = LG._lg(p).lots
    for lid in sorted(d.lots):
        lot = lots.get(lid)
        if lot is not None and lot.bien in out: out[lot.bien].append(lot.q)
    return {n: math.fsum(v) for n, v in out.items()}


def flux_nets(p):
    """{ bien : entrees - sorties } comptees par le domaine depuis l installation."""
    out = {}
    for (b, sens, _), q in _dom(p).flux.items(): out[b] = out.get(b, 0.0) + (q if sens == "entree" else -q)
    return out


def anomalies(p):
    """Les incoherences du domaine : [ ( type, detail ) ].
      croyance_sans_source     une connaissance active sans source ( ou d une source inconnue )
      croyance_du_futur        une connaissance datee apres maintenant
      observation_sans_guetteur une observation ou une patrouille sans observateur
      croyance_sur_soi         un camp qui se connait lui-meme comme cible
      ordre_recu_avant_emission, ordre_recu_sans_date, ordre_perdu_recu, ordre_du_futur
      convoi_militaire_perdu   un convoi en route du domaine absent de Monde.convois
      marche_sans_destination  une suite d ordres Arma qui ne pose pas la destination d abord"""
    d = _dom(p); w = p.w; K = d.conn; out = []
    for (ci, c), r in sorted(d.conn_idx.items()):
        s = int(K["source"][r])
        if not K["actif"][r]: continue
        if s <= AUCUNE or s >= len(SOURCES): out.append(("croyance_sans_source", (d.camps[ci].nom, c)))
        if K["t"][r] > w.pas or K["t"][r] < 0: out.append(("croyance_du_futur", (d.camps[ci].nom, c)))
        if s in (OBSERVATION, PATROUILLE) and K["observateur"][r] < 0: out.append(("observation_sans_guetteur", (ci, c)))
        if 0 <= c < CIBLE_UNITE0 and c < d.ent.n and int(d.ent["camp"][c]) == ci: out.append(("croyance_sur_soi", (ci, c)))
    Od = d.ordres; n = Od.n
    if n:
        te, tr, et = Od["t_emis"][:n], Od["t_recu"][:n], Od["etat"][:n]
        for k in np.nonzero((tr >= 0) & (tr < te))[0].tolist(): out.append(("ordre_recu_avant_emission", k))
        for k in np.nonzero((et == RECU) & (tr < 0))[0].tolist(): out.append(("ordre_recu_sans_date", k))
        for k in np.nonzero((et == PERDU) & (tr >= 0))[0].tolist(): out.append(("ordre_perdu_recu", k))
        for k in np.nonzero(te > w.pas)[0].tolist(): out.append(("ordre_du_futur", k))
    ids = {c.id for c in w.convois}
    for cid in sorted(d.en_route):
        if cid not in ids: out.append(("convoi_militaire_perdu", cid))
    for _, _, _, seq in d.ordres_arma:
        if seq and seq[0][0] != "setDestination": out.append(("marche_sans_destination", seq[0]))
    return out


# ================================================================== le scenario de la decision
def scenario_ravitaillement(n_brigades=12, garnisons=10, jours=21, mode="hasard", graine=7, mer_fermee=(4, 14),
                            p_coupure=0.05, part_iles=0.4, serie=False):
    """La porte de decision : `n_brigades` depots de brigade ( sur l ile principale ), chacun `garnisons` garnisons dont
    `part_iles` sur d autres iles ( la mer seulement ), en CRISE ( posture de combat, intensite 0,5 a 1,2 ). Chaque jour :
    le S4 de chaque garnison decide ( memes traits, meme regle, meme temoin, meme note que dans le monde ) ; sa demande
    est un camion de 5 t reparti par `_repartir` ; la route livre dans le jour ( sauf coupure : `p_coupure` par garnison
    et par jour, deux jours ), la mer en deux jours si elle est ouverte ( fermee de `mer_fermee[0]` a `mer_fermee[1]` :
    les lots attendent au port ) ; un ordre sur 25 est mal compris ( une autre classe, P_MAL radio ) ; puis la
    consommation, les ruptures, la note. Le depot de brigade n est reapprovisionne qu a 80 % du besoin de ses
    garnisons : il ne peut pas tout servir, et le choix compte. Rend le Decideur ( et la serie si `serie` )."""
    rng = np.random.default_rng(graine)
    n = n_brigades * garnisons
    brig = np.repeat(np.arange(n_brigades), garnisons)
    ile = rng.random(n) < part_iles
    # besoins d un jour de combat, en kg ( gazole, munitions, vivres ) : a calibrer ( ordres de grandeur d un bataillon )
    besoin = np.column_stack((rng.uniform(300, 900, n), rng.uniform(500, 2000, n), rng.uniform(480, 960, n)))
    intens = rng.uniform(0.5, 1.2, n)
    cible = besoin * np.array(CIBLE_GARNISON)[None, :]
    stock = besoin * rng.uniform(0.3, 3.0, (n, 3))
    depot = np.zeros((n_brigades, 3))
    for g in range(n_brigades): depot[g] = JOURS_BRIGADE * besoin[brig == g].sum(axis=0)
    cible_dep = depot.copy()
    reappro = 0.8 * np.array([besoin[brig == g].sum(axis=0) for g in range(n_brigades)])
    coupe = np.zeros(n, np.int64)
    arrivee = {}                                   # jour -> [ ( garnison, kg par classe ) ]
    port = []                                      # [ ( garnison, kg ) ] en attente de la mer
    dec = D.Decideur(POINT, mode, rng=np.random.default_rng(graine + 1), graine=graine)
    out = []
    stock0 = stock.copy()
    for jour in range(jours):
        mer = not (mer_fermee is not None and mer_fermee[0] <= jour < mer_fermee[1])
        coupe = np.maximum(0, coupe - 1)
        coupe[(rng.random(n) < p_coupure) & ~ile] = 2
        u_mal = rng.random(n); u_cl = rng.random(n)
        en_route = np.zeros(n, bool)
        for j, lst in arrivee.items():
            if j >= jour:
                for i, _ in lst: en_route[i] = True
        for i, _ in port: en_route[i] = True
        act = np.zeros(n, np.int64)
        for i in range(n):
            g = brig[i]
            rem = [float(min(1.0, stock[i, c] / cible[i, c])) for c in range(3)]
            dr = [float(np.clip(depot[g, c] / cible_dep[g, c], 0.0, 1.0)) for c in range(3)]
            x = rem + [float(min(1.0, intens[i])), float(coupe[i] == 0 and not ile[i]), float(mer), float(ile[i])] + dr \
                + [float(en_route[i])]
            a = dec.decider(i, ContexteGarnison(x))
            act[i] = a
            moyen, classe = _action(a)
            if moyen is None: continue
            dec.ajouter(i, -(COUT_ROUTE if moyen == "route" else COUT_MER))
            if u_mal[i] < P_MAL[RADIO_M]: classe = (classe + 1 + int(u_cl[i] * 3)) % 4
            if (moyen == "route") == bool(ile[i]): continue          # un moyen impossible : le cout sans livraison
            defic = np.minimum(np.maximum(0.0, cible[i] - stock[i]), depot[g])
            ordre = sorted(range(3), key=lambda c: (rem[c] * CIBLE_GARNISON[c], c))
            kg = np.array(_repartir(list(defic), CHARGE_CAMION_KG, classe, ordre))
            depot[g] -= kg
            if moyen == "route":
                if coupe[i] > 0: depot[g] += kg; continue            # la route est coupee : le camion ne part pas
                arrivee.setdefault(jour, []).append((i, kg))
            else: port.append((i, kg))
        if mer:
            for i, kg in port: arrivee.setdefault(jour + 2, []).append((i, kg))
            port = []
        for i, kg in arrivee.pop(jour, []): stock[i] += kg
        rupt = np.zeros(n, np.int64); manque = np.zeros((n, 3), bool)
        for c in range(3):
            q = besoin[:, c] * intens
            manque[:, c] = stock[:, c] < q * (1 - 1e-9)
            rupt += manque[:, c]
            stock[:, c] = np.maximum(0.0, stock[:, c] - q)
        for i in range(n):
            dec.noter(i, _note_jour(stock[i] / cible[i], int(rupt[i])), jour)
        depot = np.minimum(depot + reappro, cible_dep)
        if serie: out.append({"jour": jour, "autonomie": stock / (besoin * intens[:, None]), "ruptures": rupt.copy(),
                              "manque": manque, "actions": act.copy(), "mer": mer})
    if serie: return dec, {"ile": ile, "serie": out, "besoin": besoin, "intensite": intens, "stock0": stock0}
    return dec


# ================================================================== ce que le domaine donne aux autres ( 27 )
def depots(p):
    """[ { depot, niveau, lieu, ile, brigade, remplissage ( carburant, munitions, vivres ), stock { bien : q } } ]."""
    d = _dom(p); cat = p.socle.catalogue; out = []
    for dep in d.depots:
        st = {cat[b].nom: q for b, q in sorted(dep.stock.items())}
        if dep.niveau == "national": st["carburant"] = p.w.publics["armee"].get("carburant", 0.0)
        out.append({"depot": dep.k, "niveau": dep.niveau, "lieu": dep.lieu, "ile": dep.ile, "brigade": dep.brigade,
                    "remplissage": _remplissage_depot(p, d, dep.k), "stock": st})
    return out


def besoins_combat(p, base):
    """( gazole en unites de 10 l, { munition : coups }, rations ) d un jour de combat de la garnison."""
    return _dom(p).besoins[_base_n(p, base)]


def demander(p, base, classe="mixte", moyen="route", frictions=True):
    """Domaine 27 : la garnison demande un ravitaillement a sa brigade hors du point de decision ( un ordre ). Rend le
    numero de l ordre."""
    d = _dom(p); b = _base_n(p, base)
    c = MIXTE if classe == "mixte" else CLASSES.index(classe)
    dep = d.depots[d.depot_de_base[b]]
    return emettre_ordre(p, d.bataillon_de[b], dep.brigade, "demande", a=b, b=c, c=0 if moyen == "route" else 1,
                         frictions=frictions)


def ruptures(p):
    """[ ( jour, base, classe ) ] des ruptures depuis l installation."""
    d = _dom(p)
    return [(j, p.w.carte.par_n[b].id, CLASSES[c]) for j, b, c in d.ruptures]


def a_incarner(p):
    """Le pont : les convois militaires en route, chacun avec sa DESTINATION ( a poser avant l ordre de marche ) et un
    decalage de depart par vehicule ( domaine 14 `emplacements` : deux vehicules crees au meme point se detruisent ) ;
    les suites d ordres de mouvement des unites ( setDestination d abord )."""
    d = _dom(p); w = p.w; out = []
    par_origine = {}
    for c in w.convois:
        if c.id in d.en_route: par_origine.setdefault(c.origine.id, []).append(c)
    for oid in sorted(par_origine):
        lst = par_origine[oid]
        for c, (dx, dy) in zip(lst, TP.emplacements(len(lst))):
            out.append({"convoi": c.id, "classname": A.VEHICULE[CAMION].arma, "origine": oid, "depart_pas": c.depart,
                        "depart": (c.origine.pos[0] + dx, c.origine.pos[1] + dy), "destination": c.destination.pos,
                        "chauffeur": c.conducteur,
                        "ordres": [("setDestination", c.id, c.destination.pos), ("moveTo", c.id, c.destination.pos)]})
    return {"convois": out, "mouvements": list(d.ordres_arma)}


def camps(p):
    """[ { nom, cote, national, cellule du domaine 22, stations d ecoute } ]."""
    return [{"nom": c.nom, "cote": c.cote, "national": c.national, "cellule": c.cellule, "ecoutes": len(c.ecoutes)}
            for c in _dom(p).camps]


def entites(p, camp=None):
    """[ ( numero, camp, x, y, ile, posture, taille, vivant ) ]."""
    d = _dom(p); E = d.ent; ci = None if camp is None else _camp(d, camp)
    return [(k, d.camps[int(E["camp"][k])].nom, float(E["x"][k]), float(E["y"][k]), int(E["ile"][k]),
             POSTURES_CIBLE[int(E["posture"][k])], int(E["taille"][k]), bool(E["vivant"][k]))
            for k in range(E.n) if ci is None or int(E["camp"][k]) == ci]


def cible_unite(u):
    """La cible qu est une unite du domaine 25 pour un autre camp."""
    return CIBLE_UNITE0 + int(u)
