"""DOMAINE 12 - SERVICES PUBLICS : EAU POTABLE, ASSAINISSEMENT, DECHETS, ROUTES, ECLAIRAGE PUBLIC.

FICHE
1. Classes. Les detenteurs : Commune ( le deme d une ile, sur le modele grec de Kallikratis : une ile egeenne = un
   deme ; caisse, Stock du socle pour les materiaux des chantiers, camions-bennes au Parc, credit d entretien des
   routes ), RegieEau ( la DEYA de l ile : eau et assainissement, caisse ), SystemeEau ( un captage, une station de
   traitement et un reservoir par bassin du territoire : Stock d eau potable ), PointDeCollecte ( les conteneurs d un
   lieu habite : Stock de dechets ), Decharge ( la decharge controlee de l ile, XYTA : Stock de dechets enfouis ). Les
   tableaux : ReseauRoutier ( les troncons : un par lieu non chef-lieu, vers son voisin le plus proche sur le chemin de
   son marche - un arbre enracine aux capitales -, plus les liaisons entre capitales d une meme ile ; etat de 0 a 1,
   fermeture, trafic, usure ), EauParLieu ( demande, part servie, jours sans eau, qualite a la sortie : E. coli,
   turbidite, indice chimique ). Chantier ( une journee d equipe dont la note attend ), ContexteEntretien, QualiteEau
   ( ce que la medecine lit ), ServicesPublics ( l etat du domaine ). Colonnes par menage : sp_eau_du ( facture qui
   court ), sp_eau_arrieres, sp_eau_m3 ( m3 factures depuis l installation ).
2. Invariants et ce que le domaine detient. EAU POTABLE ( bien `eau_potable`, m3 ) : elle ne nait que par
   `potabilisation`, a partir d eau brute prelevee au territoire ( `prelever`, usage domestique repris ) : produite =
   0,97 x captee ( 3 % d eau de lavage des filtres ) ; puis produite = consommee ( abonnes, y compris les pertes
   apparentes ) + perdue ( fuites, pertes reelles ) + incendie + variation des reservoirs ( porte test_bilan_eau ).
   DECHETS ( bien `dechets`, tonnes ) : produits = collectes + accumulation aux points de collecte ; collectes =
   recycles ( consommes par le tri ) + enfouis ( stock de la decharge ) ( porte test_bilan_dechets ). Argent : tout
   par le grand livre sous des motifs declares ; le domaine DETIENT les caisses des communes et des regies ( familles
   `communes` et `regies_eau` ), les biens des systemes d eau, des points de collecte, des decharges et des communes
   ( familles `reseaux_eau`, `points_collecte`, `decharges` ). Objets : les camions-bennes, cohorte au Parc
   ( source initial ).
3. Decision `entretenir_route` ( chaque equipe routiere, chaque matin a 7 h ) : quel troncon reparer aujourd hui,
   par CRITERE ( la lecon du domaine 6 : des actions qui designent un indice de lot au hasard sont interchangeables ) :
   le plus degrade, le plus frequente, le plus proche du depot, au hasard. Traits ( inspections et compteurs de
   trafic ) : etat, trafic et longueur des troncons que designent les trois premiers criteres, et s ils sont fermes ;
   part fermee du reseau de l ile, pluie des 7 derniers jours, distance du plus proche. Note ( horizon 7 jours ) : le
   logarithme de ( 1 + le service rendu par CE chantier sur ces 7 jours, en vehicules-km ) : chaque jour, trafic du
   troncon x longueur x ( facteur de vitesse avec la reparation - sans elle, 0 si le troncon serait ferme ; plus le
   facteur d accident evite ), le contrefactuel etant l etat du troncon moins le gain de CE chantier. Logarithme :
   rouvrir une route coupee rend cent fois plus qu un rapiecage, la moyenne brute serait une loterie ( domaine 6 ).
   Regle : le plus degrade. Temoin : au hasard.
   Sans point de decision ( regles ) : les coupures d eau tournantes par quartier ( les lieux qui ont le plus manque
   sur 7 jours sont servis d abord ), la tournee des camions-bennes ( les points les plus pleins d abord ).
4. Evenements. Individuels : route_fermee, route_rouverte, coupure_eau, greve_collecte, decharge_pleine. Comptes :
   eau_potable_m3, eau_non_facturee_m3, eaux_usees_non_traitees_m3, dechets_collectes_t, dechets_recycles_t,
   chantier_routier, convoi_ralenti, facture_eau_impayee, collecte_impossible.
5. Liens. Territoire ( 8 ) : reprend l usage domestique, preleve, rejette les nitrates des eaux usees, lit la meteo
   ( pluie, gel ), les crues et les seismes ( intensites par lieu ), la pollution de l eau brute. Etat ( 6 ) : taxe
   locale ( `taxe_locale`, `percevoir` : proprete et eclairage, payee a l Etat ), TVA de l eau ( `percevoir_tva`, taux
   reduit ), dotation des communes ( KAP ) et subvention des regies par le Tresor. Banques ( 2 ) : `ouvrir_compte`.
   Energie ( 11, si installe ) : un contrat de pompage et d epuration par systeme ( `abonner`, prioritaire ; `servi`
   dit la part des heures alimentees la veille, qui borne le pompage et l epuration ), l eclairage public paye par la
   commune ( `reprendre_eclairage` ). Industrie ( 10, si installe ) : ciment et acier des chantiers qui rouvrent une
   route coupee ( `commander`, `livrer` ). Agenda ( 5, si installe ) : les trajets en vehicule du plan du jour font le
   trafic des voitures ; sans lui, un trajet aller-retour par habitant vers son marche ( a calibrer ). Moteur E1 : lit
   les convois ( trafic lourd ) ; brule le carburant des camions et des engins au marche ( comme Monde.lancer_convoi ) ;
   la main-d oeuvre des tournees et des chantiers est achetee au secteur marchand de la capitale ( sous-traitance :
   le moteur n a ni eboueurs ni cantonniers ; a reprendre par le domaine 4 ). PONTS DE DONNEES, rien n est remplace :
   un troncon ferme met les lieux qu il dessert dans `w.coupures` ( lu par Monde.aube ) et dans `w.routes_temporaires`
   ( lu par Monde.lancer_convoi ) ; tant que la logistique ( 15 ) n est pas installee, un convoi lance allonge son
   `arrivee` selon l etat des troncons traverses ( et le chauffeur ses heures ). Donne ( API en fin de fichier ) :
   medecine ( 16 ) `qualite_eau`, `facteur_gastro` ; transport ( 14 ) `etat_route`, `facteur_accident`, `troncons` ;
   logistique ( 15 ) `facteur_vitesse`, `duree_trajet_pas`, `route_ouverte` ; securite civile ( 18 ) `borne_incendie`,
   `prelever_incendie`, `routes_coupees`, `lieux_isoles` ; travail ( 4 ) `greve_collecte` ; tous `insalubrite`,
   `passer` ( un trafic lourd d un autre domaine ), `programme_urgence`, bilans.
6. Portes : tests_d12_services_publics.py.
7. Arma. Camion-benne : C_Truck_02_box_F ( Zamak, jeu de base ) faute d une benne a ordures au jeu de base ;
   conteneurs : Land_GarbageContainer_closed_F ; chateau d eau : Land_WaterTower_01_F ; eclairage : Land_LampStreet_F.
   arma_preuve = None partout : rien n a ete vu vivre en jeu.
8. Cout. Par jour : une lecture des menages ( recensement par lieu et facture vectorisee ), le reste par systeme d eau,
   par lieu, par troncon et par convoi ( chemins en cache ) ; les trajets de l agenda agreges par paire de lieux. A
   l installation, l arbre des routes : quadratique dans le nombre de lieux d une ile ( ~ 70 a Altis ). Mesure du 24/09
   ( test_cout, 10 000 habitants ) : 11 ms par jour de routines propres, 1,1 us par habitant, < 1 % d une journee du
   pays ; lineaire en menages ( recensement, factures ) : ~ 1 s par jour a 1 million d habitants."""
import math
from collections import deque
import numpy as np
from .. import config as C
from ..socle import decision as D
from . import pays as P, d02_banques as BQ, d06_etat as ET, d08_territoire as TER

EPS = 1e-9
JOURS_AN = 365.0
EUROS_PAR_DRACHME = P.EUROS_PAR_DRACHME
DR = 1.0 / EUROS_PAR_DRACHME          # un euro, en drachmes
HABITABLES = ("capitale", "ville", "village")

