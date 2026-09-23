"""DOMAINE 9 - AGRICULTURE ET ALIMENTATION : CULTURES, ELEVAGE, PECHE, SAISONS, RENDEMENTS, SOLS, TRANSFORMATION,
CONSERVATION, PEREMPTION.

FICHE
1. Classes. Les lois : Culture ( une culture de l Egee : produit, part de la parcelle, rendement reel et sa source,
   effet de l absence d engrais, calendrier de semis, de recolte, de taille, periodes ou le temps fait le rendement,
   heures de travail ), Espece ( brebis, chevre : lait, prolificite, carcasses, reforme, mortalite, classname Arma ),
   Recette ( une transformation : moudre, presser, fromager, trier les semences ; masse et calories ne s y creent pas ).
   L etat : Exploitation ( une ferme du moteur reprise : son grenier, un Stock du socle, et les LOTS dates qui le
   composent ; ses paysans ; ses heures du jour ; sa part du besoin de sa region ; son caique s il est cotier ),
   Champs ( les cultures de toutes les fermes en tableaux culture x ferme : surfaces, campagne en cours, climat
   accumule, recolte attendue, faite, perdue ), Troupeaux ( tableaux ferme x espece : adultes, recrues, naissances
   des 50 derniers jours, paturage et chaumes sur pied, etat d alimentation ), ContexteVente, Agriculture ( l etat du
   domaine ). Aucune colonne par habitant : un paysan est lu dans l index du moteur ( w.au_travail_de ).
2. Invariants. Chaque bien du domaine est dans le Stock d une exploitation ( famille « exploitations » du registre ) et
   n y entre ou n en sort que par le grand livre, avec son motif : produit ( recolte, traite, abattage, peche, moudre,
   presser, fromager, trier, taille, stock_initial ), consomme ( moudre, presser, fromager, trier, cuisiner, semis,
   affourager ), perime ( peremption ), exporte ( vente_negoce ). Pour chaque bien, la somme des lots = le stock
   ( `ecarts_lots` ). Chaque lot perit en entier le jour ou son age atteint la conservation du catalogue. Une recette
   ne cree ni masse ni calories ; une ration vaut EXACTEMENT 2 500 kcal d ingredients consommes ( motif cuisiner ). Les
   rations entrent dans le stock de la ferme du moteur ( e.stocks[ nourriture ] ) et dans livre.flux[ produit ]. Le
   cheptel : adultes + recrues = depart + naissances - abattus - morts ( `bilan_cheptel` ). L argent : les ventes au
   negoce viennent de l exterieur ( recevoir_de_l_exterieur, motif vente_negoce ) dans la caisse de la ferme, que la
   paie du moteur partage entre ses paysans ; le domaine ne detient AUCUN argent.
3. Decision `vendre_recolte` ( chaque ferme, tous les 7 jours, toutes le meme jour ) : stocker, vendre au negoce le
   surplus au-dela de la soudure, tout vendre. Traits : soudure ( grain, huile, fromage en jours de sa part du besoin
   de sa region jusqu a leur prochaine recolte ), jours jusqu a la moisson, prix et couverture de son marche, faim de
   sa region, part de ses stocks qui perit dans les 30 jours, part au-dela de la soudure. Note ( horizon 14 jours : un
   grenier vide se voit en une semaine, pas le soir meme ) : chaque jour, les rations que CETTE ferme a livrees a SA
   region sur sa part equitable ( surface ) de ce que la region demandait ( bornee a 1 ), moins 4 x la faim de SA
   region x la part non livree, plus 0,1 x son revenu du jour ( rations, et grain, huile, feta vendus au negoce ; pas le
   frais, que la decision ne touche pas ) rapporte a la valeur de sa part au prix mondial. Regle : stocker si sa region
   a faim ou si le grenier est sous 1,25 soudure, vendre le surplus sinon ( ou si un tiers du grenier va perir ).
   Temoin : tout vendre tout de suite. La note depend du choix quand les greniers sont comparables ( la premiere
   decision apres la moisson ) ; au hasard, un grenier vide par un « tout vendre » passe le reste pese sur toutes ses
   notes suivantes, quelle que soit l action du jour ( porte test_part_du_choix ).
4. Evenements. Individuels : recolte, semis, bateau_au_rebut. Comptes : rations_agricoles, astreinte_elevage ( h ),
   peremption_agricole ( kg ), vente_negoce ( drachmes ), sortie_peche ( kg ), mise_bas, abattage ( kg ),
   mort_betail, perte_recolte ( kg ), irrigation_agricole ( m3 ), disette_fourrage.
5. Liens. Lit le territoire ( 8 ) : l ETR des parcelles seches et irriguees et leurs normales ( le rendement climatique,
   separe sec / irrigue ), la chaleur et les crues, le vent du jour ( la peche ) ; preleve l eau d irrigation apres
   `reprendre_usage( irrigation )` et la verse sur la parcelle irriguee ( bilan des sols tenu comme le territoire le
   tient ). Lit l economie ( 3 ) : les prix affiches, la couverture des marches. L agenda ( 5 ), s il est la, decide qui
   est au travail : seul compte `poste == travail` DANS le lieu de la ferme ; un jour de repos, les betes sont soignees
   par une ASTREINTE bornee a leur besoin ( traite du matin et du soir, 2,5 h au plus par paysan ), comptee a part.
   L engrais ( domaine 10 ) : si le catalogue le connait et qu il est dans le grenier au jour de l apport, il est
   consomme et la culture rend son rendement plein ; sinon le rendement sans engrais. Reprend les 27 fermes du moteur
   ( p.reprendre ) : produire des fermes est au domaine. Donne ( API en fin de fichier ) : exploitation_de, stock_de,
   stocks_vivres, requisitionner ( 26 ), composition_regionale ( 16 ), rendement_attendu, rendement_constate,
   sinistres ( 20 ), recoltes_a_expedier, ventes_negoce ( 15 ), besoins_engrais ( 10 ), kcal, bilan_cheptel,
   ecarts_lots, bilans_recettes.
6. Portes : tests_d09_agriculture.py.
7. Arma. Le caique de peche ( CUP_C_Fishing_Boat_Chernarus, modele du Parc ) ; brebis et chevres ( Sheep_random_F,
   Goat_random_F ). arma_preuve = None : rien n a ete vu vivre en jeu.
8. Cout. Tout est par ferme ( 27 sur Altis, quelle que soit la population : le moteur pose une ferme par village ) sauf
   la presence, lue a chaque pas sur les seuls paysans ( 144 lectures par paysan et par jour ). Mesure : test_cout. A
   un million d habitants ( 220 000 paysans ) la presence coute ~30 millions de lectures par jour : au-dela, la lire en
   numpy dans les colonnes de l agenda ( agenda_activite ), qui disent la meme chose."""
import json, math, os
from collections import deque
import numpy as np
from .. import config as C, carte as K
from ..socle import decision as D, biens as SB
from . import d08_territoire as TER, pays as PAYS

JOURS_AN = 365
PAS_H = C.MINUTES_PAR_PAS / 60.0
EPS = 1e-9


def _j(mois, jour):
    """Le jour de l an ( 0 a 364 ) d une date d une annee non bissextile."""
    return int(TER.DEBUT_MOIS[mois - 1]) + jour - 1


def _dans(d, a, b):
    """d dans la fenetre [ a ; b ] du calendrier ; une fenetre peut passer le nouvel an."""
    return a <= d <= b if a <= b else (d >= a or d <= b)


def _longueur(a, b): return (b - a) % JOURS_AN + 1


def _ecoule(a, d): return (d - a) % JOURS_AN


def _doy(p):
    """Le jour de l an du monde, comme le territoire le lit ( une annee bissextile finit a 364 )."""
    return min(JOURS_AN - 1, p.socle.calendrier.date(p.pas).timetuple().tm_yday - 1)


# ================================================================== les biens du domaine
# nom : ( famille, unite, prix mondial en EUROS par unite ( converti en drachmes a l installation par le taux commun
# pays.EUROS_PAR_DRACHME ), TVA, masse kg par unite, volume l par unite, conservation en jours, kcal par unite, source ). kcal : ce que l homme en tire ; 0 pour
# ce qui n est pas de la nourriture humaine ( le fourrage nourrit les betes, la semence la terre ).
BIENS = {
    "cereales": ("aliment", "kg de grain de ble dur a 12 % d humidite", 0.30, "reduite", 1.0, 1.30, 730.0, 3390.0,
                 "prix : ble dur au producteur, Grece 2019-2023, 0,25 a 0,45 EUR/kg ( Commission europeenne, a calibrer ) ; "
                 "USDA SR : 339 kcal/100 g ; densite apparente 0,77 kg/l ; grain sec en grenier : deux ans ( FAO )"),
    "farine": ("aliment", "kg de semoule et farine de ble dur", 0.55, "reduite", 1.0, 1.80, 180.0, 3600.0,
               "USDA SR : semoule 360 kcal/100 g ; densite 0,55 kg/l ; six mois au sec ( a calibrer )"),
    "legumes": ("aliment", "kg de legumes frais d ete ( tomate, courgette, poivron, aubergine, pomme de terre )", 0.60,
                "reduite", 1.0, 2.00, 10.0, 250.0,
                "kcal : moyenne USDA ponderee ( tomate 18, courgette 17, poivron 20, pomme de terre 77 kcal/100 g ), a "
                "calibrer ; en cagettes ~0,5 kg/l ; 7 a 14 jours hors du froid"),
    "fruits": ("aliment", "kg de fruits frais ( peche, abricot, raisin, figue, pasteque )", 0.70, "reduite", 1.0, 2.00,
               10.0, 550.0, "kcal : moyenne USDA ( peche 39, raisin 69, figue 74, pasteque 30 kcal/100 g ), a calibrer"),
    "olives": ("aliment", "kg d olives fraiches a huile", 0.60, "reduite", 1.0, 1.60, 3.0, 2000.0,
               "a moudre dans les 24 a 72 h ( acidite, fermentation ) ; ~20 % d huile ( 1 768 kcal/kg ) plus sucres et "
               "proteines ; prix des olives a huile au producteur, annee normale ( a calibrer )"),
    "huile": ("aliment", "kg d huile d olive vierge extra", 4.5, "reduite", 1.0, 1.09, 540.0, 8840.0,
              "prix : vrac grec 2015-2022, 3,5 a 4,5 EUR/kg ( 7 a 9 en 2023-2024 ) ; USDA 884 kcal/100 g ; 0,915 kg/l ; "
              "18 mois ( date de durabilite usuelle )"),
    "lait": ("aliment", "kg de lait cru de brebis et de chevre", 1.0, "reduite", 1.0, 0.97, 2.0, 930.0,
             "brebis 108, chevre 69 kcal/100 g ( USDA ), au prorata de la production du troupeau ; lait cru au bac du "
             "village : 1 a 3 jours ; prix au producteur 2022-2023 ~1 EUR/kg"),
    "fromage": ("aliment", "kg de feta en saumure", 6.5, "reduite", 1.0, 1.00, 240.0, 2640.0,
                "USDA feta 264 kcal/100 g ; en saumure 6 a 12 mois ; prix de gros 6 a 8 EUR/kg ( a calibrer )"),
    "viande": ("aliment", "kg de carcasse d agneau et de chevreau", 7.0, "reduite", 1.0, 1.10, 4.0, 2300.0,
               "carcasse mi-grasse ~230-280 kcal/100 g ( USDA agneau ) ; chambre froide du village : quelques jours ; "
               "prix carcasse 6 a 8 EUR/kg"),
    "poisson": ("aliment", "kg de poisson entier frais", 6.0, "reduite", 1.0, 1.30, 2.0, 900.0,
                "partie comestible ~55 % a ~160 kcal/100 g ( a calibrer ) ; sur glace 1 a 3 jours ; premiere vente de la "
                "peche cotiere 5 a 10 EUR/kg"),
    "fourrage": ("matiere_premiere", "kg de foin, de son ou de grain fourrager ( matiere seche )", 0.20, "reduite", 1.0,
                 8.0, 365.0, 0.0, "foin de luzerne 0,18-0,25 EUR/kg ; balles ~130 kg/m3 ; un an au sec"),
    "semences": ("matiere_premiere", "kg de grain trie pour la semence", 0.60, "reduite", 1.0, 1.30, 365.0, 0.0,
                 "semence de ble dur 0,5-0,7 EUR/kg ; faculte germinative : une saison ( a calibrer )"),
    "bois": ("energie", "kg de bois de chauffage ( taille des oliviers et des vergers )", 0.12, "normale", 1.0, 2.20,
             math.inf, 0.0, "bois de chauffage 100-150 EUR/t ; stere ~450 kg/m3"),
}
NOMS_BIENS = tuple(BIENS)
KCAL = {b: v[7] for b, v in BIENS.items()}
KCAL_RATION = 2500.0          # la ration du moteur ( config.NOURRITURE_PAR_JOUR = 1 ) : besoin moyen d un adulte actif
STOCKABLES = ("cereales", "huile", "fromage")          # ce que la decision vend ou garde
FRAIS_VENDABLES = ("legumes", "fruits", "viande", "poisson")   # vendus au negoce le jour meme au-dela de 2 jours d usage
PARITE_NEGOCE = 0.8           # le negociant paie 0,8 fois le prix mondial ( transport, marge ) : la parite a laquelle le
                              # moteur exporte deja ses surplus de nourriture ( monde.py, expedier )


