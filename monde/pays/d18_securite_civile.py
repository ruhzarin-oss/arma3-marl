"""DOMAINE 18 - SECURITE CIVILE : INCENDIES, POMPIERS, SECOURS ROUTIERS, SEISMES, INONDATIONS.

FICHE
1. Classes. Les lois : ModeleEngin ( un engin de secours : prix, masse, reservoir d eau, equipage, debit de pompe, ligne
   d arret tenue par heure sur un feu de vegetation, vitesse, consommation, classname Arma ; et son Modele au Parc du
   socle, famille vehicule ). Les detenteurs : ServiceIncendie ( le Corps des pompiers : une caisse, famille nouvelle
   `service_incendie`, secteur administrations ). L etat : Caserne ( un centre de secours par marche : son batiment du
   domaine 13, ses engins, ses pompiers professionnels et volontaires, la garde du jour ), Engin ( un individu du Parc :
   eau dans la citerne, mission, arrivee, retour, equipage ), Sinistre ( un incendie de logement ou de site
   industriel, un feu de vegetation, un secours routier, un effondrement apres un seisme, une crue : sa part brulee ou
   ses hectares, son appel, ses engins, son eau, ses victimes ), ContexteDispatch, SecuriteCivile ( l etat du domaine ).
   Aucune colonne par habitant : les pompiers, les victimes, les sinistres sont des tables eparses ( quelques pour mille ).
   Pas de canadair : la Grece en arme ~ 2 par million d habitants ( CL-215 et CL-415 ), soit zero a 10 000 comme a
   100 000 habitants ; un pays de plusieurs millions devra le declarer ( modele aeronef, ecope en mer, a faire ).
2. Invariants et ce que le domaine detient. OBJETS : chaque engin de mes modeles nait au recensement ( initial ) ou par
   un import de remplacement ( importe ) et ne sort que detruit ( pris par le feu ) ; comptes du Parc = naissances et
   sorties faites par le domaine, individus du Parc = ma table d engins ( `audit_engins` ). EAU : l eau d extinction
   entre par `prelever_incendie` des services publics ( ou, sans eux, par `prelever` du territoire, usage domestique ) et
   n en sort que versee sur un sinistre ou perdue avec un engin detruit : preleve = verse + citernes + perdu, au m3
   ( `bilan_eau` ) ; avec les services publics, ce que j ai tire aux bornes = leur compteur `c_incendie`. ARGENT : la
   caisse du Service par le grand livre seulement : dotation de l Etat, soldes des professionnels, vacations des
   volontaires, carburant et entretien ( domaine 14 ), imports d engins ( domaine 7 ). DEGATS : un batiment n est
   endommage que par `IM.endommager` ( `audit_degats` : tout batiment endommage du domaine 13 a son sinistre enregistre
   au meme niveau ) ; un sinistre n est eteint que par une cause declaree et verifiable ( attaque : de l eau versee et
   un engin sur place ; consume ; meteo ; combustible ; secours termine ) : `audit_sinistres`.
3. Decision `dispatch` ( a chaque pas ou un sinistre appele attend des engins ET que les engins libres de l ile ne
   suffisent pas a tous ceux qui attendent : le dilemme ) : complet ( le nombre d engins que le sinistre demande, les plus
   proches ), reduit ( un seul engin, renforce au plus tot apres la reconnaissance, 30 minutes ), differer ( aucun :
   les engins restent pour les autres, le sinistre est reconsidere dans 30 minutes ), renforts ( les engins d une
   caserne plus lointaine : la plus proche reste libre pour la file ). Traits : nature annoncee,
   victimes signalees par l appelant ( elles peuvent manquer ou etre fausses ), km du premier engin libre, part des
   engins libres de l ile, file d attente, FFDI et vent du bulletin, borne au lieu, nuit, attente deja subie. Jamais la
   part brulee vraie ni les pieges vrais. Note ( horizon 3 jours : un brule meurt en jours, un feu de foret dure ) :
   chaque jour, pour CE sinistre ET ceux qui attendaient au moment du choix ( le meme groupe quelle que soit l action,
   lecon du domaine 17 ), 1 - la perte moyenne SURVENUE DEPUIS LE CHOIX : part de valeur detruite ( ratios de dommage
   du domaine 13 ), hectares, maisons, et 0,5 par mort parmi les victimes, moins ce qui etait deja perdu au moment du
   choix ( un logement deja consume a l appel ne dit rien du choix ). Regle : tout envoyer s il y a des victimes signalees, un site industriel
   ou un feu de vegetation par temps a risque, ou une attente de plus d une heure ; differer un petit sinistre quand
   d autres attendent ; un seul engin quand l ile n en a plus qu un tiers de libres. Temoin : premier appel, premier servi,
   tout ce qu il demande, par les plus proches.
   MESURE DU 26/09 ( test_decision ) : la porte ECHOUE. En mode hasard, 231 decisions a 3 000 habitants, part du choix
   0,000 ( p 1 ) ; a 30 000 habitants ( 500 a 1 300 decisions ) : 0,000 a 0,015, p >= 0,15. Sous la penurie, le choix
   DEPLACE la perte entre ce sinistre et ceux qui attendent ( le temps-engin se conserve ) : l effet principal de l action,
   seul vu par la part du choix, est presque nul. Le choix compte pourtant, par son contexte : perte moyenne par sinistre
   0,138 sous la regle, 0,181 au hasard, 0,226 sous le temoin ( premier appel, tout envoyer ).
4. Evenements. Individuels : incendie, feu_de_vegetation, sauvetage_decombres, crue_secours. Comptes : depart_de_feu,
   sortie_engin, sauvetage, deces_incendie, blesse_incendie, desincarceration, evacuation, eau_incendie ( m3 ),
   engin_perdu, decision_dispatch.
5. Liens. Immobilier ( 13 ) : `batiments`, `fiche`, `endommager( b, D1-D5, "incendie" )` ( relogement, reparation,
   reconstruction : le domaine 13 ), `appliquer_seisme` ( scenario ), le batiment de chaque caserne ( modele
   bureau_public par `_nouveau`, faute d un modele caserne_pompiers : a demander au 13 ). Transport ( 14 ) :
   `faire_le_plein`, `entretenir` ( modele camion en guise de camion de pompiers ), `accidents_du_jour` ( secours
   routiers ), `emplacements` ( pont ). N utilise PAS `acheter_flotte` : une flotte de l Etat y plante ( `_flottes`
   appelle `au_travail_de( lieu, "" )` : KeyError, defaut connu du 14 ). Hopitaux ( 17 ) et medecine ( 16 ) :
   `M.blesser( h, "brulure" | "ecrasement", ISS )` ( le blesse d ISS >= 9 est aussitot pris en charge par `soigner`, donc
   par `admettre` du 17 ) ; `HP.admettre` pour les intoxiques legers ; population ( 1 ) : `deceder( h, "accident" )`.
   Territoire ( 8 ) : `risque_incendie` ( FFDI ), `meteo` ( vent, pluie ), `catastrophes_en_cours` ( seismes avec
   intensites, crues ), `rejeter` ( pm25 des fumees ), `prelever` sans services publics. Services publics ( 12, si
   installes ) : `borne_incendie`, `prelever_incendie`, `facteur_vitesse`, `route_ouverte`. Logistique ( 15, si
   installee ) : `route_praticable`. Etat ( 6 ) : `assurer` avant chaque dotation. Exterieur ( 7 ) : `declarer_import`
   des engins de remplacement. Paie et recoit : Etat -> Service ( dotation_securite_civile ), Service -> menages
   ( solde_pompier, vacation_pompier ), Service -> stations et garages ( 14 ), Service -> exterieur ( import d engins ).
   Ne remplace aucune methode du moteur. API en fin de fichier pour les domaines 20, 21, 25 a 27.
   LIMITE DU MOTEUR : il n a pas de metier « pompier » ( config.ROLES ). Les pompiers sont des habitants adultes de la
   zone, hors metiers publics, inscrits au registre du Corps ; ils GARDENT leur metier du moteur, qui continue de les
   placer et de les payer. Il faudrait un role pompier ( garde, capitale ) dans config et population ( Younes ).
6. Portes : tests_d18_securite_civile.py.
7. Arma. Aucun camion de pompiers au jeu de base : corps de substitution plausibles, a verifier en jeu : fourgon pompe
   C_IDAP_Truck_02_water_F ( Zamak citerne IDAP, Laws of War ), camion-citerne feux de forets C_Truck_02_fuel_F ( Zamak
   citerne civil ), vehicule de secours routier C_Van_02_service_F ; caserne : Land_Offices_01_V1_F ( bureau public du
   13 ) ; arma_preuve = None partout. Un engin ne roule qu avec sa destination posee AVANT l ordre de marche ; deux engins
   poses au meme point se detruisent : `engins` rend les decalages de `TR.emplacements`.
8. Cout. Hors sinistre : une passe numpy par jour sur la table des batiments ( tirage des departs de feu ), une boucle
   sur les pompiers ( soldes, garde : ~ 1,4 pour 1 000 habitants ), rien a chaque pas. Un sinistre actif pose un tic a
   chaque pas ( echeance ) qui ne touche que les sinistres et les engins en cours. Mesure du 26/09 ( test_cout, coeur
   Rust, 10 000 habitants ) : routines propres ~ 1 ms par jour, 0,3 % d une journee du moteur seul ( 0,30 s ) ; un ete a
   feux x 300 ne se voit pas dans la journee du pays. Installation hors climatologie : 7 ms a 10 000 habitants, 12 ms a
   100 000 ( x 1,8 ) ; climatologie ~ 0,36 s par ile, fixe. Memoire : ~ 1 Ko par sinistre ouvert, une ligne d archive
   par sinistre clos ( pour les domaines 20 et 21 ), les pompiers en listes d identifiants. Installation : une passe numpy sur
   les habitants par zone ( recrutement ), les lieux de chaque ile ( voisinages : lieux au carre, ~ 70 sur Altis ), 32 ans
   de meteo simulee par ile, vectorises ( la moyenne du FFDI qui norme les departs de feux de vegetation )."""
import math
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D, objets as O
from . import pays as PAYS, d01_population as POP, d06_etat as ET, d07_exterieur as EXT, d08_territoire as TER
from . import d13_immobilier as IM, d14_transport as TR, d16_medecine as M, d17_hopitaux as HP

EUROS = PAYS.EUROS_PAR_DRACHME
MIN_PAS = C.MINUTES_PAR_PAS
PAS_J = C.PAS_PAR_JOUR
JOURS_AN = 365.0
EPS = 1e-9
MAISON_P = PO.CODE_POSTE["maison"]
TRAVAIL_P = PO.CODE_POSTE["travail"]
HOPITAL_P = PO.CODE_POSTE["hopital"]