# ================================================================== l eau potable
# Consommation reelle des abonnes : ~ 150 a 200 litres par habitant et par jour en Grece ( EYDAP, Athenes ~ 160 l ;
# EurEau 2021, Grece ~ 150 l ; les iles touristiques davantage ) : 165 l, a calibrer par ile.
CONSO_M3_HAB_J = 0.165
BANDE_CONSO = (0.150, 0.200)
# Eau non facturee : 35 a 40 % dans les regies grecques ( Kanakoudis et Tsitsifli 2010, DEYA : 30 a 50 % ; EurEau
# 2021 ) : pertes reelles ( fuites ) 25 % du volume injecte, pertes apparentes ( compteurs, branchements illicites,
# usages publics non factures ) 10 % - a calibrer.
PERTES_REELLES = 0.25
PERTES_APPARENTES = 0.10
PERTE_TRAITEMENT = 0.03               # eau de lavage des filtres ( 2 a 5 %, a calibrer )
RESERVOIR_J = 1.0                     # un reservoir tient un jour de distribution ( norme grecque usuelle, a calibrer )
SEUIL_SANS_EAU = 0.5                  # un lieu servi a moins de la moitie de sa demande est un lieu sans eau ce jour-la
# Energie : pompage en nappe et traitement ~ 0,6 kWh par m3 injecte ; epuration par boues activees ~ 0,45 kWh par m3
# ( 0,3 a 0,6 : ordres de grandeur europeens, a calibrer ).
KWH_M3_EAU, KWH_M3_EPURATION = 0.6, 0.45
# Tarifs d une DEYA grecque ( ordre de grandeur : eau 0,5 a 1,5 euro le m3 par tranches ; redevance d assainissement
# 50 a 80 % de l eau ; a calibrer ) ; TVA de l eau au taux reduit ( categorie du catalogue, domaine 6 ).
TARIF_EAU = 0.90 * DR
TARIF_ASSAINISSEMENT = 0.55 * DR
JOURS_FACTURE = 30                    # les DEYA facturent au trimestre ou au quadrimestre : 30 jours ici, a calibrer
# Exploitation ( personnel, entretien, chlore ) sous-traitee : 0,45 euro par m3 injecte, 0,25 par m3 epure ( a calibrer ).
EXPLOITATION_M3 = 0.45 * DR
EPURATION_M3 = 0.25 * DR
PRIX_EAU_MONDE = 7.0 * DR             # le m3 livre par navire-citerne aux iles grecques ( 5 a 10 euros, a calibrer )
# Qualite. Directive ( UE ) 2020/2184 : E. coli 0 par 100 ml ; turbidite 1 NTU en sortie de traitement ; nitrates
# 50 mg/l. Eau brute de nappe ~ 5 E. coli / 100 ml ( a calibrer ) ; chloration : 3 log d abattement ( 99,9 % ) si la
# turbidite reste sous 5 NTU, 1 log au-dela ( les particules protegent les germes : OMS 2017 ), rien sans courant.
ECOLI_BRUT = 5.0
K_FECAL = 50.0                        # E. coli brute x ( 1 + 50 x part des eaux usees non traitees du bassin ), a calibrer
FUITE_FOSSE = 0.05                    # une fosse septique pese 5 % d un egout non traite ( a calibrer )
ECOLI_CRUE = 20.0                     # facteur sur l eau brute pendant une crue du bassin ( ruissellement, a calibrer )
TURB_BRUTE, TURB_PLUIE, TURB_CRUE = 0.3, 3.0, 10.0   # NTU : nappe, jour de plus de 30 mm, par degre de crue ( a calibrer )
LOG_CHLORE, LOG_CHLORE_TROUBLE, TURB_LIMITE_DESINF = 3.0, 1.0, 5.0
ABATTEMENT_TURB = 0.8                 # filtration rapide : 80 % de la turbidite ( a calibrer )
ECOLI_INTRUSION = 5.0                 # E. coli / 100 ml entrees par depression d un reseau intermittent, par part coupee
ENLEVEMENT = {"nitrates": 0.0, "hydrocarbures": 0.5, "plomb": 0.3}   # traitement classique ( a calibrer )
# Assainissement : rejet de 80 % de l eau consommee ; 12 g d azote par habitant et par jour ( 10 a 13 ), enleve a 70 %
# par une station a traitement de l azote, a 30 % par une fosse ( qui en laisse partir 30 % vers la nappe ) ; nitrate =
# 4,43 x azote. Raccordement : capitales et villes a une station ( Grece : ~ 90 % de la population raccordee, AEE ) ;
# villages en fosses septiques ( a calibrer ).
RETOUR_EGOUT = 0.8
AZOTE_KG_HAB_J = 0.012
ENLEVEMENT_AZOTE_STEP = 0.7
FUITE_AZOTE_FOSSE = 0.3
NO3_PAR_N = 4.43
RACCORDES = ("capitale", "ville")
# Incendie : une borne debite 60 m3/h pendant 2 h ( ordre de grandeur europeen de la defense incendie, a calibrer ).
BORNE_M3_H, BORNE_H = 60.0, 2.0

# ================================================================== les dechets
# Dechets municipaux : 524 kg par habitant et par an en Grece ( Eurostat env_wasmun, 2021 ) = 1,44 kg par jour ;
# recyclage et compost ~ 21 % ( Eurostat, taux de recyclage des dechets municipaux, Grece ~ 17 a 21 % selon l annee ),
# le reste enfoui ( ~ 80 % ). A verifier.
DECHETS_T_HAB_J = 0.524 / JOURS_AN
PART_RECYCLEE = 0.21
PRIX_DECHETS = 20.0 * DR              # valeur des matieres recyclables triees, euros par tonne ( a calibrer )
CAMION_T = 10.0                       # charge d une benne tasseuse de 26 t ( 8 a 12 t de dechets tasses )
HAB_PAR_CAMION = 8000.0               # une benne pour 5 000 a 10 000 habitants ( a calibrer )
TOURNEE_H, ARRET_H, VITESSE_TOURNEE_KMH = 8.0, 0.25, 25.0
SEUIL_COLLECTE_J = 2.0                # un point n est visite qu au-dela de 2 jours de production ( villages : 2 a 3 fois par semaine )
EQUIPAGE_BENNE = 3                    # chauffeur et deux ripeurs
CARBURANT_BENNE_U_KM = 0.06           # 60 l aux 100 km ( unites de 10 l du moteur ), a calibrer
FRAIS_BENNE_KM = 0.5 * DR             # entretien et amortissement, euros par km ( a calibrer )
SALAIRE_SOUS_TRAITANT_H = 8.0         # drachmes de l heure : l ouvrier du moteur ( population.SALAIRE_HORAIRE )
DECHARGE_ANS = 20.0                   # une decharge est dimensionnee pour 20 ans de dechets enfouis ( a calibrer )
SURFACE_LOGEMENT_M2 = 80.0            # residence principale grecque moyenne ~ 80 m2 ( ELSTAT, a calibrer ; domaine 13 le dira )
JOURS_TAXE = 30
SEUIL_INSALUBRE_J = 3.0               # au-dela de 3 jours de dechets, mouches et rats ( a calibrer )

# ================================================================== les routes
# Etat d un troncon : 1 neuf, 0 detruit. Degradation journaliere ( a calibrer, forme HDM-4 simplifiee ) : le vieillissement
# ( une chaussee non entretenue perd ~ 0,7 en 15 a 20 ans ), plus vite quand elle est deja abimee ; la pluie qui entre
# dans les fissures ( nids-de-poule ) ; le gel ; le trafic lourd en essieux equivalents ( loi de la 4e puissance,
# AASHO : une route rurale peu circulee est dimensionnee pour ~ 2 x 10^5 ESAL ).
VIEILLISSEMENT_AN = 0.03
ACCELERATION_USURE = 1.5
K_PLUIE = 0.0005                      # par mm de pluie, x ( 1 - etat )
K_GEL = 0.002                         # par jour de gel, x ( 1 - etat )
K_ESAL = 0.7 / 2.0e5                  # par essieu equivalent de 13 t, rapporte au km ( un passage use tout le troncon )
ESAL_CHARGE, ESAL_VIDE, ESAL_VOITURE = 1.0, 0.3, 0.0004   # par passage ( a calibrer )
S_FERME, S_ROUVRE = 0.10, 0.25        # sous 0,10 la route est fermee ; il faut 0,25 pour la rouvrir
ETAT_INITIAL = (0.45, 0.95)           # routes rurales grecques : etat tire uniformement ( a calibrer )
# Vitesse relative ( 1 au-dessus de 0,6 ; 0,45 a 0,10 ) et risque d accident relatif ( 1 + 0,8 ( 1 - etat )^2 ) : la
# vitesse libre baisse avec l uni ( IRI, HDM-4 ) et les nids-de-poule ; le risque croit avec l IRI ( Tighe et al. 2000,
# Chan et al. 2010 : ordres de grandeur ) - a calibrer.
S_VITESSE, U_MIN = 0.6, 0.45
K_ACCIDENT = 0.8
# Seismes et crues : probabilite de coupure d un troncon ( eboulement, pont, remblai ) - fragilites a calibrer ( HAZUS ).
COUPURE_MMI = {7: 0.05, 8: 0.20, 9: 0.50, 10: 0.80}
DEGAT_MMI = 0.10                      # etat perdu par degre d intensite au-dela de 6
COUPURE_CRUE, DEGAT_CRUE = 0.05, 0.05 # par degre de gravite de la crue du bassin
# Equipes : une journee d equipe remet en etat 0,5 km de chaussee ( colmatage, rechargement, a calibrer ) ; 4 ouvriers,
# 5 t d enrobes ( ~ 70 euros la tonne ), 30 l de gazole. Rouvrir une route coupee demande aussi du beton : 4 t de
# ciment et 0,4 t d acier ( a calibrer ), fournis par l industrie si elle est la ( sinon par l entrepreneur ).
KM_EQUIPE_J = 0.5
OUVRIERS_EQUIPE = 4
ENROBES_T, PRIX_ENROBES_T = 5.0, 70.0 * DR
CARBURANT_EQUIPE_U = 3.0
CIMENT_T, ACIER_T = 4.0, 0.4
VITESSE_EQUIPE_KMH = 40.0
# Budget d entretien des routes : ~ 60 euros par habitant et par an ( routes locales et regionales ; a calibrer ).
BUDGET_ROUTES_HAB_AN = 60.0 * DR
EQUIPES_MAX_PAR_CAPITALE = 2
TRAFIC_VOITURE_HAB_J = 1.0            # sans l agenda : un aller-retour en vehicule par habitant vers son marche ( a calibrer )
EMA_TRAFIC = 1.0 / 7.0

# ================================================================== la decision
CRITERES = ("plus_degrade", "plus_frequente", "plus_proche", "au_hasard")
AU_HASARD = CRITERES.index("au_hasard")
HORIZON_ENTRETIEN = 7
TRAFIC_NORME = 200.0                  # vehicules par jour : le trait vaut 1
SEUIL_TRAVAUX = 0.95                  # au-dela, rien a reparer
# Finances : chaque soir le Tresor remonte la caisse d une commune ou d une regie a 10 jours de depenses ( KAP ; a
# calibrer ) ; au-dela de 60 jours, l excedent d une regie retourne au Tresor.
JOURS_COUSSIN, JOURS_EXCEDENT = 10, 60


# ================================================================== les detenteurs
class Commune:
    """Le deme d une ile : collecte des dechets, eclairage public, entretien des routes. Detient une caisse et un Stock
    ( ciment, acier des chantiers ). credit_routes : drachmes du budget d entretien pas encore engagees."""
    __slots__ = ("id", "ile", "chef_lieu", "caisse", "stock", "camions", "greve_jusqu", "credit_routes", "urgence",
                 "urgence_jusqu", "cout_ema", "depense_jour", "pop")

    def __init__(self, id, ile, chef_lieu, stock):
        self.id, self.ile, self.chef_lieu, self.stock = id, ile, chef_lieu, stock
        self.caisse = 0.0
        self.camions = 1
        self.greve_jusqu = -1
        self.credit_routes = 0.0
        self.urgence = 0; self.urgence_jusqu = -1
        self.cout_ema = 0.0; self.depense_jour = 0.0
        self.pop = 0.0


class RegieEau:
    """La regie de l eau et de l assainissement d une ile ( DEYA ). Detient une caisse."""
    __slots__ = ("id", "ile", "caisse", "cout_ema", "depense_jour")

    def __init__(self, id, ile):
        self.id, self.ile = id, ile
        self.caisse = 0.0; self.cout_ema = 0.0; self.depense_jour = 0.0