# ================================================================== les recettes
class Recette:
    """La transformation d un kilogramme d un bien. La masse ne s y cree pas : les sorties font au plus 1 kg, le reste
    est une perte declaree ( lactoserum, grignons et margines, humidite, poussieres ). Les calories non plus : l ecart
    entre l entree et les sorties quitte la chaine alimentaire humaine ( le son et le lactoserum vont aux betes )."""
    __slots__ = ("nom", "entree", "sorties", "perte_kg", "kcal_hors_chaine", "source")

    def __init__(self, nom, entree, sorties, source):
        if entree not in BIENS or any(b not in BIENS for b in sorties): raise ValueError(f"{nom} : bien inconnu")
        if any(not 0.0 < q <= 1.0 for q in sorties.values()): raise ValueError(f"{nom} : rendement hors ]0 ; 1]")
        masse = math.fsum(sorties.values())
        if masse > 1.0 + 1e-12: raise ValueError(f"{nom} : {masse} kg de sorties pour 1 kg d entree - une recette ne cree pas de matiere")
        kcal_out = math.fsum(q * KCAL[b] for b, q in sorties.items())
        if kcal_out > KCAL[entree] * (1.0 + 1e-12): raise ValueError(f"{nom} : une recette ne cree pas de calories")
        self.nom, self.entree, self.sorties, self.source = nom, entree, dict(sorties), source
        self.perte_kg = 1.0 - masse
        self.kcal_hors_chaine = KCAL[entree] - kcal_out


RECETTES = {
    "moudre": Recette("moudre", "cereales", {"farine": 0.78, "fourrage": 0.20},
                      "taux d extraction de la semoule de ble dur ~75-80 % ; le son et les remoulages vont aux betes ; 2 % "
                      "d humidite et de poussieres"),
    "presser": Recette("presser", "olives", {"huile": 0.20},
                       "rendement en huile des olives grecques 18 a 22 % ( a calibrer ) ; grignons et margines au rebut"),
    "fromager": Recette("fromager", "lait", {"fromage": 0.20},
                        "feta : 4 a 6 kg de lait par kg ( brebis ~4, chevre ~6 ), a calibrer ; le lactoserum part"),
    "trier": Recette("trier", "cereales", {"semences": 0.97, "fourrage": 0.03},
                     "triage de la semence de ferme : 2 a 5 % de dechets, aux betes"),
}

# La ration : 2 500 kcal faits de cinq composantes. Parts nominales : bilans alimentaires de la FAO pour la Grece
# ( 2019 ; cereales ~29 % des calories disponibles, huiles ~20 %, produits animaux ~26 %, fruits ~5 %, legumes ~3 % ),
# ramenees aux groupes du modele sans sucre ni alcool. Plafonds : ce qu un repas peut porter d une composante quand les
# autres manquent ( a calibrer ). Dans la composante animale, le plus perissable d abord.
COMPOSANTES = ("farine", "huile", "legumes", "fruits", "animal")
PARTS_RATION = (0.44, 0.16, 0.06, 0.06, 0.28)
PARTS_MAX = (0.85, 0.25, 0.20, 0.20, 0.50)
BIENS_COMPOSANTE = (("farine",), ("huile",), ("legumes",), ("fruits",), ("poisson", "lait", "viande", "fromage"))
PART_FROMAGE_HORS_TRAITE = 0.7   # hors saison de traite, la part animale vient surtout du fromage ( soudure du fromage )


# ================================================================== les cultures
class Culture:
    """Une culture de l Egee sur la parcelle d un village.
      bien, irriguee, part       ce qu elle donne ; sur quelle part de la parcelle ( seche ou irriguee ) ; sa part de
                                 la parcelle a Altis ( 30 % irrigue, territoire.IRRIGUE ) - ramenee a l irrigue de l ile
      rendement_t_ha, bornes     le rendement reel moyen avec engrais, et la fourchette reelle ( la porte les verifie )
      sans_engrais, engrais      part du rendement obtenue sans engrais ; dose ( kg de produit par ha ) et jour d apport
      mode                       moisson ( une coupe, h par ha ), cueillette ( murit sur la fenetre, h par tonne ),
                                 coupes ( luzerne ), paturage ( broute sur pied )
      semis, h_semis_ha, semences_kg_ha   fenetre de semis ou de plantation ( jours de l an )
      recolte, h_recolte         fenetre de recolte
      sensibilite                ( debut, fin, poids ) : quand le temps fait le rendement ( le rendement climatique du
                                 territoire, pondere, entre dans la recolte attendue a l ouverture de la fenetre )
      suit_le_jour               une cueillette continue ( legumes, fruits ) murit aussi selon le temps du jour meme
      pourrit                    part du murissant non cueilli perdue chaque jour
      taille, h_taille_ha, bois_t_ha   la taille d hiver et le bois qu elle donne"""
    __slots__ = ("nom", "bien", "irriguee", "part", "rendement_t_ha", "bornes", "source", "sans_engrais", "dose_engrais",
                 "jour_engrais", "mode", "semis", "h_semis_ha", "semences_kg_ha", "recolte", "h_recolte", "sensibilite",
                 "suit_le_jour", "pourrit", "taille", "h_taille_ha", "bois_t_ha")

    def __init__(self, nom, bien, irriguee, part, rendement_t_ha, bornes, source, sans_engrais, mode, recolte, h_recolte,
                 sensibilite, dose_engrais=0.0, jour_engrais=None, semis=None, h_semis_ha=0.0, semences_kg_ha=0.0,
                 suit_le_jour=False, pourrit=0.0, taille=None, h_taille_ha=0.0, bois_t_ha=0.0):
        if bien is not None and bien not in BIENS: raise ValueError(f"{nom} : bien inconnu {bien!r}")
        if not 0.0 < part < 1.0 or not 0.0 < rendement_t_ha < 200.0 or not bornes[0] <= rendement_t_ha <= bornes[1]:
            raise ValueError(f"{nom} : part ou rendement hors bornes")
        if not 0.0 < sans_engrais <= 1.0 or not 0.0 <= pourrit < 1.0 or mode not in ("moisson", "cueillette", "coupes", "paturage"):
            raise ValueError(f"{nom} : parametres hors bornes")
        for a, b, _ in sensibilite:
            if not (0 <= a < JOURS_AN and 0 <= b < JOURS_AN): raise ValueError(f"{nom} : fenetre hors de l annee")
        self.nom, self.bien, self.irriguee, self.part = nom, bien, irriguee, part
        self.rendement_t_ha, self.bornes, self.source, self.sans_engrais = rendement_t_ha, bornes, source, sans_engrais
        self.dose_engrais, self.jour_engrais, self.mode, self.semis = dose_engrais, jour_engrais, mode, semis
        self.h_semis_ha, self.semences_kg_ha, self.recolte, self.h_recolte = h_semis_ha, semences_kg_ha, recolte, h_recolte
        self.sensibilite, self.suit_le_jour, self.pourrit = tuple(sensibilite), suit_le_jour, pourrit
        self.taille, self.h_taille_ha, self.bois_t_ha = taille, h_taille_ha, bois_t_ha


CULTURES = (
    Culture("ble", "cereales", False, 0.30, 2.7, (2.3, 3.2),
            "ble dur, Grece : 2,5 a 3,0 t/ha ( FAOSTAT et ELSTAT 2015-2022 ) ; semis de novembre, moisson de juin ( Lemnos ) ; "
            "sans engrais : 55 a 75 % dans les essais mediterraneens en sec ( a calibrer )",
            0.65, "moisson", (_j(6, 15), _j(7, 15)), 2.5,
            ((_j(11, 1), _j(2, 28), 0.3), (_j(3, 1), _j(5, 31), 1.0), (_j(6, 1), _j(6, 14), 0.5)),
            dose_engrais=300.0, jour_engrais=_j(2, 1), semis=(_j(11, 1), _j(12, 10)), h_semis_ha=3.0,
            semences_kg_ha=200.0),
    Culture("vesce_avoine", "fourrage", False, 0.12, 4.5, (3.0, 7.0),
            "foin de vesce-avoine en sec, Grece : 4 a 6 t/ha ( a calibrer ) ; fauche de mai ; une legumineuse fixe l azote",
            0.95, "moisson", (_j(5, 1), _j(5, 31)), 4.0,
            ((_j(11, 1), _j(2, 28), 0.3), (_j(3, 1), _j(4, 30), 1.0)),
            semis=(_j(11, 1), _j(12, 10)), h_semis_ha=3.0, semences_kg_ha=120.0),
    Culture("olivier", "olives", False, 0.18, 2.3, (1.8, 3.2),
            "olives a huile, Grece : 2 a 3 t/ha ( FAOSTAT 2010-2020 ) ; recolte de novembre a janvier au filet ( 40 a 65 h "
            "par tonne ) ; alternance +/- 25 % ; taille de fevrier-mars, 1 a 3 t de bois par ha ( a calibrer )",
            0.85, "cueillette", (_j(11, 1), _j(1, 31)), 45.0,
            ((_j(4, 1), _j(6, 20), 1.0), (_j(6, 21), _j(10, 31), 0.6)),
            dose_engrais=200.0, jour_engrais=_j(2, 15), pourrit=0.03, taille=(_j(2, 1), _j(3, 31)), h_taille_ha=20.0,
            bois_t_ha=1.5),
    Culture("legumes_ete", "legumes", True, 0.03, 30.0, (20.0, 60.0),
            "legumes d ete irrigues, Grece : tomate de plein champ ~55 t/ha, courgette et poivron ~25, pomme de terre ~25 "
            "( FAOSTAT ) - melange a calibrer ; repiquage d avril-mai, cueillette de fin juin a septembre ( 20 a 35 h/t )",
            0.70, "cueillette", (_j(6, 20), _j(9, 30)), 30.0, ((_j(4, 15), _j(6, 19), 1.0),),
            dose_engrais=800.0, jour_engrais=_j(4, 15), semis=(_j(4, 15), _j(5, 15)), h_semis_ha=150.0,
            suit_le_jour=True, pourrit=0.30),
    Culture("vergers", "fruits", True, 0.07, 18.0, (12.0, 25.0),
            "vergers irrigues, Grece : peche 20-25 t/ha, abricot ~12, raisin de table 15-20 ( FAOSTAT ) - melange a "
            "calibrer ; cueillette de juin a mi-octobre ( ~40 h/t ) ; taille d hiver, ~2 t de bois par ha",
            0.85, "cueillette", (_j(6, 1), _j(10, 15)), 40.0, ((_j(3, 1), _j(5, 31), 1.0),),
            dose_engrais=400.0, jour_engrais=_j(3, 1), suit_le_jour=True, pourrit=0.30, taille=(_j(1, 5), _j(2, 28)),
            h_taille_ha=60.0, bois_t_ha=2.0),
    Culture("luzerne", "fourrage", True, 0.20, 12.0, (8.0, 16.0),
            "luzerne irriguee, Grece : 10 a 15 t de foin par ha et par an en 5 a 7 coupes ( ELSTAT, a calibrer ) ; "
            "legumineuse : pas d engrais azote", 1.0, "coupes", (_j(4, 15), _j(10, 15)), 4.0, ()),
    Culture("jachere_paturage", None, False, 0.10, 1.5, (0.5, 3.0),
            "parcours et jacheres de l Egee : 1 a 2 t de matiere seche par ha et par an, pousse de novembre a mai ( a calibrer )",
            1.0, "paturage", (0, JOURS_AN - 1), 0.0, ()),
)
NC = len(CULTURES)
IC = {c.nom: k for k, c in enumerate(CULTURES)}
ORDRE_RECOLTE = tuple(IC[n] for n in ("legumes_ete", "vergers", "olivier", "ble", "vesce_avoine", "luzerne"))
PART_SEC_ALTIS, PART_IRR_ALTIS = 0.70, 0.30
COUPES_LUZERNE = tuple(_j(4, 15) + 35 * k for k in range(6))     # 15 avril, 20 mai, 24 juin, 29 juillet, 2 sept., 7 oct.
FENETRE_COUPE_J = 10
ALTERNANCE_OLIVE = 0.25
GRACE_MOISSON_J = 10          # au-dela de 10 jours de retard, le grain s egrene et verse
PERTE_MOISSON_J = 0.005       # 0,5 % du restant par jour de retard ( a calibrer )
PATURE_MOIS = (0.06, 0.10, 0.18, 0.22, 0.14, 0.03, 0.0, 0.0, 0.01, 0.06, 0.10, 0.10)   # pousse de l herbe ( a calibrer )
PATURE_JOUR = np.repeat(np.array(PATURE_MOIS) / TER.MOIS_J, TER.MOIS_J)
DECLIN_PATURE = 0.01          # l herbe sur pied qui n est pas broutee seche et se perd
CHAUMES_KG_HA = 600.0         # chaumes et grain tombe apres la moisson, broutes jusqu aux labours ( a calibrer )
DECLIN_CHAUMES = 0.003
LABOURS = _j(11, 1)
# L irrigation : saison de chaque culture irriguee ( la parcelle irriguee du territoire est un seul reservoir de sol )
SAISON_IRRIGATION = {"legumes_ete": (_j(4, 15), _j(9, 30)), "vergers": (_j(3, 1), _j(10, 15)), "luzerne": (_j(3, 1), _j(10, 31))}

# ================================================================== l elevage
class Espece:
    """Un petit ruminant laitier grec.
      part                  part des tetes du troupeau ( Grece : ~8,5 M de moutons, ~3,5 M de chevres ; Lemnos, surtout
                            des brebis - a calibrer )
      lait_kg               lait trait par femelle et par lactation ( apres le sevrage des jeunes )
      prolificite, fertilite    jeunes par mise-bas, part des femelles qui mettent bas
      carcasse_*            kg de carcasse d un jeune de lait ( 40 a 60 jours ) et d une adulte reformee
      reforme_an, mortalite_an, mortalite_jeune   renouvellement et pertes"""
    __slots__ = ("nom", "part", "lait_kg", "prolificite", "fertilite", "carcasse_jeune_kg", "carcasse_reforme_kg",
                 "reforme_an", "mortalite_an", "mortalite_jeune", "arma", "arma_preuve", "source")

    def __init__(self, nom, part, lait_kg, prolificite, fertilite, carcasse_jeune_kg, carcasse_reforme_kg, reforme_an,
                 mortalite_an, mortalite_jeune, arma, source):
        if not (0 < part <= 1 and 0 < lait_kg < 1000 and 0.5 <= prolificite <= 3 and 0 < fertilite <= 1
                and 0 < carcasse_jeune_kg < carcasse_reforme_kg < 60 and 0 <= reforme_an < 1 and 0 <= mortalite_an < 1
                and 0 <= mortalite_jeune < 1):
            raise ValueError(f"espece {nom} hors bornes")
        self.nom, self.part, self.lait_kg, self.prolificite, self.fertilite = nom, part, lait_kg, prolificite, fertilite
        self.carcasse_jeune_kg, self.carcasse_reforme_kg = carcasse_jeune_kg, carcasse_reforme_kg
        self.reforme_an, self.mortalite_an, self.mortalite_jeune = reforme_an, mortalite_an, mortalite_jeune
        self.arma, self.arma_preuve, self.source = arma, None, source


