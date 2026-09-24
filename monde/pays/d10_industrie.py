"""DOMAINE 10 - INDUSTRIE ET EXTRACTION.

FICHE
1. Classes. Les lois : TypeGisement ( une facon d exploiter : souterraine, ciel ouvert, carriere, lignite ), Recette
   ( une transformation : entrees, sorties, pertes declarees, cadence, secteur, eau, rejets ), ModeleMachine ( la
   fiabilite d un modele : MTBF, Weibull, reparation, entretien ). L etat : Gisement ( reserve finie en tonnes, teneurs,
   rapport de decouverture qui monte avec l epuisement ), Machine ( la vie d un objet du Parc : compteur depuis
   l entretien, panne, entretien en cours ), Atelier ( un gisement ou une recette d un site, sa part de l equipe, ses
   machines, son regime ), Site ( une entreprise du moteur reprise : son stock du socle pour les biens nouveaux ),
   Chargement ( des biens en route entre deux sites ), ContexteEntretien, Industrie ( l etat du domaine ). Aucune
   colonne par habitant : les blessures sont une table eparse ( peu d habitants en ont ).
2. Invariants et ce que le domaine detient. Biens : les biens nouveaux ( cuivre, charbon, calcaire, gypse, sable,
   fonte, acier, ciment, chimie, engrais, plastique, pieces, verre ) vivent dans des Stock du socle ( familles
   industrie_sites et industrie_chargements du registre ), et ne naissent ou ne meurent que par le grand livre, sous les
   motifs du domaine. Les biens du moteur ( fer, zinc, or, outils, electricite, carburant ) restent dans les stocks du
   moteur ; chaque creation ou consommation met a jour livre.flux. AUDIT : pour chaque bien, ce que les recettes et les
   gisements impliquent ( tonnes extraites x rendements, passes x coefficients ) = ce que le grand livre a vu sous les
   motifs du domaine ( porte test_bien_hors_recette ). Chaque recette ferme son bilan matiere : entrees ( biens et
   entrees libres : air, oxygene ) = sorties + pertes declarees ( laitier, gaz, vapeur, chutes ), et son bilan du fer.
   Chaque gisement : reserve + extrait = reserve de depart. Objets : les machines sont des objets du Parc ( famille
   machine ), nees initial, fabrique ou importe, sorties au rebut ( porte test_conservation_machines ). Argent : le
   domaine n en detient pas ; il fait payer l electricite, le carburant, les cessions entre sites, les machines, par
   le grand livre ; le capital des entreprises reprises est reevalue a la valeur de leurs machines ( economie ).
3. Decision `entretenir_machine` ( chaque machine en service d un atelier qui tourne, chaque matin a 6 h 20 : ~ 35
   machines sur Altis decident le meme jour ) : attendre, entretenir ( la machine perd la duree de l entretien sur le
   poste, son compteur d usure repart de zero ). Traits : heures depuis l entretien, usure de vie, pannes des 90 jours,
   risque du poste selon la loi publiee du constructeur, regime de l atelier, redondance, stock aval. Note ( horizon
   30 jours : un cycle d entretien constructeur de 250 heures de service, ~ 31 jours de poste de 8 heures ) : la
   production que CETTE machine perd : l entretien decide se paie tout de suite ( ses heures, en postes ) par le choix
   qui l a decide ; puis chaque jour ou l atelier tourne, 1 moins la part des heures passees en reparation, moins 5 par
   blesse et 100 par mort d un accident cause par SA panne. Regle : entretenir au-dela de l intervalle constructeur.
   Temoin : jamais d entretien.
4. Evenements. Individuels : accident_du_travail, gisement_epuise, machine_hors_service. Comptes : panne_machine,
   entretien_machine, extraction_t, production_industrie, livraison_interne_t, blessure_sans_medecine.
5. Liens. Recoit : les heures de presence des ouvriers et mineurs ( moteur ), le fer que le moteur achete pour ses
   fonderies, l electricite du reseau ( payee a l Etat au tarif ), le carburant des marches, l eau du territoire
   ( `prelever`, usage industrie repris ), le credit ( banques ) pour remplacer une machine. Donne : fer, zinc, or
   ( redevance a l Etat ), outils au moteur ; les biens nouveaux par `livrer` et `commander` ; les rejets au territoire
   ( `rejeter` ) ; les morts a la population ( `deceder`, cause accident ) ; les blessures a la medecine ( `blesser`
   si le domaine 16 est installe ) ; les heures travaillees ( Habitant.heures_jour ) a la paie. Remplace la
   production du moteur des mines, carrieres et fonderies ( `p.reprendre` ) ; laisse la pharmacie au moteur ( ses
   intrants et son produit sont des biens du moteur, ses molecules appartiennent au domaine 16 ), mais fait son eau :
   le territoire coupe ses prelevements de fond des sites industriels quand l industrie est installee.
6. Portes : tests_d10_industrie.py.
7. Arma. Les engins roulants portent un classname ( un camion du jeu de base pour le tombereau ) ; les engins fixes
   ( fours, broyeurs ) et les engins de chantier absents du jeu n en ont pas. arma_preuve = None partout.
8. Cout. Tout suit le nombre de sites, d ateliers et de machines ( ~ 35 sur Altis ), plus les ouvriers presents de ces
   sites a chaque pas ( une passe sur l index du moteur, pas sur la population ). Mesure : tests_d10_industrie.test_cout."""
import importlib, math
import numpy as np
from .. import config as C, population as PO
POSTE_TRAVAIL = PO.CODE_POSTE["travail"]
from ..socle import decision as D, objets as O
from . import pays as P, d01_population as POP, d02_banques as BQ, d03_economie as ECO, d08_territoire as TER

# ================================================================== les unites
DT_H = C.MINUTES_PAR_PAS / 60.0     # un pas du monde, en heures
HEURES_POSTE = 8.0                  # un poste de travail
# La drachme du monde : le taux commun du pays ( pays.EUROS_PAR_DRACHME = 1,15 euro : la ration du moteur et le salaire
# de l ouvrier, ELSTAT 2023 ). Les prix du domaine sont ecrits en euros et convertis.
EUROS_PAR_DRACHME = P.EUROS_PAR_DRACHME
# L electricite et le carburant du moteur : les unites du domaine 11 ( d11_energie.KWH_UNITE, LITRES_UNITE ) : 1 unite
# d electricite = 10 kWh ; 1 unite de carburant = 10 litres de gazole.
KWH_PAR_UNITE_ELEC = 10.0
LITRES_PAR_UNITE_CARBURANT = 10.0
# Le lignite du domaine, pour qui le brule ( domaine 11 : sa tranche vapeur lit la masse de l unite, et doit lire ce PCI,
# pas celui de la houille ) : PCI 5,5 MJ/kg ( lignite grec, PPC ), 101 t de CO2 par TJ ( GIEC 2006, lignite ), soufre 1 %.
CHARBON_PCI_MJ_KG, CHARBON_CO2_T_TJ, CHARBON_SOUFRE = 5.5, 101.0, 0.010
HEURES_PAR_TRAVAILLEUR_AN = 1880.0  # heures reellement travaillees par emploi et par an, Grece ( OCDE 2022 : ~ 1 886 )
CAMION_T = 25.0                     # charge utile d un semi-remorque de 40 t ( reglementation europeenne )
RESERVE_CARBURANT_MARCHE = ECO.RESERVE_CARBURANT   # le moteur garde 120 unites de carburant a chaque marche

# ================================================================== les biens
# Les biens du moteur que ce domaine produit, calibres ici ( conventions : « minerais : 10 » ). La masse de l unite est
# choisie pour que la production par heure du moteur E1 soit celle d un mineur reel ( voir les gisements ) ; au prix du
# moteur et a 1,15 euro la drachme, les metaux sont alors payes ~ 0,6 fois le cours mondial de 2024 ( a calibrer, avec
# le domaine 7 ) :
#   fer    1 unite = 120 kg de concentre ou de fines a 62 % Fe ( cours ~ 100 euros la tonne ; le moteur : 6 drachmes )
#   zinc   1 unite = 20 kg de concentre a 50 % Zn, soit 10 kg de zinc paye ( LME ~ 2 700 $/t, 85 % payes, moins les
#          frais de traitement : ~ 1,8 euro le kg ; le moteur : 9 drachmes )
#   or     1 unite = 10 g d or ( LBMA 2024 ~ 2 400 $/oz, ~ 71 euros le gramme ; le moteur : 400 drachmes )
#   outils 1 unite = 25 kg d acier outille ( pelles, pics, cles, forets : a calibrer ; le moteur : 30 drachmes )
CALIBRAGE_E1 = {   # bien : ( masse kg, volume l, teneur en fer t par unite, source )
    "fer": (120.0, 50.0, 0.120 * 0.62, "120 kg de minerai a 62 % Fe ( fines, densite en vrac ~ 2,4 ) ; cours 2024"),
    "zinc": (20.0, 9.0, 0.0, "20 kg de concentre a 50 % Zn ( vrac ~ 2,2 ) ; cours LME 2024 net des frais"),
    "or": (0.01, 0.0005, 0.0, "10 g d or affine ; cours LBMA 2024"),
    "outils": (25.0, 12.0, 0.025 * 0.995, "25 kg d acier outille, a calibrer ; l outil du moteur dure 200 heures"),
}
# Les biens nouveaux, par tonne sauf mention. Prix : cours ou prix de marche europeens 2023-2024, EN EUROS, convertis
# a 1,15 euro la drachme ( ordres de grandeur, a calibrer ) ; volume : densite en vrac ou en pile.
BIENS = {   # nom : ( famille, unite, prix euros, categorie de TVA, masse kg, volume l, source )
    "cuivre": ("matiere_premiere", "tonne de concentre a 25 % Cu", 1900.0, "normale", 1000.0, 500.0,
               "LME ~ 9 000 $/t, 96 % payes moins frais de traitement : ~ 1 900 euros la tonne de concentre"),
    "charbon": ("energie", "tonne de lignite brut ( PCI 5,5 GJ/t, 48 % d eau, 16 % de cendres )", 15.0, "normale", 1000.0,
                833.0, "lignite grec de Ptolemaida-Megalopoli ( PPC : 5 a 6 GJ/t ) ; pas de marche mondial, cout a la mine "
                "~ 15 euros la tonne ( a calibrer )"),
    "calcaire": ("matiere_premiere", "tonne de calcaire concasse ( 95 % CaCO3 )", 10.0, "normale", 1000.0, 625.0,
                 "granulats calcaires ~ 10 euros la tonne depart carriere ( UEPG, a calibrer )"),
    "gypse": ("matiere_premiere", "tonne de gypse de carriere", 15.0, "normale", 1000.0, 714.0,
              "gypse de carriere ~ 15 euros la tonne ( a calibrer )"),
    "sable": ("matiere_premiere", "tonne de sable siliceux lave ( 97 % SiO2 )", 30.0, "normale", 1000.0, 625.0,
              "sable industriel ~ 30 euros la tonne ( a calibrer )"),
    "fonte": ("materiau", "tonne de fonte brute ( 94 % Fe, 4 % C )", 400.0, "normale", 1000.0, 285.0,
              "fonte de moulage ~ 400 euros la tonne ( 2024, a calibrer )"),
    "acier": ("materiau", "tonne d acier brut ( billettes, brames )", 550.0, "normale", 1000.0, 127.0,
              "demi-produits ~ 550 euros la tonne ( 2024, a calibrer )"),
    "ciment": ("materiau", "tonne de ciment CEM II/A-LL", 100.0, "normale", 1000.0, 714.0,
               "ciment en Grece ~ 100 euros la tonne ( a calibrer )"),
    "chimie": ("chimie", "tonne de produits chimiques de base ( chaux vive, soude, ammoniac, ethylene : la composition "
               "n est pas suivie, a scinder quand un domaine en aura besoin )", 200.0, "normale", 1000.0, 1111.0,
               "chaux vive ~ 120 euros la tonne, ammoniac ~ 500 ( a calibrer )"),
    "engrais": ("chimie", "tonne d ammonitrate ( 34 % N )", 400.0, "reduite", 1000.0, 1000.0,
                "ammonitrate ~ 400 euros la tonne ( 2024 ) ; TVA reduite des intrants agricoles ( a calibrer )"),
    "plastique": ("materiau", "tonne de polyethylene en granules", 1200.0, "normale", 1000.0, 1818.0,
                  "PEHD ~ 1 200 euros la tonne ( a calibrer )"),
    "pieces": ("piece", "tonne de pieces mecaniques usinees", 5000.0, "normale", 1000.0, 500.0,
               "pieces usinees ~ 5 euros le kg ( a calibrer )"),
    "verre": ("materiau", "tonne de verre sodocalcique", 400.0, "normale", 1000.0, 400.0,
              "verre creux et plat ~ 400 euros la tonne ( a calibrer )"),
}
BIENS = {b: (v[0], v[1], round(v[2] / EUROS_PAR_DRACHME, 2)) + v[3:] for b, v in BIENS.items()}   # en drachmes
BIENS_E1 = tuple(C.BIENS)
MASSE_T = {b: m / 1000.0 for b, (m, _, _, _) in CALIBRAGE_E1.items()}
MASSE_T.update({b: v[4] / 1000.0 for b, v in BIENS.items()})
TENEUR_FE = {b: v[2] for b, v in CALIBRAGE_E1.items() if v[2] > 0}
TENEUR_FE.update({"fonte": 0.94, "acier": 0.995, "pieces": 0.995})
ENERGIES = ("electricite", "carburant")     # hors du bilan matiere : de l energie, pas de la masse