# ================================================================== les engins
# nom : ( prix euros, masse kg, vie heures, classname Arma, citerne m3, equipage, debit m3 par pas, ligne km/h,
#         vitesse km/h, litres aux 100 km, source )
ENGINS = (
    ("fourgon_pompe", 280000.0, 13000.0, 10000.0, "C_IDAP_Truck_02_water_F", 3.0, 3, 5.0, 0.3, 60.0, 35.0,
     "fourgon pompe-tonne urbain ( Mercedes Atego 4x2, 3 000 L, pompe 2 lances de 500 L/min ) ; prix d appel d offres "
     "de l ordre de 250 000 a 300 000 euros ; a calibrer"),
    ("camion_citerne_feux_forets", 250000.0, 11000.0, 10000.0, "C_Truck_02_fuel_F", 4.0, 2, 3.0, 0.5, 50.0, 40.0,
     "camion-citerne feux de forets 4x4 ( 4 000 L ), le gros du parc grec ( ~ 1 600 citernes ) ; a calibrer"),
    ("vehicule_secours_routier", 150000.0, 5000.0, 8000.0, "C_Van_02_service_F", 0.0, 2, 0.0, 0.0, 70.0, 14.0,
     "fourgon de desincarceration ( outils hydrauliques ) ; a calibrer"),
)
NOMS_ENGINS = tuple(e[0] for e in ENGINS)
FPT, CCF, VSR = 0, 1, 2
CITERNE = tuple(e[5] for e in ENGINS)
EQUIPAGE = tuple(e[6] for e in ENGINS)
DEBIT_PAS = tuple(e[7] for e in ENGINS)            # m3 par pas de 10 min que l engin peut verser
LIGNE_KMH = tuple(e[8] for e in ENGINS)
VITESSE = tuple(e[9] for e in ENGINS)
L100 = tuple(e[10] for e in ENGINS)
L_POMPE_H = 15.0                   # litres de gazole par heure de pompe ( a calibrer )
DELAI_IMPORT_J = 90                # un engin de remplacement arrive en trois mois ( a calibrer )

# Dimensionnement ( Corps des pompiers grec : ~ 3 500 vehicules, ~ 14 500 personnels pour 10,4 millions d habitants,
# ~ 300 casernes et detachements ; ordres de grandeur, a verifier ). Planchers : une caserne tient une garde 24 h sur 24.
ENGINS_PAR_1000 = 0.35
PART_VSR = 0.10
POMPIERS_PAR_1000 = 1.4
POMPIERS_MIN = 20                  # par caserne : 5 de garde en regime 24 h / 72 h, de quoi armer ses deux engins ( a calibrer )
VOLONTAIRES_PAR_1000 = 0.5
VOLONTAIRES_MIN = 4
ROTATION = 4                       # un professionnel est de garde un jour sur quatre ( 24 h / 72 h )
P_VOLONTAIRE_DISPO = 0.35          # part des volontaires joignables un jour donne ( a calibrer )
DEPART_GARDE_MIN = 2.0             # la garde en caserne part en 2 minutes
DEPART_BENEVOLES_MIN = 8.0         # un equipage qui attend ses volontaires part en 8 minutes ( a calibrer )
KM_URBAIN = 1.5                    # trajet minimal dans le lieu de la caserne
DETOUR_KM = 2.0                    # une route coupee : detour ( a calibrer )
VITESSE_PISTE = 20.0               # km/h hors route, sur piste, ou a pied d engin
SOLDE_EUROS_MOIS = 1300.0          # brut d un pompier grec en debut de carriere ( ordre de grandeur, a verifier )
VACATION_EUROS_H = 8.0             # indemnite horaire d un volontaire en intervention ( a calibrer )
COUSSIN_J = 10                     # jours de depenses que le Tresor laisse dans la caisse du Service

# ================================================================== les departs de feu
# Logement : ~ 1 incendie pour 1 000 menages et par an ( Royaume-Uni, Home Office FIRE0102 : ~ 28 000 incendies de
# logement pour ~ 28 millions de menages ; Grece a calibrer ). Bande declaree par la porte : 0,5 a 2 pour 1 000.
TAUX_HABITATION_AN = 1.0e-3
BANDE_HABITATION = (0.5e-3, 2.0e-3)
# Site industriel, par site et par an, selon l activite ( ordre de grandeur NFPA : ~ 37 000 feux industriels par an aux
# Etats-Unis pour ~ 300 000 etablissements, ~ 0,1 ; plus pour le petrole et la metallurgie ; a calibrer ).
TAUX_INDUSTRIEL_AN = {"ferme": 0.02, "mine": 0.05, "carriere": 0.02, "puits": 0.10, "raffinerie": 0.30,
                      "centrale": 0.10, "fonderie": 0.15, "pharmacie": 0.05}
# Vegetation : Grece ~ 1 000 a 1 500 feux de foret declares par an ( EFFIS ) pour ~ 65 000 km2 de forets et maquis :
# ~ 2 feux pour 100 km2 d espace naturel et par an, proportionnels au FFDI du jour ( a calibrer ). Bande : 1 a 4.
TAUX_FORET_100KM2_AN = 2.0
BANDE_FORET = (1.0, 4.0)
PART_NATURELLE = 0.65              # part de l ile en forets, maquis et friches ( a calibrer )
ANNEES_CLIMAT = 32                 # annees simulees a l installation pour la moyenne du FFDI ( comme les normales du 8 )
SURFACE_ILE_KM2 = {"Altis": 270.0, "Stratis": 20.0, "Malden": 60.0, "Tanoa": 100.0}
HEURES_HABITATION = np.array([2, 2, 2, 2, 2, 2, 3, 4, 4, 4, 4, 5, 6, 5, 5, 5, 6, 7, 8, 8, 7, 6, 4, 3], float)
HEURES_FORET = np.array([1, 1, 1, 1, 1, 1, 1, 2, 3, 4, 6, 8, 10, 11, 11, 10, 9, 7, 5, 3, 2, 1, 1, 1], float)

# ================================================================== le feu d un batiment
# Une part brulee f de 0 a 1, croissance logistique : la piece d origine d abord ( f ~ 0,15 a 30 minutes ), puis les
# autres pieces ; un logement non attaque est consume en ~ 2 h 20 ( NIST : flashover de la piece en 3 a 5 minutes ;
# ~ 90 % des feux de logement restent confines a leur piece quand les pompiers arrivent en ~ 10 minutes, statistiques
# britanniques ; a calibrer ). Debit requis : 4 L/min par m2 en feu ( Grimwood ), soit 0,04 m3 par pas et par m2 ; trois
# pas de debit tenu eteignent.
F0 = 0.05
F_CONSUME = 0.97
CROISSANCE = {"habitation": 0.45, "industriel": 0.30}
Q_M2_PAS = 0.04
PAS_EXTINCTION = 3
SEUILS_DOMMAGE = (0.05, 0.25, 0.50, 0.80)        # f -> D1 a D5 ( D1 fumees ; D5 detruit )
P_PROPAGATION = {"capitale": 0.015, "ville": 0.02, "village": 0.03}   # par pas, par part brulee, feu non maitrise
CHARGE_KG_M2 = {"habitation": 45.0, "industriel": 60.0}   # EN 1991-1-2 : logement ~ 780 MJ/m2 ( ~ 45 kg de bois )
PM25_KG_PAR_KG = 0.010             # facteur d emission de fumee ( ~ 10 g/kg, a calibrer )
# Les personnes presentes au depart : prises au piege ( nuit : endormies ) ; les autres sortent seules, certaines
# intoxiquees. Un piege tient de 10 minutes a 1 heure ( piece fermee, a calibrer ) ; un sauvetage : 2 par engin et par pas.
P_PIEGE = {"habitation": (0.04, 0.10), "industriel": (0.02, 0.02)}    # ( jour, nuit )
SURVIE_PAS = (1, 6)
P_INTOX = 0.15
SAUVETAGES_PAR_ENGIN = 2
# ================================================================== le feu de vegetation
# McArthur Mk5 ( Noble et al. 1980 ) : vitesse de la tete R = 0,0012 FFDI W km/h, W charge de combustible ( maquis
# mediterraneen ~ 15 t/ha, a calibrer ) ; ellipse de rapport LB = 1 + 0,0012 U^2,154 ( U km/h, Alexander 1985 ).
# Cycle du jour : la vitesse tombe la nuit ( humidite ). Maitrise quand la ligne d arret batie depasse le perimetre
# ( modele de confinement de Fried et Fried 1996 ).
W_T_HA = 15.0
DIURNE = np.array([0.3] * 7 + [0.6] * 3 + [1.0] * 9 + [0.6] * 3 + [0.3] * 2)
EAU_PAR_KM_LIGNE = 2.0             # m3 d eau pour tenir un km de lisiere ( a calibrer )
DEBLAI_PAS = 6                     # une heure de noyage apres la maitrise, plus une heure par 50 ha
VOISINAGE_KM = 8.0
P_SOUS_LE_VENT = 0.4
EVACUATION_KM = 1.5
PART_WUI = (0.10, 0.03)            # part des logements d un village atteint qui brulent ( non defendu, defendu par 2 engins )
P_MORT_WUI, P_BLESSE_WUI = 0.15, 0.30   # dans une maison qui brule, sans ordre d evacuation ( Mati 2018, a calibrer )
PART_MAX_BRULEE = 0.25             # un feu ne passe pas le quart de l espace naturel de l ile ( routes, mer, relief )
REPOUSSE_J = 5 * 365               # ce qui a brule ne rebrule pas avant que le maquis repousse ( ~ 5 ans, a calibrer )
P_ENGIN_PERDU_PAS = 0.0005         # un engin pris par le feu, par pas, feu non maitrise et FFDI >= 50 ( a calibrer )
# ================================================================== secours routiers et catastrophes
P_INCARCERATION = 0.3              # accidents corporels qui demandent une desincarceration ( a calibrer )
PAS_DESINCARCERATION = 3
P_PIEGE_EFFONDREMENT = {4: 0.3, 5: 0.6}   # occupants coinces dans un batiment D4 / D5 ( Coburn et Spence 2002, a calibrer )
P_MORT_IMMEDIATE = {4: 0.1, 5: 0.3}
SURVIE_DECOMBRES_H = 36.0          # esperance de survie d un piege sous les decombres ( a calibrer )
PAS_PAR_SAUVETAGE_DECOMBRES = 3
PART_INONDABLE = (0.0, 0.005, 0.02, 0.05)    # part des residents du lieu exposes, par degre de crue ( a calibrer )
EVACUES_PAR_ENGIN_PAS = 15
PIC_CRUE_PAS = 36
P_MORT_CRUE = 0.003                # par degre de crue, pour un expose non evacue au pic ( Mandra 2017, a calibrer )

NATURES = ("habitation", "industriel", "foret", "route", "decombres", "inondation")
# Les abris d urgence ne brulent pas ici : `IM.endommager( b, D4 | D5 )` sur un abri occupe plante dans le domaine 13
# ( `_chasser` refond l abri dans sa cohorte, puis `_sortir` ne trouve plus son objet : AttributeError ), defaut signale.
LOGEMENTS_FEU = ("appartement", "maison")
GRAVITE_ANNONCEE = {"habitation": 0.5, "industriel": 0.8, "foret": 0.9, "route": 0.4, "decombres": 0.7, "inondation": 0.6}
PREFERENCE = {"habitation": (FPT, CCF, VSR), "industriel": (FPT, CCF, VSR), "foret": (CCF, FPT),
              "route": (VSR, FPT, CCF), "decombres": (FPT, VSR, CCF), "inondation": (FPT, CCF, VSR)}
COUVE, APPEL, MAITRISE, FINI = 0, 1, 2, 3
FINS = ("attaque", "consume", "meteo", "combustible", "secours")
CAUSES = ("accidentelle", "criminelle", "combat", "naturelle")

# ================================================================== la decision
ACTIONS = ("complet", "reduit", "differer", "renforts")
COMPLET, REDUIT, DIFFERER, RENFORTS = 0, 1, 2, 3
HORIZON_DISPATCH = 3
# Un choix engage : un sinistre differe n est reconsidere qu apres 30 minutes ( la file ) ; un envoi reduit n est
# renforce qu apres la reconnaissance du chef d agres, 30 minutes ( a calibrer ).
REVISION_PAS = 3


