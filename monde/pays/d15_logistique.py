"""DOMAINE 15 - LOGISTIQUE : ENTREPOTS, PORTS, FRET MARITIME ET AERIEN, CONVOIS ROUTIERS, COMMERCE ENTRE MARCHES ET ILES.

FICHE
1. Classes. Les detenteurs : Transporteur ( le transporteur routier d une capitale : caisse, sa flotte de camions et
   d utilitaires achetee au domaine 14, `acheter_flotte`, non geree par lui : chaque km est un vrai convoi ), Entrepot ( un
   Stock du socle et sa capacite en m3 et en tonnes : le quai d expedition de chaque marche, le hangar de transit de chaque
   port et de chaque aeroport ), AutoritePortuaire ( une par ile : caisse ; droits de port, manutention, magasinage,
   redevances d atterrissage ; le surplus va a l Etat ), Armateur ( une compagnie par ligne : caisse, subvention de
   service public ), Navire ( un individu du Parc, modele du domaine : Stock de la cale et des soutes ), CompagnieAerienne
   ( caisse ) et Avion ( individu du Parc : Stock de la soute et des reservoirs ). Les donnees : Terminal ( un port ou un
   aeroport : quais, rampes, grues, capacite de manutention en t/h, attente ), Ligne ( deux terminaux, un navire, les jours
   et les heures de depart, la distance ), Lot ( une cargaison qu un expediteur confie au fret : bien, quantite, masse,
   volume, mode, etapes, couts ), ContexteLot, Logistique ( l etat du domaine ). RemplaceExpedier, RemplaceLancerConvoi,
   RemplaceArrivees, RemplaceConducteur : les methodes du moteur reprises, en objets picklables.
   Physique des biens : masse et volume du catalogue du socle ; pour un bien du moteur que son domaine n a pas encore
   calibre ( nourriture, remedes ), une valeur d attente du domaine ( PHYSIQUE_DEFAUT, a calibrer ), jamais ecrite au
   catalogue.
2. Invariants et ce que le domaine detient. CONSERVATION : tout bien en transit est a un detenteur inscrit - dans un
   convoi du moteur ( famille convois ), dans un entrepot ( famille entrepots_logistique ), dans une cale ( navires ), dans
   une soute d avion ( avions ) ; il n y passe que par `livre.deplacer`, et les carburants n en sortent que par
   `livre.bruler` ( soutes, convois ). RAPPROCHEMENT DES LOTS ( `anomalies_transit` ) : pour chaque detenteur de transit et
   chaque bien, la quantite des lots qu il porte = son stock ( soutes a part ) ; chaque lot en route a son convoi, et ce
   convoi porte exactement le lot. ARGENT : tout par le grand livre, sous les motifs du domaine ; le domaine DETIENT les
   caisses des transporteurs, des autorites portuaires, des armateurs et des compagnies aeriennes. OBJETS : navires et
   avions ( modeles du domaine, source initial ) ; camions et utilitaires sont du domaine 14 ( achetes, jamais crees ici ).
   CHAUFFEURS : aucun convoi ne part avec un convoyeur qui n est pas a son poste ( a son lieu de travail, poste travail,
   a son heure ) : le week-end, avec l agenda, le convoyeur reste chez lui et ne conduit pas. CREDIT : un lot livre a un
   marche qui ne peut pas le payer devient une creance nommee du socle ( motif cession_lot ), reglee chaque soir sur la
   caisse du debiteur au-dela de RESERVE_REGLEMENT ; l acompte verse a la concession pour un camion commande lui est rendu
   sur le prix de vente.
3. Decision `expedier_lot` ( chaque marche, pour chacun des 4 biens des menages - nourriture, remedes, gazole, outils -
   dont il a un surplus au-dela de sa garde ( 1,5 jour de demande, + 1 la veille d un jour de repos ), a 8 h 40, 11 h 40,
   14 h 40 : jusqu a 12 decisions par marche et par jour ) : attendre, route vers le marche le plus cher de l ile, route
   vers le moins couvert de l ile, ferry vers le plus cher des autres iles, ferry vers le moins couvert, caboteur vers le
   moins couvert, avion vers le moins couvert. Des CRITERES, pas des indices ( lecon du domaine 6 ). Traits ( ce que le
   marchand voit : stocks et prix affiches des marches, horaires publies, ruptures publiees ) : couverture d origine, la
   plus basse de l ile, la plus basse des autres iles, prix d origine, prix le plus haut de l ile et des autres iles,
   ruptures d hier du marche le moins couvert, heures avant le prochain ferry et le prochain caboteur, surplus, bien
   essentiel. Note ( horizon 5 jours : 2 jours de transit au plus, 3 de vente ) : chaque soir, pour CE lot, la part du lot
   qui a servi une demande qui sans lui serait restee sans reponse la ou il est livre ( contrefactuel au pas pres :
   ventes du marche avec et sans ses unites ), MOINS la part qui a manque a son marche d origine ( les ventes que ses
   unites auraient faites si elles etaient restees ), plus, le jour de la livraison, la moitie de sa marge ( ecart de prix
   moins fret, sur la valeur du lot, bornee a +-1 ) ; attendre vaut zero. Ni le profit seul, ni la faim nationale : la
   penurie servie ou creee par CE lot. Le prix ne sert que la marge ( il dit la faim trop tard ). Regle : le marche le
   moins couvert ( ile d abord, puis les autres ) s il a moins de 2 jours et un jour de moins que l origine - par la
   route sur l ile, par le premier navire qui part ailleurs, par avion pour des remedes sous une demi-journee - sinon le
   plus cher si l ecart de prix d achat paie le fret, sinon attendre. Temoin : expedier sans condition, par ferry, vers
   l ile ou le bien est le plus cher ( le temoin aveugle qui a battu trois regles savantes ). Sans point de decision,
   par regle : les biens industriels ( fer, zinc, brut ) entre marches d une meme ile, en comparant enfin un prix d achat
   a un prix d achat ( la regle du moteur comparait le prix d achat d arrivee au prix de detail de depart : avec la
   marge de 25 % du domaine 3, un camion ne partait qu a ~40 % d ecart ).
4. Evenements. Individuels : escale ( navire, port, lots, tonnes, attente ), vol_cargo ( avion, de, vers, lots, kg ).
   Comptes : convoi_lance, convoi_refuse, lot_expedie, lot_livre, lot_annule, attente_quai_h, subvention_ligne,
   magasinage, soute_importee.
5. Liens. Remplace Monde.expedier, Monde.lancer_convoi, Monde.arrivees ( proprietaire, section 5 des conventions ) et
   Monde.conducteur ( le choix du chauffeur est une partie du lancement ). Garde ce que le moteur faisait : ventes des
   entreprises au marche ( l acheteur paie le transport ), approvisionnement en intrants, commandes publiques ( sur l ile
   de la destination ), agents « commerce » et marchand appris s ils sont poses, ravitaillement des bases ( lancer_convoi
   du moteur appelle celui-ci ). EXTERIEUR ( 7 ) : ses ventes au port des lignes 516 et 522 n existent plus dans cet
   expedier ; le negoce du domaine 7 ( `_port_horaire`, a chaque heure moins 10 ) exporte l or et le surplus de nourriture
   par le grand livre : ce domaine s y BRANCHE en decidant ses lots a H h 40, AVANT l export ( rang 50 contre 99 ), pour
   que le surplus d une ile nourrisse d abord une autre ile ; il achete ses soutes importees par `importer_au_port`
   ( douane, fret, droits ) ; le cabotage national n est pas dedouane ( marchandises de l Union ). TRANSPORT ( 14 ) :
   `acheter_flotte` ( gere=False : le domaine fait rouler ses camions ), `vehicules_de`, `faire_le_plein` ( gazole a la
   station du marche ), `entretenir` ( au km reel ), `caracteristiques` ( charge, consommation ), lit le stock et le prix
   de la station. SERVICES PUBLICS ( 12, si installes ) : `route_ouverte`, `facteur_vitesse` ( la duree d un convoi suit
   l etat des routes ; le pont du domaine 12 qui ralentissait les convois se coupe quand ce domaine est installe ) ; le
   trafic lourd des convois est deja lu par le domaine 12 dans Monde.convois. ENERGIE ( 11 ) : `vendre_produit` ( fioul des
   navires, kerosene des avions ). TRAVAIL ( 4, si installe ) : les dockers de chaque port ( `declarer_employeur`,
   `ouvrir_postes` : l autorite portuaire les paie ) ; les convoyeurs restent payes par le marche ( moteur et domaine 4 ).
   AGENDA ( 5, si installe ) : un convoyeur ne conduit que s il est a son poste. ECONOMIE ( 3 ) : demande lissee et
   ruptures ( non_servi ) des marches. IMMOBILIER ( 13 ) : la surface des commerces d un marche fait son quai
   d expedition ; ses cohortes de commerces. Paie et recoit : fret routier ( expediteur -> transporteur ; transporteur -> station, garage ), cession
   des lots ( marche d arrivee -> marche d origine, rendu : valeur + fret, ou creance ), fret maritime ( -> armateur ),
   manutention, droits de port, magasinage, redevances ( -> autorite portuaire ), affretement aerien ( -> compagnie ),
   soutes ( -> raffinerie, ou exterieur ), subvention de service public ( Etat -> armateur ), surplus des autorites
   ( -> Etat ), capital d ouverture ( investissement direct etranger, motif du domaine 7 ), acomptes sur camions
   ( transporteur <-> concession ), rapatriement de l avance des acomptes quand la flotte est complete ( -> exterieur ).
   API en fin de fichier ( domaines 17, 18, 26 ).
6. Portes : tests_d15_logistique.py.
7. Arma. Camions et utilitaires : classnames du domaine 14 ( C_Truck_02_transport_F, C_Van_01_transport_F ). Avion :
   CUP_C_AN2_CIV ( l An-2 de CUP, corps de substitution a verifier : ni Do 228 ni ATR au jeu ni a CUP a notre connaissance ).
   Navires : AUCUN corps ( ni ro-pax ni caboteur au jeu de base ni a CUP a notre connaissance : arma = None plutot qu un
   corps faux ; le quai reste vide dans Arma - a chercher dans les mods ). arma_preuve = None partout. `a_incarner` rend
   les vehicules en route avec leur DESTINATION posee avant l ordre de marche et un decalage de depart par vehicule
   ( `emplacements` du domaine 14 : deux vehicules crees au meme point se detruisent ).
8. Cout. Par heure pleine : une passe sur les entreprises du moteur ( comme Monde.expedier ), une sur les lots actifs ;
   par decision : les marches ( quelques-uns par ile ) ; a 19 h, une passe sur les marches et sur les decisions en
   attente ; les navires et les avions par echeances. Rien ne suit la population, sauf le choix du chauffeur ( l index du
   moteur des convoyeurs d une capitale ). Mesure du 24/09 ( test_cout, 10 005 habitants, Altis, flotte livree ) : le
   pays avec la logistique 1,88 s par jour contre 1,90 pour ses dependances seules ( -1 %, dans le bruit ) ; routines
   propres 39 ms par jour ( expedier 36 ), ~ 4 us par habitant, 87 convois par jour. Le cout suit les entreprises et les
   convois, pas les habitants : ~ quelques secondes par jour a 1 million d habitants si les entreprises du moteur y
   restent quelques centaines."""
import math, time
from collections import deque
import numpy as np
from .. import config as C, economie as E1, roles as RO
from ..socle import decision as D, biens as BI
from . import pays as PAYS, d03_economie as ECO, d06_etat as ET, d07_exterieur as EXT, d11_energie as ENE
from . import d14_transport as T14

EPS = 1e-9
DR = 1.0 / PAYS.EUROS_PAR_DRACHME            # un euro, en drachmes
PAS_H = 60 // C.MINUTES_PAR_PAS               # pas par heure
KMH_PAR_NOEUD = 1.852
JOURS_AN = 365.0

# ================================================================== la physique des biens
# Pour un bien du moteur que son domaine n a pas encore calibre, une valeur d attente du fret ( jamais ecrite au
# catalogue : le bien appartient a son domaine ) : kg et litres par unite.
PHYSIQUE_DEFAUT = {
    "nourriture": (1.8, 3.0, "ration d un jour : ~ 1,8 kg d aliments courants emballes ( FAO, bilans alimentaires, Grece "
                             ": ~ 1,9 kg par personne et par jour, fruits et laitages compris ) ; palettise ~ 600 kg/m3 ; a calibrer "
                             "par le domaine 9"),
    "remedes": (0.4, 1.0, "un traitement complet en boites ; a calibrer par le domaine 16"),
}
PHYSIQUE_INCONNU = (1.0, 2.0)

# ================================================================== la route
# Volume utile de la caisse ( m3 ; le domaine 14 donne la charge utile ) : porteur 12-18 t a caisse fermee ~ 40 m3,
# fourgon de 3,5 t ~ 12 m3, benne de pick-up ~ 2,5 m3 ( ordres de grandeur constructeurs, a calibrer ).
VOLUME_UTILE_M3 = {"camion": 40.0, "utilitaire": 12.0, "pick_up": 2.5}
FLOTTE_FRET = ("camion", "utilitaire")
CONVOYEURS_PAR_CAMION = 3             # un camion pour trois convoyeurs de la capitale ( a calibrer )
CONVOYEURS_PAR_UTILITAIRE = 6         # et un fourgon pour six ( au moins un )
FONDS_ROULEMENT = 3000.0              # drachmes en caisse au-dela du prix de la flotte visee
CHARGEMENT_H = 0.5                    # chargement et dechargement d un convoi ( transpalette : 15 a 20 min par cote )
RETOUR_A_VIDE = 0.8                   # litres du retour a vide rapportes a l aller charge ( a calibrer )
ENTRETIEN_KM_EUROS = {"camion": 0.12, "utilitaire": 0.06, "pick_up": 0.05}   # devis : pieces, pneus, main-d oeuvre
MARGE_TRANSPORT = 0.10                # marge du transporteur sur son cout direct ( a calibrer )
SEUIL_ENVOI_KG = 300.0                # une entreprise fait partir sa production a partir d une palette et demie
HEURE_COLLECTE = 10                   # ... ou a la collecte du jour, a partir de 10 h, des 20 kg
SEUIL_COLLECTE_KG = 20.0
APPRO_J = 2.0                         # un approvisionnement porte deux jours d intrants ( 16 heures de travail )