# ================================================================== les accidents du travail
# Incidence pour 100 000 personnes occupees et par an ( ESAW, Eurostat hsw_n2_01 : accidents non mortels avec plus de
# 3 jours d absence ; hsw_n2_02 : mortels ), UE, ordres de grandeur 2019-2021 a verifier. La Grece declare bien moins
# ( sous-declaration connue ) : on prend le niveau europeen, qui dit le risque, pas la declaration.
SECTEURS = {   # code NACE : ( non mortels, mortels, libelle )
    "B": (1500.0, 7.0, "industries extractives"),
    "C20": (1000.0, 1.5, "chimie"),
    "C23": (2000.0, 3.0, "produits mineraux non metalliques ( ciment, chaux, verre )"),
    "C24": (2500.0, 3.5, "metallurgie ( fonte, acier )"),
    "C25": (2200.0, 1.5, "produits metalliques ( forge, usinage )"),
}
TAUX_H = {k: (nf / 1e5 / HEURES_PAR_TRAVAILLEUR_AN, m / 1e5 / HEURES_PAR_TRAVAILLEUR_AN) for k, (nf, m, _) in SECTEURS.items()}
# Part des accidents liee a la maintenance et aux pannes ( EU-OSHA 2010, « Maintenance and OSH » : 15 a 20 % des
# accidents, 10 a 15 % des accidents mortels ) : elle est portee par les pannes des machines, le reste par l heure travaillee.
PART_PANNES = 0.15
# Gravite d un accident non mortel : jours perdus, classes ESAW ( 4-6 j, 7-13, 14-20, 21-30, 1-3 mois, 3-6 mois, plus
# de 6 mois ou incapacite permanente ) ; parts a verifier ( ordre de grandeur des publications ESAW ).
JOURS_PERDUS = ((4, 6, 0.20), (7, 13, 0.25), (14, 20, 0.13), (21, 30, 0.13), (31, 90, 0.20), (91, 180, 0.06), (181, 365, 0.03))
# La lesion pour la medecine ( d16_medecine.blesser : type, ISS de 1 a 75 ) : ecrasement a la mine et a la carriere,
# brulure a la fonte et a l acier ; l ISS suit les jours perdus ( ISS 1-4 jusqu a 20 jours, 5-9 jusqu a 90, 10-24 jusqu a
# 180, 25-35 au-dela : l ordre de la table ISS_TRAVAIL du domaine 16 ).
LESION_SECTEUR = {"B": "ecrasement", "C24": "brulure", "C23": "travail", "C25": "travail", "C20": "brulure"}
ISS_JOURS = ((20, 1, 4), (90, 5, 9), (180, 10, 24), (10 ** 6, 25, 35))


def iss_depuis_jours(jours, rng):
    for borne, a, b in ISS_JOURS:
        if jours <= borne: return int(rng.integers(a, b + 1))
    return 35


POIDS_BLESSE, POIDS_MORT = 5.0, 100.0   # dans la note de l entretien : un blesse vaut 5 jours de machine, un mort 100 ( a calibrer )

# ================================================================== la fiabilite des machines
# Une panne majeure ( qui arrete la machine plus d un poste ) suit une loi de Weibull en heures de service depuis le
# dernier entretien ou la derniere reparation : forme BETA > 1, l usure des pieces ( a calibrer : 1 a 1,5 pour toutes les
# pannes d une chargeuse, Kumar et Klefsjo 1992 ; au-dela de 2 pour un mode d usure ). Echelle eta = MTBF / Gamma( 1 + 1/BETA ) :
# le MTBF DECLARE est la moyenne entre deux pannes sans entretien preventif, machine neuve. L usure de vie ( Parc ) monte
# le risque : x ( 1 + A_USURE x usure ). Un entretien ou une reparation remet le compteur a zero ( aussi bon que neuf pour
# ce mode ), pas l usure de vie.
A_USURE = 1.0
PART_ACIER_MACHINE, PART_PIECES_MACHINE = 0.70, 0.10   # masse d une machine : acier de structure, pieces usinees
PART_IMPORTEE_MACHINE = 0.40      # moteurs, hydraulique, electronique : importes ( a calibrer )
DUREE_CREDIT_MACHINE = 60         # mois


class ModeleMachine:
    """La fiabilite d un modele de machine ( le prix, la masse, la duree de vie et le classname sont dans le Parc ).
      mtbf_h     heures de service entre deux pannes majeures sans entretien, machine neuve
      beta       forme de Weibull ; eta : echelle deduite du MTBF
      mttr_h     heures d atelier ouvert pour reparer
      pm_h       intervalle d entretien preventif du constructeur, en heures de service ; pm_duree_h : sa duree"""
    __slots__ = ("nom", "mtbf_h", "beta", "eta", "mttr_h", "pm_h", "pm_duree_h")

    def __init__(self, nom, mtbf_h, beta, mttr_h, pm_h, pm_duree_h):
        if not (0 < mtbf_h <= 1e5 and 1.0 <= beta <= 5.0 and 0 < mttr_h <= 500 and 0 < pm_h <= 1e4 and 0 < pm_duree_h <= 100):
            raise ValueError(f"machine {nom} : fiabilite hors bornes")
        self.nom, self.mtbf_h, self.beta, self.mttr_h, self.pm_h, self.pm_duree_h = nom, mtbf_h, beta, mttr_h, pm_h, pm_duree_h
        self.eta = mtbf_h / math.gamma(1.0 + 1.0 / beta)


# nom : ( prix euros, masse kg, vie h, MTBF h, beta, MTTR h, intervalle d entretien h, duree h, classname Arma, source )
# Prix : neuf, en euros ( converti a 1,15 euro la drachme ) ; intervalles : 250 / 500 heures de service ( plans d entretien des engins de chantier,
# ex. Caterpillar ) ; MTBF et MTTR : ordres de grandeur des etudes de fiabilite minieres ( Dhillon 2008, Mining Equipment
# Reliability ) pour une panne qui arrete l engin plus d un poste - tous a calibrer.
MODELES = {
    "foreuse_jumbo": (1000000.0, 25000.0, 20000.0, 300.0, 2.5, 10.0, 250.0, 6.0, None, "jumbo de foration a deux bras"),
    "chargeuse_souterraine": (1200000.0, 38000.0, 20000.0, 350.0, 2.5, 12.0, 250.0, 6.0, None, "chargeuse LHD de 10 t"),
    "concentrateur": (5000000.0, 150000.0, 100000.0, 900.0, 2.5, 16.0, 500.0, 8.0, None,
                      "broyeur a boulets et flottation, ~ 50 t/jour"),
    "foreuse_surface": (500000.0, 20000.0, 30000.0, 350.0, 2.5, 8.0, 250.0, 6.0, None, "foreuse de gradins"),
    "pelle_hydraulique": (800000.0, 70000.0, 60000.0, 500.0, 2.5, 12.0, 250.0, 6.0, None, "pelle de 70 t"),
    "tombereau": (600000.0, 32000.0, 50000.0, 450.0, 2.5, 10.0, 250.0, 6.0, "C_Truck_02_transport_F",
                  "tombereau rigide de 40 t ; le jeu n a pas de tombereau : le Zamak de transport en tient lieu"),
    "chargeuse_pneus": (300000.0, 20000.0, 25000.0, 400.0, 2.5, 8.0, 250.0, 4.0, None, "chargeuse sur pneus de 20 t"),
    "concasseur": (600000.0, 60000.0, 80000.0, 700.0, 2.5, 12.0, 500.0, 8.0, None, "concasseur primaire"),
    "excavatrice_godets": (20000000.0, 1500000.0, 150000.0, 600.0, 2.5, 24.0, 500.0, 12.0, None,
                           "roue-pelle a godets des mines de lignite"),
    "four_rotatif": (30000000.0, 1000000.0, 150000.0, 1200.0, 2.5, 36.0, 1000.0, 24.0, None,
                     "four rotatif de clinker ~ 300 t/jour ; arrets non programmes ~ 6 a 10 par an"),
    "broyeur_ciment": (5000000.0, 300000.0, 100000.0, 900.0, 2.5, 16.0, 500.0, 8.0, None, "broyeur a boulets de ciment"),
    "four_a_chaux": (5000000.0, 500000.0, 100000.0, 1000.0, 2.5, 24.0, 500.0, 12.0, None, "four droit a chaux ~ 100 t/jour"),
    "four_reduction": (30000000.0, 800000.0, 100000.0, 1000.0, 2.5, 24.0, 500.0, 12.0, None,
                       "four electrique de reduction a fonte ( Tysland-Hole, Elkem ) ~ 10 MVA"),
    "bas_fourneau": (20000000.0, 2000000.0, 60000.0, 1000.0, 2.5, 24.0, 500.0, 12.0, None,
                     "bas fourneau au coke de lignite ( Calbe, RDA, annees 1950 )"),
    "convertisseur": (10000000.0, 400000.0, 60000.0, 800.0, 2.5, 16.0, 500.0, 8.0, None, "convertisseur a oxygene de 10 t"),
    "presse_forge": (1000000.0, 60000.0, 60000.0, 600.0, 2.5, 8.0, 250.0, 4.0, None, "presse et marteau de forge"),
    "centre_usinage": (400000.0, 10000.0, 50000.0, 800.0, 2.5, 8.0, 500.0, 4.0, None, "centre d usinage a commande numerique"),
}
PRIX_MACHINE = {nom: round(v[0] / EUROS_PAR_DRACHME) for nom, v in MODELES.items()}   # drachmes
FIABILITE = {nom: ModeleMachine(nom, v[3], v[4], v[5], v[6], v[7]) for nom, v in MODELES.items()}


def cumul_hasard(fia, t_h, usure):
    """Le hasard cumule d une machine a t_h heures de service depuis son dernier entretien."""
    return (t_h / fia.eta) ** fia.beta * (1.0 + A_USURE * usure)


U_REFERENCE = 0.35   # usure de vie moyenne du parc de depart ( tiree uniforme de 0 a 0,7 )


def taux_pannes_reference(fia, usure=U_REFERENCE, n=200):
    """Pannes par heure de service sous le plan d entretien du constructeur ( un entretien toutes les pm_h heures, une
    panne remet aussi le compteur a zero ) : probabilite de panne dans un cycle sur la duree moyenne d un cycle. C est
    la pratique que mesurent les statistiques d accidents ( ESAW ), pas la machine jamais entretenue."""
    dt = fia.pm_h / n
    t = (np.arange(n) + 0.5) * dt
    duree = float(np.exp(-cumul_hasard(fia, t, usure)).sum() * dt)
    return (1.0 - math.exp(-cumul_hasard(fia, fia.pm_h, usure))) / duree


def proba_panne(fia, t_h, dt_h, usure):
    """La probabilite de tomber en panne pendant dt_h heures de service, a t_h heures du dernier entretien."""
    return 1.0 - math.exp(-(cumul_hasard(fia, t_h + dt_h, usure) - cumul_hasard(fia, t_h, usure)))


# ================================================================== les gisements
class TypeGisement:
    """Une facon d exploiter. materiel_t_h : tonnes de materiau ( minerai et sterile ) abattues et roulees par heure
    travaillee, tout le personnel compte ; gazole par tonne de materiau ; electricite par tonne de minerai ( roulage,
    ventilation, concassage, broyage ). Le minerai par heure-travailleur est materiel_t_h / ( 1 + decouverture )."""
    __slots__ = ("nom", "materiel_t_h", "gazole_l_t", "elec_kwh_t", "secteur", "source")

    def __init__(self, nom, materiel_t_h, gazole_l_t, elec_kwh_t, secteur, source):
        if not (0 < materiel_t_h <= 1000 and 0 <= gazole_l_t <= 10 and 0 <= elec_kwh_t <= 500): raise ValueError(f"{nom} hors bornes")
        self.nom, self.materiel_t_h, self.gazole_l_t, self.elec_kwh_t, self.secteur, self.source = (
            nom, materiel_t_h, gazole_l_t, elec_kwh_t, secteur, source)