ESPECES = (
    Espece("brebis", 0.65, 130.0, 1.3, 0.90, 9.0, 22.0, 0.20, 0.04, 0.10, "Sheep_random_F",
           "races laitieres grecques ( Lesvos, Chios, Karagouniki ) : 100 a 140 kg de lait trait par lactation ; agneau de "
           "lait de 40 a 50 jours, 8 a 10 kg de carcasse ; reforme ~20 %/an ( a calibrer sur ELSTAT )"),
    Espece("chevre", 0.35, 150.0, 1.5, 0.90, 7.0, 20.0, 0.20, 0.05, 0.12, "Goat_random_F",
           "chevre grecque locale : 120 a 180 kg de lait par lactation ; chevreau de lait ~7 kg de carcasse ( a calibrer )"),
)
NE = len(ESPECES)
FEMELLES = 0.95               # un male pour une vingtaine de femelles
MISE_BAS = (_j(11, 15), _j(1, 15))            # agnelages d automne et d hiver
N_MISE_BAS = _longueur(*MISE_BAS)
SEVRAGE_J = 50                # l agneau de lait est abattu ( ou garde pour le renouvellement ) a ~50 jours
REFORME = (_j(7, 1), _j(8, 31))              # reformes apres la lactation
N_REFORME = _longueur(*REFORME)
RECRUES_JOUR = _j(7, 1)       # les agnelles de l hiver entrent au troupeau adulte
TRAITE = (_j(1, 15), _j(3, 15), _j(7, 31))   # debut, pic, fin de la traite ( moyenne du troupeau )
MS_LACTATION, MS_TARIE, MS_JEUNE = 2.2, 1.5, 0.6   # kg de matiere seche par tete et par jour ( a calibrer, INRA )
H_TRAITE, H_HORS_TRAITE = 0.05, 0.015           # heures de soins par tete et par jour ( traite a la main ~1,5 min/brebis )
H_ASTREINTE_MAX = 2.5         # un paysan donne au plus 2,5 h un jour de repos : traite du matin et du soir, affouragement
DISETTE = 0.6                 # sous 60 % de sa ration pendant 20 jours, le troupeau commence a mourir
JOURS_DISETTE = 20
MORT_DISETTE_J = 0.005
CHARGE_FOURRAGE = 0.85        # le troupeau est dimensionne a 85 % du fourrage d une annee normale
MS_AN_TETE = 750.0            # kg de matiere seche par tete adulte et par an, jeunes compris ( a calibrer )


def _courbe_traite():
    """La part du lait d une lactation trait chaque jour de l an : un triangle du 15 janvier au 31 juillet, pic mi-mars
    ( agnelages de novembre a janvier, sevrage a ~45 jours ) ; somme 1."""
    d0, pic, d1 = TRAITE
    x = np.arange(JOURS_AN, dtype=float)
    c = np.where((x >= d0) & (x <= pic), (x - d0) / (pic - d0), 0.0)
    c = np.where((x > pic) & (x <= d1), (d1 - x) / (d1 - pic), c)
    return c / c.sum()


COURBE_TRAITE = _courbe_traite()

# ================================================================== la peche
VENT_MAX_PECHE = 8.0          # m/s : force 5 Beaufort, un caique de 8 a 10 m reste au port ( a calibrer )
PRISE_KG = 13.0               # kg par sortie : flotte cotiere grecque ~3 t par bateau et par an ( a calibrer ) ; nos pecheurs
                              # sortent chaque jour ouvre ou la mer le permet ( ~230 sorties par an ), un pecheur grec ~170
SIGMA_PRISE = 0.5
SAISON_PECHE = (0.7, 0.7, 0.9, 1.2, 1.3, 1.1, 0.9, 0.8, 1.1, 1.3, 1.1, 0.8)   # par mois ( printemps et automne ), a calibrer
EQUIPAGE, H_SORTIE = 2, 6.0
COTE_KM = 2.5                 # un village a moins de 2,5 km d un repere cotier ( cap, ilot, jetee, phare ) a son caique
MODELE_BATEAU = "caique_de_peche"

# ================================================================== la ration et la vente
CIBLE_MARCHE_J = 3.5          # jours de besoin au marche et en attente de camion a 15 h 50 : ~3 au marche, dont 2 restent
                              # a l aube apres les achats du soir ( la couverture que vise l economie, COUVERTURE_CIBLE_J ),
                              # et ~0,5 en attente de camion ; au-dela de 3 jours au marche, le moteur exporte le surplus
TAU_LIVRAISON_J = 2.0         # un ecart a la couverture visee se comble en deux jours ( sinon les fermes, qui voient le
                              # meme marche, livrent toutes ensemble un jour sur deux : camions de 30 unites au moins )
CAPACITE_RATIONS = 4.0        # un atelier de village fait au plus 4 fois sa part du besoin de sa region par jour
H_RATION = 0.04               # heures de four, de fromagerie, de moulin et d emballage par ration ( a calibrer )
TAMPON_FARINE_J = 3
MARGE_SOUDURE = 1.25
SOUDURE_EN_PLUS_J = 30        # la fenetre de recolte elle-meme
GARDE_TEMOIN_J = 3
ALPHA_USAGE = 1.0 / 30.0
PEREMPTION_HORIZON_J = 30
HORIZON_VENTE = 14            # un grenier vendu se voit en une semaine : 3 jours gardes, 3 jours de farine, puis plus rien a
                              # livrer ; deux semaines lisent la rupture et ce qu elle coute ( pas le soir meme )
JOUR_DECISION = 1             # tous les 7 jours, toutes les fermes le meme jour, le lendemain de la moisson du 15 juin
K_FAIM = 4.0
LAMBDA_REVENU = 0.1
ACTIONS_VENTE = ("stocker", "vendre_surplus", "vendre_tout")
ILES_CALENDRIER = ("Altis", "Stratis", "Malden")   # le calendrier de l Egee ; ailleurs, les fermes restent au moteur


# ================================================================== l etat
class Exploitation:
    """Une ferme du moteur, reprise par le domaine.
      stock, lots          le grenier ( un Stock du socle ) et ses lots dates : { id de bien : deque de [ jour, kg ] }
      paysans              les paysans de la ferme ( index du moteur, relu chaque matin )
      presence_h           heures de presence au poste de travail DANS la ferme depuis minuit ( agenda ou moteur ) ;
                           presents_max : le plus de paysans presents ensemble ce jour ( l equipage du caique )
      astreinte_h          heures de soins donnees un jour de repos
      part                 part de la ferme dans les surfaces agricoles de sa region : sa part du besoin ;
                           valeur_ref : cette part du besoin de sa region a l installation, au prix mondial de la ration
                           ( drachmes par jour ) - l unite fixe de son revenu dans la note ( une region que la faim vide
                           par migration ne doit pas diviser par zero )
      cible_j, livre_j     rations visees et faites aujourd hui ; ref_j : sa part equitable ( surface ) de ce que sa
                           region demandait aujourd hui - la mesure de ce qu elle devait ; revenu_j : ce que sa caisse a
                           recu depuis la paie ; frais_j : dont la vente du frais au negoce ( que la decision ne touche pas )
      usage_ema            kg par jour de cereales, d huile et de fromage passes dans ses rations ( moyenne sur 30 j )
      sequestre            grenier sous sequestre ( saisie, quarantaine sanitaire ) : rien n y entre ni n en sort, il perit"""
    __slots__ = ("id", "ferme", "lieu", "marche_id", "k", "surface_ha", "irrigue", "cotiere", "stock", "lots",
                 "paysans", "presence_h", "presents_max", "astreinte_h", "soins_besoin_h", "soins_faits_h", "atelier_besoin_h",
                 "caisse_ref", "revenu_j",
                 "livre_j", "cible_j", "ref_j", "frais_j", "part", "valeur_ref", "sequestre", "bateau", "phase_olive",
                 "usage_ema")

    def __init__(self, ferme, k, surface_ha, irrigue, cotiere, stock):
        if not surface_ha > 0 or not 0.0 <= irrigue <= 1.0: raise ValueError(f"{ferme.id} : surface ou irrigue hors bornes")
        self.id, self.ferme, self.lieu, self.marche_id = ferme.id, ferme, ferme.lieu, ferme.lieu.marche.id
        self.k, self.surface_ha, self.irrigue, self.cotiere, self.stock = k, float(surface_ha), float(irrigue), cotiere, stock
        self.lots = {}
        self.paysans = []
        self.presence_h = self.astreinte_h = self.soins_besoin_h = self.soins_faits_h = self.atelier_besoin_h = 0.0
        self.presents_max = 0
        self.caisse_ref = ferme.caisse
        self.revenu_j = self.livre_j = self.cible_j = self.ref_j = self.frais_j = 0.0
        self.part = 0.0
        self.valeur_ref = 1.0
        self.sequestre = False
        self.bateau = None
        self.phase_olive = 0
        self.usage_ema = {b: 0.0 for b in STOCKABLES}


class Champs:
    """Les cultures de toutes les fermes, en tableaux ( culture, ferme ).
      surface            ha de la culture sur la parcelle ; campagne_ha : ha en place pour la campagne en cours
      a_semer            ha restant a semer ou planter dans la fenetre ; taille : ha restant a tailler
      acc_w, acc_wf      poids et poids x rendement climatique accumules sur la campagne
      attendu            kg attendus a l ouverture de la recolte ( cueillette : sur la fenetre entiere, climat du jour a part )
      restant            ha restant a moissonner ; backlog : kg murs non cueillis
      recolte, perdu     kg de la campagne ; fraction : part de la fenetre de cueillette vecue par le monde
      engrais            1 si l engrais a ete apporte a la campagne ; ouvert : 1 pendant la fenetre de recolte
      campagnes          les campagnes closes : ( jour, ferme, culture, ha, kg recoltes, kg perdus, fraction, climat, engrais )"""
    __slots__ = ("surface", "campagne_ha", "a_semer", "taille", "acc_w", "acc_wf", "attendu", "restant", "backlog",
                 "recolte", "perdu", "fraction", "engrais", "ouvert", "ouvert_j", "climat", "campagnes")

    def __init__(self, nf):
        for k in ("surface", "campagne_ha", "a_semer", "taille", "acc_w", "acc_wf", "attendu", "restant", "backlog",
                  "recolte", "perdu", "fraction", "climat"):
            setattr(self, k, np.zeros((NC, nf)))
        self.engrais = np.zeros((NC, nf), np.int8)
        self.ouvert = np.zeros((NC, nf), np.int8)
        self.ouvert_j = np.zeros((NC, nf), np.int64)
        self.campagnes = []


class Troupeaux:
    """Les troupeaux, en tableaux ( ferme, espece ).
      adultes, recrues    tetes adultes ; agnelles et chevrettes gardees pour le renouvellement ( adultes au 1er juillet )
      naissances          ( ferme, espece, 50 ) les jeunes nes chacun des 50 derniers jours ( rang : jour % 50 )
      reforme_du_jour     les adultes a reformer chaque jour de la fenetre de reforme ( fixe au 1er juillet )
      paturage, chaumes   kg de matiere seche sur pied par ferme ; alimentation : part de la ration servie ( moyenne
                          sur 7 jours ) ; jours_disette ; cumuls du bilan du cheptel ( depart, nes, abattus, morts )"""
    __slots__ = ("adultes", "recrues", "naissances", "reforme_du_jour", "paturage", "chaumes", "alimentation",
                 "jours_disette", "depart", "nes", "abattus", "morts", "lait_j")

    def __init__(self, nf):
        self.adultes = np.zeros((nf, NE)); self.recrues = np.zeros((nf, NE))
        self.naissances = np.zeros((nf, NE, SEVRAGE_J)); self.reforme_du_jour = np.zeros((nf, NE))
        self.paturage = np.zeros(nf); self.chaumes = np.zeros(nf)
        self.alimentation = np.ones(nf); self.jours_disette = np.zeros(nf, np.int64)
        self.depart = 0.0; self.nes = self.abattus = self.morts = 0.0
        self.lait_j = np.zeros(nf)


class Agriculture:
    """L etat du domaine."""
    __slots__ = ("liste", "par_id", "par_marche", "ids", "champs", "troupeaux", "decideur", "critere", "jour_nuit",
                 "fs", "fi", "fi35", "flux_motif", "rations", "composition", "sinistres", "ventes", "serie")

    def __init__(self):
        self.liste = []           # les Exploitation, dans l ordre des identifiants de ferme
        self.par_id = {}          # id de ferme -> Exploitation
        self.par_marche = {}      # id de marche -> [ rang ]
        self.ids = {}             # nom de bien -> identifiant du catalogue
        self.champs = self.troupeaux = self.decideur = None
        self.critere = "poste"    # qui compte au travail : « poste » ( ce domaine ) ou « lieu_e1 » ( le moteur, falsificateur )
        self.jour_nuit = None
        self.fs = self.fi = self.fi35 = None
        self.flux_motif = {}      # ( nature, motif, bien ) -> kg, cumul des jours clos : lu dans le grand livre
        self.rations = 0.0        # rations faites depuis l installation
        self.composition = {}     # marche -> deque de 7 jours de kcal par composante livres a la region
        self.sinistres = deque(maxlen=2000)    # ( jour, ferme, culture, cause, kg ) : les pertes ( assurance recolte )
        self.ventes = {}          # ferme -> { bien : kg vendus au negoce aujourd hui }
        self.serie = deque(maxlen=800)         # ( jour, rations, menages sans repas, kcal stockables, astreinte h,
                                               # presence h, demande solvable non servie, ventes cumulees, besoin, grain )