class SystemeEau:
    """Un captage, une station de traitement, un reservoir : un par bassin du territoire. Stock d eau potable.
      lieux        indices ( territoire ) des lieux habites qu il dessert
      capacite     m3 du reservoir ; i_nom : m3 injectes par jour au recensement d installation
      f_elec       part de la journee d hier ou le pompage etait alimente ( 1 sans le domaine 11 )"""
    __slots__ = ("id", "bassin", "ile", "chef_lieu", "stock", "lieux", "capacite", "i_nom", "contrat", "f_elec",
                 "f_step", "injecte_jour", "kwh_nom")

    def __init__(self, id, bassin, ile, chef_lieu, stock, lieux):
        self.id, self.bassin, self.ile, self.chef_lieu, self.stock, self.lieux = id, bassin, ile, chef_lieu, stock, lieux
        self.capacite = self.i_nom = self.kwh_nom = 0.0
        self.contrat = None
        self.f_elec = 1.0; self.f_step = 1.0; self.injecte_jour = 0.0


class PointDeCollecte:
    """Les conteneurs d un lieu habite. Stock de dechets."""
    __slots__ = ("lieu", "ile", "stock", "dernier")

    def __init__(self, lieu, ile, stock): self.lieu, self.ile, self.stock, self.dernier = lieu, ile, stock, -1


class Decharge:
    """La decharge controlee d une ile. Stock des dechets enfouis ; capacite en tonnes."""
    __slots__ = ("ile", "lieu", "stock", "capacite_t", "pleine")

    def __init__(self, ile, lieu, stock, capacite_t):
        self.ile, self.lieu, self.stock, self.capacite_t, self.pleine = ile, lieu, stock, capacite_t, False


class ReseauRoutier:
    """Les troncons, en tableaux. Troncon k : de `a` ( lieu desservi, ou capitale ) a `b` ( son voisin vers le marche, ou
    l autre capitale ) ; type 0 desserte, 1 liaison entre capitales. `montee[l]` : les troncons du lieu l a sa capitale ;
    `dessous[k]` : les lieux que le troncon k relie a leur capitale ( isoles s il ferme )."""
    __slots__ = ("a", "b", "ile", "type", "longueur", "etat", "ferme", "trafic_ref", "veh_jour", "esal_jour", "pris",
                 "racine", "montee", "dessous", "capitales", "chemins", "liaisons_ok", "km_base", "c_climat", "c_trafic",
                 "c_choc", "c_repare", "n_fermetures")


class EauParLieu:
    """Par lieu du territoire ( tableaux ) : habitants, raccordement, part servie du jour, historique des manques sur
    7 jours, jours sans eau cumules, qualite du jour a la sortie."""
    __slots__ = ("hab", "raccorde", "phi", "manque7", "jours_sans_eau", "ecoli", "turb", "chim", "nitrates")


class Chantier:
    __slots__ = ("cle", "troncon", "gain", "ferme_avant", "action", "jour", "total", "jours")

    def __init__(self, cle, troncon, gain, ferme_avant, action, jour):
        self.cle, self.troncon, self.gain, self.ferme_avant, self.action, self.jour = cle, troncon, gain, ferme_avant, action, jour
        self.total = 0.0; self.jours = 0


class ContexteEntretien:
    __slots__ = ("traits", "cibles")

    def __init__(self, traits, cibles): self.traits, self.cibles = traits, cibles


class QualiteEau:
    """La qualite de l eau du robinet d un lieu, aujourd hui : ce que la medecine lit.
      ecoli ( UFC / 100 ml, limite 0 ), turbidite ( NTU, limite 1 ), chimique ( pire polluant apres traitement sur sa
      limite ), nitrates ( mg/l ), part_servie ( du jour ), manque_7j ( part de la demande non servie sur 7 jours ),
      insalubrite ( jours de dechets non collectes au lieu )"""
    __slots__ = ("lieu", "ecoli", "turbidite", "chimique", "nitrates", "part_servie", "manque_7j", "insalubrite")

    def __init__(self, **v):
        for k in self.__slots__: setattr(self, k, v[k])


class ServicesPublics:
    __slots__ = ("communes", "regies", "systemes", "points", "decharges", "routes", "eau", "commune_ile", "regie_ile",
                 "systeme_lieu", "point_lieu", "decharge_ile", "habitables", "decideur", "chantiers", "prochain_chantier",
                 "notes", "vus_convois", "contrats", "eau_id", "dechets_id", "modele_benne", "c_capte", "base_domestique",
                 "c_collecte", "c_recycle", "c_incendie", "c_hab_jours", "c_consomme_hab", "c_injecte", "c_facture_m3",
                 "mg_lieu", "mg_viv", "pluie7", "coupures_e1", "c_ralentis", "t_racine_m3", "pont_convois")


# ================================================================== la decision : entretenir une route
def _observer_entretien(ctx): return ctx.traits


def _regle_entretien(x, ctx): return 0


def _temoin_entretien(x, ctx, rng): return AU_HASARD


def _traits_entretien():
    t = []
    for c in CRITERES[:3]:
        t += [(f"etat_{c}", f"inspection du troncon que designe le critere {c} : son etat de 0 a 1"),
              (f"trafic_{c}", f"compteur de trafic de ce troncon : vehicules par jour ( moyenne 7 j ) sur {TRAFIC_NORME:.0f}"),
              (f"longueur_{c}", "longueur du troncon sur 10 km"),
              (f"ferme_{c}", "le troncon est ferme a la circulation ( arrete du deme )")]
    t += [("part_fermee", "part des troncons de l ile fermes ( registre des arretes )"),
          ("pluie_7j", "pluviometre de l ile : pluie des 7 derniers jours sur 70 mm"),
          ("distance_proche", "km du depot au troncon le plus proche a reparer, sur 20")]
    return tuple(t)


POINT_ENTRETIEN = D.PointDeDecision(
    "entretenir_route", "services_publics",
    traits=_traits_entretien(), actions=CRITERES,
    observer=_observer_entretien, regle=_regle_entretien, temoin=_temoin_entretien,
    note=("le logarithme de 1 + le service que CE chantier rend sur les 7 jours qui suivent, en vehicules-km par jour : "
          "trafic du troncon x longueur x ( vitesse relative avec la reparation - sans elle, 0 si le troncon serait "
          "ferme ; + risque d accident evite )"),
    horizon_j=HORIZON_ENTRETIEN)


# ================================================================== lois pures des routes
def vitesse_relative(etat, ferme=False):
    """La vitesse relative d un troncon ( 0 s il est ferme )."""
    s = np.asarray(etat, float)
    u = np.where(s >= S_VITESSE, 1.0, U_MIN + (1.0 - U_MIN) * np.clip((s - S_FERME) / (S_VITESSE - S_FERME), 0.0, 1.0))
    u = np.where(np.asarray(ferme, bool), 0.0, u)
    return float(u) if u.ndim == 0 else u


def risque_accident(etat):
    s = np.asarray(etat, float)
    r = 1.0 + K_ACCIDENT * (1.0 - np.clip(s, 0.0, 1.0)) ** 2
    return float(r) if r.ndim == 0 else r


def degradation_jour(etat, pluie_mm, gel, esal_km):
    """L etat perdu en un jour : vieillissement accelere par l usure, pluie, gel, trafic lourd ( ESAL par km )."""
    s = np.asarray(etat, float)
    v = VIEILLISSEMENT_AN / JOURS_AN * (1.0 + ACCELERATION_USURE * (1.0 - s))
    return v + (K_PLUIE * pluie_mm + K_GEL * gel) * (1.0 - s) + K_ESAL * esal_km


def service_chantier(trafic, longueur, etat, ferme, gain, ferme_avant):
    """Le service rendu en un jour par un chantier : vehicules-km a vitesse, plus le risque d accident evite, par rapport
    au meme troncon sans ce chantier ( son etat moins le gain )."""
    cf = max(0.0, etat - gain)
    ferme_cf = cf < S_FERME or (ferme_avant and cf < S_ROUVRE)
    du = vitesse_relative(etat, ferme) - vitesse_relative(cf, ferme_cf)
    dr = risque_accident(cf) - risque_accident(etat)
    return max(0.0, trafic * longueur * (du + dr))


# ================================================================== outils
def _sp(p): return p.domaine("services_publics")


def _membres_communes(w): return w.pays.domaines["services_publics"].communes
def _membres_regies(w): return w.pays.domaines["services_publics"].regies
def _membres_systemes(w): return w.pays.domaines["services_publics"].systemes
def _membres_points(w): return w.pays.domaines["services_publics"].points
def _membres_decharges(w): return w.pays.domaines["services_publics"].decharges


def _lieu(p, k): return p.w.carte.lieux[p.domaine("territoire").lieux[k]]


def _marche_de(p, ile):
    c = _sp(p).communes[_sp(p).commune_ile[ile]]
    return p.w.marches[p.w.carte.lieux[c.chef_lieu].marche.id]


def _depenser(p, payeur, marche, montant, motif):
    paye = p.socle.livre.transferer(payeur, marche, montant, motif)
    payeur.depense_jour += paye
    return paye


def _bruler_carburant(p, payeur, marche, q, motif):
    """Achete et brule `q` unites de gazole au marche ( comme Monde.lancer_convoi ). Rend faux si le marche n en a pas
    ou si le payeur ne peut pas payer."""
    if q <= 0: return True
    if marche.stocks["carburant"] < q or payeur.caisse < q * marche.prix["carburant"]: return False
    _depenser(p, payeur, marche, q * marche.prix["carburant"], motif)
    marche.stocks["carburant"] -= q
    p.socle.livre.flux["brule"]["carburant"] += q
    marche.demande["carburant"] += q
    return True


# ================================================================== le recensement ( 4 h 50 )
def _recenser(p):
    """Les habitants vivants de chaque lieu, et de chaque menage son lieu : une passe sur les menages par jour."""
    S = _sp(p); T = p.domaine("territoire"); w = p.w
    n = len(w.menages)
    lieu = np.full(n, -1, np.int64); viv = np.zeros(n)
    for i, mg in enumerate(w.menages):
        if mg.domicile is None: continue
        v = sum(1 for x in mg.membres if x.vivant)
        if v == 0: continue
        k = T.index_lieu.get(mg.domicile.id)
        if k is None: continue
        lieu[i] = k; viv[i] = v
    S.mg_lieu, S.mg_viv = lieu, viv
    hab = np.zeros(len(T.lieux))
    ok = lieu >= 0
    np.add.at(hab, lieu[ok], viv[ok])
    S.eau.hab = hab
    for c in S.communes: c.pop = float(hab[T.lieu_ile == T.iles.index(c.ile)].sum())