TYPES_GISEMENT = {
    "souterraine": TypeGisement("souterraine", 0.5, 0.8, 30.0, "B",
                                "mines souterraines polymetalliques de Chalcidique : Stratoni ~ 200 kt/an pour ~ 300 salaries, "
                                "~ 0,4 t/h ; energie : ventilation, exhaure, broyage ( a calibrer )"),
    "ciel_ouvert": TypeGisement("ciel_ouvert", 6.0, 0.6, 15.0, "B",
                                "mines a ciel ouvert : ~ 6 t de materiau par heure-employe ( EIA, charbon de surface 2022 : "
                                "~ 6,5 short tons ) ; gazole des tombereaux 0,4 a 1 l/t ( a calibrer )"),
    "carriere": TypeGisement("carriere", 8.0, 0.3, 2.0, "B",
                             "granulats de l UE : ~ 3 Gt/an pour ~ 200 000 emplois directs, ~ 8 t/h ( UEPG ) ; concassage "
                             "1 a 3 kWh/t"),
    "lignite": TypeGisement("lignite", 30.0, 0.05, 1.0, "B",
                            "lignite de Ptolemaida : roues-pelles electriques, ~ 5 t de lignite par heure-employe dans les "
                            "annees 2000 ( PPC ), decouverture de 5 a 7 t par t ( a calibrer )"),
}


class Gisement:
    """Un gisement fini d un site. reserve_t : tonnes de minerai en place ; rendements : unites de chaque bien par
    tonne de minerai ( teneur x recuperation / contenu d une unite ) ; decouverture : tonnes de sterile par tonne de
    minerai, de sr0 au debut a sr1 a l epuisement ( la fosse s approfondit, les galeries s allongent : le cout d une
    tonne monte ) ; eau_m3_t et rejets ( kg ) par tonne de minerai."""
    __slots__ = ("nom", "type", "reserve0_t", "reserve_t", "extrait_t", "sterile_t", "sr0", "sr1", "rendements",
                 "eau_m3_t", "rejets", "epuise_j", "source")

    def __init__(self, nom, type_, reserve_t, sr0, sr1, teneurs, eau_m3_t, rejets, source):
        if type_ not in TYPES_GISEMENT: raise ValueError(f"{nom} : type {type_!r} inconnu")
        if not (reserve_t > 0 and 0 <= sr0 <= sr1 <= 50 and 0 <= eau_m3_t <= 10): raise ValueError(f"{nom} : gisement hors bornes")
        self.nom, self.type, self.reserve0_t, self.reserve_t = nom, TYPES_GISEMENT[type_], float(reserve_t), float(reserve_t)
        self.extrait_t = self.sterile_t = 0.0
        self.sr0, self.sr1 = float(sr0), float(sr1)
        self.rendements = {}
        for b, (teneur, recuperation, contenu_t) in teneurs.items():
            if not (0 < teneur <= 1 and 0 < recuperation <= 1 and contenu_t > 0): raise ValueError(f"{nom}.{b} : teneur hors bornes")
            self.rendements[b] = teneur * recuperation / contenu_t
        if sum(r * MASSE_T[b] for b, r in self.rendements.items()) > 1.0: raise ValueError(f"{nom} : plus de produit que de minerai")
        self.eau_m3_t, self.rejets, self.epuise_j, self.source = eau_m3_t, dict(rejets), -1, source

    def decouverture(self):
        return self.sr0 + (self.sr1 - self.sr0) * min(1.0, self.extrait_t / self.reserve0_t)

    def minerai_h(self):
        """Tonnes de minerai par heure-travailleur, aujourd hui."""
        return self.type.materiel_t_h / (1.0 + self.decouverture())


G_AU = 1e-6   # t par gramme
# Les gisements d Altis sont fictifs ; leurs teneurs sont dans les fourchettes reelles et choisies basses pour que la
# production par heure retrouve celle du moteur E1 ( a calibrer ). Rejets en kg par tonne de minerai ( guide EMEP/AEE
# 2019, 2.A.5.a, ordres de grandeur a verifier ; plomb : drainage des sulfures polymetalliques, a calibrer ).
GISEMENTS = {   # nom : ( type, reserve t, sr0, sr1, { bien : ( teneur, recuperation, contenu t par unite ) }, eau m3/t, rejets, source )
    "skarn": ("souterraine", 1.2e6, 0.2, 1.0,
              {"fer": (0.30, 0.80, TENEUR_FE["fer"]), "zinc": (0.014, 0.85, 0.010), "cuivre": (0.002, 0.85, 0.25),
               "or": (0.5 * G_AU, 0.80, 10 * G_AU)}, 0.7, {"pm25": 0.02, "plomb": 0.0002, "plomb_sol": 0.002},
              "skarn a magnetite et sulfures ( Serifos : Fe 40-55 % ; Chalcidique : Zn 4-9 %, Au 1-8 g/t ) : Fe 30 %, Zn "
              "1,4 %, Cu 0,2 %, Au 0,5 g/t ; recuperations de flottation et de separation magnetique 80-85 %"),
    "fer_zinc": ("ciel_ouvert", 4.0e5, 7.0, 11.0, {"fer": (0.35, 0.75, TENEUR_FE["fer"]), "zinc": (0.013, 0.70, 0.010)},
                 0.5, {"pm25": 0.05, "plomb": 0.0001, "plomb_sol": 0.001},
                 "chapeau de fer oxyde a zinc ( calamine du Laurion ) : Fe 35 %, Zn 1,3 % ; decouverture 7 a 11 t/t"),
    "calcaire": ("carriere", 2.0e6, 0.2, 0.5, {"calcaire": (1.0, 0.95, 1.0)}, 0.1, {"pm25": 0.005},
                 "calcaire marneux a ciment ; 5 % de fines rejetees"),
    "gypse": ("carriere", 2.0e5, 0.3, 0.6, {"gypse": (1.0, 0.90, 1.0)}, 0.1, {"pm25": 0.005}, "gypse de carriere"),
    "sable": ("carriere", 5.0e5, 0.1, 0.3, {"sable": (1.0, 0.85, 1.0)}, 0.5, {"pm25": 0.005},
              "sable siliceux lave : 15 % d argiles et de fines"),
    "lignite": ("lignite", 3.0e6, 5.0, 7.0, {"charbon": (1.0, 0.95, 1.0)}, 0.05, {"pm25": 0.01},
                "lignite a ciel ouvert : 5 % de schistes rejetes"),
}

# ================================================================== les recettes
class Recette:
    """Une transformation, pour UNE unite de son produit.
      entrees   { bien : unites } ( electricite comprise, en unites du reseau de 10 kWh ) ; libres : { air, oxygene : t } pris a
                l atmosphere, hors catalogue mais dans le bilan matiere
      sorties   { bien : unites } ; pertes : { nom : t } declarees ( laitier, gaz, vapeur, chutes )
      fer_perdu t de fer qui part dans le laitier et les poussieres ( bilan du fer ), ou None
      cadence_h unites produites par heure-travailleur ; secteur : code NACE des accidents
      eau_m3, rejets ( kg ) : par unite produite"""
    __slots__ = ("nom", "produit", "entrees", "libres", "sorties", "pertes", "fer_perdu", "cadence_h", "secteur",
                 "eau_m3", "rejets", "source")

    def __init__(self, nom, entrees, libres, sorties, pertes, fer_perdu, cadence_h, secteur, eau_m3, rejets, source):
        if secteur not in SECTEURS or not cadence_h > 0 or eau_m3 < 0: raise ValueError(f"recette {nom} hors bornes")
        if any(q <= 0 for d in (entrees, libres, sorties, pertes) for q in d.values()): raise ValueError(f"{nom} : quantite non positive")
        self.nom, self.entrees, self.libres, self.sorties, self.pertes = nom, dict(entrees), dict(libres), dict(sorties), dict(pertes)
        self.produit = next(iter(sorties))
        self.fer_perdu, self.cadence_h, self.secteur, self.eau_m3, self.rejets, self.source = (
            fer_perdu, cadence_h, secteur, eau_m3, dict(rejets), source)


# Les compositions qui font les bilans ( derivation a la main, voir les sources ) :
#   minerai 62 % Fe en hematite Fe2O3 ; lignite brut : C 0,25, H 0,02, O 0,08, N+S 0,01, cendres 0,16, eau 0,48 ( PCI
#   5,5 GJ/t ; brule, il prend 0,747 t d O2 et rend 0,917 t de CO2 et 0,66 t de vapeur par tonne ) ; calcaire 95 % CaCO3 ;
#   fonte : Fe 0,94, C 0,04, Si et Mn 0,02 ; acier : Fe 0,995 ; 3 % du fer du minerai part au laitier.
RECETTES = {r.nom: r for r in (
    Recette("fonte_electrique", {"fer": 13.0252, "charbon": 1.52, "calcaire": 0.25, "electricite": 230.0}, {},
            {"fonte": 1.0}, {"laitier": 0.5609, "gaz_et_vapeur": 1.7722}, 0.0291, 0.30, "C24", 2.0,
            {"pm25": 0.3, "so2": 1.0, "no2": 0.2, "plomb_sol": 0.005},
            "four electrique de reduction ( Tysland-Hole, Elkem ) : 2 200 a 2 500 kWh et ~ 0,4 t de carbone par t de fonte ; "
            "le carbone vient du lignite ( 0,38 t de C dans 1,52 t ) ; 0,25 t de castine"),
    Recette("fonte_bas_fourneau", {"fer": 13.0252, "charbon": 3.80, "calcaire": 0.30, "electricite": 15.0},
            {"air_o2": 0.7969}, {"fonte": 1.0}, {"laitier": 0.9548, "gaz_de_gueulard": 4.5051}, 0.0291, 0.30, "C24", 2.0,
            {"pm25": 0.5, "so2": 2.5, "no2": 0.3, "plomb_sol": 0.01},
            "bas fourneau au coke de lignite ( Calbe, RDA ) : ~ 0,95 t de carbone par t de fonte, 0,31 t pour reduire le "
            "minerai, le reste brule en CO aux tuyeres ( 0,80 t d O2 du vent ) ; laitier lourd des cendres du lignite"),
    Recette("acier_convertisseur", {"fonte": 1.09, "calcaire": 0.10, "electricite": 6.0}, {"oxygene": 0.0852},
            {"acier": 1.0}, {"laitier": 0.1387, "gaz_de_convertisseur": 0.1365}, 0.0296, 0.50, "C24", 1.0,
            {"pm25": 0.1, "no2": 0.1, "plomb_sol": 0.002},
            "convertisseur a oxygene sans ferraille : ~ 1,09 t de fonte et ~ 60 Nm3 d oxygene par t d acier, laitier "
            "0,10 a 0,15 t ; ~ 60 kWh ( soufflage et separation de l air )"),
    Recette("outils_forge", {"acier": 0.0275, "electricite": 2.75}, {}, {"outils": 1.0}, {"chutes": 0.0025},
            0.0025 * 0.995, 1.0, "C25", 0.0125, {"pm25": 0.0005},
            "forge : ~ 10 % de chutes et de calamine ; chauffe par induction et traitement thermique ~ 1 000 kWh/t"),
    Recette("pieces_usinage", {"acier": 1.25, "electricite": 150.0}, {}, {"pieces": 1.0}, {"copeaux": 0.25},
            0.25 * 0.995, 0.02, "C25", 0.5, {"pm25": 0.02},
            "usinage : ~ 80 % de mise au mille, ~ 1 500 kWh/t ; 20 kg par heure-travailleur ( a calibrer )"),
    Recette("ciment", {"calcaire": 1.2637, "gypse": 0.05, "charbon": 0.5091, "electricite": 11.0}, {"air_o2": 0.3801},
            {"ciment": 1.0}, {"co2_decarbonatation": 0.3665, "vapeur_du_cru": 0.0287, "co2_combustion": 0.4667,
                              "vapeur_de_combustion": 0.336, "autres_gaz": 0.0051}, None, 2.0, "C23", 0.3,
            {"pm25": 0.05, "so2": 0.3, "no2": 1.0},
            "CEM II/A-LL : 0,80 t de clinker ( 3,5 GJ/t de clinker, cru a 1,55 t par t, les cendres du lignite entrent dans "
            "le clinker ), 0,15 t de filler calcaire, 0,05 t de gypse ; ~ 110 kWh/t ( GCCA ) ; ~ 2 t par heure-employe "
            "( Cembureau : ~ 170 Mt pour ~ 45 000 emplois )"),
    Recette("chaux", {"calcaire": 1.7182, "charbon": 0.7273, "electricite": 3.0}, {"air_o2": 0.5430}, {"chimie": 1.0},
            {"co2_decarbonatation": 0.7182, "co2_combustion": 0.6667, "vapeur": 0.48, "autres_gaz": 0.0073,
             "cendres": 0.1164}, None, 1.2, "C23", 0.1, {"pm25": 0.1, "so2": 0.5, "no2": 0.6},
            "chaux vive : CaCO3 -> CaO + CO2, 4,0 GJ/t en four droit ( EuLA ) ; ~ 1,2 t par heure-employe ( a calibrer )"),
    Recette("verre", {"sable": 0.7485, "calcaire": 0.1895, "chimie": 0.2414, "electricite": 90.0}, {}, {"verre": 1.0},
            {"co2_des_carbonates": 0.1794}, None, 0.5, "C23", 1.0, {"pm25": 0.3, "so2": 0.2, "no2": 0.5},
            "verre sodocalcique SiO2 72 %, Na2O 14 %, CaO 10 % ; la chimie est ici le carbonate de soude ; fusion "
            "electrique ~ 900 kWh/t"),
    Recette("engrais", {"chimie": 0.4255, "electricite": 5.0}, {"air_o2": 0.7996}, {"engrais": 1.0},
            {"vapeur": 0.2251}, None, 1.0, "C20", 2.0, {"pm25": 0.2, "no2": 1.0, "nitrates": 0.05},
            "nitrate d ammonium : 2 NH3 + 2 O2 -> NH4NO3 + H2O ( la moitie de l ammoniac fait l acide nitrique ) ; la chimie "
            "est ici l ammoniac, qui demande le gaz du domaine 11 ou l import"),
    Recette("plastique", {"chimie": 1.02, "electricite": 50.0}, {}, {"plastique": 1.0}, {"purges": 0.02}, None, 1.0,
            "C20", 1.0, {"pm25": 0.01},
            "polymerisation de l ethylene ( la chimie est ici l ethylene ) : ~ 98 % de rendement, 400 a 1 000 kWh/t"),
)}