class ContexteDispatch:
    __slots__ = ("traits",)

    def __init__(self, traits): self.traits = traits


def _observer(ctx): return ctx.traits


def _regle(x, ctx):
    grav, vict, dist, libres, file, ffdi, vent, borne, nuit, att = x
    if vict >= 0.5 or att >= 0.5: return COMPLET
    if grav >= 0.8 or (grav >= 0.75 and ffdi >= 0.25): return COMPLET
    if file >= 0.2 and grav <= 0.45: return DIFFERER
    if libres <= 0.34: return REDUIT
    return COMPLET


def _temoin(x, ctx, rng): return COMPLET


POINT_DISPATCH = D.PointDeDecision(
    "dispatch", "securite_civile",
    traits=(("gravite", "la nature du sinistre annoncee par l appelant au 199"),
            ("victimes", "l appelant signale des personnes a l interieur ou coincees"),
            ("distance", "les km du premier engin libre, lus au tableau des casernes, sur 30"),
            ("libres", "la part des engins de l ile libres et armes, au tableau de garde"),
            ("file", "les autres sinistres appeles qui attendent des engins sur l ile, sur 5"),
            ("ffdi", "l indice de danger d incendie du bulletin meteo du jour, sur 100"),
            ("vent", "le vent moyen du bulletin, m/s sur 20"),
            ("borne", "le plan des bornes : une borne incendie au lieu"),
            ("nuit", "l heure de l appel : de 22 h a 7 h"),
            ("attente", "le temps deja passe depuis l appel, sur 2 heures")),
    actions=ACTIONS, observer=_observer, regle=_regle, temoin=_temoin,
    note="1 - la perte moyenne survenue depuis le choix a CE sinistre et a ceux qui attendaient ( valeur detruite, "
         "hectares, maisons, 0,5 par mort parmi leurs victimes ), chaque jour sur 3 jours",
    horizon_j=HORIZON_DISPATCH)


# ================================================================== les classes
class ServiceIncendie:
    """Le Corps des pompiers : la caisse qui recoit la dotation de l Etat et paie soldes, vacations, carburant."""
    __slots__ = ("id", "caisse", "recu_etat", "soldes", "vacations", "carburant", "entretien", "imports")

    def __init__(self):
        self.id = "service_incendie"; self.caisse = 0.0
        self.recu_etat = self.soldes = self.vacations = self.carburant = self.entretien = self.imports = 0.0


class Caserne:
    __slots__ = ("id", "lieu", "ile", "batiment", "engins", "pros", "volontaires", "garde", "benevoles", "occupes", "pop")

    def __init__(self, id, lieu, ile, batiment, pop):
        self.id, self.lieu, self.ile, self.batiment, self.pop = id, lieu, ile, batiment, pop
        self.engins, self.pros, self.volontaires = [], [], []
        self.garde, self.benevoles, self.occupes = [], [], set()


class Engin:
    __slots__ = ("oid", "modele", "caserne", "eau", "mission", "depart", "arrivee", "libre", "equipage", "km", "pompe_pas",
                 "plein_jusqu", "vivant")

    def __init__(self, oid, modele, caserne, eau):
        self.oid, self.modele, self.caserne, self.eau = oid, modele, caserne, eau
        self.mission = -1; self.depart = self.arrivee = self.libre = -1; self.plein_jusqu = -1
        self.equipage = []; self.km = 0.0; self.pompe_pas = 0; self.vivant = True


class Sinistre:
    """Un sinistre. f : part brulee d un batiment ; L : longueur de l ellipse d un feu de vegetation ( km )."""
    __slots__ = ("id", "nature", "cause", "ile", "lieu", "b", "surface", "f", "pas_feu", "pas_appel", "pas_arrivee",
                 "pas_fin", "etat", "besoin", "engins", "eau", "maitrise_pas", "fin", "dommage", "cout", "morts", "blesses",
                 "sauves", "pieges", "victimes", "signal", "L", "R0", "LB", "ligne", "villages", "maisons", "d0", "deblai",
                 "exposes", "evacues", "gravite", "travail", "parent", "enfants", "delai_min", "attente_pas", "bloque_jusqu")

    def __init__(self, id, nature, cause, ile, lieu, pas_feu):
        self.id, self.nature, self.cause, self.ile, self.lieu, self.pas_feu = id, nature, cause, ile, lieu, pas_feu
        self.b = -1; self.surface = 0.0; self.f = 0.0; self.pas_appel = pas_feu; self.pas_arrivee = -1; self.pas_fin = -1
        self.etat = COUVE; self.besoin = 1; self.engins = []; self.eau = 0.0; self.maitrise_pas = 0; self.fin = ""
        self.dommage = 0; self.cout = 0.0; self.morts = self.blesses = self.sauves = 0
        self.pieges = []; self.victimes = []; self.signal = False
        self.L = self.R0 = 0.0; self.LB = 1.0; self.ligne = 0.0; self.villages = []; self.maisons = 0; self.d0 = 0.0
        self.deblai = 0; self.exposes = []; self.evacues = 0; self.gravite = 0; self.travail = 0
        self.parent = -1; self.enfants = []; self.delai_min = -1.0; self.attente_pas = 0; self.bloque_jusqu = -1


class SecuriteCivile:
    __slots__ = ("service", "casernes", "engins", "par_oid", "modeles", "actifs", "finis", "archives", "prochain",
                 "tic_pas", "actif", "scenario", "decideur", "ouvertes", "n_cle", "ffdi_moyen", "surface_nat", "voisins",
                 "ateliers", "eau", "stats", "heures_vol", "nes", "sortis", "occupants_avant", "seismes_vus", "crues_vus",
                 "idx_logements", "caserne_de_marche", "commandes", "brule_ha")

    def __init__(self):
        self.service = ServiceIncendie()
        self.casernes, self.engins, self.par_oid, self.modeles = [], [], {}, []
        self.actifs, self.finis, self.archives = {}, {}, []
        self.prochain = 0; self.tic_pas = -1; self.actif = True
        self.scenario = {"habitation": 1.0, "industriel": 1.0, "foret": 1.0}
        self.decideur = None; self.ouvertes = []; self.n_cle = 0
        self.ffdi_moyen, self.surface_nat, self.voisins, self.ateliers = {}, {}, {}, []
        self.eau = {"borne": 0.0, "milieu": 0.0, "verse": 0.0, "perdu": 0.0}
        self.stats = {k: 0 for k in ("departs", "sorties", "sauvetages", "morts", "blesses", "decisions", "detruits",
                                     "desincarcerations", "evacues", "engins_perdus")}
        self.heures_vol = {}
        self.nes = {n: {s: 0 for s in O.SOURCES} for n in NOMS_ENGINS}
        self.sortis = {n: {s: 0 for s in O.PUITS} for n in NOMS_ENGINS}
        self.occupants_avant = {}; self.seismes_vus = set(); self.crues_vus = set()
        self.idx_logements = (); self.caserne_de_marche = {}; self.commandes = 0
        self.brule_ha = {}          # ile -> hectares brules recemment ( le maquis repousse en ~ 5 ans )


def _dom(p): return p.domaines["securite_civile"]
def _membres_service(w): return (w.pays.domaines["securite_civile"].service,)


# ================================================================== lois pures ( testables seules )
def dommage_de(f):
    """L etat de dommage EMS-98 ( 1 a 5 ) d un batiment dont une part f a brule ; 0 s il n a pas brule."""
    if f <= 0.0: return 0
    return 1 + int(np.searchsorted(SEUILS_DOMMAGE, f, side="right"))


def vitesse_feu_kmh(ffdi, heure=14):
    return 0.0012 * max(0.0, ffdi) * W_T_HA * float(DIURNE[int(heure) % 24])


def rapport_ellipse(vent_ms):
    return min(6.0, 1.0 + 0.0012 * (3.6 * max(0.0, vent_ms)) ** 2.154)


def perimetre_km(L, LB): return math.pi / 2.0 * L * (1.0 + 1.0 / LB)


def hectares(L, LB): return math.pi / 4.0 * L * (L / LB) * 100.0


def tirer_departs_habitation(n_logements, jours, rng, facteur=1.0):
    """Le nombre de departs de feu de logement sur `jours` jours ( Poisson du taux annuel )."""
    return int(rng.poisson(n_logements * TAUX_HABITATION_AN * facteur * jours / JOURS_AN))


def lambda_foret(surface_nat_km2, ffdi, ffdi_moyen, facteur=1.0):
    """Les departs de feux de vegetation attendus un jour de FFDI `ffdi` sur une ile de `surface_nat_km2`."""
    return TAUX_FORET_100KM2_AN * surface_nat_km2 / 100.0 / JOURS_AN * np.maximum(0.0, ffdi) / max(1e-6, ffdi_moyen) * facteur


def ffdi_climatologique(profil, annees, rng):
    """Les FFDI journaliers d une ile, `annees` annees independantes tirees du generateur du territoire : autant de
    stations repliques qui vivent deux ans ensemble ( vectorise ), la premiere annee oubliee ( la secheresse du
    combustible, KBDI, part de zero ). Rend un tableau annees x 365."""
    tab = TER.TableClimat([profil] * annees); e = TER.EtatMeteo(annees)
    out = np.zeros((annees, int(JOURS_AN)))
    for d in range(2 * int(JOURS_AN)):
        m = TER.tirer_meteo(tab, e, d % int(JOURS_AN), rng)
        if d >= JOURS_AN: out[:, d - int(JOURS_AN)] = m.ffdi
    return out


# ================================================================== l eau
def _borne_m3_pas(p, lieu):
    if p.a("services_publics"):
        from . import d12_services_publics as SP
        return SP.borne_incendie(p, lieu)[0] * MIN_PAS / 60.0
    return 60.0 * MIN_PAS / 60.0 if p.w.carte.lieux[lieu].type in ("capitale", "ville") else 0.0


def _prelever(p, S, lieu, m3):
    """Tirer `m3` pour l extinction : a la borne des services publics, sinon au milieu ( territoire, domestique )."""
    if m3 <= EPS: return 0.0
    if p.a("services_publics"):
        from . import d12_services_publics as SP
        x = SP.prelever_incendie(p, lieu, m3); S.eau["borne"] += x
    else:
        x = TER.prelever(p, lieu, m3, "domestique"); S.eau["milieu"] += x
    return x


def bilan_eau(p):
    """Preleve - ( verse + citernes + perdu ), m3 : zero, sinon de l eau est nee ou morte hors des flux comptes."""
    S = _dom(p)
    cit = math.fsum(e.eau for e in S.engins if e.vivant)
    return (S.eau["borne"] + S.eau["milieu"]) - (S.eau["verse"] + cit + S.eau["perdu"])