# ================================================================== l eau ( 5 h )
def _eau(p):
    S = _sp(p); T = p.domaine("territoire"); E = S.eau; L = p.socle.livre; B = T.bassins
    eau = S.eau_id
    besoin_l = E.hab * CONSO_M3_HAB_J / (1.0 - PERTES_REELLES)          # m3 a injecter par lieu
    crues = {}
    for c in TER.catastrophes_en_cours(p, type_="inondation"): crues[c.lieu] = max(crues.get(c.lieu, 0), c.gravite)
    m = T.meteo
    for sy in S.systemes:
        lieux = sy.lieux
        besoin = float(besoin_l[lieux].sum())
        r = S.regies[S.regie_ile[sy.ile]]
        # 1. le pompage et le traitement : remplir le reservoir, borne par le courant d hier
        voulu = max(0.0, besoin + sy.capacite - sy.stock[eau]) * sy.f_elec
        if voulu > EPS:
            brut = TER.prelever(p, sy.chef_lieu, voulu / (1.0 - PERTE_TRAITEMENT), "domestique")
            S.c_capte += brut
            if brut > EPS: L.produire(sy.stock, eau, brut * (1.0 - PERTE_TRAITEMENT), "potabilisation")
        # 2. la distribution : les lieux qui ont le plus manque sur 7 jours d abord ( coupures tournantes )
        dispo = sy.stock[eau]
        injecte = 0.0
        ordre = sorted(lieux.tolist(), key=lambda k: (-float(E.manque7[k].sum()), k))
        for k in ordre:
            b = float(besoin_l[k])
            x = min(b, dispo - injecte)
            E.phi[k] = x / b if b > EPS else 1.0
            injecte += x
        sy.injecte_jour = injecte
        if injecte > EPS:
            perdu = L.perdre(sy.stock, eau, injecte * PERTES_REELLES, "fuites_reseau")
            L.consommer(sy.stock, eau, injecte - perdu, "consommation_eau")
            p.compter("eau_potable_m3", injecte - perdu)
            p.compter("eau_non_facturee_m3", injecte * (PERTES_REELLES + PERTES_APPARENTES))
            _depenser(p, r, _marche_de(p, sy.ile), injecte * EXPLOITATION_M3, "exploitation_eau")
        for k in lieux.tolist():
            if E.hab[k] > 0 and E.phi[k] < SEUIL_SANS_EAU:
                E.jours_sans_eau[k] += 1
                p.noter("coupure_eau", lieu=T.lieux[k], part=round(float(E.phi[k]), 3))
        # 3. les eaux usees et la qualite de l eau du bassin
        b = sy.bassin
        crue = crues.get(B.nom[b], 0)
        sy.f_step = sy.f_elec * (0.0 if crue else 1.0)             # une crue noie la station : by-pass
        hab = E.hab[lieux]; rac = E.raccorde[lieux]
        conso = hab * CONSO_M3_HAB_J * E.phi[lieux]
        eu = conso * RETOUR_EGOUT
        traite = float((eu * rac).sum()) * sy.f_step
        non_traite = float((eu * rac).sum()) - traite
        if non_traite > 0: p.compter("eaux_usees_non_traitees_m3", non_traite)
        if traite > EPS: _depenser(p, r, _marche_de(p, sy.ile), traite * EPURATION_M3, "exploitation_eau")
        for j, k in enumerate(lieux.tolist()):
            if hab[j] <= 0: continue
            n_kg = hab[j] * AZOTE_KG_HAB_J
            n_eau = n_kg * ((1.0 - ENLEVEMENT_AZOTE_STEP * sy.f_step) if rac[j] else FUITE_AZOTE_FOSSE)
            if n_eau > 0: TER.rejeter(p, T.lieux[k], "nitrates", n_eau * NO3_PAR_N)
        hb = float(hab.sum())
        u = (float((hab * (1 - rac)).sum()) * FUITE_FOSSE + float((hab * rac).sum()) * (1.0 - sy.f_step)) / hb if hb > 0 else 0.0
        i = int(B.ile[b])
        ecoli_brut = ECOLI_BRUT * (1.0 + K_FECAL * u) * (ECOLI_CRUE if crue else 1.0)
        turb = TURB_BRUTE + (TURB_PLUIE if m is not None and m.pluie[i] > 30.0 else 0.0) + TURB_CRUE * crue
        lr = (LOG_CHLORE if turb <= TURB_LIMITE_DESINF else LOG_CHLORE_TROUBLE) * min(1.0, sy.f_elec)
        ecoli_sortie = ecoli_brut * 10.0 ** (-lr)
        turb_sortie = turb * (1.0 - ABATTEMENT_TURB)
        lid = sy.chef_lieu
        chim = max(TER.concentration(p, lid, x) * (1.0 - ENLEVEMENT[x]) / TER.POLLUANT[x].limite for x in TER.EAU)
        nitr = TER.concentration(p, lid, "nitrates")
        for k in lieux.tolist():
            E.ecoli[k] = ecoli_sortie + ECOLI_INTRUSION * (1.0 - E.phi[k])
            E.turb[k] = turb_sortie; E.chim[k] = chim; E.nitrates[k] = nitr
    # memoire des manques
    E.manque7[:, :-1] = E.manque7[:, 1:]
    E.manque7[:, -1] = np.where(E.hab > 0, 1.0 - E.phi, 0.0)
    S.c_hab_jours += float(E.hab.sum())
    S.c_consomme_hab += float((E.hab * CONSO_M3_HAB_J * E.phi).sum())


# ================================================================== les dechets
def _produire_dechets(p):
    """21 h : les dechets du jour de chaque lieu habite, dans ses conteneurs."""
    S = _sp(p); L = p.socle.livre; E = S.eau
    for pt in S.points:
        q = float(E.hab[pt.lieu]) * DECHETS_T_HAB_J
        if q > 0: L.produire(pt.stock, S.dechets_id, q, "production_dechets")


def _collecter(p):
    """7 h : la tournee de chaque benne de chaque ile ; les points les plus pleins d abord, tant que le temps et la charge
    le permettent ; rien en greve, sans gazole ou sans caisse. Les lieux isoles par une route coupee ne sont pas servis."""
    S = _sp(p); T = p.domaine("territoire"); L = p.socle.livre; w = p.w; E = S.eau
    dech = S.dechets_id
    isoles = set(lieux_isoles(p))
    for c in S.communes:
        if p.jour < c.greve_jusqu:
            p.compter("collecte_impossible"); continue
        d = S.decharges[S.decharge_ile[c.ile]]
        depot = w.carte.lieux[d.lieu]
        m = _marche_de(p, c.ile)
        pts = [pt for pt in S.points if pt.ile == c.ile and T.lieux[pt.lieu] not in isoles]
        prod = {pt.lieu: max(EPS, float(E.hab[pt.lieu]) * DECHETS_T_HAB_J) for pt in pts}
        for _ in range(c.camions):
            cands = [pt for pt in pts if pt.stock[dech] >= SEUIL_COLLECTE_J * prod[pt.lieu] - EPS and pt.stock[dech] > EPS]
            if not cands: break
            cands.sort(key=lambda pt: (-pt.stock[dech], pt.lieu))
            temps, charge, km, pos = TOURNEE_H, 0.0, 0.0, depot
            fait = []
            for pt in cands:
                if charge >= CAMION_T - EPS: break
                lieu = w.carte.lieux[T.lieux[pt.lieu]]
                aller = w.carte.km_route(pos, lieu); retour = w.carte.km_route(lieu, depot)
                t = (aller + retour) / VITESSE_TOURNEE_KMH + ARRET_H
                if t > temps + EPS and fait: continue
                q = min(pt.stock[dech], CAMION_T - charge)
                fait.append((pt, q)); charge += q; km += aller
                temps -= aller / VITESSE_TOURNEE_KMH + ARRET_H
                pos = lieu
            km += w.carte.km_route(pos, depot)
            if not _bruler_carburant(p, c, m, km * CARBURANT_BENNE_U_KM, "carburant_services"):
                p.compter("collecte_impossible"); break
            _depenser(p, c, m, EQUIPAGE_BENNE * TOURNEE_H * SALAIRE_SOUS_TRAITANT_H + km * FRAIS_BENNE_KM,
                      "collecte_dechets")
            for pt, q in fait:
                x = L.deplacer(pt.stock, d.stock, dech, q, "collecte_dechets")
                S.c_collecte += x; pt.dernier = p.jour
                p.compter("dechets_collectes_t", x)
            recycle = L.consommer(d.stock, dech, charge * PART_RECYCLEE, "recyclage")
            S.c_recycle += recycle
            if recycle > 0: p.compter("dechets_recycles_t", recycle)
        if not d.pleine and d.stock[dech] > d.capacite_t:
            d.pleine = True
            p.noter("decharge_pleine", ile=c.ile, lieu=d.lieu, tonnes=round(d.stock[dech], 1))


# ================================================================== les routes : l arbre et les chemins
def _batir_routes(p, S):
    T = p.domaine("territoire"); w = p.w
    R = ReseauRoutier()
    n = len(T.lieux)
    lieux = [w.carte.lieux[lid] for lid in T.lieux]
    racine = np.full(n, -1, np.int64)
    a, b, ile, typ, lon = [], [], [], [], []
    parent_troncon = np.full(n, -1, np.int64)
    capitales = {}
    for i, nom in enumerate(T.iles):
        sel = [k for k in range(n) if T.lieu_ile[k] == i]
        caps = [k for k in sel if lieux[k].type == "capitale"]
        if not caps:
            chef = T.capitale_ile[i]
            caps = [T.index_lieu[chef]] if chef in T.index_lieu else sel[:1]
        capitales[i] = caps
        for k in sel:
            racine[k] = min(caps, key=lambda c: (lieux[k].distance(lieux[c]), c))
        # chaque lieu rejoint son voisin le plus proche parmi ceux, plus proches de sa capitale, que son chemin longe
        for k in sorted(sel, key=lambda k: (lieux[k].distance(lieux[racine[k]]), k)):
            r = racine[k]
            if k == r: continue
            dk = lieux[k].distance(lieux[r])
            cands = [c for c in sel if racine[c] == r and c != k and lieux[c].distance(lieux[r]) < dk
                     and lieux[k].distance(lieux[c]) + lieux[c].distance(lieux[r]) <= 1.2 * dk]
            par = min(cands, key=lambda c: (lieux[k].distance(lieux[c]), c)) if cands else r
            parent_troncon[k] = len(a)
            a.append(k); b.append(par); ile.append(i); typ.append(0)
            lon.append(max(0.2, w.carte.km_route(lieux[k], lieux[par])))
    # les liaisons entre capitales d une meme ile
    for i, caps in capitales.items():
        for x in range(len(caps)):
            for y in range(x + 1, len(caps)):
                a.append(caps[x]); b.append(caps[y]); ile.append(i); typ.append(1)
                lon.append(max(0.2, w.carte.km_route(lieux[caps[x]], lieux[caps[y]])))
    nt = len(a)
    R.a, R.b = np.array(a, np.int64), np.array(b, np.int64)
    R.ile, R.type, R.longueur = np.array(ile, np.int64), np.array(typ, np.int64), np.array(lon, float)
    rng = p.hasard("services_publics_installation")
    R.etat = rng.uniform(*ETAT_INITIAL, nt)
    R.ferme = np.zeros(nt, bool)
    R.veh_jour, R.esal_jour = np.zeros(nt), np.zeros(nt)
    R.trafic_ref = np.zeros(nt)
    R.pris = np.zeros(nt, bool)
    R.racine = racine; R.capitales = capitales
    R.montee = []
    for k in range(n):
        ch, x = [], k
        while parent_troncon[x] >= 0:
            t = int(parent_troncon[x]); ch.append(t); x = int(R.b[t])
        R.montee.append(ch)
    R.dessous = [[] for _ in range(nt)]
    for k in range(n):
        for t in R.montee[k]: R.dessous[t].append(k)
    R.chemins = {}; R.liaisons_ok = None
    # distance du depot ( la capitale ) de chaque ile a chaque troncon : pour le critere du plus proche
    R.km_base = np.array([min(w.carte.km_route(lieux[c], lieux[int(R.a[t])]) for c in capitales[int(R.ile[t])])
                          for t in range(nt)])
    for k in ("c_climat", "c_trafic", "c_choc", "c_repare"): setattr(R, k, np.zeros(nt))
    R.n_fermetures = 0
    return R