# ================================================================== les ports et les aeroports
# Ordres de grandeur d un port insulaire de l Egee ( a calibrer ) : deux postes a quai, une rampe ro-ro, deux grues
# mobiles ; une rampe roule 6 a 8 remorques de 15-20 t par heure ; une grue avec son equipe charge ~ 30 t/h de
# marchandises palettisees.
QUAIS_PORT = 2
RAMPES_PORT = 1
GRUES_PORT = 2
T_H_RAMPE = 120.0
T_H_GRUE = 30.0
T_H_AEROPORT = 4.0                    # chariots et tapis d une piste regionale ( a calibrer )
FENETRE_H = {"ferry": 2.0, "caboteur": 6.0}   # temps a quai avant le depart pour charger ( a calibrer )
DOCKERS_PAR_GRUE = 4                  # une equipe ( a calibrer ) ; domaine 4 s il est installe
# Entrepots : hangar de transit portuaire de 1 500 m2 ( 300 a l aeroport ), stocke sur 4 m a 60 % de remplissage,
# dalle de 3 t/m2 ( a calibrer ) ; quai d expedition d un marche : la surface de ses commerces ( domaine 13 ).
ENTREPOT_M2 = {"port": 1500.0, "aeroport": 300.0}
M2_COMMERCE = 60.0
HAUTEUR_STOCKAGE_M = 4.0
REMPLISSAGE = 0.6
CHARGE_SOL_T_M2 = 3.0
# Tarifs portuaires ( euros ; ordres de grandeur des reglements des autorites portuaires grecques, a calibrer ) :
DROITS_PORT_GT_EUROS = 0.10           # par unite de jauge brute et par escale
MANUTENTION_T_EUROS = {"ferry": 4.0, "caboteur": 8.0, "avion": 30.0}    # par tonne payante ( poids ou m3 ), a chaque bout
MAGASINAGE_M3_J_EUROS = 0.30          # par m3 et par jour au-dela de la franchise
FRANCHISE_MAGASINAGE_J = 1
REDEVANCE_ATTERRISSAGE_T_EUROS = 8.0  # par tonne de masse maximale au decollage
FONDS_AUTORITE = 5000.0               # au-dela, le surplus de l autorite est verse a l Etat
AEROPORTS = {"Altis": "airbase01"}    # une ile sans aeroport connu de la carte : sa capitale ( aerodrome a verifier )

# ================================================================== les navires ( modeles du domaine )
# nom : ( genre, prix euros, deplacement lege kg, jauge brute, longueur m, vitesse de service noeuds, fioul t/h en
#         service, port en lourd utile t, volume utile m3, source )
NAVIRES = {
    "roro_ligne_vitale": ("ferry", 14e6, 1.9e6, 2500, 78.0, 14.0, 0.55, 600.0, 3000.0,
                          "ro-pax insulaire de 70-80 m ( type des navires des lignes de service public de l Egee du Nord, "
                          "Lemnos - Agios Efstratios ) : 2 x 1 800 kW a 75 %, ~ 200 g/kWh ; ~ 300 m lineaires, 450 "
                          "passagers ; a calibrer"),
    "roro_egeen": ("ferry", 60e6, 9.0e6, 18500, 145.0, 24.0, 4.2, 2500.0, 12000.0,
                   "ro-pax type Blue Star Delos ( 2011 ) : 145 m, 18 500 GT, 4 x 7 680 kW a 80 %, ~ 180 g/kWh ; "
                   "~ 1 500 m lineaires, 2 400 passagers ; a calibrer"),
    "caboteur": ("caboteur", 4e6, 1.3e6, 2000, 88.0, 11.0, 0.25, 3000.0, 4000.0,
                 "caboteur de marchandises generales de 3 000 tpl : 1 500 kW a 80 %, ~ 205 g/kWh, 11 noeuds, "
                 "grues de bord ; a calibrer"),
}
VIE_NAVIRE_H = 30 * 5000.0            # 30 ans de 5 000 heures de marche
POP_GRAND_FERRY = 20000               # au-dela, la ligne prend un grand ro-pax de l Egee
FRET_T_EUROS = {"ferry": 25.0, "caboteur": 12.0}    # tonne payante ( poids ou m3 au choix du transporteur )
HEURES_LIGNE = {"ferry": (16.0, 7.0), "caboteur": (18.0, 8.0)}   # depart de l ile principale, depart du retour
ESCALE_MIN_H = 1.0
RESERVE_SOUTE = 2.5                   # le navire soute pour 2,5 traversees
RESERVE_REGLEMENT = 500.0            # un marche regle ses lots achetes a credit au-dela de cette caisse ( a calibrer )

# ================================================================== l avion cargo ( modele du domaine )
# Dornier 228-212, l avion des lignes insulaires grecques d Olympic des annees 1990 : 2 t de charge, 14,7 m3 de cabine,
# 400 km/h en croisiere, ~ 300 l/h de kerosene, 6,4 t au decollage ( constructeur ; a calibrer ).
AVION = ("dornier_228", "CUP_C_AN2_CIV", 7e6, 3700.0, 6400.0, 1900.0, 14.7, 400.0, 300.0)
VIE_AVION_H = 60000.0
BLOC_SUPPLEMENT_H = 0.4               # roulage, montee, approche
TARIF_BLOC_EUROS_H = 1400.0           # l heure bloc affretee ( ordre des tarifs ACMI d un bi-turbopropulseur, a calibrer )
HEURES_VOL = (7.5, 18.5)              # vols de jour ( aerodromes sans balisage de nuit )
KM_ENTRE_ILES = 120.0                 # la traversee du moteur ( carte.km_mer, a calibrer ) ; le vol la suit
CAPITAL_ARMATEUR_J = 20               # jours de soutes apportes a l ouverture
CAPITAL_COMPAGNIE = 20000.0

# ================================================================== la decision
BIENS_DECISION = ("nourriture", "remedes", "carburant", "outils")
BIENS_INDUSTRIELS = ("fer", "zinc", "petrole")
ESSENTIELS = ("nourriture", "remedes")
HEURES_DECISION = (8 + 40 / 60, 11 + 40 / 60, 14 + 40 / 60)
GARDE_J = 1.5
GARDE_VEILLE_J = 1.0
LOT_MAX_J = 2.0
LOT_MIN_U = 10.0
COUV_ALERTE_J = 2.0
HORIZON_LOT = 5
PREPARATION_MAX_H = 24
ACTIONS = ("attendre", "route_plus_chere", "route_moins_couverte", "ferry_plus_chere", "ferry_moins_couverte",
           "caboteur_moins_couverte", "avion_moins_couverte")
MODE_ACTION = (None, "route", "route", "ferry", "ferry", "caboteur", "avion")
POIDS_MARGE = 0.5

# etats d un lot
PREPARATION, ROUTE1, QUAI_A, EN_MER, QUAI_B, ROUTE2, LIVRE, ANNULE = range(8)
ETATS = ("preparation", "route1", "quai_depart", "en_mer", "quai_arrivee", "route2", "livre", "annule")
ACTIFS = (PREPARATION, ROUTE1, QUAI_A, EN_MER, QUAI_B, ROUTE2)

MOTIFS = {"fret_routier": "achat", "cession_lot": "achat", "fret_mer": "achat", "manutention": "achat",
          "droits_de_port": "achat", "magasinage": "achat", "affretement_aerien": "achat", "redevance_aeroport": "achat",
          "carburant_convoi": "achat", "subvention_ligne": "subvention", "surplus_autorite": "revenu_propriete",
          "commerce_industriel": "achat", "acompte_vehicule": "financier", "rapatriement_capital": "financier"}


# ================================================================== les classes
class Entrepot:
    """Un stock en transit et sa capacite. capacite_m3 : surface x hauteur de stockage x remplissage ; capacite_t :
    surface x charge au sol."""
    __slots__ = ("k", "lieu_id", "genre", "surface_m2", "capacite_m3", "capacite_t", "stock")

    def __init__(self, k, lieu_id, genre, surface_m2):
        if not 0.0 < surface_m2 < 1e7: raise ValueError(f"surface d entrepot hors bornes {surface_m2!r}")
        self.k, self.lieu_id, self.genre, self.surface_m2 = k, lieu_id, genre, float(surface_m2)
        self.capacite_m3 = self.surface_m2 * HAUTEUR_STOCKAGE_M * REMPLISSAGE
        self.capacite_t = self.surface_m2 * CHARGE_SOL_T_M2
        self.stock = BI.Stock()


class Transporteur:
    """Le transporteur routier d une capitale. vehicules : [ modele, pas ou il redevient libre ] par vehicule possede."""
    __slots__ = ("id", "marche_id", "lieu", "caisse", "vehicules", "cible", "km", "convois", "acomptes")

    def __init__(self, marche_id, lieu, cible):
        self.id, self.marche_id, self.lieu = f"transport@{marche_id}", marche_id, lieu
        self.caisse = 0.0
        self.vehicules = []
        self.cible = dict(cible)
        self.km = 0.0
        self.convois = 0
        self.acomptes = {}          # modele -> drachmes d acompte versees a la concession pour une commande


class AutoritePortuaire:
    __slots__ = ("id", "ile", "caisse", "recettes")

    def __init__(self, ile):
        self.id, self.ile, self.caisse, self.recettes = f"autorite@{ile}", ile, 0.0, 0.0


class Terminal:
    """Un port ou un aeroport. rampes, grues : le materiel ; facteur : ce qui reste de la capacite ( 1 ; une greve, une
    avarie, un scenario ) ; occupes : navires a quai."""
    __slots__ = ("k", "genre", "ile", "lieu", "autorite", "entrepot", "quais", "occupes", "rampes", "grues", "facteur",
                 "attente_h", "escales", "tonnes")

    def __init__(self, k, genre, ile, lieu, autorite, entrepot):
        self.k, self.genre, self.ile, self.lieu, self.autorite, self.entrepot = k, genre, ile, lieu, autorite, entrepot
        self.quais = QUAIS_PORT if genre == "port" else 1
        self.occupes = 0
        self.rampes, self.grues = (RAMPES_PORT, GRUES_PORT) if genre == "port" else (0, 0)
        self.facteur = 1.0
        self.attente_h = 0.0
        self.escales = 0
        self.tonnes = 0.0

    def t_h(self, mode):
        """Tonnes par heure que le terminal charge ou decharge pour ce mode."""
        if mode == "ferry": x = self.rampes * T_H_RAMPE
        elif mode == "caboteur": x = self.grues * T_H_GRUE
        else: x = T_H_AEROPORT
        return max(1e-6, x * self.facteur)


class Armateur:
    __slots__ = ("id", "caisse", "recettes_j", "couts_j", "subventions", "recettes")

    def __init__(self, nom):
        self.id, self.caisse = f"armateur@{nom}", 0.0
        self.recettes_j = self.couts_j = self.subventions = self.recettes = 0.0


class Navire:
    """Un navire : sa cale et ses soutes ( Stock ), son individu au Parc, sa ligne, le terminal ou il est a quai ( -1 en
    mer ), les lots a bord, un depart en attente ( terminal ) quand il arrive en retard."""
    __slots__ = ("k", "modele", "objet", "ligne", "terminal", "stock", "a_bord", "en_attente", "traversees")

    def __init__(self, k, modele, objet, terminal):
        self.k, self.modele, self.objet, self.terminal = k, modele, objet, terminal
        self.ligne = -1
        self.stock = BI.Stock()
        self.a_bord = []
        self.en_attente = -1
        self.traversees = 0


class Ligne:
    __slots__ = ("k", "genre", "a", "b", "navire", "jours", "heure_a", "heure_b", "km", "armateur")

    def __init__(self, k, genre, a, b, navire, jours, heure_a, heure_b, km, armateur):
        self.k, self.genre, self.a, self.b, self.navire = k, genre, a, b, navire
        self.jours, self.heure_a, self.heure_b, self.km, self.armateur = tuple(jours), heure_a, heure_b, km, armateur


class CompagnieAerienne:
    __slots__ = ("id", "caisse", "recettes", "vols")

    def __init__(self, nom): self.id, self.caisse, self.recettes, self.vols = f"compagnie@{nom}", 0.0, 0.0, 0


class Avion:
    __slots__ = ("k", "objet", "base", "terminal", "libre", "stock", "a_bord", "compagnie")

    def __init__(self, k, objet, base, compagnie):
        self.k, self.objet, self.base, self.terminal, self.libre = k, objet, base, base, 0
        self.stock = BI.Stock()
        self.a_bord = []
        self.compagnie = compagnie


class Lot:
    """Une cargaison confiee au fret. origine, dest : identifiants de lieux ; marche_o, marche_d : marches de depart et
    d arrivee ( un lot entre marches est cede a l arrivee ), ou None ; payeur : qui paie le fret ; recepteur : nom de la
    fonction qui recoit le lot a l arrivee ( « marche » ou une fonction d un autre domaine ). ou : l indice de son
    detenteur ( entrepot, navire, avion ) ; convoi : le numero de son convoi en route."""
    __slots__ = ("id", "cle", "bien", "q", "kg", "m3", "mode", "origine", "dest", "marche_o", "marche_d", "payeur",
                 "recepteur", "etat", "ou", "convoi", "pas_decision", "pas_dispo", "pas_livre", "valeur", "fret",
                 "jours_quai")

    def __init__(self, id, cle, bien, q, kg, m3, mode, origine, dest, marche_o, marche_d, payeur, recepteur, pas):
        self.id, self.cle, self.bien, self.q, self.kg, self.m3, self.mode = id, cle, bien, q, kg, m3, mode
        self.origine, self.dest, self.marche_o, self.marche_d = origine, dest, marche_o, marche_d
        self.payeur, self.recepteur = payeur, recepteur
        self.etat, self.ou, self.convoi = PREPARATION, -1, -1
        self.pas_decision, self.pas_dispo, self.pas_livre = pas, pas, -1
        self.valeur = self.fret = 0.0
        self.jours_quai = 0