# ================================================================== le delai d intervention
def delai_intervention_min(p, depuis, vers, modele=FPT, benevoles=False):
    """Minutes du depart de caserne a l arrivee : depart ( garde ou volontaires ) + route a la vitesse de l engin,
    ralentie par l etat des routes ( 12 ) ; route coupee ( 12, 15 ou moteur ) : detour et piste."""
    w = p.w; a = w.carte.lieux[depuis]; b = w.carte.lieux[vers]
    km = KM_URBAIN if a.id == b.id else max(KM_URBAIN, w.carte.km_route(a, b))
    v = VITESSE[modele]; f = 1.0
    coupe = a.id in w.routes_coupees or b.id in w.routes_coupees
    if a.id != b.id:
        if p.a("services_publics"):
            from . import d12_services_publics as SP
            f = SP.facteur_vitesse(p, a, b); coupe = coupe or not SP.route_ouverte(p, a, b)
        if p.a("logistique"):
            from . import d15_logistique as LG
            coupe = coupe or not LG.route_praticable(p, a, b)
    if coupe: km *= DETOUR_KM; v = VITESSE_PISTE; f = 1.0
    return (DEPART_BENEVOLES_MIN if benevoles else DEPART_GARDE_MIN) + km / (v * max(f, 0.05)) * 60.0


# ================================================================== les sinistres : naissance
def _nouveau(p, S, nature, cause, ile, lieu, pas_feu):
    s = Sinistre(S.prochain, nature, cause, ile, lieu, pas_feu); S.prochain += 1
    S.actifs[s.id] = s
    return s


def _presents_menage(p, k):
    """Les membres vivants d un menage qui sont chez eux ( colonnes, pas de vue )."""
    tb = p.w.table
    return [i for i in tb.menages.membres_ids(k)
            if tb.vivant[i] and tb.poste[i] == MAISON_P and tb.lieu[i] == tb.domicile[i]]


def _nuit(heure): return heure < 7.0 or heure >= 22.0


def _feu_batiment(p, S, b, nature, cause, rng, parent=-1):
    """Un batiment prend feu maintenant : ses presents, pieges ou non, l appel apres la detection."""
    w = p.w; d13 = IM._dom(p); T = d13.B
    if T["vivant"][b] != 1 or T["modele"][b] == d13.idx_modele["abri_urgence"]: return None
    lid = d13.lieux[int(T["lieu"][b])]
    for x in S.actifs.values():
        if x.b == b and x.etat != FINI: return None
    s = _nouveau(p, S, nature, cause, w.carte.lieux[lid].ile, lid, w.pas)
    s.b = int(b); s.surface = float(T["surface"][b]); s.f = F0; s.parent = parent
    nuit = _nuit(w.heure)
    s.pas_appel = w.pas + 1 + int(nuit and rng.random() < 0.5)
    presents = []
    if nature == "habitation":
        occ = int(T["occupant"][b])
        if occ >= 0: presents = _presents_menage(p, occ)
    else:
        prop = IM.proprietaire(p, b)
        role = getattr(prop, "role", None)
        if role in PO.CODE_ROLE:
            tb = w.table; ln = w.carte.lieux[lid].n
            presents = [i for i in w.ids_au_travail(w.carte.lieux[lid], role)
                        if tb.vivant[i] and tb.poste[i] == TRAVAIL_P and tb.lieu[i] == ln]
    pp = P_PIEGE[nature][1 if nuit else 0]
    for i in presents:
        u = rng.random()
        if u < pp:
            s.pieges.append([i, s.pas_appel + int(rng.integers(SURVIE_PAS[0], SURVIE_PAS[1] + 1))])
            s.victimes.append(i)
        elif u < pp + P_INTOX:
            _blesser(p, S, s, i, "brulure", int(rng.integers(2, 9)), lid)
    s.signal = (rng.random() < 0.9) if s.pieges else (rng.random() < 0.1)
    s.besoin = 3 if nature == "industriel" else 2
    if parent >= 0 and parent in S.actifs: S.actifs[parent].enfants.append(s.id)
    S.stats["departs"] += 1; p.compter("depart_de_feu")
    _assurer_tic(p, S)
    return s


def _feu_vegetation(p, S, lieu, cause, rng, d0=None):
    w = p.w; l = w.carte.lieux[lieu]
    s = _nouveau(p, S, "foret", cause, l.ile, lieu, w.pas)
    ffdi = TER.risque_incendie(p, l.ile)[0]; vent = TER.meteo(p, l.ile).vent_ms
    s.R0 = 0.0012 * ffdi * W_T_HA; s.LB = rapport_ellipse(vent)
    s.d0 = float(rng.uniform(0.5, 3.0)) if d0 is None else float(d0)
    s.L = 0.01
    s.pas_appel = w.pas + 1 + int(rng.random() < 0.5)
    for km, v in S.voisins.get(lieu, ()):
        dv = max(0.3, (s.d0 if v == lieu else km + s.d0 * (2.0 * rng.random() - 1.0)))
        s.villages.append([dv, v, rng.random() < (0.5 if v == lieu else P_SOUS_LE_VENT), False, False])
    s.besoin = 2
    S.stats["departs"] += 1; p.compter("depart_de_feu")
    _assurer_tic(p, S)
    return s


# ================================================================== les victimes
def _blesser(p, S, s, i, type_, iss, lieu):
    w = p.w; h = w.habitants[i]
    if not h.vivant: return
    M.blesser(p, h, type_, int(iss), cause="accident", lieu=lieu)
    if i not in s.victimes: s.victimes.append(i)
    s.blesses += 1; S.stats["blesses"] += 1; p.compter("blesse_incendie")
    if 4 <= iss < 9 and h.vivant: HP.admettre(p, h, None, lieu, None)


def _tuer(p, S, s, i):
    h = p.w.habitants[i]
    if not h.vivant: return
    POP.deceder(p, h, "accident")
    if i not in s.victimes: s.victimes.append(i)
    s.morts += 1; S.stats["morts"] += 1; p.compter("deces_incendie")


def _sauver(p, S, s, now, capacite, type_="brulure"):
    """Les pieges morts avant l arrivee meurent ; `capacite` d entre les autres sont sortis, blesses selon leur exposition."""
    reste = []
    for i, t in s.pieges:
        if t < now: _tuer(p, S, s, i)
        else: reste.append([i, t])
    s.pieges = reste
    n = min(capacite, len(reste))
    for i, t in reste[:n]:
        expo = (now - s.pas_feu) / max(1.0, t - s.pas_feu)
        _blesser(p, S, s, i, type_, int(min(50, max(9, 9 + 30 * expo))), s.lieu)
        s.sauves += 1; S.stats["sauvetages"] += 1; p.compter("sauvetage")
    s.pieges = reste[n:]


# ================================================================== les engins : depart, place, retour
def _libres(p, S, ile, now):
    """Les engins libres de l ile qu une caserne peut armer maintenant : ( engin, caserne ) dans l ordre des numeros."""
    out = []
    parc = p.socle.parc
    tb = p.w.table
    for c in S.casernes:
        if c.ile != ile: continue
        dispo = sum(1 for i in c.garde + c.benevoles if i not in c.occupes and tb.vivant[i] and tb.poste[i] != HOPITAL_P)
        for k in sorted(c.engins, key=lambda k: (S.engins[k].modele, k)):     # un equipage n arme qu un engin
            e = S.engins[k]
            if not e.vivant or e.mission >= 0 or e.libre > now or dispo < EQUIPAGE[e.modele]: continue
            o = parc.objets.get(e.oid)
            if o is None or o.etat != O.SERVICE: continue
            out.append(k); dispo -= EQUIPAGE[e.modele]
    return sorted(out)


def _armer(p, c, e, now):
    """L equipage : la garde d abord, puis les volontaires ; rend vrai si un volontaire a du venir."""
    tb = p.w.table
    pris, benevole = [], False
    for i in c.garde:
        if len(pris) >= EQUIPAGE[e.modele]: break
        if i not in c.occupes and tb.vivant[i] and tb.poste[i] != HOPITAL_P: pris.append(i)
    for i in c.benevoles:
        if len(pris) >= EQUIPAGE[e.modele]: break
        if i not in c.occupes and tb.vivant[i] and tb.poste[i] != HOPITAL_P: pris.append(i); benevole = True
    if len(pris) < EQUIPAGE[e.modele]: return None
    for i in pris: c.occupes.add(i)
    e.equipage = pris
    return benevole


def _envoyer(p, S, s, k, now):
    e = S.engins[k]; c = S.casernes[e.caserne]
    benevole = _armer(p, c, e, now)
    if benevole is None: return False
    vers = s.lieu
    dmin = delai_intervention_min(p, c.lieu, vers, e.modele, benevole)
    if s.nature == "foret": dmin += s.d0 / VITESSE_PISTE * 60.0
    arr = now + max(1, int(math.ceil(dmin / MIN_PAS - 1e-9)))
    e.mission, e.depart, e.arrivee = s.id, now, arr
    km = KM_URBAIN if c.lieu == vers else p.w.carte.km_route(p.w.carte.lieux[c.lieu], p.w.carte.lieux[vers])
    e.km += 2.0 * km + (2.0 * s.d0 if s.nature == "foret" else 0.0)
    s.engins.append(k)
    if s.delai_min < 0: s.delai_min = dmin
    S.stats["sorties"] += 1; p.compter("sortie_engin")
    return True


def _sur_place(S, s, now):
    return [k for k in s.engins if S.engins[k].vivant and S.engins[k].mission == s.id and S.engins[k].arrivee <= now
            and S.engins[k].plein_jusqu <= now]


def _rentrer(p, S, s, now):
    """Fin de mission : chaque engin rentre ( le temps de l aller ), son equipage le ramene."""
    for k in s.engins:
        e = S.engins[k]
        if not e.vivant or e.mission != s.id: continue
        aller = max(1, e.arrivee - e.depart)
        e.mission = -1; e.libre = now + (aller if e.arrivee <= now else max(1, now - e.depart))
        e.plein_jusqu = -1
        e.pompe_pas += max(0, now - max(e.arrivee, e.depart))


def _retours(p, S, now):
    """Les engins rentres a la caserne : equipage libere, plein d eau a la borne de la caserne, gazole, entretien,
    heures des volontaires."""
    parc = p.socle.parc
    for e in S.engins:
        if not e.vivant or e.mission >= 0 or not e.equipage or e.libre > now: continue
        c = S.casernes[e.caserne]
        h_mission = max(0, e.libre - e.depart) * MIN_PAS / 60.0
        for i in e.equipage:
            c.occupes.discard(i)
            if i in c.volontaires: S.heures_vol[i] = S.heures_vol.get(i, 0.0) + h_mission
        e.equipage = []
        manque = CITERNE[e.modele] - e.eau
        if manque > EPS: e.eau += _prelever(p, S, c.lieu, manque)
        marche = p.w.carte.lieux[c.lieu].marche.id
        litres = e.km * L100[e.modele] / 100.0 + e.pompe_pas * MIN_PAS / 60.0 * L_POMPE_H
        if litres > 0: S.service.carburant += TR.faire_le_plein(p, S.service, "carburant", litres, marche)
        if e.km > 0: S.service.entretien += TR.entretenir(p, S.service, "camion", e.km, marche)
        o = parc.objets.get(e.oid)
        if o is not None: parc.user(o, h_mission)
        e.km = 0.0; e.pompe_pas = 0


def _perdre_engin(p, S, s, k):
    e = S.engins[k]; c = S.casernes[e.caserne]
    o = p.socle.parc.objets.get(e.oid)
    if o is not None: p.socle.parc.sortir(o, "detruit")
    S.sortis[NOMS_ENGINS[e.modele]]["detruit"] += 1
    S.eau["perdu"] += e.eau; e.eau = 0.0
    e.vivant = False; e.mission = -1
    for i in e.equipage:
        c.occupes.discard(i)
        _blesser(p, S, s, i, "brulure", 16, s.lieu)
    e.equipage = []
    S.stats["engins_perdus"] += 1; p.compter("engin_perdu")
    _commander(p, S, e.modele, e.caserne)


