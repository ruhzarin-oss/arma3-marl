"""DOMAINE 11 - ENERGIE : PETROLE ET GAZ, RAFFINAGE, ELECTRICITE ( PRODUCTION, RESEAU, STOCKAGE, PANNES, PRIX ).

FICHE
1. Classes. Les lois : Combustible ( masse, PCI, facteur de CO2, soufre d une unite du moteur ), Technologie ( rendement
   PCI, part a vide, minimum technique, demarrage, fiabilite, NOx, poussieres, eau ). Les objets et detenteurs :
   Unite ( un groupe : thermique, eolien, solaire, hydraulique ; son exemplaire au Parc ), Batterie ( Stock du socle en
   electricite ), Reservoir ( les cuves d un site : fioul, gaz, charbon, gazole importe ; et les produits de la
   raffinerie ), GestionnaireReseau ( le gestionnaire d une ile non interconnectee, sur le modele de HEDNO : caisse, Stock
   de l electricite en transit ), Charge ( une zone de delestage : un lieu habite, le puits ou la raffinerie, les sites
   du moteur d une ile, un contrat ), Gisement ( les reserves finies du puits ), ReseauIle ( un reseau d ile : groupes,
   charges, meteo de l heure, journal horaire, cumuls ), Energie ( l etat du domaine ). Deux adaptateurs ( StocksE1,
   ReseauE1 ) laissent le grand livre ecrire dans les dictionnaires du moteur. Colonnes par menage : en_du ( la facture
   qui court, drachmes ), en_arrieres ( l impaye ). Unites : 1 unite de liquide = 10 litres ( le gazole du moteur :
   0,03 unite par km = 30 l aux 100 km d un camion ), ~0,1 MWh PCI par unite de combustible, 1 unite d electricite = 10 kWh.
2. Invariants. BIENS : tout passe par le grand livre, sous des motifs de biens nommes ( extraction, oleoduc, raffinage,
   combustion_centrale, production_thermique, eolienne, solaire, hydraulique, charge et decharge de batterie, pertes du
   reseau et du stockage, consommations par categorie, livraison aux sites du moteur, livraison de combustible, import,
   export ). ENERGIE : pour chaque groupe thermique, combustible ( MJ PCI ) = electricite + chaleur perdue, et ce
   combustible est exactement celui que le grand livre a vu bruler ; pour chaque ile, heure par heure, production +
   decharge - charge = consommations + livraison aux sites + pertes ( 7 % de l injection ) ; le stock d une batterie est
   exactement ce que ses charges et decharges comptees y ont laisse. RAFFINERIE : masse de brut = coupes +
   autoconsommation + pertes, au kilogramme. ARGENT : chaque drachme passe par le grand livre sous un motif declare. Le
   domaine DETIENT l argent des gestionnaires ( famille gestionnaires_reseau ) et des biens ( gestionnaires_reseau,
   reservoirs_energie, batteries ) ; le puits, la raffinerie et les centrales restent des entreprises du moteur, dont le
   domaine 3 tient les comptes ( leur capital est reevalue a la valeur de leurs groupes ).
3. Decision `delestage_zone` ( chaque zone habitee, tous les 3 jours, decalees : un tiers des zones decide chaque jour,
   ~4 notes par action et par jour ) : aucun effacement, effacement leger ( -5 % sur les 5 heures de pointe prevues ),
   fort ( -15 % ). Une zone qui s efface passe apres les autres dans l ordre du delestage tournant. Traits : marge de
   capacite publiee, part du parc thermique en panne, energie non servie de l ile hier, heures delestees de CETTE zone
   sur 7 jours, chaleur d hier, autonomie en combustible, part residentielle de la zone, programme en cours. Note
   ( horizon 3 jours, la duree du programme ) : chaque jour, - ( energie non servie par delestage dans CETTE zone + 0,1 x
   energie qu elle a effacee ) / sa demande. Regle : fort si la marge est sous 1,05 ou si l ile a deleste plus de 1 % de
   sa demande hier ; leger sous 1,25, si un quart du thermique est en panne ou s il reste moins de 2 jours de
   combustible ; sinon aucun. Temoin : jamais d effacement. La conduite du reseau est une regle deterministe, pas un
   point de decision : engagement par ordre de merite avec reserve N-1 ( les groupes rapides a l arret et la batterie y
   comptent ), repartition ( minimum technique, limite de penetration du renouvelable 50 %, batterie en pointe, recharge
   de nuit par les groupes de base ), delestage tournant par depart entier ( l allocation des sites du moteur se reduit
   de ce qui manque ; le puits et la raffinerie, qui alimentent les centrales, sont proteges comme un hopital ).
4. Evenements. Individuels : panne_centrale, remise_en_service, delestage_electrique, coupure_ligne, gisement_en_declin.
   Comptes : energie_non_servie ( kWh ), ecretement ( kWh ), demarrage_groupe, import_combustible ( drachmes ),
   export_petrolier ( drachmes ), facture_impayee ( drachmes ), manque_combustible, manque_eau_energie ( m3 ).
5. Liens. Reprend du moteur ( p.reprendre ) le puits, la raffinerie et les centrales ; perd le stock du reseau E1, qui
   n etait pas physique, et le remplace par l allocation horaire des sites du moteur ( ReseauE1 ). Contourne, comme le
   domaine 9, un bogue de pays._neutraliser_repris ( voir _contourner_neutralisation ). Le brut du puits va par oleoduc
   a la raffinerie ( prix mondial ) ; le gazole raffine va aux stocks du moteur, qui le vend au marche ; les autres coupes
   vont aux cuves : fioul et gaz aux centrales, le reste exporte chaque soir au-dela de 3 jours de production ; le
   raffineur importe du gazole quand le prix de gros depasse la parite import et que le pays tombe sous 5 jours de
   demande ( les rendements reels, 39 % de gazole contre 80 % dans la recette du moteur, le laisseraient court ). Lit la
   meteo du territoire ( temperature, vent, ecart diurne, rayonnement extraterrestre ), ses catastrophes ( seismes et
   intensites, tempetes, cyclones, crues ) ; preleve son eau ( reprendre_usage « energie », prelever ) et rejette SO2,
   NO2, PM2,5, hydrocarbures par `rejeter` ; tient lui-meme l inventaire du CO2 ( le territoire n a pas de gaz a effet
   de serre ). Industrie ( s il est installe ) : lignite commande et livre par ses mines, son PCI lu dans son module ;
   ses ateliers soutirent l electricite comme charge interruptible. Economie : reevaluer_capital des centrales ; prix des
   marches et demande lissee du gazole. Banques :
   compte des gestionnaires ( ouvrir_compte ). Paie et recoit : factures au tarif reglemente du moteur ( menages tous
   les 30 jours, commerces, Etat, puits et raffinerie, contrats -> gestionnaire ) ; achat de l electricite des centrales
   ( gestionnaire -> centrale : combustible et exploitation + 10 %, et capacite ) ; compensation de service public
   ( Etat -> gestionnaire ) et redevance ( gestionnaire -> Etat ) ; reversement de ce que les sites du moteur ont paye a
   l Etat pour l electricite ; brut ( raffinerie -> puits ) ; fioul et gaz ( centrale -> raffinerie ) ; imports de
   combustible, exports de produits ; redevance petroliere ( puits -> Etat ). API ( fin de fichier ) : tarif,
   cout_marginal, abonner, resilier, servi, coupure_en_cours, soutirer, vendre_produit, livrer_combustible,
   stock_produit, prix_depart, reprendre_eclairage, forcer_panne, couper_ligne, bilan_electricite, bilan_combustion,
   bilan_raffinerie, emissions, resume_jour.
6. Portes : tests_d11_energie.py.
7. Arma. Groupes diesel : Land_dp_mainFactory_F et Land_dp_smallFactory_F ( la centrale diesel d Altis ) ; tranche
   vapeur : Land_Factory_Main_F ; eoliennes : Land_wpp_Turbine_V2_F ; panneaux : Land_spp_Panel_F ; batterie en
   conteneurs : Land_Cargo20_grey_F. arma_preuve = None : rien n a ete vu vivre en jeu.
8. Cout. Tout est par ile, par zone ( lieu ), par groupe : le cout horaire ne suit PAS la population. Seuls le recensement
   des menages par zone ( une passe par jour ), la facture ( vectorisee, un paiement par menage et par mois ) et le
   compte des ouvriers presents ( index du moteur ) la touchent. Mesure du 23/09 ( test_cout, 10 000 habitants ) :
   ~23 ms par jour, 1,3 % d une journee du moteur."""
import importlib, math
from collections import deque
import numpy as np
from .. import config as C
from .. import population as PO
from ..socle import decision as D, objets as O, calendrier as CAL, biens as BI
from . import d02_banques as BQ, d03_economie as ECO, d08_territoire as TER

JOURS_AN = 365.0
PAS_H = C.PAS_PAR_JOUR // 24          # pas de 10 minutes par heure
EPS = 1e-9

# ================================================================== les unites du moteur, en unites reelles
# Le moteur compte le carburant en unites : 0,03 unite par km et par vehicule ( config.CARBURANT_PAR_KM ). Un convoi
# est un camion : un poids lourd brule 30 a 35 l aux 100 km. Une unite de carburant vaut donc 10 litres de gazole.
# On garde cette unite de 10 litres pour tous les liquides ( brut, essence, kerosene, fioul ) : a 9 drachmes l unite,
# le gazole du moteur est a 0,9 drachme le litre ( gazole mondial ~0,58 euro plus l accise grecque ~0,41 ), le brut a
# 5 drachmes les 10 litres, soit ~80 euros ( 86 dollars ) le baril : 1 drachme ~ 1 euro. Une unite de gaz est la masse de gaz qui porte
# la meme energie, a peu pres : 7,5 kg ( ~10 Nm3 de gaz naturel ). Chaque unite de combustible porte ainsi ~0,1 MWh PCI.
# L electricite : 1 unite = 10 kWh. PRIX_MONDE["electricite"] = 1 drachme = 100 euros le MWh ( prix de gros grec,
# ordre de grandeur ) ; le tarif du moteur ( ~1,8 drachme ) vaut 0,18 euro le kWh ( tarif reglemente grec ).
KWH_UNITE = 10.0
MJ_KWH = 3.6
LITRES_UNITE = 10.0


class Combustible:
    """Une unite de combustible du moteur, en grandeurs reelles.
      masse_kg   la masse d une unite ( 10 litres x la masse volumique ; 7,5 kg pour le gaz )
      pci        pouvoir calorifique inferieur, MJ/kg ( GIEC 2006, vol. 2, chap. 1, tableau 1.2 )
      co2        facteur d emission, t de CO2 par TJ PCI ( meme source, tableau 1.4 )
      soufre     teneur massique en soufre ( fioul lourd 1 %, gazole de centrale 0,1 % : directive 2016/802/UE )"""
    __slots__ = ("bien", "masse_kg", "pci", "co2", "soufre", "source")

    def __init__(self, bien, masse_kg, pci, co2, soufre, source):
        if not 0.0 < masse_kg <= 1e5 or not 5.0 <= pci <= 60.0 or not 0.0 < co2 <= 120.0 or not 0.0 <= soufre < 0.1:
            raise ValueError(f"combustible {bien} hors bornes")
        self.bien, self.masse_kg, self.pci, self.co2, self.soufre, self.source = bien, float(masse_kg), float(pci), float(co2), float(soufre), source

    def mj(self): return self.masse_kg * self.pci


_GIEC = "GIEC 2006 vol. 2 chap. 1 ( PCI tableau 1.2, CO2 tableau 1.4 )"
COMBUSTIBLES = {
    "petrole": Combustible("petrole", 8.6, 42.3, 73.3, 0.010, f"brut 0,86 kg/l ( melanges Oural et Arabe leger ) ; {_GIEC}"),
    "carburant": Combustible("carburant", 8.4, 43.0, 74.1, 0.001, f"gazole 0,84 kg/l ; {_GIEC} ; 0,1 % S ( gazole de centrale )"),
    "essence": Combustible("essence", 7.45, 44.3, 69.3, 0.00001, f"essence 0,745 kg/l ( EN 228, 10 ppm S ) ; {_GIEC}"),
    "kerosene": Combustible("kerosene", 8.0, 44.1, 71.5, 0.0003, f"Jet A-1 0,80 kg/l ; {_GIEC}"),
    "fioul": Combustible("fioul", 9.7, 40.4, 77.4, 0.010, f"fioul lourd 0,97 kg/l, 1 % S ( directive 2016/802 ) ; {_GIEC}"),
    "gaz": Combustible("gaz", 7.5, 48.0, 56.1, 0.0, f"gaz naturel ou gaz de raffinerie, 7,5 kg ~ 10 Nm3 ; {_GIEC}"),
}
# Le charbon est celui du domaine 10 : du lignite grec ( PCI 5,5 MJ/kg, 101 t de CO2 par TJ, soufre 1 % ), lu dans son
# module quand il est installe ( CHARBON_PCI_MJ_KG, CHARBON_CO2_T_TJ, CHARBON_SOUFRE ) ; ces valeurs par defaut sinon.
# Le lignite n a pas de marche mondial : il vient des mines du domaine 10 ( commander, livrer_combustible ), jamais
# de l import.
CHARBON = (5.5, 101.0, 0.010)
# Prix mondiaux, drachmes par unite, sur une meme base 2024 ( Brent 80 dollars le baril, 1 euro = 1,08 dollar ; a calibrer,
# domaine 7 ) : Eurobob ~800 dollars la tonne, Jet ~790, fioul 1 % S ~520, TTF ~35 euros le MWh. Le brut du moteur
# ( 5 drachmes les 10 litres ) et ces prix donnent une marge brute de raffinage de ~8 dollars le baril ( marges complexes
# mediterraneennes 2023-2024 : 5 a 12 ). Le gazole du moteur ( 9 drachmes ) est au-dessus du gazole mondial ( ~5,8 ) : il
# porte l equivalent des accises grecques ( ~0,4 euro le litre ).
PRIX_NOUVEAUX = {"gaz": 3.5, "essence": 5.5, "kerosene": 5.9, "fioul": 4.7}
UNITES_NOUVEAUX = {
    "gaz": ("energie", "7,5 kg de gaz combustible ( ~10 Nm3 de gaz naturel, ~0,1 MWh PCI )", 7.5, 10000.0),
    "essence": ("energie", "10 litres d essence sans plomb ( EN 228 ), 7,45 kg", 7.45, 10.0),
    "kerosene": ("energie", "10 litres de kerosene ( Jet A-1 ), 8,0 kg", 8.0, 10.0),
    "fioul": ("energie", "10 litres de fioul lourd ( 1 % S ), 9,7 kg", 9.7, 10.0)}

# ================================================================== le puits et la raffinerie
# Rendements massiques d une raffinerie a hydrocraqueur ( ordre de grandeur des raffineries grecques, riches en
# distillats moyens ; a calibrer ). En volume : gazole 38,9 %, essence 24,2 %, kerosene 9,7 %, fioul 18,6 %.
RENDEMENTS = (("gaz", 0.03), ("essence", 0.21), ("kerosene", 0.09), ("carburant", 0.38), ("fioul", 0.21))
AUTOCONSOMMATION = 0.065              # gaz et coke brules dans les fours de la raffinerie
PERTES_RAFFINAGE = 0.015              # torche, evaporation
if abs(sum(r for _, r in RENDEMENTS) + AUTOCONSOMMATION + PERTES_RAFFINAGE - 1.0) > 1e-12:
    raise ValueError("raffinerie : les coupes, l autoconsommation et les pertes ne font pas 100 % du brut")
PCI_GAZ_RAFFINERIE, CO2_GAZ_RAFFINERIE = 49.5, 57.6   # GIEC 2006 ( gaz de raffinerie )
DEBIT_OUVRIER_H = C.RECETTES["raffinerie"][1]["petrole"]   # unites de brut par ouvrier et par heure : la productivite du
PETROLE_PETROLIER_H = C.RECETTES["puits"][2]["petrole"]    # moteur ( une vraie raffinerie en traite 50 fois plus )
ELEC_RAFFINAGE_KWH_T = 60.0           # kWh par tonne de brut ( a calibrer : BREF raffinage, ordre de grandeur )
EAU_RAFFINAGE_M3_T = 0.6              # eau douce par tonne de brut ( BREF : 0,1 a 1,2 m3/t, a calibrer )
EMIS_RAFFINAGE_KG_T = (("so2", 0.30), ("no2", 0.25), ("pm25", 0.02), ("hydrocarbures", 0.002))   # a calibrer ( E-PRTR )
ELEC_PUITS_KWH = 0.2                  # kWh par unite de brut remontee ( 20 kWh/m3, pompage et separation, a calibrer )
EAU_PUITS_M3 = 0.0005                 # m3 par unite ( a calibrer )
EMIS_PUITS_KG = (("hydrocarbures_sol", 0.002),)   # kg par unite ( valeur de fond du territoire, a calibrer )
REDEVANCE_HYDROCARBURES = 0.07        # part de la valeur du brut ( loi grecque 2289/1995 : bareme de 2 a 20 %, a calibrer )
RESERVES_ANNEES = 12.0                # reserves restantes en annees de production nominale ( Prinos, Kavala : R/P ~10 ans )
PART_DECLIN = 0.35                    # sous 35 % des reserves de depart, le debit decroit avec ce qui reste ( declin exponentiel )
CUVES_J = 30                          # capacite des cuves de la raffinerie, en jours de production nominale
CUVE_BRUT_J = 5                       # le brut du puits arrive par oleoduc dans une cuve de 5 jours de traitement nominal
STOCK_TAMPON_J = 3                    # la raffinerie garde 3 jours de sa production recente et exporte le reste chaque soir
DECOTE_EXPORT = 0.03                  # transport jusqu au client etranger
FRET_IMPORT = 0.08                    # fret et assurance d un combustible importe
COUVERTURE_GAZOLE_J = 5               # le raffineur importe du gazole quand les stocks du pays tombent sous 5 jours de demande
IMPORT_GAZOLE_MAX_J = 3               # ... au plus 3 jours de demande par jour, quand le prix de gros depasse la parite import