# ================================================================== le grenier : lots dates
def _lot_ajouter(ex, b, q, jour):
    dq = ex.lots.get(b)
    if dq is None: dq = ex.lots[b] = deque()
    if dq and dq[-1][0] == jour: dq[-1][1] += q
    else: dq.append([jour, q])


def _lot_retirer(ex, b, q):
    """Premier entre, premier sorti : on mange, vend ou transforme d abord ce qui perira d abord."""
    dq = ex.lots.get(b)
    if not dq: return
    while q > 0.0 and dq:
        lot = dq[0]
        if lot[1] <= q:
            q -= lot[1]; dq.popleft()
        else:
            lot[1] -= q; q = 0.0
    if ex.stock[b] <= 0.0: dq.clear()


def _entrer(p, A, ex, nom, q, motif, jour=None, nature="produit"):
    """Une source dans le grenier : produit ( recolte, traite, transformation ) ; le lot est date du jour."""
    if not q > 0.0: return 0.0
    b = A.ids[nom]
    p.socle.livre.source(ex.stock, b, q, nature, motif)
    _lot_ajouter(ex, b, q, p.jour if jour is None else jour)
    return q


def _sortir(p, A, ex, nom, q, nature, motif):
    """Un puits depuis le grenier ( consomme, perime, exporte ) : les plus vieux lots d abord. Rend ce qui est sorti."""
    if not q > 0.0: return 0.0
    b = A.ids[nom]
    pris = p.socle.livre.puits(ex.stock, b, q, nature, motif)
    _lot_retirer(ex, b, pris)
    return pris


def _q(A, ex, nom): return ex.stock[A.ids[nom]]


def _transformer(p, A, ex, recette, q):
    """Transforme q kg de l entree selon la recette. Rend les kg d entree transformes."""
    pris = _sortir(p, A, ex, recette.entree, q, "consomme", recette.nom)
    for b, k in recette.sorties.items(): _entrer(p, A, ex, b, pris * k, recette.nom)
    return pris


def _vendre(p, A, ex, nom, q):
    """Vend au negoce ( exportation ) : le bien sort du pays, l exterieur paie la caisse de la ferme."""
    pris = _sortir(p, A, ex, nom, q, "exporte", "vente_negoce")
    if pris <= 0.0: return 0.0
    montant = pris * p.socle.catalogue[nom].prix_monde * PARITE_NEGOCE
    p.socle.livre.recevoir_de_l_exterieur(ex.ferme, montant, "vente_negoce")
    if nom not in STOCKABLES: ex.frais_j += montant
    v = A.ventes.setdefault(ex.id, {})
    v[nom] = v.get(nom, 0.0) + pris
    p.compter("vente_negoce", montant)
    return pris


def _perimer(p, A):
    """Chaque lot perit en entier le jour ou son age atteint la conservation du catalogue."""
    cat = p.socle.catalogue; j = p.jour
    for ex in A.liste:
        for b, dq in ex.lots.items():
            cj = cat[b].conservation_j
            if math.isinf(cj): continue
            q = 0.0
            while dq and j - dq[0][0] >= cj:
                q += dq.popleft()[1]
            if q > 0.0:
                pris = p.socle.livre.perimer(ex.stock, b, min(q, ex.stock[b]), "peremption")
                if ex.stock[b] <= 0.0: dq.clear()
                p.compter("peremption_agricole", pris)


def ecarts_lots(p):
    """Pour chaque exploitation et chaque bien : stock - somme des lots ( zero, a l arrondi pres )."""
    A = p.domaine("agriculture"); out = []
    for ex in A.liste:
        for b, q in ex.stock.items():
            s = math.fsum(l[1] for l in ex.lots.get(b, ()))
            if abs(s - q) > 1e-9 * max(1.0, abs(q)): out.append((ex.id, p.socle.catalogue[b].nom, q, s))
        for b, dq in ex.lots.items():
            if dq and b not in ex.stock: out.append((ex.id, p.socle.catalogue[b].nom, 0.0, math.fsum(l[1] for l in dq)))
    return out


# ================================================================== le rendement climatique, sec et irrigue
def facteurs_climatiques(p):
    """Le rendement climatique du jour de chaque parcelle, SEPARE pour la part seche et la part irriguee : la formule du
    territoire ( ETR sur ETM des 30 derniers jours rapportee a sa normale, reponse Ky de la FAO, chaleur, crues ), sans
    la moyenne ponderee qui melangeait les deux. Rend ( sec, irrigue ), des tableaux par parcelle."""
    T = p.domaine("territoire"); P, N = T.parcelles, T.normales
    d = T.doy
    i, s = P.ile, P.sol

    def rel(eta, etm, ne, nm):
        r = np.divide(eta, etm, out=np.ones_like(eta), where=etm > 1e-9)
        rn = np.divide(ne, nm, out=np.ones_like(ne), where=nm > 1e-9)
        return np.clip(r / np.maximum(rn, 1e-3), 0.0, TER.Q_MAX)

    commun = np.clip(1.0 - TER.K_CHALEUR * T.etat.chaleur[i], 0.0, 1.0) * np.where(P.inond_fin >= p.jour, P.inond_facteur, 1.0)
    fs = np.clip(1.0 - TER.KY * (1.0 - rel(P.eta_sec, P.etm_sec, N.eta_sec[i, s, d], N.etm_sec[i, s, d])), 0.0, TER.F_MAX)
    fi = np.clip(1.0 - TER.KY * (1.0 - rel(P.eta_irr, P.etm_irr, N.eta_irr[i, s, d], N.etm_irr[i, s, d])), 0.0, TER.F_MAX)
    return fs * commun, fi * commun


# ================================================================== la nuit ( 0 h 10, apres le territoire )
def _nuit(p):
    A = p.domaine("agriculture")
    if A.jour_nuit == p.jour: return
    A.jour_nuit = p.jour
    d = _doy(p)
    for ex in A.liste:
        ex.presence_h = ex.astreinte_h = ex.soins_besoin_h = ex.soins_faits_h = ex.atelier_besoin_h = 0.0
        ex.presents_max = 0
        ex.livre_j = ex.cible_j = ex.ref_j = ex.frais_j = 0.0
    A.ventes = {}
    _climat_du_jour(p, A)
    _accumuler(A, d)
    _fenetres(p, A, d)
    _irriguer(p, A, d)
    _paturages(A, d)
    _perimer(p, A)


def _climat_du_jour(p, A):
    fs, fi = facteurs_climatiques(p)
    k = np.array([ex.k for ex in A.liste], np.int64)
    A.fs, A.fi = fs[k], fi[k]
    A.fi35 = A.fi35 + (A.fi - A.fi35) / 35.0


def _accumuler(A, d):
    """Le temps du jour entre dans le rendement des cultures qui sont dans une periode ou il compte."""
    ch = A.champs
    for c, cu in enumerate(CULTURES):
        f = A.fi if cu.irriguee else A.fs
        for a, b, poids in cu.sensibilite:
            if _dans(d, a, b):
                ch.acc_w[c] += poids; ch.acc_wf[c] += poids * f


def _climat_campagne(ch, c):
    return np.divide(ch.acc_wf[c], ch.acc_w[c], out=np.ones_like(ch.acc_w[c]), where=ch.acc_w[c] > 0)


def _facteur_engrais(ch, c):
    return np.where(ch.engrais[c] > 0, 1.0, CULTURES[c].sans_engrais)


def _alternance(p, A):
    an = p.socle.calendrier.date(p.pas).year
    return np.array([1.0 + ALTERNANCE_OLIVE * (1 if (an + ex.phase_olive) % 2 == 0 else -1) for ex in A.liste])


def _ouvrir(p, A, c, d, fraction=1.0):
    """La fenetre de recolte s ouvre : la recolte attendue est fixee sur le climat accumule de la campagne."""
    ch = A.champs; cu = CULTURES[c]
    base = cu.rendement_t_ha * 1000.0 * ch.campagne_ha[c] * _facteur_engrais(ch, c)
    if cu.nom == "olivier": base = base * _alternance(p, A)
    clim = _climat_campagne(ch, c)
    ch.climat[c] = clim
    ch.attendu[c] = base * clim               # cueillette : le climat du jour joue en plus pour les legumes et les fruits
    if cu.mode == "moisson": ch.restant[c] = ch.campagne_ha[c]
    else: ch.backlog[c] = 0.0
    ch.recolte[c] = 0.0; ch.perdu[c] = 0.0
    ch.fraction[c] = fraction
    ch.ouvert[c] = 1; ch.ouvert_j[c] = p.jour


def _clore(p, A, c, f=None):
    """La fenetre de recolte se ferme : ce qui reste sur pied est perdu, la campagne est enregistree."""
    ch = A.champs; cu = CULTURES[c]
    fermes = range(len(A.liste)) if f is None else (f,)
    for g in fermes:
        if not ch.ouvert[c, g]: continue
        reste = ch.backlog[c, g] if cu.mode == "cueillette" else ch.restant[c, g] * _kg_ha(ch, c, g)
        if reste > 0:
            ch.perdu[c, g] += reste
            A.sinistres.append((p.jour, A.liste[g].id, cu.nom, "non_recolte", reste))
            p.compter("perte_recolte", reste)
        ch.backlog[c, g] = 0.0; ch.restant[c, g] = 0.0
        ch.ouvert[c, g] = 0
        ex = A.liste[g]
        ha = ch.campagne_ha[c, g]
        if ha > 0:
            ch.campagnes.append((p.jour, g, c, ha, ch.recolte[c, g], ch.perdu[c, g], ch.fraction[c, g],
                                 ch.climat[c, g], int(ch.engrais[c, g])))
            p.noter("recolte", ferme=ex.id, culture=cu.nom, kg=round(float(ch.recolte[c, g]), 1), surface_ha=round(float(ha), 2),
                    rendement_t_ha=round(float(ch.recolte[c, g] / ha / 1000.0 / max(ch.fraction[c, g], 1e-9)), 3))
        if cu.mode != "coupes":
            ch.acc_w[c, g] = 0.0; ch.acc_wf[c, g] = 0.0
            if cu.semis is None: ch.engrais[c, g] = 0      # culture perenne : la campagne suivante commence


def _kg_ha(ch, c, g):
    return ch.attendu[c, g] / ch.campagne_ha[c, g] if ch.campagne_ha[c, g] > 0 else 0.0


def _fenetres(p, A, d):
    """Ouvertures et fermetures du calendrier : semis, recoltes, coupes de luzerne, labours, taille, engrais."""
    ch = A.champs
    for c, cu in enumerate(CULTURES):
        if cu.mode == "paturage": continue
        if cu.mode == "coupes":
            if d in COUPES_LUZERNE:
                _clore(p, A, c)
                ch.campagne_ha[c] = ch.surface[c]
                base = cu.rendement_t_ha * 1000.0 / len(COUPES_LUZERNE) * ch.campagne_ha[c] * _facteur_engrais(ch, c)
                ch.attendu[c] = base * A.fi35; ch.climat[c] = A.fi35
                ch.restant[c] = ch.campagne_ha[c]; ch.recolte[c] = 0.0; ch.perdu[c] = 0.0; ch.fraction[c] = 1.0
                ch.ouvert[c] = 1; ch.ouvert_j[c] = p.jour
            elif any(_ecoule(x, d) == FENETRE_COUPE_J for x in COUPES_LUZERNE):
                _clore(p, A, c)
            continue
        a, b = cu.recolte
        if d == a:
            _ouvrir(p, A, c, d)
        elif d == (b + 1) % JOURS_AN:
            _clore(p, A, c)
        if cu.semis is not None and d == cu.semis[0]:
            ch.a_semer[c] = ch.surface[c]; ch.campagne_ha[c] = 0.0
            ch.acc_w[c] = 0.0; ch.acc_wf[c] = 0.0; ch.engrais[c] = 0
        if cu.semis is not None and d == (cu.semis[1] + 1) % JOURS_AN:
            for g in np.nonzero(ch.a_semer[c] > 0)[0].tolist():
                A.sinistres.append((p.jour, A.liste[g].id, cu.nom, "non_seme", float(ch.a_semer[c, g])))
            ch.a_semer[c] = 0.0
        if cu.taille is not None and d == cu.taille[0]: ch.taille[c] = ch.surface[c]
        if cu.taille is not None and d == (cu.taille[1] + 1) % JOURS_AN: ch.taille[c] = 0.0
        if cu.jour_engrais is not None and d == cu.jour_engrais: _fertiliser(p, A, c)
    if d == LABOURS: A.troupeaux.chaumes[:] = 0.0


def _fertiliser(p, A, c):
    """L apport d engrais du domaine 10, s il existe et s il est dans le grenier ; sinon, la culture fait sans."""
    cu = CULTURES[c]; ch = A.champs
    if "engrais" not in p.socle.catalogue.par_nom: return
    e = p.socle.catalogue.id("engrais")
    for g, ex in enumerate(A.liste):
        ha = ch.surface[c, g] if cu.semis is None else max(ch.campagne_ha[c, g], ch.a_semer[c, g])
        besoin = cu.dose_engrais * ha
        if besoin <= 0 or ex.sequestre or ex.stock[e] < besoin: continue
        p.socle.livre.consommer(ex.stock, e, besoin, "fertiliser")
        ch.engrais[c, g] = 1