class ContexteLot:
    __slots__ = ("traits", "cibles", "bien", "heures_ferry", "heures_cabo", "gain_route", "gain_mer", "autres")

    def __init__(self, traits, cibles, bien, heures_ferry, heures_cabo, gain_route, gain_mer, autres):
        self.traits, self.cibles, self.bien = traits, cibles, bien
        self.heures_ferry, self.heures_cabo, self.gain_route, self.gain_mer, self.autres = heures_ferry, heures_cabo, gain_route, gain_mer, autres


class Logistique:
    __slots__ = ("transporteurs", "par_capitale", "autorites", "terminaux", "port_de", "aeroport_de", "entrepots",
                 "quai_marche", "armateurs", "lignes", "navires", "compagnies", "avions", "lots", "prochain_lot",
                 "convois", "suivi", "decideur", "cle", "snap", "entrees", "sorties", "mesure", "mer_ouverte", "stats",
                 "transits", "lancements", "chrono", "modeles", "collecte_j", "recepteurs", "jour_install", "dettes")

    def __init__(self):
        self.transporteurs, self.par_capitale = [], {}
        self.autorites = {}
        self.terminaux, self.port_de, self.aeroport_de = [], {}, {}
        self.entrepots, self.quai_marche = [], {}
        self.armateurs, self.lignes, self.navires = [], [], []
        self.compagnies, self.avions = [], []
        self.lots = {}                   # id -> Lot actif ( les livres et annules sortent )
        self.prochain_lot = 0
        self.convois = {}                # numero de convoi -> ( transporteur, vehicule, lot ou -1 )
        self.suivi = {}                  # cle de decision -> [ lot, action, r_origine, r_arrivee, q, origine, arrivee, bien, marge ]
        self.decideur = None
        self.cle = 0
        self.snap, self.entrees, self.sorties = {}, {}, {}   # marche -> { bien : quantite } ( la mesure de 19 h )
        self.mesure = {}                 # ( marche, bien ) -> ( A, S, U, D ) du jour
        self.mer_ouverte = True
        self.stats = {k: 0.0 for k in ("convois", "refus_chauffeur", "refus_vehicule", "refus_carburant", "refus_caisse",
                                       "refus_route", "refus_mer", "km", "litres", "lots", "lots_livres", "lots_annules",
                                       "tonnes_mer", "tonnes_air", "tonnes_route", "traversees", "vols", "soutes_importees",
                                       "subventions", "depuis_chez_lui", "convois_week_end", "retard_port_h",
                                       "attente_rade_h", "entrepot_plein")}
        self.transits = {m: deque(maxlen=2000) for m in ("route", "ferry", "caboteur", "avion")}   # heures de transit
        self.lancements = deque(maxlen=5000)   # ( jour, pas, chauffeur, poste, a son lieu de travail )
        self.chrono = {}
        self.modeles = {}                # nom -> identifiant du Modele au Parc
        self.collecte_j = {}             # entreprise -> jour de sa derniere collecte
        self.recepteurs = {"marche": _recevoir_marche}
        self.jour_install = 0
        self.dettes = []                 # creances nees de lots livres a un marche qui ne pouvait pas payer


def _lg(p): return p.domaine("logistique")


def _chrono(lg, nom, t0): lg.chrono[nom] = lg.chrono.get(nom, 0.0) + time.perf_counter() - t0


def _sp(p):
    if not p.a("services_publics"): return None
    import importlib
    return importlib.import_module(".d12_services_publics", __package__)


# ================================================================== la physique
def masse_kg(p, bien):
    b = p.socle.catalogue[bien]
    return b.masse_kg if b.masse_kg is not None else PHYSIQUE_DEFAUT.get(b.nom, PHYSIQUE_INCONNU)[0]


def volume_l(p, bien):
    b = p.socle.catalogue[bien]
    return b.volume_l if b.volume_l is not None else PHYSIQUE_DEFAUT.get(b.nom, PHYSIQUE_INCONNU)[1]


def charge(p, cargaison):
    """( kg, m3 ) d une cargaison { bien : quantite }."""
    kg = m3 = 0.0
    for b, q in cargaison.items():
        kg += q * masse_kg(p, b); m3 += q * volume_l(p, b) / 1000.0
    return kg, m3


def tonnes_payantes(kg, m3):
    """La tonne payante du fret maritime : le poids ou le volume ( 1 t = 1 m3 ), au choix du transporteur."""
    return max(kg / 1000.0, m3)


# ================================================================== la route : chauffeurs et vehicules
def au_poste(h):
    """Vrai si le convoyeur est a son poste : a son lieu de travail, poste travail. Avec l agenda, un convoyeur au repos
    ( samedi, dimanche, ferie ) est chez lui : il ne conduit pas."""
    return h.poste == "travail" and h.travail is not None and h.lieu is h.travail


def conducteur(p, capitale):
    """Un convoyeur de cette capitale libre, a son heure et A SON POSTE. Le moteur prenait le premier dont l horaire
    ouvrait l heure, meme reste chez lui le dimanche."""
    w = p.w; heure = w.heure; pas = w.pas; libre = w.conducteur_libre
    for h in w.au_travail_de(capitale, "convoyeur"):
        if h.vivant and libre.get(h.id, 0) <= pas and h.au_travail(heure) and au_poste(h) and h.id not in w.sejours:
            return h
    return None


class RemplaceConducteur:
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self, capitale): return conducteur(self.pays, capitale)


def _vehicule(p, tr, kg, m3):
    """Le plus petit vehicule libre du transporteur qui porte la cargaison, ou None."""
    pas = p.w.pas; best = None
    for k, (nom, libre) in enumerate(tr.vehicules):
        if libre > pas: continue
        c = T14.caracteristiques(nom)
        if c.charge_kg + EPS < kg or VOLUME_UTILE_M3.get(nom, 0.0) + EPS < m3: continue
        if best is None or c.charge_kg < T14.caracteristiques(tr.vehicules[best][0]).charge_kg: best = k
    return best


def capacite_libre(p, tr):
    """( kg, m3 ) du plus grand vehicule libre du transporteur."""
    pas = p.w.pas; kg = m3 = 0.0
    for nom, libre in tr.vehicules:
        if libre > pas: continue
        c = T14.caracteristiques(nom)
        if c.charge_kg > kg: kg, m3 = c.charge_kg, VOLUME_UTILE_M3.get(nom, 0.0)
    return kg, m3


def duree_convoi_pas(p, origine, destination, km=None):
    """( aller, retour ) en pas : la route a la vitesse moyenne des convois, ralentie par l etat des troncons ( domaine
    12 ), plus le chargement et le dechargement a l aller."""
    w = p.w
    if km is None: km = w.carte.km_route(origine, destination)
    SP = _sp(p)
    f = SP.facteur_vitesse(p, origine, destination) if SP is not None else 1.0
    h = km / C.VITESSE_CONVOI_KMH / max(f, 0.05)
    aller = max(1, math.ceil((h + CHARGEMENT_H) * PAS_H - 1e-9))
    retour = max(1, math.ceil(h * PAS_H - 1e-9))
    return aller, retour


def route_praticable(p, origine, destination):
    w = p.w
    if origine.ile != destination.ile: return False
    coupees = w.routes_coupees | getattr(w, "routes_temporaires", set())
    if origine.id in coupees or destination.id in coupees: return False
    SP = _sp(p)
    return SP is None or bool(SP.route_ouverte(p, origine, destination))


def _station(p, mid):
    t = T14._tr(p)
    return t.par_marche[mid][1], t.bid["carburant"]


def _plan_carburant(p, marche, litres):
    """( litres a la station, unites au marche, cout TTC ) pour faire `litres` : la station du marche d abord ( domaine
    14 ), le stock du marche pour le reste, comme le moteur. None si les deux ensemble ne suffisent pas."""
    mid = marche.lieu.id
    st, b = _station(p, mid)
    dispo = st.stock[b] * T14.LITRES_UNITE
    l_st = min(litres, max(0.0, dispo - 1e-6))
    reste = (litres - l_st) / T14.LITRES_UNITE
    if reste > marche.stocks.get("carburant", 0.0) + EPS: return None
    prix_l = T14.prix_station(p, st, "carburant") / T14.LITRES_UNITE * (1.0 + ET.taux_tva(p, "carburant"))
    return l_st, max(0.0, reste), l_st * prix_l + max(0.0, reste) * marche.prix["carburant"]


def _lancer(p, origine, destination, cargaison, payeur, motif, marche, vendeur=None, kg=None, m3=None, lot=-1):
    """Un convoi routier : chauffeur a son poste, vehicule du transporteur de la capitale qui porte la charge, route
    ouverte, gazole achete a la station ( ou au marche ), prix du fret paye par `payeur` au transporteur. Rend
    ( convoi, prix ) ou None. Le convoi entre dans Monde.convois : les autres domaines ( 4, 6, 12 ) le lisent la."""
    w = p.w; lg = _lg(p); st = lg.stats; L = p.socle.livre
    if origine.ile != destination.ile: st["refus_mer"] += 1; return None
    if not route_praticable(p, origine, destination): st["refus_route"] += 1; return None
    tr = lg.par_capitale.get(marche.lieu.id)
    if tr is None: st["refus_vehicule"] += 1; return None
    if kg is None: kg, m3 = charge(p, cargaison)
    v = _vehicule(p, tr, kg, m3)
    if v is None: st["refus_vehicule"] += 1; p.compter("convoi_refuse"); return None
    ch = conducteur(p, marche.lieu)
    if ch is None: st["refus_chauffeur"] += 1; p.compter("convoi_refuse"); return None
    km = w.carte.km_route(origine, destination)
    nom = tr.vehicules[v][0]; c = T14.caracteristiques(nom)
    litres = km * c.l100 / 100.0 * (1.0 + RETOUR_A_VIDE)
    plan = _plan_carburant(p, marche, litres)
    if plan is None: st["refus_carburant"] += 1; p.compter("convoi_refuse"); return None
    l_st, u_m, cout = plan
    prix = (cout + 2.0 * km * ENTRETIEN_KM_EUROS.get(nom, 0.1) * DR) * (1.0 + MARGE_TRANSPORT)
    if payeur.caisse < prix: st["refus_caisse"] += 1; p.compter("convoi_refuse"); return None
    L.transferer(payeur, tr, prix, "fret_routier")
    if l_st > EPS: T14.faire_le_plein(p, tr, "carburant", l_st, marche.lieu.id)
    if u_m > EPS:
        paye = L.transferer(tr, marche, u_m * marche.prix["carburant"], "carburant_convoi")
        u = L.bruler(EXT.StockE1(marche.stocks, p.socle.catalogue), p.socle.catalogue.id("carburant"),
                     paye / max(EPS, marche.prix["carburant"]), "carburant_convoi")
        marche.demande["carburant"] += u
    T14.entretenir(p, tr, nom, 2.0 * km, marche.lieu.id)
    coh = p.socle.parc.cohortes.get((T14._tr(p).mids[T14.IDX[nom]], tr, tr.lieu.id))
    if coh is not None and coh.nombre > 0:          # l usure au km reel : la flotte n est pas geree par le domaine 14
        coh.usure = min(1.0, coh.usure + 2.0 * km / c.vie_km / coh.nombre)
    aller, retour = duree_convoi_pas(p, origine, destination, km)
    w.n_convoi += 1
    cv = E1.Convoi(w.n_convoi, origine, destination, cargaison, w.pas, w.pas + aller, payeur, motif, ch.id)
    cv.vendeur = vendeur if vendeur is not None else payeur
    w.convois.append(cv)
    w.conducteur_libre[ch.id] = w.pas + aller + retour
    ch.heures_jour += (aller + retour) * C.MINUTES_PAR_PAS / 60.0
    tr.vehicules[v][1] = w.pas + aller + retour
    tr.km += 2.0 * km; tr.convois += 1
    lg.convois[cv.id] = (lg.transporteurs.index(tr), v, lot)
    st["convois"] += 1; st["km"] += 2.0 * km; st["litres"] += litres; st["tonnes_route"] += kg / 1000.0
    repos = not p.socle.calendrier.ouvre(p.socle.calendrier.date(w.pas))
    if repos: st["convois_week_end"] += 1
    if not au_poste(ch): st["depuis_chez_lui"] += 1
    lg.lancements.append((p.jour, w.pas, ch.id, ch.poste, au_poste(ch), repos))
    p.compter("convoi_lance")
    return cv, prix