# ================================================================== les technologies
class Technologie:
    """Une filiere de production thermique.
      rendement     rendement electrique net a pleine charge, PCI
      part_a_vide   part du combustible de pleine charge brulee a puissance nulle : la courbe de consommation est
                    lineaire ( a vide + increment ), le rendement baisse a charge partielle
      pmin          minimum technique, en part de la puissance ; demarrage_h : delai de demarrage ; duree_min_h : duree
                    minimale de marche
      mtbf_h, mttr_h  heures de marche entre deux pannes, heures de reparation ( taux de panne force = mttr / ( mtbf + mttr ) )
      nox, pm25     g par kWh electrique ; eau : m3 d eau douce par MWh ; om : drachmes par MWh ; capital : drachmes par kW"""
    __slots__ = ("nom", "combustibles", "rendement", "part_a_vide", "pmin", "demarrage_h", "duree_min_h", "mtbf_h",
                 "mttr_h", "nox", "pm25", "eau", "om", "capital", "vie_ans", "modele", "arma", "source")

    def __init__(self, nom, combustibles, rendement, part_a_vide, pmin, demarrage_h, duree_min_h, mtbf_h, mttr_h, nox,
                 pm25, eau, om, capital, vie_ans, modele, arma, source):
        if not 0.2 <= rendement <= 0.65 or not 0.0 <= part_a_vide < 0.5 or not 0.0 < pmin < 1.0:
            raise ValueError(f"technologie {nom} hors bornes")
        if demarrage_h < 0 or duree_min_h < 1 or mtbf_h <= 0 or mttr_h <= 0 or nox < 0 or pm25 < 0 or eau < 0:
            raise ValueError(f"technologie {nom} hors bornes")
        self.nom, self.combustibles, self.rendement, self.part_a_vide, self.pmin = nom, tuple(combustibles), rendement, part_a_vide, pmin
        self.demarrage_h, self.duree_min_h, self.mtbf_h, self.mttr_h = int(demarrage_h), int(duree_min_h), float(mtbf_h), float(mttr_h)
        self.nox, self.pm25, self.eau, self.om, self.capital, self.vie_ans = nox, pm25, eau, om, capital, vie_ans
        self.modele, self.arma, self.source = modele, arma, source


THERMIQUES = {
    "diesel_fioul": Technologie(
        "diesel_fioul", ("fioul",), 0.43, 0.12, 0.40, 1, 4, 1500, 48, 12.0, 0.40, 0.10, 10.0, 1100.0, 25,
        "groupe_diesel_fioul", "Land_dp_mainFactory_F",
        "moteurs semi-rapides au fioul lourd des iles grecques : 44-46 % aux bornes ( fiches Wartsila 32/46 ), ~43 % net ; "
        "NOx IMO Tier I ; fiabilite ordre de grandeur NERC GADS ; a calibrer"),
    "diesel_gazole": Technologie(
        "diesel_gazole", ("carburant",), 0.38, 0.10, 0.30, 0, 1, 1200, 24, 10.0, 0.15, 0.05, 12.0, 600.0, 20,
        "groupe_diesel_gazole", "Land_dp_smallFactory_F",
        "groupes rapides au gazole : 36-40 % ; demarrage en minutes ; a calibrer"),
    "turbine_gaz": Technologie(
        "turbine_gaz", ("gaz", "carburant"), 0.35, 0.25, 0.50, 0, 1, 1000, 72, 3.0, 0.05, 0.05, 8.0, 700.0, 25,
        "turbine_a_gaz", "Land_dp_smallFactory_F",
        "turbine aeroderivee en cycle ouvert, bicombustible : 33-38 % ( IEA ETSAP E02 ) ; a calibrer"),
    "vapeur_charbon": Technologie(
        "vapeur_charbon", ("charbon",), 0.36, 0.15, 0.40, 8, 12, 1200, 100, 2.0, 0.10, 0.20, 6.0, 1800.0, 35,
        "tranche_vapeur_charbon", "Land_Factory_Main_F",
        "tranche sous-critique au lignite : 33-39 % ( IEA ETSAP E01 ; tranches de PPC a Ptolemaida 32-41 % ) ; refroidissement "
        "a l eau de mer, eau douce d appoint ; a calibrer"),
}
# Le parc thermique d une ile : ( technologie, nombre de groupes, part de la puissance thermique par groupe ). Somme 1.
MIX_THERMIQUE = (("diesel_fioul", 3, 0.20), ("diesel_gazole", 2, 0.12), ("turbine_gaz", 1, 0.16))
# Une ile sans centrale ni raffinerie : une station au port, au gazole, comme les petites iles grecques ( Agios
# Efstratios, Kastellorizo ) ; le fioul lourd demande des cuves chauffees et une raffinerie ou un terminal.
MIX_PETITE_ILE = (("diesel_gazole", 3, 0.25), ("turbine_gaz", 1, 0.25))
MARGE_THERMIQUE = 1.35                # puissance thermique installee sur la pointe estimee ( critere N-1 des iles, a calibrer )
PART_EOLIEN, PART_SOLAIRE = 0.25, 0.30   # puissance installee sur la pointe ( ~20 % d energie renouvelable, a calibrer )
PART_BATTERIE, DUREE_BATTERIE_H = 0.15, 2.0
# Eolien : courbe de puissance d une machine de 2 MW ( demarrage 3 m/s, nominale 13 m/s, coupure 25 m/s ), moyeu a 80 m,
# cisaillement en loi de puissance d exposant 1/7 ; variation horaire du vent : AR(1) log-normal et brise diurne ( a calibrer ).
V_DEMARRAGE, V_NOMINALE, V_COUPURE = 3.0, 13.0, 25.0
H_MOYEU, ALPHA_CISAILLEMENT = 80.0, 1.0 / 7.0
SIGMA_VENT_H, PHI_VENT_H, BRISE = 0.25, 0.8, 0.15
# Solaire : rayonnement global du jour par Hargreaves ( FAO-56 eq. 50, kRs = 0,19 sur une ile ), plafonne au ciel clair
# ( 0,75 Ra ) ; reparti dans la journee selon la hauteur du soleil ; rapport de performance 0,80 ( IEC 61724 : 0,75-0,85 ).
KRS, CIEL_CLAIR, PR_SOLAIRE = 0.19, 0.75, 0.80
# Batterie lithium-ion : rendement aller-retour 0,88 ( NREL ATB 2023 : 85-90 % ), charge minimale 10 %.
RENDEMENT_BATTERIE, SOC_MIN, SOC_NUIT_MAX = 0.88, 0.10, 0.90
ETA_CH = ETA_DE = math.sqrt(RENDEMENT_BATTERIE)
# Hydraulique : une retenue sert une turbine si elle peut tourner 1000 heures par an ; chute 40 m, rendement 0,85.
CHUTE_M, RENDEMENT_HYDRO, HEURES_HYDRO, HYDRO_MIN_KW = 40.0, 0.85, 1000.0, 20.0
RENOUVELABLES = {   # genre : ( mtbf, mttr, capital drachmes par kW, vie, modele, arma, masse kg du MW de reference, source )
    "eolien": (2000.0, 60.0, 1300.0, 20, "parc_eolien", "Land_wpp_Turbine_V2_F", 250000.0, "disponibilite ~97 % ( a calibrer )"),
    "solaire": (5000.0, 48.0, 700.0, 25, "parc_solaire", "Land_spp_Panel_F", 60000.0, "disponibilite ~99 % ( a calibrer )"),
    "hydro": (3000.0, 72.0, 2500.0, 40, "turbine_hydraulique", None, 50000.0, "a calibrer"),
    "batterie": (4000.0, 48.0, 600.0, 15, "batterie_stationnaire", "Land_Cargo20_grey_F", 20000.0,
                 "600 drachmes par kW pour 2 h ( NREL ATB 2023, ordre de grandeur ) ; a calibrer")}

# ================================================================== la demande
# Consommation par habitant hors chauffage et climatisation ( Grece : ~1 700 kWh par habitant et par an pour les
# menages, ~1 450 pour le tertiaire, Eurostat ; la part climatique est ajoutee par la temperature ; a calibrer ).
E_RES_KWH_HAB_J = 3.7
E_TER_KWH_HAB_J = 3.2
W_ECLAIRAGE_HAB = 11.0                # W par habitant, de la tombee de la nuit a l aube ( ~1 % de la consommation, a calibrer )
# Formes des courbes de charge ( ordre de grandeur des courbes horaires grecques, ADMIE et HEDNO ; a calibrer ) :
# residentiel : creux a 4 h, reprise du matin, pic du soir a 20-21 h ; tertiaire : journee de 8 h a 20 h.
PROFIL_RES = np.array((0.75, 0.62, 0.55, 0.52, 0.52, 0.55, 0.68, 0.90, 1.00, 0.98, 0.95, 0.95, 0.98, 1.02, 1.00, 0.95,
                       0.95, 1.05, 1.25, 1.45, 1.60, 1.62, 1.45, 1.10))
PROFIL_TER = np.array((0.45, 0.42, 0.40, 0.40, 0.40, 0.45, 0.55, 0.80, 1.10, 1.30, 1.40, 1.45, 1.45, 1.42, 1.38, 1.35,
                       1.30, 1.30, 1.30, 1.25, 1.15, 0.95, 0.70, 0.55))
PROFIL_RES = PROFIL_RES / PROFIL_RES.mean()
PROFIL_TER = PROFIL_TER / PROFIL_TER.mean()
TER_SAMEDI, TER_REPOS, RES_REPOS = 0.85, 0.65, 1.05
# Sensibilite a la temperature : +3,5 % par degre au-dessus de 24 degres ( climatisation ), +2 % par degre sous 16 degres
# ( pompes a chaleur, radiateurs ) : ordre de grandeur des etudes de la demande grecque ( a calibrer ). Temperature
# horaire : sinusoide entre tmin ( 3 h ) et tmax ( 15 h ).
K_FROID, T_FROID, K_CHAUD, T_CHAUD, HEURE_TMAX = 0.035, 24.0, 0.02, 16.0, 15
PART_COMMERCE = 0.6                   # part du tertiaire payee par le commerce ( marches ), le reste par l Etat
PERTES_RESEAU = 0.07                  # transport et distribution des iles non interconnectees ( HEDNO, RAE : 7-9 % )
PENETRATION_MAX = 0.5                 # part maximale de la demande servie par l eolien et le solaire ( stabilite, a calibrer )
RESERVE_MIN = 0.10
HEURES_POINTE = 5                     # la pointe : les 5 heures de plus forte demande prevue du jour ( effacement, batterie )
NUIT_H = (0, 1, 2, 3, 4, 5)           # recharge de la batterie par les groupes de base
CHARGE_NUIT_COUT = 1.2                # ... seulement avec les groupes dont le cout est a moins de 20 % du moins cher
FACTEUR_CHARGE = 0.6                  # pour dimensionner les stocks de combustible
JOURS_STOCK, JOURS_MINI = 5.0, 2.0

# ================================================================== la decision
ACTIONS_DELESTAGE = ("aucun", "leger", "fort")
EFFACEMENT = (0.0, 0.05, 0.15)
KAPPA_EFFACEMENT = 0.1                # un kWh efface sur preavis coute un dixieme d un kWh coupe sans preavis ( remuneration
                                      # de l effacement ~0,1-0,5 euro le kWh contre 5-20 euros de valeur de l energie non servie )
JOURS_PROGRAMME = 3
HORIZON_DELESTAGE = 3

# ================================================================== les prix et l argent
MARGE_PRODUCTEUR = 0.10               # le gestionnaire paie aux centrales leur cout variable + 10 % ( cout plus marge des iles )
CAPACITE_DR_KW_AN = 120.0             # paiement de capacite ( cout fixe des centrales des iles ~100-150 euros par kW et par an )
VOLL_DR_KWH = 10.0                    # valeur de l energie non servie ( a calibrer : 5-20 euros le kWh, ACER )
JOURS_FACTURE = 30                    # un menage recoit sa facture tous les 30 jours ( decale par menage )
FONDS_ROULEMENT_J, PLAFOND_CAISSE_J, DOTATION_J = 7, 15, 7

# ================================================================== les catastrophes et le reseau
MMI_LIGNE = (7.0, 0.7)                # fragilite des lignes et postes : P = Phi( ( MMI - 7 ) / 0,7 ) ( a calibrer, HAZUS )
MMI_CENTRALE = (7.5, 0.7)
VENT_TEMPETE, PENTE_TEMPETE = 13.0, 0.03   # vent moyen du jour au-dela de 13 m/s ( rafales > 80 km/h ) : +3 % par m/s
P_CYCLONE_CAT, P_CRUE = 0.15, 0.10
REPARATION_J = (1, 4)
MTTR_SEISME_H = 72

NOMS_TECH = ("diesel_fioul", "diesel_gazole", "turbine_gaz", "vapeur_charbon", "eolien", "solaire", "hydro")
ZONE, SITE, MOTEUR, CONTRAT = 0, 1, 2, 3