def _irriguer(p, A, d):
    """L irrigation reprise au territoire : quand une culture irriguee est dans sa saison, la reserve du sol de la part
    irriguee est remplie a la capacite des qu elle passe sous la moitie ( pilotage FAO-56 ), par un prelevement dans le
    bassin du village ( la restriction du bassin coupe sa part ). L eau recue est versee a la parcelle comme le
    territoire le fait lui-meme ( rendement d application 75 %, bilan des sols tenu )."""
    T = p.domaine("territoire"); P = T.parcelles
    en_saison = [n for n, (a, b) in SAISON_IRRIGATION.items() if _dans(d, a, b)]
    if not en_saison: return
    total = 0.0
    for ex in A.liste:
        k = ex.k
        a_irr = P.surface_ha[k] * P.irrigue[k]
        if a_irr <= 0: continue
        mm = float(TER.besoin_irrigation(P.w_irr[k:k + 1], P.ru[k:k + 1])[0])
        if mm <= 0: continue
        m3 = mm * 10.0 * a_irr / TER.EFFICIENCE
        recu = TER.prelever(p, ex.lieu, m3, "irrigation")
        mmr = recu / (10.0 * a_irr)
        P.w_irr[k] += TER.EFFICIENCE * mmr
        P.c_irr_brut[k] += mmr; P.c_irr_pertes[k] += (1.0 - TER.EFFICIENCE) * mmr
        total += recu
    if total > 0: p.compter("irrigation_agricole", total)


def _paturages(A, d):
    """L herbe pousse sur les jacheres selon la saison et le temps ; herbe et chaumes sur pied se perdent lentement."""
    tr, ch = A.troupeaux, A.champs
    c = IC["jachere_paturage"]
    cu = CULTURES[c]
    tr.paturage = tr.paturage * (1.0 - DECLIN_PATURE) + cu.rendement_t_ha * 1000.0 * ch.surface[c] * PATURE_JOUR[d] * A.fs
    tr.chaumes = tr.chaumes * (1.0 - DECLIN_CHAUMES)


# ================================================================== la presence ( chaque pas )
def _presence(p):
    """Un paysan compte au travail s il est a son POSTE de travail DANS le lieu de sa ferme ( l agenda ou le moteur l y
    mettent ) : un paysan chez lui le dimanche habite le village de sa ferme, il n y travaille pas. `critere = lieu_e1`
    rend le critere de Monde.produire ( dans le lieu, a l heure de son horaire ) : le falsificateur de la porte."""
    A = p.domaine("agriculture")
    e1 = A.critere == "lieu_e1"
    heure = ((p.w.minutes - C.MINUTES_PAR_PAS) % (24 * 60)) / 60.0     # l heure ou Monde.deplacer a pose les postes
    for ex in A.liste:
        n = 0
        lieu = ex.lieu
        for h in ex.paysans:
            if not h.vivant: continue
            if (h.lieu is lieu and h.au_travail(heure)) if e1 else (h.poste == "travail" and h.lieu is lieu):
                n += 1; h.heures_jour += PAS_H
        if n:
            ex.presence_h += n * PAS_H
            if n > ex.presents_max: ex.presents_max = n


def _paysans(p):
    """6 h 20, apres l index du moteur ( aube ) : les paysans de chaque ferme."""
    A = p.domaine("agriculture")
    for ex in A.liste: ex.paysans = [h for h in p.w.au_travail_de(ex.lieu, "paysan") if h.vivant]


# ================================================================== la journee de la ferme ( 15 h 50 )
def _besoin_region(p, mid):
    """Les rations par jour que la region d un marche consomme : ses habitants a la ration du jour ( la loi de
    rationnement s il y en a une ), plus les intrants de nourriture des entreprises de la region ( la pharmacie du
    moteur : 0,5 ration par heure d ouvrier ), a leur activite du jour. PAS la demande enregistree par le marche : le
    moteur y ajoute chaque heure jusqu a 60 unites qu une entreprise voulait sans pouvoir les payer ( monde.py, expedier )
    - la suivre a fait livrer 1 600 rations par jour a Kavala, vider la caisse du marche et arreter ses camions ( 23/09 )."""
    w = p.w
    ration = w.gouv.lois.get("rationnement_nourriture") or C.NOURRITURE_PAR_JOUR
    intrants = 0.0
    for e in w.entreprises.values():
        q = e.intrants.get("nourriture", 0.0)
        if q > 0 and e.lieu.marche.id == mid and e.id not in p.repris:
            intrants += q * 8.0 * e.activite * len(w.au_travail_de(e.lieu, e.role))
    return w._pop_marche.get(mid, 0) * ration + intrants


def _attente_region(A, mid):
    """Les rations des fermes d une region qui attendent leur camion ( le tableau de la cooperative )."""
    return math.fsum(A.liste[g].ferme.stocks["nourriture"] for g in A.par_marche.get(mid, ()))


def _livrable(A, ex):
    """Les rations que le grenier d une ferme peut faire aujourd hui ( le grain moulu, les olives pressees )."""
    kc = [math.fsum(_q(A, ex, b) * KCAL[b] for b in bs) for bs in BIENS_COMPOSANTE]
    kc[0] += _q(A, ex, "cereales") * RECETTES["moudre"].sorties["farine"] * KCAL["farine"]
    kc[1] += _q(A, ex, "olives") * RECETTES["presser"].sorties["huile"] * KCAL["huile"]
    return _rations_possibles(kc)


def _cibles(p, A):
    """Ce que chaque region demande aux fermes aujourd hui, et qui le livre. La demande : ce que la region mange ( plus sa
    faim d hier ), et l ecart entre la couverture visee et ce qu elle a au marche et en attente de camion, comble en deux
    jours - le prix n y entre pas, il dit la faim trop tard. Qui livre : chaque ferme sert sa part equitable ( sa surface
    dans la region ) si son grenier le peut ; ce qu une ferme ne peut pas servir ( elle a tout vendu ) est reparti entre
    celles qui ont encore de quoi, au prorata de leur part, jusqu a ce que leurs greniers ou leurs ateliers ( 4 fois leur
    part ) soient pleins - ses clients vont ailleurs. Rend ( cibles, parts equitables ) par rang de ferme : la part
    equitable est ce que la note compare a la livraison."""
    w = p.w
    n = len(A.liste)
    cibles, refs = [0.0] * n, [0.0] * n
    for mid, gs in A.par_marche.items():
        need = _besoin_region(p, mid)
        if need <= 0: continue
        ecart = CIBLE_MARCHE_J * need - max(0.0, w.marches[mid].stocks["nourriture"]) - _attente_region(A, mid)
        T_r = max(0.0, min(CAPACITE_RATIONS * need, need * (1.0 + w.faim_region.get(mid, 0.0)) + ecart / TAU_LIVRAISON_J))
        gs = [g for g in gs if not A.liste[g].sequestre]
        cap = {g: min(_livrable(A, A.liste[g]), CAPACITE_RATIONS * A.liste[g].part * need) for g in gs}
        for g in gs:
            refs[g] = A.liste[g].part * T_r
            cibles[g] = min(cap[g], refs[g])
        for _ in range(len(gs)):                      # le remplissage : au plus une passe par ferme saturee
            manque = T_r - math.fsum(cibles[g] for g in gs)
            libres = [g for g in gs if cap[g] - cibles[g] > EPS]
            if manque <= EPS or not libres: break
            poids = math.fsum(A.liste[g].part for g in libres)
            for g in libres: cibles[g] = min(cap[g], cibles[g] + manque * A.liste[g].part / poids)
    return cibles, refs


def _journee(p):
    """La journee de travail de chaque ferme, dans l ordre ou une ferme la fait : les betes, les recoltes qui murissent,
    puis l atelier ( les rations de la region ), les travaux des champs, la mer. Les heures sont celles de la presence au
    poste ; un jour de repos, l astreinte soigne et trait les betes ( et le lait du jour part en feta ), rien d autre :
    ni recolte, ni mer, ni rations - un jour de repos, aucun camion ne partirait les porter ( les convoyeurs aussi se
    reposent ). Deux passes : les recoltes de toutes les fermes d abord, pour que le marche sache qui peut livrer."""
    A = p.domaine("agriculture"); d = _doy(p)
    reste = [0.0] * len(A.liste)
    for f, ex in enumerate(A.liste):
        if ex.sequestre: continue
        H = ex.presence_h
        besoin_e = _besoin_soins(A, f, d)
        fait_e = min(H, besoin_e); H -= fait_e
        if besoin_e - fait_e > EPS: fait_e += _astreinte(p, ex, besoin_e - fait_e)
        ex.soins_besoin_h, ex.soins_faits_h = besoin_e, fait_e
        reste[f] = _recoltes(p, A, f, ex, d, H)
        _troupeau(p, A, f, ex, d, fait_e / besoin_e if besoin_e > 0 else 1.0)
    cibles, refs = _cibles(p, A)
    for f, ex in enumerate(A.liste):
        if ex.sequestre: continue
        H = reste[f]
        ex.cible_j, ex.ref_j = cible, _ = cibles[f], refs[f]
        besoin_a = cible * H_RATION
        fait_a = min(H, besoin_a); H -= fait_a
        ex.atelier_besoin_h = besoin_a
        _atelier(p, A, f, ex, cible if besoin_a <= 0 else cible * fait_a / besoin_a)
        H = _operations(p, A, f, ex, d, H)
        _peche(p, A, f, ex, d, H)


def _astreinte(p, ex, heures):
    """Un jour de repos ( ou quand la presence ne suffit pas ), les paysans de la ferme qui sont au village et valides
    soignent et traient les betes : 2,5 h chacun au plus, a tour de role ( rang de l identifiant decale du jour ). Rend les heures
    donnees, creditees a chacun ( Habitant.heures_jour : la paie les voit ) et comptees a part."""
    dispo = [h for h in ex.paysans if h.vivant and h.poste not in ("hopital", "voyage")
             and not (h.etat == "I" and h.gravite > 0.5) and (h.lieu is ex.lieu or h.domicile is ex.lieu)]
    if not dispo: return 0.0
    n = len(dispo)
    rang = sorted(((h.id + p.jour) % n, h.id, k) for k, h in enumerate(dispo))
    donne = 0.0
    for _, _, k in rang:
        h = dispo[k]
        if donne >= heures - EPS: break
        x = min(H_ASTREINTE_MAX, heures - donne)
        h.heures_jour += x; donne += x
    ex.astreinte_h += donne
    p.compter("astreinte_elevage", donne)
    return donne


def _besoin_soins(A, f, d):
    """Heures de soins du jour : la traite des femelles adultes pendant la saison de traite, l affouragement et la
    surveillance de toutes les autres tetes ( males, recrues, jeunes )."""
    tr = A.troupeaux
    adultes = float(tr.adultes[f].sum())
    autres = float(tr.recrues[f].sum() + tr.naissances[f].sum())
    if COURBE_TRAITE[d] > 0:
        return adultes * FEMELLES * H_TRAITE + (adultes * (1.0 - FEMELLES) + autres) * H_HORS_TRAITE
    return (adultes + autres) * H_HORS_TRAITE


def _recoltes(p, A, f, ex, d, H):
    ch = A.champs
    for c in ORDRE_RECOLTE:
        if not ch.ouvert[c, f]: continue
        cu = CULTURES[c]
        if cu.mode == "cueillette":
            a, b = cu.recolte
            mur = ch.attendu[c, f] / _longueur(a, b)
            if cu.suit_le_jour: mur *= (A.fi[f] if cu.irriguee else A.fs[f])
            dispo = ch.backlog[c, f] + mur
            if dispo <= 0: continue
            besoin = dispo / 1000.0 * cu.h_recolte
            part = min(1.0, H / besoin) if besoin > 0 else 1.0
            pris = dispo * part; H -= besoin * part
            reste = dispo - pris
            pourri = reste * cu.pourrit
            ch.backlog[c, f] = reste - pourri
            ch.perdu[c, f] += pourri
            if pourri > 0:
                A.sinistres.append((p.jour, ex.id, cu.nom, "non_cueilli", pourri)); p.compter("perte_recolte", pourri)
            ch.recolte[c, f] += pris
            _entrer(p, A, ex, cu.bien, pris, "recolte")
        else:                                           # moisson, coupe
            if ch.restant[c, f] <= 0: continue
            ha = min(ch.restant[c, f], H / cu.h_recolte) if cu.h_recolte > 0 else ch.restant[c, f]
            if ha <= 0: continue
            H -= ha * cu.h_recolte
            kg_ha = _kg_ha(ch, c, f)
            retard = max(0, p.jour - int(ch.ouvert_j[c, f]) - GRACE_MOISSON_J) if cu.mode == "moisson" else 0
            perte = min(1.0, PERTE_MOISSON_J * retard)
            kg = ha * kg_ha * (1.0 - perte)
            ch.restant[c, f] -= ha
            ch.recolte[c, f] += kg; ch.perdu[c, f] += ha * kg_ha * perte
            if perte > 0: A.sinistres.append((p.jour, ex.id, cu.nom, "retard", ha * kg_ha * perte))
            _entrer(p, A, ex, cu.bien, kg, "recolte")
            if cu.nom == "ble":
                A.troupeaux.chaumes[f] += CHAUMES_KG_HA * ha
                _mettre_de_cote(p, A, ex, f)
            if ch.restant[c, f] <= EPS and cu.mode == "moisson": ch.restant[c, f] = 0.0
    return H


def _mettre_de_cote(p, A, ex, f):
    """Apres la moisson, la semence de l automne est triee dans le grain de la ferme ( ble et vesce-avoine, plus 10 % )."""
    ch = A.champs
    voulu = 1.1 * sum(CULTURES[c].semences_kg_ha * ch.surface[c, f] for c in range(NC) if CULTURES[c].semis is not None)
    manque = voulu - _q(A, ex, "semences")
    if manque > 0:
        _transformer(p, A, ex, RECETTES["trier"], min(_q(A, ex, "cereales"), manque / RECETTES["trier"].sorties["semences"]))