# ================================================================== le plan des sites
# Chaque site du moteur repris est une suite d ateliers : ( nom, gisement ou recette, part de l equipe, { modele : nombre
# pour l equipe de reference } ). L equipe de reference est celle du moteur a l echelle 1 ( 10 mineurs par mine ou
# carriere, 6 ouvriers par fonderie ) ; a une autre echelle, le parc suit l equipe. Une cimenterie et un four a chaux
# sont adosses a leur carriere, comme dans la realite ; la fonderie du moteur devient une petite acierie integree
# ( fonte, convertisseur, forge, usinage ). Les chaines verre, engrais, plastique ont leurs recettes mais aucun site
# d Altis : ni soude, ni ammoniac, ni ethylene ( gaz et petrochimie : domaine 11, ou l import ).
_FER_ZINC = {"foreuse_surface": 1, "pelle_hydraulique": 1, "tombereau": 2}
PLAN_ALTIS = {
    "Mine01": (("skarn", "skarn", 1.0, {"foreuse_jumbo": 1, "chargeuse_souterraine": 2, "concentrateur": 1}),),
    "quarry01": (("fer_zinc", "fer_zinc", 0.35, _FER_ZINC), ("calcaire", "calcaire", 0.20, {"tombereau": 1, "concasseur": 1}),
                 ("gypse", "gypse", 0.05, {"chargeuse_pneus": 1}),
                 ("cimenterie", "ciment", 0.40, {"four_rotatif": 1, "broyeur_ciment": 1})),
    "quarry02": (("fer_zinc", "fer_zinc", 0.50, _FER_ZINC), ("calcaire", "calcaire", 0.15, {"tombereau": 1, "concasseur": 1}),
                 ("sable", "sable", 0.10, {"chargeuse_pneus": 1}), ("chaufour", "chaux", 0.25, {"four_a_chaux": 1})),
    "quarry03": (("lignite", "lignite", 0.60, {"excavatrice_godets": 1, "tombereau": 1}),
                 ("fer_zinc", "fer_zinc", 0.40, {"pelle_hydraulique": 1, "tombereau": 2})),
    "factory02": (("fonte", "fonte_bas_fourneau", 0.35, {"bas_fourneau": 1}), ("acierie", "acier_convertisseur", 0.15, {"convertisseur": 1}),
                  ("forge", "outils_forge", 0.40, {"presse_forge": 1}), ("usinage", "pieces_usinage", 0.10, {"centre_usinage": 1})),
    "factory04": (("fonte", "fonte_electrique", 0.35, {"four_reduction": 1}), ("acierie", "acier_convertisseur", 0.15, {"convertisseur": 1}),
                  ("forge", "outils_forge", 0.40, {"presse_forge": 1}), ("usinage", "pieces_usinage", 0.10, {"centre_usinage": 1})),
}
PLAN_PAR_TYPE = {"mine": "Mine01", "carriere": "quarry02", "fonderie": "factory04"}   # les sites des autres iles
EQUIPE_REFERENCE = {"mine": 10, "carriere": 10, "fonderie": 6}
TYPES_REPRIS = tuple(PLAN_PAR_TYPE)

# ================================================================== le regime des ateliers
REGIME_MIN = 0.25                 # un atelier d un bien du moteur ne descend pas sous un quart ( le moteur : 0,1 )
PAS_REGIME = 0.25
RESERVE_RESEAU_MIN = 50.0        # unites du reseau du moteur laissees en plus d une journee des autres sites
STOCK_MIN_J = 2.0                 # sans client, un atelier remplit 2 jours de sa production nominale, puis s arrete
JOURS_STOCK = 5.0                 # avec clients : 5 jours de leur besoin
JOURS_RATTRAPAGE = 3.0            # un manque de stock se comble en 3 jours
JOURS_INTRANTS = 3.0              # un site garde 3 jours de ses intrants venus d ailleurs
LOT_MIN_T = 1.0                   # on n envoie pas un camion pour moins d une tonne
# l ordre des biens nouveaux pour le regime : l aval d abord, pour que le besoin de l amont soit connu
ORDRE_BIENS = ("pieces", "verre", "engrais", "plastique", "ciment", "chimie", "acier", "fonte", "gypse", "sable",
               "calcaire", "charbon", "cuivre")
HORIZON_ENTRETIEN = 30


# ================================================================== les classes de l etat
class Machine:
    """La vie d un objet du Parc dans un atelier.
      t_h        heures de service depuis le dernier entretien ou la derniere reparation ( le compteur de la loi )
      pm_h       heures d atelier ouvert qui restent a l entretien en cours ( 0 : aucun ) ; repar_h : a la reparation
      panne_h, ouvert_h     du jour : heures ou la machine etait en reparation, heures ou son atelier etait ouvert
      blesses, morts        du jour, des accidents causes par sa panne ; pannes : jours des pannes ( 90 jours )"""
    __slots__ = ("objet", "fia", "t_h", "pm_h", "repar_h", "panne_h", "ouvert_h", "blesses", "morts", "pannes")

    def __init__(self, objet, fia):
        self.objet, self.fia = objet, fia
        self.t_h = self.pm_h = self.repar_h = self.panne_h = self.ouvert_h = 0.0
        self.blesses = self.morts = 0
        self.pannes = []


class Atelier:
    """Un gisement ou une recette d un site. part : sa part des heures de l equipe ; regime : la part de sa capacite
    qu il ouvre aujourd hui ; nominal_j : unites de son bien directeur par jour a plein regime ; p_acc, p_mort : la
    probabilite qu une panne d une de ses machines blesse ou tue ( la part PART_PANNES du risque de son secteur ).
    Cumuls ( l audit ) : minerai extrait, passes de recette. Du jour : produit ( t de minerai ou unites ), heures payees."""
    __slots__ = ("nom", "site", "gisement", "recette", "part", "machines", "regime", "directeur", "nominal_j",
                 "couverture", "p_acc", "p_mort", "secteur", "cumul_minerai", "cumul_passes", "produit_j", "gazole_j")

    def __init__(self, nom, site, gisement, recette, part):
        if not 0.0 < part <= 1.0: raise ValueError(f"{nom} : part d equipe hors ]0 ; 1]")
        self.nom, self.site, self.gisement, self.recette, self.part = nom, site, gisement, recette, part
        self.machines = []
        self.regime = 1.0
        self.directeur = recette.produit if recette is not None else max(
            gisement.rendements, key=lambda b: gisement.rendements[b] * _prix(b))
        self.nominal_j = self.couverture = 0.0
        self.p_acc = self.p_mort = 0.0
        self.secteur = recette.secteur if recette is not None else gisement.type.secteur
        self.cumul_minerai = self.cumul_passes = self.produit_j = self.gazole_j = 0.0

    def productivite(self):
        """Unites du bien directeur par heure-travailleur, aujourd hui."""
        if self.recette is not None: return self.recette.cadence_h
        return self.gisement.minerai_h() * self.gisement.rendements[self.directeur]


class Site:
    """Une entreprise du moteur reprise ( mine, carriere, fonderie ). Son stock du socle tient les biens nouveaux ; les
    biens du moteur restent dans Entreprise.stocks. equipe : les travailleurs affectes ( index du moteur, au matin )."""
    __slots__ = ("id", "entreprise", "lieu", "type", "stock", "ateliers", "equipe", "equipe_ref", "facteur_eau",
                 "actif", "heures_j")

    def __init__(self, entreprise, stock):
        self.id, self.entreprise, self.lieu, self.type = entreprise.id, entreprise, entreprise.lieu, entreprise.type
        self.stock = stock
        self.ateliers = []
        self.equipe = self.equipe_ref = 0
        self.facteur_eau = 1.0
        self.actif = True
        self.heures_j = 0.0


class Chargement:
    """Des biens nouveaux en route d un site a un autre : ils existent, ils sont a quelqu un, ils ne sont nulle part."""
    __slots__ = ("id", "origine", "destination", "stock", "arrivee")

    def __init__(self, id, origine, destination, stock, arrivee):
        self.id, self.origine, self.destination, self.stock, self.arrivee = id, origine, destination, stock, arrivee


class ContexteEntretien:
    __slots__ = ("traits", "machine")

    def __init__(self, traits, machine): self.traits, self.machine = traits, machine


class Industrie:
    """L etat du domaine."""
    __slots__ = ("sites", "par_entreprise", "chargements", "prochain_chargement", "machines", "decideur", "rng_pannes",
                 "rng_accidents", "facteur_risque", "commandes", "livre_biens", "e1_flux", "fabrications", "stats",
                 "heures_secteur", "accidents_secteur", "attendu", "blessures", "remplacements", "co2_t",
                 "reserve_reseau", "vu_pharmacie")

    def __init__(self):
        self.sites = []                 # Site, dans l ordre des identifiants
        self.par_entreprise = {}        # id d entreprise -> Site
        self.chargements = {}           # id -> Chargement en route
        self.prochain_chargement = 0
        self.machines = {}              # numero d objet du Parc -> Machine
        self.decideur = None
        self.rng_pannes = self.rng_accidents = None
        self.facteur_risque = 1.0       # multiplie tous les risques d accident ( controle positif des portes )
        self.commandes = {}             # bien -> unites par jour commandees par d autres domaines
        self.livre_biens = {}           # ( nature, bien ) -> unites vues par le grand livre sous les motifs du domaine, jours clos
        self.e1_flux = {}               # ( nature, bien ) -> unites des biens du moteur creees ou consommees par le domaine
        self.fabrications = {}          # bien -> unites consommees pour fabriquer des machines
        self.stats = {k: 0.0 for k in ("pannes", "entretiens", "blesses", "morts", "jours_perdus", "livre_t",
                                       "eau_manquante_m3", "machines_rebut", "machines_fabriquees", "machines_importees",
                                       "machines_non_remplacees", "gazole_u", "electricite_u",
                                       "pannes_attendues")}
        self.heures_secteur = {k: 0.0 for k in SECTEURS}       # heures travaillees ( exposees ) par secteur
        self.accidents_secteur = {k: [0, 0] for k in SECTEURS} # [ non mortels, mortels ]
        self.attendu = [0.0, 0.0]       # accidents attendus ( somme des intensites tirees ) : non mortels, mortels
        self.blessures = {}             # id d habitant -> [ ( jour, jours perdus ) ]
        self.remplacements = []         # ( jour, modele, site, issue )
        self.co2_t = 0.0
        self.vu_pharmacie = {}          # id de la pharmacie du moteur -> sa production cumulee deja abreuvee
        self.reserve_reseau = RESERVE_RESEAU_MIN   # unites du reseau du moteur que l industrie laisse aux autres sites