def _commander(p, S, m, caserne):
    """Un engin de remplacement, importe ( prix au port, fret et droit par le domaine 7 ), arrive en trois mois."""
    sv = S.service; w = p.w
    prix = S.modeles[m].prix_monde * 1.1
    if sv.caisse < prix:
        manque = prix - sv.caisse
        ET.assurer(p, manque)
        sv.recu_etat += p.socle.livre.transferer(w.gouv, sv, manque, "dotation_securite_civile")
    paye = EXT.declarer_import(p, sv, S.modeles[m].prix_monde, "produit_fini", "import_vehicules")
    if paye <= 0.0: return False
    sv.imports += paye; S.commandes += 1
    p.poser(DELAI_IMPORT_J * PAS_J, "securite_civile_engin", m, (caserne,))
    return True


def _arrivee_engin(p, m, donnees):
    S = _dom(p); c = S.casernes[donnees[0]]
    o = p.socle.parc.creer(S.modeles[m], S.service, c.lieu, "importe", p.w.pas)
    S.nes[NOMS_ENGINS[m]]["importe"] += 1; S.commandes -= 1
    e = Engin(o.id, m, c.id, 0.0)
    e.eau = _prelever(p, S, c.lieu, CITERNE[m])
    S.engins.append(e); S.par_oid[o.id] = len(S.engins) - 1; c.engins.append(len(S.engins) - 1)


# ================================================================== le pas : evolution des sinistres
def _verser(p, S, s, besoin, now, sur):
    """Verse au plus `besoin` m3 : les citernes, puis la borne du lieu ( un fourgon pompe s y branche ). Rend le verse."""
    cap = sum(DEBIT_PAS[S.engins[k].modele] for k in sur)
    voulu = min(besoin, cap)
    verse = 0.0
    for k in sur:
        if verse >= voulu - EPS: break
        e = S.engins[k]
        x = min(e.eau, voulu - verse, DEBIT_PAS[e.modele])
        e.eau -= x; verse += x
    if verse < voulu - EPS and any(S.engins[k].modele == FPT for k in sur):
        b = _borne_m3_pas(p, s.lieu)
        if b > EPS: verse += _prelever(p, S, s.lieu, min(b, voulu - verse))
    s.eau += verse; S.eau["verse"] += verse
    if verse > 0: p.compter("eau_incendie", verse)
    return verse


def _pas_batiment(p, S, s, now, rng):
    sur = _sur_place(S, s, now)
    if s.pas_arrivee < 0 and sur: s.pas_arrivee = now
    _sauver(p, S, s, now, SAUVETAGES_PAR_ENGIN * len(sur))
    q = max(0.2, Q_M2_PAS * s.surface * s.f)
    verse = _verser(p, S, s, q, now, sur) if sur else 0.0
    for k in sur:
        e = S.engins[k]
        if e.eau <= EPS and CITERNE[e.modele] > 0 and _borne_m3_pas(p, s.lieu) <= EPS:
            c = S.casernes[e.caserne]
            e.plein_jusqu = now + 1 + int(math.ceil(2 * delai_intervention_min(p, s.lieu, c.lieu, e.modele) / MIN_PAS))
            e.eau += _prelever(p, S, c.lieu, CITERNE[e.modele])
    if verse >= q - EPS:
        s.etat = MAITRISE; s.maitrise_pas += 1
        if s.maitrise_pas >= PAS_EXTINCTION: _terminer(p, S, s, "attaque", now); return
    else:
        s.maitrise_pas = 0
        s.f = min(1.0, s.f + CROISSANCE[s.nature] * s.f * (1.0 - s.f) * (1.0 - verse / q))
        if s.f > 0.5:
            pr = P_PROPAGATION.get(p.w.carte.lieux[s.lieu].type, 0.0) * s.f
            if pr > 0 and rng.random() < pr: _propager(p, S, s, rng)
    if s.f >= F_CONSUME: s.f = 1.0; _terminer(p, S, s, "consume", now)


def _propager(p, S, s, rng):
    d13 = IM._dom(p); T = d13.B; n = T.n
    k = int(T["lieu"][s.b])
    cands = np.nonzero((T["vivant"][:n] == 1) & (T["lieu"][:n] == k) & (T["modele"][:n] != d13.idx_modele["abri_urgence"]))[0]
    brule = {x.b for x in S.actifs.values()}
    cands = [int(b) for b in cands.tolist() if int(b) not in brule]
    if not cands: return
    b = cands[int(rng.integers(0, len(cands)))]
    nom = IM.NOMS_MODELES[int(T["modele"][b])]
    nature = "habitation" if nom in LOGEMENTS_FEU else "industriel"
    _feu_batiment(p, S, b, nature, s.cause, rng, parent=s.id)


def _pas_foret(p, S, s, now, rng):
    w = p.w
    sur = _sur_place(S, s, now)
    if s.pas_arrivee < 0 and sur: s.pas_arrivee = now
    R = s.R0 * float(DIURNE[int(w.heure) % 24])
    ffdi_j = TER.risque_incendie(p, s.ile)[0]
    nat = S.surface_nat.get(s.ile, 100.0) * 100.0
    ha_max = max(1.0, min(PART_MAX_BRULEE * nat, nat - S.brule_ha.get(s.ile, 0.0)))
    if s.etat != MAITRISE:
        s.L += R * MIN_PAS / 60.0
        # la ligne d arret : chaque engin sur place qui a de l eau tient sa part de lisiere
        for k in sur:
            e = S.engins[k]
            x = LIGNE_KMH[e.modele] * MIN_PAS / 60.0
            if CITERNE[e.modele] > 0:
                eau = min(e.eau, x * EAU_PAR_KM_LIGNE)
                x = eau / EAU_PAR_KM_LIGNE; e.eau -= eau; s.eau += eau; S.eau["verse"] += eau
                if eau > 0: p.compter("eau_incendie", eau)
                if e.eau <= EPS:
                    e.plein_jusqu = now + 1 + int(math.ceil((2 * s.d0 / VITESSE_PISTE * 60 + 10) / MIN_PAS))
                    e.eau += _prelever(p, S, s.lieu, CITERNE[e.modele])
            s.ligne += x
            if ffdi_j >= 50.0 and rng.random() < P_ENGIN_PERDU_PAS: _perdre_engin(p, S, s, k)
        if s.ligne >= perimetre_km(s.L, s.LB) and sur:
            s.etat = MAITRISE; s.deblai = now + DEBLAI_PAS + int(hectares(s.L, s.LB) / 50.0)
        # les villages sous le vent
        for v in s.villages:
            dv, lid, sous_vent, evacue, touche = v
            if not sous_vent or touche: continue
            if not evacue and sur and s.L >= dv - EVACUATION_KM and s.pas_appel <= now:
                v[3] = True; S.stats["evacues"] += 1; p.compter("evacuation")
            if s.L >= dv:
                v[4] = True; _village_atteint(p, S, s, lid, v[3], len(sur) >= 2, rng)
        if hectares(s.L, s.LB) >= ha_max:
            s.L = math.sqrt(ha_max / 100.0 * 4.0 / math.pi * s.LB)
            _terminer(p, S, s, "combustible", now); return
    elif now >= s.deblai:
        _terminer(p, S, s, "attaque", now)


def _village_atteint(p, S, s, lid, evacue, defendu, rng):
    """Le front entre dans un village : une part des logements brule ( D4 ou D5 ) ; sans ordre d evacuation, ceux qui
    y sont peuvent y mourir."""
    d13 = IM._dom(p); T = d13.B; n = T.n
    k = d13.k_lieu.get(lid)
    if k is None: return
    log = np.array([d13.idx_modele[x] for x in ("maison", "appartement")])
    cands = np.nonzero((T["vivant"][:n] == 1) & (T["lieu"][:n] == k) & np.isin(T["modele"][:n], log))[0]
    if not len(cands): return
    nb = int(rng.binomial(len(cands), PART_WUI[1 if defendu else 0]))
    for b in sorted(rng.choice(cands, nb, replace=False).tolist()) if nb else ():
        occ = int(T["occupant"][b])
        presents = _presents_menage(p, occ) if occ >= 0 and not evacue else []
        dm = 4 + int(rng.random() < 0.5)
        s.cout += IM.endommager(p, b, dm, "incendie"); s.maisons += 1
        for i in presents:
            u = rng.random()
            if u < P_MORT_WUI: _tuer(p, S, s, i)
            elif u < P_MORT_WUI + P_BLESSE_WUI: _blesser(p, S, s, i, "brulure", int(rng.integers(9, 31)), lid)


def _pas_route(p, S, s, now, rng):
    sur = _sur_place(S, s, now)
    if s.pas_arrivee < 0 and sur: s.pas_arrivee = now
    if sur:
        s.travail += 1
        if s.travail >= PAS_DESINCARCERATION:
            S.stats["desincarcerations"] += 1; p.compter("desincarceration")
            _terminer(p, S, s, "secours", now)


def _pas_decombres(p, S, s, now, rng):
    sur = _sur_place(S, s, now)
    if s.pas_arrivee < 0 and sur: s.pas_arrivee = now
    s.travail += len(sur)
    cap = s.travail // PAS_PAR_SAUVETAGE_DECOMBRES
    if cap: s.travail -= cap * PAS_PAR_SAUVETAGE_DECOMBRES
    _sauver(p, S, s, now, cap, "ecrasement")
    if not s.pieges: _terminer(p, S, s, "secours", now)


def _pas_crue(p, S, s, now, rng):
    sur = _sur_place(S, s, now)
    if s.pas_arrivee < 0 and sur: s.pas_arrivee = now
    n = min(len(s.exposes), EVACUES_PAR_ENGIN_PAS * len(sur))
    if n:
        s.evacues += n; S.stats["evacues"] += n; p.compter("evacuation", n)
        s.exposes = s.exposes[n:]
    if now >= s.pas_feu + PIC_CRUE_PAS:
        for i in s.exposes:
            if rng.random() < P_MORT_CRUE * s.gravite: _tuer(p, S, s, i)
        s.exposes = []
    if not s.exposes: _terminer(p, S, s, "secours", now)


PAS_DE = {"habitation": _pas_batiment, "industriel": _pas_batiment, "foret": _pas_foret, "route": _pas_route,
          "decombres": _pas_decombres, "inondation": _pas_crue}