def _operations(p, A, f, ex, d, H):
    """Semis et plantations, puis taille : dans leur fenetre, autant que les heures le permettent."""
    ch = A.champs
    for c, cu in enumerate(CULTURES):
        if H <= 0: break
        if ch.a_semer[c, f] > 0 and cu.semis is not None and _dans(d, *cu.semis):
            ha = min(ch.a_semer[c, f], H / cu.h_semis_ha)
            if cu.semences_kg_ha > 0:
                dispo = _q(A, ex, "semences")
                if dispo < ha * cu.semences_kg_ha:           # plus de semence triee : on seme du grain de consommation
                    _transformer(p, A, ex, RECETTES["trier"], min(_q(A, ex, "cereales"),
                                 (ha * cu.semences_kg_ha - dispo) / RECETTES["trier"].sorties["semences"]))
                ha = min(ha, _q(A, ex, "semences") / cu.semences_kg_ha)
                _sortir(p, A, ex, "semences", ha * cu.semences_kg_ha, "consomme", "semis")
            if ha <= 0: continue
            H -= ha * cu.h_semis_ha
            ch.a_semer[c, f] -= ha; ch.campagne_ha[c, f] += ha
            if ch.a_semer[c, f] <= EPS:
                ch.a_semer[c, f] = 0.0
                p.noter("semis", ferme=ex.id, culture=cu.nom, surface_ha=round(float(ch.campagne_ha[c, f]), 2))
        if ch.taille[c, f] > 0 and cu.taille is not None and _dans(d, *cu.taille):
            ha = min(ch.taille[c, f], H / cu.h_taille_ha)
            if ha <= 0: continue
            H -= ha * cu.h_taille_ha
            ch.taille[c, f] -= ha
            _entrer(p, A, ex, "bois", ha * cu.bois_t_ha * 1000.0, "taille")
    return H


def _peche(p, A, f, ex, d, H):
    """Une sortie par jour ouvre si la mer le permet ( vent sous la force 5 ) et si deux paysans sont au travail pour
    6 heures ; la prise suit la saison et le hasard du jour."""
    if ex.bateau is None or H < EQUIPAGE * H_SORTIE: return H
    if ex.presents_max < EQUIPAGE: return H
    vent = TER.meteo(p, ex.lieu).vent_ms
    if vent >= VENT_MAX_PECHE: return H
    mois = int(TER.MOIS_DU_JOUR[d])
    u = p.du_jour("agriculture_peche").lognormal(-0.5 * SIGMA_PRISE ** 2, SIGMA_PRISE, len(A.liste))[f]
    kg = PRISE_KG * SAISON_PECHE[mois] * float(u)
    _entrer(p, A, ex, "poisson", kg, "peche")
    p.compter("sortie_peche", kg)
    parc = p.socle.parc
    if parc.user(ex.bateau, H_SORTIE) >= 1.0:
        parc.sortir(ex.bateau, "rebut"); p.noter("bateau_au_rebut", ferme=ex.id); ex.bateau = None
    return H - EQUIPAGE * H_SORTIE


def _troupeau(p, A, f, ex, d, soins):
    """La journee du troupeau : mises bas, jeunes abattus ou gardes a 50 jours, recrues, reformes, morts ; ce qu il
    mange ( paturage, chaumes, puis foin du grenier ) ; le lait trait, s il a ete nourri et soigne."""
    tr = A.troupeaux; rng_k = p.jour % SEVRAGE_J
    for e, es in enumerate(ESPECES):
        a = tr.adultes[f, e]
        # les jeunes de 50 jours : abattus, sauf les femelles gardees pour remplacer reformes et morts
        n50 = tr.naissances[f, e, rng_k]
        if n50 > 0:
            vivants = n50 * (1.0 - es.mortalite_jeune)
            tr.morts += n50 - vivants
            garde_part = (es.reforme_an + es.mortalite_an) / max(EPS, es.fertilite * es.prolificite * FEMELLES * 0.5 * (1.0 - es.mortalite_jeune))
            garde = min(vivants * 0.5, vivants * 0.5 * min(1.0, garde_part)) if a > 0 else 0.0
            abattus = vivants - garde
            tr.recrues[f, e] += garde; tr.abattus += abattus
            _entrer(p, A, ex, "viande", abattus * es.carcasse_jeune_kg, "abattage")
            p.compter("abattage", abattus * es.carcasse_jeune_kg)
        tr.naissances[f, e, rng_k] = 0.0
        if _dans(d, *MISE_BAS):
            nes = a * FEMELLES * es.fertilite * es.prolificite / N_MISE_BAS
            tr.naissances[f, e, rng_k] = nes; tr.nes += nes
            p.compter("mise_bas", nes)
        if d == RECRUES_JOUR:
            tr.reforme_du_jour[f, e] = a * es.reforme_an / N_REFORME
            tr.adultes[f, e] += tr.recrues[f, e]; tr.recrues[f, e] = 0.0
        if _dans(d, *REFORME):
            r = min(tr.adultes[f, e], tr.reforme_du_jour[f, e])
            tr.adultes[f, e] -= r; tr.abattus += r
            _entrer(p, A, ex, "viande", r * es.carcasse_reforme_kg, "abattage")
            p.compter("abattage", r * es.carcasse_reforme_kg)
        morts = tr.adultes[f, e] * es.mortalite_an / JOURS_AN
        if tr.jours_disette[f] >= JOURS_DISETTE: morts += tr.adultes[f, e] * MORT_DISETTE_J
        morts = min(morts, tr.adultes[f, e])
        tr.adultes[f, e] -= morts; tr.morts += morts
        if morts > 0: p.compter("mort_betail", morts)
    # manger
    adultes = float(tr.adultes[f].sum()); jeunes = float(tr.recrues[f].sum() + tr.naissances[f].sum())
    besoin = adultes * (MS_LACTATION if COURBE_TRAITE[d] > 0 else MS_TARIE) + jeunes * MS_JEUNE
    servi = 0.0
    if besoin > 0:
        x = min(tr.paturage[f], besoin); tr.paturage[f] -= x; servi += x
        x = min(tr.chaumes[f], besoin - servi); tr.chaumes[f] -= x; servi += x
        if servi < besoin: servi += _sortir(p, A, ex, "fourrage", besoin - servi, "consomme", "affourager")
    ratio = servi / besoin if besoin > 0 else 1.0
    tr.alimentation[f] += (ratio - tr.alimentation[f]) / 7.0
    if tr.alimentation[f] < DISETTE:
        tr.jours_disette[f] += 1
        if tr.jours_disette[f] == JOURS_DISETTE: p.compter("disette_fourrage")
    else: tr.jours_disette[f] = 0
    # traire
    lait = 0.0
    if COURBE_TRAITE[d] > 0:
        for e, es in enumerate(ESPECES):
            lait += tr.adultes[f, e] * FEMELLES * es.lait_kg * COURBE_TRAITE[d]
        lait *= min(1.0, ratio / 0.9) * max(0.0, min(1.0, soins))
    tr.lait_j[f] = lait
    _entrer(p, A, ex, "lait", lait, "traite")


# ================================================================== l atelier : moulin, pressoir, fromagerie, four
def _rations_possibles(dispo_kcal):
    """Le plus grand nombre de rations que les calories disponibles par composante permettent, chaque ration portant au
    plus PARTS_MAX de chaque composante ( fonction concave par morceaux : on suit ses points de rupture )."""
    m = np.array(PARTS_MAX) * KCAL_RATION
    av = np.asarray(dispo_kcal, float)
    ruptures = sorted(set([0.0] + [a / mm for a, mm in zip(av, m) if a > 0]))
    def g(n): return float(np.minimum(av, m * n).sum() - KCAL_RATION * n)
    n_ok = 0.0
    for k in range(len(ruptures)):
        n0 = ruptures[k]
        g0 = g(n0)
        if g0 < -1e-9: break
        n_ok = n0
        n1 = ruptures[k + 1] if k + 1 < len(ruptures) else None
        pente = float(np.where(m * (n0 + 1e-12) < av, m, 0.0).sum() - KCAL_RATION)
        if n1 is None:
            if pente < 0: n_ok = n0 + g0 / -pente
            break
        g1 = g(n1)
        if g1 < 0:
            n_ok = n0 + g0 / -pente if pente < 0 else n1
            break
    return max(0.0, n_ok)


def _cuisiner(p, A, ex, n):
    """Fait n rations : chaque composante a sa part nominale si elle le peut, puis le manque est comble jusqu aux
    plafonds, le perissable d abord ( legumes, fruits, animal ), puis la farine, puis l huile. Les rations faites valent
    EXACTEMENT les kcal consommes / 2 500. Rend ( rations, kcal par composante, { bien : kg } )."""
    kg_pris = {}
    if n <= 0: return 0.0, [0.0] * len(COMPOSANTES), kg_pris
    dispo = [math.fsum(_q(A, ex, b) * KCAL[b] for b in bs) for bs in BIENS_COMPOSANTE]
    K_ = n * KCAL_RATION
    pris = [min(s * K_, a) for s, a in zip(PARTS_RATION, dispo)]
    manque = K_ - math.fsum(pris)
    for c in (2, 3, 4, 0, 1):                  # legumes, fruits, animal, farine, huile
        if manque <= 0: break
        x = min(manque, min(PARTS_MAX[c] * K_, dispo[c]) - pris[c])
        if x > 0: pris[c] += x; manque -= x
    kcal_faits = [0.0] * len(COMPOSANTES)
    for c, bs in enumerate(BIENS_COMPOSANTE):
        reste = pris[c]
        for b in bs:
            if reste <= 0: break
            kg = min(_q(A, ex, b), reste / KCAL[b])
            q = _sortir(p, A, ex, b, kg, "consomme", "cuisiner")
            kcal_faits[c] += q * KCAL[b]; reste -= q * KCAL[b]; kg_pris[b] = q
            if b in STOCKABLES: ex.usage_ema[b] += q
            elif b == "farine": ex.usage_ema["cereales"] += q / RECETTES["moudre"].sorties["farine"]
    return math.fsum(kcal_faits) / KCAL_RATION, kcal_faits, kg_pris


def _livrer_rations(p, A, ex, cible):
    """Le four et la fromagerie : au plus `cible` rations, autant que le grenier en permet ; elles entrent dans le stock
    de la ferme du moteur, qui les expedie a son marche ( camions de 30 unites au moins ). Rend ( rations, { bien : kg } )."""
    e = ex.ferme
    avant = {b: ex.usage_ema[b] for b in STOCKABLES}
    for b in STOCKABLES: ex.usage_ema[b] = 0.0
    dispo = [math.fsum(_q(A, ex, b) * KCAL[b] for b in bs) for bs in BIENS_COMPOSANTE]
    n = min(cible, _rations_possibles(dispo))
    rations, kc, kg_pris = _cuisiner(p, A, ex, n * (1.0 - 1e-12))
    for b in STOCKABLES: ex.usage_ema[b] = (1.0 - ALPHA_USAGE) * avant[b] + ALPHA_USAGE * ex.usage_ema[b]
    if rations > 0:
        e.stocks["nourriture"] += rations
        e.produit_du_jour["nourriture"] += rations
        p.socle.livre.flux["produit"]["nourriture"] += rations
        A.rations += rations
        p.compter("rations_agricoles", rations)
        comp = A.composition.setdefault(ex.marche_id, deque(maxlen=7))
        if not comp or comp[-1][0] != p.jour: comp.append([p.jour] + [0.0] * len(COMPOSANTES))
        for c in range(len(COMPOSANTES)): comp[-1][1 + c] += kc[c]
    return rations, kg_pris


def _atelier(p, A, f, ex, cible):
    """Le pressoir ( toutes les olives du jour ), le moulin ( la farine du jour et un tampon de 3 jours ), le four et la
    fromagerie ( les rations ), puis le lait qui reste en feta, et le frais qui depasse deux jours d usage au negoce."""
    if _q(A, ex, "olives") > 0: _transformer(p, A, ex, RECETTES["presser"], _q(A, ex, "olives"))
    farine_voulue = (cible * PARTS_MAX[0] + TAMPON_FARINE_J * ex.part * _besoin_region(p, ex.marche_id) * PARTS_RATION[0]) \
        * KCAL_RATION / KCAL["farine"]
    manque = farine_voulue - _q(A, ex, "farine")
    if manque > 0 and _q(A, ex, "cereales") > 0:
        _transformer(p, A, ex, RECETTES["moudre"], min(_q(A, ex, "cereales"), manque / RECETTES["moudre"].sorties["farine"]))
    rations, kg_pris = _livrer_rations(p, A, ex, cible)
    ex.livre_j = rations
    if _q(A, ex, "lait") > 0: _transformer(p, A, ex, RECETTES["fromager"], _q(A, ex, "lait"))
    for b in FRAIS_VENDABLES:
        garde = 2.0 * kg_pris.get(b, 0.0) + 1.0
        x = _q(A, ex, b) - garde
        if x > 0: _vendre(p, A, ex, b, x)


# ================================================================== la decision : vendre ou stocker la recolte
class ContexteVente:
    """Ce que voit une ferme le matin de sa decision : son grenier et ses lots, son calendrier, le prix et la couverture
    affiches a son marche, le bulletin de la faim de sa region. Pas les greniers des autres, pas la recolte a venir."""
    __slots__ = ("traits", "ferme")

    def __init__(self, traits, ferme): self.traits, self.ferme = traits, ferme


def _observer_vente(ctx): return ctx.traits


def _regle_vente(x, ctx):
    soudure, _, _, _, faim, perit, surplus = x
    if faim > 0.1: return 0                          # sa region a faim ( > 2 % des menages ) : on garde
    if perit > 1.0 / 3.0 and surplus > 0: return 1  # ce qui va perir se vend
    if soudure >= MARGE_SOUDURE / 2.0: return 1      # au-dela de 1,25 fois la soudure : le surplus part
    return 0


def _temoin_vente(x, ctx, rng): return 2