MOTIF_PRODUCTION, MOTIF_INTRANT, MOTIF_LIVRAISON = "production_industrie", "intrant_industrie", "livraison_interne"
MOTIF_VENTE, MOTIF_FABRICATION = "vente_industrie", "fabrication_machine"
MOTIFS_BIENS = (MOTIF_PRODUCTION, MOTIF_INTRANT, MOTIF_FABRICATION)


def _prix(b):
    return C.PRIX_MONDE[b] if b in C.PRIX_MONDE else BIENS[b][2]


def _dom(p): return p.domaines["industrie"]
def _membres_sites(w): return w.pays.domaines["industrie"].sites
def _membres_chargements(w): return w.pays.domaines["industrie"].chargements.values()

# ================================================================== le point de decision : entretenir une machine
ACTIONS_ENTRETIEN = ("attendre", "entretenir")


def _observer_entretien(ctx): return ctx.traits


def _regle_entretien(x, ctx):
    """Le plan du constructeur : entretenir des que le compteur depasse l intervalle ( trait 0 = compteur / 2 intervalles )."""
    return 1 if x[0] >= 0.5 else 0


def _temoin_entretien(x, ctx, rng): return 0


POINT_ENTRETIEN = D.PointDeDecision(
    "entretenir_machine", "industrie",
    traits=(("heures_entretien", "compteur horaire depuis le dernier entretien ( carnet ), sur deux intervalles constructeur"),
            ("usure", "heures de service cumulees sur la duree de vie du constructeur ( carnet )"),
            ("pannes_90j", "registre des pannes de l atelier : pannes de CETTE machine en 90 jours, sur 3"),
            ("risque_poste", "loi de fiabilite publiee du constructeur appliquee au compteur et a l usure : probabilite de "
                             "panne sur le prochain poste de 8 heures, sur 0,5 - une prevision, pas le tirage"),
            ("regime", "plan de production du jour de l atelier"),
            ("redondance", "tableau de l atelier : part des AUTRES machines en service ce matin"),
            ("stock_aval", "magasin de l usine ou marche de la region : couverture du produit de l atelier sur deux fois "
                           "sa cible")),
    actions=ACTIONS_ENTRETIEN,
    observer=_observer_entretien, regle=_regle_entretien, temoin=_temoin_entretien,
    note="l entretien decide coute tout de suite ses heures ( en postes de 8 h ) a CE choix ; puis chaque jour ou l atelier "
         "tourne, 1 moins la part de ses heures ouvertes ou CETTE machine etait en reparation, moins 5 par blesse et 100 "
         "par mort des accidents causes par SA panne ; moyenne sur 30 jours",
    horizon_j=HORIZON_ENTRETIEN)


def _traits_entretien(m, a):
    fia, o = m.fia, m.objet
    autres = [x for x in a.machines if x is not m]
    en_service = sum(1 for x in autres if x.objet.etat == O.SERVICE and x.pm_h <= 0)
    return (min(1.0, m.t_h / (2.0 * fia.pm_h)), o.usure, min(1.0, len(m.pannes) / 3.0),
            min(1.0, proba_panne(fia, m.t_h, HEURES_POSTE, o.usure) / 0.5), a.regime,
            en_service / len(autres) if autres else 1.0, min(1.0, max(0.0, a.couverture)))


# ================================================================== les lois, pour les portes
def simuler_flotte(fia, n, pannes_par_machine, rng, dt_h=DT_H, usure=0.0):
    """n machines du meme modele, sans entretien, reparees a chaque panne ( compteur a zero ), jusqu a ce que chacune
    ait connu `pannes_par_machine` pannes : rend les durees de service entre deux pannes. Meme loi et meme pas que le
    monde ( proba_panne, vectorisee ). Arreter a un nombre de pannes, pas a une date : une fenetre de temps fixe
    compterait les intervalles longs de travers."""
    t = np.zeros(n); k = np.zeros(n, np.int64); durees = []
    base = (1.0 + A_USURE * usure)
    while (k < pannes_par_machine).any():
        actif = k < pannes_par_machine
        p = 1.0 - np.exp(-(((t + dt_h) / fia.eta) ** fia.beta - (t / fia.eta) ** fia.beta) * base)
        panne = actif & (rng.random(n) < p)
        t = np.where(actif, t + dt_h, t)
        durees.append(t[panne].copy())
        t[panne] = 0.0; k[panne] += 1
    return np.concatenate(durees)


def tirer_accidents(rng, heures, secteur, facteur=1.0):
    """( non mortels, mortels ) pour `heures` heures travaillees dans un secteur, hors la part des pannes."""
    nf, m = TAUX_H[secteur]
    return (int(rng.poisson(nf * (1.0 - PART_PANNES) * heures * facteur)),
            int(rng.poisson(m * (1.0 - PART_PANNES) * heures * facteur)))


def tirer_jours_perdus(rng):
    u = rng.random(); acc = 0.0
    for a, b, part in JOURS_PERDUS:
        acc += part
        if u < acc: return int(rng.integers(a, b + 1))
    return JOURS_PERDUS[-1][1]


# ================================================================== le matin ( 6 h 20 ) : regimes et entretien
def _demande_lissee(p, e, b):
    w = p.w; em = p.domaine("economie").marches[e.lieu.marche.id]
    return max(0.0, w.marches[e.lieu.marche.id].stocks[b]) / max(ECO.DEMANDE_MIN, em.demande_lisse[b])


def _dispo_bien(D_, b, bid):
    return (math.fsum(s.stock[bid] for s in D_.sites if s.actif)
            + math.fsum(c.stock[bid] for c in D_.chargements.values()))


def cout_variable(p, a):
    """Drachmes par unite du bien directeur d un atelier, aux prix du jour : ses intrants ( biens du moteur au marche de
    sa region, biens nouveaux au prix de cession, electricite au tarif du reseau, gazole au marche ) et ses salaires.
    Un gisement porte tout son cout sur son bien directeur ( les coproduits sont un bonus : prudent )."""
    w = p.w; e = a.site.entreprise; m = w.marches[e.lieu.marche.id]
    salaire = PO.SALAIRE_HORAIRE.get(e.role, 0)
    if a.recette is not None:
        r = a.recette
        return math.fsum(k * (w.reseau.tarif if b == "electricite" else m.prix[b] if b in BIENS_E1 else BIENS[b][2])
                         for b, k in r.entrees.items()) + salaire / r.cadence_h
    g = a.gisement; sr = g.decouverture()
    par_t = ((1.0 + sr) * g.type.gazole_l_t / LITRES_PAR_UNITE_CARBURANT * m.prix["carburant"]
             + g.type.elec_kwh_t / KWH_PAR_UNITE_ELEC * w.reseau.tarif + salaire / g.minerai_h())
    return par_t / g.rendements[a.directeur]


def valeur_directeur(p, a):
    """Ce que rapporte une unite du bien directeur : le prix que le marche de la region paie au producteur pour un bien
    du moteur ( economie ), le prix de cession pour un bien nouveau."""
    b = a.directeur
    if b in BIENS: return BIENS[b][2]
    m = p.w.marches[a.site.entreprise.lieu.marche.id]
    return m.prix[b] * (1.0 - m.marge)


def _regimes(p, D_):
    """Chaque atelier regle son regime sur son bien directeur. Un bien du moteur ( fer, zinc, outils ) : par crans de
    0,25 sur la couverture du marche de sa region ( sous la cible : plus ; au-dela de deux fois : moins ), comme la regle
    du moteur et de l economie ; un gisement qui donne de l or tourne plein ( l or se vend au prix mondial ). Un bien
    nouveau : produire le besoin de ses clients ( ateliers aval a leur regime, commandes ), plus de quoi ramener le
    stock du pays a sa cible en 3 jours ; sans client, remplir 2 jours de production et s arreter. Et le cout : un
    atelier ne fait pas un bien nouveau a perte ( cout variable au-dessus du prix de cession : arret ) ; un bien du
    moteur perd un cran quand son prix ne couvre plus le cout variable, comme la regle de l economie. Un four a fonte
    electrique paie ~ 2 300 kWh par tonne : au tarif du moteur ( ~ 0,18 euro le kWh, le tarif reglemente grec ) il
    perd de l argent, et il n existe en vrai qu avec une electricite a quelques centimes ( hydraulique norvegienne )."""
    cat = p.socle.catalogue
    ateliers = [a for s in D_.sites if s.actif for a in s.ateliers]
    for a in ateliers:
        a.nominal_j = a.site.equipe * a.part * HEURES_POSTE * a.productivite()
        g = a.gisement
        if g is not None and g.reserve_t <= 0.0: a.regime = 0.0; continue
        b = a.directeur
        if b in BIENS: continue
        if g is not None and "or" in g.rendements: a.regime = 1.0; a.couverture = 0.0; continue
        couv = _demande_lissee(p, a.site.entreprise, b)
        cible = ECO.COUVERTURE_CIBLE_J.get(b, 5.0)
        a.couverture = couv / (2.0 * cible)
        if couv >= 2.0 * cible or cout_variable(p, a) > valeur_directeur(p, a): a.regime = max(REGIME_MIN, a.regime - PAS_REGIME)
        elif couv < cible: a.regime = min(1.0, a.regime + PAS_REGIME)
    for b in ORDRE_BIENS:
        prod = [a for a in ateliers if a.directeur == b and not (a.gisement is not None and a.gisement.reserve_t <= 0.0)]
        for a in [a for a in prod if cout_variable(p, a) > valeur_directeur(p, a)]:
            a.regime = 0.0; prod.remove(a)
        if not prod: continue
        besoin = D_.commandes.get(b, 0.0) + math.fsum(
            a.recette.entrees[b] * a.nominal_j * a.regime for a in ateliers if a.recette is not None and b in a.recette.entrees)
        nominal = math.fsum(a.nominal_j for a in prod)
        if nominal <= 0.0: continue
        cible = max(STOCK_MIN_J * nominal, JOURS_STOCK * besoin)
        dispo = _dispo_bien(D_, b, cat.id(b))
        r = min(1.0, max(0.0, (besoin + (cible - dispo) / JOURS_RATTRAPAGE) / nominal))
        for a in prod: a.regime = r; a.couverture = dispo / (2.0 * cible)


def _matin(p):
    """6 h 20, avant la prise de poste : l equipe de chaque site, les regimes, puis chaque machine en service d un
    atelier qui tourne decide de son entretien."""
    D_ = _dom(p); w = p.w
    for s in D_.sites:
        e = s.entreprise
        s.actif = not ECO.comptes(p, e).liquidee
        s.equipe = sum(1 for h in w.au_travail_de(e.lieu, e.role) if h.vivant) if s.actif else 0
    D_.reserve_reseau = RESERVE_RESEAU_MIN + HEURES_POSTE * math.fsum(
        len(w.au_travail_de(e.lieu, e.role)) * e.intrants.get("electricite", 0.0)
        for e in w.entreprises.values() if e.id not in p.repris and e.type != "centrale")
    _regimes(p, D_)
    dec = D_.decideur; parc = p.socle.parc
    for s in D_.sites:
        if not s.actif: continue
        for a in s.ateliers:
            if a.regime <= 0.0: continue
            for m in a.machines:
                if m.objet.etat != O.SERVICE or m.pm_h > 0: continue
                if dec.decider(m.objet.id, ContexteEntretien(_traits_entretien(m, a), m)) == 1:
                    m.pm_h = m.fia.pm_duree_h
                    dec.ajouter(m.objet.id, -m.fia.pm_duree_h / HEURES_POSTE)
                    parc.mettre_en_etat(m.objet, O.IMMOBILISE)
                    D_.stats["entretiens"] += 1
                    p.compter("entretien_machine")

# ================================================================== les mouvements de biens
def _e1(D_, nature, b, q):
    k = (nature, b); D_.e1_flux[k] = D_.e1_flux.get(k, 0.0) + q


def _dispo(p, s, b):
    """Ce qu un atelier du site peut prendre d un bien materiel : le stock du moteur pour ses biens, le stock du socle
    du site pour les biens nouveaux."""
    if b in BIENS_E1: return max(0.0, s.entreprise.stocks[b])
    return s.stock[p.socle.catalogue.id(b)]