# ================================================================== fonctions pures ( testables seules )
def phi(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def irradiation_jour(ra_mm, dtr):
    """Rayonnement global du jour sur le plan horizontal, kWh/m2 : Hargreaves ( FAO-56 eq. 50 ) Rs = kRs x racine( tmax -
    tmin ) x Ra, plafonne au ciel clair. `ra_mm` : rayonnement extraterrestre en mm d eau evaporable ( territoire )."""
    ra = ra_mm / 0.408                                          # MJ/m2/j
    rs = min(KRS * math.sqrt(max(0.0, dtr)) * ra, CIEL_CLAIR * ra)
    return rs / MJ_KWH


def profil_solaire(latitude, jour_an, lever, coucher, rs_kwh):
    """L eclairement moyen de chaque heure ( W/m2 ), dont la somme sur 24 h redonne `rs_kwh` : la hauteur du soleil,
    integree sur six instants par heure, entre le lever et le coucher."""
    decl = math.radians(23.45) * math.sin(2 * math.pi * (284 + jour_an) / 365)
    phi_ = math.radians(latitude)
    midi = (lever + coucher) / 2.0
    t = np.arange(24 * 6) / 6.0 + 1.0 / 12.0
    s = math.sin(phi_) * math.sin(decl) + math.cos(phi_) * math.cos(decl) * np.cos(np.radians(15.0 * (t - midi)))
    s = np.where((t >= lever) & (t < coucher), np.maximum(s, 0.0), 0.0)
    par_h = s.reshape(24, 6).mean(axis=1)
    tot = par_h.sum()
    return par_h * (rs_kwh * 1000.0 / tot) if tot > 0 else np.zeros(24)


def puissance_eolienne(v_moyeu):
    """Part de la puissance nominale d une eolienne a la vitesse `v_moyeu` ( m/s ) : cubique entre le demarrage et la
    vitesse nominale, pleine jusqu a la coupure."""
    v = np.asarray(v_moyeu, float)
    cube = (v ** 3 - V_DEMARRAGE ** 3) / (V_NOMINALE ** 3 - V_DEMARRAGE ** 3)
    return np.where(v < V_DEMARRAGE, 0.0, np.where(v < V_NOMINALE, cube, np.where(v < V_COUPURE, 1.0, 0.0)))


def mj_combustible(tech, pmax_kw, e_kwh):
    """Le combustible ( MJ PCI ) d une heure de marche a `e_kwh` : courbe lineaire a vide + increment, egale a
    pmax / rendement a pleine charge."""
    return MJ_KWH * (tech.part_a_vide * pmax_kw + (1.0 - tech.part_a_vide) * e_kwh) / tech.rendement


def emax_combustible(tech, pmax_kw, mj_dispo):
    """La plus forte production d une heure que `mj_dispo` permet."""
    return min(pmax_kw, (mj_dispo * tech.rendement / MJ_KWH - tech.part_a_vide * pmax_kw) / (1.0 - tech.part_a_vide))


def repartir(besoin, unites, res_dispo, batt, pointe, nuit, pen_max=PENETRATION_MAX):
    """La repartition d une heure, par ordre de merite. `besoin` : kWh a injecter dans le reseau ; `unites` : ( pmin,
    pmax, cout incremental ) des groupes thermiques en ligne, pmax deja borne par le combustible ; `res_dispo` : kWh
    eoliens, solaires et hydrauliques disponibles ; `batt` : ( charge maximale, decharge maximale ) en kWh cote reseau.
    Les groupes tournent au moins a leur minimum ; le renouvelable sert la demande jusqu a sa limite de penetration,
    son surplus charge la batterie, le reste est ecrete ; la batterie se decharge en pointe ( elle remplace le groupe le
    plus cher ) ou quand les groupes manquent ; la nuit, les groupes de base la rechargent.
    Rend ( sorties, renouvelable produit, ecrete, charge, decharge, manque, surplus ) : injection nette = besoin - manque
    + surplus ( un surplus : le minimum des groupes depasse la demande, il faut en arreter un )."""
    n = len(unites)
    sorties = [u[0] for u in unites]
    t_min = sum(sorties)
    ch_max, de_max = batt
    res_charge = min(res_dispo, max(0.0, pen_max * besoin), max(0.0, besoin - t_min))
    reste = besoin - t_min - res_charge
    charge = decharge = surplus = 0.0
    if reste < 0.0:
        charge = min(-reste, ch_max)
        surplus = -reste - charge
        reste = 0.0
    res_bat = max(0.0, min(res_dispo - res_charge, ch_max - charge))
    charge += res_bat
    res_util = res_charge + res_bat
    ordre = sorted(range(n), key=lambda k: (unites[k][2], k))
    if reste > 0.0:
        marge = sum(u[1] - u[0] for u in unites)
        if charge <= 0.0 and de_max > 0.0:
            if pointe: decharge = min(de_max, reste)
            elif marge < reste: decharge = min(de_max, reste - marge)
        reste -= decharge
        for k in ordre:
            if reste <= 0.0: break
            add = min(unites[k][1] - unites[k][0], reste)
            if add > 0.0: sorties[k] += add; reste -= add
    manque = max(0.0, reste)
    if nuit and n and decharge <= 0.0 and charge < ch_max and manque <= 0.0:
        base = min(u[2] for u in unites) * CHARGE_NUIT_COUT
        for k in ordre:
            if unites[k][2] > base: continue
            add = min(unites[k][1] - sorties[k], ch_max - charge)
            if add > 0.0: sorties[k] += add; charge += add
    return sorties, res_util, res_dispo - res_util, charge, decharge, manque, surplus


def verifier_courbe(charge_h):
    """Une courbe de charge d un jour doux est-elle grecque ? Pic entre 18 h et 22 h, creux entre 1 h et 6 h, pic au
    moins 1,3 fois le creux. Rend ( ok, heure du pic, heure du creux, rapport )."""
    c = np.asarray(charge_h, float)
    hp, hc = int(np.argmax(c)), int(np.argmin(c))
    r = float(c[hp] / max(1e-9, c[hc]))
    return (18 <= hp <= 22 and 1 <= hc <= 6 and r >= 1.3), hp, hc, r


def verifier_solaire(prod_h, irr_h, cap_kw, libre=None):
    """Une serie solaire suit-elle l eclairement ? Production nulle quand l eclairement est nul, egale a capacite x
    eclairement x rapport de performance aux heures `libre` ( non ecretees : toutes par defaut ), a 1e-9 pres, pic a
    moins d une heure du pic de l eclairement. Rend ( ok, pire ecart relatif, ecart des pics en heures )."""
    p_, g = np.asarray(prod_h, float), np.asarray(irr_h, float)
    m = np.ones(len(g), bool) if libre is None else np.asarray(libre, bool)
    attendu = cap_kw * g / 1000.0 * PR_SOLAIRE
    ecart = float(np.max(np.abs(p_ - attendu)[m]) / max(1e-9, attendu.max())) if m.any() else 0.0
    dpic = abs(int(np.argmax(p_)) - int(np.argmax(g))) if g.max() > 0 else 0
    nuit_propre = bool(np.all(p_[g <= 0] <= 1e-12))
    return (ecart <= 1e-9 and dpic <= 1 and nuit_propre), ecart, dpic


# ================================================================== les classes
class StocksE1:
    """Un dictionnaire de stocks du moteur ( nom -> quantite ) vu comme un stock du socle ( identifiant -> quantite ) :
    le grand livre y ecrit ses sources, ses puits et ses deplacements, avec leur motif."""
    __slots__ = ("d", "noms")

    def __init__(self, d, noms): self.d, self.noms = d, noms

    def _ajouter(self, b, q):
        n = self.noms[b]; self.d[n] = self.d.get(n, 0.0) + q

    def _retirer(self, b, q):
        n = self.noms[b]; dispo = self.d.get(n, 0.0)
        q = min(q, dispo)
        if not q > 0.0: return 0.0
        self.d[n] = dispo - q
        return q


class ReseauE1:
    """Le reseau du moteur ( w.reseau.stock ) vu comme un stock du socle en electricite : l allocation de l heure des
    sites du moteur, qui y puisent a chaque pas."""
    __slots__ = ("r",)

    def __init__(self, r): self.r = r

    def _ajouter(self, b, q): self.r.stock += q

    def _retirer(self, b, q):
        q = min(q, self.r.stock)
        if not q > 0.0: return 0.0
        self.r.stock -= q
        return q


class GestionnaireReseau:
    """Le gestionnaire du reseau d une ile ( HEDNO pour les iles grecques non interconnectees ) : il achete l electricite
    des centrales, la vend au tarif reglemente, recoit la compensation de service public de l Etat. Son stock :
    l electricite de l heure en transit ( nul entre deux heures )."""
    __slots__ = ("nom", "ile", "caisse", "stock")

    def __init__(self, ile, stock):
        self.nom, self.ile, self.caisse, self.stock = f"gestionnaire@{ile}", ile, 0.0, stock


class Reservoir:
    """Les cuves d un site : fioul, gaz, charbon, gazole importe ( le gazole des centrales du moteur reste dans leurs
    stocks, que le moteur approvisionne ). Proprietaire : l entreprise du site ou le gestionnaire."""
    __slots__ = ("nom", "lieu", "ile", "proprietaire", "stock")

    def __init__(self, nom, lieu, ile, proprietaire, stock):
        self.nom, self.lieu, self.ile, self.proprietaire, self.stock = nom, lieu, ile, proprietaire, stock


class Batterie:
    """Un stockage d electricite : son Stock du socle ( unites de 10 kWh ) est l energie stockee."""
    __slots__ = ("nom", "ile", "lieu", "p_kw", "e_kwh", "stock", "el", "objet", "en_panne", "panne_jusqu", "mtbf", "mttr",
                 "c_charge", "c_decharge", "c_pertes", "col")

    def __init__(self, nom, ile, lieu, p_kw, e_kwh, stock, el, objet, col):
        if not p_kw > 0 or not e_kwh > 0: raise ValueError("batterie : puissance et energie positives")
        self.nom, self.ile, self.lieu, self.p_kw, self.e_kwh, self.stock, self.objet = nom, ile, lieu, p_kw, e_kwh, stock, objet
        self.el = el
        g = RENOUVELABLES["batterie"]
        self.mtbf, self.mttr = g[0], g[1]
        self.en_panne, self.panne_jusqu = False, 0
        self.c_charge = self.c_decharge = self.c_pertes = 0.0
        self.col = col


class Unite:
    """Un groupe de production. genre : thermique, eolien, solaire, hydro. Compteurs cumules ( c_ ) et du jour ( j_ ) :
    MJ de combustible, kWh, chaleur perdue, heures, cout du combustible ( drachmes, au prix du jour )."""
    __slots__ = ("id", "ile", "genre", "tech", "pmax", "lieu", "entreprise", "reservoir", "proprietaire", "objet", "valeur",
                 "en_ligne", "pret_a", "depuis", "en_panne", "panne_jusqu", "mtbf", "mttr", "col", "bassin",
                 "c_mj", "c_kwh", "c_perte_mj", "c_heures", "c_pleine_h", "c_mj_pleine", "c_kwh_pleine", "c_demarrages",
                 "c_pannes", "c_unites", "j_kwh", "j_cout", "j_mj", "sortie_h")

    def __init__(self, id, ile, genre, tech, pmax, lieu, entreprise, reservoir, proprietaire, objet, valeur, col):
        if not pmax > 0: raise ValueError("unite : puissance positive")
        self.id, self.ile, self.genre, self.tech, self.pmax, self.lieu = id, ile, genre, tech, float(pmax), lieu
        self.entreprise, self.reservoir, self.proprietaire, self.objet, self.valeur = entreprise, reservoir, proprietaire, objet, valeur
        self.en_ligne, self.pret_a, self.depuis, self.en_panne, self.panne_jusqu = False, -1, 0, False, 0
        if genre == "thermique": self.mtbf, self.mttr = tech.mtbf_h, tech.mttr_h
        else: self.mtbf, self.mttr = RENOUVELABLES[genre][0], RENOUVELABLES[genre][1]
        self.col, self.bassin = col, -1
        self.c_mj = self.c_kwh = self.c_perte_mj = self.c_heures = self.c_pleine_h = self.c_mj_pleine = self.c_kwh_pleine = 0.0
        self.c_demarrages = self.c_pannes = 0
        self.c_unites = {}            # bien -> unites brulees
        self.j_kwh = self.j_cout = self.j_mj = 0.0
        self.sortie_h = 0.0

    def nom_tech(self): return self.tech.nom if self.genre == "thermique" else self.genre


class Charge:
    """Une zone de delestage : un lieu habite ( residentiel, tertiaire, eclairage ), un site de l energie ( puits,
    raffinerie ), les sites du moteur d une ile, ou un contrat d un autre domaine. d_ : les kWh du jour ( demande,
    servi, non servi par delestage ou par coupure de ligne, efface ; servis par categorie )."""
    __slots__ = ("cle", "ile", "type", "lieu", "hab", "effacement", "prioritaire", "coupe_jusqu", "entreprise", "payeur",
                 "kw", "heures", "rang", "h_del7", "part_res", "servi_h", "plan", "ouvriers",
                 "dem", "dem_res", "dem_ter", "dem_ecl", "eff_h", "d_serv", "d_del", "d_cut", "d_eff",
                 "d_res", "d_ter", "d_ecl", "d_h_del", "c_dem", "c_serv", "c_del", "c_cut")

    def __init__(self, cle, ile, type_, lieu, rang, entreprise=None, payeur=None, kw=0.0, heures=None, prioritaire=False):
        self.cle, self.ile, self.type, self.lieu, self.rang = cle, ile, type_, lieu, rang
        self.entreprise, self.payeur, self.kw, self.prioritaire = entreprise, payeur, float(kw), bool(prioritaire)
        self.heures = np.ones(24, bool) if heures is None else np.asarray(heures, bool)
        self.hab, self.effacement, self.coupe_jusqu, self.part_res, self.servi_h = 0.0, 0, 0, 0.0, 1.0
        self.h_del7 = [0] * 7
        self.plan, self.ouvriers = 0.0, []
        self.dem = self.dem_res = self.dem_ter = self.dem_ecl = self.eff_h = 0.0
        self.d_serv = self.d_del = self.d_cut = self.d_eff = self.d_res = self.d_ter = self.d_ecl = 0.0
        self.d_h_del = 0
        self.c_dem = self.c_serv = self.c_del = self.c_cut = 0.0


class Gisement:
    """Les reserves finies du puits, en unites de brut. Le debit par petrolier baisse avec ce qui reste sous 35 % des
    reserves de depart ( declin exponentiel ) ; il ne descend jamais sous zero."""
    __slots__ = ("reste", "depart", "c_extrait", "en_declin")

    def __init__(self, depart):
        if not depart > 0: raise ValueError("gisement : reserves positives")
        self.reste = self.depart = float(depart)
        self.c_extrait = 0.0
        self.en_declin = False

    def facteur(self): return min(1.0, self.reste / (PART_DECLIN * self.depart))


class ReseauIle:
    """Le reseau electrique d une ile : ses groupes, ses charges, ses cuves, sa batterie, sa meteo du jour, son journal
    horaire ( h ) et ses cumuls."""
    __slots__ = ("ile", "rang", "gestionnaire", "thermiques", "renouvelables", "batterie", "charges", "par_lieu",
                 "reservoirs", "sites_moteur", "pointe_estimee", "latitude", "midi", "temp", "irr", "vent_hub", "nuit",
                 "tmax", "u_pannes", "vent_z", "prevision", "pointe", "h", "hier", "cumul", "bulletin", "serie",
                 "soutirages", "centrales", "cut_jour")

    def __init__(self, ile, rang, gestionnaire, latitude, midi):
        self.ile, self.rang, self.gestionnaire, self.latitude, self.midi = ile, rang, gestionnaire, latitude, midi
        self.thermiques, self.renouvelables, self.batterie, self.charges, self.par_lieu = [], [], None, [], {}
        self.reservoirs, self.sites_moteur, self.centrales = {}, [], []
        self.pointe_estimee = 0.0
        self.temp = self.irr = self.vent_hub = self.nuit = None
        self.tmax, self.u_pannes, self.vent_z, self.prevision = 25.0, None, 0.0, np.zeros(24)
        self.pointe = np.zeros(24, bool)
        self.h = _journal_horaire()
        self.hier = None
        self.cumul = {k: 0.0 for k in CUMULS}
        self.bulletin = {}
        self.serie = deque(maxlen=400)
        self.cut_jour = 0.0          # kWh coupes par les lignes depuis minuit ( pour le journal horaire )
        self.soutirages = {}          # payeur -> kWh du jour ( soutirer )


HORAIRES = ("demande", "servi", "ens_delestage", "ens_coupure", "efface", "besoin", "injection", "pertes", "ecrete",
            "charge", "decharge", "soc", "cout_marginal", "temperature", "irradiance", "vent_moyeu", "zones",
            "residentiel", "tertiaire", "eclairage", "sites", "contrats") + NOMS_TECH
CUMULS = ("demande", "servi", "ens_delestage", "ens_coupure", "efface", "injection", "pertes", "ecrete", "charge",
          "decharge", "pertes_batterie", "production", "livre_moteur") + NOMS_TECH


def _journal_horaire(): return {k: np.zeros(24) for k in HORAIRES}


class ContexteDelestage:
    __slots__ = ("traits", "charge")

    def __init__(self, traits, charge): self.traits, self.charge = traits, charge


class Energie:
    """L etat du domaine."""
    __slots__ = ("reseaux", "par_ile", "unites", "batteries", "reservoirs", "gestionnaires", "puits", "raffinerie",
                 "gisement", "depot", "contrats", "decideur", "jour_prepare", "noms", "ids", "combustibles", "elec",
                 "zones", "mg_zone", "mg_viv", "eclairage_payeur", "raff", "co2_t", "emis_jour", "eau_jour",
                 "livre_biens", "argent", "extrait_jour", "nominal_brut_j", "nominal_puits_j", "compensation",
                 "redevance", "factures", "impayes", "production_7j", "production_jour")

    def __init__(self):
        self.reseaux, self.par_ile, self.unites, self.batteries, self.reservoirs, self.gestionnaires = [], {}, [], [], [], []
        self.puits = self.raffinerie = self.gisement = self.depot = None
        self.contrats = {}
        self.decideur = None
        self.jour_prepare = None
        self.noms = self.ids = self.combustibles = None
        self.elec = -1
        self.zones, self.mg_zone, self.mg_viv = [], np.zeros(0, np.int64), np.zeros(0)
        self.eclairage_payeur = None
        self.raff = {k: 0.0 for k in ("brut_kg", "autoconso_kg", "pertes_kg", "brut_u", "heures")}
        for b, _ in RENDEMENTS: self.raff[b + "_kg"] = 0.0; self.raff[b + "_u"] = 0.0
        self.co2_t = {}               # source -> t de CO2 cumulees
        self.emis_jour = {}           # ( lieu, polluant ) -> kg du jour
        self.eau_jour = {}            # lieu -> m3 du jour
        self.livre_biens = {}         # ( nature, motif, bien ) -> quantite, jours clos ( mes motifs )
        self.argent = {}              # motif -> drachmes, cumul
        self.extrait_jour = 0.0
        self.nominal_brut_j = self.nominal_puits_j = 0.0
        self.compensation = self.redevance = self.factures = self.impayes = 0.0
        self.production_7j = {b: deque(maxlen=7) for b, _ in RENDEMENTS}   # unites produites par jour, 7 derniers jours
        self.production_jour = {b: 0.0 for b, _ in RENDEMENTS}


# ================================================================== le point de decision
def _observer_delestage(ctx): return ctx.traits


def _regle_delestage(x, ctx):
    marge = 2.0 * x[0]
    if marge < 1.05 or x[2] >= 0.1: return 2
    if marge < 1.25 or x[1] >= 0.25 or x[5] < 0.2: return 1
    return 0


def _temoin_delestage(x, ctx, rng): return 0


POINT_DELESTAGE = D.PointDeDecision(
    "delestage_zone", "energie",
    traits=(("marge", "bulletin du gestionnaire : puissance thermique disponible et batterie sur la pointe d hier de l ile, sur 2"),
            ("pannes", "bulletin du gestionnaire : part de la puissance thermique en panne ce matin"),
            ("delestage_ile", "bulletin du gestionnaire : energie non servie de l ile hier sur sa demande, fois 10"),
            ("delestage_zone", "ses compteurs : heures ou CETTE zone a ete delestee sur 7 jours, sur 24"),
            ("chaleur", "station meteo de l ile : temperature maximale d hier, de 10 a 40 degres"),
            ("combustible", "bulletin du gestionnaire : jours d autonomie en combustible des centrales, sur 10"),
            ("residentiel", "ses compteurs : part du residentiel dans sa demande d hier"),
            ("programme", "son programme d effacement en cours, sur 2")),
    actions=ACTIONS_DELESTAGE,
    observer=_observer_delestage, regle=_regle_delestage, temoin=_temoin_delestage,
    note=("chaque jour, moins l energie non servie par delestage dans CETTE zone et 0,1 fois l energie qu elle a effacee, "
          "sur sa demande ; moyenne sur les 3 jours du programme"),
    horizon_j=HORIZON_DELESTAGE)


# ================================================================== petits outils
def _membres_gestionnaires(w): return w.pays.domaines["energie"].gestionnaires
def _membres_reservoirs(w): return w.pays.domaines["energie"].reservoirs
def _membres_batteries(w): return w.pays.domaines["energie"].batteries


def _travailleurs(p, e):
    """Les ouvriers de l entreprise `e` presents a leur poste : h.poste == travail, sur le lieu du site. Leurs NUMEROS,
    dans l ordre de l index du moteur, lus dans les colonnes ( 24/09 : une vue par ouvrier et par heure coutait )."""
    w = p.w; tb = w.table; lieu = e.lieu
    ids = w.ids_au_travail(lieu, e.role)
    if not ids: return []
    n = lieu.n
    if n < 0 or n >= len(tb.par_n) or tb.par_n[n] is not lieu: return []      # h.lieu is e.lieu : jamais vrai
    a = np.array(ids, dtype=np.int64)
    ok = (tb.vivant[a] != 0) & (tb.poste[a] == _CODE_TRAVAIL) & (tb.lieu[a] == n)
    return a[ok].tolist()


_CODE_TRAVAIL = PO.CODE_POSTE["travail"]


def _vivants_au_travail(w, lieu, role):
    """len([h for h in w.au_travail_de(lieu, role) if h.vivant]), lu dans la colonne."""
    ids = w.ids_au_travail(lieu, role)
    if not ids: return 0
    return int(np.count_nonzero(w.table.vivant[np.array(ids, dtype=np.int64)]))


def _crediter_heures(p, ids, x):
    """x.heures_jour += x pour chaque ouvrier, dans l ordre ( add.at : sequentiel, doublons compris )."""
    if ids: np.add.at(p.w.table.heures, np.array(ids, dtype=np.int64), x)


def _prix_unitaire(p, E, bien, lieu=None):
    """Drachmes par unite : le gazole au prix du marche de la region ( ce que le moteur le paie ), les autres au prix
    mondial du catalogue."""
    if bien == "carburant":
        m = p.w.marches[lieu.marche.id] if lieu is not None else next(iter(p.w.marches.values()))
        return m.prix["carburant"]
    return p.socle.catalogue[bien].prix_monde


def _tarif_kwh(p): return p.w.reseau.tarif / KWH_UNITE


def _cout_incremental(p, E, u, bien):
    """Drachmes par kWh supplementaire d un groupe : combustible de l increment, plus exploitation."""
    t = u.tech
    prix_mj = _prix_unitaire(p, E, bien, _lieu(p, u.lieu)) / E.combustibles[bien].mj()
    return MJ_KWH * (1.0 - t.part_a_vide) / t.rendement * prix_mj + t.om / 1000.0


def _cout_plein(p, E, u, bien):
    t = u.tech
    return MJ_KWH / t.rendement * _prix_unitaire(p, E, bien, _lieu(p, u.lieu)) / E.combustibles[bien].mj() + t.om / 1000.0


def _lieu(p, lid): return p.w.carte.lieux[lid]


def _porteur(E, u, bien):
    """Le detenteur du combustible `bien` d un groupe : les stocks du moteur de sa centrale pour le gazole, ses cuves sinon."""
    if bien == "carburant" and u.entreprise is not None: return StocksE1(u.entreprise.stocks, E.noms)
    return u.reservoir.stock


def _dispo_unites(E, porteur, bien):
    if isinstance(porteur, StocksE1): return porteur.d.get(bien, 0.0)
    return porteur[E.ids[bien]]


def _choisir_combustible(E, u):
    """Le combustible du groupe : le premier de sa filiere qui a de quoi tenir une heure a son minimum."""
    t = u.tech
    for b in t.combustibles:
        if b not in E.combustibles: continue
        besoin = mj_combustible(t, u.pmax, t.pmin * u.pmax)
        if _dispo_unites(E, _porteur(E, u, b), b) * E.combustibles[b].mj() >= besoin: return b
    return None


def _panne(p, E, u, heures, cause):
    u.en_panne, u.panne_jusqu = True, p.w.pas + int(round(heures * PAS_H))
    if isinstance(u, Unite): u.en_ligne, u.pret_a = False, -1; u.c_pannes += 1
    p.socle.parc.mettre_en_etat(u.objet, O.PANNE)
    p.noter("panne_centrale", unite=u.objet.id, lieu=u.lieu, technologie=u.nom_tech() if isinstance(u, Unite) else "batterie",
            heures=round(heures, 1), cause=cause)


# ================================================================== le debut du jour ( 0 h, apres le territoire )
def _debut_de_jour(p, E):
    w = p.w; cal = p.socle.calendrier
    E.jour_prepare = p.jour
    date = cal.date(w.pas)
    jour_an = date.timetuple().tm_yday
    Tt = p.domaine("territoire")
    n_u = len(E.unites) + len(E.batteries)
    u_pannes = p.du_jour("energie_pannes").random((24, max(1, n_u)))
    z_vent = p.du_jour("energie_vent").standard_normal((len(E.reseaux), 24))
    _recenser(p, E)
    for R in E.reseaux:
        m = TER.meteo(p, R.ile)
        i = Tt.iles.index(R.ile)
        dtr = m.tmax - m.tmin
        R.temp = m.tmoy + dtr / 2.0 * np.cos(2 * np.pi * (np.arange(24) - HEURE_TMAX) / 24.0)
        lever, coucher = CAL.lever_coucher(R.latitude, min(366, jour_an), R.midi)
        t0 = np.arange(24.0)
        R.nuit = 1.0 - np.clip(np.minimum(t0 + 1.0, coucher) - np.maximum(t0, lever), 0.0, 1.0)
        R.irr = profil_solaire(R.latitude, jour_an, lever, coucher, irradiation_jour(float(Tt.tab.ra[i, Tt.doy]), dtr))
        z = np.zeros(24); a = R.vent_z
        for k in range(24):
            a = PHI_VENT_H * a + math.sqrt(1 - PHI_VENT_H ** 2) * z_vent[R.rang, k]; z[k] = a
        R.vent_z = a
        v10 = m.vent_ms * (1.0 + BRISE * np.cos(2 * np.pi * (np.arange(24) - HEURE_TMAX) / 24.0)) \
            * np.exp(SIGMA_VENT_H * z - SIGMA_VENT_H ** 2 / 2.0)
        R.vent_hub = v10 * (H_MOYEU / 10.0) ** ALPHA_CISAILLEMENT
        R.u_pannes = u_pannes
        modele = _prevoir(p, E, R)
        R.prevision = np.where(R.hier["besoin"] > 0, R.hier["besoin"], modele) if R.hier is not None else modele
        R.pointe = np.zeros(24, bool); R.pointe[np.argsort(-R.prevision, kind="stable")[:HEURES_POINTE]] = True
        _catastrophes(p, E, R, m)
        _bulletin(p, E, R)
        R.tmax = m.tmax
    _decider(p, E)


def _recenser(p, E):
    """Les habitants de chaque zone ( une passe sur les menages ), et la zone de chaque menage pour sa facture. En
    colonnes : les membres vivants de la LISTE de chaque menage ( menages_inscrits ), la zone par domicile."""
    w = p.w
    n = len(w.menages)
    p.colonnes["menage"].assurer(n)
    rang = {c.lieu: k for k, c in enumerate(E.zones)}
    mz = np.full(n, -1, np.int64); mv = np.zeros(n)
    nz = len(E.zones)
    tb = w.table; mt = tb.menages
    if n > 0 and nz > 0:
        nh = tb.n
        mi = PO.menages_inscrits(tb, nh)
        sel = (mi >= 0) & (tb.vivant[:nh] != 0)
        viv = np.bincount(mi[sel], minlength=n)[:n]
        dom = mt.domicile[:n]
        zone_n = {}
        for dn in np.unique(dom[dom >= 0]).tolist():
            k = rang.get(mt.par_n[dn].id)
            if k is not None: zone_n[dn] = k
        if zone_n:
            carte = np.full(int(dom.max()) + 1, -1, np.int64)
            for dn, k in zone_n.items(): carte[dn] = k
            z = np.where(dom >= 0, carte[np.maximum(dom, 0)], -1)
            ok = (z >= 0) & (viv > 0)
            mz[ok] = z[ok]; mv[ok] = viv[ok]
    hab = np.bincount(mz[mz >= 0], weights=mv[mz >= 0], minlength=nz)[:nz] if nz else np.zeros(0)
    for k, c in enumerate(E.zones): c.hab = float(hab[k])
    E.mg_zone, E.mg_viv = mz, mv


def _demande_zones(R, h, clim, wk_res, wk_ter):
    """kWh de l heure des zones habitees, avant effacement : ( residentiel, tertiaire, eclairage ) par zone."""
    out = []
    er = E_RES_KWH_HAB_J / 24.0 * PROFIL_RES[h] * wk_res * (1.0 + clim)
    et = E_TER_KWH_HAB_J / 24.0 * PROFIL_TER[h] * wk_ter * (1.0 + clim)
    el = W_ECLAIRAGE_HAB / 1000.0 * R.nuit[h]
    for c in R.charges:
        if c.type == ZONE: out.append((c.hab * er, c.hab * et, c.hab * el))
    return out


def _clim(T): return K_FROID * max(0.0, T - T_FROID) + K_CHAUD * max(0.0, T_CHAUD - T)


def _semaine(p):
    cal = p.socle.calendrier
    d = cal.date(p.w.pas)
    if cal.ouvre(d): return 1.0, 1.0
    if d.weekday() == 5 and cal.ferie(d) is None: return RES_REPOS, TER_SAMEDI
    return RES_REPOS, TER_REPOS


def _prevoir(p, E, R):
    """La prevision d injection de la journee quand hier manque ( le premier jour ) : les zones selon le modele, les
    sites a leur effectif nominal."""
    wr, wt = _semaine(p)
    prev = np.zeros(24)
    sites = _sites_nominal_kw(p, E, R)
    for h in range(24):
        z = sum(a + b + c for a, b, c in _demande_zones(R, h, _clim(R.temp[h]), wr, wt))
        prev[h] = (z + sites * (1.0 if 7 <= h < 15 else 0.3)) / (1.0 - PERTES_RESEAU)
    return prev


def _sites_nominal_kw(p, E, R):
    """La puissance des sites a leur effectif du jour ( pour dimensionner et prevoir )."""
    w = p.w; kw = 0.0
    for e in R.sites_moteur:
        q = e.intrants.get("electricite", 0.0)
        n = _vivants_au_travail(w, e.lieu, e.role)
        kw += n * q * KWH_UNITE * (1.0 / 3.0 if PO.TRAVAIL.get(e.role, ((), None))[1] == "garde" else 1.0)
    for c in R.charges:
        if c.type != SITE: continue
        e = c.entreprise
        n = _vivants_au_travail(w, e.lieu, e.role)
        if e.type == "raffinerie": kw += n * DEBIT_OUVRIER_H * COMBUSTIBLES["petrole"].masse_kg / 1000.0 * ELEC_RAFFINAGE_KWH_T
        else: kw += n / 3.0 * PETROLE_PETROLIER_H * ELEC_PUITS_KWH
    return kw


def _catastrophes(p, E, R, m):
    """Les lignes coupees et les centrales touchees du jour : seisme ( intensite par lieu ), tempete, cyclone, crue."""
    w = p.w; j = p.jour
    pz = np.zeros(len(R.charges))
    cause = [""] * len(R.charges)
    rngs = p.du_jour("energie_seisme")
    for cat in TER.catastrophes_en_cours(p, R.ile):
        if cat.debut_j != j: continue
        if cat.type == "seisme" and cat.intensites:
            for k, c in enumerate(R.charges):
                mmi = cat.intensites.get(c.lieu)
                if mmi is None: continue
                pr = phi((mmi - MMI_LIGNE[0]) / MMI_LIGNE[1])
                if pr > pz[k]: pz[k], cause[k] = pr, "seisme"
            for u in R.thermiques + R.renouvelables:
                mmi = cat.intensites.get(u.lieu)
                if mmi is None or u.en_panne: continue
                if rngs.random() < phi((mmi - MMI_CENTRALE[0]) / MMI_CENTRALE[1]): _panne(p, E, u, MTTR_SEISME_H, "seisme")
        elif cat.type == "inondation":
            bassin = TER.bassin_de(p, cat.lieu)
            for k, c in enumerate(R.charges):
                if c.lieu is None or c.lieu not in w.carte.lieux: continue
                if TER.bassin_de(p, c.lieu) == bassin and P_CRUE * cat.gravite > pz[k]:
                    pz[k], cause[k] = P_CRUE * cat.gravite, "crue"
    if m.vent_ms >= VENT_TEMPETE or m.cyclone > 0:
        pr = min(0.5, PENTE_TEMPETE * max(0.0, m.vent_ms - VENT_TEMPETE)) if m.cyclone == 0 else min(0.9, P_CYCLONE_CAT * m.cyclone)
        for k, c in enumerate(R.charges):
            if c.type in (ZONE, CONTRAT) and pr > pz[k]: pz[k], cause[k] = pr, "tempete" if m.cyclone == 0 else "cyclone"
    if not pz.any(): return
    u = p.du_jour("energie_lignes").random(len(R.charges))
    dur = p.du_jour("energie_reparations").integers(REPARATION_J[0], REPARATION_J[1] + 1, len(R.charges))
    for k in np.nonzero(u < pz)[0].tolist():
        c = R.charges[k]
        if c.lieu is None: continue
        couper_ligne(p, c.lieu, int(dur[k]), cause[k])


def _bulletin(p, E, R):
    """Ce que le gestionnaire publie le matin : marge, pannes, delestage d hier, autonomie en combustible."""
    dispo = sum(u.pmax for u in R.thermiques if not u.en_panne)
    tot = sum(u.pmax for u in R.thermiques) or 1.0
    batt = R.batterie.p_kw if R.batterie is not None and not R.batterie.en_panne else 0.0
    pointe = float(R.hier["besoin"].max()) if R.hier is not None else 0.8 * R.pointe_estimee
    ens = (R.hier["ens_delestage"].sum() / max(EPS, R.hier["demande"].sum() + R.hier["ens_delestage"].sum())) if R.hier is not None else 0.0
    stocks = {}; mj_j = 0.0                 # chaque cuve une fois, meme si plusieurs groupes y puisent
    for u in R.thermiques:
        for b in u.tech.combustibles:
            if b in E.combustibles:
                stocks[(id(_porteur_cle(E, u, b)), b)] = _dispo_unites(E, _porteur(E, u, b), b) * E.combustibles[b].mj()
        mj_j += mj_combustible(u.tech, u.pmax, FACTEUR_CHARGE * u.pmax) * 24.0
    mj = math.fsum(stocks.values())
    R.bulletin = {"marge": (dispo + batt) / max(EPS, pointe), "pannes": 1.0 - dispo / tot, "ens": ens,
                  "autonomie_j": mj / max(EPS, mj_j), "pointe_hier": pointe, "tmax_hier": R.tmax}


def _decider(p, E):
    """Un tiers des zones habitees decide chaque jour son programme d effacement pour 3 jours."""
    dec = E.decideur
    for R in E.reseaux:
        b = R.bulletin
        for c in R.charges:
            if c.type != ZONE or c.hab <= 0 or (c.rang + p.jour) % JOURS_PROGRAMME: continue
            x = (min(1.0, b["marge"] / 2.0), min(1.0, max(0.0, b["pannes"])), min(1.0, 10.0 * b["ens"]),
                 min(1.0, sum(c.h_del7) / 24.0), min(1.0, max(0.0, (b["tmax_hier"] - 10.0) / 30.0)),
                 min(1.0, b["autonomie_j"] / 10.0), min(1.0, max(0.0, c.part_res)), c.effacement / 2.0)
            c.effacement = dec.decider(c.cle, ContexteDelestage(x, c))


# ================================================================== l heure : la conduite du reseau
def _heure(p):
    E = p.domaine("energie")
    if E.jour_prepare != p.jour: _debut_de_jour(p, E)
    h = int(round(p.heure * 60)) // 60 % 24
    for R in E.reseaux: _conduire(p, E, R, h)


def _reparer_et_casser(p, E, R, h):
    pas = p.w.pas
    for u in R.thermiques + R.renouvelables + ([R.batterie] if R.batterie is not None else []):
        if u.en_panne and u.panne_jusqu <= pas:
            u.en_panne = False
            p.socle.parc.mettre_en_etat(u.objet, O.SERVICE)
            p.noter("remise_en_service", unite=u.objet.id, lieu=u.lieu)
        if u.en_panne: continue
        marche = u.en_ligne if isinstance(u, Unite) and u.genre == "thermique" else True
        if marche and R.u_pannes[h, u.col] < 1.0 / u.mtbf: _panne(p, E, u, u.mttr, "aleatoire")


def _demandes(p, E, R, h):
    """La demande de chaque charge pour l heure : zones ( apres effacement ), sites ( ouvriers presents ), sites du
    moteur ( allocation a completer ), contrats. Une charge dont la ligne est coupee ne demande rien au reseau : sa
    demande est de l energie non servie par coupure."""
    w = p.w; pas = w.pas
    wr, wt = _semaine(p)
    clim = _clim(R.temp[h])
    zones = iter(_demande_zones(R, h, clim, wr, wt))
    tot_moteur = _besoin_sites_moteur(p, E, R)
    buffer_part = w.reseau.stock * KWH_UNITE * (tot_moteur / max(EPS, sum(_besoin_sites_moteur(p, E, X) for X in E.reseaux))) \
        if len(E.reseaux) > 1 else w.reseau.stock * KWH_UNITE
    for c in R.charges:
        c.dem_res = c.dem_ter = c.dem_ecl = c.eff_h = 0.0
        if c.type == ZONE:
            r, t, e = next(zones)
            f = EFFACEMENT[c.effacement] if R.pointe[h] else 0.0
            c.eff_h = (r + t) * f
            c.dem_res, c.dem_ter, c.dem_ecl = r * (1 - f), t * (1 - f), e
            c.dem = c.dem_res + c.dem_ter + c.dem_ecl
        elif c.type == SITE: c.dem = _planifier_site(p, E, c)
        elif c.type == MOTEUR: c.dem = max(0.0, tot_moteur - buffer_part)
        else: c.dem = c.kw if c.heures[h] else 0.0
        if c.coupe_jusqu > pas:
            c.d_cut += c.dem; c.dem_res = c.dem_ter = c.dem_ecl = 0.0; c.dem = 0.0; c.eff_h = 0.0


def _besoin_sites_moteur(p, E, R):
    """kWh que les sites du moteur de l ile ( non repris ) vont tirer dans l heure : ouvriers presents x intrant x activite."""
    tot = 0.0
    for e in R.sites_moteur:
        if e.id in p.repris or e.activite <= 0: continue
        n = len(_travailleurs(p, e))
        tot += n * e.intrants.get("electricite", 0.0) * e.activite
    return tot * KWH_UNITE


def _planifier_site(p, E, c):
    """Le debit que les ouvriers presents peuvent tenir dans l heure, et les kWh qu il demande."""
    e = c.entreprise
    c.ouvriers = _travailleurs(p, e)
    n = len(c.ouvriers)
    if e.type == "raffinerie":
        brut = min(n * DEBIT_OUVRIER_H, e.stocks.get("petrole", 0.0), _place_cuves(E))
        c.plan = max(0.0, brut)
        return c.plan * COMBUSTIBLES["petrole"].masse_kg / 1000.0 * ELEC_RAFFINAGE_KWH_T
    g = E.gisement
    c.plan = max(0.0, min(n * PETROLE_PETROLIER_H * g.facteur(), g.reste))
    return c.plan * ELEC_PUITS_KWH


def _place_cuves(E):
    """Le brut que les cuves des produits laissent traiter : la coupe la plus a l etroit decide."""
    if E.depot is None or E.nominal_brut_j <= 0: return math.inf
    mb = COMBUSTIBLES["petrole"].masse_kg
    lim = math.inf
    for b, r in RENDEMENTS:
        if b == "carburant": continue
        cap = CUVES_J * E.nominal_brut_j * mb * r / E.combustibles[b].masse_kg
        place = max(0.0, cap - E.depot.stock[E.ids[b]])
        lim = min(lim, place * E.combustibles[b].masse_kg / (mb * r))
    return lim


def _renouvelables(p, E, R, h):
    """kWh disponibles de l heure : ( eolien, solaire, hydraulique ), groupes en panne exclus."""
    eol = sol = hyd = 0.0
    for u in R.renouvelables:
        if u.en_panne: u.sortie_h = 0.0; continue
        if u.genre == "eolien": u.sortie_h = u.pmax * float(puissance_eolienne(R.vent_hub[h])); eol += u.sortie_h
        elif u.genre == "solaire": u.sortie_h = u.pmax * R.irr[h] / 1000.0 * PR_SOLAIRE; sol += u.sortie_h
        else:
            u.sortie_h = u.pmax if (R.pointe[h] and _hydro_dispo(p, u)) else 0.0; hyd += u.sortie_h
    return eol, sol, hyd


def _hydro_dispo(p, u):
    B = p.domaine("territoire").bassins
    return B.retenue[u.bassin] > B.min_r[u.bassin] + 0.5 * (B.cap_r[u.bassin] - B.min_r[u.bassin])


def _engager(p, E, R, h, besoin, res):
    """L engagement des groupes : ceux qui demarrent arrivent en ligne ; on demarre par ordre de cout a pleine charge
    jusqu a couvrir la demande des trois heures qui viennent, moins la moitie du renouvelable, plus une reserve egale au
    plus gros groupe en ligne ( N-1 ) ; les groupes rapides a l arret et la batterie comptent dans cette reserve ( ils
    reprennent la charge en quelques minutes ). On arrete le plus cher quand il n est plus utile et qu il a tourne son
    temps minimum ; il reste toujours un groupe en ligne ( l inertie du reseau )."""
    pas = p.w.pas
    for u in R.thermiques:
        if u.pret_a >= 0 and pas >= u.pret_a and not u.en_panne:
            u.en_ligne, u.pret_a, u.depuis = True, -1, pas
    besoin_max = max(besoin, R.prevision[(h + 1) % 24], R.prevision[(h + 2) % 24])
    cible = besoin_max - min(0.5 * res, PENETRATION_MAX * besoin_max)
    actifs = [u for u in R.thermiques if (u.en_ligne or u.pret_a >= 0) and not u.en_panne]
    libres = []
    for u in R.thermiques:
        if u.en_ligne or u.pret_a >= 0 or u.en_panne: continue
        b = _choisir_combustible(E, u)
        if b is not None: libres.append((_cout_plein(p, E, u, b), u.id, u))
    libres.sort(key=lambda x: (x[0], x[1]))
    batt = _batterie_limites(R)[1]

    def couverture(groupe):
        cap = sum(u.pmax for u in groupe)
        rapide = batt + sum(u.pmax for _, _, u in libres if u.tech.demarrage_h == 0 and u not in groupe)
        req = max(RESERVE_MIN * besoin_max, max((u.pmax for u in groupe), default=0.0))
        return cap - max(0.0, req - rapide)
    while libres and couverture(actifs) < cible:
        _, _, u = libres.pop(0)
        if u.tech.demarrage_h == 0: u.en_ligne, u.depuis = True, pas
        else: u.pret_a = pas + u.tech.demarrage_h * PAS_H
        u.c_demarrages += 1; p.compter("demarrage_groupe")
        actifs.append(u)
    en_ligne = [u for u in actifs if u.en_ligne]
    if len(en_ligne) > 1:
        cher = max(en_ligne, key=lambda u: (_cout_plein(p, E, u, _choisir_combustible(E, u) or u.tech.combustibles[-1]), u.id))
        reste = [u for u in actifs if u is not cher]
        if (pas - cher.depuis >= cher.tech.duree_min_h * PAS_H and any(u.en_ligne for u in reste)
                and couverture(reste) >= cible):
            cher.en_ligne = False
    if not any(u.en_ligne for u in R.thermiques):
        for _, _, u in libres:
            if u.tech.demarrage_h == 0 and not u.en_ligne:
                u.en_ligne, u.depuis = True, pas; u.c_demarrages += 1; p.compter("demarrage_groupe"); break


def _groupes(p, E, R):
    """Les groupes en ligne, utilisables : leur combustible, le combustible qui leur revient ( les groupes d un meme
    site se partagent ses cuves a parts egales ), leur pmax borne par ce combustible, leur cout incremental."""
    choix = []
    for u in R.thermiques:
        if not u.en_ligne or u.en_panne: continue
        b = _choisir_combustible(E, u)
        if b is None:
            u.en_ligne = False; p.compter("manque_combustible"); continue
        choix.append((u, b))
    parts = {}
    for u, b in choix:
        k = (id(_porteur_cle(E, u, b)), b)
        parts[k] = parts.get(k, 0) + 1
    out = []
    for u, b in choix:
        k = (id(_porteur_cle(E, u, b)), b)
        mj = _dispo_unites(E, _porteur(E, u, b), b) * E.combustibles[b].mj() / parts[k]
        pmax = emax_combustible(u.tech, u.pmax, mj)
        pmin = u.tech.pmin * u.pmax
        if pmax < pmin - EPS:
            u.en_ligne = False; p.compter("manque_combustible"); continue
        out.append((u, b, pmin, max(pmin, pmax), _cout_incremental(p, E, u, b)))
    return out


def _porteur_cle(E, u, b):
    return u.entreprise.stocks if (b == "carburant" and u.entreprise is not None) else u.reservoir


def _batterie_limites(R):
    b = R.batterie
    if b is None or b.en_panne: return 0.0, 0.0
    kwh = _kwh_batterie(b)
    ch = max(0.0, min(b.p_kw, (b.e_kwh - kwh) / ETA_CH))
    de = max(0.0, min(b.p_kw, (kwh - SOC_MIN * b.e_kwh) * ETA_DE))
    return ch, de


def _kwh_batterie(b): return b.stock[b.el] * KWH_UNITE


def _planifier(p, E, R, h, besoin, res):
    """La repartition de l heure ; un surplus ( minimum des groupes au-dessus de la demande ) arrete le plus cher."""
    while True:
        gr = _groupes(p, E, R)
        plan = repartir(besoin, [(g[2], g[3], g[4]) for g in gr], res, _batterie_limites(R), bool(R.pointe[h]), h in NUIT_H)
        if plan[6] <= EPS or len(gr) <= 1: return gr, plan
        cher = max(gr, key=lambda g: (g[4], g[0].id))[0]
        cher.en_ligne = False


def _delester(p, E, R, a_couper):
    """Le delestage tournant : les charges sont coupees entieres ( un depart de ligne ), dans l ordre des classes ( sites
    du moteur et zones sans programme, puis effacement leger, puis fort, puis les charges prioritaires : contrats
    prioritaires, puits et raffinerie qui alimentent les centrales ), et dans chaque classe celle
    qui a ete le moins delestee sur 7 jours d abord. L allocation des sites du moteur, une charge industrielle
    interruptible, se reduit seulement de ce qui manque. Rend ( kWh coupes, charges touchees )."""
    ordre = sorted((c for c in R.charges if c.dem > 0.0),
                   key=lambda c: (3 if c.prioritaire else (c.effacement if c.type == ZONE else 0),
                                  sum(c.h_del7) + c.d_h_del, c.rang))
    coupe = 0.0; n = 0
    for c in ordre:
        reste = a_couper - coupe
        if reste <= EPS: break
        x = min(c.dem, reste) if c.type == MOTEUR else c.dem
        coupe += x; c.d_del += x; c.d_h_del += 1; n += 1
        c.servi_h = 1.0 - x / c.dem
        c.dem -= x
        if c.type == ZONE: c.dem_res = c.dem_ter = c.dem_ecl = 0.0
    return coupe, n


def _conduire(p, E, R, h):
    """Une heure du reseau d une ile : pannes et reparations, demandes, renouvelables, engagement, repartition,
    delestage s il manque, puis la comptabilite ( combustible, production, batterie, consommations, pertes ), le
    travail des sites et des centrales."""
    w = p.w
    _reparer_et_casser(p, E, R, h)
    _demandes(p, E, R, h)
    for c in R.charges: c.servi_h = 1.0 if c.coupe_jusqu <= w.pas else 0.0
    eol, sol, hyd = _renouvelables(p, E, R, h)
    res = eol + sol + hyd
    D0 = sum(c.dem for c in R.charges)
    besoin0 = besoin = D0 / (1.0 - PERTES_RESEAU)
    _engager(p, E, R, h, besoin, res)
    gr, plan = _planifier(p, E, R, h, besoin, res)
    ens_del = 0.0
    if plan[5] > EPS:
        coupe, n = _delester(p, E, R, plan[5] * (1.0 - PERTES_RESEAU))
        ens_del = coupe
        besoin = sum(c.dem for c in R.charges) / (1.0 - PERTES_RESEAU)
        gr, plan = _planifier(p, E, R, h, besoin, res)
        p.compter("energie_non_servie", coupe)
        p.noter("delestage_electrique", ile=R.ile, tranche=h, kwh=round(coupe, 3), charges=n)
    _appliquer(p, E, R, h, gr, plan, (eol, sol, hyd), besoin0, besoin, ens_del)


def _appliquer(p, E, R, h, gr, plan, res3, besoin0, besoin, ens_del):
    """La comptabilite de l heure : chaque kWh et chaque unite de combustible passent par le grand livre."""
    w = p.w; L = p.socle.livre; el = E.elec; G = R.gestionnaire; H = R.h
    sorties, res_util, ecrete, charge, decharge, manque, surplus = plan
    sorties = list(sorties)
    if surplus > EPS and sorties:         # un seul groupe dont le minimum depasse la demande : il suit la demande
        sorties[0] = max(0.0, sorties[0] - surplus)
    # ---- le combustible et la production thermique
    thermique = 0.0; cm = 0.0
    actifs = set()
    for (u, b, pmin, pmax, cout), e_kwh in zip(gr, sorties):
        cb = E.combustibles[b]
        brule = L.bruler(_porteur(E, u, b), E.ids[b], mj_combustible(u.tech, u.pmax, e_kwh) / cb.mj(), "combustion_centrale")
        mj = brule * cb.mj()
        u.c_unites[b] = u.c_unites.get(b, 0.0) + brule
        u.c_mj += mj; u.c_kwh += e_kwh; u.c_perte_mj += mj - MJ_KWH * e_kwh; u.c_heures += 1.0
        if e_kwh >= u.pmax - EPS: u.c_pleine_h += 1.0; u.c_mj_pleine += mj; u.c_kwh_pleine += e_kwh
        u.j_kwh += e_kwh; u.j_mj += mj
        u.j_cout += brule * _prix_unitaire(p, E, b, _lieu(p, u.lieu)) + u.tech.om / 1000.0 * e_kwh
        p.socle.parc.user(u.objet, 1.0)
        thermique += e_kwh
        H[u.tech.nom][h] += e_kwh
        if e_kwh > pmin + EPS: cm = max(cm, cout)
        # CO2 du combustible, SO2 de son soufre, NOx et poussieres de la technologie, eau d appoint
        _emettre(E, u.lieu, "so2", 2.0 * cb.soufre * brule * cb.masse_kg)
        _emettre(E, u.lieu, "no2", u.tech.nox * e_kwh / 1000.0)
        _emettre(E, u.lieu, "pm25", u.tech.pm25 * e_kwh / 1000.0)
        E.co2_t[u.tech.nom] = E.co2_t.get(u.tech.nom, 0.0) + mj * cb.co2 / 1e6
        E.eau_jour[u.lieu] = E.eau_jour.get(u.lieu, 0.0) + u.tech.eau * e_kwh / 1000.0
        if u.entreprise is not None:
            u.entreprise.produit_du_jour["electricite"] += e_kwh / KWH_UNITE
            if e_kwh > 0: actifs.add(u.entreprise.id)
    if gr and cm == 0.0: cm = min(g[4] for g in gr)
    if manque > EPS or ens_del > 0: cm = VOLL_DR_KWH
    # ---- le renouvelable : produit ce qui sert ( demande et batterie ), ecrete le reste, au prorata
    eol, sol, hyd = res3
    tot_res = eol + sol + hyd
    f = res_util / tot_res if tot_res > 0 else 0.0
    for u in R.renouvelables:
        e_kwh = u.sortie_h * f
        u.c_kwh += e_kwh; u.j_kwh += e_kwh
        if e_kwh > 0: u.c_heures += 1.0; p.socle.parc.user(u.objet, 1.0)
        H[u.genre][h] += e_kwh
        if u.genre == "hydro" and e_kwh > 0:
            TER.prelever(p, u.lieu, e_kwh * MJ_KWH * 1e6 / (1000.0 * 9.81 * CHUTE_M * RENDEMENT_HYDRO), "energie")
    for motif, x in (("production_thermique", thermique), ("production_eolienne", eol * f), ("production_solaire", sol * f),
                     ("production_hydraulique", hyd * f)):
        if x > 0: L.produire(G.stock, el, x / KWH_UNITE, motif)
    if ecrete > EPS: p.compter("ecretement", ecrete)
    # ---- la batterie : pertes pour moitie a la charge, pour moitie a la decharge ( racine du rendement aller-retour )
    B = R.batterie
    if decharge > EPS:
        L.deplacer(B.stock, G.stock, el, decharge / KWH_UNITE, "decharge_batterie")
        perte = decharge * (1.0 / ETA_DE - 1.0)
        L.perdre(B.stock, el, perte / KWH_UNITE, "pertes_stockage")
        B.c_decharge += decharge; B.c_pertes += perte; R.cumul["pertes_batterie"] += perte
    if charge > EPS:
        L.deplacer(G.stock, B.stock, el, charge * ETA_CH / KWH_UNITE, "charge_batterie")
        perte = charge * (1.0 - ETA_CH)
        L.perdre(G.stock, el, perte / KWH_UNITE, "pertes_stockage")
        B.c_charge += charge; B.c_pertes += perte; R.cumul["pertes_batterie"] += perte
    # ---- les consommations, par categorie ; les sites du moteur recoivent leur allocation ; le reste est perdu
    res = ter = ecl = sites = contrats = moteur = eff = 0.0
    for c in R.charges:
        if c.type == ZONE: c.d_eff += c.eff_h; eff += c.eff_h
        if c.dem <= 0.0: continue
        c.d_serv += c.dem
        if c.type == ZONE:
            res += c.dem_res; ter += c.dem_ter; ecl += c.dem_ecl
            c.d_res += c.dem_res; c.d_ter += c.dem_ter; c.d_ecl += c.dem_ecl
        elif c.type == SITE: sites += c.dem
        elif c.type == MOTEUR: moteur += c.dem
        else: contrats += c.dem
    for motif, x in (("consommation_residentielle", res), ("consommation_tertiaire", ter), ("eclairage_public", ecl),
                     ("consommation_sites_energie", sites), ("consommation_contrats", contrats)):
        if x > 0: L.consommer(G.stock, el, x / KWH_UNITE, motif)
    if moteur > 0: L.deplacer(G.stock, ReseauE1(w.reseau), el, moteur / KWH_UNITE, "livraison_sites_moteur")
    pertes = L.perdre(G.stock, el, G.stock[el], "pertes_reseau") * KWH_UNITE
    # ---- les sites de l energie produisent s ils ont eu leur courant ; les ouvriers des centrales qui tournent travaillent
    for c in R.charges:
        if c.type == SITE: _produire_site(p, E, c, c.servi_h > 0 and c.coupe_jusqu <= w.pas)
    _oleoduc(p, E)
    for e in R.centrales:
        if e.id in actifs:
            _crediter_heures(p, _travailleurs(p, e), 1.0)
    # ---- le journal de l heure et les cumuls
    servi = res + ter + ecl + sites + contrats + moteur
    cut = sum(c.d_cut for c in R.charges)
    H["demande"][h] += servi + ens_del; H["servi"][h] += servi; H["ens_delestage"][h] += ens_del
    H["ens_coupure"][h] += cut - R.cut_jour; R.cut_jour = cut
    H["efface"][h] += eff
    H["besoin"][h] += besoin0; H["injection"][h] += besoin; H["pertes"][h] += pertes; H["ecrete"][h] += ecrete
    H["charge"][h] += charge; H["decharge"][h] += decharge; H["soc"][h] = _kwh_batterie(B) if B is not None else 0.0
    H["cout_marginal"][h] = cm; H["temperature"][h] = R.temp[h]; H["irradiance"][h] = R.irr[h]
    H["vent_moyeu"][h] = R.vent_hub[h]
    H["zones"][h] += res + ter + ecl; H["residentiel"][h] += res; H["tertiaire"][h] += ter; H["eclairage"][h] += ecl
    H["sites"][h] += sites + moteur; H["contrats"][h] += contrats
    cu = R.cumul
    cu["demande"] += servi + ens_del; cu["servi"] += servi; cu["ens_delestage"] += ens_del
    cu["injection"] += besoin; cu["pertes"] += pertes; cu["ecrete"] += ecrete; cu["charge"] += charge
    cu["decharge"] += decharge; cu["production"] += thermique + res_util; cu["livre_moteur"] += moteur
    cu["efface"] += eff


def _emettre(E, lieu, polluant, kg):
    if kg > 0: E.emis_jour[(lieu, polluant)] = E.emis_jour.get((lieu, polluant), 0.0) + kg


def _produire_site(p, E, c, alimente):
    """Le puits ou la raffinerie produit ce que ses ouvriers presents ont prevu, s il a eu son electricite. Les heures
    travaillees sont creditees ( la raffinerie a court de brut ne paie que les heures de traitement, comme le moteur )."""
    e = c.entreprise; L = p.socle.livre
    if not alimente or c.plan <= EPS or not c.ouvriers: return
    n = len(c.ouvriers)
    if e.type == "raffinerie":
        _raffiner(p, E, e, c.plan)
        frac = c.plan / (n * DEBIT_OUVRIER_H)
    else:
        q = c.plan
        L.produire(StocksE1(e.stocks, E.noms), E.ids["petrole"], q, "extraction")
        e.produit_du_jour["petrole"] += q
        g = E.gisement
        g.reste = max(0.0, g.reste - q); g.c_extrait += q
        E.extrait_jour += q
        for pol, k in EMIS_PUITS_KG: _emettre(E, e.lieu.id, pol, k * q)
        E.eau_jour[e.lieu.id] = E.eau_jour.get(e.lieu.id, 0.0) + EAU_PUITS_M3 * q
        if not g.en_declin and g.facteur() < 1.0:
            g.en_declin = True
            p.noter("gisement_en_declin", lieu=e.lieu.id, reste=round(g.reste), depart=round(g.depart))
        frac = 1.0
    _crediter_heures(p, c.ouvriers, frac)


def _oleoduc(p, E):
    """Le brut du puits part par oleoduc a la raffinerie de la meme ile ( terminal01 -> factory01 : 2 km, comme le brut de
    Prinos vendu sous contrat a un raffineur ), jusqu a remplir sa cuve de brut, au prix mondial, sans TVA ni camion :
    le moteur faisait passer ce brut par le marche d Athira, ou il s entassait. Ce qui depasse la cuve reste au puits,
    que le moteur vend au marche comme avant."""
    e, r = E.puits, E.raffinerie
    if e is None or r is None or e.lieu.ile != r.lieu.ile or E.nominal_brut_j <= 0: return
    L = p.socle.livre
    q = min(e.stocks.get("petrole", 0.0), max(0.0, CUVE_BRUT_J * E.nominal_brut_j - r.stocks.get("petrole", 0.0)))
    if q <= EPS: return
    x = L.deplacer(StocksE1(e.stocks, E.noms), StocksE1(r.stocks, E.noms), E.ids["petrole"], q, "oleoduc")
    L.payer_ou_devoir(r, e, x * p.socle.catalogue["petrole"].prix_monde, "vente_brut", p.socle.creances, p.jour)


def _raffiner(p, E, e, brut):
    """Une heure de raffinerie : le brut entre, chaque coupe sort a son rendement massique ; le gazole va aux stocks du
    moteur ( qui le vend au marche ), les autres produits aux cuves ; l autoconsommation et les pertes restent en masse."""
    L = p.socle.livre; S = StocksE1(e.stocks, E.noms)
    pris = L.consommer(S, E.ids["petrole"], brut, "raffinage")
    kg = pris * COMBUSTIBLES["petrole"].masse_kg
    E.raff["brut_u"] += pris; E.raff["brut_kg"] += kg
    for b, r in RENDEMENTS:
        mk = kg * r
        u = mk / E.combustibles[b].masse_kg
        L.produire(S if b == "carburant" else E.depot.stock, E.ids[b], u, "raffinage")
        if b == "carburant": e.produit_du_jour["carburant"] += u
        E.raff[b + "_kg"] += mk; E.raff[b + "_u"] += u; E.production_jour[b] += u
    E.raff["autoconso_kg"] += kg * AUTOCONSOMMATION; E.raff["pertes_kg"] += kg * PERTES_RAFFINAGE
    t = kg / 1000.0
    E.co2_t["raffinerie"] = E.co2_t.get("raffinerie", 0.0) + kg * AUTOCONSOMMATION * PCI_GAZ_RAFFINERIE * CO2_GAZ_RAFFINERIE / 1e6
    for pol, k in EMIS_RAFFINAGE_KG_T: _emettre(E, e.lieu.id, pol, k * t)
    E.eau_jour[e.lieu.id] = E.eau_jour.get(e.lieu.id, 0.0) + EAU_RAFFINAGE_M3_T * t


# ================================================================== 5 h : le combustible des centrales
def _combustibles(p):
    """Chaque matin, chaque cuve de centrale est completee a 5 jours de marche : le fioul et le gaz par la raffinerie
    de l ile ( payes a son prix de depart ), puis par l import sous 2 jours ( fioul, charbon, gazole des sites sans
    moteur ; pas de gaz importe : une ile sans terminal ). Le gazole des centrales du moteur reste approvisionne par le
    moteur ( convois depuis le marche )."""
    E = p.domaine("energie"); L = p.socle.livre; cat = p.socle.catalogue
    for R in E.reseaux:
        raffinerie_ici = E.depot is not None and E.raffinerie.lieu.ile == R.ile
        for res in R.reservoirs.values():
            besoins = {}
            for u in R.thermiques:
                if u.reservoir is not res: continue
                for b in u.tech.combustibles:
                    if b not in E.combustibles or (b == "carburant" and u.entreprise is not None): continue
                    if b == "gaz" and not raffinerie_ici: continue          # pas de gaz sans raffinerie : le suivant
                    q = mj_combustible(u.tech, u.pmax, FACTEUR_CHARGE * u.pmax) * 24.0 / E.combustibles[b].mj()
                    besoins[b] = besoins.get(b, 0.0) + q
                    break
            for b in sorted(besoins):
                j = besoins[b]; i = E.ids[b]
                manque = JOURS_STOCK * j - res.stock[i]
                if manque <= EPS: continue
                if raffinerie_ici and b in dict(RENDEMENTS):
                    q = min(manque, E.depot.stock[i])
                    if q > EPS:
                        L.deplacer(E.depot.stock, res.stock, i, q, "livraison_combustible")
                        L.payer_ou_devoir(res.proprietaire, E.raffinerie, q * cat[b].prix_monde, "vente_combustible",
                                          p.socle.creances, p.jour)
                        manque -= q
                if b in ("gaz", "charbon") or res.stock[i] >= JOURS_MINI * j: continue
                prix = cat[b].prix_monde * (1.0 + FRET_IMPORT)
                paye = L.payer_l_exterieur(res.proprietaire, manque * prix, "import_combustible")
                if paye > EPS:
                    L.importer(res.stock, i, paye / prix, "import_combustible")
                    p.compter("import_combustible", paye)


# ================================================================== 23 h 50 : la journee se ferme
def _fin_de_jour(p):
    E = p.domaine("energie"); w = p.w; L = p.socle.livre
    tarif = _tarif_kwh(p)
    rev = _reversement(p)
    moteur_tot = sum(sum(c.d_serv for c in R.charges if c.type == MOTEUR) for R in E.reseaux)
    for R in E.reseaux:
        G = R.gestionnaire
        recu = 0.0
        # les commerces et l Etat : tertiaire et eclairage des zones de l ile
        par_marche = {}
        public = 0.0
        for c in R.charges:
            if c.type == ZONE:
                m = _lieu(p, c.lieu).marche
                par_marche[m.id] = par_marche.get(m.id, 0.0) + c.d_ter * PART_COMMERCE
                public += c.d_ter * (1.0 - PART_COMMERCE) + (c.d_ecl if E.eclairage_payeur is None else 0.0)
            elif c.type == SITE: recu += _facturer(p, E, c.entreprise, G, c.d_serv * tarif)
            elif c.type == CONTRAT: recu += _facturer(p, E, c.payeur, G, c.d_serv * tarif)
        for mid in sorted(par_marche): recu += _facturer(p, E, w.marches[mid], G, par_marche[mid] * tarif)
        if E.eclairage_payeur is not None:
            recu += _facturer(p, E, E.eclairage_payeur, G, sum(c.d_ecl for c in R.charges if c.type == ZONE) * tarif)
        recu += _facturer(p, E, w.gouv, G, public * tarif)
        # ce que les sites du moteur ont paye a l Etat pour l electricite, au prorata de ce que chaque ile leur a livre
        part = sum(c.d_serv for c in R.charges if c.type == MOTEUR) / moteur_tot if moteur_tot > 0 else (1.0 if R.rang == 0 else 0.0)
        if rev * part > EPS: recu += L.transferer(w.gouv, G, rev * part, "facture_electricite")
        for payeur in sorted(R.soutirages, key=lambda x: str(getattr(x, "id", getattr(x, "nom", "")))):
            recu += _facturer(p, E, payeur, G, R.soutirages[payeur] * tarif)
        R.soutirages = {}
        # l achat aux centrales : combustible et exploitation + 10 %, et la capacite
        dus = {}
        for u in R.thermiques:
            if u.entreprise is None: continue
            dus[u.entreprise] = dus.get(u.entreprise, 0.0) + u.j_cout * (1.0 + MARGE_PRODUCTEUR) + u.pmax * CAPACITE_DR_KW_AN / JOURS_AN
        total = math.fsum(dus.values())
        for cr in list(p.socle.creances.de(G)): total += cr.montant
        # ses propres groupes ( une ile sans centrale du moteur ) : le combustible de demain matin se paie avec sa caisse
        propres = FONDS_ROULEMENT_J * math.fsum(u.j_cout for u in R.thermiques if u.entreprise is None)
        if G.caisse < total + propres:
            x = L.transferer(w.gouv, G, total + propres - G.caisse, "compensation_service_public")
            E.compensation += x
        for cr in list(p.socle.creances.de(G)): p.socle.creances.regler(cr, L)
        for e in sorted(dus, key=lambda e: e.id):
            L.payer_ou_devoir(G, e, dus[e], "achat_electricite_producteur", p.socle.creances, p.jour)
        plafond = PLAFOND_CAISSE_J * max(total + propres / FONDS_ROULEMENT_J, 1.0)
        if G.caisse > plafond:
            E.redevance += L.transferer(G, w.gouv, G.caisse - plafond, "redevance_gestionnaire")
        _journee_ile(p, E, R, recu, total)
    _factures_menages(p, E, tarif)
    _exporter(p, E)
    _importer_gazole(p, E)
    _redevance_petroliere(p, E)
    _eau_et_rejets(p, E)
    _noter_zones(p, E)
    for u in E.unites: u.j_kwh = u.j_cout = u.j_mj = 0.0


def _facturer(p, E, payeur, G, montant):
    if montant <= EPS or payeur is None: return 0.0
    paye = p.socle.livre.transferer(payeur, G, montant, "facture_electricite")
    E.factures += paye
    if montant - paye > EPS: E.impayes += montant - paye; p.compter("facture_impayee", montant - paye)
    return paye


def _reversement(p):
    """Ce que les sites du moteur ont paye a l Etat pour l electricite aujourd hui ( Monde.produire ) : l Etat le reverse
    au gestionnaire, qui a fourni cette electricite. Lu dans le grand livre du jour."""
    return p.socle.livre.jour_argent.get(("electricite", "Entreprise", "Gouvernement"), (0.0, 0))[0]


def _factures_menages(p, E, tarif):
    """Le residentiel servi de chaque zone est reparti sur ses menages par personne ; chaque menage paie sa facture tous
    les 30 jours ( decale par menage ) ; ce qu il ne peut pas payer reste en arrieres."""
    w = p.w
    n = len(E.mg_zone)
    if n == 0 or not E.zones: return
    res = np.array([c.d_res for c in E.zones]); hab = np.array([max(EPS, c.hab) for c in E.zones])
    zi = E.mg_zone
    ok = zi >= 0
    du = p.col("menage", "en_du"); arr = p.col("menage", "en_arrieres")
    add = np.zeros(n)
    add[ok] = res[zi[ok]] * E.mg_viv[ok] / hab[zi[ok]] * tarif
    du[:n] += add
    ids = np.arange(n)
    for i in np.nonzero(ok & ((ids + p.jour) % JOURS_FACTURE == 0) & (du[:n] + arr[:n] > EPS))[0].tolist():
        mg = w.menages[i]
        G = E.par_ile[E.zones[int(zi[i])].ile].gestionnaire
        voulu = float(du[i] + arr[i])
        paye = p.socle.livre.transferer(mg, G, voulu, "facture_electricite")
        E.factures += paye
        du[i] = 0.0; arr[i] = voulu - paye
        if voulu - paye > EPS: E.impayes += voulu - paye; p.compter("facture_impayee", voulu - paye)


def _exporter(p, E):
    """Chaque soir, la raffinerie garde 3 jours de sa production recente ( plus 5 jours de ce que les centrales de l ile
    brulent, pour le fioul et le gaz ) et exporte le reste au prix mondial moins le transport : une raffinerie vend en
    continu, sinon sa tresorerie dort dans ses cuves et elle ne peut plus acheter son brut."""
    if E.depot is None: return
    L = p.socle.livre; cat = p.socle.catalogue
    R = E.par_ile[E.depot.ile]
    for b, _ in RENDEMENTS:
        E.production_7j[b].append(E.production_jour[b]); E.production_jour[b] = 0.0
        if b == "carburant": continue
        garde = STOCK_TAMPON_J * sum(E.production_7j[b]) / len(E.production_7j[b])
        if b in ("fioul", "gaz"):
            garde += sum(JOURS_STOCK * mj_combustible(u.tech, u.pmax, FACTEUR_CHARGE * u.pmax) * 24.0 / E.combustibles[b].mj()
                         for u in R.thermiques if u.tech.combustibles[0] == b)
        i = E.ids[b]
        if E.depot.stock[i] <= garde + EPS: continue
        q = L.exporter(E.depot.stock, i, E.depot.stock[i] - garde, "export_petrolier")
        x = L.recevoir_de_l_exterieur(E.raffinerie, q * cat[b].prix_monde * (1.0 - DECOTE_EXPORT), "export_petrolier")
        p.compter("export_petrolier", x)


def _importer_gazole(p, E):
    """Le raffineur est aussi l importateur des produits ( comme les raffineurs grecs ) : quand les stocks de gazole du
    pays ( marches et raffinerie ) tombent sous 5 jours de la demande que les marchands observent ( domaine 3 ) et que le
    prix de gros ( ce que le marche de sa region lui paie ) depasse la parite import ( prix mondial + fret ), il importe
    de quoi revenir a la cible, au
    plus 3 jours de demande, dans ses propres stocks : le moteur l expedie au marche comme sa production. Les rendements
    reels ( 39 % de gazole, contre 80 % dans la recette du moteur ) laissent le pays court en gazole sans cela."""
    if E.raffinerie is None: return
    w = p.w; L = p.socle.livre
    d = p.domaine("economie")
    dem = sum(d.marches[k].demande_lisse["carburant"] for k in d.marches)
    stock = sum(m.stocks["carburant"] for m in w.marches.values()) + E.raffinerie.stocks.get("carburant", 0.0)
    parite = p.socle.catalogue["carburant"].prix_monde * (1.0 + FRET_IMPORT)
    gros = prix_depart(p, "carburant")        # ce que le marche paie au raffineur : le prix affiche moins la marge du detaillant
    if dem <= 0 or stock >= COUVERTURE_GAZOLE_J * dem or gros <= parite: return
    q = min(COUVERTURE_GAZOLE_J * dem - stock, IMPORT_GAZOLE_MAX_J * dem)
    paye = L.payer_l_exterieur(E.raffinerie, q * parite, "import_combustible")
    if paye > EPS:
        L.importer(StocksE1(E.raffinerie.stocks, E.noms), E.ids["carburant"], paye / parite, "import_combustible")
        p.compter("import_combustible", paye)


def _redevance_petroliere(p, E):
    if E.puits is None or E.extrait_jour <= 0: return
    p.socle.livre.transferer(E.puits, p.w.gouv, E.extrait_jour * p.socle.catalogue["petrole"].prix_monde * REDEVANCE_HYDROCARBURES,
                             "redevance_hydrocarbures")
    E.extrait_jour = 0.0


def _eau_et_rejets(p, E):
    """L eau douce du jour est prelevee au bassin de chaque site ; les polluants du jour sont rejetes a son lieu."""
    for lieu in sorted(E.eau_jour):
        m3 = E.eau_jour[lieu]
        if m3 <= EPS: continue
        livre = TER.prelever(p, lieu, m3, "energie")
        if m3 - livre > 1e-6: p.compter("manque_eau_energie", m3 - livre)
    for (lieu, pol) in sorted(E.emis_jour):
        TER.rejeter(p, lieu, pol, E.emis_jour[(lieu, pol)])
    E.eau_jour = {}; E.emis_jour = {}


def _noter_zones(p, E):
    """La note du jour de chaque zone qui attend la sienne, puis la memoire des delestages sur 7 jours."""
    dec = E.decideur
    for R in E.reseaux:
        for c in R.charges:
            voulu = c.d_serv + c.d_del + c.d_cut + c.d_eff
            if c.type == ZONE and c.cle in dec.attentes:
                r = -(c.d_del + KAPPA_EFFACEMENT * c.d_eff) / voulu if voulu > EPS else 0.0
                dec.noter(c.cle, r, p.jour)
            if c.type == ZONE and voulu > EPS: c.part_res = (c.d_res + c.d_eff) / voulu
            c.h_del7 = c.h_del7[1:] + [c.d_h_del]
            c.c_dem += voulu; c.c_serv += c.d_serv; c.c_del += c.d_del; c.c_cut += c.d_cut
            c.d_serv = c.d_del = c.d_cut = c.d_eff = c.d_res = c.d_ter = c.d_ecl = 0.0
            c.d_h_del = 0
    for cle in [k for k, a in dec.attentes.items() if not a.choix]: del dec.attentes[cle]


def _journee_ile(p, E, R, recu, achats):
    """Le resume du jour d une ile, puis le journal horaire d hier devient la prevision de demain."""
    H = R.h
    tarif = _tarif_kwh(p)
    prod = {t: float(H[t].sum()) for t in NOMS_TECH}
    cout = sum(u.j_cout for u in R.thermiques)
    R.serie.append({"jour": p.jour, "demande": float(H["demande"].sum()), "servi": float(H["servi"].sum()),
                    "ens_delestage": float(H["ens_delestage"].sum()), "ens_coupure": float(H["ens_coupure"].sum()),
                    "efface": float(H["efface"].sum()), "pertes": float(H["pertes"].sum()), "ecrete": float(H["ecrete"].sum()),
                    "production": prod, "pointe": float(H["besoin"].max()), "tarif": tarif,
                    "cout_marginal_moyen": float(np.average(H["cout_marginal"], weights=np.maximum(H["injection"], EPS))),
                    "cout_moyen": (cout / max(EPS, sum(prod[t] for t in THERMIQUES))) if cout > 0 else 0.0,
                    "recettes": recu, "achats": achats,
                    "co2_t_pays": sum(E.co2_t.values())})
    for k in NOMS_TECH: R.cumul[k] += prod[k]
    R.cumul["ens_coupure"] += float(H["ens_coupure"].sum())
    R.cut_jour = 0.0
    R.hier = {k: v.copy() for k, v in H.items()}
    R.h = _journal_horaire()


def _cloture(p, comptes):
    """Les mouvements de biens clos du jour sous les motifs du domaine, pour les bilans."""
    E = p.domaine("energie")
    for n, m, b, q in comptes["biens"]:
        if m in MOTIFS_BIENS: E.livre_biens[(n, m, b)] = E.livre_biens.get((n, m, b), 0.0) + q
    for m, pa, re, s, k in comptes["argent"]:
        if m in MOTIFS_ARGENT: E.argent[m] = E.argent.get(m, 0.0) + s


MOTIFS_BIENS = ("extraction", "raffinage", "combustion_centrale", "production_thermique", "production_eolienne",
                "production_solaire", "production_hydraulique", "charge_batterie", "decharge_batterie", "pertes_stockage",
                "pertes_reseau", "consommation_residentielle", "consommation_tertiaire", "eclairage_public",
                "consommation_sites_energie", "consommation_contrats", "livraison_sites_moteur", "livraison_combustible",
                "import_combustible", "export_petrolier", "stock_reseau_e1", "vente_produit_petrolier", "oleoduc")
MOTIFS_ARGENT = {"facture_electricite": "achat", "achat_electricite_producteur": "achat",
                 "compensation_service_public": "subvention", "redevance_gestionnaire": "revenu_propriete",
                 "dotation_gestionnaire": "transfert_capital", "vente_combustible": "achat", "import_combustible": "achat",
                 "export_petrolier": "achat", "redevance_hydrocarbures": "revenu_propriete",
                 "vente_produit_petrolier": "achat", "vente_brut": "achat"}


# ================================================================== l API des autres domaines
def tarif(p):
    """Le tarif reglemente, drachmes par kWh ( celui que l aube du moteur fixe, en unites de 10 kWh )."""
    return _tarif_kwh(p)


def cout_marginal(p, ile, heure=None):
    """Le cout marginal du systeme d une ile, drachmes par kWh, a l heure demandee ( la derniere conduite sinon ) ;
    la valeur de l energie non servie quand il a fallu delester."""
    R = p.domaine("energie").par_ile[ile]
    h = int(p.heure) if heure is None else int(heure)
    return float(R.h["cout_marginal"][h] if R.h["injection"][h] > 0 else (R.hier["cout_marginal"][h] if R.hier else 0.0))


def abonner(p, cle, lieu, payeur, kw, heures=None, prioritaire=False):
    """Un contrat de fourniture ( domaine 12 : pompage ; 17 : hopital ; 10 : usine ) : `kw` pendant les heures
    `heures` ( 24 booleens, toutes par defaut ), paye par `payeur` au tarif, chaque soir. Un contrat prioritaire n est
    delesta qu apres tout le reste. Rend la Charge."""
    E = p.domaine("energie")
    lid = lieu if isinstance(lieu, str) else lieu.id
    if cle in E.contrats: raise ValueError(f"contrat {cle!r} deja pose")
    if not 0.0 <= kw < 1e7: raise ValueError(f"puissance invalide {kw!r}")
    l = p.w.carte.lieux[lid]
    R = E.par_ile[l.ile]
    c = Charge(cle, l.ile, CONTRAT, lid, len(R.charges), payeur=payeur, kw=kw, heures=heures, prioritaire=prioritaire)
    zone = R.par_lieu.get(lid)
    if zone is not None: c.coupe_jusqu = zone.coupe_jusqu
    R.charges.append(c); E.contrats[cle] = c
    return c


def resilier(p, cle):
    E = p.domaine("energie")
    c = E.contrats.pop(cle)
    E.par_ile[c.ile].charges.remove(c)


def servi(p, cle):
    """( part servie a la derniere heure, kWh servis aujourd hui, kWh non servis aujourd hui ) d un contrat."""
    c = p.domaine("energie").contrats[cle]
    return c.servi_h, c.d_serv, c.d_del + c.d_cut


def coupure_en_cours(p, lieu):
    """Vrai si la zone du lieu est sans courant a cette heure ( delestee ou ligne coupee ) : l alimentation de secours
    d un hopital ( domaine 17 ) demarre."""
    E = p.domaine("energie")
    lid = lieu if isinstance(lieu, str) else lieu.id
    R = E.par_ile.get(p.w.carte.lieux[lid].ile)
    c = R.par_lieu.get(lid) if R is not None else None
    return c is not None and (c.servi_h <= 0.0 or c.coupe_jusqu > p.w.pas)


def soutirer(p, lieu, kwh, payeur):
    """Un soutirage immediat de `kwh` au lieu : servi par la marge des groupes deja en ligne ( la reserve tournante ),
    qui brulent le combustible de l increment ; paye au tarif le soir. Rien si la zone est coupee. Rend les kWh servis."""
    E = p.domaine("energie"); L = p.socle.livre
    if coupure_en_cours(p, lieu) or kwh <= 0: return 0.0
    R = E.par_ile[p.w.carte.lieux[lieu if isinstance(lieu, str) else lieu.id].ile]
    h = int(p.heure)
    inj = kwh / (1.0 - PERTES_RESEAU)
    reste = inj; fait = 0.0
    for u, b, pmin, pmax, cout in sorted(_groupes(p, E, R), key=lambda g: (g[4], g[0].id)):
        mj_dispo = _dispo_unites(E, _porteur(E, u, b), b) * E.combustibles[b].mj()
        x = min(reste, max(0.0, mj_dispo * u.tech.rendement / (MJ_KWH * (1.0 - u.tech.part_a_vide))),
                max(0.0, u.pmax - R.h[u.tech.nom][h]))
        if x <= EPS: continue
        cb = E.combustibles[b]
        mj = MJ_KWH * (1.0 - u.tech.part_a_vide) * x / u.tech.rendement
        brule = L.bruler(_porteur(E, u, b), E.ids[b], mj / cb.mj(), "combustion_centrale")
        mj = brule * cb.mj()
        u.c_unites[b] = u.c_unites.get(b, 0.0) + brule
        u.c_mj += mj; u.c_kwh += x; u.c_perte_mj += mj - MJ_KWH * x; u.j_kwh += x; u.j_mj += mj
        u.j_cout += brule * _prix_unitaire(p, E, b, _lieu(p, u.lieu))
        R.h[u.tech.nom][h] += x
        E.co2_t[u.tech.nom] = E.co2_t.get(u.tech.nom, 0.0) + mj * cb.co2 / 1e6
        _emettre(E, u.lieu, "so2", 2.0 * cb.soufre * brule * cb.masse_kg)
        _emettre(E, u.lieu, "no2", u.tech.nox * x / 1000.0); _emettre(E, u.lieu, "pm25", u.tech.pm25 * x / 1000.0)
        E.eau_jour[u.lieu] = E.eau_jour.get(u.lieu, 0.0) + u.tech.eau * x / 1000.0
        reste -= x; fait += x
        if reste <= EPS: break
    if fait <= EPS: return 0.0
    G = R.gestionnaire; el = E.elec
    L.produire(G.stock, el, fait / KWH_UNITE, "production_thermique")
    servi_kwh = fait * (1.0 - PERTES_RESEAU)
    L.consommer(G.stock, el, servi_kwh / KWH_UNITE, "consommation_contrats")
    pertes = L.perdre(G.stock, el, G.stock[el], "pertes_reseau") * KWH_UNITE
    R.h["injection"][h] += fait; R.h["pertes"][h] += pertes; R.h["demande"][h] += servi_kwh; R.h["servi"][h] += servi_kwh
    R.h["besoin"][h] += fait              # la prevision de demain engagera des groupes pour cette charge
    R.h["contrats"][h] += servi_kwh
    R.cumul["injection"] += fait; R.cumul["pertes"] += pertes; R.cumul["demande"] += servi_kwh; R.cumul["servi"] += servi_kwh
    R.cumul["production"] += fait
    R.soutirages[payeur] = R.soutirages.get(payeur, 0.0) + servi_kwh
    return servi_kwh


def prix_depart(p, bien):
    """Le prix de depart raffinerie d un produit, drachmes par unite : le gazole au prix ou le marche de la region le
    rachete, les autres au prix mondial du catalogue."""
    E = p.domaine("energie")
    if bien == "carburant":
        m = p.w.marches[E.raffinerie.lieu.marche.id]
        return m.prix["carburant"] * (1.0 - m.marge)
    return p.socle.catalogue[bien].prix_monde


def stock_produit(p, bien):
    E = p.domaine("energie")
    if E.raffinerie is None: return 0.0
    return E.raffinerie.stocks.get("carburant", 0.0) if bien == "carburant" else E.depot.stock[E.ids[bien]]


def vendre_produit(p, acheteur, bien, q, vers):
    """La raffinerie vend `q` unites d un produit ( carburant, essence, kerosene, fioul, gaz ) a `acheteur` ( domaine 14 :
    stations-service ; 26 : carburant militaire ), livrees a `vers` : un detenteur a Stock du socle ( attribut stock ),
    ou un dictionnaire de stocks du moteur ( un stock public, une garnison ). Payee au prix de depart. Rend la quantite
    vendue."""
    E = p.domaine("energie"); L = p.socle.livre
    if bien not in ("carburant",) + tuple(b for b, _ in RENDEMENTS): raise ValueError(f"produit inconnu {bien!r}")
    if E.raffinerie is None or q <= 0: return 0.0
    prix = prix_depart(p, bien)
    source = StocksE1(E.raffinerie.stocks, E.noms) if bien == "carburant" else E.depot.stock
    q = min(q, stock_produit(p, bien), max(0.0, acheteur.caisse) / prix)
    if q <= EPS: return 0.0
    paye = L.transferer(acheteur, E.raffinerie, q * prix, "vente_produit_petrolier")
    cible = StocksE1(vers, E.noms) if isinstance(vers, dict) else (vers if hasattr(vers, "_ajouter") else vers.stock)
    return L.deplacer(source, cible, E.ids[bien], paye / prix, "vente_produit_petrolier")


def livrer_combustible(p, de, bien, q, vendeur, prix_unitaire, ile=None):
    """Un fournisseur ( domaine 10 : charbon ) livre `q` unites de `bien` aux cuves des centrales qui le brulent sur
    l ile ; le proprietaire des cuves paie `vendeur` a `prix_unitaire`. `de` : un detenteur a Stock du socle. Rend la
    quantite livree."""
    E = p.domaine("energie"); L = p.socle.livre
    if bien not in E.combustibles: raise ValueError(f"combustible inconnu {bien!r}")
    for R in E.reseaux:
        if ile is not None and R.ile != ile: continue
        for u in R.thermiques:
            if bien not in u.tech.combustibles or u.reservoir is None: continue
            src = de if hasattr(de, "_retirer") else de.stock
            x = L.deplacer(src, u.reservoir.stock, E.ids[bien], q, "livraison_combustible")
            if x > 0: L.payer_ou_devoir(u.reservoir.proprietaire, vendeur, x * prix_unitaire, "vente_combustible", p.socle.creances, p.jour)
            return x
    return 0.0


def reprendre_eclairage(p, payeur):
    """Le domaine 12 prend l eclairage public en charge : il reste dans la demande des zones, mais `payeur` le paie."""
    p.domaine("energie").eclairage_payeur = payeur


def forcer_panne(p, ile, technologie=None, n=None, heures=24.0, cause="forcee"):
    """Met en panne `n` groupes ( tous par defaut ) d une technologie ( ou de toutes ) d une ile, pour `heures` heures
    ( porte, sabotage, domaine 27 ). Rend les groupes touches."""
    E = p.domaine("energie")
    R = E.par_ile[ile]
    us = [u for u in R.thermiques + R.renouvelables if (technologie is None or u.nom_tech() == technologie) and not u.en_panne]
    us.sort(key=lambda u: (-u.pmax, u.id))
    for u in us[:n] if n is not None else us: _panne(p, E, u, heures, cause)
    return us[:n] if n is not None else us


def couper_ligne(p, lieu, jours, cause="forcee"):
    """La ligne qui alimente un lieu est coupee pendant `jours` jours ( seisme, tempete, sabotage ) : sa zone et les
    contrats du lieu ne sont plus alimentes."""
    E = p.domaine("energie")
    lid = lieu if isinstance(lieu, str) else lieu.id
    R = E.par_ile[p.w.carte.lieux[lid].ile]
    fin = p.w.pas + int(round(jours * C.PAS_PAR_JOUR))
    touche = False
    for c in R.charges:
        if c.lieu == lid and fin > c.coupe_jusqu: c.coupe_jusqu = fin; touche = True
    if touche: p.noter("coupure_ligne", lieu=lid, cause=cause, jours=jours)


def bilan_electricite(p):
    """Par ile : production + decharge - charge - consommations - livraison aux sites - pertes - variation du stock en
    transit ( kWh ), lu dans le grand livre sous les motifs du domaine, et la batterie : son stock moins ce que les
    charges et decharges comptees y ont laisse. Zero partout, sinon de l electricite est nee hors production."""
    E = p.domaine("energie")
    lb = _livre_biens(p)
    el = p.socle.catalogue[E.elec].nom
    g = lambda n, m: lb.get((n, m, el), 0.0) * KWH_UNITE
    prod = sum(g("produit", m) for m in ("production_thermique", "production_eolienne", "production_solaire", "production_hydraulique"))
    cons = sum(g("consomme", m) for m in ("consommation_residentielle", "consommation_tertiaire", "eclairage_public",
                                         "consommation_sites_energie", "consommation_contrats"))
    moteur = g("deplace", "livraison_sites_moteur")
    pertes = g("perdu", "pertes_reseau") + g("perdu", "pertes_stockage")
    stock_g = sum(R.gestionnaire.stock[E.elec] for R in E.reseaux) * KWH_UNITE
    stock_b = sum(b.stock[E.elec] for b in E.batteries) * KWH_UNITE
    reseau = prod - cons - moteur - pertes - stock_g - stock_b
    batt = sum(b.stock[E.elec] * KWH_UNITE - (b.c_charge * ETA_CH - b.c_decharge / ETA_DE) for b in E.batteries)
    compte = sum(R.cumul["production"] for R in E.reseaux) - prod
    return {"reseau_kwh": reseau, "batterie_kwh": batt, "production_comptee_kwh": compte, "production_kwh": prod,
            "tolerance": 1e-9 * max(1.0, prod)}


def _livre_biens(p):
    """Les mouvements de biens sous mes motifs : jours clos plus le jour en cours."""
    E = p.domaine("energie")
    out = dict(E.livre_biens)
    cat = p.socle.catalogue
    for (n, m, b), q in p.socle.livre.jour_biens.items():
        if m in MOTIFS_BIENS:
            k = (n, m, cat[b].nom); out[k] = out.get(k, 0.0) + q
    return out


def bilan_combustion(p):
    """Pour chaque groupe thermique : combustible ( MJ ) - electricite ( MJ ) - chaleur perdue ; le rendement a pleine
    charge ; et pour chaque combustible, les unites que les groupes disent avoir brulees moins celles que le grand
    livre a vu bruler sous le motif combustion_centrale."""
    E = p.domaine("energie")
    lb = _livre_biens(p)
    groupes = {}
    brule = {}
    for u in E.unites:
        if u.genre != "thermique": continue
        groupes[u.id] = {"technologie": u.tech.nom, "ecart_mj": u.c_mj - MJ_KWH * u.c_kwh - u.c_perte_mj, "mj": u.c_mj,
                         "kwh": u.c_kwh, "rendement_plein": (MJ_KWH * u.c_kwh_pleine / u.c_mj_pleine) if u.c_mj_pleine > 0 else None,
                         "rendement_moyen": (MJ_KWH * u.c_kwh / u.c_mj) if u.c_mj > 0 else None, "nominal": u.tech.rendement,
                         "heures_pleines": u.c_pleine_h, "heures": u.c_heures}
        for b, q in u.c_unites.items(): brule[b] = brule.get(b, 0.0) + q
    ecarts = {b: brule[b] - lb.get(("brule", "combustion_centrale", b), 0.0) for b in brule}
    return groupes, ecarts


def bilan_raffinerie(p):
    """La masse de brut moins les coupes, l autoconsommation et les pertes ( kg ) ; les parts de chaque coupe en masse
    et en volume ; les unites produites que le grand livre a vues sous le motif raffinage."""
    E = p.domaine("energie")
    r = E.raff
    kg = r["brut_kg"]
    sortie = math.fsum([r[b + "_kg"] for b, _ in RENDEMENTS] + [r["autoconso_kg"], r["pertes_kg"]])
    lb = _livre_biens(p)
    vu = {b: lb.get(("produit", "raffinage", b), 0.0) for b, _ in RENDEMENTS}
    return {"brut_kg": kg, "ecart_kg": kg - sortie,
            "masse": {b: r[b + "_kg"] / kg if kg > 0 else 0.0 for b, _ in RENDEMENTS},
            "volume": {b: r[b + "_u"] / r["brut_u"] if r["brut_u"] > 0 else 0.0 for b, _ in RENDEMENTS},
            "ecart_livre": {b: vu[b] - r[b + "_u"] for b, _ in RENDEMENTS},
            "brut_livre": lb.get(("consomme", "raffinage", "petrole"), 0.0) - r["brut_u"]}


def emissions(p):
    """Le CO2 cumule par source ( t ), et ce que le territoire a recu de SO2, NO2 et PM2,5 depuis l installation ( kg ) ne
    se lit que chez lui ( bilan_pollution ) : ici l inventaire du CO2, que le territoire ne tient pas."""
    return dict(p.domaine("energie").co2_t)


def resume_jour(p, ile):
    """Le dernier jour clos d une ile ( dict ), ou None."""
    R = p.domaine("energie").par_ile[ile]
    return R.serie[-1] if R.serie else None


# ================================================================== installation
def _neutraliser_repris_corrige(p):
    """CONTOURNEMENT ( le meme que celui du domaine 9 ), a retirer quand pays.py sera corrige : pays._neutraliser_repris
    lit w.entreprises[ e.id ], or le moteur indexe w.entreprises par l identifiant du LIEU ( monde.py :
    self.entreprises[ l.id ] ) et e.id vaut « centrale@PowerPlant01 » : KeyError a 6 h 10 des la premiere reprise. Meme
    effet, par une passe sur les entreprises."""
    rep = p.repris
    for e in p.w.entreprises.values():
        if e.id in rep: e.activite = 0.0


def _contourner_neutralisation(p):
    """Remplace, dans la table des routines ( une donnee ), la neutralisation du pays par sa version corrigee - seulement
    si le bogue se declencherait ( un identifiant repris qui n est pas une cle de w.entreprises )."""
    if all(eid in p.w.entreprises for eid in p.repris): return
    for lst in p.routines.values():
        for k, (o, dom, fn) in enumerate(lst):
            if getattr(fn, "__name__", "") == "_neutraliser_repris" and dom == "pays":
                lst[k] = (o, dom, _neutraliser_repris_corrige)


def _declarer_biens(p):
    cat = p.socle.catalogue
    for b, (fam, unite, masse, vol) in UNITES_NOUVEAUX.items():
        cat.declarer(b, fam, unite, PRIX_NOUVEAUX[b], categorie_tva="normale", masse_kg=masse, volume_l=vol,
                     source=COMBUSTIBLES[b].source + " ; prix : cotations 2024-2025, a calibrer")
    # la calibration des biens du moteur qui sont a l energie : masse et volume de l unite
    for b, masse, vol, unite in (("petrole", 8.6, 10.0, "10 litres de brut ( 8,6 kg, ~0,1 MWh PCI )"),
                                 ("carburant", 8.4, 10.0, "10 litres de gazole ( 8,4 kg ) : 0,03 unite par km = 30 l aux 100 km d un camion"),
                                 ("electricite", 0.0, 0.0, "10 kWh ( ne se transporte que par le reseau )")):
        x = cat[b]; x.masse_kg, x.volume_l, x.unite = masse, vol, unite
        x.source = "domaine 11 : " + unite
    combs = dict(COMBUSTIBLES)
    if "charbon" in cat.par_nom and cat["charbon"].masse_kg:
        pci, co2, s = CHARBON
        if p.a("industrie"):
            ind = importlib.import_module(".d10_industrie", __package__)
            pci = getattr(ind, "CHARBON_PCI_MJ_KG", pci); co2 = getattr(ind, "CHARBON_CO2_T_TJ", co2)
            s = getattr(ind, "CHARBON_SOUFRE", s)
        combs["charbon"] = Combustible("charbon", cat["charbon"].masse_kg, pci, co2, s,
                                       "lignite du domaine 10 : sa masse, son PCI, son CO2 et son soufre")
    return combs


def _declarer_modeles(p):
    parc = p.socle.parc
    for t in THERMIQUES.values():
        parc.declarer_modele(t.modele, "machine", t.capital * 1000.0, 20000.0, t.vie_ans * 8760.0, arma=t.arma,
                             source="le MW de reference : " + t.source)
    for g, (mtbf, mttr, cap, vie, mod, arma, masse, src) in RENOUVELABLES.items():
        parc.declarer_modele(mod, "machine", cap * 1000.0, masse, vie * 8760.0, arma=arma, source="le MW de reference : " + src)


def _dimensionner(p, E, R):
    """La pointe d un jour chaud ( normale du mois le plus chaud + 4 degres ) : zones, sites a leur effectif, pertes."""
    pr = TER.PROFILS[R.ile]
    tmax, tmin = float(pr.tmax.max()) + 4.0, float(pr.tmin.max()) + 4.0
    temp = (tmax + tmin) / 2 + (tmax - tmin) / 2 * np.cos(2 * np.pi * (np.arange(24) - HEURE_TMAX) / 24.0)
    R.nuit = np.where((np.arange(24) < 6) | (np.arange(24) >= 21), 1.0, 0.0)
    sites = _sites_nominal_kw(p, E, R)
    zones = max(sum(a + b + c for a, b, c in _demande_zones(R, h, _clim(temp[h]), 1.0, 1.0)) for h in range(24))
    return (zones + sites) / (1.0 - PERTES_RESEAU)


def _batir_ile(p, E, R, ile, col):
    """Les charges, les groupes, les cuves et la batterie d une ile."""
    w = p.w; L = p.socle.livre; parc = p.socle.parc; cat = p.socle.catalogue
    lieux = sorted((l for l in w.carte.lieux.values() if l.ile == ile), key=lambda l: l.id)
    for l in lieux:
        if l.type in ("capitale", "ville", "village"):
            c = Charge(l.id, ile, ZONE, l.id, len(R.charges)); R.charges.append(c); R.par_lieu[l.id] = c; E.zones.append(c)
    for e in sorted(w.entreprises.values(), key=lambda e: e.id):
        if e.lieu.ile != ile: continue
        if e.type in ("puits", "raffinerie"):
            p.reprendre(e, "energie")
            # le puits et la raffinerie alimentent les centrales : les delester affame le reseau lui-meme ( mesure du 23/09 :
            # proteger les menages en coupant la raffinerie faisait tomber les groupes au gazole a sec ) ; ils passent
            # avec les contrats prioritaires
            c = Charge(e.id, ile, SITE, e.lieu.id, len(R.charges), entreprise=e, prioritaire=True)
            R.charges.append(c); R.par_lieu[e.lieu.id] = c
            if e.type == "puits": E.puits = e
            else: E.raffinerie = e
        elif e.type == "centrale":
            p.reprendre(e, "energie"); R.centrales.append(e)
        elif e.intrants.get("electricite", 0.0) > 0: R.sites_moteur.append(e)
    R.charges.append(Charge(f"sites_moteur@{ile}", ile, MOTEUR, None, len(R.charges)))
    _recenser(p, E)
    R.pointe_estimee = _dimensionner(p, E, R)
    thermique = MARGE_THERMIQUE * R.pointe_estimee
    # les sites : les centrales du moteur, la plus proche de la raffinerie d abord ; a defaut le port de l ile
    sites = sorted(R.centrales, key=lambda e: (e.lieu.distance(E.raffinerie.lieu) if E.raffinerie is not None
                                              and E.raffinerie.lieu.ile == ile else 0.0, e.id))
    port = w.carte.port(ile) or lieux[0]
    def site(k):
        if sites:
            e = sites[k % len(sites)]
            return e.lieu.id, e, e
        return port.id, None, R.gestionnaire
    def reservoir(lid, proprio):
        res = R.reservoirs.get(lid)
        if res is None:
            res = Reservoir(f"cuves@{lid}", lid, ile, proprio, BI.Stock())
            R.reservoirs[lid] = res; E.reservoirs.append(res)
        return res
    mix = list(MIX_THERMIQUE if sites or (E.raffinerie is not None and E.raffinerie.lieu.ile == ile) else MIX_PETITE_ILE)
    if "charbon" in E.combustibles and p.a("industrie") and sites:
        mix = [("vapeur_charbon", 1, 0.20), ("diesel_fioul", 2, 0.20)] + mix[1:]
    for k, (tn, n, part) in enumerate(mix):
        t = THERMIQUES[tn]
        for _ in range(n):
            lid, e, proprio = site(k)
            res = reservoir(lid, proprio)
            pmax = part * thermique
            obj = parc.creer(t.modele, proprio, lid, "initial", w.pas, usure=ECO.AMORTI_AU_DEPART)
            u = Unite(len(E.unites), ile, "thermique", t, pmax, lid, e, res, proprio, obj, pmax * t.capital, col[0])
            col[0] += 1
            R.thermiques.append(u); E.unites.append(u)
    lid0, e0, _ = site(0)
    for genre, part in (("eolien", PART_EOLIEN), ("solaire", PART_SOLAIRE)):
        g = RENOUVELABLES[genre]
        obj = parc.creer(g[4], R.gestionnaire, lid0, "initial", w.pas, usure=ECO.AMORTI_AU_DEPART)
        u = Unite(len(E.unites), ile, genre, None, part * R.pointe_estimee, lid0, None, None, R.gestionnaire, obj,
                  part * R.pointe_estimee * g[2], col[0])
        col[0] += 1
        R.renouvelables.append(u); E.unites.append(u)
    # l hydraulique : une retenue qui peut faire tourner une turbine 1000 heures par an
    Tt = p.domaine("territoire"); B = Tt.bassins
    for b in range(len(B.nom)):
        if Tt.iles[int(B.ile[b])] != ile: continue
        e_kwh = (B.cap_r[b] - B.min_r[b]) * 1000.0 * 9.81 * CHUTE_M * RENDEMENT_HYDRO / 3.6e6
        kw = e_kwh / HEURES_HYDRO
        if kw < HYDRO_MIN_KW: continue
        g = RENOUVELABLES["hydro"]
        obj = parc.creer(g[4], R.gestionnaire, B.nom[b], "initial", w.pas, usure=ECO.AMORTI_AU_DEPART)
        u = Unite(len(E.unites), ile, "hydro", None, kw, B.nom[b], None, None, R.gestionnaire, obj, kw * g[2], col[0])
        u.bassin = b; col[0] += 1
        R.renouvelables.append(u); E.unites.append(u)
    # la batterie, pres du premier site
    g = RENOUVELABLES["batterie"]
    obj = parc.creer(g[4], R.gestionnaire, lid0, "initial", w.pas, usure=ECO.AMORTI_AU_DEPART)
    R.batterie = Batterie(f"batterie@{ile}", ile, lid0, PART_BATTERIE * R.pointe_estimee,
                          PART_BATTERIE * DUREE_BATTERIE_H * R.pointe_estimee, BI.Stock(), E.elec, obj, col[0])
    col[0] += 1
    E.batteries.append(R.batterie)
    # le capital des centrales du moteur devient celui de leurs groupes ( valeur nette a mi-vie )
    for e in R.centrales:
        us = [u for u in R.thermiques if u.entreprise is e]
        if not us: continue
        ECO.reevaluer_capital(p, e, sum(u.valeur for u in us) * (1.0 - ECO.AMORTI_AU_DEPART),
                              max(u.tech.vie_ans for u in us))


def _stock_initial(p, E):
    """Les cuves des centrales recoivent leurs jours de stock par importation, payee par leur proprietaire : un site ne
    nait pas plein."""
    L = p.socle.livre; cat = p.socle.catalogue
    for R in E.reseaux:
        for u in R.thermiques:
            for b in u.tech.combustibles:
                if b not in E.combustibles or b in ("gaz", "charbon") or (b == "carburant" and u.entreprise is not None): continue
                q = JOURS_STOCK * mj_combustible(u.tech, u.pmax, FACTEUR_CHARGE * u.pmax) * 24.0 / E.combustibles[b].mj()
                prix = cat[b].prix_monde * (1.0 + FRET_IMPORT)
                paye = L.payer_l_exterieur(u.reservoir.proprietaire, q * prix, "import_combustible")
                if paye > EPS: L.importer(u.reservoir.stock, E.ids[b], paye / prix, "import_combustible")
                break


def _commander_lignite(p, E):
    """Les tranches au lignite commandent leur besoin du jour aux mines du domaine 10, qui le livrent chaque apres-midi
    ( livrer_combustible ) : le lignite ne s importe pas."""
    if "charbon" not in E.combustibles or not p.a("industrie"): return
    t = sum(mj_combustible(u.tech, u.pmax, FACTEUR_CHARGE * u.pmax) * 24.0 / E.combustibles["charbon"].mj()
            for R in E.reseaux for u in R.thermiques if "charbon" in u.tech.combustibles)
    ind = importlib.import_module(".d10_industrie", __package__)
    if t > 0 and hasattr(ind, "commander"): ind.commander(p, "charbon", t)


def installer(p):
    w = p.w; L = p.socle.livre
    E = Energie()
    p.domaines["energie"] = E
    E.combustibles = _declarer_biens(p)
    cat = p.socle.catalogue
    E.noms = cat.noms(); E.ids = {n: cat.id(n) for n in E.noms}
    E.elec = E.ids["electricite"]
    for m, nature in MOTIFS_ARGENT.items(): L.declarer_motif(m, nature, "energie")
    J = p.socle.journal
    for t, champs in (("panne_centrale", ("unite", "lieu", "technologie", "heures", "cause")),
                      ("remise_en_service", ("unite", "lieu")), ("delestage_electrique", ("ile", "tranche", "kwh", "charges")),
                      ("coupure_ligne", ("lieu", "cause", "jours")), ("gisement_en_declin", ("lieu", "reste", "depart"))):
        J.declarer(t, "energie", "individuel", champs)
    for t in ("energie_non_servie", "ecretement", "demarrage_groupe", "import_combustible", "export_petrolier",
              "facture_impayee", "manque_combustible", "manque_eau_energie"):
        J.declarer(t, "energie", "compte")
    cm = p.colonnes["menage"]
    cm.ajouter("en_du", np.float64, 0.0); cm.ajouter("en_arrieres", np.float64, 0.0)
    cm.assurer(len(w.menages))
    _declarer_modeles(p)
    TER.reprendre_usage(p, "energie")
    # le stock du reseau du moteur n etait pas physique : l electricite ne se stocke pas sans batterie
    L.perdre(ReseauE1(w.reseau), E.elec, w.reseau.stock, "stock_reseau_e1")
    col = [0]
    for k, ile in enumerate(w.carte.iles):
        pr = TER.PROFILS[ile]
        lat, midi = CAL.SOLEIL.get(ile, (pr.latitude, 13.35))
        G = GestionnaireReseau(ile, BI.Stock())
        E.gestionnaires.append(G)
        R = ReseauIle(ile, k, G, lat, midi)
        E.reseaux.append(R); E.par_ile[ile] = R
    for R in E.reseaux:
        for e in sorted(w.entreprises.values(), key=lambda e: e.id):
            if e.lieu.ile == R.ile and e.type == "raffinerie" and E.depot is None:
                E.depot = Reservoir(f"cuves@{e.lieu.id}", e.lieu.id, R.ile, e, BI.Stock()); E.reservoirs.append(E.depot)
    for R in E.reseaux: _batir_ile(p, E, R, R.ile, col)
    _contourner_neutralisation(p)
    # le gisement et le nominal de la raffinerie
    if E.puits is not None:
        n = _vivants_au_travail(w, E.puits.lieu, E.puits.role)
        E.nominal_puits_j = n * PETROLE_PETROLIER_H * 8.0
        E.gisement = Gisement(max(1.0, E.nominal_puits_j) * JOURS_AN * RESERVES_ANNEES)
    if E.raffinerie is not None:
        n = _vivants_au_travail(w, E.raffinerie.lieu, E.raffinerie.role)
        E.nominal_brut_j = n * DEBIT_OUVRIER_H * 8.0
    reg = p.socle.registre
    reg.inscrire("gestionnaires_reseau", "entreprises", _membres_gestionnaires, "caisse", "stock", "GestionnaireReseau")
    reg.inscrire("reservoirs_energie", "entreprises", _membres_reservoirs, None, "stock", None)
    reg.inscrire("batteries", "entreprises", _membres_batteries, None, "stock", None)
    # les comptes des gestionnaires, et leur dotation : une semaine d achats aux centrales
    bq = p.domaine("banques")
    for R in E.reseaux:
        BQ.ouvrir_compte(p, R.gestionnaire, bq.banques[0])
        dot = DOTATION_J * sum(u.pmax * 24.0 * FACTEUR_CHARGE for u in R.thermiques) * 0.15
        L.transferer(w.gouv, R.gestionnaire, dot, "dotation_gestionnaire")
    _stock_initial(p, E)
    _commander_lignite(p, E)
    for R in E.reseaux:                 # a la reprise, les groupes de base tournent deja : le reseau ne nait pas eteint
        for u in R.thermiques:
            if u.tech.nom == "diesel_fioul" or (u.tech.nom == "diesel_gazole" and not any(x.tech.nom == "diesel_fioul" for x in R.thermiques)):
                u.en_ligne, u.depuis = True, w.pas
    E.decideur = p.decideur(POINT_DELESTAGE)
    for h in range(24): p.routine(h, 40, "energie", _heure)
    p.routine(5, 41, "energie", _combustibles)
    p.routine(23 + 50 / 60, 90, "energie", _fin_de_jour)
    p.cloture("energie", _cloture)
    _debut_de_jour(p, E)
    return E