POINT_VENTE = D.PointDeDecision(
    "vendre_recolte", "agriculture",
    traits=(("soudure", "son grenier ( grain, huile, feta ) en jours de sa part du besoin de sa region jusqu a la prochaine "
                        "recolte de chacun, sur deux fois ce besoin ( ses lots, son calendrier, ce que ses rations ont pris )"),
            ("jours_recolte", "jours jusqu a la prochaine moisson, sur 365 ( le calendrier )"),
            ("prix_marche", "prix affiche de la ration a son marche, sur 2,5 fois le prix mondial"),
            ("couverture", "stock de nourriture de son marche en jours du besoin de sa region, sur 5 ( affiche )"),
            ("faim_region", "part des menages de sa region sans repas hier, fois 5, bornee ( bulletin du soir )"),
            ("peremption", "part de son grenier qui perit dans les 30 jours ( dates de ses lots )"),
            ("surplus", "part de son grenier au-dela de 1,25 fois la soudure ( son grenier )")),
    actions=ACTIONS_VENTE,
    observer=_observer_vente, regle=_regle_vente, temoin=_temoin_vente,
    note=("chaque jour, pour CETTE ferme : ses rations livrees a SA region sur sa part equitable ( surface ) de ce que la "
          "region demandait ( bornee a 1 ), "
          "moins 4 x la faim de SA region x la part non livree, plus 0,1 x son revenu du jour ( rations vendues au marche, "
          "grain, huile et feta vendus au negoce ; pas le frais, que la decision ne touche pas ) sur la valeur de sa part du besoin de sa region au prix mondial ( a l installation ) ; moyenne sur 14 jours"),
    horizon_j=HORIZON_VENTE)


def _prochaine(d, debut, fin):
    """Jours jusqu a la fin de la prochaine recolte d une culture ( la soudure )."""
    return _ecoule(d, debut) + _longueur(debut, fin)


def besoin_soudure(p, A, ex, d):
    """kg de chaque bien stockable que la ferme doit garder pour nourrir sa part de sa region jusqu a sa prochaine
    recolte : le plus grand de l usage nominal et de ce que ses rations ont vraiment pris ces 30 jours."""
    B = ex.part * _besoin_region(p, ex.marche_id) * KCAL_RATION
    nominal = {"cereales": B * PARTS_RATION[0] / (KCAL["farine"] * RECETTES["moudre"].sorties["farine"]),
               "huile": B * PARTS_RATION[1] / KCAL["huile"],
               "fromage": B * PARTS_RATION[4] * PART_FROMAGE_HORS_TRAITE / KCAL["fromage"]}
    jours = {"cereales": _prochaine(d, *CULTURES[IC["ble"]].recolte) + SOUDURE_EN_PLUS_J,
             "huile": _prochaine(d, *CULTURES[IC["olivier"]].recolte) + SOUDURE_EN_PLUS_J,
             "fromage": _ecoule(d, TRAITE[0]) + SOUDURE_EN_PLUS_J}
    return {b: max(nominal[b], ex.usage_ema[b]) * jours[b] for b in STOCKABLES}, {b: max(nominal[b], ex.usage_ema[b]) for b in STOCKABLES}


def _traits_vente(p, A, ex, d):
    w = p.w; m = w.marches[ex.marche_id]
    soud, jour_b = besoin_soudure(p, A, ex, d)
    kcal_st = math.fsum(_q(A, ex, b) * KCAL[b] for b in STOCKABLES)
    kcal_so = math.fsum(soud[b] * KCAL[b] for b in STOCKABLES)
    perit = 0.0
    cat = p.socle.catalogue
    for b in STOCKABLES:
        cj = cat[b].conservation_j
        for lot in ex.lots.get(A.ids[b], ()):
            if p.jour - lot[0] + PEREMPTION_HORIZON_J >= cj: perit += lot[1] * KCAL[b]
    need = _besoin_region(p, ex.marche_id)
    surplus = math.fsum(max(0.0, _q(A, ex, b) - MARGE_SOUDURE * soud[b]) * KCAL[b] for b in STOCKABLES)
    return (min(1.0, kcal_st / max(EPS, 2.0 * kcal_so)),
            _ecoule(d, CULTURES[IC["ble"]].recolte[0]) / JOURS_AN,
            min(1.0, m.prix["nourriture"] / (2.5 * C.PRIX_MONDE["nourriture"])),
            min(1.0, max(0.0, m.stocks["nourriture"]) / max(EPS, 5.0 * need)) if need > 0 else 1.0,
            min(1.0, 5.0 * w.faim_region.get(ex.marche_id, 0.0)),
            min(1.0, perit / kcal_st) if kcal_st > 0 else 0.0,
            min(1.0, surplus / kcal_st) if kcal_st > 0 else 0.0), soud, jour_b


def _matin(p):
    """6 h 40, tous les 7 jours : chaque ferme decide de vendre ou de garder sa recolte, et le negociant emporte ce
    qu elle vend."""
    if p.jour % 7 != JOUR_DECISION: return
    A = p.domaine("agriculture"); d = _doy(p)
    for ex in A.liste:
        if ex.sequestre: continue
        x, soud, jour_b = _traits_vente(p, A, ex, d)
        a = A.decideur.decider(ex.id, ContexteVente(x, ex))
        if a == 1:
            for b in STOCKABLES: _vendre(p, A, ex, b, _q(A, ex, b) - MARGE_SOUDURE * soud[b])
        elif a == 2:
            for b in STOCKABLES: _vendre(p, A, ex, b, _q(A, ex, b) - GARDE_TEMOIN_J * jour_b[b])


def _avant_paie(p):
    """17 h 50 : ce que la caisse de chaque ferme a recu depuis la derniere paie ( ventes au marche et au negoce )."""
    for ex in p.domaine("agriculture").liste: ex.revenu_j = max(0.0, ex.ferme.caisse - ex.caisse_ref)


def _apres_paie(p):
    for ex in p.domaine("agriculture").liste: ex.caisse_ref = ex.ferme.caisse


def note_du_jour(p, ex):
    """La consequence du jour pour une ferme ( voir POINT_VENTE.note )."""
    q = 1.0 if ex.ref_j <= EPS else min(1.0, ex.livre_j / ex.ref_j)
    f = p.w.faim_region.get(ex.marche_id, 0.0)
    return q - K_FAIM * f * (1.0 - q) + LAMBDA_REVENU * max(0.0, ex.revenu_j - ex.frais_j) / ex.valeur_ref


def _soir(p):
    """20 h 10, apres le repas : chaque decision en attente encaisse la journee de SA ferme."""
    A = p.domaine("agriculture"); dec = A.decideur
    for ex in A.liste:
        att = dec.attentes.get(ex.id)
        if att is None: continue
        if not att.choix: del dec.attentes[ex.id]; continue
        dec.noter(ex.id, note_du_jour(p, ex), p.jour)


# ================================================================== la cloture
def _cloture(p, comptes):
    """Les flux de biens du jour, lus dans le grand livre par ( nature, motif, bien ) : la matiere des bilans des
    recettes ; et la serie du jour."""
    A = p.domaine("agriculture")
    mes = set(NOMS_BIENS) | {"nourriture", "engrais"}
    for nature, motif, bien, q in comptes["biens"]:
        if bien in mes:
            k = (nature, motif, bien)
            A.flux_motif[k] = A.flux_motif.get(k, 0.0) + q
    kst = math.fsum(_q(A, ex, b) * KCAL[b] for ex in A.liste for b in STOCKABLES)
    faim = p.w.stats_jour.get("menages_sans_nourriture", 0)
    E = p.domaine("economie")
    non_servi = math.fsum(em.non_servi["nourriture"] for em in E.marches.values())
    vendu = math.fsum(em.ventes_q["nourriture"] for em in E.marches.values())
    besoin = math.fsum(_besoin_region(p, mid) for mid in A.par_marche)
    A.serie.append((p.jour - 1, math.fsum(ex.livre_j for ex in A.liste), faim, kst,
                    math.fsum(ex.astreinte_h for ex in A.liste), math.fsum(ex.presence_h for ex in A.liste),
                    non_servi, vendu, besoin, _q_national(A, "cereales")))


def _q_national(A, nom):
    return math.fsum(_q(A, ex, nom) for ex in A.liste)


def bilans_recettes(p):
    """Pour chaque recette : ( kg d entree, ecart de masse, ecart de kcal ) mesures dans le grand livre depuis
    l installation ( jours clos ), contre la recette DECLAREE ( les constantes du module, pas l objet qui travaille ).
    Zero, sinon une transformation cree ou detruit de la matiere. Et pour la cuisine : kcal consommes - 2 500 x
    rations produites."""
    A = p.domaine("agriculture"); fm = A.flux_motif
    out = {}
    for nom, (entree, sorties, _) in DECLAREES.items():
        q_in = fm.get(("consomme", nom, entree), 0.0)
        masse_out = math.fsum(fm.get(("produit", nom, b), 0.0) for b in sorties)
        kcal_out = math.fsum(fm.get(("produit", nom, b), 0.0) * BIENS[b][7] for b in sorties)
        perte = 1.0 - math.fsum(sorties.values())
        kcal_hors = BIENS[entree][7] - math.fsum(k * BIENS[b][7] for b, k in sorties.items())
        out[nom] = (q_in, q_in * (1.0 - perte) - masse_out, q_in * BIENS[entree][7] - kcal_out - q_in * kcal_hors)
    return out


# Les recettes telles que declarees ( pour les bilans : un objet Recette modifie en marche se voit contre elles ).
DECLAREES = {nom: (r.entree, dict(r.sorties), r.source) for nom, r in RECETTES.items()}


def bilan_cheptel(p):
    """Tetes presentes - ( depart + naissances - abattus - morts ). Zero, sinon une bete est nee ou morte hors compte."""
    tr = p.domaine("agriculture").troupeaux
    present = float(tr.adultes.sum() + tr.recrues.sum() + tr.naissances.sum())
    return present - (tr.depart + tr.nes - tr.abattus - tr.morts)


# ================================================================== l API des autres domaines
def exploitation_de(p, lieu):
    """L Exploitation d un village ( Lieu, identifiant de lieu ou de ferme ), ou None."""
    A = p.domaine("agriculture")
    lid = lieu if isinstance(lieu, str) else lieu.id
    return A.par_id.get(lid) or A.par_id.get(f"ferme@{lid}")


def stock_de(p, lieu):
    """Le Stock du socle d une ferme : un domaine qui lui livre un bien ( l engrais du domaine 10 ) le deplace ici par
    le grand livre ( livre.deplacer ) ; il ne livre JAMAIS un bien du domaine 9 ( ses lots ne le suivraient pas )."""
    ex = exploitation_de(p, lieu)
    return None if ex is None else ex.stock


def kcal(bien):
    """kcal par unite d un bien du domaine ( la ration : 2 500 )."""
    return KCAL_RATION if bien == "nourriture" else KCAL[bien]


def stocks_vivres(p, ile=None):
    """{ lieu : { bien : kg } } des vivres stockables ( grain, farine, huile, feta ) des fermes, et le total en kcal :
    ce que l intendance militaire ( domaine 26 ) peut requisitionner."""
    A = p.domaine("agriculture"); out = {}; tot = 0.0
    for ex in A.liste:
        if ile is not None and ex.lieu.ile != ile: continue
        v = {b: _q(A, ex, b) for b in ("cereales", "farine", "huile", "fromage")}
        out[ex.lieu.id] = v; tot += math.fsum(q * KCAL[b] for b, q in v.items())
    return out, tot


def requisitionner(p, lieu, bien, kg, vers, motif="requisition"):
    """Deplace `kg` d un bien stockable d une ferme vers le Stock d un autre detenteur inscrit ( `vers` ), par le grand
    livre, les plus vieux lots d abord. Le paiement ( ou l indemnite ) est au domaine qui requisitionne. Rend les kg."""
    A = p.domaine("agriculture"); ex = exploitation_de(p, lieu)
    if ex is None or bien not in BIENS: return 0.0
    L = p.socle.livre
    if motif not in L.motifs: L.declarer_motif(motif, "achat", "agriculture")
    pris = L.deplacer(ex.stock, vers, A.ids[bien], max(0.0, min(kg, _q(A, ex, bien))), motif)
    _lot_retirer(ex, A.ids[bien], pris)
    return pris


def composition_regionale(p, marche):
    """La ration de la region d un marche sur les 7 derniers jours : kcal livrees et part de chaque composante ( farine,
    huile, legumes, fruits, animal ). Ce que la medecine ( 16 ) lit pour l etat nutritionnel : une ration a 85 % de pain
    nourrit sans proteines ni vitamines."""
    A = p.domaine("agriculture")
    mid = marche if isinstance(marche, str) else marche.lieu.id
    dq = A.composition.get(mid, ())
    tot = [math.fsum(r[1 + c] for r in dq) for c in range(len(COMPOSANTES))]
    s = math.fsum(tot)
    return {"kcal_7j": s, "parts": {n: (t / s if s > 0 else 0.0) for n, t in zip(COMPOSANTES, tot)}}


def rendement_attendu(p, lieu, culture):
    """kg attendus de la campagne en cours d une culture d une ferme, au rendement reel moyen et au climat accumule."""
    A = p.domaine("agriculture"); ex = exploitation_de(p, lieu); c = IC[culture]; ch = A.champs
    g = A.liste.index(ex); cu = CULTURES[c]
    ha = ch.campagne_ha[c, g] if cu.semis is not None else ch.surface[c, g]
    return cu.rendement_t_ha * 1000.0 * ha * float(_facteur_engrais(ch, c)[g]) * float(_climat_campagne(ch, c)[g])