def _electricite(p, D_, s, voulu):
    """L electricite d un atelier, en unites ( 10 kWh ) ; rend ce qui est servi. Avec le domaine 11, un soutirage a son
    reseau ( la marge des groupes en ligne, payee au tarif le soir par le domaine 11 ). Sans lui, le reseau du moteur,
    paye a l Etat au tarif comme le moteur - mais l industrie est interruptible : elle ne prend que ce qui depasse une
    journee du besoin des autres sites du moteur ( raffinerie, puits, pharmacie ). Un atelier reel tire 10 a 100 fois
    plus que les sites du moteur ( un four a fonte : 2 300 kWh par tonne ) : sans cette reserve, il assecherait le
    reseau et arreterait la raffinerie, donc les convois ( contrat d interruptibilite des industriels grecs, ADMIE
    2014-2019 )."""
    if voulu <= 0.0: return 0.0
    w = p.w; L = p.socle.livre
    if p.a("energie"):
        ENE = importlib.import_module(".d11_energie", __package__)
        q = ENE.soutirer(p, s.lieu, voulu * KWH_PAR_UNITE_ELEC, s.entreprise) / KWH_PAR_UNITE_ELEC
    else:
        q = min(voulu, max(0.0, w.reseau.stock - D_.reserve_reseau))
        if q <= 0.0: return 0.0
        w.reseau.stock -= q; L.flux["consomme"]["electricite"] += q
        L.transferer(s.entreprise, w.gouv, q * w.reseau.tarif, "electricite")
    D_.stats["electricite_u"] += q
    return q


def _consommer(p, D_, s, b, q):
    """Un intrant materiel consomme par un atelier : un bien du moteur sort de son stock ( livre.flux ) ; un bien
    nouveau passe par le grand livre."""
    w = p.w; L = p.socle.livre; e = s.entreprise
    if b in BIENS_E1:
        q = min(q, max(0.0, e.stocks[b]))
        e.stocks[b] -= q; L.flux["consomme"][b] += q; _e1(D_, "consomme", b, q)
    else:
        L.consommer(s.stock, p.socle.catalogue.id(b), q, MOTIF_INTRANT)


def _produire_bien(p, D_, s, b, q):
    """Un bien produit. L or paie la redevance miniere en nature a la reserve de l Etat, comme le moteur ( REDEVANCE_OR ;
    loi grecque 4512/2018 : une redevance progressive sur la valeur - a calibrer ). Les biens du moteur vont dans le
    stock de l entreprise, que le moteur expedie a son marche."""
    w = p.w; e = s.entreprise
    if b in BIENS_E1:
        if b == "or":
            r = q * C.REDEVANCE_OR
            e.stocks["or"] += q - r; w.publics["reserve"]["or"] += r
        else:
            e.stocks[b] += q
        w.flux["produit"][b] += q; e.produit_du_jour[b] += q; _e1(D_, "produit", b, q)
    else:
        p.socle.livre.produire(s.stock, p.socle.catalogue.id(b), q, MOTIF_PRODUCTION)


# ================================================================== un pas de 10 minutes
def _extraire(p, D_, s, a, h_eff):
    """h_eff heures-travailleur effectives ( presence, regime, machines, eau ) sur un gisement. Le gazole ( stock de
    l entreprise ) et l electricite ( reseau ) limitent. Rend la part du travail possible qui a ete faite."""
    g = a.gisement; e = s.entreprise; w = p.w
    if g.reserve_t <= 0.0 or h_eff <= 0.0: return 0.0
    sr = g.decouverture()
    voulu = h_eff * g.type.materiel_t_h / (1.0 + sr)
    minerai = min(g.reserve_t, voulu)
    gaz = minerai * (1.0 + sr) * g.type.gazole_l_t / LITRES_PAR_UNITE_CARBURANT
    if gaz > 0: minerai *= min(1.0, max(0.0, e.stocks["carburant"]) / gaz)
    if minerai <= 1e-12: return 0.0
    elec = minerai * g.type.elec_kwh_t / KWH_PAR_UNITE_ELEC
    if elec > 0: minerai *= _electricite(p, D_, s, elec) / elec
    if minerai <= 1e-12: return 0.0
    q = min(minerai * (1.0 + sr) * g.type.gazole_l_t / LITRES_PAR_UNITE_CARBURANT, max(0.0, e.stocks["carburant"]))
    e.stocks["carburant"] -= q; w.flux["brule"]["carburant"] += q; D_.stats["gazole_u"] += q; a.gazole_j += q
    if minerai >= g.reserve_t:
        minerai = g.reserve_t; g.reserve_t = 0.0
    else:
        g.reserve_t -= minerai
    g.extrait_t += minerai; g.sterile_t += minerai * sr
    a.cumul_minerai += minerai; a.produit_j += minerai
    for b, r in g.rendements.items(): _produire_bien(p, D_, s, b, minerai * r)
    p.compter("extraction_t", minerai)
    if g.reserve_t <= 0.0 and g.epuise_j < 0:
        g.epuise_j = p.jour
        p.noter("gisement_epuise", site=s.id, gisement=g.nom, extrait_t=round(g.extrait_t, 3))
    return minerai / voulu


def _transformer(p, D_, s, a, h_eff):
    """h_eff heures-travailleur effectives sur une recette : les passes que les intrants permettent. Rend la part du
    travail possible qui a ete faite."""
    r = a.recette
    voulu = h_eff * r.cadence_h
    if voulu <= 0.0: return 0.0
    passes = voulu
    for b, k in r.entrees.items():
        if b != "electricite": passes = min(passes, _dispo(p, s, b) / k)
    if passes <= 1e-12: return 0.0
    k_el = r.entrees.get("electricite", 0.0)
    if k_el > 0: passes *= _electricite(p, D_, s, passes * k_el) / (passes * k_el)
    if passes <= 1e-12: return 0.0
    for b, k in r.entrees.items():
        if b != "electricite": _consommer(p, D_, s, b, passes * k)
    for b, k in r.sorties.items(): _produire_bien(p, D_, s, b, passes * k)
    a.cumul_passes += passes; a.produit_j += passes
    p.compter("production_industrie", passes)
    return passes / voulu


def _panne(p, D_, s, a, m, presents):
    """Une panne : la machine s arrete pour sa reparation ; elle peut blesser ou tuer un travailleur present ( la part
    des accidents liee aux pannes, EU-OSHA )."""
    p.socle.parc.mettre_en_etat(m.objet, O.PANNE)
    m.repar_h = m.fia.mttr_h; m.t_h = 0.0
    m.pannes.append(p.jour)
    D_.stats["pannes"] += 1
    p.compter("panne_machine")
    rng = D_.rng_accidents
    pa, pm = a.p_acc * D_.facteur_risque, a.p_mort * D_.facteur_risque
    D_.attendu[0] += pa; D_.attendu[1] += pm
    u = rng.random()
    vivants = [h for h in presents if h.vivant]
    if u < pa + pm and vivants:
        h = vivants[int(rng.integers(len(vivants)))]
        mortel = u >= pa
        _accident(p, D_, s, a, h, mortel)
        if mortel: m.morts += 1
        else: m.blesses += 1


def _accident(p, D_, s, a, h, mortel):
    """Un accident du travail. Mort : par la population ( cause accident ). Blessure : par la medecine si elle est
    installee et sait `blesser` ( gravite dans [ 0 ; 1 ] : jours perdus sur 180 ), sinon comptee ici."""
    k = D_.accidents_secteur[a.secteur]
    if mortel:
        k[1] += 1; D_.stats["morts"] += 1
        POP.deceder(p, h, "accident")
        p.noter("accident_du_travail", habitant=h.id, site=s.id, atelier=a.nom, mortel=True, jours_perdus=0)
        return
    k[0] += 1; D_.stats["blesses"] += 1
    j = tirer_jours_perdus(D_.rng_accidents)
    D_.stats["jours_perdus"] += j
    D_.blessures.setdefault(h.id, []).append((p.jour, j))
    p.noter("accident_du_travail", habitant=h.id, site=s.id, atelier=a.nom, mortel=False, jours_perdus=j)
    if p.a("medecine"):
        MED = importlib.import_module(".d16_medecine", __package__)
        MED.blesser(p, h, LESION_SECTEUR.get(a.secteur, "travail"), iss_depuis_jours(j, D_.rng_accidents), "accident", s.lieu.id)
    else: p.compter("blessure_sans_medecine")


def _machines(p, D_, s, a, ouvert_h, service_h, presents):
    """Le temps passe pour les machines d un atelier : entretien et reparation avancent avec les heures d atelier
    ouvert ; une machine en service s use ( Parc ) et peut tomber en panne selon sa loi."""
    parc = p.socle.parc; rng = D_.rng_pannes
    for m in a.machines:
        o = m.objet
        m.ouvert_h += ouvert_h
        if o.etat == O.PANNE:
            m.panne_h += ouvert_h
            m.repar_h -= ouvert_h
            if m.repar_h <= 1e-9: m.repar_h = 0.0; parc.mettre_en_etat(o, O.SERVICE)
            continue
        if m.pm_h > 0.0:
            m.pm_h -= ouvert_h
            if m.pm_h <= 1e-9: m.pm_h = 0.0; m.t_h = 0.0; parc.mettre_en_etat(o, O.SERVICE)
            continue
        if service_h <= 0.0: continue
        lam = cumul_hasard(m.fia, m.t_h + service_h, o.usure) - cumul_hasard(m.fia, m.t_h, o.usure)
        D_.stats["pannes_attendues"] += lam
        m.t_h += service_h
        parc.user(o, service_h)
        if rng.random() < 1.0 - math.exp(-lam): _panne(p, D_, s, a, m, presents)


def _pas(p):
    """Chaque pas : les travailleurs presents de chaque site, leurs heures payees ( celles ou l atelier a vraiment
    travaille : sans intrant, sans reseau, c est du chomage technique, comme le moteur ), leurs accidents, la production
    de chaque atelier et la vie de ses machines."""
    D_ = _dom(p); w = p.w
    for s in D_.sites:
        if not s.actif or s.equipe <= 0: continue
        e = s.entreprise; lieu = e.lieu
        # EN COLONNES ( 24/09 ) : les presents trouves sur la table du moteur, une vue seulement pour eux, dans l ordre
        tb = w.table
        ids = np.array(w.ids_au_travail(lieu, e.role), np.int64)
        if len(ids): ids = ids[(tb.vivant[ids] == 1) & (tb.lieu[ids] == lieu.n) & (tb.poste[ids] == POSTE_TRAVAIL)]
        n = len(ids)
        if n == 0: continue
        presents = [PO.Habitant(tb, i) for i in ids.tolist()]
        presence = min(1.0, n / s.equipe)
        paye = 0.0
        rng = D_.rng_accidents
        for a in s.ateliers:
            if a.regime <= 0.0: continue
            h_a = n * DT_H * a.part * a.regime
            ouvert = DT_H * presence
            en_service = sum(1 for m in a.machines if m.objet.etat == O.SERVICE and m.pm_h <= 0.0)
            dispo = en_service / len(a.machines) if a.machines else 1.0
            h_eff = h_a * dispo * s.facteur_eau
            fait = _extraire(p, D_, s, a, h_eff) if a.gisement is not None else _transformer(p, D_, s, a, h_eff)
            if h_eff <= 0.0: fait = 1.0            # machines arretees : l equipe repare et entretient, elle est payee
            paye += a.part * a.regime * fait
            D_.heures_secteur[a.secteur] += h_a
            nf, mo = TAUX_H[a.secteur]
            lam_nf = nf * (1.0 - PART_PANNES) * h_a * D_.facteur_risque
            lam_m = mo * (1.0 - PART_PANNES) * h_a * D_.facteur_risque
            D_.attendu[0] += lam_nf; D_.attendu[1] += lam_m
            k_nf, k_m = int(rng.poisson(lam_nf)), int(rng.poisson(lam_m))
            for mortel, k in ((True, k_m), (False, k_nf)):
                for _ in range(k):
                    vivants = [h for h in presents if h.vivant]
                    if vivants: _accident(p, D_, s, a, vivants[int(rng.integers(len(vivants)))], mortel)
            _machines(p, D_, s, a, ouvert, ouvert * a.regime * min(1.0, fait) if fait > 0 else 0.0, presents)
        if paye > 0.0:
            np.add.at(tb.heures, ids[tb.vivant[ids] == 1], DT_H * paye)
            s.heures_j += n * DT_H * paye