# ================================================================== la fin d un sinistre
def _terminer(p, S, s, fin, now):
    if s.etat == FINI: return
    if fin not in FINS: raise ValueError(f"fin inconnue {fin!r}")
    w = p.w
    s.etat = FINI; s.fin = fin; s.pas_fin = now
    if s.nature in ("habitation", "industriel"):
        _sauver(p, S, s, now, len(s.pieges) if fin == "attaque" else 0)
        for i, _ in s.pieges: _tuer(p, S, s, i)
        s.pieges = []
        s.dommage = dommage_de(s.f)
        if s.dommage: s.cout += IM.endommager(p, s.b, s.dommage, "incendie")
        kg = s.f * s.surface * CHARGE_KG_M2[s.nature] * PM25_KG_PAR_KG
        if kg > 0: TER.rejeter(p, s.lieu, "pm25", kg)
    elif s.nature == "foret":
        TER.rejeter(p, s.lieu, "pm25", hectares(s.L, s.LB) * W_T_HA * 1000.0 * 0.5 * PM25_KG_PAR_KG)
        S.brule_ha[s.ile] = S.brule_ha.get(s.ile, 0.0) + hectares(s.L, s.LB)
    elif s.nature == "decombres":
        for i, _ in s.pieges: _tuer(p, S, s, i)
        s.pieges = []
    _rentrer(p, S, s, now)
    del S.actifs[s.id]
    S.finis[s.id] = s
    ha = round(hectares(s.L, s.LB), 2) if s.nature == "foret" else 0.0
    S.archives.append((s.id, w.jour, s.nature, s.cause, s.lieu, s.b, s.dommage, round(s.cout, 2), s.morts, s.blesses,
                       ha, s.maisons, fin, round(s.delai_min, 1), s.pas_feu, s.pas_appel, s.pas_arrivee, now,
                       round(s.eau, 3)))
    if s.nature in ("habitation", "industriel"):
        p.noter("incendie", sinistre=s.id, nature=s.nature, lieu=s.lieu, fin=fin, dommage=s.dommage, morts=s.morts,
                blesses=s.blesses)
    elif s.nature == "foret":
        p.noter("feu_de_vegetation", sinistre=s.id, lieu=s.lieu, hectares=ha, fin=fin, maisons=s.maisons, morts=s.morts)
    elif s.nature == "decombres":
        p.noter("sauvetage_decombres", lieu=s.lieu, sauves=s.sauves, morts=s.morts)
    elif s.nature == "inondation":
        p.noter("crue_secours", lieu=s.lieu, evacues=s.evacues, morts=s.morts)


# ================================================================== le dispatch
def _traits(p, S, s, libres, n_eng, file, now):
    w = p.w
    km = min((w.carte.km_route(w.carte.lieux[S.casernes[S.engins[k].caserne].lieu], w.carte.lieux[s.lieu])
              for k in libres), default=30.0)
    ffdi, vent = TER.risque_incendie(p, s.ile)[0], TER.meteo(p, s.ile).vent_ms
    return [GRAVITE_ANNONCEE[s.nature], 1.0 if s.signal else 0.0, min(1.0, km / 30.0),
            min(1.0, len(libres) / max(1, n_eng)), min(1.0, file / 5.0), min(1.0, ffdi / 100.0), min(1.0, vent / 20.0),
            1.0 if _borne_m3_pas(p, s.lieu) > EPS else 0.0, 1.0 if _nuit(w.heure) else 0.0,
            min(1.0, (now - s.pas_appel) / 12.0)]


def _besoin(S, s):
    if s.nature == "foret":
        dpdt = math.pi / 2.0 * s.R0 * (1.0 + 1.0 / s.LB)
        return max(2, min(6, 1 + int(math.ceil(dpdt / LIGNE_KMH[CCF]))))
    return s.besoin


def _ordre(p, S, s, libres, action):
    """Les engins a envoyer, dans l ordre : nature preferee, km, numero. Renforts : pas la caserne la plus proche."""
    w = p.w
    pref = PREFERENCE[s.nature]
    def cle(k):
        e = S.engins[k]
        r = pref.index(e.modele) if e.modele in pref else 9
        km = w.carte.km_route(w.carte.lieux[S.casernes[e.caserne].lieu], w.carte.lieux[s.lieu])
        return (r, km, k)
    ok = sorted((k for k in libres if S.engins[k].modele in pref), key=cle)
    if action == RENFORTS and ok:
        proche = min(ok, key=lambda k: (w.carte.km_route(w.carte.lieux[S.casernes[S.engins[k].caserne].lieu],
                                                         w.carte.lieux[s.lieu]), k))
        ok = [k for k in ok if S.engins[k].caserne != S.engins[proche].caserne]
    return ok


def _dispatcher(p, S, now):
    if not S.actif: return
    dec = S.decideur
    for ile in sorted({s.ile for s in S.actifs.values()}):
        attente = [s for s in sorted(S.actifs.values(), key=lambda x: (x.pas_appel, x.id))
                   if s.ile == ile and s.etat != FINI and s.pas_appel <= now and s.bloque_jusqu <= now
                   and len([k for k in s.engins if S.engins[k].vivant and S.engins[k].mission == s.id]) < _besoin(S, s)]
        if not attente: continue
        for s in attente: s.attente_pas += 1
        libres = _libres(p, S, ile, now)
        n_eng = sum(1 for e in S.engins if e.vivant and S.casernes[e.caserne].ile == ile)
        for s in attente:
            if not libres: break
            engages = len([k for k in s.engins if S.engins[k].vivant and S.engins[k].mission == s.id])
            manque = _besoin(S, s) - engages
            demande = sum(max(0, _besoin(S, x) - len([k for k in x.engins if S.engins[k].vivant
                                                        and S.engins[k].mission == x.id])) for x in attente)
            if len(libres) < demande:
                autres = [x.id for x in attente if x is not s]
                ctx = ContexteDispatch(_traits(p, S, s, libres, n_eng, len(autres), now))
                cle = S.n_cle; S.n_cle += 1
                a = dec.decider(cle, ctx)
                groupe = [s.id] + autres
                S.ouvertes.append([cle, p.jour, groupe, 0, [perte(p, S, x) for x in groupe]])
                S.stats["decisions"] += 1; p.compter("decision_dispatch")
            else:
                a = COMPLET
            if a in (DIFFERER, REDUIT): s.bloque_jusqu = now + REVISION_PAS
            if a == DIFFERER: continue
            n = 1 if a == REDUIT else manque
            for k in _ordre(p, S, s, libres, a):
                if n <= 0: break
                if _envoyer(p, S, s, k, now): n -= 1
                libres.remove(k)
            if s.etat == COUVE: s.etat = APPEL


# ================================================================== le tic
def _assurer_tic(p, S):
    """Un seul tic par pas : `tic_pas` est le seau du tic en attente ( un depart servi avant le tic du meme pas en
    posait un second : les feux vivaient deux pas par pas, bogue du 26/09 )."""
    if S.tic_pas < p.w.pas:
        p.poser(0, "securite_civile_tic", 0); S.tic_pas = p.w.pas


def _tic(p, cle, donnees):
    S = _dom(p); now = p.w.pas
    rng = p.hasard("securite_civile_feu")
    _retours(p, S, now)
    for sid in sorted(S.actifs):
        s = S.actifs.get(sid)
        if s is None or s.etat == FINI: continue
        if s.etat == COUVE and s.pas_appel <= now: s.etat = APPEL
        PAS_DE[s.nature](p, S, s, now, rng)
    _dispatcher(p, S, now)
    if S.actifs or any(e.vivant and (e.mission >= 0 or e.equipage) for e in S.engins): _assurer_tic(p, S)


def _depart(p, cle, donnees):
    """Un depart de feu tire le matin tombe maintenant."""
    S = _dom(p); rng = p.hasard("securite_civile_feu")
    nature = NATURES[donnees[0]]
    if nature == "foret": _feu_vegetation(p, S, donnees[1], "accidentelle", rng)
    else: _feu_batiment(p, S, int(donnees[1]), nature, "accidentelle", rng)


# ================================================================== les routines du jour
def tirer_departs(p, S, rng):
    """Les departs de feu d un jour : [ ( heure, nature, cible ) ] ( un batiment ; un lieu habite pour la vegetation ).
    Logements : Poisson du taux annuel sur les logements vivants ; sites : le taux de leur activite ; vegetation : le
    taux par 100 km2 d espace naturel, au FFDI du jour rapporte a sa moyenne climatique."""
    w = p.w; d13 = IM._dom(p); T = d13.B; n = T.n
    out = []
    lam = TAUX_HABITATION_AN / JOURS_AN * S.scenario["habitation"]
    log = np.nonzero((T["vivant"][:n] == 1) & np.isin(T["modele"][:n], S.idx_logements))[0]
    k = int(rng.poisson(len(log) * lam))
    if k:
        for b in sorted(rng.choice(log, min(k, len(log)), replace=False).tolist()):
            out.append((float(rng.choice(24, p=HEURES_HABITATION / HEURES_HABITATION.sum()) + rng.random()),
                        "habitation", int(b)))
    if S.ateliers:
        u = rng.random(len(S.ateliers))
        for (b, typ), x in zip(S.ateliers, u.tolist()):
            if x < TAUX_INDUSTRIEL_AN.get(typ, 0.05) / JOURS_AN * S.scenario["industriel"] and T["vivant"][b] == 1:
                out.append((8.0 + 10.0 * rng.random(), "industriel", int(b)))
    for ile in sorted(S.surface_nat):
        ffdi = TER.risque_incendie(p, ile)[0]
        k = int(rng.poisson(lambda_foret(S.surface_nat[ile], ffdi, S.ffdi_moyen[ile], S.scenario["foret"])))
        cands = [l for l in sorted(S.voisins) if w.carte.lieux[l].ile == ile and w.carte.lieux[l].type in ("village", "ville")]
        for _ in range(k if cands else 0):
            out.append((float(rng.choice(24, p=HEURES_FORET / HEURES_FORET.sum()) + rng.random()), "foret",
                        cands[int(rng.integers(0, len(cands)))]))
    return out


def _departs(p):
    """0 h 20, apres la meteo : les departs de feu du jour, poses a leur heure ( echeances )."""
    S = _dom(p); w = p.w
    pas0 = w.pas - int(round(w.heure * 60)) // MIN_PAS      # le pas de minuit
    for heure, nature, cible in tirer_departs(p, S, p.du_jour("securite_civile_departs")):
        pas = pas0 + int(heure * 60) // MIN_PAS
        p.poser(max(0, pas - w.pas), "securite_civile_depart", 0, (NATURES.index(nature), cible))


def _garde(p):
    """6 h : la garde du jour ( un professionnel sur quatre ), les volontaires joignables, la dotation de l Etat."""
    S = _dom(p); w = p.w; tb = w.table
    rng = p.du_jour("securite_civile_garde")
    for c in S.casernes:
        c.garde = [i for j, i in enumerate(c.pros) if (j + w.jour) % ROTATION == 0 and tb.vivant[i]]
        u = rng.random(len(c.volontaires)) if c.volontaires else ()
        c.benevoles = [i for i, x in zip(c.volontaires, u) if x < P_VOLONTAIRE_DISPO and tb.vivant[i]]
    _doter(p, S)


def _cout_jour(p, S):
    return (len([i for c in S.casernes for i in c.pros]) * SOLDE_EUROS_MOIS / EUROS / 30.4
            + VACATION_EUROS_H / EUROS * 4.0 + 50.0 * len(S.engins))


def _doter(p, S):
    sv = S.service; w = p.w
    manque = COUSSIN_J * _cout_jour(p, S) - sv.caisse
    if manque <= EPS: return
    ET.assurer(p, manque)
    sv.recu_etat += p.socle.livre.transferer(w.gouv, sv, manque, "dotation_securite_civile")


def _paie(p):
    """23 h 30 : les soldes des professionnels et les vacations des volontaires, a leurs menages."""
    S = _dom(p); w = p.w; tb = w.table; L = p.socle.livre; sv = S.service
    solde = SOLDE_EUROS_MOIS / EUROS / 30.4
    for c in S.casernes:
        for i in c.pros:
            if not tb.vivant[i]: continue
            sv.soldes += L.transferer(sv, w.menages[int(tb.menage[i])], solde, "solde_pompier")
    for i in sorted(S.heures_vol):
        h = S.heures_vol[i]
        if tb.vivant[i] and h > 0:
            sv.vacations += L.transferer(sv, w.menages[int(tb.menage[i])], round(h * VACATION_EUROS_H / EUROS, 2),
                                         "vacation_pompier")
    S.heures_vol = {}