class RemplaceLancerConvoi:
    """Prend la place de Monde.lancer_convoi ( meme contrat : vrai si le convoi part ) : les bases du moteur, les agents
    et le marchand appris y passent."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self, origine, destination, cargaison, payeur, motif, marche_carburant, vendeur=None):
        return _lancer(self.pays, origine, destination, cargaison, payeur, motif, marche_carburant, vendeur) is not None


# ================================================================== expedier : l heure pleine du moteur
def _tronquer(p, tr, cargo):
    """La cargaison ramenee a ce que porte le plus grand vehicule libre ( au prorata de chaque bien )."""
    kg, m3 = charge(p, cargo)
    ck, cm = capacite_libre(p, tr)
    if ck <= EPS: return {}
    f = min(1.0, ck / max(EPS, kg), cm / max(EPS, m3) if m3 > EPS else 1.0)
    return {b: q * f * (1.0 - 1e-9) for b, q in cargo.items()} if f < 1.0 else cargo


def _compter(d, mid, b, q):
    x = d.setdefault(mid, {})
    x[b] = x.get(b, 0.0) + q


def _expedier(p, h):
    w = p.w; lg = _lg(p); t0 = time.perf_counter()
    _avancer_lots(p, lg)
    for e in w.entreprises.values():
        m = w.marches[e.lieu.marche.id]
        tr = lg.par_capitale.get(m.lieu.id)
        if tr is None: continue
        # vendre la production : une cargaison par entreprise, a partir d une palette et demie ou a la collecte du jour
        cargo = {b: e.stocks[b] for b in e.produits if b != "electricite" and e.stocks[b] > EPS}
        if cargo:
            kg, m3 = charge(p, cargo)
            collecte = h >= HEURE_COLLECTE and lg.collecte_j.get(e.id, -1) < p.jour and kg >= SEUIL_COLLECTE_KG
            if kg >= SEUIL_ENVOI_KG or collecte or cargo.get("or", 0.0) >= 0.5:
                cargo = _tronquer(p, tr, cargo)
                if cargo and _lancer(p, e.lieu, m.lieu, cargo, m, "vente", m, vendeur=e) is not None:
                    for b, q in cargo.items(): e.stocks[b] -= q
                    lg.collecte_j[e.id] = p.jour
        # s approvisionner ( la regle du moteur, en quantites qu un vehicule porte )
        for b, need in e.intrants.items():
            if b == "electricite": continue
            if e.stocks[b] < need * 8 and m.stocks[b] > 1:
                ck, cm = capacite_libre(p, tr)
                q = min(m.stocks[b], need * 8 * APPRO_J, ck / max(EPS, masse_kg(p, b)),
                        cm * 1000.0 / max(EPS, volume_l(p, b)) if volume_l(p, b) > 0 else math.inf)
                if q <= EPS: m.demande[b] += need * 8; continue
                cout = q * m.prix[b] * (1 + w.gouv.tva)
                if e.caisse >= cout:
                    m.demande[b] += q
                    if _lancer(p, m.lieu, e.lieu, {b: q}, e, "approvisionnement", m) is not None:
                        m.stocks[b] -= q; _compter(lg.sorties, m.lieu.id, b, q)
                        w.transferer(e, m, q * m.prix[b], "achat intrant")
                        w.transferer(e, w.gouv, q * m.prix[b] * w.gouv.tva, "tva")
                else: m.demande[b] += q
    # le commerce entre marches : le marchand appris ou les agents s ils sont poses ; sinon les biens industriels par
    # regle ( les biens des menages passent par le point de decision, a H h 40 )
    if 7 <= h < 15:
        gc = w.agents.get("commerce")
        if w.marchand is not None: w.marchand(w, h)
        elif gc: RO.commerce_agents(w, gc, h)
        else: _commerce_industriel(p, lg)
    _commandes_publiques(p, lg)
    _chrono(lg, "expedier", t0)


def _commerce_industriel(p, lg):
    """Fer, zinc, brut : vers le marche de la meme ile ou le prix d ACHAT paie le fret. La regle du moteur comparait le
    prix d achat d arrivee au prix de DETAIL de depart."""
    w = p.w
    for a in w.marches.values():
        tr = lg.par_capitale.get(a.lieu.id)
        if tr is None: continue
        for b in BIENS_INDUSTRIELS:
            surplus = a.stocks[b] - w.reserve_marche(a, b)
            if surplus < LOT_MIN_U: continue
            autres = [x for x in w.marches.values() if x is not a and x.lieu.ile == a.lieu.ile]
            if not autres: continue
            cible = max(autres, key=lambda x: (x.prix[b] * (1 - x.marge), x.lieu.id))
            ck, cm = capacite_libre(p, tr)
            q = min(surplus, ck / max(EPS, masse_kg(p, b)))
            if q < LOT_MIN_U: continue
            km = w.carte.km_route(a.lieu, cible.lieu)
            cout_u = 2 * km * 0.3 * a.prix["carburant"] / T14.LITRES_UNITE / q     # ~ 30 l aux 100 km
            if cible.prix[b] * (1 - cible.marge) - a.prix[b] * (1 - a.marge) > cout_u + 0.05 * a.prix[b]:
                if _lancer(p, a.lieu, cible.lieu, {b: q}, a, "commerce", a) is not None:
                    a.stocks[b] -= q; _compter(lg.sorties, a.lieu.id, b, q)


def _commandes_publiques(p, lg):
    """La regle du moteur, sur l ile de la destination ( un camion ne traverse pas la mer )."""
    w = p.w
    for cmd in list(w.gouv.commandes):
        b, dest = cmd["bien"], cmd["destination"]
        lieu_dest = w.depot_armee if dest == "armee" else w.carte.gouvernement
        ms = [x for x in w.marches.values() if x.lieu.ile == lieu_dest.ile]
        if not ms: continue
        m = max(ms, key=lambda x: (x.stocks[b], x.lieu.id))
        tr = lg.par_capitale.get(m.lieu.id)
        ck = capacite_libre(p, tr)[0] if tr is not None else 0.0
        q = min(cmd["quantite"], m.stocks[b], ck / max(EPS, masse_kg(p, b)))
        m.demande[b] += cmd["quantite"]
        if q < 1: continue
        cout = q * m.prix[b]
        if w.gouv.caisse < cout: continue
        if _lancer(p, m.lieu, lieu_dest, {b: q}, w.gouv, "commande_" + dest, m) is not None:
            m.stocks[b] -= q; _compter(lg.sorties, m.lieu.id, b, q)
            w.transferer(w.gouv, m, cout, "commande publique")
            cmd["quantite"] -= q; cmd["_dest"] = dest
            if cmd["quantite"] < 1: w.gouv.commandes.remove(cmd)


class RemplaceExpedier:
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self, h): _expedier(self.pays, h)


# ================================================================== arrivees
def _arrivees(p):
    w = p.w; lg = _lg(p); cat = p.socle.catalogue
    arrives = [c for c in w.convois if c.arrivee <= w.pas]
    for c in arrives:
        w.convois.remove(c)
        info = lg.convois.pop(c.id, None)
        if info is not None and info[2] >= 0 and info[2] in lg.lots:
            _arrivee_lot(p, lg, c, lg.lots[info[2]]); continue
        if c.motif == "ravitaillement_base":
            for b, q in c.cargaison.items(): w.garnisons[c.destination.id][b] += q
            w.derniere_livraison[c.destination.id] = w.jour
            continue
        f = lg.recepteurs.get("convoi:" + c.motif)
        if f is not None: f(p, c); continue
        if c.motif in ("vente", "commerce"):
            m = w.marches[c.destination.id]
            for b, q in c.cargaison.items():
                m.stocks[b] += q; m.offre[b] += q; _compter(lg.entrees, m.lieu.id, b, q)
                w.transferer(m, c.vendeur if c.motif == "vente" else c.payeur, q * m.prix[b] * (1 - m.marge), c.motif)
        elif c.motif == "approvisionnement":
            for b, q in c.cargaison.items(): c.payeur.stocks[b] += q
        elif c.motif.startswith("commande_"):
            dest = c.motif[len("commande_"):]
            for b, q in c.cargaison.items(): w.publics[dest][b] += q
        else:
            raise KeyError(f"convoi {c.id} au motif {c.motif!r} sans recepteur ( logistique.recevoir_convoi )")
        w.noter("convoi", id=c.id, motif=c.motif, de=c.origine.id, vers=c.destination.id,
                cargaison={b: round(q, 1) for b, q in c.cargaison.items()})


class RemplaceArrivees:
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self): _arrivees(self.pays)


# ================================================================== les lots
def _stock_e1(p, d): return EXT.StockE1(d, p.socle.catalogue)


def _ile(p, lieu_id): return p.w.carte.lieux[lieu_id].ile


def _terminaux_du_lot(p, lg, lot):
    """( terminal de depart, terminal d arrivee ) d un lot par mer ou par air."""
    io, id_ = _ile(p, lot.origine), _ile(p, lot.dest)
    table = lg.aeroport_de if lot.mode == "avion" else lg.port_de
    return lg.terminaux[table[io]], lg.terminaux[table[id_]]


def _nouveau_lot(p, lg, cle, bien, q, mode, origine, dest, source, payeur, marche_o=None, marche_d=None,
                 recepteur="marche"):
    """Le lot quitte `source` ( un stock ) pour le quai d expedition de son lieu de depart ( entrepot du marche, ou
    hangar du terminal quand il part d un port ). Rend le Lot ou None."""
    w = p.w; L = p.socle.livre; cat = p.socle.catalogue
    ent = lg.entrepots[lg.quai_marche[origine]] if origine in lg.quai_marche else None
    if ent is None: return None
    kg, m3 = q * masse_kg(p, bien), q * volume_l(p, bien) / 1000.0
    if not a_la_place(p, ent, kg, m3): lg.stats["entrepot_plein"] += 1; return None
    q = L.deplacer(source, ent.stock, cat.id(bien), q, "preparation_lot")
    if q <= EPS: return None
    kg, m3 = q * masse_kg(p, bien), q * volume_l(p, bien) / 1000.0
    lot = Lot(lg.prochain_lot, cle, bien, q, kg, m3, mode, origine, dest, marche_o, marche_d, payeur, recepteur, w.pas)
    lot.ou = ent.k
    lg.prochain_lot += 1
    lg.lots[lot.id] = lot
    if marche_o is not None: lot.valeur = q * w.marches[marche_o].prix[bien]
    lg.stats["lots"] += 1
    p.compter("lot_expedie", q)
    return lot


def _premier_bout(p, lg, lot):
    """Le lieu que vise le premier convoi du lot : l arrivee ( route ), le port ou l aeroport de depart."""
    if lot.mode == "route": return p.w.carte.lieux[lot.dest]
    return _terminaux_du_lot(p, lg, lot)[0].lieu


def _marche_capitale(p, lieu_id):
    """Le marche dont les convoyeurs et le transporteur servent ce lieu."""
    return p.w.marches[p.w.carte.lieux[lieu_id].marche.id]


def _charger_convoi(p, lg, lot, src, o, d, motif, marche):
    """Un convoi pour le lot : depuis `src` ( un Stock du socle ) vers `d`. Rend vrai s il part."""
    cat = p.socle.catalogue
    cargo = {}
    r = _lancer(p, o, d, cargo, lot.payeur, motif, marche, kg=lot.kg, m3=lot.m3, lot=lot.id)
    if r is None: return False
    cv, prix = r
    x = p.socle.livre.deplacer(src, _stock_e1(p, cargo), cat.id(lot.bien), lot.q, "chargement_lot")
    if abs(x - lot.q) > 1e-9 * max(1.0, lot.q): raise RuntimeError(f"lot {lot.id} : {x} charges pour {lot.q}")
    lot.fret += prix; lot.convoi = cv.id
    return True


def _avancer_lots(p, lg):
    """Chaque heure pleine : les lots prets partent vers leur prochain bout de route."""
    w = p.w; carte = w.carte
    for lot in list(lg.lots.values()):
        if lot.etat == PREPARATION:
            ent = lg.entrepots[lot.ou]
            o = carte.lieux[lot.origine]; d = _premier_bout(p, lg, lot)
            if lot.mode != "route" and not a_la_place(p, _terminaux_du_lot(p, lg, lot)[0].entrepot, lot.kg, lot.m3):
                lg.stats["entrepot_plein"] += 1                # le hangar du port est plein : le lot attend a son quai
                if w.pas - lot.pas_decision > PREPARATION_MAX_H * PAS_H: _annuler(p, lg, lot)
                continue
            if o is d:
                if lot.mode == "route": _livrer(p, lg, lot, ent.stock); continue
                ta = _terminaux_du_lot(p, lg, lot)[0]
                p.socle.livre.deplacer(ent.stock, ta.entrepot.stock, p.socle.catalogue.id(lot.bien), lot.q, "quai")
                lot.etat, lot.ou, lot.pas_dispo = QUAI_A, ta.entrepot.k, w.pas
                continue
            if _charger_convoi(p, lg, lot, ent.stock, o, d, "fret_lot" if lot.mode == "route" else "fret_port",
                               _marche_capitale(p, lot.origine)):
                lot.etat = ROUTE1
            elif w.pas - lot.pas_decision > PREPARATION_MAX_H * PAS_H:
                _annuler(p, lg, lot)
        elif lot.etat == QUAI_B and lot.pas_dispo <= w.pas:
            t = lg.terminaux[_terminal_du_hangar(lg, lot.ou)]
            d = carte.lieux[lot.dest]
            if t.lieu is d: _livrer(p, lg, lot, t.entrepot.stock); continue
            if _charger_convoi(p, lg, lot, t.entrepot.stock, t.lieu, d, "fret_livraison", _marche_capitale(p, lot.dest)):
                lot.etat = ROUTE2


def _terminal_du_hangar(lg, k_entrepot):
    for t in lg.terminaux:
        if t.entrepot.k == k_entrepot: return t.k
    raise KeyError(k_entrepot)


def _annuler(p, lg, lot):
    """Le lot n a trouve ni chauffeur ni vehicule en un jour : il revient a son expediteur."""
    ent = lg.entrepots[lot.ou]
    retour = lg.recepteurs["retour:" + lot.recepteur] if ("retour:" + lot.recepteur) in lg.recepteurs else None
    if lot.marche_o is not None:
        m = p.w.marches[lot.marche_o]
        p.socle.livre.deplacer(ent.stock, _stock_e1(p, m.stocks), p.socle.catalogue.id(lot.bien), lot.q, "lot_annule")
        _compter(lg.entrees, lot.marche_o, lot.bien, lot.q)
    elif retour is not None: retour(p, lot, ent.stock)
    lot.etat = ANNULE
    s = lg.suivi.get(lot.cle)
    if s is not None: s[2] = 0.0
    del lg.lots[lot.id]
    lg.stats["lots_annules"] += 1
    p.compter("lot_annule")


def _arrivee_lot(p, lg, c, lot):
    src = _stock_e1(p, c.cargaison)
    if lot.etat == ROUTE1 and lot.mode != "route":
        ta = _terminaux_du_lot(p, lg, lot)[0]
        p.socle.livre.deplacer(src, ta.entrepot.stock, p.socle.catalogue.id(lot.bien), lot.q, "dechargement_lot")
        lot.etat, lot.ou, lot.convoi, lot.pas_dispo = QUAI_A, ta.entrepot.k, -1, p.w.pas
        return
    _livrer(p, lg, lot, src)


def _recevoir_marche(p, lot, src):
    """Le recepteur des lots entre marches : le lot entre au marche d arrivee, qui le paie RENDU a celui d origine
    ( valeur au prix de depart + tout le fret ) ; ce qu il ne peut payer devient une creance."""
    w = p.w; L = p.socle.livre
    m = w.marches[lot.marche_d]
    q = L.deplacer(src, _stock_e1(p, m.stocks), p.socle.catalogue.id(lot.bien), lot.q, "livraison_lot")
    m.offre[lot.bien] += q
    _compter(_lg(p).entrees, m.lieu.id, lot.bien, q)
    if lot.marche_o is not None:
        _, c = L.payer_ou_devoir(m, w.marches[lot.marche_o], lot.valeur + lot.fret, "cession_lot", p.socle.creances, p.jour)
        if c is not None: _lg(p).dettes.append(c)


def _livrer(p, lg, lot, src):
    w = p.w
    lg.recepteurs[lot.recepteur](p, lot, src)
    lot.etat, lot.pas_livre, lot.convoi = LIVRE, w.pas, -1
    lg.transits[lot.mode].append((w.pas - lot.pas_decision) / PAS_H)
    lg.stats["lots_livres"] += 1
    p.compter("lot_livre", lot.q)
    s = lg.suivi.get(lot.cle)
    if s is not None and lot.marche_d is not None and lot.marche_o is not None:
        s[3] = lot.q
        md, mo = w.marches[lot.marche_d], w.marches[lot.marche_o]
        pm = max(EPS, p.socle.catalogue[lot.bien].prix_monde)
        marge = (lot.q * (md.prix[lot.bien] - mo.prix[lot.bien]) - lot.fret) / max(EPS, lot.q * pm)
        s[8] += POIDS_MARGE * max(-1.0, min(1.0, marge))
    del lg.lots[lot.id]


def a_la_place(p, ent, kg, m3):
    """Vrai si l entrepot peut recevoir encore `kg` et `m3`."""
    o_m3, o_t = occupation(p, ent)
    return o_m3 + m3 <= ent.capacite_m3 + EPS and o_t + kg / 1000.0 <= ent.capacite_t + EPS


def occupation(p, ent):
    """( m3, t ) occupes dans un entrepot."""
    m3 = t = 0.0; cat = p.socle.catalogue
    for b, q in ent.stock.items():
        m3 += q * volume_l(p, b) / 1000.0; t += q * masse_kg(p, b) / 1000.0
    return m3, t


# ================================================================== les navires
def _pas_a(jour, heure):
    """Le pas du monde ou tombe `heure` du jour `jour`."""
    return int(round((jour * 1440 + heure * 60 - C.DATE_DEPART[3] * 60 - C.DATE_DEPART[4]) / C.MINUTES_PAR_PAS))


def _poser_a(p, pas, type_, cle, donnees):
    p.poser(max(0, pas - p.w.pas), type_, cle, donnees)


def _programmer(p):
    """0 h 10 : les departs du jour depuis l ile principale."""
    lg = _lg(p); cal = p.socle.calendrier
    js = cal.jour_semaine(p.w.pas)
    for li in lg.lignes:
        if js in li.jours: _poser_a(p, _pas_a(p.jour, li.heure_a), "logistique_appareiller", li.navire, (li.a,))


def _soute(p, lg, nav, arm, besoin):
    """Le navire soute jusqu a RESERVE_SOUTE traversees : raffinerie du pays ( domaine 11 ), l import pour le reste.
    Rend vrai si la traversee est couverte."""
    L = p.socle.livre; fid = p.socle.catalogue.id("fioul")
    if nav.stock[fid] >= besoin - EPS: return True
    voulu = RESERVE_SOUTE * besoin - nav.stock[fid]
    c0 = arm.caisse
    x = ENE.vendre_produit(p, arm, "fioul", voulu, nav) if p.a("energie") else 0.0
    if voulu - x > EPS and nav.stock[fid] < besoin:
        q, _ = EXT.importer_au_port(p, arm, nav.stock, "fioul", voulu - x, "import_biens")
        if q > EPS: lg.stats["soutes_importees"] += q; p.compter("soute_importee", q)
    arm.couts_j += c0 - arm.caisse
    return nav.stock[fid] >= besoin - EPS


def _appareiller(p, k, donnees):
    """Le navire `k` part du terminal donne : il charge ce qui attend pour l autre bout de sa ligne ( les plus anciens
    d abord ), dans sa cale et dans ce que le terminal manutentionne pendant sa fenetre - le premier lot passe toujours,
    quitte a retarder le depart -, soute et traverse."""
    w = p.w; lg = _lg(p); L = p.socle.livre; cat = p.socle.catalogue
    nav = lg.navires[k]; t = lg.terminaux[donnees[0]]; li = lg.lignes[nav.ligne]
    if not lg.mer_ouverte: return
    if nav.terminal != t.k:
        nav.en_attente = t.k; return
    autre = lg.terminaux[li.b if t.k == li.a else li.a]
    gen = NAVIRES[nav.modele]
    heures = li.km / (gen[5] * KMH_PAR_NOEUD)
    fioul = heures * gen[6] * 1000.0 / masse_kg(p, "fioul")
    arm = lg.armateurs[li.armateur]
    if li.genre == "caboteur" and t.k == li.a and not any(
            x.etat == QUAI_A and x.ou == t.entrepot.k and x.mode == "caboteur" and x.pas_dispo <= w.pas for x in lg.lots.values()):
        return                                     # le caboteur reste au port d attache tant qu il n a rien a porter
    if not _soute(p, lg, nav, arm, fioul):
        p.noter("escale", navire=nav.k, port=t.lieu.id, lots=0, tonnes=0.0, attente_h=-1.0); return
    cap_kg, cap_m3 = gen[7] * 1000.0, gen[8]
    t_h = t.t_h(li.genre)
    kg = m3 = 0.0; charges = []
    attente = sorted((x for x in lg.lots.values() if x.etat == QUAI_A and x.ou == t.entrepot.k and x.mode == li.genre
                      and _ile(p, x.dest) == autre.ile and x.pas_dispo <= w.pas), key=lambda x: (x.pas_dispo, x.id))
    for lot in attente:
        if kg + lot.kg > cap_kg or m3 + lot.m3 > cap_m3: continue
        if charges and (kg + lot.kg) / 1000.0 / t_h > FENETRE_H[li.genre]: continue
        tp = tonnes_payantes(lot.kg, lot.m3)
        prix = tp * (FRET_T_EUROS[li.genre] + MANUTENTION_T_EUROS[li.genre]) * DR
        if lot.payeur.caisse < prix: continue
        L.transferer(lot.payeur, arm, tp * FRET_T_EUROS[li.genre] * DR, "fret_mer")
        L.transferer(lot.payeur, t.autorite, tp * MANUTENTION_T_EUROS[li.genre] * DR, "manutention")
        arm.recettes_j += tp * FRET_T_EUROS[li.genre] * DR; arm.recettes += tp * FRET_T_EUROS[li.genre] * DR
        t.autorite.recettes += tp * MANUTENTION_T_EUROS[li.genre] * DR
        lot.fret += prix
        L.deplacer(t.entrepot.stock, nav.stock, cat.id(lot.bien), lot.q, "embarquement")
        lot.etat, lot.ou = EN_MER, nav.k
        nav.a_bord.append(lot.id); charges.append(lot)
        kg += lot.kg; m3 += lot.m3
    retard_h = max(0.0, kg / 1000.0 / t_h - FENETRE_H[li.genre])
    lg.stats["retard_port_h"] += retard_h
    L.bruler(nav.stock, cat.id("fioul"), fioul, "soute_navire")
    t.occupes = max(0, t.occupes - 1)
    t.tonnes += kg / 1000.0
    nav.terminal = -1; nav.traversees += 1
    lg.stats["traversees"] += 1; lg.stats["tonnes_mer"] += kg / 1000.0
    _poser_a(p, w.pas + math.ceil((retard_h + heures) * PAS_H), "logistique_accoster", nav.k, (autre.k,))
    p.noter("escale", navire=nav.k, port=t.lieu.id, lots=len(charges), tonnes=round(kg / 1000.0, 3),
            attente_h=round(retard_h, 2))


def _accoster(p, k, donnees):
    """Le navire arrive : un poste a quai ( sinon il attend en rade ), droits de port, dechargement au rythme du
    terminal ; puis le depart du retour, ou le depart qu il a manque."""
    w = p.w; lg = _lg(p); L = p.socle.livre; cat = p.socle.catalogue
    nav = lg.navires[k]; t = lg.terminaux[donnees[0]]; li = lg.lignes[nav.ligne]
    gen = NAVIRES[nav.modele]
    if t.occupes >= t.quais:
        t.attente_h += 1.0; lg.stats["attente_rade_h"] += 1.0; p.compter("attente_quai_h", 1.0)
        _poser_a(p, w.pas + PAS_H, "logistique_accoster", k, donnees); return
    t.occupes += 1; t.escales += 1
    nav.terminal = t.k
    arm = lg.armateurs[li.armateur]
    droits = L.transferer(arm, t.autorite, gen[3] * DROITS_PORT_GT_EUROS * DR, "droits_de_port")
    arm.couts_j += droits; t.autorite.recettes += droits
    kg = sum(lg.lots[i].kg for i in nav.a_bord if i in lg.lots)
    dispo = w.pas + math.ceil(kg / 1000.0 / t.t_h(li.genre) * PAS_H)
    for i in nav.a_bord:
        lot = lg.lots.get(i)
        if lot is None: continue
        L.deplacer(nav.stock, t.entrepot.stock, cat.id(lot.bien), lot.q, "debarquement")
        tp = tonnes_payantes(lot.kg, lot.m3)
        paye, _ = L.payer_ou_devoir(lot.payeur, t.autorite, tp * MANUTENTION_T_EUROS[li.genre] * DR, "manutention",
                                    p.socle.creances, p.jour)
        t.autorite.recettes += paye
        lot.fret += tp * MANUTENTION_T_EUROS[li.genre] * DR
        lot.etat, lot.ou, lot.pas_dispo = QUAI_B, t.entrepot.k, dispo
    nav.a_bord = []
    t.tonnes += kg / 1000.0
    if nav.en_attente == t.k:
        nav.en_attente = -1
        _poser_a(p, w.pas + math.ceil(ESCALE_MIN_H * PAS_H), "logistique_appareiller", k, (t.k,))
    elif t.k == li.b:
        j = p.jour if p.heure + ESCALE_MIN_H <= li.heure_b else p.jour + 1
        _poser_a(p, _pas_a(j, li.heure_b), "logistique_appareiller", k, (t.k,))


# ================================================================== l avion
def _vols(p):
    """Toutes les heures et demie, de jour : un avion libre a sa base ou a une escale emporte les lots qui l attendent
    vers une meme ile ; aller et retour affretes, payes par les expediteurs au prorata de la masse."""
    w = p.w; lg = _lg(p); L = p.socle.livre; cat = p.socle.catalogue
    if not lg.mer_ouverte: return
    t0 = time.perf_counter()
    for av in lg.avions:
        if av.libre > w.pas or av.terminal < 0: continue
        t = lg.terminaux[av.terminal]
        prets = sorted((x for x in lg.lots.values() if x.etat == QUAI_A and x.mode == "avion" and x.ou == t.entrepot.k
                        and x.pas_dispo <= w.pas), key=lambda x: (x.pas_dispo, x.id))
        if not prets: continue
        ile = _ile(p, prets[0].dest)
        autre = lg.terminaux[lg.aeroport_de[ile]]
        kg = m3 = 0.0; pris = []
        for lot in prets:
            if _ile(p, lot.dest) != ile or kg + lot.kg > AVION[5] or m3 + lot.m3 > AVION[6]: continue
            pris.append(lot); kg += lot.kg; m3 += lot.m3
        bloc = KM_ENTRE_ILES / AVION[7] + BLOC_SUPPLEMENT_H
        prix = 2.0 * bloc * TARIF_BLOC_EUROS_H * DR
        if any(lot.payeur.caisse < prix * lot.kg / kg for lot in pris): pris = [x for x in pris if x.payeur.caisse >= prix]
        if not pris: continue
        kg = sum(x.kg for x in pris)
        comp = av.compagnie
        kid = cat.id("kerosene"); ker = 2.0 * bloc * AVION[8] / T14.LITRES_UNITE
        if av.stock[kid] < ker:
            c0 = comp.caisse
            x = ENE.vendre_produit(p, comp, "kerosene", 2 * ker - av.stock[kid], av) if p.a("energie") else 0.0
            if av.stock[kid] < ker: EXT.importer_au_port(p, comp, av.stock, "kerosene", 2 * ker - av.stock[kid], "import_biens")
            if av.stock[kid] < ker: continue
        for lot in pris:
            part = prix * lot.kg / kg
            L.transferer(lot.payeur, comp, part, "affretement_aerien")
            man = lot.kg / 1000.0 * MANUTENTION_T_EUROS["avion"] * DR
            L.transferer(lot.payeur, t.autorite, man, "manutention")
            t.autorite.recettes += man
            lot.fret += part + man
            L.deplacer(t.entrepot.stock, av.stock, cat.id(lot.bien), lot.q, "embarquement")
            lot.etat, lot.ou = EN_MER, av.k
            av.a_bord.append(lot.id)
        comp.recettes += prix; comp.vols += 1
        red = 2.0 * AVION[4] / 1000.0 * REDEVANCE_ATTERRISSAGE_T_EUROS * DR
        L.transferer(comp, t.autorite, red / 2, "redevance_aeroport"); L.transferer(comp, autre.autorite, red / 2, "redevance_aeroport")
        L.bruler(av.stock, kid, ker, "kerosene_vol")
        av.terminal = -1; av.libre = w.pas + math.ceil(2 * bloc * PAS_H)
        lg.stats["vols"] += 1; lg.stats["tonnes_air"] += kg / 1000.0
        _poser_a(p, w.pas + math.ceil(bloc * PAS_H), "logistique_atterrir", av.k, (autre.k, t.k))
        p.noter("vol_cargo", avion=av.k, de=t.lieu.id, vers=autre.lieu.id, lots=len(pris), kg=round(kg, 1))
    _chrono(lg, "vols", t0)


def _atterrir(p, k, donnees):
    """L avion pose ses lots au hangar de l aeroport d arrivee, puis rentre ( le retour est deja affrete )."""
    w = p.w; lg = _lg(p); L = p.socle.livre; cat = p.socle.catalogue
    av = lg.avions[k]; t = lg.terminaux[donnees[0]]
    dispo = w.pas + max(1, math.ceil(sum(lg.lots[i].kg for i in av.a_bord if i in lg.lots) / 1000.0 / t.t_h("avion") * PAS_H))
    for i in av.a_bord:
        lot = lg.lots.get(i)
        if lot is None: continue
        L.deplacer(av.stock, t.entrepot.stock, cat.id(lot.bien), lot.q, "debarquement")
        lot.etat, lot.ou, lot.pas_dispo = QUAI_B, t.entrepot.k, dispo
    av.a_bord = []
    av.terminal = donnees[1]


# ================================================================== la decision
def _demande(p, mid, b):
    em = p.domaine("economie").marches[mid]
    return max(ECO.DEMANDE_MIN, em.demande_lisse.get(b, 0.0))


def couverture(p, mid, b):
    """Jours de demande lissee que le stock affiche d un marche tient."""
    return max(0.0, p.w.marches[mid].stocks[b]) / _demande(p, mid, b)


def _ligne_vers(lg, ile_a, ile_b, genre):
    for li in lg.lignes:
        if li.genre != genre: continue
        ia, ib = lg.terminaux[li.a].ile, lg.terminaux[li.b].ile
        if {ia, ib} == {ile_a, ile_b}: return li
    return None


def heures_avant_depart(p, lg, ile_a, ile_b, genre):
    """Heures jusqu au prochain depart publie de `ile_a` vers `ile_b` ( 999 sans ligne )."""
    li = _ligne_vers(lg, ile_a, ile_b, genre)
    if li is None or not lg.mer_ouverte: return 999.0
    cal = p.socle.calendrier; w = p.w
    depuis_a = lg.terminaux[li.a].ile == ile_a
    for j in range(p.jour, p.jour + 15):
        if depuis_a:
            js = cal.jour_semaine(_pas_a(j, 12.0))
            if js not in li.jours: continue
            pas = _pas_a(j, li.heure_a)
        else:
            js = cal.jour_semaine(_pas_a(j - 1, 12.0))
            if js not in li.jours: continue
            pas = _pas_a(j, li.heure_b)
        if pas >= w.pas: return (pas - w.pas) / PAS_H
    return 999.0


def _veille_de_repos(p):
    cal = p.socle.calendrier
    return not cal.ouvre(cal.date(p.w.pas + C.PAS_PAR_JOUR))


def _cout_unitaire(p, lg, mo, md, b, mode):
    """Le fret d une unite ( drachmes ), pour la regle : route au cout d un camion, mer au tarif et a la manutention."""
    w = p.w; carte = w.carte
    kg_u, m3_u = masse_kg(p, b), volume_l(p, b) / 1000.0
    route = 2 * 0.3 * w.marches[mo].prix["carburant"] / T14.LITRES_UNITE * 1.3 * DR   # ~ 30 l/100 km, 1,3 x le gazole
    if mode == "route": return carte.km_route(carte.lieux[mo], carte.lieux[md]) * route / 20.0 + 0.01
    tp = max(kg_u / 1000.0, m3_u)
    return tp * (FRET_T_EUROS.get(mode, 0.0) + 2 * MANUTENTION_T_EUROS.get(mode, 0.0)) * DR + 0.02


def _contexte(p, lg, m, b, q, dem):
    w = p.w; mid = m.lieu.id; ile = m.lieu.ile
    ici = [x for x in sorted(w.marches) if x != mid and w.marches[x].lieu.ile == ile]
    ailleurs = [x for x in sorted(w.marches) if w.marches[x].lieu.ile != ile and lg.mer_ouverte
                and _ligne_vers(lg, ile, w.marches[x].lieu.ile, "ferry") is not None]
    cabo = [x for x in ailleurs if _ligne_vers(lg, ile, w.marches[x].lieu.ile, "caboteur") is not None]
    air = [x for x in ailleurs if lg.avions and w.marches[x].lieu.ile in lg.aeroport_de and ile in lg.aeroport_de]

    def cher(cs): return max(cs, key=lambda x: (w.marches[x].prix[b], x)) if cs else None

    def bas(cs): return min(cs, key=lambda x: (couverture(p, x, b), x)) if cs else None
    cibles = (None, cher(ici), bas(ici), cher(ailleurs), bas(ailleurs), bas(cabo), bas(air))
    pm = max(EPS, C.PRIX_MONDE.get(b, p.socle.catalogue[b].prix_monde))
    c_o = couverture(p, mid, b)
    c_i = min((couverture(p, x, b) for x in ici), default=10.0)
    c_a = min((couverture(p, x, b) for x in ailleurs), default=10.0)
    p_i = max((w.marches[x].prix[b] for x in ici), default=0.0)
    p_a = max((w.marches[x].prix[b] for x in ailleurs), default=0.0)
    x_bas = bas(ici + ailleurs)
    manque = 0.0
    if x_bas is not None:
        A, S, U, Dm = lg.mesure.get((x_bas, b), (0.0, 0.0, 0.0, 0.0))
        manque = U / max(EPS, Dm) if Dm > EPS else 0.0
    ile_f = w.marches[bas(ailleurs)].lieu.ile if ailleurs else None
    hf = heures_avant_depart(p, lg, ile, ile_f, "ferry") if ile_f else 999.0
    hc = heures_avant_depart(p, lg, ile, ile_f, "caboteur") if ile_f else 999.0
    x = (min(1.0, c_o / 10.0), min(1.0, c_i / 10.0), min(1.0, c_a / 10.0), min(1.0, m.prix[b] / (3 * pm)),
         min(1.0, p_i / (3 * pm)), min(1.0, p_a / (3 * pm)), min(1.0, max(0.0, manque)), min(1.0, hf / 72.0),
         min(1.0, hc / 168.0), min(1.0, q / max(EPS, dem) / 5.0), 1.0 if b in ESSENTIELS else 0.0)
    ach_o = m.prix[b] * (1 - m.marge)
    gr = (w.marches[cher(ici)].prix[b] * (1 - w.marches[cher(ici)].marge) - ach_o - _cout_unitaire(p, lg, mid, cher(ici), b, "route")) if ici else -1.0
    gm = (w.marches[cher(ailleurs)].prix[b] * (1 - w.marches[cher(ailleurs)].marge) - ach_o
          - _cout_unitaire(p, lg, mid, cher(ailleurs), b, "ferry")) if ailleurs else -1.0
    return ContexteLot(x, cibles, b, hf, hc, gr - 0.05 * ach_o, gm - 0.05 * ach_o, bool(ailleurs))


def _observer(ctx): return ctx.traits


def _regle(x, ctx):
    c_o, c_i, c_a = x[0] * 10.0, x[1] * 10.0, x[2] * 10.0
    seuil = min(COUV_ALERTE_J, c_o - 1.0)
    if ctx.autres and c_a < seuil and c_a <= c_i:
        if ctx.bien == "remedes" and c_a < 0.5 and ctx.cibles[6] is not None: return 6
        if ctx.heures_ferry <= 36.0 or ctx.heures_ferry <= ctx.heures_cabo or ctx.cibles[5] is None: return 4
        return 5
    if ctx.cibles[2] is not None and c_i < seuil: return 2
    if ctx.cibles[1] is not None and ctx.gain_route > 0: return 1
    if ctx.cibles[3] is not None and ctx.gain_mer > 0: return 3
    return 0


def _temoin(x, ctx, rng): return 3 if ctx.autres else 1


POINT_LOT = D.PointDeDecision(
    "expedier_lot", "logistique",
    traits=(("couverture_origine", "le stock affiche de son marche en jours de demande lissee, sur 10"),
            ("couverture_ile", "la plus basse des autres marches de son ile ( stocks affiches ), sur 10"),
            ("couverture_autres_iles", "la plus basse des marches des iles desservies ( stocks affiches ), sur 10"),
            ("prix_origine", "le prix affiche de son marche, sur 3 fois le prix mondial"),
            ("prix_max_ile", "le prix affiche le plus haut de son ile, sur 3 fois le prix mondial"),
            ("prix_max_autres_iles", "le prix affiche le plus haut des iles desservies, sur 3 fois le prix mondial"),
            ("ruptures_cible", "les ruptures publiees hier par le marche le moins couvert, sur sa demande"),
            ("heures_ferry", "les heures jusqu au prochain ferry publie, sur 72"),
            ("heures_caboteur", "les heures jusqu au prochain caboteur publie, sur 168"),
            ("surplus", "le lot en jours de demande de son marche, sur 5"),
            ("essentiel", "1 pour la nourriture et les remedes ( la nature du bien )")),
    actions=ACTIONS, observer=_observer, regle=_regle, temoin=_temoin,
    note="chaque soir, pour CE lot : la part du lot qui a servi une demande restee sinon sans reponse la ou il est livre "
         "( ventes avec et sans ses unites ), moins la part qui a manque a son marche d origine, plus le jour de la "
         "livraison la moitie de sa marge ( ecart de prix moins fret, sur sa valeur, bornee a +-1 ) ; attendre vaut "
         "zero ; moyenne sur 5 jours",
    horizon_j=HORIZON_LOT)


def _decider(p):
    """8 h 40, 11 h 40, 14 h 40 : chaque marche decide, bien par bien, ou envoyer ce qu il a au-dela de sa garde - avant
    que le negoce du domaine 7 n exporte le surplus a l heure moins 10."""
    w = p.w; lg = _lg(p); dec = lg.decideur; t0 = time.perf_counter()
    veille = _veille_de_repos(p)
    for mid in sorted(w.marches):
        m = w.marches[mid]
        if not any(h.vivant and au_poste(h) for h in w.au_travail_de(m.lieu, "convoyeur")): continue   # depot ferme
        for b in BIENS_DECISION:
            dem = _demande(p, mid, b)
            garde = (GARDE_J + (GARDE_VEILLE_J if veille else 0.0)) * dem
            surplus = m.stocks[b] - garde
            if surplus < LOT_MIN_U: continue
            q = min(surplus, LOT_MAX_J * dem)
            if q < LOT_MIN_U: continue
            ctx = _contexte(p, lg, m, b, q, dem)
            cle = lg.cle; lg.cle += 1
            a = dec.decider(cle, ctx)
            dest, mode = ctx.cibles[a], MODE_ACTION[a]
            lot = None
            if dest is not None:
                lot = _nouveau_lot(p, lg, cle, b, q, mode, mid, dest, _stock_e1(p, m.stocks), m, mid, dest)
                if lot is not None: _compter(lg.sorties, mid, b, lot.q)
            lg.suivi[cle] = [lot.id if lot else -1, a, lot.q if lot else 0.0, 0.0, max(EPS, lot.q if lot else q), mid,
                             dest, b, 0.0]
    _chrono(lg, "decision", t0)


def _avant_achats(p):
    """18 h 50, apres le negoce du domaine 7 : ce que chaque marche a avant les achats du soir."""
    lg = _lg(p)
    lg.snap = {mid: {b: m.stocks[b] for b in BIENS_DECISION} for mid, m in p.w.marches.items()}
    lg.entrees, lg.sorties = {}, {}


def _mesurer(p, lg):
    """19 h : pour chaque marche et chaque bien des menages, A ( offert avant les achats ), S ( vendu ), U ( demande
    payable non servie, domaine 3 ), D = S + U."""
    w = p.w; eco = p.domaine("economie").marches
    lg.mesure = {}
    for mid, m in w.marches.items():
        for b in BIENS_DECISION:
            a0 = lg.snap.get(mid, {}).get(b, m.stocks[b]) + lg.entrees.get(mid, {}).get(b, 0.0) - lg.sorties.get(mid, {}).get(b, 0.0)
            A = max(0.0, a0)
            S = max(0.0, A - m.stocks[b])
            U = max(0.0, eco[mid].non_servi.get(b, 0.0))
            lg.mesure[(mid, b)] = (A, S, U, S + U)


def _noter(p):
    """19 h : la note du jour de chaque decision en attente ( la mesure contrefactuelle de la fiche )."""
    lg = _lg(p); dec = lg.decideur; t0 = time.perf_counter()
    _mesurer(p, lg)
    for cle in list(lg.suivi):
        s = lg.suivi[cle]
        lot_id, a, r_o, r_d, q, mo, md, b, marge = s
        r = 0.0
        if r_o > EPS:
            A, S, U, Dm = lg.mesure.get((mo, b), (0.0, 0.0, 0.0, 0.0))
            pen = min(Dm, A + r_o) - min(Dm, A)
            r -= pen / q
            vendu = min(Dm, A + r_o)
            s[2] = r_o * (1.0 - vendu / (A + r_o)) if A + r_o > EPS else 0.0
        if r_d > EPS and md is not None:
            A, S, U, Dm = lg.mesure.get((md, b), (0.0, 0.0, 0.0, 0.0))
            rd = min(r_d, A)
            r += (min(Dm, A) - min(Dm, A - rd)) / q
            s[3] = rd * (1.0 - S / A) if A > EPS else 0.0
        if marge != 0.0: r += marge; s[8] = 0.0
        dec.noter(cle, r, p.jour)
        att = dec.attentes.get(cle)
        if att is None or not att.choix:
            dec.attentes.pop(cle, None); del lg.suivi[cle]
    _chrono(lg, "notes", t0)


# ================================================================== le soir et le matin
def _soir(p):
    """23 h 40 : le magasinage des lots au-dela de leur franchise, la subvention de service public ( l Etat couvre le
    deficit du jour de chaque ligne ), le surplus des autorites a l Etat."""
    w = p.w; lg = _lg(p); L = p.socle.livre
    for lot in lg.lots.values():
        if lot.etat not in (QUAI_A, QUAI_B): continue
        lot.jours_quai += 1
        if lot.jours_quai <= FRANCHISE_MAGASINAGE_J: continue
        t = lg.terminaux[_terminal_du_hangar(lg, lot.ou)]
        x = L.transferer(lot.payeur, t.autorite, lot.m3 * MAGASINAGE_M3_J_EUROS * DR, "magasinage")
        lot.fret += x; t.autorite.recettes += x
        p.compter("magasinage", x)
    for arm in lg.armateurs:
        deficit = arm.couts_j - arm.recettes_j
        if deficit > EPS:
            x = L.transferer(w.gouv, arm, deficit, "subvention_ligne")
            arm.subventions += x; lg.stats["subventions"] += x
            p.compter("subvention_ligne", x)
        arm.couts_j = arm.recettes_j = 0.0
    for a in lg.autorites.values():
        if a.caisse > FONDS_AUTORITE: L.transferer(a, w.gouv, a.caisse - FONDS_AUTORITE, "surplus_autorite")
    K = p.socle.creances; garde = []
    for c in lg.dettes:                          # le marche debiteur regle ses lots a credit, les plus anciens d abord
        if K.actives.get(c.id) is not c: continue
        x = c.debiteur.caisse - RESERVE_REGLEMENT
        if x > EPS: K.regler(c, L, x)
        if K.actives.get(c.id) is c: garde.append(c)
    lg.dettes = garde


def _matin(p):
    """6 h 30 : chaque transporteur recompte sa flotte au Parc ( domaine 14 ) et complete ce qui manque a sa cible."""
    lg = _lg(p); t0 = time.perf_counter()
    for tr in lg.transporteurs: _completer_flotte(p, tr)
    _chrono(lg, "matin", t0)


def _cout_import(nom):
    """Ce que coute a la concession l import d un vehicule neuf ( FOB, fret, droit : domaine 14 )."""
    c = T14.caracteristiques(nom)
    return c.fob * (1.0 + EXT.FRET["produit_fini"]) * (1.0 + ET.DROITS_DOUANE["produit_fini"]) * (1.0 + 1e-6)


def _completer_flotte(p, tr):
    """Achete a la concession de son marche ce qui manque a la cible ( domaine 14, `acheter_flotte`, flotte non geree :
    chaque km est un convoi de ce domaine ). Un camion n est pas en stock : la concession le commande a l etranger
    ( 3 jours ) contre un ACOMPTE du transporteur - une concession de 500 habitants ne peut pas avancer 55 000 drachmes -
    rendu quand le vehicule arrive, avant la vente au prix catalogue."""
    L = p.socle.livre
    _recompter_flotte(p, tr)
    conc = T14._tr(p).par_marche[tr.marche_id][0]
    for nom, n in tr.cible.items():
        m = T14.IDX[nom]
        a = sum(1 for v in tr.vehicules if v[0] == nom)
        if a >= n: continue
        fait = T14.acheter_flotte(p, tr, nom, n - a, gere=False)
        du = tr.acomptes.get(nom, 0.0)
        if fait > 0 and du > EPS:            # la concession rend l acompte sur le prix qu elle vient de toucher
            tr.acomptes[nom] = du - L.transferer(conc, tr, min(du, fait * _cout_import(nom)), "acompte_vehicule")
        reste = n - a - fait - conc.commandes[m]
        if reste > 0 and tr.caisse >= reste * _cout_import(nom):
            x = L.transferer(tr, conc, reste * _cout_import(nom), "acompte_vehicule")
            k = T14.importer_vehicules(p, conc, nom, reste, conc.marche)
            tr.acomptes[nom] = tr.acomptes.get(nom, 0.0) + x
            if k < reste:
                tr.acomptes[nom] -= L.transferer(conc, tr, (reste - k) * _cout_import(nom), "acompte_vehicule")
    _recompter_flotte(p, tr)
    complet = all(sum(1 for v in tr.vehicules if v[0] == nom) >= n for nom, n in tr.cible.items())
    garde = FONDS_ROULEMENT + max(T14.caracteristiques(nom).prix_ttc for nom in tr.cible)
    if complet and not any(x > EPS for x in tr.acomptes.values()) and tr.caisse > 2 * garde:
        L.payer_l_exterieur(tr, tr.caisse - garde, "rapatriement_capital")   # l avance des acomptes rentre chez l investisseur


def _recompter_flotte(p, tr):
    """Les vehicules du transporteur tels que le Parc les compte ( un vol ou un rebut du domaine 14 s y lit )."""
    compte = {}
    for nom, n, _ in T14.vehicules_de(p, tr): compte[nom] = compte.get(nom, 0) + n
    garde = []
    for nom in sorted(compte):
        miens = sorted((v for v in tr.vehicules if v[0] == nom), key=lambda v: v[1])
        miens = miens[:compte[nom]]
        miens += [[nom, 0] for _ in range(compte[nom] - len(miens))]
        garde += miens
    tr.vehicules = garde


# ================================================================== installation
def _membres_transporteurs(w): return w.pays.domaines["logistique"].transporteurs
def _membres_autorites(w): return list(w.pays.domaines["logistique"].autorites.values())
def _membres_armateurs(w): return w.pays.domaines["logistique"].armateurs
def _membres_compagnies(w): return w.pays.domaines["logistique"].compagnies
def _membres_entrepots(w): return w.pays.domaines["logistique"].entrepots
def _membres_navires(w): return w.pays.domaines["logistique"].navires
def _membres_avions(w): return w.pays.domaines["logistique"].avions


def jours_de_service(genre, pop):
    """Les jours de la semaine ( 0 = lundi ) ou la ligne part de l ile principale : un ferry par jour a partir de 5 000
    habitants sur la plus petite ile, quatre par semaine a partir de 1 000, trois sinon ( le minimum d une ligne de
    service public, a calibrer ) ; un caboteur deux fois par semaine."""
    if genre == "ferry":
        if pop >= 5000: return (0, 1, 2, 3, 4, 5, 6)
        if pop >= 1000: return (0, 2, 4, 6)
        return (0, 2, 4)
    return (1, 5)


def _entrepot(lg, lieu_id, genre, surface):
    e = Entrepot(len(lg.entrepots), lieu_id, genre, surface)
    lg.entrepots.append(e)
    return e


def _installer_terminaux(p, lg):
    w = p.w; parc = p.socle.parc
    for ile in w.carte.iles:
        a = AutoritePortuaire(ile); lg.autorites[ile] = a
        port = w.carte.port(ile)
        if port is not None:
            t = Terminal(len(lg.terminaux), "port", ile, port, a, _entrepot(lg, port.id, "port", ENTREPOT_M2["port"]))
            lg.terminaux.append(t); lg.port_de[ile] = t.k
        nom = AEROPORTS.get(ile)
        lieu = w.carte.lieux.get(nom if ile == w.carte.iles[0] else f"{ile}:{nom}") if nom else None
        if lieu is None:
            caps = [c for c in w.carte.capitales if c.ile == ile]
            lieu = caps[0] if caps else None
        if lieu is not None:
            t = Terminal(len(lg.terminaux), "aeroport", ile, lieu, a,
                         _entrepot(lg, lieu.id, "aeroport", ENTREPOT_M2["aeroport"]))
            lg.terminaux.append(t); lg.aeroport_de[ile] = t.k
    mc = parc.par_nom.get("commerce")
    for mid in sorted(w.marches):
        n = 0
        if mc is not None:
            c = parc.cohortes.get((mc.id, w.marches[mid], mid))
            n = c.nombre if c is not None else 0
        e = _entrepot(lg, mid, "quai_marche", max(M2_COMMERCE, n * M2_COMMERCE))
        lg.quai_marche[mid] = e.k
    for t in lg.terminaux:          # un terminal qui est aussi un marche partage son hangar comme quai d expedition
        if t.lieu.id not in lg.quai_marche: lg.quai_marche[t.lieu.id] = t.entrepot.k


def _installer_transporteurs(p, lg):
    w = p.w; L = p.socle.livre
    for mid in sorted(w.marches):
        m = w.marches[mid]
        conv = sum(1 for h in w.au_travail_de(m.lieu, "convoyeur") if h.vivant)
        cible = {"camion": max(1, math.ceil(conv / CONVOYEURS_PAR_CAMION)),
                 "utilitaire": max(1, round(conv / CONVOYEURS_PAR_UTILITAIRE))}
        tr = Transporteur(mid, m.lieu, cible)
        lg.transporteurs.append(tr); lg.par_capitale[mid] = tr
    p.socle.registre.inscrire("transporteurs", "entreprises", _membres_transporteurs, "caisse", None, "Transporteur")
    for tr in lg.transporteurs:
        cap = sum(n * (T14.caracteristiques(nom).prix_ttc + _cout_import(nom)) for nom, n in tr.cible.items()) + FONDS_ROULEMENT
        L.recevoir_de_l_exterieur(tr, cap, "investissement_direct")
        _ouvrir_compte(p, tr)
        _completer_flotte(p, tr)


def _ouvrir_compte(p, x):
    if p.a("banques"):
        from . import d02_banques as BQ
        BQ.ouvrir_compte(p, x)


def _installer_flotte(p, lg):
    """Les modeles du domaine au Parc, puis une ligne ferry et une ligne caboteur de l ile principale vers chaque autre
    ile, et un avion a l aeroport de l ile principale ( s il y a plus d une ile )."""
    w = p.w; parc = p.socle.parc; L = p.socle.livre
    for nom, (genre, prix, masse, gt, lon, kn, tph, dwt, vol, src) in NAVIRES.items():
        lg.modeles[nom] = parc.declarer_modele(nom, "navire", prix * DR, masse, VIE_NAVIRE_H, None, None, src).id
    lg.modeles[AVION[0]] = parc.declarer_modele(AVION[0], "aeronef", AVION[2] * DR, AVION[3], VIE_AVION_H, AVION[1], None,
                                                "Dornier 228-212 ( constructeur ) ; corps CUP a verifier").id
    reg = p.socle.registre
    reg.inscrire("armateurs", "entreprises", _membres_armateurs, "caisse", None, "Armateur")
    reg.inscrire("compagnies_aeriennes", "entreprises", _membres_compagnies, "caisse", None, "CompagnieAerienne")
    iles = w.carte.iles
    if len(iles) < 2: return
    pop = {}
    for mg in w.menages:
        if mg.domicile is None: continue
        pop[mg.domicile.ile] = pop.get(mg.domicile.ile, 0) + sum(1 for x in mg.membres if x.vivant)
    hub = iles[0]
    for ile in iles[1:]:
        if hub not in lg.port_de or ile not in lg.port_de: continue
        ta, tb = lg.terminaux[lg.port_de[hub]], lg.terminaux[lg.port_de[ile]]
        km = w.carte.km_mer(ta.lieu, tb.lieu)
        petite = min(pop.get(hub, 0), pop.get(ile, 0))
        for genre in ("ferry", "caboteur"):
            modele = ("roro_egeen" if petite >= POP_GRAND_FERRY else "roro_ligne_vitale") if genre == "ferry" else "caboteur"
            arm = Armateur(f"{genre}_{hub}_{ile}"); lg.armateurs.append(arm)
            o = parc.creer(lg.modeles[modele], arm, ta.lieu.id, "initial", w.pas)
            nav = Navire(len(lg.navires), modele, o.id, ta.k)
            lg.navires.append(nav)
            ta.occupes += 1; ta.quais = max(ta.quais, ta.occupes)
            ha, hb = HEURES_LIGNE[genre]
            li = Ligne(len(lg.lignes), genre, ta.k, tb.k, nav.k, jours_de_service(genre, petite), ha, hb, km,
                       len(lg.armateurs) - 1)
            lg.lignes.append(li); nav.ligne = li.k
    if hub in lg.aeroport_de:
        comp = CompagnieAerienne(hub); lg.compagnies.append(comp)
        base = lg.aeroport_de[hub]
        o = parc.creer(lg.modeles[AVION[0]], comp, lg.terminaux[base].lieu.id, "initial", w.pas)
        lg.avions.append(Avion(0, o.id, base, comp))
    fr = masse_kg(p, "fioul")
    for li in lg.lignes:
        gen = NAVIRES[lg.navires[li.navire].modele]
        cap = CAPITAL_ARMATEUR_J * 2 * li.km / (gen[5] * KMH_PAR_NOEUD) * gen[6] * 1000.0 / fr * p.socle.catalogue["fioul"].prix_monde
        L.recevoir_de_l_exterieur(lg.armateurs[li.armateur], cap, "investissement_direct")
        _ouvrir_compte(p, lg.armateurs[li.armateur])
    for comp in lg.compagnies:
        L.recevoir_de_l_exterieur(comp, CAPITAL_COMPAGNIE, "investissement_direct"); _ouvrir_compte(p, comp)


def _installer_dockers(p, lg):
    """Avec le domaine 4 : l autorite portuaire emploie une equipe de dockers par grue, au port."""
    if not p.a("travail"): return
    from . import d04_travail as TR
    for t in lg.terminaux:
        if t.genre != "port": continue
        TR.declarer_employeur(p, t.lieu.id, "ouvrier", t.autorite)
        TR.ouvrir_postes(p, t.lieu.id, "ouvrier", DOCKERS_PAR_GRUE * t.grues)


def installer(p):
    w = p.w; L = p.socle.livre
    if "fioul" not in p.socle.catalogue.par_nom or "kerosene" not in p.socle.catalogue.par_nom:
        raise RuntimeError("logistique : fioul et kerosene viennent du domaine 11 ( energie )")
    lg = Logistique(); p.domaines["logistique"] = lg
    lg.jour_install = p.jour
    for m, nature in MOTIFS.items(): L.declarer_motif(m, nature, "logistique")
    J = p.socle.journal
    J.declarer("escale", "logistique", "individuel", ("navire", "port", "lots", "tonnes", "attente_h"))
    J.declarer("vol_cargo", "logistique", "individuel", ("avion", "de", "vers", "lots", "kg"))
    for t in ("convoi_lance", "convoi_refuse", "lot_expedie", "lot_livre", "lot_annule", "attente_quai_h",
              "subvention_ligne", "magasinage", "soute_importee"):
        J.declarer(t, "logistique", "compte")
    _installer_terminaux(p, lg)
    reg = p.socle.registre
    reg.inscrire("autorites_portuaires", "administrations", _membres_autorites, "caisse", None, "AutoritePortuaire")
    reg.inscrire("entrepots_logistique", "entreprises", _membres_entrepots, None, "stock", None)
    reg.inscrire("navires", "entreprises", _membres_navires, None, "stock", None)
    reg.inscrire("avions", "entreprises", _membres_avions, None, "stock", None)
    for a in lg.autorites.values(): _ouvrir_compte(p, a)
    _installer_transporteurs(p, lg)
    _installer_flotte(p, lg)
    _installer_dockers(p, lg)
    lg.decideur = p.decideur(POINT_LOT)
    w.expedier = RemplaceExpedier(p)
    w.lancer_convoi = RemplaceLancerConvoi(p)
    w.arrivees = RemplaceArrivees(p)
    w.conducteur = RemplaceConducteur(p)
    p.echeance("logistique_appareiller", _appareiller)
    p.echeance("logistique_accoster", _accoster)
    p.echeance("logistique_atterrir", _atterrir)
    p.routine(10 / 60, 50, "logistique", _programmer)
    p.routine(6.5, 50, "logistique", _matin)
    for h in HEURES_DECISION: p.routine(h, 50, "logistique", _decider)
    for h in range(int(HEURES_VOL[0]), int(HEURES_VOL[1]) + 1): p.routine(h + 0.5, 50, "logistique", _vols)
    p.routine(18 + 50 / 60, 100, "logistique", _avant_achats)
    p.routine(19, 60, "logistique", _noter)
    p.routine(23 + 40 / 60, 60, "logistique", _soir)
    _programmer(p)            # les departs d aujourd hui ( la routine de 0 h 10 est passee )
    return lg


# ================================================================== controles ( portes )
def anomalies_transit(p):
    """Ce que les lots ne s expliquent pas : [ ( type, detail ) ].
      detenteur   un entrepot, une cale ou une soute d avion dont le stock d un bien n est pas la somme des lots qu il
                  porte ( soutes de fioul et de kerosene a part ) : une cargaison apparue ou disparue ;
      convoi      un lot en route sans son convoi, ou un convoi qui ne porte pas exactement son lot ;
      parc        un navire ou un avion que le Parc ne compte plus."""
    lg = _lg(p); w = p.w; cat = p.socle.catalogue; out = []
    attendu = {}
    for lot in lg.lots.values():
        if lot.etat in (PREPARATION, QUAI_A, QUAI_B): cle = ("entrepot", lot.ou)
        elif lot.etat == EN_MER: cle = ("avion" if lot.mode == "avion" else "navire", lot.ou)
        else: cle = None
        if cle is not None:
            d = attendu.setdefault(cle, {}); d[lot.bien] = d.get(lot.bien, 0.0) + lot.q
    soutes = ("fioul", "kerosene")
    for genre, liste in (("entrepot", lg.entrepots), ("navire", lg.navires), ("avion", lg.avions)):
        for x in liste:
            a = attendu.get((genre, x.k), {})
            vu = {cat[b].nom: q for b, q in x.stock.items() if cat[b].nom not in soutes or genre == "entrepot"}
            for b in sorted(set(a) | set(vu)):
                if abs(a.get(b, 0.0) - vu.get(b, 0.0)) > 1e-6 * max(1.0, a.get(b, 0.0)):
                    out.append(("detenteur", genre, x.k, b, vu.get(b, 0.0), a.get(b, 0.0)))
    en_route = {c.id: c for c in w.convois}
    for lot in lg.lots.values():
        if lot.etat not in (ROUTE1, ROUTE2): continue
        c = en_route.get(lot.convoi)
        if c is None: out.append(("convoi", lot.id, "absent")); continue
        q = c.cargaison.get(lot.bien, 0.0)
        if abs(q - lot.q) > 1e-6 * max(1.0, lot.q) or len(c.cargaison) != 1:
            out.append(("convoi", lot.id, q, lot.q))
    parc = p.socle.parc
    for x in list(lg.navires) + list(lg.avions):
        if x.objet not in parc.objets: out.append(("parc", x.objet))
    return out


def en_transit(p):
    """{ bien : quantite } en transit : convois du moteur, entrepots, cales, soutes d avion ( sans les soutes )."""
    lg = _lg(p); cat = p.socle.catalogue; out = {}
    for c in p.w.convois:
        for b, q in c.cargaison.items(): out[b] = out.get(b, 0.0) + q
    for liste in (lg.entrepots, lg.navires, lg.avions):
        for x in liste:
            for b, q in x.stock.items():
                n = cat[b].nom
                if liste is not lg.entrepots and n in ("fioul", "kerosene"): continue
                out[n] = out.get(n, 0.0) + q
    return out


# ================================================================== API pour les autres domaines ( 17, 18, 26 )
def envoyer(p, payeur, source, bien, q, origine, destination, recepteur, mode="auto"):
    """Domaines 17, 18, 26 : confier au fret `q` unites de `bien` prises dans `source` ( un Stock du socle ou un
    detenteur a attribut stock ) du lieu `origine` vers le lieu `destination` ( identifiants ). `recepteur` : le nom d une
    fonction declaree par `recevoir_lot` qui fait entrer le lot chez le destinataire ( elle recoit ( p, lot, stock ) et
    doit en deplacer lot.q par le grand livre ). `mode` : route, ferry, caboteur, avion, ou auto ( la route sur une meme
    ile, le premier navire ailleurs ). `payeur` paie tout le fret. Le lieu d origine doit avoir un quai ( un marche, un
    port, un aeroport ). Rend le numero du lot, ou -1."""
    lg = _lg(p); w = p.w
    if recepteur not in lg.recepteurs: raise KeyError(f"recepteur {recepteur!r} non declare ( recevoir_lot )")
    o, d = w.carte.lieux[origine], w.carte.lieux[destination]
    if mode == "auto":
        if o.ile == d.ile: mode = "route"
        else:
            hf = heures_avant_depart(p, lg, o.ile, d.ile, "ferry"); hc = heures_avant_depart(p, lg, o.ile, d.ile, "caboteur")
            mode = "ferry" if hf <= hc else "caboteur"
    if (mode == "route") != (o.ile == d.ile): return -1
    src = source.stock if hasattr(source, "stock") else source
    lot = _nouveau_lot(p, lg, -1, bien, q, mode, origine, destination, src, payeur, None, None, recepteur)
    return lot.id if lot is not None else -1


def recevoir_lot(p, nom, fonction, retour=None):
    """Declare un recepteur de lots ( une fonction de module : picklable ) ; `retour` recoit un lot annule."""
    if getattr(fonction, "__name__", "") == "<lambda>": raise ValueError("une lambda ne se pickle pas")
    lg = _lg(p); lg.recepteurs[nom] = fonction
    if retour is not None: lg.recepteurs["retour:" + nom] = retour


def recevoir_convoi(p, motif, fonction):
    """Domaine 26 : un motif de convoi propre ( ravitaillement d un depot ) et la fonction ( p, convoi ) qui fait entrer sa
    cargaison chez le destinataire, par le grand livre."""
    if getattr(fonction, "__name__", "") == "<lambda>": raise ValueError("une lambda ne se pickle pas")
    _lg(p).recepteurs["convoi:" + motif] = fonction


def lancer_convoi(p, origine, destination, cargaison, payeur, motif, marche_carburant, vendeur=None):
    """Domaines 17, 18, 26 : un convoi routier ( chauffeur a son poste, camion du transporteur, gazole, etat des routes ).
    Rend le convoi ( E1.Convoi ) ou None."""
    r = _lancer(p, origine, destination, cargaison, payeur, motif, marche_carburant, vendeur)
    return r[0] if r is not None else None


def delai_estime_h(p, origine, destination, mode="auto"):
    """Heures estimees d un envoi ( route ; ou attente du prochain depart + traversee + routes aux deux bouts )."""
    lg = _lg(p); w = p.w
    o, d = w.carte.lieux[origine], w.carte.lieux[destination]
    if o.ile == d.ile: return sum(duree_convoi_pas(p, o, d)[:1]) / PAS_H
    mode = "ferry" if mode == "auto" else mode
    ta, tb = (lg.terminaux[lg.aeroport_de[o.ile]], lg.terminaux[lg.aeroport_de[d.ile]]) if mode == "avion" else \
        (lg.terminaux[lg.port_de[o.ile]], lg.terminaux[lg.port_de[d.ile]])
    r1 = duree_convoi_pas(p, o, ta.lieu)[0] / PAS_H if o is not ta.lieu else 0.0
    r2 = duree_convoi_pas(p, tb.lieu, d)[0] / PAS_H if d is not tb.lieu else 0.0
    if mode == "avion": return r1 + 1.0 + KM_ENTRE_ILES / AVION[7] + BLOC_SUPPLEMENT_H + r2
    li = _ligne_vers(lg, o.ile, d.ile, mode)
    if li is None: return math.inf
    return r1 + heures_avant_depart(p, lg, o.ile, d.ile, mode) + li.km / (NAVIRES[lg.navires[li.navire].modele][5] * KMH_PAR_NOEUD) + r2


def lots(p, etat=None):
    """Les lots actifs : [ ( numero, bien, quantite, mode, etat, origine, destination ) ]."""
    return [(x.id, x.bien, x.q, x.mode, ETATS[x.etat], x.origine, x.dest) for x in _lg(p).lots.values()
            if etat is None or ETATS[x.etat] == etat]


def ports(p):
    """Domaines 18, 26 : { ile : ( lieu, quais, occupes, t/h ferry, t/h caboteur, attente cumulee h, escales ) }."""
    lg = _lg(p)
    return {t.ile: (t.lieu.id, t.quais, t.occupes, t.t_h("ferry"), t.t_h("caboteur"), t.attente_h, t.escales)
            for t in lg.terminaux if t.genre == "port"}


def regler_port(p, ile, facteur=None, quais=None):
    """Scenario ( portes, domaine 18 : un seisme ; 27 : un sabotage ) : la capacite de manutention du port d une ile
    multipliee par `facteur`, son nombre de postes a quai fixe."""
    lg = _lg(p); t = lg.terminaux[lg.port_de[ile]]
    if facteur is not None:
        if not 0.0 < facteur <= 10.0: raise ValueError(f"facteur hors ]0 ; 10] : {facteur!r}")
        t.facteur = float(facteur)
    if quais is not None:
        if not 1 <= int(quais) <= 50: raise ValueError(f"quais hors [1 ; 50] : {quais!r}")
        t.quais = int(quais)


def fermer_la_mer(p, fermee=True):
    """Domaines 18, 26, 27 : plus aucun depart de navire ni d avion ( tempete, blocus ) ; les lots attendent a quai."""
    _lg(p).mer_ouverte = not fermee


def navires(p):
    """Domaine 26 ( requisition ) : [ ( numero, modele, ligne, terminal ou -1 en mer, lots a bord, charge utile t ) ]."""
    lg = _lg(p)
    return [(n.k, n.modele, n.ligne, n.terminal, len(n.a_bord), NAVIRES[n.modele][7]) for n in lg.navires]


def flotte_routiere(p):
    """Domaines 18, 26 : { capitale : { modele : ( nombre, libres maintenant ) } }."""
    lg = _lg(p); pas = p.w.pas; out = {}
    for tr in lg.transporteurs:
        d = out.setdefault(tr.marche_id, {})
        for nom, libre in tr.vehicules:
            n, l = d.get(nom, (0, 0)); d[nom] = (n + 1, l + (1 if libre <= pas else 0))
    return out


def a_incarner(p):
    """Le pont : les convois en route, chacun avec sa DESTINATION ( a poser avant l ordre de marche ) et un decalage de
    depart propre ( domaine 14, `emplacements` : deux vehicules crees au meme point se detruisent )."""
    lg = _lg(p); w = p.w; out = []
    par_origine = {}
    for c in w.convois:
        info = lg.convois.get(c.id)
        if info is None: continue
        tr = lg.transporteurs[info[0]]
        if info[1] >= len(tr.vehicules): continue
        nom = tr.vehicules[info[1]][0]
        par_origine.setdefault(c.origine.id, []).append((c, nom))
    for oid, lst in par_origine.items():
        dec = T14.emplacements(len(lst))
        for (c, nom), (dx, dy) in zip(lst, dec):
            out.append({"convoi": c.id, "classname": T14.caracteristiques(nom).arma, "destination": c.destination.pos,
                        "depart": (c.origine.pos[0] + dx, c.origine.pos[1] + dy), "chauffeur": c.conducteur})
    return out


def statistiques(p):
    """Les compteurs du domaine et les transits moyens ( heures ) par mode."""
    lg = _lg(p)
    tr = {m: (len(v), float(np.mean(v)) if v else 0.0) for m, v in lg.transits.items()}
    return dict(lg.stats), tr