# ================================================================== l apres-midi ( 16 h ) : gazole et livraisons entre sites
def _acheter_gazole(p, D_):
    """Les sites qui roulent au gazole l achetent au marche de leur region, TVA comprise, comme le moteur achete les
    intrants de ses entreprises : deux jours de reserve, sans descendre le marche sous la reserve de ses convois."""
    w = p.w; L = p.socle.livre; g = w.gouv
    for s in D_.sites:
        if not s.actif: continue
        besoin = 0.0
        for a in s.ateliers:
            gi = a.gisement
            if gi is None or gi.reserve_t <= 0: continue
            besoin += (s.equipe * a.part * HEURES_POSTE * a.regime * gi.type.materiel_t_h * gi.type.gazole_l_t
                       / LITRES_PAR_UNITE_CARBURANT)
        e = s.entreprise
        if besoin <= 0.0 or e.stocks["carburant"] >= 2.0 * besoin: continue
        m = w.marches[e.lieu.marche.id]
        q = min(3.0 * besoin - e.stocks["carburant"], m.stocks["carburant"] - RESERVE_CARBURANT_MARCHE)
        m.demande["carburant"] += max(0.0, q)
        if q <= 0.0: continue
        cout = q * m.prix["carburant"]
        if e.caisse < cout * (1.0 + g.tva): q = max(0.0, e.caisse / (m.prix["carburant"] * (1.0 + g.tva)))
        if q <= 1e-9: continue
        m.stocks["carburant"] -= q; e.stocks["carburant"] += q
        L.transferer(e, m, q * m.prix["carburant"], "achat intrant")
        L.transferer(e, g, q * m.prix["carburant"] * g.tva, "tva")


def _besoin_site(s, b):
    return math.fsum(a.recette.entrees[b] * a.nominal_j * a.regime for a in s.ateliers
                     if a.recette is not None and b in a.recette.entrees)


def _en_route_vers(D_, s, bid):
    return math.fsum(c.stock[bid] for c in D_.chargements.values() if c.destination is s)


def _livraisons(p, D_):
    """Chaque site qui manque d un intrant venu d ailleurs ( lignite, calcaire, gypse, sable, fonte ) le fait venir du
    site le plus proche qui en a ( au-dela de son propre jour de besoin ). Le camion part, les biens sont en route le
    temps du trajet ( km de la carte a la vitesse des convois ) ; le gazole est achete au marche de depart par le site
    qui recoit, qui paie aussi la marchandise au prix de cession ( ou la doit : creance du socle ). Un marche sans
    gazole au-dela de sa reserve : pas de camion ce jour-la."""
    w = p.w; L = p.socle.livre; cat = p.socle.catalogue
    for s in D_.sites:
        if not s.actif: continue
        biens = sorted({b for a in s.ateliers if a.recette is not None for b in a.recette.entrees if b in BIENS})
        for b in biens:
            bid = cat.id(b)
            besoin = _besoin_site(s, b)
            manque = JOURS_INTRANTS * besoin - s.stock[bid] - _en_route_vers(D_, s, bid)
            if besoin <= 0.0 or manque < LOT_MIN_T: continue
            sources = sorted((x for x in D_.sites if x is not s and x.actif and x.lieu.ile == s.lieu.ile),
                             key=lambda x: (x.lieu.distance(s.lieu), x.id))
            for src in sources:
                q = min(manque, src.stock[bid] - _besoin_site(src, b))
                if q < LOT_MIN_T: continue
                km = w.carte.km_route(src.lieu, s.lieu)
                m = w.marches[src.lieu.marche.id]
                gaz = 2.0 * km * C.CARBURANT_PAR_KM * math.ceil(q / CAMION_T)
                m.demande["carburant"] += gaz
                if m.stocks["carburant"] - RESERVE_CARBURANT_MARCHE < gaz:
                    p.compter("livraison_sans_gazole"); break
                m.stocks["carburant"] -= gaz; L.flux["brule"]["carburant"] += gaz
                L.transferer(s.entreprise, m, gaz * m.prix["carburant"], "carburant du convoi")
                duree = max(1, math.ceil(km / C.VITESSE_CONVOI_KMH * 60.0 / C.MINUTES_PAR_PAS))
                ch = Chargement(D_.prochain_chargement, src, s, _stock(), p.pas + duree)
                D_.prochain_chargement += 1
                L.deplacer(src.stock, ch.stock, bid, q, MOTIF_LIVRAISON)
                D_.chargements[ch.id] = ch
                p.poser(duree, "industrie_livraison", ch.id)
                if src.entreprise is not s.entreprise:
                    L.payer_ou_devoir(s.entreprise, src.entreprise, q * BIENS[b][2], MOTIF_VENTE, p.socle.creances, p.jour)
                D_.stats["livre_t"] += q
                p.compter("livraison_interne_t", q)
                manque -= q
                if manque < LOT_MIN_T: break


def _arrivee(p, cle, donnees):
    D_ = _dom(p); L = p.socle.livre
    ch = D_.chargements.pop(cle)
    for bid, q in list(ch.stock.items()): L.deplacer(ch.stock, ch.destination.stock, bid, q, MOTIF_LIVRAISON)


def _livrer_energie(p, D_):
    """Le lignite que le domaine 11 commande ( `commander( p, "charbon", t par jour )` ) part chaque jour aux cuves de ses
    centrales de l ile, par sa fonction `livrer_combustible` ( il paie au prix de cession ) ; chaque site garde son
    propre besoin du jour."""
    q = D_.commandes.get("charbon", 0.0)
    if q <= 0.0 or not p.a("energie"): return
    ENE = importlib.import_module(".d11_energie", __package__); bid = p.socle.catalogue.id("charbon")
    for s in D_.sites:
        dispo = s.stock[bid] - _besoin_site(s, "charbon")
        if not s.actif or dispo < LOT_MIN_T: continue
        q -= ENE.livrer_combustible(p, s.stock, "charbon", min(q, dispo), s.entreprise, BIENS["charbon"][2], s.lieu.ile)
        if q < LOT_MIN_T: break


def _apres_midi(p):
    D_ = _dom(p)
    _acheter_gazole(p, D_)
    _livraisons(p, D_)
    _livrer_energie(p, D_)


# ================================================================== le soir ( 23 h 30 )
def _eau_et_rejets(p, D_):
    """L eau du jour, prise au bassin du site ( usage industrie repris au territoire ) : ce qui manque limite la
    production du lendemain. Les rejets du jour au territoire, par polluant. La pharmacie du moteur, que le domaine ne
    reprend pas, a aussi son eau ici : le territoire ne fait plus les prelevements de fond des sites industriels."""
    w = p.w
    for s in D_.sites:
        if not s.actif: continue
        m3 = 0.0
        for a in s.ateliers:
            if a.produit_j <= 0.0: continue
            src = a.gisement if a.gisement is not None else a.recette
            m3 += a.produit_j * (src.eau_m3_t if a.gisement is not None else src.eau_m3)
            for pol, kg in src.rejets.items(): TER.rejeter(p, s.lieu, pol, a.produit_j * kg)
            if a.recette is not None:
                D_.co2_t += a.produit_j * math.fsum(v for k, v in a.recette.pertes.items() if k.startswith("co2") or k.startswith("gaz"))
        if m3 > 0.0:
            livre = TER.prelever(p, s.lieu, m3, "industrie")
            s.facteur_eau = max(0.0, min(1.0, livre / m3))
            D_.stats["eau_manquante_m3"] += m3 - livre
        else:
            s.facteur_eau = 1.0
    for e in w.entreprises.values():
        if e.type != "pharmacie": continue
        tot = sum(e.produit_du_jour.values())
        vu = D_.vu_pharmacie.setdefault(e.id, tot)
        if tot > vu: TER.prelever(p, e.lieu, (tot - vu) * TER.EAU_PAR_UNITE["pharmacie"], "industrie")
        D_.vu_pharmacie[e.id] = tot


def _noter_entretien(p, D_):
    """Chaque machine dont l atelier a ouvert aujourd hui encaisse sa journee : 1 moins la part des heures ouvertes
    passees en reparation, moins ses accidents. Les heures d un entretien ont deja ete comptees au choix qui l a
    decide : les compter ici les ferait payer aussi aux choix des jours precedents ( une note lue sur 30 jours melange
    sinon chaque choix avec les 29 suivants, et ne depend plus du sien : part du choix 0,004 au premier essai )."""
    dec = D_.decideur
    for m in D_.machines.values():
        if m.ouvert_h > 0.0:
            r = 1.0 - m.panne_h / m.ouvert_h - POIDS_BLESSE * m.blesses - POIDS_MORT * m.morts
            dec.noter(m.objet.id, r, p.jour)
        m.panne_h = m.ouvert_h = 0.0; m.blesses = m.morts = 0
        if m.pannes and m.pannes[0] < p.jour - 90: m.pannes = [j for j in m.pannes if j >= p.jour - 90]


def _atelier_de(D_, m):
    for s in D_.sites:
        for a in s.ateliers:
            if m in a.machines: return s, a
    return None, None


def _fonderie_qui_fabrique(p, D_, s, acier_t, pieces_t):
    cat = p.socle.catalogue
    for f in sorted((x for x in D_.sites if x.actif and x.type == "fonderie" and x.lieu.ile == s.lieu.ile),
                    key=lambda x: (x.lieu.distance(s.lieu), x.id)):
        if f.stock[cat.id("acier")] >= acier_t and f.stock[cat.id("pieces")] >= pieces_t: return f
    return None


def remplacer(p, m, motif="fin_de_vie"):
    """Une machine usee jusqu a la corde part au rebut ; l entreprise la remplace. Fabriquee au pays si une fonderie
    de l ile a l acier et les pieces ( 70 % et 10 % de sa masse ; le reste de sa valeur, moteurs et hydraulique, est
    importe ) ; importee sinon. L entreprise paie ( investissement, domaine 3 ) et demande un credit a sa banque s il le
    faut ; sans le credit, la machine n est pas remplacee et l atelier tourne avec une machine de moins."""
    D_ = _dom(p); parc = p.socle.parc; L = p.socle.livre; cat = p.socle.catalogue
    s, a = _atelier_de(D_, m)
    o = m.objet; mod = parc.modeles[o.modele]; e = s.entreprise
    parc.sortir(o, "rebut")
    a.machines.remove(m); del D_.machines[o.id]
    D_.stats["machines_rebut"] += 1
    prix = mod.prix_monde
    if e.caisse < prix:
        BQ.demander_credit(p, e, prix - e.caisse, "entreprise", "machine", DUREE_CREDIT_MACHINE)
    issue = "non_remplacee"
    if e.caisse >= prix:
        acier_t, pieces_t = PART_ACIER_MACHINE * mod.masse_kg / 1000.0, PART_PIECES_MACHINE * mod.masse_kg / 1000.0
        f = _fonderie_qui_fabrique(p, D_, s, acier_t, pieces_t)
        if f is not None:
            for b, q in (("acier", acier_t), ("pieces", pieces_t)):
                L.consommer(f.stock, cat.id(b), q, MOTIF_FABRICATION); D_.fabrications[b] = D_.fabrications.get(b, 0.0) + q
            ECO.investir(p, e, prix * (1.0 - PART_IMPORTEE_MACHINE), f.entreprise, "achat_machine")
            ECO.investir(p, e, prix * PART_IMPORTEE_MACHINE)
            neuf = parc.creer(mod.nom, e, s.lieu.id, "fabrique", p.pas); issue = "fabriquee"
            D_.stats["machines_fabriquees"] += 1
        else:
            ECO.investir(p, e, prix)
            neuf = parc.creer(mod.nom, e, s.lieu.id, "importe", p.pas); issue = "importee"
            D_.stats["machines_importees"] += 1
        nm = Machine(neuf, m.fia); a.machines.append(nm); D_.machines[neuf.id] = nm
    else:
        D_.stats["machines_non_remplacees"] += 1
    D_.remplacements.append((p.jour, mod.nom, s.id, issue))
    p.noter("machine_hors_service", machine=o.id, modele=mod.nom, site=s.id, remplacement=issue)
    return issue


def _soir(p):
    D_ = _dom(p)
    _eau_et_rejets(p, D_)
    _noter_entretien(p, D_)
    for m in [m for m in D_.machines.values() if m.objet.usure >= 1.0 and m.objet.etat == O.SERVICE and m.pm_h <= 0]:
        remplacer(p, m)
    for s in D_.sites:
        s.heures_j = 0.0
        for a in s.ateliers: a.produit_j = 0.0; a.gazole_j = 0.0


def _minuit(p):
    """Les flux de hasard du jour : les pannes et les accidents d un jour ne dependent pas de ceux de la veille."""
    D_ = _dom(p)
    D_.rng_pannes = p.du_jour("industrie_pannes")
    D_.rng_accidents = p.du_jour("industrie_accidents")


def _cloture(p, comptes):
    """Les biens que le grand livre a vus sous les motifs du domaine ( production, intrants, fabrication ), cumules :
    la matiere de l audit."""
    D_ = _dom(p)
    for nature, motif, bien, q in comptes["biens"]:
        if motif in MOTIFS_BIENS:
            k = (nature, bien); D_.livre_biens[k] = D_.livre_biens.get(k, 0.0) + q