def _secours_routiers(p):
    """20 h 30, apres les accidents du jour ( domaine 14 ) : ceux qui ont des coinces appellent la desincarceration."""
    S = _dom(p); w = p.w
    rng = p.du_jour("securite_civile_route")
    for ev in TR.accidents_du_jour(p):
        if ev["victimes"] - ev["tues"] <= 0 or rng.random() >= P_INCARCERATION: continue
        lieu = ev["lieu"]
        if lieu not in w.carte.lieux: continue
        s = _nouveau(p, S, "route", "accidentelle", w.carte.lieux[lieu].ile, lieu, w.pas)
        s.pas_appel = w.pas; s.besoin = 1; s.signal = True
    if S.actifs: _assurer_tic(p, S)


def _avant_seisme(p):
    """0 h 10, avant les dommages du domaine 13 : qui dort ou dans les lieux secoues aujourd hui."""
    S = _dom(p)
    for c in TER.catastrophes_en_cours(p, type_="seisme"):
        if c.debut_j != p.jour or not c.intensites: continue
        k = (c.debut_j, c.ile, c.lieu, round(c.valeur, 3))
        if k in S.seismes_vus: continue
        S.seismes_vus.add(k)
        _photographier(p, S, {l: i for l, i in c.intensites.items() if i >= IM.I_DOMMAGE_MIN})


def _photographier(p, S, intensites):
    d13 = IM._dom(p); T = d13.B; n = T.n
    ks = [d13.k_lieu[l] for l in sorted(intensites) if l in d13.k_lieu]
    if not ks: return
    sel = np.nonzero((T["vivant"][:n] == 1) & np.isin(T["lieu"][:n], ks) & (T["occupant"][:n] >= 0))[0]
    for b in sel.tolist(): S.occupants_avant[b] = (int(T["occupant"][b]), int(T["dommage"][b]))


def _apres_seisme(p):
    """0 h 10, apres le domaine 13 : les batiments effondres ( D4, D5 ) retiennent une part de leurs occupants."""
    S = _dom(p)
    if not S.occupants_avant: return
    d13 = IM._dom(p); T = d13.B; w = p.w
    rng = p.hasard("securite_civile_seisme")
    par_lieu = {}
    for b in sorted(S.occupants_avant):
        occ, avant = S.occupants_avant[b]
        dm = int(T["dommage"][b])
        if dm < IM.DS_DETRUIT or avant >= IM.DS_DETRUIT: continue
        tb = w.table
        for i in tb.menages.membres_ids(occ):
            if not tb.vivant[i] or tb.lieu[i] != tb.domicile[i] or rng.random() >= P_PIEGE_EFFONDREMENT[dm]: continue
            lid = d13.lieux[int(T["lieu"][b])]
            par_lieu.setdefault(lid, []).append((i, rng.random() < P_MORT_IMMEDIATE[dm],
                                                 w.pas + int(rng.exponential(SURVIE_DECOMBRES_H) * 60 / MIN_PAS)))
    S.occupants_avant = {}
    for lid in sorted(par_lieu):
        s = _nouveau(p, S, "decombres", "naturelle", w.carte.lieux[lid].ile, lid, w.pas)
        s.pas_appel = w.pas; s.signal = True
        for i, mort, t in par_lieu[lid]:
            if mort: _tuer(p, S, s, i)
            else: s.pieges.append([i, t]); s.victimes.append(i)
        s.besoin = max(1, min(4, int(math.ceil(len(s.pieges) / 3))))
        if not s.pieges: _terminer(p, S, s, "secours", w.pas)
    if S.actifs: _assurer_tic(p, S)


def _crues(p):
    """0 h 30 : les crues du jour ( territoire ) exposent une part des residents de leur lieu ; les engins evacuent."""
    S = _dom(p); w = p.w
    for c in TER.catastrophes_en_cours(p, type_="inondation"):
        k = (c.debut_j, c.lieu)
        if c.debut_j != p.jour or k in S.crues_vus or c.lieu not in w.carte.lieux: continue
        S.crues_vus.add(k)
        inonder(p, c.lieu, c.gravite)


def _meteo_du_jour(p):
    """0 h 30 : la pluie ou un FFDI tres bas eteignent les feux de vegetation encore ouverts."""
    S = _dom(p)
    for sid in sorted(S.actifs):
        s = S.actifs.get(sid)
        if s is None or s.nature != "foret": continue
        m = TER.meteo(p, s.ile)
        if m.pluie_mm >= 2.0 or m.ffdi < 3.0: _terminer(p, S, s, "meteo", p.w.pas)


# ================================================================== la note, a la cloture
def perte(p, S, sid):
    """La perte d un sinistre, de 0 a 1 : valeur detruite, hectares, maisons, retard, et 0,5 par mort de ses victimes."""
    s = S.actifs.get(sid) or S.finis.get(sid)
    if s is None: return 0.0
    tb = p.w.table
    morts = sum(1 for i in s.victimes if not tb.vivant[i])
    if s.nature in ("habitation", "industriel"):
        x = IM.RATIO_DOMMAGE[dommage_de(s.f)] + sum(perte(p, S, c) for c in s.enfants)
    elif s.nature == "foret":
        x = 0.5 * min(1.0, hectares(s.L, s.LB) / 1000.0) + 0.3 * min(1.0, s.maisons / 10.0)
    elif s.nature == "route":
        x = 0.3 * min(1.0, s.attente_pas / 12.0)
    elif s.nature == "inondation":
        x = 0.5 * len(s.exposes) / max(1, len(s.exposes) + s.evacues)
    else:
        x = 0.0
    return min(1.0, x + 0.5 * morts)


def _cloture(p, comptes):
    S = _dom(p); dec = S.decideur
    reste = []
    for o in S.ouvertes:
        cle, j0, groupe, vus, base = o
        r = 1.0 - sum(max(0.0, perte(p, S, sid) - b) for sid, b in zip(groupe, base)) / len(groupe)
        dec.noter(cle, r, p.jour)
        o[3] = vus + 1
        if o[3] >= HORIZON_DISPATCH: dec.attentes.pop(cle, None)
        else: reste.append(o)
    S.ouvertes = reste
    for ile in S.brule_ha: S.brule_ha[ile] *= 1.0 - 1.0 / REPOUSSE_J
    garder = {sid for o in S.ouvertes for sid in o[2]}
    for sid in list(S.finis):
        s = S.finis[sid]
        if s.pas_fin < p.w.pas - 10 * PAS_J and sid not in garder and s.parent not in garder: del S.finis[sid]


# ================================================================== l installation
def _surface_ile(w, ile):
    if ile in SURFACE_ILE_KM2: return SURFACE_ILE_KM2[ile]
    pos = np.array([l.pos[:2] for l in w.carte.lieux.values() if l.ile == ile], float)
    if len(pos) < 2: return 20.0
    return max(20.0, float(np.ptp(pos[:, 0]) * np.ptp(pos[:, 1])) / 1e6 * 0.45)