def _chemin_capitales(R, i, x, y):
    """Les liaisons ouvertes qui menent de la capitale x a la capitale y ( Dijkstra sur les capitales d une ile ) ;
    None si aucune."""
    if x == y: return []
    caps = R.capitales[i]
    lien = {}
    for t in np.nonzero((R.type == 1) & (R.ile == i) & ~R.ferme)[0].tolist():
        u, v = int(R.a[t]), int(R.b[t])
        lien.setdefault(u, []).append((v, t)); lien.setdefault(v, []).append((u, t))
    dist = {x: 0.0}; prec = {}; faits = set()
    while True:
        cands = [(d, c) for c, d in dist.items() if c not in faits]
        if not cands: return None
        d, c = min(cands)
        if c == y: break
        faits.add(c)
        for v, t in lien.get(c, ()):
            nd = d + R.longueur[t]
            if nd < dist.get(v, math.inf) - EPS: dist[v] = nd; prec[v] = (c, t)
    ch = []
    while y != x:
        c, t = prec[y]; ch.append(t); y = c
    return ch


def chemin(p, o, d):
    """Les troncons qu un vehicule emprunte du lieu `o` au lieu `d` ( indices du territoire ) : sa montee vers sa
    capitale, les liaisons ouvertes entre capitales, la descente vers `d` ; dans un meme arbre, la difference
    symetrique des deux montees. En cache ; le cache tombe quand une liaison ferme ou rouvre."""
    R = _sp(p).routes
    cle = (int(o), int(d))
    ch = R.chemins.get(cle)
    if ch is not None: return ch
    mo, md = R.montee[o], R.montee[d]
    ro, rd = int(R.racine[o]), int(R.racine[d])
    if ro == rd:
        so, sd = set(mo), set(md)
        ch = np.array(sorted(so ^ sd), np.int64)
    else:
        lien = None
        if ro >= 0 and rd >= 0:
            T_ = p.domaine("territoire")
            if T_.lieu_ile[ro] == T_.lieu_ile[rd]: lien = _chemin_capitales(R, int(T_.lieu_ile[ro]), ro, rd)
        ch = np.array(mo + (lien or []) + md, np.int64)
    R.chemins[cle] = ch
    return ch


def _invalider_chemins(R):
    ok = tuple((~R.ferme[R.type == 1]).tolist())
    if ok != R.liaisons_ok:
        R.chemins = {}; R.liaisons_ok = ok


def _index(p, lieu):
    T = p.domaine("territoire")
    lid = lieu if isinstance(lieu, str) else lieu.id
    return T.index_lieu[lid]


# ================================================================== les routes : le trafic
def _passage(R, ch, veh, esal):
    if len(ch):
        np.add.at(R.veh_jour, ch, veh)
        np.add.at(R.esal_jour, ch, esal)


def _convois(p):
    """Chaque heure pleine ( les convois du moteur partent a l heure ) : les nouveaux convois font le trafic lourd de
    leurs troncons ( aller charge, retour a vide ) ; sans la logistique, leur arrivee suit l etat des troncons."""
    S = _sp(p); R = S.routes; w = p.w; T = p.domaine("territoire")
    for cv in reversed(w.convois):
        if cv.id <= S.vus_convois: break
        o, d = T.index_lieu.get(cv.origine.id), T.index_lieu.get(cv.destination.id)
        if o is None or d is None: continue
        ch = chemin(p, o, d)
        _passage(R, ch, 2.0, ESAL_CHARGE + ESAL_VIDE)
        if S.pont_convois and not p.a("logistique") and len(ch):
            f = facteur_duree(R, ch)
            duree = max(1, cv.arrivee - cv.depart)
            extra = int(math.ceil(duree * f - 1e-9)) - duree
            if extra > 0:
                cv.arrivee += extra
                w.conducteur_libre[cv.conducteur] = w.conducteur_libre.get(cv.conducteur, 0) + 2 * extra
                w.habitants[cv.conducteur].heures_jour += 2 * extra * C.MINUTES_PAR_PAS / 60.0
                S.c_ralentis += 1
                p.compter("convoi_ralenti", extra)
    S.vus_convois = w.n_convoi


def facteur_duree(R, ch):
    """Le temps de parcours sur ces troncons, rapporte a celui de routes en bon etat ( >= 1 )."""
    lon = R.longueur[ch]
    u = np.maximum(vitesse_relative(R.etat[ch]), U_MIN)
    return float((lon / u).sum() / lon.sum())


def _trafic_voitures(p):
    """23 h : les trajets en vehicule du jour ( plan de l agenda, aller et retour ), ou sans l agenda un aller-retour
    par habitant vers son marche."""
    S = _sp(p); R = S.routes; T = p.domaine("territoire")
    if p.a("agenda") and p.domaine("agenda").plan is not None:
        from . import d05_agenda as AG
        a = p.domaine("agenda"); pl = a.plan
        vers_t = np.array([T.index_lieu.get(l.id, -1) for l in a.lieux], np.int64)
        paires = {}
        for s in range(AG.NS):
            v = np.nonzero(pl.actif[:, s] & (pl.mode[:, s] == AG.EN_VEHICULE))[0]
            if not len(v): continue
            dom = pl.dom[v].astype(np.int32)
            dest = AG._dest_lieu(a, dom, pl.trav[v].astype(np.int32), pl.dest[v, s].astype(np.int32))
            o, d = vers_t[dom], vers_t[dest]
            ok = (o >= 0) & (d >= 0) & (o != d)
            cle, nb = np.unique(o[ok] * len(T.lieux) + d[ok], return_counts=True)
            for c_, n_ in zip(cle.tolist(), nb.tolist()): paires[c_] = paires.get(c_, 0) + n_
        for c_, n_ in paires.items():
            o, d = divmod(c_, len(T.lieux))
            _passage(R, chemin(p, o, d), 2.0 * n_, 2.0 * n_ * ESAL_VOITURE)
    else:
        hab = S.eau.hab
        for k in np.nonzero(hab > 0)[0].tolist():
            ch = R.montee[k]
            if ch: _passage(R, np.array(ch, np.int64), 2.0 * TRAFIC_VOITURE_HAB_J * hab[k], 2.0 * TRAFIC_VOITURE_HAB_J * hab[k] * ESAL_VOITURE)


# ================================================================== les routes : la journee
def _fermer(p, R, t, cause):
    if R.ferme[t]: return
    R.ferme[t] = True; R.n_fermetures += 1
    T = p.domaine("territoire")
    p.noter("route_fermee", troncon=int(t), de=T.lieux[int(R.a[t])], vers=T.lieux[int(R.b[t])], cause=cause)
    _invalider_chemins(R)
    iso = [T.lieux[k] for k in R.dessous[t]] if R.type[t] == 0 else []
    if iso:     # tout de suite : la liste que relit l aube, et l ensemble que lit lancer_convoi s il existe deja
        deja = {c["lieu"] for c in p.w.coupures if c.get("services_publics") and c["debut"] == p.jour}
        p.w.coupures.extend({"lieu": lid, "debut": p.jour, "jours": 1, "services_publics": True}
                            for lid in sorted(set(iso) - deja))
        if hasattr(p.w, "routes_temporaires"): p.w.routes_temporaires = set(p.w.routes_temporaires) | set(iso)


def _rouvrir(p, R, t):
    if not R.ferme[t]: return
    R.ferme[t] = False
    T = p.domaine("territoire")
    p.noter("route_rouverte", troncon=int(t), de=T.lieux[int(R.a[t])], vers=T.lieux[int(R.b[t])])
    _invalider_chemins(R)


def _routes_minuit(p):
    """0 h 20, apres la meteo du territoire : le climat du jour use les routes ; seismes et crues du jour coupent."""
    S = _sp(p); R = S.routes; T = p.domaine("territoire"); m = T.meteo
    if m is None: return
    pluie = m.pluie[R.ile]; gel = (m.tmin[R.ile] < 0.0).astype(float)
    S.pluie7[:, :-1] = S.pluie7[:, 1:]; S.pluie7[:, -1] = m.pluie
    ds = degradation_jour(R.etat, pluie, gel, 0.0)
    R.etat = np.maximum(0.0, R.etat - ds); R.c_climat += ds
    rng = p.du_jour("services_publics_chocs")
    for c in TER.catastrophes_en_cours(p, type_="seisme"):
        if c.debut_j != p.jour or not c.intensites: continue
        for t in range(len(R.a)):
            mmi = max(c.intensites.get(T.lieux[int(R.a[t])], 0.0), c.intensites.get(T.lieux[int(R.b[t])], 0.0))
            g = int(math.floor(mmi))
            if g < 7: continue
            d = min(R.etat[t], DEGAT_MMI * (mmi - 6.0))
            R.etat[t] -= d; R.c_choc[t] += d
            if rng.random() < COUPURE_MMI[min(10, g)]:
                R.c_choc[t] += R.etat[t]; R.etat[t] = 0.0; _fermer(p, R, t, "seisme")
    for c in TER.catastrophes_en_cours(p, type_="inondation"):
        if c.debut_j != p.jour: continue
        b = T.bassins.nom.index(c.lieu)
        for t in np.nonzero(T.lieu_bassin[R.a] == b)[0].tolist():
            d = min(R.etat[t], DEGAT_CRUE * c.gravite)
            R.etat[t] -= d; R.c_choc[t] += d
            if rng.random() < COUPURE_CRUE * c.gravite:
                R.c_choc[t] += R.etat[t]; R.etat[t] = 0.0; _fermer(p, R, t, "crue")
    for t in np.nonzero((R.etat < S_FERME) & ~R.ferme)[0].tolist(): _fermer(p, R, t, "usure")