def rendement_constate(p, lieu, culture):
    """La derniere campagne close d une culture d une ferme : ( t/ha recoltees, t/ha perdues, climat, engrais ), ou None."""
    A = p.domaine("agriculture"); ex = exploitation_de(p, lieu); g = A.liste.index(ex); c = IC[culture]
    for j, gg, cc, ha, kg, perdu, fr, clim, eng in reversed(A.champs.campagnes):
        if gg == g and cc == c:
            return kg / ha / 1000.0 / max(fr, 1e-9), perdu / ha / 1000.0 / max(fr, 1e-9), clim, eng
    return None


def sinistres(p, depuis=0):
    """Les pertes de recolte depuis un jour : ( jour, ferme, culture, cause, kg ) - causes : non_recolte, non_cueilli,
    retard, non_seme. Avec le climat de la campagne ( rendement_constate ), la matiere de l assurance recolte ( 20 )."""
    return [s for s in p.domaine("agriculture").sinistres if s[0] >= depuis]


def recoltes_a_expedier(p):
    """{ lieu : { bien : kg } } de ce que chaque ferme a en grenier, et { bien : ( kg par unite, litres par unite ) } :
    la matiere du fret des recoltes ( domaine 15 )."""
    A = p.domaine("agriculture"); cat = p.socle.catalogue
    st = {ex.lieu.id: {cat[b].nom: q for b, q in ex.stock.items()} for ex in A.liste}
    return st, {b: (cat[b].masse_kg, cat[b].volume_l) for b in NOMS_BIENS}


def ventes_negoce(p):
    """{ ferme : { bien : kg } } vendus au negoce aujourd hui ( ils quittent le pays a la ferme : le fret les prendra
    en charge quand le domaine 15 le voudra )."""
    return {k: dict(v) for k, v in p.domaine("agriculture").ventes.items()}


def besoins_engrais(p):
    """{ lieu : kg } d engrais que chaque ferme apporterait a ses prochaines campagnes ( domaine 10 )."""
    A = p.domaine("agriculture"); ch = A.champs; out = {}
    for g, ex in enumerate(A.liste):
        out[ex.lieu.id] = math.fsum(CULTURES[c].dose_engrais * ch.surface[c, g] for c in range(NC))
    return out


# ================================================================== installation
def _cotieres(carte, lieux):
    """Les villages a moins de COTE_KM d un repere cotier de leur ile ( cap, ilot, jetee, phare : CfgWorlds >> Names ).
    Le trait de cote lui-meme n est pas dans les donnees du monde ( a calibrer sur la carte d altitude )."""
    out = set()
    for ile in sorted({l.ile for l in lieux}):
        try:
            with open(os.path.join(K.ICI, "donnees", K.ILES[ile])) as fh: donnees = json.load(fh)
        except (KeyError, OSError): continue
        reperes = [tuple(x["pos"][:2]) for x in donnees if x.get("type") == "NameLocal"
                   and (x["id"].startswith("Cap") or x["id"].endswith("Island") or x["id"] in ("KavalaPier", "Faros"))]
        for l in lieux:
            if l.ile == ile and reperes and min(math.dist(l.pos[:2], r) for r in reperes) <= COTE_KM * 1000.0:
                out.add(l.id)
    return out


def _exploitations(w): return w.pays.domaines["agriculture"].liste


def _acc_depuis(cu, depuis, jusqu_a):
    """Poids de sensibilite d une campagne entre deux jours de l an ( climat normal : le monde nait normal )."""
    w = 0.0
    d = depuis
    while d != jusqu_a:
        for a, b, poids in cu.sensibilite:
            if _dans(d, a, b): w += poids
        d = (d + 1) % JOURS_AN
    return w


def _debut_campagne(cu):
    """Le jour ou commence la campagne en cours : semis ou plantation, sinon la fin de la recolte precedente."""
    if cu.semis is not None: return cu.semis[0]
    return (cu.recolte[1] + 1) % JOURS_AN


def _etat_initial(p, A, d):
    """Le monde nait le 15 juin, dans un etat normal pour la date : ble mur, legumes et fruits plantes, olives nouees,
    luzerne coupee, vesce fauchee en mai ; greniers de la fin de la campagne precedente ; troupeau en fin de traite."""
    ch, tr = A.champs, A.troupeaux
    for c, cu in enumerate(CULTURES):
        if cu.mode in ("paturage", "coupes"): continue
        a, b = cu.recolte
        debut = _debut_campagne(cu)
        en_place = True                                       # une culture perenne est toujours en place
        if cu.semis is not None:                              # semee ou plantee, et pas encore recoltee ?
            en_place = _ecoule(cu.semis[1], d) <= _ecoule(cu.semis[1], b) and d != cu.semis[1]
        if not en_place: continue
        ch.campagne_ha[c] = ch.surface[c]
        acc = _acc_depuis(cu, debut, d)
        ch.acc_w[c] = acc; ch.acc_wf[c] = acc
        if _dans(d, a, b):
            _ouvrir(p, A, c, d, fraction=(_longueur(d, b)) / _longueur(a, b) if cu.mode == "cueillette" else 1.0)
            if cu.mode == "moisson" and _ecoule(a, d) > 0:
                ch.ouvert_j[c] = p.jour - _ecoule(a, d)
    c = IC["luzerne"]
    passees = [x for x in COUPES_LUZERNE if _ecoule(x, d) < FENETRE_COUPE_J]
    if passees:                                            # une coupe en cours au 15 juin ? ( non, avec le calendrier d Altis )
        ch.campagne_ha[c] = ch.surface[c]
        ch.attendu[c] = CULTURES[c].rendement_t_ha * 1000.0 / len(COUPES_LUZERNE) * ch.surface[c]
        ch.restant[c] = ch.surface[c]; ch.ouvert[c] = 1; ch.ouvert_j[c] = p.jour; ch.fraction[c] = 1.0; ch.climat[c] = 1.0
    tr.paturage[:] = 0.0; tr.chaumes[:] = 0.0


def _stocks_initiaux(p, A, d):
    """Les greniers du 15 juin, en jours de la part de chaque ferme ( a calibrer ) : 30 jours de vieux grain, 5 de
    farine, 200 d huile ( la recolte de l hiver ), 120 de feta ( la traite du printemps ), 150 de fourrage pour le
    troupeau ; le bois de la taille de l hiver. Une source declaree : produit, motif stock_initial."""
    tr = A.troupeaux; ch = A.champs
    for f, ex in enumerate(A.liste):
        B = ex.part * _besoin_region(p, ex.marche_id) * KCAL_RATION
        besoin_ms = float(tr.adultes[f].sum()) * MS_TARIE + float(tr.recrues[f].sum()) * MS_JEUNE
        for nom, q, age in (
                ("cereales", 30 * B * PARTS_RATION[0] / (KCAL["farine"] * RECETTES["moudre"].sorties["farine"]), 365),
                ("farine", 5 * B * PARTS_RATION[0] / KCAL["farine"], 5),
                ("huile", 200 * B * PARTS_RATION[1] / KCAL["huile"], 180),
                ("fromage", 40 * B * PARTS_RATION[4] * PART_FROMAGE_HORS_TRAITE / KCAL["fromage"], 105),
                ("fromage", 40 * B * PARTS_RATION[4] * PART_FROMAGE_HORS_TRAITE / KCAL["fromage"], 60),
                ("fromage", 40 * B * PARTS_RATION[4] * PART_FROMAGE_HORS_TRAITE / KCAL["fromage"], 20),
                ("fourrage", 150 * besoin_ms, 40),
                ("bois", 1000.0 * math.fsum(CULTURES[c].bois_t_ha * ch.surface[c, f] for c in range(NC)), 110)):
            _entrer(p, A, ex, nom, q, "stock_initial", jour=p.jour - age)


def installer(p):
    w = p.w
    T = p.domaine("territoire")
    A = Agriculture()
    cat, L, J = p.socle.catalogue, p.socle.livre, p.socle.journal
    # --- les biens, les motifs, le journal
    for nom, (fam, unite, prix, tva, masse, vol, cons, _, src) in BIENS.items():
        b = cat.declarer(nom, fam, unite, prix / PAYS.EUROS_PAR_DRACHME, categorie_tva=tva, masse_kg=masse, volume_l=vol, conservation_j=cons,
                         source=src)
        A.ids[nom] = b.id
    L.declarer_motif("vente_negoce", "achat", "agriculture")
    for t, champs in (("recolte", ("ferme", "culture", "kg", "surface_ha", "rendement_t_ha")),
                      ("semis", ("ferme", "culture", "surface_ha")), ("bateau_au_rebut", ("ferme",))):
        J.declarer(t, "agriculture", "individuel", champs)
    for t in ("rations_agricoles", "astreinte_elevage", "peremption_agricole", "vente_negoce", "sortie_peche", "mise_bas",
              "abattage", "mort_betail", "perte_recolte", "irrigation_agricole", "disette_fourrage"):
        J.declarer(t, "agriculture", "compte")
    parc = p.socle.parc
    if MODELE_BATEAU not in parc.par_nom:
        parc.declarer_modele(MODELE_BATEAU, "navire", 45000.0 / PAYS.EUROS_PAR_DRACHME, 5000.0, 40000.0, arma="CUP_C_Fishing_Boat_Chernarus",
                             source="caique de bois de 8 a 10 m d occasion : 30 000 a 60 000 EUR ; ~5 t ; 40 000 h de "
                                    "moteur ( a calibrer ) ; classname CUP Vehicles, jamais vu vivre en jeu")
    # --- les fermes reprises : celles des iles dont le calendrier est celui de l Egee
    fermes = sorted((e for e in w.entreprises.values() if e.type == "ferme" and e.lieu.ile in ILES_CALENDRIER),
                    key=lambda e: e.id)
    cotieres = _cotieres(w.carte, [e.lieu for e in fermes])
    P = T.parcelles
    rng = p.hasard("agriculture_installation")
    for e in fermes:
        k = P.lieu_id.index(e.lieu.id)
        ex = Exploitation(e, k, float(P.surface_ha[k]), float(P.irrigue[k]), e.lieu.id in cotieres, SB.Stock())
        ex.phase_olive = int(rng.integers(0, 2))
        A.par_id[ex.id] = ex; A.liste.append(ex)
        p.reprendre(e, "agriculture")
    nf = len(A.liste)
    for g, ex in enumerate(A.liste): A.par_marche.setdefault(ex.marche_id, []).append(g)
    p.domaines["agriculture"] = A                  # _besoin_region lit l index des entreprises reprises
    for mid, gs in A.par_marche.items():
        tot = math.fsum(A.liste[g].surface_ha for g in gs)
        for g in gs:
            ex = A.liste[g]; ex.part = ex.surface_ha / tot
            ex.valeur_ref = max(1.0, ex.part * _besoin_region(p, mid) * C.PRIX_MONDE["nourriture"])
    p.socle.registre.inscrire("exploitations", "entreprises", _exploitations, None, "stock", None)
    TER.reprendre_usage(p, "irrigation")
    # --- les champs : l assolement d Altis, ramene a la part irriguee de chaque parcelle
    A.champs = ch = Champs(nf)
    for c, cu in enumerate(CULTURES):
        for g, ex in enumerate(A.liste):
            part = cu.part * (ex.irrigue / PART_IRR_ALTIS if cu.irriguee else (1.0 - ex.irrigue) / PART_SEC_ALTIS)
            ch.surface[c, g] = ex.surface_ha * part
    # --- les troupeaux : a 85 % du fourrage d une annee normale
    A.troupeaux = tr = Troupeaux(nf)
    for g, ex in enumerate(A.liste):
        ms = (CULTURES[IC["luzerne"]].rendement_t_ha * ch.surface[IC["luzerne"], g]
              + CULTURES[IC["vesce_avoine"]].rendement_t_ha * CULTURES[IC["vesce_avoine"]].sans_engrais * ch.surface[IC["vesce_avoine"], g]
              + CULTURES[IC["jachere_paturage"]].rendement_t_ha * ch.surface[IC["jachere_paturage"], g]
              + CHAUMES_KG_HA / 1000.0 * ch.surface[IC["ble"], g]) * 1000.0
        tetes = math.floor(CHARGE_FOURRAGE * ms / MS_AN_TETE)
        for e, es in enumerate(ESPECES):
            tr.adultes[g, e] = float(round(tetes * es.part))
            tr.recrues[g, e] = float(round(tr.adultes[g, e] * (es.reforme_an + es.mortalite_an)))
    tr.depart = float(tr.adultes.sum() + tr.recrues.sum())
    A.fs = np.ones(nf); A.fi = np.ones(nf); A.fi35 = np.ones(nf)
    # --- les caiques des villages cotiers
    for ex in A.liste:
        if ex.cotiere:
            ex.bateau = parc.creer(MODELE_BATEAU, ex.ferme, ex.lieu.id, "initial", p.pas, usure=float(rng.uniform(0.2, 0.6)))
    A.decideur = p.decideur(POINT_VENTE)
    p.domaines["agriculture"] = A
    d = _doy(p)
    _etat_initial(p, A, d)
    _stocks_initiaux(p, A, d)
    _paysans(p)
    for mid, gs in A.par_marche.items():          # une ferme sur deux a deja un demi-camion : les livraisons alternent
        for r, g in enumerate(gs):
            if r % 2: _livrer_rations(p, A, A.liste[g], A.liste[g].part * _besoin_region(p, mid))
    A.jour_nuit = p.jour
    # --- l horloge du domaine
    for minute in range(0, 24 * 60, C.MINUTES_PAR_PAS): p.routine(minute / 60.0, 5, "agriculture", _presence)
    p.routine(10 / 60, 20, "agriculture", _nuit)
    p.routine(6 + 20 / 60, 20, "agriculture", _paysans)
    p.routine(6 + 40 / 60, 20, "agriculture", _matin)
    p.routine(15 + 50 / 60, 20, "agriculture", _journee)
    p.routine(17 + 50 / 60, 20, "agriculture", _avant_paie)
    p.routine(18 + 10 / 60, 20, "agriculture", _apres_paie)
    p.routine(20 + 10 / 60, 20, "agriculture", _soir)
    p.cloture("agriculture", _cloture)
    return A