def installer(p):
    w = p.w; L = p.socle.livre; parc = p.socle.parc
    S = SecuriteCivile()
    p.domaines["securite_civile"] = S
    for nom, prix, masse, vie, arma, cit, eq, deb, lig, v, l100, src in ENGINS:
        S.modeles.append(parc.declarer_modele(nom, "vehicule", round(prix / EUROS, 2), masse, vie, arma, None, src))
    L.declarer_motif("dotation_securite_civile", "transfert_courant", "securite_civile")
    for m in ("solde_pompier", "vacation_pompier"): L.declarer_motif(m, "remuneration", "securite_civile")
    J = p.socle.journal
    for t, champs in (("incendie", ("sinistre", "nature", "lieu", "fin", "dommage", "morts", "blesses")),
                      ("feu_de_vegetation", ("sinistre", "lieu", "hectares", "fin", "maisons", "morts")),
                      ("sauvetage_decombres", ("lieu", "sauves", "morts")),
                      ("crue_secours", ("lieu", "evacues", "morts"))):
        J.declarer(t, "securite_civile", "individuel", champs)
    for t in ("depart_de_feu", "sortie_engin", "sauvetage", "deces_incendie", "blesse_incendie", "desincarceration",
              "evacuation", "eau_incendie", "engin_perdu", "decision_dispatch"):
        J.declarer(t, "securite_civile", "compte")
    p.socle.registre.inscrire("service_incendie", "administrations", _membres_service, "caisse", None, "ServiceIncendie")
    d13 = IM._dom(p)
    S.idx_logements = np.array([d13.idx_modele[x] for x in LOGEMENTS_FEU], np.int16)
    for b in IM.batiments(p, "atelier"):
        prop = IM.proprietaire(p, b)
        if type(prop).__name__ == "Entreprise": S.ateliers.append((int(b), prop.type))
    # les zones : population par marche ( colonnes )
    tb = w.table; nh = tb.n
    mdl = IM._marche_par_n(p)
    dom = tb.domicile[:nh]
    viv = tb.vivant[:nh] != 0
    zone = np.where(viv & (dom >= 0), mdl[np.maximum(dom, 0)], -1)
    age = tb.age[:nh]
    publics = [PO.CODE_ROLE[r] for r in ("chef_gouvernement", "ministre", "officier", "soldat", "policier", "medecin",
                                           "infirmier", "enseignant", "enfant", "retraite") if r in PO.CODE_ROLE]
    aptes = viv & (age >= 20) & (age <= 55) & ~np.isin(tb.role[:nh], publics)
    pop_zone = np.bincount(zone[zone >= 0], minlength=len(w.carte.par_n))
    rng = p.hasard("securite_civile_installation")
    for cap in sorted(w.marches):
        l = w.carte.lieux[cap]; pz = int(pop_zone[l.n])
        b = IM._nouveau(p, d13, "bureau_public", w.gouv, cap, 600.0, IM.annee(p) - 25, "initial", 0)
        c = Caserne(len(S.casernes), cap, l.ile, b, pz)
        S.casernes.append(c); S.caserne_de_marche[cap] = c.id
        n = max(2, int(round(ENGINS_PAR_1000 * pz / 1000.0)))
        n_vsr = int(round(PART_VSR * n)); n_ccf = max(1, (n - n_vsr) // 2); n_fpt = max(1, n - n_vsr - n_ccf)
        for m, k in ((FPT, n_fpt), (CCF, n_ccf), (VSR, n_vsr)):
            for _ in range(k):
                o = parc.creer(S.modeles[m], S.service, cap, "initial", w.pas, float(rng.uniform(0.0, 0.5)))
                S.nes[NOMS_ENGINS[m]]["initial"] += 1
                e = Engin(o.id, m, c.id, 0.0)
                S.engins.append(e); S.par_oid[o.id] = len(S.engins) - 1; c.engins.append(len(S.engins) - 1)
        cands = np.nonzero(aptes & (zone == l.n))[0]
        n_p = min(len(cands), max(POMPIERS_MIN, int(round(POMPIERS_PAR_1000 * pz / 1000.0))))
        n_v = min(len(cands) - n_p, max(VOLONTAIRES_MIN, int(round(VOLONTAIRES_PAR_1000 * pz / 1000.0))))
        tir = rng.choice(cands, n_p + max(0, n_v), replace=False) if len(cands) else np.zeros(0, np.int64)
        c.pros = sorted(int(i) for i in tir[:n_p]); c.volontaires = sorted(int(i) for i in tir[n_p:])
    if pop_zone.sum() >= 5000 and not any(S.engins[k].modele == VSR for c in S.casernes for k in c.engins):
        c = max(S.casernes, key=lambda x: (x.pop, x.lieu))
        o = parc.creer(S.modeles[VSR], S.service, c.lieu, "initial", w.pas, 0.2)
        S.nes[NOMS_ENGINS[VSR]]["initial"] += 1
        S.engins.append(Engin(o.id, VSR, c.id, 0.0)); S.par_oid[o.id] = len(S.engins) - 1; c.engins.append(len(S.engins) - 1)
    # les voisinages des lieux habites ( pour les feux de vegetation ) et l espace naturel des iles
    hab = [l for l in sorted(w.carte.lieux.values(), key=lambda x: x.id) if l.type in ("capitale", "ville", "village")]
    for a in hab:
        S.voisins[a.id] = sorted((round(a.distance(b) / 1000.0, 3), b.id) for b in hab
                                 if b.ile == a.ile and a.distance(b) / 1000.0 <= VOISINAGE_KM)
    T = p.domaine("territoire")
    for i, ile in enumerate(T.iles):
        S.surface_nat[ile] = PART_NATURELLE * _surface_ile(w, ile)
        S.ffdi_moyen[ile] = float(ffdi_climatologique(T.profils[i], ANNEES_CLIMAT, p.hasard("securite_civile_climat")).mean())
    # le plein d eau de depart
    for e in S.engins: e.eau = _prelever(p, S, S.casernes[e.caserne].lieu, CITERNE[e.modele])
    S.decideur = p.decideur(POINT_DISPATCH)
    p.echeance("securite_civile_tic", _tic)
    p.echeance("securite_civile_depart", _depart)
    p.echeance("securite_civile_engin", _arrivee_engin)
    p.routine(10 / 60, 15, "securite_civile", _avant_seisme)
    p.routine(10 / 60, 25, "securite_civile", _apres_seisme)
    p.routine(20 / 60, 70, "securite_civile", _departs)
    p.routine(0.5, 70, "securite_civile", _crues)
    p.routine(0.5, 71, "securite_civile", _meteo_du_jour)
    p.routine(6.0, 70, "securite_civile", _garde)
    p.routine(20.5, 40, "securite_civile", _secours_routiers)
    p.routine(23.5, 70, "securite_civile", _paie)
    p.cloture("securite_civile", _cloture)
    _garde(p)
    return S


# ================================================================== controles ( pour les portes )
def audit_engins(p):
    """Comptes du Parc pour mes modeles = naissances et sorties faites par le domaine ; individus du Parc = ma table."""
    S = _dom(p); parc = p.socle.parc
    mes = {m.id: m.nom for m in S.modeles}
    vus = {o.id for o in parc.objets.values() if o.modele in mes}
    table = {e.oid for e in S.engins if e.vivant}
    ecarts = {}
    for mid, nom in mes.items():
        k = parc.comptes[mid]
        for s in O.SOURCES:
            if k[s] != S.nes[nom][s]: ecarts[(nom, s)] = k[s] - S.nes[nom][s]
        for s in O.PUITS:
            if k[s] != S.sortis[nom][s]: ecarts[(nom, s)] = k[s] - S.sortis[nom][s]
    ver = {nom: v for nom, v in parc.verifier().items() if nom in NOMS_ENGINS and v != 0}
    return {"orphelins": sorted(vus - table), "fantomes": sorted(table - vus), "sources": ecarts, "parc": ver}


def audit_propre(a): return not any(a.values())


def audit_sinistres(p):
    """Chaque sinistre fini a une cause declaree et verifiable : attaque = un engin est arrive et de l eau a ete versee
    ( un feu ) ou le travail est fait ( secours ) ; consume = part brulee 1 ; combustible = plafond atteint ; meteo = pluie
    ou FFDI bas ce jour-la. Rend la liste des manquements."""
    S = _dom(p); out = []
    for s in list(S.finis.values()):
        if s.fin not in FINS: out.append(("fin_inconnue", s.id)); continue
        if s.fin == "attaque":
            if s.pas_arrivee < 0 or not s.engins: out.append(("eteint_sans_engin", s.id))
            if s.nature in ("habitation", "industriel", "foret") and s.eau <= EPS: out.append(("eteint_sans_eau", s.id))
        elif s.fin == "consume" and s.f < 1.0 - 1e-6: out.append(("consume_non_brule", s.id))
        elif s.fin == "secours" and s.nature in ("route",) and s.pas_arrivee < 0: out.append(("secours_sans_engin", s.id))
    return out


def audit_degats(p):
    """Tout batiment endommage du domaine 13 a son sinistre enregistre au meme niveau ( par endommager ou un seisme ) ;
    tout batiment brule par ce domaine a son sinistre au domaine 13. Rend la liste des manquements ( le defaut connu du
    domaine 13 sur les commerces d un seisme porte son propre nom )."""
    S = _dom(p); d13 = IM._dom(p); T = d13.B; n = T.n
    vus = {}
    for j, b, dm, cout in d13.sinistres: vus[b] = max(vus.get(b, 0), dm)
    out = []
    com = d13.idx_modele["commerce"]
    for b in np.nonzero((T["dommage"][:n] > 0))[0].tolist():
        if vus.get(b, 0) < int(T["dommage"][b]):
            # defaut du domaine 13 ( 26/09 ) : un commerce tire de sa cohorte par un seisme recoit son dommage sans
            # sinistre enregistre ( appliquer_seisme ) ; compte a part, pour que le 13 le corrige
            tag = ("commerce_seisme_sans_sinistre" if T["modele"][b] == com and T["origine"][b] == 3
                   else "degat_hors_endommager")
            out.append((tag, b, int(T["dommage"][b])))
    for s in S.finis.values():
        if s.b >= 0 and s.dommage > 0 and vus.get(s.b, 0) < s.dommage: out.append(("feu_sans_sinistre", s.b, s.dommage))
    return out


# ================================================================== API pour les autres domaines
CHAMPS_ARCHIVE = ("sinistre", "jour", "nature", "cause", "lieu", "batiment", "dommage", "cout", "morts", "blesses",
                  "hectares", "maisons", "fin", "delai_min", "pas_feu", "pas_appel", "pas_arrivee", "pas_fin", "eau_m3")


def sinistres(p, depuis_j=0, nature=None, cause=None):
    """Domaines 20 ( assurance habitation et incendie ), 21 ( enquete ) : les sinistres termines depuis `depuis_j`,
    en dictionnaires ( CHAMPS_ARCHIVE ) ; le cout de reparation est celui du domaine 13."""
    return [dict(zip(CHAMPS_ARCHIVE, a)) for a in _dom(p).archives
            if a[1] >= depuis_j and (nature is None or a[2] == nature) and (cause is None or a[3] == cause)]


def en_cours(p):
    """Les sinistres ouverts : ( numero, nature, lieu, etat, part brulee ou hectares, engins ) ."""
    S = _dom(p)
    return [(s.id, s.nature, s.lieu, ("couve", "appel", "maitrise", "fini")[s.etat],
             round(hectares(s.L, s.LB), 2) if s.nature == "foret" else round(s.f, 3), list(s.engins))
            for s in sorted(S.actifs.values(), key=lambda x: x.id)]


def allumer(p, nature="habitation", b=None, lieu=None, cause="accidentelle", d0=None):
    """Domaines 21 ( incendie criminel : cause « criminelle » ), 25 a 27 ( feu de combat : cause « combat » ), scenarios
    et portes : un feu maintenant, dans le batiment `b` ( habitation, industriel ) ou pres du lieu ( foret ). Rend le
    numero du sinistre, ou -1."""
    S = _dom(p); rng = p.hasard("securite_civile_feu")
    if nature not in ("habitation", "industriel", "foret"): raise ValueError(f"nature inconnue {nature!r}")
    if cause not in CAUSES: raise ValueError(f"cause inconnue {cause!r}")
    s = _feu_vegetation(p, S, lieu, cause, rng, d0) if nature == "foret" else _feu_batiment(p, S, int(b), nature, cause, rng)
    return -1 if s is None else s.id


def seisme(p, intensites):
    """Scenario, domaines 25 a 27 : un seisme ( ou un bombardement ) maintenant : { lieu : intensite MMI } ; les degats
    du domaine 13, puis la recherche sous les decombres. Rend le resultat de `IM.appliquer_seisme`."""
    S = _dom(p)
    _photographier(p, S, intensites)
    out = IM.appliquer_seisme(p, intensites)
    _apres_seisme(p)
    return out


def inonder(p, lieu, gravite):
    """Une crue ( territoire, ou scenario ) : une part des residents du lieu est exposee ; les engins evacuent avant le
    pic. Rend le numero du sinistre, ou -1."""
    S = _dom(p); w = p.w; tb = w.table; nh = tb.n
    g = max(1, min(3, int(gravite)))
    rng = p.hasard("securite_civile_crue")
    ids = np.nonzero((tb.vivant[:nh] != 0) & (tb.domicile[:nh] == w.carte.lieux[lieu].n))[0]
    n = int(round(PART_INONDABLE[g] * len(ids)))
    if n <= 0: return -1
    s = _nouveau(p, S, "inondation", "naturelle", w.carte.lieux[lieu].ile, lieu, w.pas)
    s.pas_appel = w.pas; s.gravite = g; s.signal = True
    s.exposes = sorted(int(i) for i in rng.choice(ids, n, replace=False))
    s.victimes = list(s.exposes)
    s.besoin = max(1, min(3, int(math.ceil(n / (EVACUES_PAR_ENGIN_PAS * 6)))))
    _assurer_tic(p, S)
    return s.id


def scenario(p, **facteurs):
    """Multiplie les taux de departs de feu ( habitation, industriel, foret ) : scenarios et portes."""
    S = _dom(p)
    for k, v in facteurs.items():
        if k not in S.scenario or not 0.0 <= v < 1e6: raise ValueError(f"facteur invalide {k}={v!r}")
        S.scenario[k] = float(v)
    return dict(S.scenario)


def suspendre(p, oui=True):
    """Scenario ( greve, controle positif des portes, guerre ) : plus aucun engin ne part."""
    _dom(p).actif = not oui


def engins(p):
    """Le pont, les domaines 25 a 27 : ( numero, modele, caserne, mission, classname, preuve, decalage ( dx, dy ) m )."""
    S = _dom(p); out = []
    for c in S.casernes:
        pos = TR.emplacements(len(c.engins))
        for k, (dx, dy) in zip(c.engins, pos):
            e = S.engins[k]
            if not e.vivant: continue
            m = S.modeles[e.modele]
            out.append((e.oid, m.nom, c.lieu, e.mission, m.arma, m.arma_preuve, (dx, dy)))
    return out


def casernes(p):
    """( lieu, batiment du 13, engins vivants, professionnels, volontaires, de garde aujourd hui )."""
    S = _dom(p)
    return [(c.lieu, c.batiment, sum(1 for k in c.engins if S.engins[k].vivant), len(c.pros), len(c.volontaires),
             len(c.garde)) for c in S.casernes]


def pompiers(p):
    """Domaines 4, 25 : les identifiants des pompiers ( professionnels, volontaires ) : a ne pas mobiliser deux fois."""
    S = _dom(p)
    return sorted(i for c in S.casernes for i in c.pros), sorted(i for c in S.casernes for i in c.volontaires)