# ================================================================== l audit et les bilans ( portes )
def bilan_recette(r):
    """( entrees, sorties + pertes ) en tonnes, et ( fer entre, fer sorti + fer perdu ) : les deux bilans d une
    recette. L electricite n a pas de masse."""
    ent = math.fsum(q * MASSE_T[b] for b, q in r.entrees.items() if b not in ENERGIES) + math.fsum(r.libres.values())
    sor = math.fsum(q * MASSE_T[b] for b, q in r.sorties.items()) + math.fsum(r.pertes.values())
    fe_in = math.fsum(q * TENEUR_FE[b] for b, q in r.entrees.items() if b in TENEUR_FE)
    fe_out = math.fsum(q * TENEUR_FE[b] for b, q in r.sorties.items() if b in TENEUR_FE) + (r.fer_perdu or 0.0)
    return (ent, sor), (fe_in, fe_out)


def audit(p):
    """Pour chaque ( nature, bien ) : ( ce que les gisements et les recettes impliquent, ce que le grand livre a vu
    sous les motifs du domaine - jour en cours compris - ou, pour un bien du moteur, ce que le domaine a ecrit dans
    livre.flux ). Un bien cree hors d une recette sous un motif du domaine creuse un ecart."""
    D_ = _dom(p); L = p.socle.livre; cat = p.socle.catalogue
    implique = {}
    def ajouter(k, q): implique[k] = implique.get(k, 0.0) + q
    for s in D_.sites:
        for a in s.ateliers:
            if a.gisement is not None:
                for b, r in a.gisement.rendements.items(): ajouter(("produit", b), a.cumul_minerai * r)
            else:
                for b, k in a.recette.entrees.items():
                    if b not in ENERGIES: ajouter(("consomme", b), a.cumul_passes * k)
                for b, k in a.recette.sorties.items(): ajouter(("produit", b), a.cumul_passes * k)
    for b, q in D_.fabrications.items(): ajouter(("consomme", b), q)
    vu = dict(D_.livre_biens)
    for (nature, motif, bid), q in L.jour_biens.items():
        if motif in MOTIFS_BIENS:
            k = (nature, cat[bid].nom); vu[k] = vu.get(k, 0.0) + q
    for k, q in D_.e1_flux.items(): vu[k] = vu.get(k, 0.0) + q
    return {k: (implique.get(k, 0.0), vu.get(k, 0.0)) for k in sorted(set(implique) | set(vu))}


def ecart_audit(p):
    """Le pire ecart relatif de l audit, et son bien."""
    pire, qui = 0.0, None
    for k, (i, v) in audit(p).items():
        x = abs(i - v) / max(1e-9, abs(i), abs(v))
        if abs(i - v) > 1e-9 and x > pire: pire, qui = x, k
    return pire, qui


# ================================================================== l API des autres domaines
def stock_du_pays(p, bien):
    """Les unites d un bien nouveau dans les sites et en route."""
    return _dispo_bien(_dom(p), bien, p.socle.catalogue.id(bien))


def commander(p, bien, unites_par_jour):
    """Une commande permanente d un autre domaine ( immobilier : ciment, acier, verre ; transport : pieces ; armee :
    acier ) : les ateliers la produisent en plus du besoin des chaines. 0 l annule."""
    if bien not in BIENS: raise KeyError(f"industrie : {bien!r} n est pas un bien du domaine")
    if not 0.0 <= unites_par_jour < 1e7: raise ValueError(f"commande hors bornes : {unites_par_jour!r}")
    _dom(p).commandes[bien] = float(unites_par_jour)


def livrer(p, bien, quantite, vers, payeur, prix=None):
    """Livre `quantite` unites d un bien nouveau a un autre domaine : du site le mieux pourvu vers le Stock `vers` ( un
    biens.Stock du socle, que le domaine acheteur a inscrit au registre ) ; `payeur` ( un detenteur a caisse ) paie
    l entreprise du site au prix de cession ( le prix mondial du catalogue par defaut ), ou le doit ( creance ). Rend la
    quantite livree."""
    D_ = _dom(p); L = p.socle.livre; bid = p.socle.catalogue.id(bien)
    reste = float(quantite)
    for s in sorted((x for x in D_.sites if x.actif), key=lambda x: (-x.stock[bid], x.id)):
        if reste <= 0.0: break
        q = L.deplacer(s.stock, vers, bid, min(reste, s.stock[bid]), MOTIF_LIVRAISON)
        if q <= 0.0: continue
        L.payer_ou_devoir(payeur, s.entreprise, q * (BIENS[bien][2] if prix is None else prix), MOTIF_VENTE,
                          p.socle.creances, p.jour)
        reste -= q
    return float(quantite) - reste


def valeur_stocks(p, entreprise):
    """Drachmes : les biens nouveaux du site d une entreprise reprise, au prix de cession. Les comptes du domaine 3
    ( _valeur_stocks ) ne voient que les biens du moteur : sans cette ligne, ce qu une carriere a mis en stock ( ciment,
    lignite ) sort de son resultat comme une charge sans produit."""
    s = _dom(p).par_entreprise.get(entreprise.id)
    if s is None: return 0.0
    cat = p.socle.catalogue
    return math.fsum(q * BIENS[cat[b].nom][2] for b, q in s.stock.items())


def charbon_demande(p):
    """Le lignite que les ateliers demandent par jour a leur regime ( t/jour ) : ce que le domaine 11 lit s il veut
    brancher des centrales au lignite."""
    return math.fsum(_besoin_site(s, "charbon") for s in _dom(p).sites if s.actif)


def electricite_consommee(p):
    """Unites du reseau consommees par le domaine depuis l installation ( 1 unite = KWH_PAR_UNITE_ELEC kWh )."""
    return _dom(p).stats["electricite_u"]


def machines_de(p, entreprise):
    """Les objets du Parc ( machines ) d une entreprise reprise : ce que l immobilier, l assurance, la justice lisent."""
    s = _dom(p).par_entreprise.get(entreprise.id)
    return [m.objet for a in s.ateliers for m in a.machines] if s is not None else []


def forcer_reserve(p, site_id, gisement, tonnes):
    """Un scenario ( portes ) : le gisement d un site devient un gisement neuf de `tonnes` tonnes."""
    s = _dom(p).par_entreprise[site_id]
    g = next(a.gisement for a in s.ateliers if a.gisement is not None and a.gisement.nom == gisement)
    g.reserve0_t = g.reserve_t = float(tonnes); g.extrait_t = g.sterile_t = 0.0; g.epuise_j = -1
    return g


def accidents(p):
    """{ secteur : ( heures travaillees, non mortels, mortels ) } depuis l installation, et les attendus."""
    D_ = _dom(p)
    return {k: (D_.heures_secteur[k], *D_.accidents_secteur[k]) for k in SECTEURS}, tuple(D_.attendu)


# ================================================================== installation
def _stock():
    from ..socle import biens as B
    return B.Stock()


def _plan(e):
    return PLAN_ALTIS.get(e.lieu.id) or PLAN_ALTIS[PLAN_PAR_TYPE[e.type]]


def _p_accident_panne(a):
    """La probabilite qu une panne blesse ( ou tue ) : la part PART_PANNES du risque du secteur, rapportee aux pannes
    que font les machines de l atelier par heure travaillee sous le plan d entretien du constructeur ( une machine tourne
    quand son equipe travaille : equipe x part heures-travailleur par heure-machine )."""
    equipe = max(1e-9, a.site.equipe_ref * a.part)
    pannes_h = math.fsum(taux_pannes_reference(m.fia) / equipe for m in a.machines)
    nf, mo = TAUX_H[a.secteur]
    return (min(1.0, nf * PART_PANNES / pannes_h), min(1.0, mo * PART_PANNES / pannes_h)) if pannes_h > 0 else (0.0, 0.0)


def installer(p):
    w = p.w; L = p.socle.livre; cat = p.socle.catalogue; parc = p.socle.parc
    # --- les biens : les nouveaux au catalogue, ceux du moteur calibres
    for nom, (fam, unite, prix, tva, masse, vol, src) in BIENS.items():
        cat.declarer(nom, fam, unite, prix, categorie_tva=tva, masse_kg=masse, volume_l=vol, source=src)
    for nom, (masse, vol, _, src) in CALIBRAGE_E1.items():
        b = cat[nom]; b.masse_kg, b.volume_l, b.source = masse, vol, "industrie ( domaine 10 ) : " + src
    L.declarer_motif(MOTIF_VENTE, "achat", "industrie")
    L.declarer_motif("achat_machine", "achat", "industrie")
    J = p.socle.journal
    for t, champs in (("accident_du_travail", ("habitant", "site", "atelier", "mortel", "jours_perdus")),
                      ("gisement_epuise", ("site", "gisement", "extrait_t")),
                      ("machine_hors_service", ("machine", "modele", "site", "remplacement"))):
        J.declarer(t, "industrie", "individuel", champs)
    for t in ("panne_machine", "entretien_machine", "extraction_t", "production_industrie", "livraison_interne_t",
              "blessure_sans_medecine", "livraison_sans_gazole"):
        J.declarer(t, "industrie", "compte")
    for nom, v in MODELES.items():
        parc.declarer_modele(nom, "machine", PRIX_MACHINE[nom], v[1], v[2], v[8], None, v[9] + " ; fiabilite a calibrer")
    D_ = Industrie()
    p.domaines["industrie"] = D_
    # --- les sites repris, leurs ateliers, leurs machines ( d ages varies )
    rng = p.hasard("industrie_installation")
    for e in sorted(w.entreprises.values(), key=lambda e: (TYPES_REPRIS.index(e.type) if e.type in TYPES_REPRIS else 9, e.id)):
        if e.type not in TYPES_REPRIS: continue
        s = Site(e, _stock())
        s.equipe = s.equipe_ref = sum(1 for h in w.au_travail_de(e.lieu, e.role) if h.vivant)
        k = max(1, int(round(s.equipe_ref / EQUIPE_REFERENCE[e.type]))) if s.equipe_ref else 1
        for nom, ref, part, machines in _plan(e):
            if ref in GISEMENTS:
                t, res, sr0, sr1, ten, eau, rej, src = GISEMENTS[ref]
                a = Atelier(nom, s, Gisement(ref, t, res * k, sr0, sr1, ten, eau, rej, src), None, part)
            else:
                a = Atelier(nom, s, None, RECETTES[ref], part)
            for mod, n in sorted(machines.items()):
                for _ in range(n * k):
                    o = parc.creer(mod, e, e.lieu.id, "initial", p.pas, float(rng.uniform(0.0, 0.7)))
                    m = Machine(o, FIABILITE[mod])
                    m.t_h = float(rng.uniform(0.0, FIABILITE[mod].pm_h))     # un parc en service, pas sorti d usine
                    a.machines.append(m); D_.machines[o.id] = m
            a.p_acc, a.p_mort = _p_accident_panne(a)
            s.ateliers.append(a)
        if abs(sum(a.part for a in s.ateliers) - 1.0) > 1e-9: raise ValueError(f"{e.id} : parts d equipe qui ne font pas 1")
        D_.sites.append(s); D_.par_entreprise[e.id] = s
        p.reprendre(e, "industrie")
        # le capital de l entreprise devient celui de ses machines : valeur nette, et la duree qui donne leur usure annuelle
        objets = [m.objet for a in s.ateliers for m in a.machines]
        net = math.fsum(parc.modeles[o.modele].prix_monde * (1.0 - o.usure) for o in objets)
        par_an = math.fsum(parc.modeles[o.modele].prix_monde / (parc.modeles[o.modele].vie_h / (HEURES_POSTE * 365.0))
                           for o in objets)
        ECO.reevaluer_capital(p, e, net, net / par_an if par_an > 0 else None)
    for e in w.entreprises.values():
        if e.type == "pharmacie": D_.vu_pharmacie[e.id] = sum(e.produit_du_jour.values())
    reg = p.socle.registre
    reg.inscrire("industrie_sites", "entreprises", _membres_sites, None, "stock", None)
    reg.inscrire("industrie_chargements", "entreprises", _membres_chargements, None, "stock", None)
    TER.reprendre_usage(p, "industrie")
    D_.decideur = p.decideur(POINT_ENTRETIEN)
    D_.rng_pannes = p.du_jour("industrie_pannes")
    D_.rng_accidents = p.du_jour("industrie_accidents")
    p.echeance("industrie_livraison", _arrivee)
    p.routine(0.0, 5, "industrie", _minuit)
    for minute in range(0, 24 * 60, C.MINUTES_PAR_PAS):
        p.routine(minute / 60.0, 50, "industrie", _pas)
    p.routine(6 + 20 / 60, 40, "industrie", _matin)
    p.routine(16.0, 40, "industrie", _apres_midi)
    p.routine(23.5, 40, "industrie", _soir)
    p.cloture("industrie", _cloture)
    return D_