def _coupures_e1(p):
    """5 h 50, avant l aube du moteur : les lieux isoles par un troncon ferme entrent dans w.coupures pour la journee
    ( Monde.aube en fait routes_temporaires ; Monde.lancer_convoi les refuse ). Une donnee ; rien n est remplace."""
    S = _sp(p); w = p.w
    autres = [c for c in w.coupures if not c.get("services_publics")]
    miens = [{"lieu": lid, "debut": p.jour, "jours": 1, "services_publics": True} for lid in sorted(lieux_isoles(p))]
    w.coupures[:] = autres + miens
    S.coupures_e1 = len(miens)


def _candidats(R, ile):
    return np.nonzero((R.ile == ile) & (R.etat < SEUIL_TRAVAUX) & ~R.pris)[0]


def _designer(R, cands, critere, rng):
    if not len(cands): return -1
    if critere == 0: return int(cands[np.lexsort((cands, R.etat[cands]))[0]])
    if critere == 1: return int(cands[np.lexsort((cands, R.etat[cands], -R.trafic_ref[cands]))[0]])
    if critere == 2: return int(cands[np.lexsort((cands, R.etat[cands], R.km_base[cands]))[0]])
    return int(cands[int(rng.integers(0, len(cands)))])


def _equipes(p):
    """7 h : chaque equipe routiere de chaque ile choisit son troncon ( point `entretenir_route` ), y va, travaille."""
    S = _sp(p); R = S.routes; T = p.domaine("territoire"); L = p.socle.livre
    R.pris[:] = False
    rng = p.hasard("services_publics_equipes")
    for c in S.communes:
        i = T.iles.index(c.ile)
        n_cap = len(R.capitales.get(i, ()))
        cout = equipe_cout(p, c.ile)
        c.credit_routes += BUDGET_ROUTES_HAB_AN * c.pop / JOURS_AN
        n = min(EQUIPES_MAX_PAR_CAPITALE * max(1, n_cap), int(c.credit_routes // max(cout, EPS)))
        c.credit_routes -= n * cout
        if p.jour < c.urgence_jusqu: n += c.urgence
        m = _marche_de(p, c.ile)
        part_fermee = float(R.ferme[R.ile == i].mean()) if (R.ile == i).any() else 0.0
        pluie = float(S.pluie7[i].sum())
        for e in range(n):
            cands = _candidats(R, i)
            if not len(cands): break
            cibles = [_designer(R, cands, k, rng) for k in range(3)]
            x = []
            for t in cibles:
                x += [float(R.etat[t]), min(1.0, R.trafic_ref[t] / TRAFIC_NORME), min(1.0, R.longueur[t] / 10.0), float(R.ferme[t])]
            x += [part_fermee, min(1.0, pluie / 70.0), min(1.0, float(R.km_base[cibles[2]]) / 20.0)]
            cout = equipe_cout(p, c.ile)
            if m.stocks["carburant"] < CARBURANT_EQUIPE_U or c.caisse < cout: break
            cle = S.prochain_chantier; S.prochain_chantier += 1
            a = S.decideur.decider(cle, ContexteEntretien(tuple(x), cibles))
            t = cibles[a] if a < 3 else _designer(R, cands, 3, rng)
            ferme_avant = bool(R.ferme[t])
            gain = travailler(p, c, t)
            S.chantiers[cle] = Chantier(cle, t, gain, ferme_avant, a, p.jour)


def travailler(p, c, t):
    """Une journee d equipe de la commune `c` sur le troncon `t` : gazole brule, main-d oeuvre et enrobes payes a
    l entrepreneur, trajet depuis le depot deduit des heures, beton pour une route coupee. Rend l etat gagne."""
    S = _sp(p); R = S.routes
    m = _marche_de(p, c.ile)
    if not _bruler_carburant(p, c, m, CARBURANT_EQUIPE_U, "carburant_services"): return 0.0
    R.pris[t] = True
    _depenser(p, c, m, OUVRIERS_EQUIPE * 8.0 * SALAIRE_SOUS_TRAITANT_H + ENROBES_T * PRIX_ENROBES_T, "travaux_routiers")
    heures = max(2.0, 8.0 - 2.0 * R.km_base[t] / VITESSE_EQUIPE_KMH)
    km = KM_EQUIPE_J * heures / 8.0
    if R.ferme[t] and not _beton(p, c): km *= 0.5
    gain = min(1.0 - R.etat[t], km / R.longueur[t])
    R.etat[t] += gain; R.c_repare[t] += gain
    if R.ferme[t] and R.etat[t] >= S_ROUVRE: _rouvrir(p, R, t)
    p.compter("chantier_routier")
    return float(gain)


def equipe_cout(p, ile):
    """Le cout d une journee d equipe, drachmes ( main-d oeuvre, enrobes, gazole au prix du marche de l ile )."""
    m = _marche_de(p, ile)
    return OUVRIERS_EQUIPE * 8.0 * SALAIRE_SOUS_TRAITANT_H + ENROBES_T * PRIX_ENROBES_T + CARBURANT_EQUIPE_U * m.prix["carburant"]


def _beton(p, c):
    """Le ciment et l acier d un chantier qui rouvre une route : du stock de la commune, livres par l industrie si elle
    est installee ( sinon l entrepreneur les apporte ). Faux si l industrie ne peut pas fournir."""
    if not p.a("industrie"): return True
    from . import d10_industrie as IND
    L = p.socle.livre; cat = p.socle.catalogue
    ok = True
    for bien, q in (("ciment", CIMENT_T), ("acier", ACIER_T)):
        bid = cat.id(bien)
        if c.stock[bid] < q: IND.livrer(p, bien, q - c.stock[bid], c.stock, c)
        if c.stock[bid] < q - EPS: ok = False
    if ok:
        for bien, q in (("ciment", CIMENT_T), ("acier", ACIER_T)): L.consommer(c.stock, cat.id(bien), q, "travaux_routiers")
    return ok


# ================================================================== le soir ( 23 h 40 )
def _soir(p):
    S = _sp(p); R = S.routes; w = p.w; L = p.socle.livre
    _trafic_voitures(p)
    # le trafic lourd use les troncons ; le trafic de reference suit ce qui a roule ( fige sur un troncon ferme )
    ds = K_ESAL * R.esal_jour / 1.0
    R.etat = np.maximum(0.0, R.etat - ds); R.c_trafic += ds
    for t in np.nonzero((R.etat < S_FERME) & ~R.ferme)[0].tolist(): _fermer(p, R, t, "usure")
    ouvert = ~R.ferme
    R.trafic_ref = np.where(ouvert, R.trafic_ref + EMA_TRAFIC * (R.veh_jour - R.trafic_ref), R.trafic_ref)
    # les notes des chantiers
    dec = S.decideur; H = POINT_ENTRETIEN.horizon_j
    for cle in sorted(S.chantiers):
        ch = S.chantiers[cle]
        t = ch.troncon
        ch.total += service_chantier(float(R.trafic_ref[t]), float(R.longueur[t]), float(R.etat[t]), bool(R.ferme[t]),
                                     ch.gain, ch.ferme_avant)
        ch.jours += 1
        mur = ch.jours >= H
        note = math.log1p(ch.total / H)
        dec.noter(cle, note * H if mur else 0.0, p.jour)
        if mur:
            S.notes.append((p.jour, ch.action, note, ch.total / H))
            del S.chantiers[cle]; dec.attentes.pop(cle, None)
    R.veh_jour[:] = 0.0; R.esal_jour[:] = 0.0
    # l energie consommee hier par les systemes ( contrats du domaine 11 )
    if S.contrats:
        from . import d11_energie as EN
        for sy in S.systemes:
            if sy.contrat is None: continue
            _, serv, non = EN.servi(p, sy.contrat)
            sy.f_elec = serv / (serv + non) if serv + non > EPS else 1.0
    _factures(p)
    _finances(p)


def _factures(p):
    """Les factures d eau des menages ( vectorisees ) ; chaque menage paie tous les 30 jours, decale par menage, avec la
    TVA de l eau ; puis la taxe locale ( proprete, eclairage ) a l Etat."""
    S = _sp(p); w = p.w; L = p.socle.livre; E = S.eau
    n = len(S.mg_lieu)
    if n == 0: return
    k = S.mg_lieu; ok = k >= 0
    m3 = np.zeros(n)
    fac = (1.0 - PERTES_REELLES - PERTES_APPARENTES) / (1.0 - PERTES_REELLES)
    m3[ok] = S.mg_viv[ok] * CONSO_M3_HAB_J * E.phi[k[ok]] * fac
    du = p.col("menage", "sp_eau_du"); arr = p.col("menage", "sp_eau_arrieres"); fm = p.col("menage", "sp_eau_m3")
    tarif = np.zeros(n)
    tarif[ok] = TARIF_EAU + TARIF_ASSAINISSEMENT * E.raccorde[k[ok]]
    du[:n] += m3 * tarif; fm[:n] += m3
    S.c_facture_m3 += float(m3.sum())
    S.c_injecte += math.fsum(sy.injecte_jour for sy in S.systemes)     # le meme jour que la facture
    T = p.domaine("territoire")
    ids = np.arange(n)
    for i in np.nonzero(ok & ((ids + p.jour) % JOURS_FACTURE == 0) & (du[:n] + arr[:n] > EPS))[0].tolist():
        mg = w.menages[i]
        r = S.regies[S.regie_ile[T.iles[int(T.lieu_ile[k[i]])]]]
        voulu = float(du[i] + arr[i])
        paye = L.transferer(mg, r, voulu, "facture_eau")
        part_eau = TARIF_EAU / float(tarif[i]) if tarif[i] > 0 else 1.0
        if paye > 0: ET.percevoir_tva(p, mg, "eau_potable", paye * part_eau)
        du[i] = 0.0; arr[i] = voulu - paye
        if voulu - paye > EPS: p.compter("facture_eau_impayee", voulu - paye)
    for i in np.nonzero(ok & ((ids + p.jour) % JOURS_TAXE == 7))[0].tolist():
        ET.percevoir(p, w.menages[i], ET.taxe_locale(SURFACE_LOGEMENT_M2, JOURS_TAXE), "taxe_locale")


def _finances(p):
    """Le Tresor remonte la caisse des communes et des regies a 10 jours de depenses ( dotation KAP, subvention ) ;
    l excedent d une regie au-dela de 60 jours lui revient."""
    S = _sp(p); w = p.w; L = p.socle.livre
    for x, motif in [(c, "dotation_communes") for c in S.communes] + [(r, "subvention_regie_eau") for r in S.regies]:
        x.cout_ema += 0.1 * (x.depense_jour - x.cout_ema)
        x.depense_jour = 0.0
        besoin = JOURS_COUSSIN * max(x.cout_ema, 50.0)
        if isinstance(x, Commune): besoin += equipe_cout(p, x.ile) + x.camions * 400.0
        if x.caisse < besoin: L.transferer(w.gouv, x, besoin - x.caisse, motif)
        elif isinstance(x, RegieEau) and x.caisse > JOURS_EXCEDENT * max(x.cout_ema, 50.0) + besoin:
            L.transferer(x, w.gouv, x.caisse - besoin, "excedent_regie_eau")


# ================================================================== API pour les autres domaines
def qualite_eau(p, lieu):
    """La qualite de l eau du robinet d un lieu habite, aujourd hui ( domaine 16 ). Un lieu non habite : None."""
    S = _sp(p); E = S.eau; k = _index(p, lieu)
    if S.systeme_lieu[k] < 0: return None
    return QualiteEau(lieu=p.domaine("territoire").lieux[k], ecoli=float(E.ecoli[k]), turbidite=float(E.turb[k]),
                      chimique=float(E.chim[k]), nitrates=float(E.nitrates[k]), part_servie=float(E.phi[k]),
                      manque_7j=float(E.manque7[k].mean()), insalubrite=insalubrite(p, lieu))


def facteur_gastro(p, lieu):
    """Proposition au domaine 16 ( qui calibre ) : le multiplicateur du risque de gastro-enterite hydrique d un lieu, a
    la place de la penurie et de la pollution de l eau BRUTE qu il lit aujourd hui : ( 1 + 4 x manque sur 7 jours )
    x ( 1 + 2 x min( 3, indice chimique apres traitement ) ) x ( 1 + 0,5 log10( 1 + E. coli ) ) x ( 1 + 0,25 x min( 4,
    jours de dechets non collectes au-dela de 3, / 7 ) ). Les deux premiers termes sont ceux du domaine 16 ; les deux autres, a
    calibrer."""
    q = qualite_eau(p, lieu)
    if q is None: return 1.0
    return ((1.0 + 4.0 * q.manque_7j) * (1.0 + 2.0 * min(3.0, q.chimique)) * (1.0 + 0.5 * math.log10(1.0 + q.ecoli))
            * (1.0 + 0.25 * min(4.0, max(0.0, q.insalubrite - SEUIL_INSALUBRE_J) / 7.0)))


def insalubrite(p, lieu):
    """Les jours de production de dechets qui attendent aux conteneurs d un lieu ( 0 si rien, ou lieu non habite )."""
    S = _sp(p); k = _index(p, lieu)
    j = S.point_lieu[k]
    if j < 0: return 0.0
    pt = S.points[j]
    prod = float(S.eau.hab[k]) * DECHETS_T_HAB_J
    return pt.stock[S.dechets_id] / prod if prod > EPS else 0.0


def troncons(p):
    """La table des troncons ( domaine 14 ) : [ ( indice, de, vers, type, km, etat, ferme, trafic, facteur vitesse,
    facteur accident ) ]."""
    R = _sp(p).routes; T = p.domaine("territoire")
    return [(t, T.lieux[int(R.a[t])], T.lieux[int(R.b[t])], ("desserte", "liaison")[int(R.type[t])], float(R.longueur[t]),
             float(R.etat[t]), bool(R.ferme[t]), float(R.trafic_ref[t]), vitesse_relative(R.etat[t], R.ferme[t]),
             risque_accident(R.etat[t])) for t in range(len(R.a))]


def etat_route(p, origine, destination):
    """( etat moyen pondere par les km, facteur de vitesse, facteur d accident pondere, ouverte ) du trajet entre deux
    lieux ( domaines 14 et 15 )."""
    R = _sp(p).routes
    ch = chemin(p, _index(p, origine), _index(p, destination))
    if not len(ch): return 1.0, 1.0, 1.0, True
    lon = R.longueur[ch]
    return (float((R.etat[ch] * lon).sum() / lon.sum()), 1.0 / facteur_duree(R, ch),
            float((risque_accident(R.etat[ch]) * lon).sum() / lon.sum()), route_ouverte(p, origine, destination))


def facteur_vitesse(p, origine, destination):
    """La vitesse moyenne du trajet rapportee a des routes en bon etat ( domaine 15 : duree = duree nominale / facteur )."""
    R = _sp(p).routes
    ch = chemin(p, _index(p, origine), _index(p, destination))
    return 1.0 / facteur_duree(R, ch) if len(ch) else 1.0


def duree_trajet_pas(p, origine, destination, vitesse_kmh=C.VITESSE_CONVOI_KMH):
    """La duree d un trajet en pas, etat des routes compris ( domaine 15, a la place du calcul de lancer_convoi )."""
    km = p.w.carte.km_route(p.w.carte.lieux[origine if isinstance(origine, str) else origine.id],
                            p.w.carte.lieux[destination if isinstance(destination, str) else destination.id])
    return max(1, math.ceil(km / vitesse_kmh * 60 / C.MINUTES_PAR_PAS / facteur_vitesse(p, origine, destination)))


def facteur_accident(p, origine, destination):
    return etat_route(p, origine, destination)[2]


def route_ouverte(p, origine, destination):
    """Vrai si aucun troncon du trajet n est ferme et que les capitales se rejoignent par des liaisons ouvertes."""
    R = _sp(p).routes; T = p.domaine("territoire")
    o, d = _index(p, origine), _index(p, destination)
    ro, rd = int(R.racine[o]), int(R.racine[d])
    if ro != rd and T.lieu_ile[ro] == T.lieu_ile[rd] and _chemin_capitales(R, int(T.lieu_ile[ro]), ro, rd) is None:
        return False
    ch = chemin(p, o, d)
    return not bool(R.ferme[ch].any()) if len(ch) else True


def routes_coupees(p):
    """Les troncons fermes ( domaine 18 ) : [ ( indice, de, vers ) ]."""
    R = _sp(p).routes; T = p.domaine("territoire")
    return [(t, T.lieux[int(R.a[t])], T.lieux[int(R.b[t])]) for t in np.nonzero(R.ferme)[0].tolist()]


def lieux_isoles(p):
    """Les lieux coupes de leur capitale par un troncon ferme."""
    R = _sp(p).routes; T = p.domaine("territoire")
    out = set()
    for t in np.nonzero(R.ferme & (R.type == 0))[0].tolist(): out.update(T.lieux[k] for k in R.dessous[t])
    return sorted(out)


def borne_incendie(p, lieu):
    """( m3/h disponibles a une borne du lieu, m3 en reserve dans le reservoir ) : 60 m3/h si le reservoir tient deux
    heures de borne et que le lieu est servi aujourd hui ( domaine 18 )."""
    S = _sp(p); k = _index(p, lieu)
    s = S.systeme_lieu[k]
    if s < 0: return 0.0, 0.0
    sy = S.systemes[s]
    stock = sy.stock[S.eau_id]
    ok = stock >= BORNE_M3_H * BORNE_H and S.eau.phi[k] >= SEUIL_SANS_EAU
    return (BORNE_M3_H if ok else min(BORNE_M3_H, stock / BORNE_H)), stock


def prelever_incendie(p, lieu, m3):
    """Les pompiers ( domaine 18 ) tirent `m3` du reservoir qui sert le lieu. Rend les m3 tires."""
    S = _sp(p); k = _index(p, lieu)
    s = S.systeme_lieu[k]
    if s < 0 or m3 <= 0: return 0.0
    x = p.socle.livre.consommer(S.systemes[s].stock, S.eau_id, float(m3), "lutte_incendie")
    S.c_incendie += x
    return x


def couper_troncon(p, t, cause="forcee"):
    """Detruit le troncon `t` ( scenario, sabotage, domaine 27 ) : etat 0, ferme."""
    R = _sp(p).routes
    R.c_choc[t] += R.etat[t]; R.etat[t] = 0.0
    _fermer(p, R, int(t), cause)


def greve_collecte(p, ile, jours):
    """Les eboueurs d une ile cessent le travail pendant `jours` jours ( domaine 4 : syndicats ; portes )."""
    c = _sp(p).communes[_sp(p).commune_ile[ile]]
    c.greve_jusqu = p.jour + int(jours)
    p.noter("greve_collecte", ile=ile, jours=int(jours))


def programme_urgence(p, ile, equipes, jours):
    """Un programme d urgence ( apres un seisme, un hiver rude ) : `equipes` equipes de plus chaque jour pendant `jours`
    jours, payees par la dotation de l Etat."""
    c = _sp(p).communes[_sp(p).commune_ile[ile]]
    c.urgence, c.urgence_jusqu = int(equipes), p.jour + int(jours)


def passer(p, origine, destination, vehicules, esal_par_vehicule=ESAL_CHARGE):
    """Un trafic d un autre domaine ( transport, logistique, armee ) qui use les troncons de ce trajet aujourd hui."""
    R = _sp(p).routes
    ch = chemin(p, _index(p, origine), _index(p, destination))
    _passage(R, ch, float(vehicules), float(vehicules) * esal_par_vehicule)


# ------------------------------------------------------------------ bilans ( portes )
def bilan_eau(p):
    """( produite - 0,97 x captee au territoire, produite - consommee - perdue - variation des reservoirs ), m3. Zero
    et zero, sinon de l eau potable est nee sans captage ou a disparu hors des puits comptes."""
    S = _sp(p); T = p.domaine("territoire"); L = p.socle.livre
    capte = float(T.bassins.par_usage[:, TER.USAGES.index("domestique")].sum()) - S.base_domestique
    prod = L.flux["produit"].get("eau_potable", 0.0)
    sorti = L.flux["consomme"].get("eau_potable", 0.0) + L.flux["perdu"].get("eau_potable", 0.0)
    stock = math.fsum(sy.stock[S.eau_id] for sy in S.systemes)
    return prod - (1.0 - PERTE_TRAITEMENT) * capte, prod - sorti - stock


def bilan_dechets(p):
    """( produits - collectes - aux points, collectes - recycles - enfouis ), tonnes."""
    S = _sp(p); L = p.socle.livre; d = S.dechets_id
    prod = L.flux["produit"].get("dechets", 0.0)
    aux_points = math.fsum(pt.stock[d] for pt in S.points)
    enfouis = math.fsum(x.stock[d] for x in S.decharges)
    return prod - S.c_collecte - aux_points, S.c_collecte - L.flux["consomme"].get("dechets", 0.0) - enfouis


def mesures_eau(p):
    """Consommation par habitant servi ( m3 par jour ), eau non facturee ( part du volume injecte )."""
    S = _sp(p)
    return (S.c_consomme_hab / max(EPS, S.c_hab_jours), 1.0 - S.c_facture_m3 / max(EPS, S.c_injecte))


# ================================================================== installation
def _declarer_biens(p):
    cat = p.socle.catalogue
    e = cat.declarer("eau_potable", "eau", "m3 d eau potable ( directive 2020/2184 )", PRIX_EAU_MONDE,
                     categorie_tva="reduite", masse_kg=1000.0, volume_l=1000.0,
                     source="prix : navire-citerne vers les iles grecques, 5 a 10 euros le m3 ( a calibrer )")
    d = cat.declarer("dechets", "matiere_premiere", "tonne de dechets municipaux en melange", PRIX_DECHETS,
                     categorie_tva="normale", masse_kg=1000.0, volume_l=3300.0,
                     source="prix : matieres triees ~ 20 euros la tonne ; 300 kg/m3 en conteneur ( a calibrer )")
    return e.id, d.id


def installer(p):
    w = p.w; L = p.socle.livre; T = p.domaine("territoire")
    S = ServicesPublics()
    p.domaines["services_publics"] = S
    S.eau_id, S.dechets_id = _declarer_biens(p)
    for m, nature in (("facture_eau", "achat"), ("exploitation_eau", "achat"), ("collecte_dechets", "achat"),
                      ("travaux_routiers", "achat"), ("carburant_services", "achat"),
                      ("dotation_communes", "transfert_courant"), ("subvention_regie_eau", "subvention"),
                      ("excedent_regie_eau", "transfert_courant")):
        L.declarer_motif(m, nature, "services_publics")
    for m in ("potabilisation", "fuites_reseau", "consommation_eau", "lutte_incendie", "production_dechets",
              "collecte_dechets", "recyclage"):
        L.declarer_motif(m, "achat", "services_publics")
    J = p.socle.journal
    for t, champs in (("route_fermee", ("troncon", "de", "vers", "cause")), ("route_rouverte", ("troncon", "de", "vers")),
                      ("coupure_eau", ("lieu", "part")), ("greve_collecte", ("ile", "jours")),
                      ("decharge_pleine", ("ile", "lieu", "tonnes"))):
        J.declarer(t, "services_publics", "individuel", champs)
    for t in ("eau_potable_m3", "eau_non_facturee_m3", "eaux_usees_non_traitees_m3", "dechets_collectes_t",
              "dechets_recycles_t", "chantier_routier", "convoi_ralenti", "facture_eau_impayee", "collecte_impossible"):
        J.declarer(t, "services_publics", "compte")
    cm = p.colonnes["menage"]
    for nom in ("sp_eau_du", "sp_eau_arrieres", "sp_eau_m3"): cm.ajouter(nom, np.float64, 0.0)
    cm.assurer(len(w.menages))
    from ..socle import biens as BI
    n = len(T.lieux)
    lieux = [w.carte.lieux[lid] for lid in T.lieux]
    # les detenteurs
    S.communes, S.regies, S.commune_ile, S.regie_ile = [], [], {}, {}
    S.decharges, S.decharge_ile = [], {}
    for i, ile in enumerate(T.iles):
        chef = T.capitale_ile[i] if T.capitale_ile[i] in w.carte.lieux else next(l.id for l in lieux if l.ile == ile)
        S.commune_ile[ile] = len(S.communes); S.communes.append(Commune(len(S.communes), ile, chef, BI.Stock()))
        S.regie_ile[ile] = len(S.regies); S.regies.append(RegieEau(len(S.regies), ile))
        S.decharge_ile[ile] = len(S.decharges); S.decharges.append(Decharge(ile, chef, BI.Stock(), 0.0))
    S.habitables = np.array([l.type in HABITABLES for l in lieux])
    S.points, S.point_lieu = [], np.full(n, -1, np.int64)
    for k in np.nonzero(S.habitables)[0].tolist():
        S.point_lieu[k] = len(S.points); S.points.append(PointDeCollecte(k, lieux[k].ile, BI.Stock()))
    B = T.bassins
    S.systemes, S.systeme_lieu = [], np.full(n, -1, np.int64)
    for b in range(len(B.nom)):
        ks = np.array([k for k in range(n) if T.lieu_bassin[k] == b and S.habitables[k]], np.int64)
        if not len(ks): continue
        for k in ks.tolist(): S.systeme_lieu[k] = len(S.systemes)
        S.systemes.append(SystemeEau(len(S.systemes), b, T.iles[int(B.ile[b])], B.nom[b], BI.Stock(), ks))
    E = S.eau = EauParLieu()
    E.hab = np.zeros(n); E.raccorde = np.array([1.0 if l.type in RACCORDES else 0.0 for l in lieux])
    E.phi = np.ones(n); E.manque7 = np.zeros((n, 7)); E.jours_sans_eau = np.zeros(n, np.int64)
    E.ecoli, E.turb, E.chim, E.nitrates = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    reg = p.socle.registre
    reg.inscrire("communes", "administrations", _membres_communes, "caisse", "stock", "Commune")
    reg.inscrire("regies_eau", "entreprises", _membres_regies, "caisse", None, "RegieEau")
    reg.inscrire("reseaux_eau", "entreprises", _membres_systemes, None, "stock", None)
    reg.inscrire("points_collecte", "administrations", _membres_points, None, "stock", None)
    reg.inscrire("decharges", "administrations", _membres_decharges, None, "stock", None)
    bq = p.domaine("banques")
    for x in S.communes + S.regies: BQ.ouvrir_compte(p, x, bq.banques[0])
    S.routes = _batir_routes(p, S)
    S.pluie7 = np.zeros((len(T.iles), 7))
    S.chantiers = {}; S.prochain_chantier = 0; S.notes = deque(maxlen=20000)
    S.vus_convois = w.n_convoi; S.c_ralentis = 0; S.coupures_e1 = 0; S.pont_convois = True
    S.c_capte = S.c_collecte = S.c_recycle = S.c_incendie = 0.0
    S.c_hab_jours = S.c_consomme_hab = S.c_injecte = S.c_facture_m3 = 0.0
    S.decideur = p.decideur(POINT_ENTRETIEN)
    _recenser(p)
    _trafic_voitures(p)                          # le trafic de reference de depart : celui des habitants
    S.routes.trafic_ref = S.routes.veh_jour.copy(); S.routes.veh_jour[:] = 0.0; S.routes.esal_jour[:] = 0.0
    # les camions-bennes, la decharge, les reservoirs, le premier remplissage
    S.modele_benne = p.socle.parc.declarer_modele(
        "camion_benne", "vehicule", 180000.0 * DR, 12000.0, 20000.0, arma="C_Truck_02_box_F",
        source="benne tasseuse de 26 t ~ 180 000 euros, 20 000 h de service ( a calibrer ) ; classname : Zamak du jeu de base")
    for c in S.communes:
        c.camions = max(1, int(math.ceil(c.pop / HAB_PAR_CAMION)))
        p.socle.parc.creer_cohorte(S.modele_benne, c, c.chef_lieu, c.camions, "initial")
        S.decharges[S.decharge_ile[c.ile]].capacite_t = DECHARGE_ANS * JOURS_AN * c.pop * DECHETS_T_HAB_J * (1 - PART_RECYCLEE)
    S.base_domestique = float(B.par_usage[:, TER.USAGES.index("domestique")].sum())
    TER.reprendre_usage(p, "domestique")
    for sy in S.systemes:
        sy.i_nom = float(E.hab[sy.lieux].sum()) * CONSO_M3_HAB_J / (1.0 - PERTES_REELLES)
        sy.capacite = max(10.0, RESERVOIR_J * sy.i_nom)
        sy.kwh_nom = sy.i_nom * KWH_M3_EAU + float((E.hab[sy.lieux] * E.raccorde[sy.lieux]).sum()) * CONSO_M3_HAB_J * RETOUR_EGOUT * KWH_M3_EPURATION
        brut = TER.prelever(p, sy.chef_lieu, sy.capacite / (1.0 - PERTE_TRAITEMENT), "domestique")
        S.c_capte += brut
        if brut > EPS: L.produire(sy.stock, S.eau_id, brut * (1.0 - PERTE_TRAITEMENT), "potabilisation")
    # l energie : un contrat prioritaire par systeme, l eclairage public a la commune
    S.contrats = []
    if p.a("energie"):
        from . import d11_energie as EN
        for sy in S.systemes:
            if sy.kwh_nom <= EPS: continue
            sy.contrat = f"eau@{sy.chef_lieu}"
            EN.abonner(p, sy.contrat, sy.chef_lieu, S.regies[S.regie_ile[sy.ile]], sy.kwh_nom / 24.0, prioritaire=True)
            S.contrats.append(sy.contrat)
        EN.reprendre_eclairage(p, S.communes[0])
    # l industrie : une commande permanente de ciment et d acier pour les chantiers qui rouvrent une route
    if p.a("industrie"):
        from . import d10_industrie as IND
        IND.commander(p, "ciment", 0.1); IND.commander(p, "acier", 0.01)
    # la dotation d ouverture : le coussin de dix jours de depenses estimees
    for c in S.communes:
        L.transferer(w.gouv, c, JOURS_COUSSIN * (equipe_cout(p, c.ile) + c.camions * 400.0), "dotation_communes")
    for r in S.regies:
        v = sum(sy.i_nom for sy in S.systemes if sy.ile == r.ile)
        L.transferer(w.gouv, r, JOURS_COUSSIN * max(100.0, v * (EXPLOITATION_M3 + EPURATION_M3)), "subvention_regie_eau")
    _eau(p)
    # l horloge
    p.routine(0 + 20 / 60, 50, "services_publics", _routes_minuit)
    p.routine(4 + 50 / 60, 50, "services_publics", _recenser)
    p.routine(5, 50, "services_publics", _eau)
    p.routine(5 + 50 / 60, 50, "services_publics", _coupures_e1)
    p.routine(7, 50, "services_publics", _equipes)
    p.routine(7 + 10 / 60, 50, "services_publics", _collecter)
    p.routine(21, 50, "services_publics", _produire_dechets)
    p.routine(23 + 40 / 60, 50, "services_publics", _soir)
    for h in range(24): p.routine(h, 30, "services_publics", _convois)
    return S
