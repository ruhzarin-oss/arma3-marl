"""DOMAINE 16 - MEDECINE A : PATHOLOGIES, EPIDEMIES, DIAGNOSTIC, TRAITEMENTS.

FICHE
1. Classes. Les lois : Pathologie ( une maladie, une lesion, une complication : histoire naturelle, transmission,
   gravite et letalite par age, saison, symptomes ; chaque parametre avec sa source, ou la mention a calibrer ),
   Examen ( sensibilite, specificite ), Molecule ( un produit de sante, declare comme bien du catalogue : unite, prix,
   peremption, DDD, effets indesirables ), Effet ( ce qu une molecule fait a une pathologie ), Antibiotique ( la loi
   de la resistance ). Maladies transmissibles : grippe, COVID ( souche ancestrale ), rougeole, gastro-enterite
   ( norovirus et voie hydrique ), rhume, angine a streptocoque, tuberculose ( latente, reactivation ) ; sporadique :
   pneumonie a pneumocoque ( et surinfection d une grippe ou d une rougeole ). Lesions : chute, route, travail,
   ecrasement, brulure, balistique, eclats, arme blanche ( gravite ISS ). Complications de grossesse : pre-eclampsie,
   hemorragie du post-partum. Decompensations : crise diabetique, AVC, insuffisance cardiaque, exacerbation de BPCO.
   Effets indesirables legers et graves. L etat : Affections ( la table EPARSE des affections en cours, une ligne par
   ( habitant, affection ) : un habitant en porte plusieurs, jamais un champ par maladie dans Habitant ), Pharmacie
   ( les produits de sante d une capitale : stock du socle, lots ranges par peremption ), IndexDuJour ( menages,
   equipes de travail, classes, lieux, ages, faim : les groupes de contact, refaits a 6 h ), Medecine ( l etat du
   domaine ), ContexteConsulter, ContextePrescrire, et les objets qui prennent la place des methodes du moteur :
   RemplaceContagion, RemplaceProgression, RemplaceSoigner. Colonnes par habitant : med_chroniques ( diabete,
   insuline, HTA, cardiopathie, BPCO ), med_traite ( sous traitement d entretien ), med_sans_traitement_j,
   med_mental ( depression, anxiete, depression traitee ), med_mental_j, med_accouchement_vu, med_pe_conception. Par
   habitant et par maladie infectieuse, dans le domaine ( tableaux n x 8 ) : statut ( susceptible, immun, tuberculose
   latente ), fin d immunite, infection en cours, deja infecte ; par vaccin ( ROR, grippe, COVID ) : doses.
2. Invariants. Habitant.etat RESUME les affections : I si une affection clinique a une gravite >= 0,10 ( le malade se
   sent malade ; gravite = la pire ), E si une infection court sans symptome qui arrete ( incubation, porteur
   asymptomatique ou gueri encore contagieux, rhume ), R apres une guerison, S sinon ; remede = une affection clinique
   est soignee. Le moteur et l agenda lisent ces champs ( hopital si I et gravite > 0,3 ; pas de travail au-dela de
   0,5 ) : `incoherences_e1` et `hopital_incoherent` le verifient. Une infection au plus par ( habitant, maladie ) ;
   infecte[ h, m ] = 1 si et seulement si une ligne active porte ( h, m ). Temps d une affection : infection, debut
   de la contagiosite, symptomes, aggravation, fin des symptomes ( l issue, deces ou guerison, se tire la ), fin de
   la contagiosite, fin de l infection. TOUTE mort passe par d01.deceder ( porte test_deceder ). Biens : les
   pharmacies sont inscrites au registre ( famille `pharmacies`, stock du socle ) ; tout produit de sante entre par
   le grand livre ( importe ; produit pour le sang donne ) et en sort par lui ( consomme, perime ) ; la somme des lots
   egale le stock ( `ecarts_lots` ). Le premier stock ( 60 jours ) est une dotation importee sans paiement, comme les
   stocks de depart du moteur. Argent : consultation et participation aux medicaments ( menage -> Etat ),
   importations ( Etat -> exterieur ), kit de soins du moteur ( remedes : stock public des hopitaux, sinon achete au
   marche par le menage, comme Monde.soigner ), tout par le grand livre. Le domaine ne detient pas d argent.
3. Decisions. `consulter` ( le malade, aux jours 1, 3, 7, 14, 21 et 28 de ses symptomes, s il n est pas hospitalise ) :
   attendre ou consulter. Traits : fievre, toux, gene respiratoire, troubles digestifs, mal de gorge ( ses symptomes
   VISIBLES, pas son diagnostic ), jours de symptomes, malaise ressenti, age, maladie chronique connue, caisse du
   menage, distance au medecin, rumeur ( cas declares de sa region ). Note, pour CE malade, sur 7 jours : sante du
   jour ( 1 - gravite / 0,5 ; 0 s il meurt ), moins le cout de la consultation ( 0,05 ). Regle : consulter devant une
   gene respiratoire, un malaise fort, une fievre de 3 jours ( tout de suite a 65 ans ou malade chronique ), une toux
   de 14 jours, une diarrhee apres 75 ans. Temoin : ne jamais consulter.
   `prescrire` ( le medecin, a chaque consultation pour fievre, toux ou mal de gorge ) : sans antibiotique,
   antibiotique, tester puis decider ( test rapide du streptocoque, ou radio du thorax ). Traits : les memes
   symptomes, leur duree, l age, la maladie chronique, la part de grippe et de COVID parmi les cas declares ( 14 j ),
   la resistance publiee, le stock d amoxicilline. Note, pour CE patient, sur 7 jours : sa sante du jour, moins la
   resistance que la prescription cree ( 0,1 par traitement de 14 DDD, a calibrer ). Regle : criteres de Centor et de
   gravite ( tester devant une angine febrile sans toux ou une toux febrile qui dure ; antibiotique devant fievre et
   gene respiratoire ). Temoin : toujours l antibiotique ( la pratique grecque : ~33 DDD pour 1 000 habitants et par
   jour, parmi les plus hautes d Europe ). Porte : part du choix >= 0,01 en mode hasard, et la sante seule ( sans cout
   ni penalite ) des malades bacteriens repond au choix.
4. Evenements. Individuels : blessure, epidemie_declaree, rupture_sante, complication_grossesse, introduction.
   Comptes : infection, infection_importee, cas_symptomatique, hospitalisation, guerison, deces_medical, consultation,
   prescription_antibiotique, test_diagnostique, diagnostic_errone, effet_indesirable, vaccination, vaccin_manquant,
   peremption_sante, import_sante, decompensation, accident_travail, accident_route, episode_depressif,
   gastro_hydrique, reactivation_tb, traitement_chronique_manquant, sans_soin.
5. Liens. Remplace Monde.contagion ( chaque heure pleine : transmission par groupes de contact - menage, equipe de
   travail, classe, marche, loisir, culte, hopital -, frequence-dependante ), Monde.progression_maladie ( a l aube :
   cours clinique, decisions, soins, sante publique ) et Monde.soigner ( le soin par defaut ; le domaine 17 le
   remplacera par le sien et appellera l API ci-dessous ). R0 est cale sur le pays : la premiere semaine, les
   contacts reels ( heures par cadre, taille des groupes, journee des malades ) sont mesures, puis chaque maladie
   recoit le q pour lequel un cas moyen fait R0 infections, epuisement des petits groupes compris ; ensuite q ne
   bouge plus ( une quarantaine reduit vraiment la transmission ). L epidemie posee par le moteur ( trois E a Pyrgos )
   devient une grippe. Au depart, rhume, angine et gastro sont a leur regime permanent de la saison. Lit : population
   ( ages, sexe, grossesses, accouchements, deceder ), territoire ( eau : penurie du bassin, pollution de l eau, crues,
   temperature ), agenda s il est la ( ou chacun est, dans quel cadre ; replanifier a l hospitalisation ), la faim
   ( Habitant.faim : contagion x 1,5, letalite ), la pauvrete du menage ( sante mentale ). Accidents de fond du travail
   et de la route tant que les domaines 4, 10 et 14 ne les reprennent pas ( `reprendre_accidents` ). Neutralise par
   une donnee : la table de mortalite NATURELLE du domaine 1 perd la part des causes que ce domaine fait mourir
   lui-meme ( infections, accidents, suicides ; PART_CAUSES_MODELISEES ), sans quoi ces morts compteraient deux fois ;
   les complications, decompensations et effets graves ne tuent ici que quand le soin manque ( leur mortalite soignee
   est deja dans cette table ). Donne : `blesser`, `iss_depuis_ais`, `ais_balistique`, `reprendre_accidents`
   ( accidents, guerre ) ; `introduire`, `declencher`, `infecter`, `vacciner`, `forcer_saison`, `suivre_transmission`
   ( scenarios, etat ) ; `affections`, `symptomes_visibles`, `sante_du_jour`, `diagnostiquer`, `examiner`, `traiter`,
   `prendre`, `besoins`, `priorite`, `a_soigner`, `prise_en_charge`, `soigner_defaut`, `pharmacie_de`,
   `reprendre_chaine`, `resistance` ( hopitaux ) ; `risque_sante` ( assurance ) ; `vers_arma` ( pont ).
6. Portes : tests_d16_medecine.py.
7. Arma. Le malade et le blesse ont le corps de l habitant : `vers_arma` rend le niveau de dommage ( setDamage ) et
   l inconscience d un blesse critique ; arma_preuve = None, rien n a ete vu en jeu. Les ambulances, lits et
   equipements appartiennent au domaine 17.
8. Cout. La contagion ne touche, chaque heure, que les groupes ou se trouve un contagieux ( np.isin, bincount ) ;
   avec l agenda, les positions sont lues dans ses colonnes, sans boucle Python ; sans lui, une lecture de la
   population par heure ( comme Monde.contagion, qu elle remplace ). Une boucle par jour pour l index des groupes, une
   pour les accidents du travail ; decisions et soins sur les seuls malades ; l etalonnage de la premiere semaine suit
   au plus 200 000 habitants. Memoire : ~60 octets par habitant ( colonnes, tableaux n x 8 ), ~150 octets par
   affection en cours. Mesure du 23/09 ( test_cout, 10 000 habitants, rhume endemique ) : 1,69 s par jour pour
   population et territoire, 1,89 s avec la medecine ( +12 %, ~20 us par habitant ) : lineaire, ~20 s par jour a
   1 million, ~17 minutes a 50 millions avant portage en Rust."""
import math
import numpy as np
from .. import config as C
from ..socle import decision as D, biens as B
from . import d01_population as POP, d05_agenda as AG, d08_territoire as TER

JOURS_AN = 365.0
PAS_J = C.PAS_PAR_JOUR
INF = np.inf

# ================================================================== le moteur E1 : ce qu il lit de la sante
SEUIL_E1 = 0.10             # au-dela, le malade se sent malade : Habitant.etat = "I" ( l agenda le garde chez lui )
GRAVITE_HOPITAL = 0.3       # Monde.deplacer et l agenda : I et gravite > 0,3 -> hopital de sa capitale
GRAVITE_ALITE = 0.5         # Habitant.au_travail : I et gravite > 0,5 -> ne travaille pas
G_DEBUT = 0.25              # un cas qui va s aggraver commence modere, a la maison
G_GRAVE, G_CRITIQUE = (0.35, 0.8), (0.8, 1.0)
FRACTION_AGGRAVATION = 0.3  # l aggravation tombe au premier tiers de la maladie ( COVID : ~7 jours apres les symptomes )
G_CONVALESCENCE = 0.2       # un blesse sorti de sa phase aigue se remet chez lui
MALADIE_DU_MOTEUR = "grippe"   # les E poses par le moteur ( Monde.aube, epidemie_jour ) : une grippe
IMMUNITE_A_VIE = 2 ** 30

# ================================================================== les groupes de contact
CADRES = ("maison", "travail", "ecole", "commun", "loisir", "culte", "hopital")
MAISON_C, TRAVAIL_C, ECOLE_C, COMMUN_C, LOISIR_C, CULTE_C, HOPITAL_C = range(7)
# Contacts-equivalents par heure de presence dans le cadre ( un contact rapproche d une heure vaut 1 ). Ordres de
# grandeur de POLYMOD ( Mossong 2008 : ~13 contacts par jour, dont maison ~3,5, travail ~5, ecole ~8 ) ponderes par
# la duree et la proximite ; la maison est calee sur le taux d attaque secondaire des foyers ( COVID 16,6 %, Madewell
# 2020 ; grippe 10-20 %, Tsang 2016 ). A calibrer.
CONTACTS_H = np.array((0.06, 0.40, 1.00, 0.80, 1.00, 0.60, 0.30))
# La journee type d un habitant moyen ( heures par jour, moyenne de la semaine et de la population, a calibrer sur
# l enquete emploi du temps d ELSTAT ) : elle donne l exposition a priori, avant l etalonnage.
JOURNEE_TYPE = np.array((15.5, 3.4, 1.0, 0.25, 0.55, 0.05, 0.0))
EXPOSITION_A_PRIORI = float((CONTACTS_H * JOURNEE_TYPE).sum())   # contacts-equivalents par jour
JOURS_ETALONNAGE = 7        # R0 est defini sur les contacts REELS de ce pays : mesures sa premiere semaine, puis figes
ETALONNAGE_MAX = 200000     # au-dela, l etalonnage suit un echantillon d habitants ( memoire : 56 octets chacun )
TAILLE_EQUIPE = 20
TAILLE_CLASSE = 22          # classes grecques : ~20 eleves ( OCDE, Regards sur l education ), a calibrer
DECALAGE = 40
BIT_LIEU = 1 << 39
ACT_CADRE = {AG.MAISON: MAISON_C, AG.TRAVAIL: TRAVAIL_C, AG.ECOLE: ECOLE_C, AG.COURSES: COMMUN_C,
             AG.LOISIR: LOISIR_C, AG.CULTE: CULTE_C, AG.HOPITAL: HOPITAL_C}
CODE_POSTE = {"maison": AG.MAISON, "travail": AG.TRAVAIL, "hopital": AG.HOPITAL, "voyage": AG.VOYAGE,
              "trajet": AG.TRAJET, "courses": AG.COURSES, "loisir": AG.LOISIR, "culte": AG.CULTE}
SOIGNANTS = ("medecin", "infirmier")

# ================================================================== les symptomes visibles
SYMPTOMES = ("fievre", "toux", "gorge", "diarrhee", "vomissement", "eruption", "dyspnee", "douleur", "saignement",
             "fatigue", "odorat")
BIT = {s: 1 << k for k, s in enumerate(SYMPTOMES)}
BRUIT_SYMPTOME = 0.02       # un symptome sans rapport avec la maladie, vu quand meme ( pour le diagnostic )

# ================================================================== les soins recus par une affection ( bits )
SOUTIEN, SPECIFIQUE, ECHEC = 1, 2, 4
LATENTE, CONTAGIEUSE, CLINIQUE = 0, 1, 2
GROUPES = ("infection", "sporadique", "lesion", "grossesse", "decompensation", "iatrogene")


def par_age(table, ages):
    """Une valeur par age, lue dans une table en escalier ( ( age minimal, valeur ), ... ) triee."""
    seuils = np.array([a for a, _ in table], float)
    vals = np.array([v for _, v in table], float)
    k = np.searchsorted(seuils, np.asarray(ages, float), side="right") - 1
    return vals[np.maximum(k, 0)]


def interpole(table, ages):
    """Une valeur par age, interpolee lineairement entre les ancres ( prevalences des maladies chroniques )."""
    return np.interp(np.asarray(ages, float), [a for a, _ in table], [v for _, v in table])


class Pathologie:
    """Une pathologie : maladie infectieuse, infection sporadique, lesion, complication. Les durees sont des lois gamma
    ( moyenne, ecart-type, en jours ) ; la letalite et l hospitalisation sont des tables par age, PAR INFECTION
    ( ou par cas, pour ce qui n est pas transmissible ). Champs :
      r0              infections secondaires d un cas dans une population sans immunite ( 0 : non transmissible )
      latence         infection -> debut de la contagiosite ; presympt : contagiosite -> symptomes
      contagion       symptomes -> fin de la contagiosite ( sans traitement ) ; maladie : duree des symptomes
      asym, k_asym    part des infections sans symptome, et leur contagiosite relative
      ifr, ihr        deces et hospitalisations par infection, par age ( avec les soins standard )
      part_critique   part des cas graves qui sont critiques ( reanimation )
      saison          ( amplitude, jour du pic dans l annee ) : la transmission vaut 1 - amplitude au creux
      immunite_j      duree moyenne de l immunite apres guerison ( IMMUNITE_A_VIE : a vie )
      import_100k     cas importes par jour pour 100 000 habitants, au pic de saison
      g_legere        gravite d un cas leger ( ou de tout cas d une pathologie non infectieuse )
      symptomes       { symptome : probabilite chez un cas symptomatique }
      bacterie        un antibiotique agit ; aggravation : part des cas legers non traites qui s aggravent
      sans_specifique multiplicateur de letalite sans le traitement specifique ; sans_soutien : sans hopital
      table_d01       la mortalite AVEC soins est deja dans la table naturelle du domaine 1 : ce domaine ne tue que
                      quand le soin manque ( complications, decompensations )
      letal_legers    la letalite touche aussi les cas legers ( tuberculose, lesions )
      incidence       cas par an et par habitant, par age ( pathologie sporadique )
      progression     part des infections qui deviennent maladie ( tuberculose : 10 % ; les autres restent latentes )"""
    __slots__ = ("nom", "groupe", "r0", "latence", "presympt", "contagion", "maladie", "asym", "k_asym", "ifr", "ihr",
                 "part_critique", "saison", "immunite_j", "import_100k", "g_legere", "symptomes", "bacterie",
                 "aggravation", "sans_specifique", "sans_soutien", "mult_faim", "rr_chronique", "progression",
                 "letal_legers", "table_d01", "evidente", "cause", "incidence", "source")

    def __init__(self, nom, groupe, source, r0=0.0, latence=(0.0, 0.0), presympt=(0.0, 0.0), contagion=(0.0, 0.0),
                 maladie=(1.0, 0.0), asym=0.0, k_asym=1.0, ifr=((0, 0.0),), ihr=((0, 0.0),), part_critique=0.2,
                 saison=(0.0, 0), immunite_j=0.0, import_100k=0.0, g_legere=(0.1, 0.3), symptomes=None,
                 bacterie=False, aggravation=0.0, sans_specifique=1.0, sans_soutien=1.0, mult_faim=1.5,
                 rr_chronique=False, progression=1.0, letal_legers=False, table_d01=False, evidente=False,
                 cause="maladie", incidence=None):
        if groupe not in GROUPES: raise ValueError(f"{nom} : groupe inconnu {groupe!r}")
        for quoi, (m, s) in (("latence", latence), ("presympt", presympt), ("contagion", contagion),
                             ("maladie", maladie)):
            if not (0.0 <= m < 5000 and 0.0 <= s < 5000): raise ValueError(f"{nom} : {quoi} hors bornes")
        if not 0.0 <= r0 <= 30.0: raise ValueError(f"{nom} : R0 hors [0 ; 30]")
        if r0 > 0 and presympt[0] + contagion[0] <= 0: raise ValueError(f"{nom} : transmissible sans periode contagieuse")
        if not (0.0 <= asym <= 1.0 and 0.0 <= k_asym <= 1.0 and 0.0 <= part_critique <= 1.0):
            raise ValueError(f"{nom} : parts hors [0 ; 1]")
        for t in (ifr, ihr):
            if any(not 0.0 <= v <= 1.0 for _, v in t) or [a for a, _ in t] != sorted(a for a, _ in t):
                raise ValueError(f"{nom} : table par age")
        if not (0.0 <= saison[0] < 1.0 and 0 <= saison[1] < 366): raise ValueError(f"{nom} : saison hors bornes")
        if not (0.0 <= g_legere[0] <= g_legere[1] <= 1.0): raise ValueError(f"{nom} : gravite legere hors bornes")
        if not (0.0 <= aggravation <= 1.0 and 0.0 < progression <= 1.0 and sans_specifique >= 1.0 and sans_soutien >= 1.0
                and mult_faim >= 1.0 and immunite_j >= 0.0 and import_100k >= 0.0):
            raise ValueError(f"{nom} : parametre hors bornes")
        if cause not in POP.CAUSES: raise ValueError(f"{nom} : cause de deces inconnue {cause!r}")
        self.nom, self.groupe, self.source, self.r0 = nom, groupe, source, float(r0)
        self.latence, self.presympt, self.contagion, self.maladie = latence, presympt, contagion, maladie
        self.asym, self.k_asym, self.ifr, self.ihr, self.part_critique = asym, k_asym, ifr, ihr, part_critique
        self.saison, self.immunite_j, self.import_100k, self.g_legere = saison, immunite_j, import_100k, g_legere
        self.symptomes = dict(symptomes or {})
        if any(s not in BIT or not 0.0 <= v <= 1.0 for s, v in self.symptomes.items()):
            raise ValueError(f"{nom} : symptomes")
        self.bacterie, self.aggravation = bacterie, aggravation
        self.sans_specifique, self.sans_soutien, self.mult_faim = sans_specifique, sans_soutien, mult_faim
        self.rr_chronique, self.progression, self.letal_legers = rr_chronique, progression, letal_legers
        self.table_d01, self.evidente, self.cause, self.incidence = table_d01, evidente, cause, incidence

    @property
    def transmissible(self): return self.r0 > 0.0


def _ifr_covid():
    """Levin 2020 ( Eur J Epidemiol ) : log10( IFR % ) = -3,27 + 0,0524 x age, avant toute vaccination."""
    return tuple((a, min(1.0, 10 ** (-3.27 + 0.0524 * (a + 2.5)) / 100.0)) for a in range(0, 101, 5))


MALADIES = (
    Pathologie("grippe", "infection",
               "Biggerstaff 2014 ( R saisonnier median 1,28 ), Lessler 2009 ( incubation ), Leung 2015 ( 16 % "
               "d asymptomatiques ), CDC 2018-2019 ( letalite et hospitalisation par age ) ; pic de saison en "
               "janvier-fevrier ( surveillance grecque ), amplitude a calibrer",
               r0=1.3, latence=(1.0, 0.4), presympt=(0.6, 0.3), contagion=(4.0, 1.5), maladie=(5.0, 2.0),
               asym=0.16, k_asym=0.5,
               ifr=((0, 5e-5), (5, 2e-5), (18, 1e-4), (50, 5e-4), (65, 3e-3), (75, 8e-3), (85, 2e-2)),
               ihr=((0, 0.010), (5, 0.003), (18, 0.005), (50, 0.012), (65, 0.04), (75, 0.07), (85, 0.12)),
               part_critique=0.15, saison=(0.5, 35), immunite_j=700.0, import_100k=3.0, g_legere=(0.12, 0.30),
               symptomes={"fievre": 0.9, "toux": 0.85, "gorge": 0.6, "fatigue": 0.9, "dyspnee": 0.05},
               sans_soutien=2.0, rr_chronique=True),
    Pathologie("covid", "infection",
               "Liu 2020 ( R0 median 2,79 ), Li 2020 et Lauer 2020 ( incubation 5,1-5,2 j ), He 2020 ( contagiosite "
               "~2 j avant les symptomes ), Buitrago-Garcia 2022 ( asymptomatiques ~30 %, contagiosite relative "
               "0,35 ), Levin 2020 ( IFR par age ), Salje 2020 ( hospitalisation par age ) ; souche ancestrale, "
               "population sans immunite",
               r0=2.8, latence=(3.0, 1.0), presympt=(2.2, 1.0), contagion=(6.0, 2.0), maladie=(10.0, 4.0),
               asym=0.30, k_asym=0.35, ifr=_ifr_covid(),
               ihr=((0, 0.001), (20, 0.005), (30, 0.010), (40, 0.014), (50, 0.029), (60, 0.058), (70, 0.093), (80, 0.26)),
               part_critique=0.25, saison=(0.2, 15), immunite_j=365.0, import_100k=0.0, g_legere=(0.05, 0.30),
               symptomes={"fievre": 0.7, "toux": 0.65, "gorge": 0.3, "fatigue": 0.7, "dyspnee": 0.25, "diarrhee": 0.1,
                          "odorat": 0.4},
               sans_soutien=2.0, rr_chronique=True),
    Pathologie("rougeole", "infection",
               "Guerra 2017 ( R0 12-18 ), Lessler 2009 ( incubation 12,5 j jusqu au prodrome ), CDC Pink Book "
               "( contagieux 4 j avant et 4 j apres l eruption ; 1 a 3 deces pour 1 000 ), ECDC ( ~30 % des cas "
               "hospitalises en Europe ) ; la malnutrition multiplie la letalite ( a calibrer )",
               r0=15.0, latence=(9.5, 1.5), presympt=(2.0, 0.5), contagion=(7.0, 1.0), maladie=(10.0, 3.0),
               asym=0.0, k_asym=0.5,
               ifr=((0, 0.003), (1, 0.002), (5, 0.0005), (20, 0.002), (40, 0.003)),
               ihr=((0, 0.4), (5, 0.2), (20, 0.4)), part_critique=0.1, saison=(0.3, 90), immunite_j=IMMUNITE_A_VIE,
               import_100k=0.0004, g_legere=(0.15, 0.30),
               symptomes={"fievre": 1.0, "eruption": 0.98, "toux": 0.9, "fatigue": 0.8, "diarrhee": 0.1},
               sans_soutien=2.0, mult_faim=4.0),
    Pathologie("gastro", "infection",
               "norovirus : Lee 2013 ( incubation 1,2 j ), Steele 2020 et Heijne 2009 ( R 1,1-2 ), Qi 2018 ( ~30 % "
               "asymptomatiques ), Lopman 2011 ( deces des plus de 65 ans ) ; voie hydrique : Kovats 2004 ( +5 a 10 % "
               "par degre ) ; a calibrer",
               r0=1.6, latence=(0.9, 0.3), presympt=(0.3, 0.1), contagion=(2.5, 1.0), maladie=(2.0, 1.0),
               asym=0.30, k_asym=0.3,
               ifr=((0, 5e-5), (5, 1e-5), (65, 5e-4), (80, 2e-3)), ihr=((0, 0.01), (5, 0.003), (65, 0.02), (80, 0.05)),
               part_critique=0.1, saison=(0.3, 30), immunite_j=180.0, import_100k=2.0, g_legere=(0.10, 0.25),
               symptomes={"diarrhee": 0.9, "vomissement": 0.7, "fievre": 0.4, "douleur": 0.6, "fatigue": 0.5},
               sans_soutien=5.0),
    Pathologie("rhume", "infection",
               "rhinovirus : Lessler 2009 ( incubation 1,9 j ), Heikkinen 2003 ( 2 a 4 rhumes par adulte et par an, "
               "6 a 8 chez l enfant ) ; R0 et duree d immunite ( changement de serotype ) a calibrer sur l incidence",
               r0=1.8, latence=(1.2, 0.4), presympt=(0.5, 0.2), contagion=(5.0, 2.0), maladie=(7.0, 2.5),
               asym=0.25, k_asym=0.5, saison=(0.3, 290), immunite_j=60.0, import_100k=10.0, g_legere=(0.02, 0.09),
               symptomes={"gorge": 0.6, "toux": 0.5, "fievre": 0.15, "fatigue": 0.4}),
    Pathologie("angine", "infection",
               "streptocoque A : Shaikh 2010 ( prevalence ), Cohen 2016 Cochrane, Spinks 2021 Cochrane ( antibiotique : "
               "-16 h de symptomes, moins de complications, contagiosite arretee en 24 h ) ; toujours sensible a "
               "l amoxicilline ; R0 a calibrer",
               r0=1.4, latence=(2.0, 0.7), presympt=(1.0, 0.5), contagion=(10.0, 3.0), maladie=(6.0, 2.0),
               asym=0.30, k_asym=0.2, ifr=((0, 2e-5),), ihr=((0, 0.005),), saison=(0.3, 60), immunite_j=365.0,
               import_100k=1.0, g_legere=(0.08, 0.20),
               symptomes={"gorge": 0.95, "fievre": 0.8, "toux": 0.1, "douleur": 0.3, "fatigue": 0.5},
               bacterie=True, aggravation=0.01, sans_specifique=3.0),
    Pathologie("tuberculose", "infection",
               "Styblo 1985 ( ~10 infections par an et par cas contagieux ), Behr 2018 ( ~5-10 % des infectes "
               "deviennent malades, surtout dans les deux ans ), Tiemersma 2011 ( sans traitement ~3 ans de maladie, "
               "~70 % de deces a 10 ans ; traite ~5 % ), OMS 2022 ( Grece ~4 cas pour 100 000 par an ) ; a calibrer",
               r0=10.0, latence=(250.0, 150.0), presympt=(15.0, 7.0), contagion=(600.0, 300.0), maladie=(620.0, 300.0),
               asym=0.0, ifr=((0, 0.05),), ihr=((0, 0.3),), immunite_j=0.0, g_legere=(0.12, 0.30),
               symptomes={"toux": 0.95, "fievre": 0.6, "fatigue": 0.8, "saignement": 0.3, "dyspnee": 0.3},
               bacterie=True, sans_specifique=10.0, progression=0.10, letal_legers=True, rr_chronique=True),
    Pathologie("pneumonie", "sporadique",
               "pneumonie communautaire a pneumocoque : Welte 2012 ( incidence en Europe, 14 pour 1 000 apres 65 ans ), "
               "Fine 1996 ( mortalite ~1 % en ambulatoire, 5-15 % a l hopital ) ; sans antibiotique x3 ( a calibrer )",
               presympt=(2.0, 1.0), maladie=(10.0, 4.0),
               ifr=((0, 0.005), (18, 0.01), (50, 0.03), (65, 0.06), (80, 0.12)),
               ihr=((0, 0.3), (18, 0.25), (65, 0.5), (80, 0.75)), part_critique=0.2, g_legere=(0.15, 0.30),
               symptomes={"fievre": 0.85, "toux": 0.9, "dyspnee": 0.6, "douleur": 0.5, "fatigue": 0.9},
               bacterie=True, aggravation=0.25, sans_specifique=3.0, sans_soutien=1.5, rr_chronique=True,
               incidence=((0, 0.004), (5, 0.0007), (18, 0.0015), (50, 0.003), (65, 0.006), (75, 0.015))),
)
INFECTIEUSES = tuple(m.nom for m in MALADIES)          # l ordre des colonnes des tableaux n x M
M_INF = len(INFECTIEUSES)
IM = {n: k for k, n in enumerate(INFECTIEUSES)}
COMPLICATION_PNEUMONIE = {"grippe": 0.02, "rougeole": 0.05}   # surinfection bacterienne ( a calibrer )

# ------------------------------------------------------------------ lesions, complications, decompensations
TYPES_LESION = ("chute", "route", "travail", "ecrasement", "brulure", "balistique", "eclats", "arme_blanche")
PENETRANTES = ("balistique", "eclats", "arme_blanche")
SOURCE_LESION = ("mortalite par ISS : ordres de grandeur des registres de traumatologie ( TARN, NTDB ) ; sans soins x2,5 "
                 "( contondant ) a x4 ( penetrant ) ; a calibrer")
LESIONS = tuple(Pathologie("lesion_" + t, "lesion", SOURCE_LESION, g_legere=(0.0, 1.0),
                           symptomes={"douleur": 1.0, "saignement": 1.0 if t in PENETRANTES else 0.3},
                           sans_soutien=4.0 if t in PENETRANTES else 3.0 if t == "brulure" else 2.5,
                           letal_legers=True, evidente=True, cause="accident", mult_faim=1.0)
                for t in TYPES_LESION)
AUTRES = (
    Pathologie("pre_eclampsie", "grossesse", "3 % des grossesses apres 20 semaines ( Abalos 2013 ) ; eclampsie non "
               "traitee : ~2 % de deces maternels ( a calibrer ) ; sulfate de magnesium ( essai Magpie 2002 )",
               maladie=(60.0, 0.0), ifr=((0, 0.02),), g_legere=(0.35, 0.6), symptomes={"douleur": 0.5},
               letal_legers=True, table_d01=True, evidente=True, cause="maternelle", mult_faim=1.0),
    Pathologie("hemorragie_post_partum", "grossesse", "5 % des accouchements, 30 % de formes severes ( OMS 2012 ) ; "
               "sans oxytocine ni sang : ~3 % de deces des formes severes ( a calibrer )",
               maladie=(2.0, 0.5), ifr=((0, 0.01),), g_legere=(0.35, 0.7), symptomes={"saignement": 1.0},
               letal_legers=True, table_d01=True, evidente=True, cause="maternelle", mult_faim=1.0),
    Pathologie("crise_diabetique", "decompensation", "acidocetose : mortelle sans insuline, ~1-2 % traitee ( table du "
               "domaine 1 ) ; a calibrer", maladie=(7.0, 2.0), ifr=((0, 0.25),), g_legere=(0.4, 0.8),
               symptomes={"vomissement": 0.6, "fatigue": 1.0, "dyspnee": 0.4}, letal_legers=True, table_d01=True,
               evidente=True, mult_faim=1.0),
    Pathologie("avc", "decompensation", "accident vasculaire : ~15-20 % de deces a 30 jours avec soins ( table du "
               "domaine 1 ) ; sans soins, surmortalite a calibrer", maladie=(14.0, 5.0), ifr=((0, 0.15),),
               g_legere=(0.4, 0.9), symptomes={"fatigue": 1.0}, letal_legers=True, table_d01=True, evidente=True,
               mult_faim=1.0),
    Pathologie("decompensation_cardiaque", "decompensation", "insuffisance cardiaque aigue, infarctus : surmortalite "
               "sans soins a calibrer", maladie=(10.0, 3.0), ifr=((0, 0.2),), g_legere=(0.4, 0.9),
               symptomes={"dyspnee": 1.0, "douleur": 0.5, "fatigue": 1.0}, letal_legers=True, table_d01=True,
               evidente=True, mult_faim=1.0),
    Pathologie("exacerbation_bpco", "decompensation", "exacerbation severe de BPCO : surmortalite sans soins a calibrer",
               maladie=(10.0, 3.0), ifr=((0, 0.1),), g_legere=(0.35, 0.8),
               symptomes={"dyspnee": 1.0, "toux": 1.0, "fatigue": 0.8}, letal_legers=True, table_d01=True,
               evidente=True, mult_faim=1.0),
    Pathologie("effet_indesirable", "iatrogene", "diarrhee, eruption, nausees : effets courants des medicaments",
               maladie=(2.0, 1.0), g_legere=(0.04, 0.09), symptomes={"diarrhee": 0.6, "eruption": 0.3}, evidente=True),
    Pathologie("effet_indesirable_grave", "iatrogene", "anaphylaxie, colite a C. difficile, hepatite medicamenteuse : "
               "rares ; letalite sans soins a calibrer", maladie=(7.0, 3.0), ifr=((0, 0.05),), g_legere=(0.35, 0.6),
               symptomes={"diarrhee": 0.5, "eruption": 0.5, "dyspnee": 0.3}, letal_legers=True, table_d01=True,
               evidente=True),
)
PATHOS = MALADIES + LESIONS + AUTRES
IP = {m.nom: k for k, m in enumerate(PATHOS)}
K_ASYM = np.array([m.k_asym for m in PATHOS])
if len(IP) != len(PATHOS): raise RuntimeError("medecine : deux pathologies de meme nom")

# ================================================================== le terrain : maladies chroniques, sante mentale
DIABETE, INSULINE, HTA, CARDIO, BPCO = 1, 2, 4, 8, 16
CHRONIQUES = {DIABETE: "diabete", HTA: "hta", CARDIO: "cardio", BPCO: "bpco"}
# Prevalence par age ( ancres interpolees ). Diabete : IDF Atlas 2021 et etude EMENO 2015-2016 ; HTA : EMENO ( ~40 %
# des adultes ) ; cardiopathie ischemique et insuffisance cardiaque : EHIS 2019 ; BPCO : Tzanakis 2004 ( 8,4 % des 35
# ans et plus ). Ordres de grandeur, a calibrer.
PREVALENCE_CHRONIQUE = {
    DIABETE: ((0, 0.002), (18, 0.005), (30, 0.01), (45, 0.05), (55, 0.11), (65, 0.18), (75, 0.23), (85, 0.22)),
    HTA: ((0, 0.0), (18, 0.02), (30, 0.06), (45, 0.20), (55, 0.35), (65, 0.52), (75, 0.63), (85, 0.66)),
    CARDIO: ((0, 0.0), (18, 0.002), (30, 0.004), (45, 0.02), (55, 0.05), (65, 0.10), (75, 0.18), (85, 0.25)),
    BPCO: ((0, 0.0), (18, 0.003), (30, 0.01), (45, 0.04), (55, 0.08), (65, 0.12), (75, 0.15), (85, 0.16)),
}
PART_INSULINE = 0.25        # diabetiques sous insuline ( type 1 et type 2 insulino-requerants ), a calibrer
PART_TRAITES = {DIABETE: 0.85, HTA: 0.65, CARDIO: 0.85, BPCO: 0.5}   # EMENO : ~70 % des hypertendus connus traites
TRAITEMENT_CHRONIQUE = ((DIABETE | INSULINE, "insuline"), (DIABETE, "antidiabetique"), (HTA, "antihypertenseur"),
                        (CARDIO, "antihypertenseur"), (BPCO, "bronchodilatateur"))
# Risque relatif de deces par infection respiratoire ( COVID : meta-analyses 2020-2021, ordre de grandeur )
RR_CHRONIQUE = {DIABETE: 1.6, HTA: 1.2, CARDIO: 2.0, BPCO: 2.0}
RR_GROSSESSE = 2.0          # grippe et COVID graves chez la femme enceinte ( a calibrer )
RR_PNEUMONIE = {BPCO: 3.0, DIABETE: 1.5, CARDIO: 2.0}   # incidence de la pneumonie communautaire ( Torres 2013, a calibrer )
# Decompensations : ( bit, pathologie, par an sous traitement, par an sans traitement )
DECOMPENSATIONS = ((DIABETE, "crise_diabetique", 0.01, 0.05), (HTA, "avc", 0.004, 0.008),
                   (CARDIO, "decompensation_cardiaque", 0.05, 0.10), (BPCO, "exacerbation_bpco", 0.10, 0.15))
SEVRAGE_INSULINE_J = 2      # au-dela, sans insuline, la crise menace chaque jour
CRISE_SANS_INSULINE_J = 0.15
# Sante mentale ( bits de med_mental ) : episode depressif et anxiete generalisee
DEPRESSION, ANXIETE, DEP_TRAITEE = 1, 2, 4
PREVALENCE_DEPRESSION, PREVALENCE_ANXIETE = 0.06, 0.05    # EHIS 2019 Grece, ordre de grandeur, a calibrer
DUREE_DEPRESSION_J, DUREE_ANXIETE_J = 180.0, 365.0
# Risques relatifs d un episode : faim, pauvrete ( Paul et Moser 2009 : chomage x2 ), maladie chronique, femme ; a calibrer
RR_FAIM_MENTAL, RR_PAUVRE_MENTAL, RR_CHRONIQUE_MENTAL, RR_FEMME_MENTAL = 2.0, 1.8, 1.5, 1.6
PART_DEPRESSION_TRAITEE = 0.4
SUICIDE_AN_DEPRIME = 4e-4   # Grece ~4-5 suicides pour 100 000 par an ; ~60 % avec depression ( a calibrer )
# Tuberculose latente au depart ( part par age ) et reactivation annuelle
TB_LATENTE = ((0, 0.002), (15, 0.01), (45, 0.04), (65, 0.10))
REACTIVATION_TB_AN = 0.001

# La part des deces de la table naturelle ( domaine 1 ) que CE domaine fait mourir lui-meme : infections aigues
# ( grippe, pneumonie, septicemies ), accidents de la route et du travail, suicides. Ordre de grandeur des causes de
# deces d ELSTAT ( 2019 ) : ~6 % apres 65 ans ; ~1/4 de 15 a 39 ans ( route, suicide ). A calibrer.
PART_CAUSES_MODELISEES = ((0, 0.08), (15, 0.25), (40, 0.07), (65, 0.07))

# ================================================================== accidents de fond ( sans domaine qui les reprenne )
# Accidents du travail avec arret, pour 100 000 travailleurs et par an ( ESAW, ordres de grandeur, a calibrer )
ACCIDENTS_TRAVAIL = {"mineur": 3000, "petrolier": 2000, "ouvrier": 1800, "paysan": 1500, "convoyeur": 1200,
                     "soldat": 800, "policier": 600, "marchand": 300, "infirmier": 500, "medecin": 200,
                     "enseignant": 200, "patron": 200, "officier": 300, "ministre": 100, "chef_gouvernement": 100}
JOURS_OUVRES_AN = 250.0
ISS_TRAVAIL = (((1, 4), 0.70), ((5, 9), 0.268), ((10, 24), 0.03), ((25, 50), 0.002))   # ~1-5 deces pour 100 000 travailleurs
# Route : ~11 700 victimes et ~600 tues par an pour 10,4 millions ( ELSTAT 2022 ) ; ~5 % des victimes meurent
ROUTE_VICTIMES_100K_AN = 110.0
ISS_ROUTE = (((1, 8), 0.76), ((9, 15), 0.12), ((16, 24), 0.05), ((25, 49), 0.02), ((50, 75), 0.05))
LETAL_ISS = ((1, 0.0002), (4, 0.001), (9, 0.015), (16, 0.07), (25, 0.25), (41, 0.55), (75, 1.0))
PART_AIGUE = 0.6            # sans soins, la plupart des morts d un blesse grave tombent dans les premieres heures

# ================================================================== l eau et la gastro-enterite
GASTRO_EAU_AN = 0.10        # episodes d origine hydrique ou alimentaire par personne et par an, eau normale ( a calibrer )
K_PENURIE, K_POLLUTION, K_CRUE, K_TEMPERATURE, T_SEUIL = 4.0, 2.0, 5.0, 0.05, 18.0


# ================================================================== diagnostic
class Examen:
    """Un examen : la pathologie qu il cherche, sa sensibilite et sa specificite, ou il se fait."""
    __slots__ = ("nom", "cible", "sensibilite", "specificite", "lieu", "source")

    def __init__(self, nom, cible, sensibilite, specificite, lieu, source):
        if (cible not in IP or not (0.5 <= sensibilite <= 1.0 and 0.5 <= specificite <= 1.0)
                or lieu not in ("cabinet", "hopital")):
            raise ValueError(f"examen {nom} hors bornes")
        self.nom, self.cible, self.sensibilite, self.specificite = nom, cible, sensibilite, specificite
        self.lieu, self.source = lieu, source


EXAMENS = (
    Examen("tdr_grippe", "grippe", 0.62, 0.98, "cabinet", "Chartrand 2012 ( Ann Intern Med )"),
    Examen("antigene_covid", "covid", 0.73, 0.996, "cabinet", "Dinnes 2022 ( Cochrane, symptomatiques )"),
    Examen("pcr_covid", "covid", 0.90, 0.99, "hopital", "ordre de grandeur, a calibrer"),
    Examen("tdr_strep", "angine", 0.86, 0.95, "cabinet", "Cohen 2016 ( Cochrane )"),
    Examen("radio_thorax", "pneumonie", 0.77, 0.90, "cabinet", "Self 2013 ( sensibilite contre scanner ), a calibrer"),
    Examen("igm_rougeole", "rougeole", 0.83, 0.95, "hopital", "a calibrer"),
    Examen("crachat_bk", "tuberculose", 0.60, 0.98, "cabinet", "Steingart 2006"),
    Examen("xpert_tb", "tuberculose", 0.85, 0.98, "hopital", "Horne 2019 ( Cochrane )"),
)
EX = {e.nom: e for e in EXAMENS}
EXAMEN_DE = {}
for _e in EXAMENS: EXAMEN_DE.setdefault(_e.cible, []).append(_e.nom)
# Ce que le medecin attend sans rien savoir d autre : poids relatifs des consultations pour chaque maladie ( a calibrer )
A_PRIORI = {"rhume": 30.0, "grippe": 4.0, "covid": 1.0, "gastro": 10.0, "angine": 6.0, "pneumonie": 2.0,
            "rougeole": 0.05, "tuberculose": 0.05}


def resultat_examen(ex, malade, u):
    """Le resultat d un examen pour des patients dont on sait ( ici, pas le medecin ) s ils ont la cible : un vrai
    malade est positif avec la probabilite `sensibilite`, un non-malade avec 1 - `specificite`."""
    malade = np.asarray(malade, bool)
    return np.where(malade, u < ex.sensibilite, u < 1.0 - ex.specificite)


def vraisemblances(masque):
    """Pour un masque de symptomes vus : { maladie : P( ces symptomes | maladie ) } ( independance conditionnelle )."""
    out = {}
    for nom in A_PRIORI:
        m = PATHOS[IP[nom]]
        v = 1.0
        for s, b in BIT.items():
            ps = m.symptomes.get(s, BRUIT_SYMPTOME)
            v *= ps if masque & b else (1.0 - ps)
        out[nom] = v
    return out


def diagnostic_clinique(masque, a_priori):
    """Le diagnostic le plus probable au vu des seuls symptomes ( Bayes naif ), et les candidats tries."""
    v = vraisemblances(masque)
    post = {n: v[n] * a_priori.get(n, 0.0) for n in v}
    tri = sorted(post, key=lambda n: (-post[n], n))
    return tri[0], tri


# ================================================================== produits de sante
class Molecule:
    """Un produit de sante, declare comme bien du catalogue ( famille sante ). unite : ce que compte le stock ;
    prix : drachmes par unite au port ( ~ euros, a calibrer ) ; ddd : doses definies journalieres OMS par unite
    ( antibiotiques ) ; indesirables : ( probabilite d un effet leger, d un effet grave ) par traitement ;
    provenance : importe, ou don ( le sang )."""
    __slots__ = ("nom", "classe", "unite", "prix", "conservation_j", "ddd", "indesirables", "provenance", "masse_kg",
                 "volume_l", "source")

    def __init__(self, nom, classe, unite, prix, conservation_j, ddd=0.0, indesirables=(0.0, 0.0), provenance="importe",
                 masse_kg=0.02, volume_l=0.05, source="a calibrer"):
        if not prix > 0 or not conservation_j > 0 or ddd < 0 or not all(0.0 <= x <= 1.0 for x in indesirables):
            raise ValueError(f"molecule {nom} hors bornes")
        if provenance not in ("importe", "don"): raise ValueError(f"{nom} : provenance {provenance!r}")
        self.nom, self.classe, self.unite, self.prix, self.conservation_j = nom, classe, unite, prix, conservation_j
        self.ddd, self.indesirables, self.provenance, self.masse_kg, self.volume_l, self.source = \
            ddd, indesirables, provenance, masse_kg, volume_l, source


MOLECULES = (
    Molecule("amoxicilline", "antibiotique", "dose-jour de 3 g ( 2 DDD )", 0.6, 730, 2.0, (0.08, 0.001),
             source="OMS ATC/DDD ( J01CA04 : DDD 1,5 g ) ; diarrhee 5-10 % ; prix a calibrer"),
    Molecule("ceftriaxone", "antibiotique", "dose-jour de 2 g injectable ( 1 DDD )", 3.0, 730, 1.0, (0.05, 0.002)),
    Molecule("antituberculeux", "antibiotique", "dose-jour de l association RHZE", 0.5, 730, 1.0, (0.10, 0.01)),
    Molecule("oseltamivir", "antiviral", "dose-jour ( 2 x 75 mg )", 6.0, 1825, 0.0, (0.10, 0.0)),
    Molecule("antiviral_covid", "antiviral", "dose-jour ( nirmatrelvir-ritonavir )", 100.0, 730, 0.0, (0.05, 0.0)),
    Molecule("paracetamol", "antalgique", "dose-jour de 3 g", 0.1, 1095),
    Molecule("morphine", "antalgique", "dose-jour injectable", 1.0, 730, 0.0, (0.10, 0.002)),
    Molecule("sro", "soutien", "sachet-jour de sels de rehydratation orale", 0.2, 1095),
    Molecule("oxygene", "soutien", "jour d oxygenotherapie ( ~3 m3 )", 5.0, 3650, masse_kg=4.0, volume_l=5.0),
    Molecule("corticoide", "soutien", "dose-jour de dexamethasone 6 mg", 0.2, 1095, 0.0, (0.02, 0.0)),
    Molecule("anesthesique", "soutien", "anesthesie d une intervention", 20.0, 730),
    Molecule("insuline", "chronique", "dose-jour ( ~40 UI )", 1.0, 730),
    Molecule("antidiabetique", "chronique", "dose-jour de metformine", 0.1, 1095),
    Molecule("antihypertenseur", "chronique", "dose-jour", 0.1, 1095),
    Molecule("bronchodilatateur", "chronique", "dose-jour inhalee", 0.5, 730),
    Molecule("antidepresseur", "chronique", "dose-jour d ISRS", 0.2, 1095),
    Molecule("vaccin_ror", "vaccin", "dose ( rougeole, oreillons, rubeole )", 20.0, 730, masse_kg=0.01),
    Molecule("vaccin_grippe", "vaccin", "dose saisonniere", 8.0, 240, masse_kg=0.01),
    Molecule("vaccin_covid", "vaccin", "dose", 20.0, 180, masse_kg=0.01),
    Molecule("sang", "sang", "culot globulaire", 100.0, 42, provenance="don", masse_kg=0.3, volume_l=0.3,
             source="conservation des culots : 42 jours ; ~58 dons pour 1 000 habitants et par an en Grece ( a verifier )"),
    Molecule("sulfate_magnesium", "obstetrique", "dose-jour", 1.0, 1095),
    Molecule("oxytocine", "obstetrique", "dose", 1.0, 730),
)
MOL = {m.nom: m for m in MOLECULES}
NOMS_MOL = tuple(m.nom for m in MOLECULES)
IMOL = {n: k for k, n in enumerate(NOMS_MOL)}
DONS_SANG_AN = 0.058        # culots par habitant et par an
PARTICIPATION = 0.25        # part du prix payee par le patient en ville ( EOPYY : 0, 10 ou 25 % selon le produit )
TARIF_CONSULTATION = 10.0   # drachmes ( a calibrer : gratuit au centre de sante, 20-50 EUR en cabinet prive )
STOCK_CIBLE_J = 60          # jours de consommation que la pharmacie vise
DELAI_LIVRAISON_J = 3
# Consommation attendue par 1 000 habitants et par jour, pour le premier stock ( a calibrer ; relayee ensuite par la
# consommation mesuree )
CONSO_A_PRIORI = {"amoxicilline": 8.0, "ceftriaxone": 0.5, "antituberculeux": 0.05, "oseltamivir": 0.5,
                  "antiviral_covid": 0.05, "paracetamol": 5.0, "morphine": 0.2, "sro": 1.0, "oxygene": 0.5,
                  "corticoide": 0.3, "anesthesique": 0.1, "insuline": 22.0, "antidiabetique": 60.0,
                  "antihypertenseur": 210.0, "bronchodilatateur": 25.0, "antidepresseur": 25.0, "vaccin_ror": 0.05,
                  "vaccin_grippe": 0.5, "vaccin_covid": 0.05, "sang": 0.16, "sulfate_magnesium": 0.01,
                  "oxytocine": 0.05}


class Effet:
    """Ce qu une molecule fait a une pathologie. f_letal : multiplicateur de la letalite ; f_duree : du reste de la
    maladie ; fin_contagion_j : la contagiosite cesse ce nombre de jours apres le debut ; fenetre_j : l effet n existe
    que si le traitement commence avant ce delai depuis les symptomes ; prevention : probabilite que l aggravation
    survienne malgre un traitement precoce ; specifique : le traitement de reference de la pathologie ; cure_j :
    duree d un traitement qui guerit ( tuberculose )."""
    __slots__ = ("f_letal", "f_duree", "fin_contagion_j", "fenetre_j", "prevention", "specifique", "cure_j")

    def __init__(self, f_letal=1.0, f_duree=1.0, fin_contagion_j=None, fenetre_j=None, prevention=None,
                 specifique=False, cure_j=None):
        self.f_letal, self.f_duree, self.fin_contagion_j, self.fenetre_j = f_letal, f_duree, fin_contagion_j, fenetre_j
        self.prevention, self.specifique, self.cure_j = prevention, specifique, cure_j


EFFETS = {
    ("grippe", "oseltamivir"): Effet(0.7, 0.8, fenetre_j=2.0, prevention=0.7),      # Jefferson 2014 ( -17 h )
    ("covid", "antiviral_covid"): Effet(0.15, 1.0, fenetre_j=5.0, prevention=0.11),     # EPIC-HR 2022 ( -89 % )
    ("covid", "corticoide"): Effet(0.83),                                                 # RECOVERY 2021
    ("pneumonie", "amoxicilline"): Effet(prevention=0.5, specifique=True),
    ("pneumonie", "ceftriaxone"): Effet(prevention=0.5, specifique=True),
    ("angine", "amoxicilline"): Effet(1.0, 0.8, fin_contagion_j=1.0, specifique=True),
    ("angine", "ceftriaxone"): Effet(1.0, 0.8, fin_contagion_j=1.0, specifique=True),
    ("tuberculose", "antituberculeux"): Effet(fin_contagion_j=14.0, specifique=True, cure_j=180.0),
    ("gastro", "sro"): Effet(0.3),
    ("pre_eclampsie", "sulfate_magnesium"): Effet(specifique=True),
    ("hemorragie_post_partum", "oxytocine"): Effet(specifique=True),
    ("crise_diabetique", "insuline"): Effet(specifique=True),
    ("avc", "antihypertenseur"): Effet(specifique=True),
    ("decompensation_cardiaque", "antihypertenseur"): Effet(specifique=True),
    ("exacerbation_bpco", "bronchodilatateur"): Effet(specifique=True),
    ("exacerbation_bpco", "corticoide"): Effet(0.8),
    ("effet_indesirable_grave", "corticoide"): Effet(specifique=True),
}
# Ce que l hopital donne pour un diagnostic : ( molecule, unites, essentielle ). Le kit du moteur ( remedes ) et
# l oxygene d un malade respiratoire grave font le soin de soutien.
PROTOCOLE_HOPITAL = {
    "grippe": (("oseltamivir", 5, False),), "covid": (("corticoide", 10, False),),
    "pneumonie": (("ceftriaxone", 7, True),), "angine": (("amoxicilline", 7, True),), "rougeole": (),
    "gastro": (("sro", 3, False),), "rhume": (), "tuberculose": (("antituberculeux", 30, True),),
    "pre_eclampsie": (("sulfate_magnesium", 2, True), ("antihypertenseur", 7, False)),
    "hemorragie_post_partum": (("oxytocine", 2, True),), "crise_diabetique": (("insuline", 7, True),),
    "avc": (("antihypertenseur", 7, True),), "decompensation_cardiaque": (("antihypertenseur", 7, True),),
    "exacerbation_bpco": (("bronchodilatateur", 7, True), ("corticoide", 5, False)),
    "effet_indesirable_grave": (("corticoide", 3, True),), "effet_indesirable": (),
}
RESPIRATOIRES = ("grippe", "covid", "pneumonie", "rougeole", "tuberculose", "exacerbation_bpco", "decompensation_cardiaque")
COURS_ANTIBIOTIQUE = 7      # dose-jours d amoxicilline en ville
RENOUVELLEMENT_TB = (30, 5) # 30 dose-jours par mois, cinq renouvellements apres le premier mois


class Antibiotique:
    """La loi de la resistance d un antibiotique : dr/dt = kappa ( u ( 1 - r ) - K r ), u en DDD pour 1 000 habitants
    et par jour. Equilibre r* = u / ( u + K ) : cale pour que l usage grec de reference donne la resistance grecque
    mesuree ; tau : annees pour s approcher de l equilibre ( constante de temps ). Goossens 2005 ( Lancet ) : la
    resistance suit l usage d un pays a l autre d Europe."""
    __slots__ = ("nom", "u_ref", "r_ref", "tau_ans", "K", "kappa", "source")

    def __init__(self, nom, u_ref, r_ref, tau_ans, source):
        if not (u_ref > 0 and 0 < r_ref < 1 and tau_ans > 0): raise ValueError(f"antibiotique {nom} hors bornes")
        self.nom, self.u_ref, self.r_ref, self.tau_ans, self.source = nom, u_ref, r_ref, tau_ans, source
        self.K = u_ref * (1.0 - r_ref) / r_ref
        self.kappa = 1.0 / (tau_ans * JOURS_AN * (u_ref + self.K))

    def pas(self, r, u, jours=1.0):
        """La resistance apres `jours` jours a l usage u ( solution exacte de l equation lineaire )."""
        u = np.maximum(0.0, u)
        eq = u / (u + self.K)
        return eq + (r - eq) * np.exp(-self.kappa * (u + self.K) * jours)


ANTIBIOTIQUES = (
    Antibiotique("amoxicilline", 13.0, 0.25, 3.0, "ECDC ESAC-Net 2019 ( Grece : ~13 DDD de penicillines en ville ) et "
                 "EARS-Net ( pneumocoque non sensible a la penicilline ~25 % ) : ordres de grandeur, a verifier"),
    Antibiotique("ceftriaxone", 2.5, 0.05, 3.0,
                 "cephalosporines de 3e generation ; resistance du pneumocoque ~5 %, a verifier"),
    Antibiotique("antituberculeux", 0.05, 0.03, 5.0, "tuberculose multiresistante en Grece ~3 % ( ECDC ), a verifier"),
)
ABX = {a.nom: a for a in ANTIBIOTIQUES}
IABX = {a.nom: k for k, a in enumerate(ANTIBIOTIQUES)}
EMA_USAGE_J = 90.0          # l usage qui selectionne : moyenne mobile sur trois mois ( a calibrer )
POIDS_RESISTANCE = 0.10     # la note du prescripteur perd 0,1 par traitement de 14 DDD ( a calibrer )
DDD_COURS_REF = 14.0
# La resistance ne concerne que le germe de la pathologie : le streptocoque A reste sensible a l amoxicilline.
GERME_RESISTANCE = {"pneumonie": 1.0, "angine": 0.0, "tuberculose": 1.0}

# ================================================================== vaccination
VACCINS = ("ror", "grippe", "covid")
COUVERTURE_ROR = (0.97, 0.83)       # OMS/UNICEF WUENIC 2022, Grece : RCV1 ~97 %, RCV2 ~83 % ( a verifier )
EFFICACITE_ROR = (0.93, 0.97)       # CDC : une dose 93 %, deux doses 97 %
AGE_ROR_J = (365, 5 * 365)
ADULTES_IMMUNS_ROUGEOLE = 0.95      # nes avant la vaccination generale ou vaccines ( a calibrer )
PROTECTION_MATERNELLE_J = 270
COUVERTURE_GRIPPE = 0.60            # plus de 65 ans et malades chroniques ( OCDE, ordre de grandeur, a verifier )
EFFICACITE_GRIPPE = 0.5             # efficacite vaccinale moyenne ( CDC, 40-60 % )
CAMPAGNE_GRIPPE = (274, 365)        # du 1er octobre au 31 decembre ( jour de l annee )

# ================================================================== decisions
JOURS_DECISION = (1, 3, 7, 14, 21, 28)
HORIZON_SOINS = 7
COUT_NOTE_CONSULTATION = 0.05       # une demi-journee et une consultation ( a calibrer )
SANS, ANTIBIOTIQUE, TESTER = 0, 1, 2


# ================================================================== l etat
class Affections:
    """La table EPARSE des affections en cours : une ligne par ( habitant, affection ), des tableaux numpy qui
    grandissent par doublement ; une ligne liberee est reprise ( `gen` dit sa generation : une echeance qui vise une
    ligne reprise est ignoree ). Temps en jours du monde ( minutes / 1 440 ) : t0 l infection ( ou l accident ),
    t_inf le debut de la contagiosite, t_symp des symptomes, t_aggr de l aggravation ( ou la fin de la phase aigue d une
    lesion ), t_gueri la fin des symptomes ( l issue se tire la ), t_fin_cont la fin de la contagiosite, t_fin la fin de
    l infection ( un porteur gueri peut rester contagieux, comme l angine non traitee )."""
    CHAMPS = (("hab", np.int32, -1), ("path", np.int16, -1), ("phase", np.int8, 0), ("actif", np.bool_, False),
              ("t0", np.float64, 0.0), ("t_inf", np.float64, INF), ("t_symp", np.float64, INF),
              ("t_aggr", np.float64, INF), ("t_gueri", np.float64, INF), ("t_fin_cont", np.float64, -INF),
              ("t_fin", np.float64, INF),
              ("asym", np.bool_, False), ("g", np.float32, 0.0), ("g2", np.float32, 0.0), ("gmax", np.float32, 0.0),
              ("letal", np.float32, 0.0), ("mult", np.float32, 1.0), ("prev", np.float32, 1.0),
              ("u_issue", np.float32, 1.0), ("u2", np.float32, 1.0), ("soin", np.int8, 0), ("consulte", np.int8, 0),
              ("diag", np.int16, -1), ("resistant", np.bool_, False), ("symp", np.int16, 0), ("iss", np.int16, 0),
              ("cause", np.int8, 0), ("sang", np.int8, 0), ("infecteur", np.int32, -1), ("gen", np.int32, 0),
              ("region", np.int16, 0))
    __slots__ = tuple(c for c, _, _ in CHAMPS) + ("cap", "k", "libres")

    def __init__(self, cap=256):
        self.cap, self.k, self.libres = cap, 0, []
        for c, dt, d in self.CHAMPS: setattr(self, c, np.full(cap, d, dtype=dt))

    def allouer(self):
        if self.libres: s = self.libres.pop()
        else:
            s = self.k; self.k += 1
            if self.k > self.cap:
                cap = 2 * self.cap
                for c, dt, d in self.CHAMPS:
                    a = np.full(cap, d, dtype=dt); a[:self.cap] = getattr(self, c); setattr(self, c, a)
                self.cap = cap
        g = int(self.gen[s]) + 1
        for c, dt, d in self.CHAMPS: getattr(self, c)[s] = d
        self.gen[s] = g; self.actif[s] = True
        return s

    def liberer(self, s):
        self.actif[s] = False; self.libres.append(s)

    def n_actives(self): return int(self.actif[:self.k].sum())


class Pharmacie:
    """Les produits de sante d une capitale ( la pharmacie de son hopital ) : un stock du socle, par lots ranges par date
    de peremption ( ce qui perime le plus tot sort le premier ). conso : consommation mesuree ( unites par jour, moyenne
    mobile sur 30 jours ) ; sortie_jour : ce qui est sorti aujourd hui ; pop : habitants servis."""
    __slots__ = ("id", "lieu", "stock", "lots", "conso", "pop", "sortie_jour")

    def __init__(self, id, lieu, stock, n_mol):
        self.id, self.lieu, self.stock = id, lieu, stock
        self.lots = {}                      # identifiant de bien -> [ [ quantite, jour de peremption ], ... ] FIFO
        self.conso = np.zeros(n_mol); self.sortie_jour = np.zeros(n_mol); self.pop = 0


class IndexDuJour:
    """Ce que le domaine lit des habitants a 6 h, une fois par jour : groupes de contact, lieux, ages, faim."""
    __slots__ = ("n", "jour", "men", "equipe", "classe", "soignant", "enfant", "dom", "hop", "region", "age", "sexe",
                 "faim", "vivant", "role", "enceinte", "pauvre")


class Medecine:
    __slots__ = ("aff", "par_hab", "cap", "n_init", "statut", "immun_fin", "infecte", "deja", "doses", "vacc_saison",
                 "pharmacies", "region_de_lieu", "lieux", "index_lieu", "lieu_bassin", "resistance", "usage", "ddd_jour",
                 "declares", "q", "expo_ref", "expo_malade", "expo_heures", "jour0", "saison_forcee", "reprises",
                 "cal_pos", "cal_h", "cal_n", "cal_hI", "cal_malades_h",
                 "chaine_externe", "dec_consulter", "dec_prescrire", "ix", "compteurs", "tues", "suivi", "epidemies",
                 "cas_jour", "id_mol", "traces")

    def compter(self, cle, v=1):
        self.compteurs[cle] = self.compteurs.get(cle, 0) + v


# ================================================================== les objets qui prennent la place du moteur
class RemplaceContagion:
    """Prend la place de Monde.contagion ( chaque heure pleine ) : un objet, pour rester picklable."""
    __slots__ = ("pays",)
    def __init__(self, pays): self.pays = pays
    def __call__(self): _contagion(self.pays)


class RemplaceProgression:
    """Prend la place de Monde.progression_maladie ( a l aube, avant que le moteur ne place chacun ) : le cours clinique
    du jour, les decisions, les soins, les routines de sante publique."""
    __slots__ = ("pays",)
    def __init__(self, pays): self.pays = pays
    def __call__(self): _journee(self.pays)


class RemplaceSoigner:
    """Prend la place de Monde.soigner( h ) : le soin par defaut, tant que le domaine 17 ( hopitaux ) ne le reprend pas.
    Le domaine 17 posera sa propre methode sur w.soigner et appellera l API de ce domaine."""
    __slots__ = ("pays",)
    def __init__(self, pays): self.pays = pays
    def __call__(self, h): return soigner_defaut(self.pays, h)


# ================================================================== petits outils
def _gamma(rng, loi, n):
    m, s = loi
    if s <= 0 or m <= 0: return np.full(n, float(m))
    return rng.gamma((m / s) ** 2, s * s / m, n)


def duree_contagieuse(m):
    """Jours de contagiosite ponderes d une infection moyenne : ( presymptomatique + contagion ) x ( part symptomatique
    + part asymptomatique x contagiosite relative )."""
    return (m.presympt[0] + m.contagion[0]) * (1.0 - m.asym + m.asym * m.k_asym)


def q_contact(m, exposition_j):
    """La probabilite de transmission par contact-equivalent : R0 = q x exposition quotidienne x duree contagieuse."""
    return m.r0 / (exposition_j * duree_contagieuse(m)) if m.r0 > 0 else 0.0


def taux_par_membre(q, c, pression, taille):
    """Le taux horaire d infection de chaque membre d un groupe : q x contacts par heure du cadre x contagiosite
    presente / ( taille - 1 ). Frequence-dependant : un contagieux fait q x c infections par heure, quelle que soit la
    taille du groupe ; seul dans son groupe, il n en fait aucune."""
    return q * c * pression / np.maximum(1.0, np.asarray(taille, float) - 1.0)


def facteur_saison(m, jour_an, force=None):
    """La transmission du jour relativement au pic de saison : 1 au pic, 1 - amplitude au creux."""
    if force is not None: return float(force)
    a, pic = m.saison
    if a <= 0: return 1.0
    return 1.0 - a * (1.0 - math.cos(2 * math.pi * (jour_an - pic) / 365.0)) / 2.0


def _jour_an(p):
    return p.socle.calendrier.date(p.w.pas).timetuple().tm_yday - 1


def tirer_histoires(m, t, ages, rng, rr=None):
    """L histoire naturelle de n nouvelles infections ( ou cas ) de la maladie m, commencees au temps t ( jours ).
    rr : risque relatif de deces de chacun ( maladies chroniques, grossesse ), reparti entre gravite et letalite.
    Rend un dictionnaire de tableaux, un element par infection."""
    n = len(ages)
    ages = np.asarray(ages, float)
    rr = np.ones(n) if rr is None else np.asarray(rr, float)
    L = _gamma(rng, m.latence, n); P = _gamma(rng, m.presympt, n)
    Dc = _gamma(rng, m.contagion, n); Dm = _gamma(rng, m.maladie, n)
    asym = rng.random(n) < m.asym
    t_inf = t + L if m.transmissible else np.full(n, INF)
    t_symp = t + L + P
    t_fin_cont = t_symp + Dc if m.transmissible else np.full(n, -INF)
    t_gueri = np.where(asym, INF, t_symp + Dm)
    t_fin = np.where(asym, t_fin_cont, np.maximum(t_gueri, t_fin_cont))
    sympt = max(1e-9, 1.0 - m.asym)
    ifr, ihr = par_age(m.ifr, ages), par_age(m.ihr, ages)
    p_sev = np.minimum(0.95, ihr / sympt * np.sqrt(rr))
    u = rng.random(n)
    grave = ~asym & (u < p_sev)
    critique = grave & (u < p_sev * m.part_critique)
    lo, hi = m.g_legere
    gmax = np.where(critique, rng.uniform(*G_CRITIQUE, n), np.where(grave, rng.uniform(*G_GRAVE, n), rng.uniform(lo, hi, n)))
    gmax = np.where(asym, 0.0, gmax)
    g = np.where(grave, np.minimum(gmax, G_DEBUT), gmax)
    if m.letal_legers: letal = np.minimum(0.95, ifr / sympt * rr)
    else: letal = np.minimum(0.95, np.divide(ifr, np.maximum(ihr, 1e-12)) * np.sqrt(rr))
    aggr = grave | (~asym & (m.aggravation > 0))
    t_aggr = np.where(aggr, t_symp + FRACTION_AGGRAVATION * Dm, INF)
    symp = np.zeros(n, np.int64)
    for s, ps in m.symptomes.items():
        symp |= np.where(rng.random(n) < ps, BIT[s], 0)
    symp = np.where(asym, 0, symp)
    return {"t_inf": t_inf, "t_symp": t_symp, "t_fin_cont": t_fin_cont, "t_gueri": t_gueri, "t_fin": t_fin,
            "t_aggr": t_aggr, "asym": asym,
            "g": g, "g2": gmax, "letal": letal, "u_issue": rng.random(n), "u2": rng.random(n), "symp": symp,
            "grave": grave, "duree_maladie": Dm}


def letalite_iss(iss, age):
    """La letalite d une lesion AVEC soins, par ISS, corrigee de l age ( la mortalite du traumatise double vers 75 ans )."""
    iss = np.asarray(iss, float)
    return np.minimum(1.0, par_age(LETAL_ISS, iss) * (1.0 + np.maximum(0.0, np.asarray(age, float) - 55.0) / 20.0))


def iss_depuis_ais(ais):
    """L Injury Severity Score ( Baker 1974 ) : somme des carres des trois pires AIS de trois regions differentes ;
    un AIS de 6 ( lesion insurvivable ) donne 75. `ais` : { region : AIS de 1 a 6 }."""
    v = sorted((int(a) for a in ais.values() if a > 0), reverse=True)
    if any(not 1 <= a <= 6 for a in v): raise ValueError(f"AIS hors [1 ; 6] : {ais}")
    if not v: return 0
    if v[0] == 6: return 75
    return sum(a * a for a in v[:3])


ZONES_AIS = {"tete": 4, "cou": 3, "thorax": 3, "abdomen": 3, "membre": 2, "externe": 1}


def ais_balistique(zone, energie_j):
    """AIS d une blessure par projectile, selon la zone et l energie a l impact ( J ) : une arme de poing ( ~500 J ) ou un
    fusil ( 1 500-3 500 J ) ; +1 au-dela de 1 500 J, +1 au-dela de 3 000 J ( cavitation ). A calibrer."""
    if zone not in ZONES_AIS: raise ValueError(f"zone inconnue {zone!r} : {tuple(ZONES_AIS)}")
    a = ZONES_AIS[zone] + (energie_j >= 1500) + (energie_j >= 3000)
    return int(min(6 if zone in ("tete", "thorax") else 5, a))


# ================================================================== les decisions
class ContexteConsulter:
    """Ce qu un malade voit le matin ou il se demande s il va chez le medecin : son corps, sa bourse, la route, la
    rumeur. Ni son diagnostic, ni sa gravite a venir."""
    __slots__ = ("traits",)
    def __init__(self, traits): self.traits = traits


def _observer(ctx): return ctx.traits


def _regle_consulter(x, ctx):
    fievre, toux, dyspnee, digestif, gorge, jours, malaise, age, chronique = x[:9]
    if dyspnee >= 0.5 or malaise >= 0.66: return 1
    if fievre >= 0.5 and (jours >= 3 / 28 or age >= 65 / 90 or chronique >= 0.5): return 1
    if toux >= 0.5 and jours >= 14 / 28: return 1
    if digestif >= 0.5 and age >= 75 / 90 and jours >= 1 / 28: return 1
    return 0


def _temoin_consulter(x, ctx, rng): return 0


POINT_CONSULTER = D.PointDeDecision(
    "consulter", "medecine",
    traits=(("fievre", "son corps : il a de la fievre"), ("toux", "son corps : il tousse"),
            ("dyspnee", "son corps : il respire mal"), ("digestif", "son corps : diarrhee ou vomissements"),
            ("gorge", "son corps : mal de gorge"), ("jours", "les jours depuis ses premiers symptomes, sur 28"),
            ("malaise", "le malaise qu il ressent ( sa gravite actuelle ), sur 0,3"),
            ("age", "son age, sur 90 ans"), ("chronique", "une maladie chronique qu on lui a dite"),
            ("caisse", "la caisse de son menage en jours de nourriture, sur 30"),
            ("distance", "les km jusqu au medecin de sa capitale, sur 30"),
            ("rumeur", "les cas declares de sa region cette semaine, pour 100 habitants, sur 5")),
    actions=("attendre", "consulter"), observer=_observer, regle=_regle_consulter, temoin=_temoin_consulter,
    note="pour CE malade, chaque jour : 1 - gravite / 0,5 ( 0 s il meurt ), moins le cout de la consultation",
    horizon_j=HORIZON_SOINS)


class ContextePrescrire:
    """Ce que le medecin voit devant un patient febrile ou qui tousse : les symptomes, leur duree, l age, le terrain, la
    surveillance publique ( part de grippe et de COVID, resistance publiee ), son stock."""
    __slots__ = ("traits",)
    def __init__(self, traits): self.traits = traits


def _regle_prescrire(x, ctx):
    fievre, toux, gorge, dyspnee, jours, age, chronique = x[:7]
    if dyspnee >= 0.5 and fievre >= 0.5: return ANTIBIOTIQUE
    if gorge >= 0.5 and fievre >= 0.5 and toux < 0.5: return TESTER
    if toux >= 0.5 and fievre >= 0.5 and (jours >= 5 / 14 or age >= 65 / 90 or chronique >= 0.5): return TESTER
    return SANS


def _temoin_prescrire(x, ctx, rng): return ANTIBIOTIQUE


POINT_PRESCRIRE = D.PointDeDecision(
    "prescrire", "medecine",
    traits=(("fievre", "l examen : fievre"), ("toux", "l examen : toux"), ("gorge", "l examen : angine"),
            ("dyspnee", "l examen : gene respiratoire"), ("jours", "ce que dit le patient : jours de symptomes, sur 14"),
            ("age", "le dossier : age, sur 90 ans"), ("chronique", "le dossier : maladie chronique"),
            ("part_virale", "la surveillance : part de grippe et de COVID parmi les cas respiratoires declares ( 14 j )"),
            ("resistance", "le bulletin : resistance publiee du pneumocoque a l amoxicilline, sur 0,5"),
            ("stock", "sa pharmacie : jours de stock d amoxicilline, sur 60")),
    actions=("sans_antibiotique", "antibiotique", "tester"), observer=_observer, regle=_regle_prescrire,
    temoin=_temoin_prescrire,
    note="pour CE patient, chaque jour : 1 - gravite / 0,5 ( 0 s il meurt ), moins la resistance creee ( par DDD )",
    horizon_j=HORIZON_SOINS)


# ================================================================== les lots des pharmacies
def _entrer(p, med, ph, nom, q, nature, motif):
    """Une entree par le grand livre ( import ou don ), avec son lot date."""
    if q <= 0: return 0.0
    b = med.id_mol[nom]
    L = p.socle.livre
    if nature == "importe": L.importer(ph.stock, b, q, motif)
    else: L.produire(ph.stock, b, q, motif)
    lots = ph.lots.setdefault(b, [])
    fin = p.jour + MOL[nom].conservation_j
    k = len(lots)
    while k > 0 and lots[k - 1][1] > fin: k -= 1            # ranges par date de peremption : premier perime, premier sorti
    lots.insert(k, [q, fin])
    return q


def _retirer_lots(ph, b, q):
    lots = ph.lots.get(b, [])
    reste = q
    while reste > 0 and lots:
        l = lots[0]
        x = min(l[0], reste)
        l[0] -= x; reste -= x
        if l[0] <= 1e-12: lots.pop(0)
    if not lots and b in ph.lots and not ph.stock[b]: ph.lots.pop(b, None)


def prendre(p, detenteur, molecule, unites, motif="soin", region=None):
    """Sortir `unites` d une molecule du stock d un detenteur ( une pharmacie de ce domaine, ou celle d un autre domaine,
    qui a un `stock` du socle et, s il veut la peremption, des `lots` au meme format ) : consommation au grand livre,
    ce qui perime le plus tot d abord. L antibiotique compte dans l usage de la `region` ( celle du patient ; par defaut
    celle de la pharmacie ) : c est lui qui fait monter la resistance. Rend la quantite prise."""
    med = p.domaine("medecine")
    b = med.id_mol[molecule]
    pris = p.socle.livre.consommer(detenteur.stock, b, float(unites), motif)
    if pris > 0:
        if hasattr(detenteur, "lots"): _retirer_lots(detenteur, b, pris)
        if isinstance(detenteur, Pharmacie): detenteur.sortie_jour[IMOL[molecule]] += pris
        if molecule in ABX:
            r = region if region is not None else detenteur.id if isinstance(detenteur, Pharmacie) else None
            if r is not None: med.ddd_jour[int(r), IABX[molecule]] += pris * MOL[molecule].ddd
            med.compter("abx_ddd", pris * MOL[molecule].ddd)
    return pris


def ecarts_lots(p):
    """Les pharmacies dont la somme des lots n est pas le stock : [ ( pharmacie, molecule, stock, lots ) ]."""
    med = p.domaine("medecine")
    out = []
    for ph in med.pharmacies:
        for nom in NOMS_MOL:
            b = med.id_mol[nom]
            s, l = ph.stock[b], sum(x[0] for x in ph.lots.get(b, ()))
            if abs(s - l) > 1e-6 * max(1.0, s): out.append((ph.lieu, nom, s, l))
    return out


def _perimer(p, med):
    L = p.socle.livre
    for ph in med.pharmacies:
        for b, lots in list(ph.lots.items()):
            q = sum(l[0] for l in lots if l[1] <= p.jour)
            if q > 0: lots[:] = [l for l in lots if l[1] > p.jour]
            if q > 0:
                pris = L.perimer(ph.stock, b, q, "peremption_sante")
                p.compter("peremption_sante", pris)
            if not lots: ph.lots.pop(b, None)


def _reapprovisionner(p, med):
    """Chaque semaine, la pharmacie de chaque capitale commande de quoi tenir STOCK_CIBLE_J jours ; l Etat paie
    l exterieur au prix mondial, la marchandise arrive DELAI_LIVRAISON_J jours plus tard. Le sang vient des dons."""
    if med.chaine_externe: return
    w = p.w; L = p.socle.livre
    for ph in med.pharmacies:
        for k, nom in enumerate(NOMS_MOL):
            mol = MOL[nom]
            b = med.id_mol[nom]
            besoin = max(ph.conso[k], CONSO_A_PRIORI.get(nom, 0.0) * ph.pop / 1000.0 * 0.25)
            if mol.provenance == "don":
                _entrer(p, med, ph, nom, DONS_SANG_AN * ph.pop * 7.0 / JOURS_AN, "produit", "don_du_sang")
                continue
            voulu = STOCK_CIBLE_J * besoin - ph.stock[b]
            if voulu <= 0.5: continue
            paye = L.payer_l_exterieur(w.gouv, voulu * mol.prix, "import_produits_sante")
            q = paye / mol.prix
            if q <= 0:
                p.noter("rupture_sante", bien=nom, lieu=ph.lieu); continue
            p.compter("import_sante", paye)
            p.poser(DELAI_LIVRAISON_J * PAS_J, "medecine_livraison", ph.id, (b, q))


def _livraison(p, cle, donnees):
    med = p.domaine("medecine")
    b, q = donnees
    ph = med.pharmacies[cle]
    nom = p.socle.catalogue.biens[b].nom
    _entrer(p, med, ph, nom, q, "importe", "import_produits_sante")
    med.compter("commandes")


def reprendre_chaine(p):
    """Le domaine 17 prend en charge la chaine du medicament : les pharmacies de ce domaine ne commandent plus."""
    p.domaine("medecine").chaine_externe = True


def pharmacie_de(p, h):
    med = p.domaine("medecine")
    return med.pharmacies[med.region_de_lieu[h.domicile.marche.id]]


# ================================================================== l installation des infections et des lesions
def _creer(p, med, hid, path, t, hist=None, j=0, **champs):
    A = med.aff
    s = A.allouer()
    A.hab[s] = hid; A.path[s] = path; A.t0[s] = t
    if hist is not None:
        for c in ("t_inf", "t_symp", "t_fin_cont", "t_gueri", "t_fin", "t_aggr", "asym", "g", "g2", "letal", "u_issue",
                  "u2", "symp"):
            getattr(A, c)[s] = hist[c][j]
        A.phase[s] = LATENTE
    for c, v in champs.items(): getattr(A, c)[s] = v
    ix = med.ix
    A.region[s] = ix.region[hid] if hid < ix.n else med.region_de_lieu[p.w.habitants[hid].domicile.marche.id]
    med.par_hab.setdefault(hid, []).append(s)
    return s


def rr_normalise(ch, ages, rr_par_bit=None):
    """Le risque relatif de chacun du fait de ses maladies chroniques ( bits `ch` ), RAPPORTE a celui de son age : les
    tables par age ( letalite, incidence ) sont des moyennes de population qui contiennent deja les malades chroniques ;
    sans cette normalisation, le terrain compterait deux fois ( bogue du 23/09 : letalite doublee apres 65 ans )."""
    rr_par_bit = RR_CHRONIQUE if rr_par_bit is None else rr_par_bit
    ch = np.asarray(ch); ages = np.asarray(ages, float)
    rr, moyen = np.ones(len(ch)), np.ones(len(ch))
    for bit, v in rr_par_bit.items():
        rr *= np.where(ch & bit, v, 1.0)
        moyen *= 1.0 + interpole(PREVALENCE_CHRONIQUE[bit], ages) * (v - 1.0)
    return rr / moyen


def _rr_individuel(p, med, habs, m):
    """Le risque relatif de deces de chacun pour la maladie m : maladies chroniques ( rapportees a son age ), grossesse."""
    rr = np.ones(len(habs))
    if not len(habs) or not m.rr_chronique: return rr
    rr = rr_normalise(p.col("habitant", "med_chroniques")[habs], _ages(p, habs))
    if m.nom in ("grippe", "covid"): rr *= np.where(p.col("habitant", "enceinte")[habs] == 1, RR_GROSSESSE, 1.0)
    return np.minimum(rr, 6.0)


def _ages(p, habs):
    return (p.jour - p.col("habitant", "naissance_j")[np.asarray(habs, np.int64)]) / JOURS_AN


def infecter(p, habs, maladie, t=None, rng=None, infecteurs=None, importe=False):
    """Infecte les habitants `habs` ( identifiants ) par `maladie`, au temps t ( jours ; maintenant par defaut ).
    Ceux qui sont deja infectes par elle, immuns, ou morts sont ignores. Rend les identifiants infectes."""
    med = p.domaine("medecine"); w = p.w
    m = PATHOS[IP[maladie]]; k = IM[maladie]
    t = w.minutes / 1440.0 if t is None else t
    rng = rng if rng is not None else p.hasard("medecine_infections")
    habs = np.asarray(habs, np.int64)
    if not len(habs): return []
    habs, prem = np.unique(habs, return_index=True)
    if infecteurs is not None: infecteurs = np.asarray(infecteurs)[prem]
    _assurer(p, med, len(w.habitants))
    ok = (med.infecte[habs, k] == 0) & ~_immun(med, habs, k, p.jour) & (p.col("habitant", "deces_j")[habs] < 0)
    habs, inf_ = habs[ok], (np.asarray(infecteurs)[ok] if infecteurs is not None else np.full(ok.sum(), -1))
    if not len(habs): return []
    if m.progression < 1.0:                       # tuberculose : la plupart des infections restent latentes
        prog = rng.random(len(habs)) < m.progression
        lat = habs[~prog]
        med.statut[lat, k] = 2; med.deja[lat, k] = True
        habs, inf_ = habs[prog], inf_[prog]
        if not len(habs): return lat.tolist()
    hist = tirer_histoires(m, t, _ages(p, habs), rng, _rr_individuel(p, med, habs, m))
    res = np.zeros(len(habs), bool)
    if m.bacterie and m.nom in GERME_RESISTANCE:
        abx = "antituberculeux" if m.nom == "tuberculose" else "amoxicilline"
        reg = med.ix.region[np.minimum(habs, med.ix.n - 1)]
        res = rng.random(len(habs)) < med.resistance[reg, IABX[abx]] * GERME_RESISTANCE[m.nom]
    if med.traces:
        for i in inf_.tolist():
            if i in med.traces: med.traces[i] += 1
    for j, hid in enumerate(habs.tolist()):
        _creer(p, med, hid, IP[maladie], t, hist, j, infecteur=int(inf_[j]), resistant=bool(res[j]))
        med.infecte[hid, k] = 1; med.deja[hid, k] = True
        h = w.habitants[hid]
        w.infectes_du_jour.add(hid)
        if h.lieu is not None: w.contagions_lieu[h.lieu.id] = w.contagions_lieu.get(h.lieu.id, 0) + 1
        _synchroniser(p, med, hid)
    n = len(habs)
    med.compter(("infections", maladie), n)
    p.compter("infection_importee" if importe else "infection", float(n))
    return habs.tolist()


def blesser(p, h, type_, gravite, cause="accident", lieu=None):
    """Une lesion : `type_` parmi TYPES_LESION, `gravite` = ISS ( 1 a 75, `iss_depuis_ais` le calcule ), `cause` du
    deces eventuel parmi d01.CAUSES ( accident, combat, violence ). Le blesse est aussitot pris en charge par le soin
    en place ( Monde.soigner : ce domaine ou le domaine 17 ) si ISS >= 9 ; sans soins dans l heure ( ISS >= 41 ), les
    3 heures ( >= 25 ) ou les 6 heures ( >= 16 ), il peut mourir de sa phase aigue. Rend la cle de l affection."""
    if type_ not in TYPES_LESION: raise ValueError(f"type de lesion inconnu {type_!r} : {TYPES_LESION}")
    iss = int(gravite)
    if not 1 <= iss <= 75: raise ValueError(f"ISS hors [1 ; 75] : {gravite!r}")
    if cause not in POP.CAUSES: raise ValueError(f"cause inconnue {cause!r}")
    if not h.vivant: return None
    med = p.domaine("medecine"); w = p.w
    _assurer(p, med, len(w.habitants))
    t = w.minutes / 1440.0
    rng = p.hasard("medecine_blessures")
    age = float(_ages(p, [h.id])[0])
    if iss < 9: dur = rng.gamma(4.0, 7.0 / 4.0)
    elif iss < 16: dur = rng.gamma(9.0, 21.0 / 9.0)
    elif iss < 25: dur = rng.gamma(9.0, 45.0 / 9.0)
    else: dur = rng.gamma(9.0, 90.0 / 9.0)
    g = min(1.0, iss / 30.0)
    aigu = max(1.0, iss / 2.0) if g > GRAVITE_HOPITAL else INF
    symp = BIT["douleur"] | (BIT["saignement"] if type_ in PENETRANTES or rng.random() < 0.3 else 0)
    fin = t + max(dur, aigu + 1.0 if aigu < INF else 0)
    s = _creer(p, med, h.id, IP["lesion_" + type_], t, t_symp=t, t_gueri=fin, t_fin=fin,
               t_aggr=t + aigu if aigu < INF else INF, g=g, g2=G_CONVALESCENCE, gmax=g,
               letal=float(letalite_iss(iss, age)), u_issue=rng.random(), u2=rng.random(), symp=symp, iss=iss,
               cause=POP.CAUSES.index(cause), phase=CLINIQUE)
    p.noter("blessure", habitant=h.id, nature=type_, iss=iss, cause=cause)
    med.compter(("lesions", type_))
    if iss >= 75:                                   # une lesion insurvivable ( un AIS de 6 ) tue sur le coup
        _tuer(p, med, h.id, cause, "lesion_" + type_); return None
    _synchroniser(p, med, h.id)
    if iss >= 16:
        delai = 1 if iss >= 41 else 3 if iss >= 25 else 6
        p.poser(max(1, int(delai * 60 / C.MINUTES_PAR_PAS)), "medecine_phase_aigue", h.id, (s, int(med.aff.gen[s])))
    if iss >= 9 and h.vivant: w.soigner(h)
    return s


def _phase_aigue(p, hid, donnees):
    """L echeance de la phase aigue d un blesse grave : sans soins a temps, il peut en mourir maintenant."""
    s, gen = donnees
    med = p.domaine("medecine"); A = med.aff
    if s >= A.k or not A.actif[s] or A.gen[s] != gen or A.hab[s] != hid: return
    if A.soin[s] & SOUTIEN: return
    m = PATHOS[A.path[s]]
    letal_ss = min(0.98, float(A.letal[s]) * m.sans_soutien)
    if A.u_issue[s] < PART_AIGUE * letal_ss:
        _tuer(p, med, hid, POP.CAUSES[int(A.cause[s])], m.nom)
    else:
        A.mult[s] *= 0.4 / max(1e-9, 1.0 - PART_AIGUE * letal_ss)      # la mort tardive, la phase aigue passee
        A.u_issue[s] = p.hasard("medecine_blessures").random()


# ================================================================== le resume E1
def _synchroniser(p, med, hid):
    """Habitant.etat, gravite, remede et jours_etat resument les affections en cours ( voir la fiche, point 2 )."""
    h = p.w.habitants[hid]
    if not h.vivant: return
    A = med.aff
    g, infecte, traite = 0.0, False, False
    for s in med.par_hab.get(hid, ()):
        if A.phase[s] == CLINIQUE and not A.asym[s]:
            if A.g[s] > g: g = float(A.g[s])
            if A.soin[s] & (SOUTIEN | SPECIFIQUE): traite = True
        if PATHOS[A.path[s]].groupe == "infection": infecte = True
    if g >= SEUIL_E1: etat = "I"
    elif infecte or g > 0: etat = "E"
    else: etat = "R" if h.etat in ("E", "I", "R") else "S"
    avant_hop = h.etat == "I" and h.gravite > GRAVITE_HOPITAL
    if etat != h.etat: h.jours_etat = 0.0
    h.etat = etat
    h.gravite = g if etat == "I" else 0.0
    h.remede = traite and etat == "I"
    apres_hop = etat == "I" and h.gravite > GRAVITE_HOPITAL
    if avant_hop != apres_hop and p.a("agenda"): AG.replanifier(p, h, rentrer=apres_hop)


def _retirer_affection(med, s):
    hid = int(med.aff.hab[s])
    lst = med.par_hab.get(hid)
    if lst is not None:
        if s in lst: lst.remove(s)
        if not lst: del med.par_hab[hid]
    m = PATHOS[med.aff.path[s]]
    if m.nom in IM: med.infecte[hid, IM[m.nom]] = 0
    med.aff.liberer(s)


def _tuer(p, med, hid, cause, nom):
    """Une mort causee par ce domaine : la ligne se ferme, et la mort passe par d01.deceder."""
    for s in list(med.par_hab.get(hid, ())): _retirer_affection(med, s)
    h = p.w.habitants[hid]
    if not h.vivant: return
    med.tues[hid] = cause
    med.compter(("deces", nom))
    p.compter("deces_medical")
    POP.deceder(p, h, cause)


def _letal_final(p, med, s, h):
    A = med.aff; m = PATHOS[A.path[s]]
    if m.table_d01:
        return 0.0 if A.soin[s] & SPECIFIQUE else float(A.letal[s])
    grave = A.gmax[s] > GRAVITE_HOPITAL
    if not (grave or m.letal_legers): return 0.0
    L = float(A.letal[s]) * float(A.mult[s])
    if m.sans_specifique > 1.0 and not A.soin[s] & SPECIFIQUE: L *= m.sans_specifique
    if grave and not A.soin[s] & SOUTIEN: L *= m.sans_soutien
    if h.faim > 1.0: L *= m.mult_faim
    return min(0.99, L)


# ================================================================== la contagion, chaque heure
def _cles_du_moment(p, med):
    """La cle du groupe de contact de chaque habitant a cette heure ( -1 : seul, en route, en mer, mort )."""
    ix = med.ix; n = ix.n; w = p.w
    if p.a("agenda"):
        col = p.colonnes["habitant"]
        act = col["agenda_activite"][:n].astype(np.int64)
        lieu = col["agenda_lieu"][:n].astype(np.int64)
    else:
        H = w.habitants
        il = med.index_lieu
        act = np.fromiter((CODE_POSTE.get(H[i].poste, -1) if H[i].lieu is not None else -1 for i in range(n)), np.int64, n)
        lieu = np.fromiter((il[H[i].lieu.id] if H[i].lieu is not None else -1 for i in range(n)), np.int64, n)
        act[(act == AG.TRAVAIL) & ix.enfant] = AG.ECOLE
    cle = np.full(n, -1, np.int64)
    m = act == AG.MAISON
    cle[m] = (MAISON_C << DECALAGE) | ix.men[m]
    t = act == AG.TRAVAIL
    m = t & ~ix.soignant & (ix.equipe >= 0)
    cle[m] = (TRAVAIL_C << DECALAGE) | ix.equipe[m]
    m = t & ~ix.soignant & (ix.equipe < 0) & (lieu >= 0)
    cle[m] = (TRAVAIL_C << DECALAGE) | BIT_LIEU | lieu[m]
    m = t & ix.soignant & (lieu >= 0)
    cle[m] = (HOPITAL_C << DECALAGE) | lieu[m]
    e = act == AG.ECOLE
    m = e & (ix.classe >= 0)
    cle[m] = (ECOLE_C << DECALAGE) | ix.classe[m]
    m = e & (ix.classe < 0) & (lieu >= 0)
    cle[m] = (ECOLE_C << DECALAGE) | BIT_LIEU | lieu[m]
    for a, c in ((AG.COURSES, COMMUN_C), (AG.LOISIR, LOISIR_C), (AG.CULTE, CULTE_C), (AG.HOPITAL, HOPITAL_C)):
        m = (act == a) & (lieu >= 0)
        cle[m] = (c << DECALAGE) | lieu[m]
    cle[p.col("habitant", "deces_j")[:n] >= 0] = -1
    return cle


def _mesurer_contacts(p, med, cle):
    """Une heure de la semaine d etalonnage : pour chaque habitant de l echantillon, les heures passees dans chaque cadre
    avec au moins une autre personne, et la taille de ces groupes ; pour les malades ( etat I hors de l hopital ), les
    heures par cadre. Ce que fait vraiment un habitant, et ce que fait un malade."""
    pos = med.cal_pos
    n = min(len(cle), len(pos))
    med.expo_heures += 1
    H = p.w.habitants
    mal = [hid for hid in med.par_hab if hid < n and H[hid].vivant and H[hid].etat == "I" and H[hid].poste != "hopital"]
    med.cal_malades_h += len(mal)
    ok = np.nonzero(cle[:n] >= 0)[0]
    if not len(ok): return
    _, inv, cnt = np.unique(cle[ok], return_inverse=True, return_counts=True)
    ni = cnt[inv]
    avec = ni >= 2
    ii = ok[avec]; cc = (cle[ii] >> DECALAGE).astype(np.int64); nn = ni[avec].astype(np.float32)
    k = pos[ii]; dans = k >= 0
    np.add.at(med.cal_h, (k[dans], cc[dans]), np.float32(1.0))
    np.add.at(med.cal_n, (k[dans], cc[dans]), nn[dans])
    if mal:
        mm = np.zeros(len(cle), bool); mm[mal] = True
        np.add.at(med.cal_hI, cc[mm[ii]], 1.0)


def part_alitee(m):
    """La part des cas symptomatiques d une maladie qui se sentent malades ( gravite >= SEUIL_E1 ) : eux changent leur
    journee ( l agenda les garde chez eux ), les autres ( un rhume ) non."""
    lo, hi = m.g_legere
    if hi <= lo: return 1.0 if lo >= SEUIL_E1 else 0.0
    return float(min(1.0, max(0.0, (hi - max(lo, SEUIL_E1)) / (hi - lo))))


def r_reseau(m, q, h, nb, hI=None):
    """Le R d un cas de la maladie m, en moyenne sur des habitants dont on connait les heures par cadre ( h ) et la taille
    moyenne de leurs groupes ( nb ) : dans un groupe de n personnes, on n infecte pas plus de n - 1 autres, et un contact
    repete chaque jour s epuise ( ( n - 1 ) ( 1 - exp( -x / ( n - 1 ) ) ) ). Pendant ses symptomes, un malade alite vit la
    journee des malades ( hI, heures par cadre ; celle de tout le monde si elle n a pas ete vue )."""
    P, Dc = m.presympt[0], m.contagion[0]
    c = CONTACTS_H[None, :]
    k1 = np.maximum(nb - 1.0, 1e-9)

    def S(x): return np.where(nb > 1.0, k1 * (1.0 - np.exp(-x / k1)), 0.0)
    f = part_alitee(m) if hI is not None else 0.0
    hs = h if hI is None else np.broadcast_to(hI[None, :], h.shape)
    sym = f * S(q * c * (h * P + hs * Dc)) + (1.0 - f) * S(q * c * h * (P + Dc))
    r = (1.0 - m.asym) * sym + m.asym * S(q * m.k_asym * c * h * (P + Dc))
    return float(r.sum(1).mean())


def q_reseau(m, h, nb, hI=None):
    """Le q qui donne a un cas moyen de CE pays son R0 ( dichotomie : r_reseau croit avec q ). Plafonne si les contacts
    mesures ne peuvent pas donner R0 ( rend alors le plafond )."""
    E = max(1e-6, float((h * CONTACTS_H).sum(1).mean()))
    lo, hi = 0.0, q_contact(m, E)
    while r_reseau(m, hi, h, nb, hI) < m.r0 and hi < 1e3: hi *= 2.0
    for _ in range(60):
        mi = 0.5 * (lo + hi)
        if r_reseau(m, mi, h, nb, hI) < m.r0: lo = mi
        else: hi = mi
    return hi


def _contagion(p):
    w = p.w; med = p.domaines["medecine"]
    t = w.minutes / 1440.0
    heure = int(round(w.heure)) % 24
    if heure == 6: _adopter_e1(p, med, t)
    _transitions(p, med, t)
    A = med.aff; k = A.k
    etalonne = med.expo_ref is not None
    contag = A.actif[:k] & (A.t_inf[:k] <= t) & (t < A.t_fin_cont[:k])
    if not contag.any() and etalonne: return
    cle = _cles_du_moment(p, med)
    if not etalonne: _mesurer_contacts(p, med, cle)
    if not contag.any(): return
    idx = np.nonzero(contag)[0]
    habs = A.hab[idx].astype(np.int64)
    dans = habs < len(cle)
    idx, habs = idx[dans], habs[dans]
    ck = cle[habs]
    ok = ck >= 0
    idx, habs, ck = idx[ok], habs[ok], ck[ok]
    if not len(idx): return
    paths = A.path[idx]
    poids = np.where(A.asym[idx], K_ASYM[paths], 1.0)
    chauds = np.unique(ck)
    membres = np.nonzero(np.isin(cle, chauds))[0]
    gm = np.searchsorted(chauds, cle[membres])
    taille = np.bincount(gm, minlength=len(chauds)).astype(float)
    cg = CONTACTS_H[(chauds >> DECALAGE).astype(np.int64)]
    gi_inf = np.searchsorted(chauds, ck)
    rng = p.socle.hasard.sous_flux("medecine_contagion", p.jour, heure)
    ja = _jour_an(p)
    faim = med.ix.faim[membres]
    for path in np.unique(paths).tolist():
        m = PATHOS[path]; km = IM[m.nom]
        sel = paths == path
        pres = np.bincount(gi_inf[sel], weights=poids[sel], minlength=len(chauds))
        q = med.q[km] * facteur_saison(m, ja, med.saison_forcee.get(m.nom))
        taux = taux_par_membre(q, cg, pres, taille)                  # infections par heure, par susceptible present
        tj = taux[gm]
        sus = (med.infecte[membres, km] == 0) & ~_immun(med, membres, km, p.jour)
        if not sus.any(): continue
        pj = 1.0 - np.exp(-tj * np.where(faim > 1.0, 1.5, 1.0))      # Monde.contagion : la faim x 1,5
        u = rng.random(len(membres))
        nouveaux = membres[sus & (u < pj) & (tj > 0)]
        if not len(nouveaux): continue
        # l infecteur de chacun : un contagieux de son groupe, tire selon sa contagiosite
        inf_ids = habs[sel]; inf_g = gi_inf[sel]; inf_w = poids[sel]
        ordre = np.argsort(inf_g, kind="stable")
        inf_ids, inf_g, inf_w = inf_ids[ordre], inf_g[ordre], inf_w[ordre]
        rangs = np.arange(len(chauds))
        debut, fin = np.searchsorted(inf_g, rangs), np.searchsorted(inf_g, rangs, side="right")
        infecteurs = []
        for j in nouveaux.tolist():
            g = int(np.searchsorted(chauds, cle[j]))
            a, b = int(debut[g]), int(fin[g])
            ww = inf_w[a:b]
            r = rng.random() * ww.sum()
            infecteurs.append(int(inf_ids[a + min(b - a - 1, int(np.searchsorted(np.cumsum(ww), r, side="right")))]))
        infecter(p, nouveaux, m.nom, t, rng, np.array(infecteurs))


def _immun(med, habs, k, jour):
    st = med.statut[habs, k]
    return ((st == 1) & (med.immun_fin[habs, k] > jour)) | (st == 2)


# ================================================================== le cours des affections
def _transitions(p, med, t):
    """Chaque heure : debut des symptomes, aggravation ( ou sortie de phase aigue ), fin ( guerison ou deces )."""
    A = med.aff; k = A.k
    if k == 0: return
    act = A.actif[:k]
    ph = A.phase[:k]
    a_sync = set()
    dev = np.nonzero(act & (ph < CLINIQUE) & (A.t_symp[:k] <= t) & (A.t_fin[:k] > t))[0]
    for s in dev.tolist():
        A.phase[s] = CLINIQUE
        if not A.asym[s]:
            m = PATHOS[A.path[s]]
            med.compter(("cas", m.nom)); p.compter("cas_symptomatique")
            A.gmax[s] = max(float(A.gmax[s]), float(A.g[s]))
            c = COMPLICATION_PNEUMONIE.get(m.nom)
            if c and A.u2[s] < c: _cas_sporadique(p, med, int(A.hab[s]), "pneumonie", t)
        a_sync.add(int(A.hab[s]))
    cont = np.nonzero(act & (A.phase[:k] == LATENTE) & (A.t_inf[:k] <= t))[0]
    A.phase[cont] = CONTAGIEUSE
    agg = np.nonzero(A.actif[:k] & (A.phase[:k] == CLINIQUE) & (A.t_aggr[:k] <= t))[0]
    H = p.w.habitants
    for s in agg.tolist():
        if not A.actif[s]: continue
        m = PATHOS[A.path[s]]
        A.t_aggr[s] = INF
        if m.groupe == "lesion":                                  # fin de la phase aigue : il en meurt, ou il se remet
            hid = int(A.hab[s])
            if H[hid].vivant and A.u_issue[s] < _letal_final(p, med, s, H[hid]):
                _tuer(p, med, hid, POP.CAUSES[int(A.cause[s])], m.nom); a_sync.discard(hid); continue
            A.letal[s] = 0.0
            A.g[s] = min(float(A.g[s]), float(A.g2[s]))
        elif A.g2[s] > GRAVITE_HOPITAL:                           # un cas grave : l aggravation, sauf prevention
            if A.u2[s] < A.prev[s]: A.g[s] = A.g2[s]
            else:
                A.g2[s] = min(float(A.g2[s]), G_DEBUT); A.letal[s] = 0.0
        elif m.aggravation > 0 and not A.soin[s] & SPECIFIQUE and A.u2[s] < m.aggravation:
            A.g[s] = A.g2[s] = 0.45                               # un cas leger non traite qui s aggrave
        A.gmax[s] = max(float(A.gmax[s]), float(A.g[s]))
        a_sync.add(int(A.hab[s]))
    gueri = np.nonzero(A.actif[:k] & (A.phase[:k] == CLINIQUE) & (A.t_gueri[:k] <= t))[0]
    for s in gueri.tolist():                                      # la fin des symptomes : l issue se tire ici
        if not A.actif[s]: continue
        hid = int(A.hab[s]); h = H[hid]
        m = PATHOS[A.path[s]]
        A.t_gueri[s] = INF
        if not h.vivant: continue
        letal = 0.0 if A.asym[s] else _letal_final(p, med, s, h)
        med.compter(("letal_attendu", m.nom), letal)
        if A.u_issue[s] < letal:
            _tuer(p, med, hid, POP.CAUSES[int(A.cause[s])] if m.groupe == "lesion" else m.cause, m.nom)
            a_sync.discard(hid)
            continue
        A.g[s] = A.g2[s] = 0.0; A.letal[s] = 0.0; A.t_aggr[s] = INF
        a_sync.add(hid)
    fin = np.nonzero(A.actif[:k] & (A.t_fin[:k] <= t))[0]
    for s in fin.tolist():                                        # la fin de l infection : l immunite
        if not A.actif[s]: continue
        hid = int(A.hab[s]); h = H[hid]
        m = PATHOS[A.path[s]]
        if not h.vivant:
            _retirer_affection(med, s); continue
        if m.nom in IM:
            km = IM[m.nom]
            if m.immunite_j >= IMMUNITE_A_VIE: med.statut[hid, km] = 1; med.immun_fin[hid, km] = IMMUNITE_A_VIE
            elif m.immunite_j > 0:
                med.statut[hid, km] = 1
                med.immun_fin[hid, km] = p.jour + int(p.hasard("medecine_immunite").exponential(m.immunite_j))
        med.compter(("guerisons", m.nom)); p.compter("guerison")
        _retirer_affection(med, s)
        a_sync.add(hid)
    for hid in a_sync: _synchroniser(p, med, hid)
    # celui qui vient de s aggraver arrive a l hopital : il y est soigne tout de suite ( par qui tient Monde.soigner )
    for hid in a_sync:
        h = H[hid]
        if (h.vivant and h.etat == "I" and h.gravite > GRAVITE_HOPITAL
                and any(A.consulte[s] < 2 for s in _cliniques(med, hid))):
            p.w.soigner(h)                        # le soutien qui manque se retente le matin ( _clinique )


def _adopter_e1(p, med, t):
    """Les E et I poses par le moteur ( Monde.aube : l epidemie de Pyrgos ) ou par un autre code, sans affection : une
    grippe commence pour eux maintenant."""
    rng = p.hasard("medecine_moteur")
    orph = [h.id for h in p.w.habitants if h.vivant and h.etat in ("E", "I") and h.id not in med.par_hab]
    if orph:
        for hid in orph: p.w.habitants[hid].etat = "S"
        infecter(p, orph, MALADIE_DU_MOTEUR, t, rng)


def _cas_sporadique(p, med, hid, nom, t):
    m = PATHOS[IP[nom]]; h = p.w.habitants[hid]
    if not h.vivant or med.infecte[hid, IM[nom]]: return
    rng = p.hasard("medecine_sporadique")
    hist = tirer_histoires(m, t, _ages(p, [hid]), rng, _rr_individuel(p, med, np.array([hid]), m))
    res = False
    if m.nom in GERME_RESISTANCE:
        r = med.resistance[med.ix.region[min(hid, med.ix.n - 1)], IABX["amoxicilline"]]
        res = bool(rng.random() < r * GERME_RESISTANCE[m.nom])
    _creer(p, med, hid, IP[nom], t, hist, 0, resistant=res)
    med.infecte[hid, IM[nom]] = 1; med.deja[hid, IM[nom]] = True
    med.compter(("cas_sporadiques", nom))
    _synchroniser(p, med, hid)


# ================================================================== l aube : la journee clinique et la sante publique
def _assurer(p, med, n):
    """Les tableaux n x M suivent la population ; un nouveau-ne recoit sa protection maternelle contre la rougeole."""
    if n > med.cap:
        cap = max(n, 2 * med.cap)
        for nom in ("statut", "immun_fin", "infecte", "deja", "doses"):
            a = getattr(med, nom)
            b = np.zeros((cap,) + a.shape[1:], a.dtype); b[:med.cap] = a
            setattr(med, nom, b)
        v = np.zeros(cap, med.vacc_saison.dtype); v[:med.cap] = med.vacc_saison; med.vacc_saison = v
        med.cap = cap
    if n > med.n_init:
        neufs = np.arange(med.n_init, n)
        nj = p.col("habitant", "naissance_j")[neufs]
        k = IM["rougeole"]
        med.statut[neufs, k] = 1; med.immun_fin[neufs, k] = nj + PROTECTION_MATERNELLE_J
        med.n_init = n


def _index_du_jour(p, med):
    w = p.w; H = w.habitants; n = len(H)
    _assurer(p, med, n)
    p.colonnes["habitant"].assurer(n)
    ix = IndexDuJour()
    ix.n, ix.jour = n, p.jour
    il = med.index_lieu; rl = med.region_de_lieu
    men = np.full(n, -1, np.int64); dom = np.full(n, -1, np.int64); hop = np.full(n, -1, np.int64)
    region = np.zeros(n, np.int64); faim = np.zeros(n); vivant = np.zeros(n, bool)
    soignant = np.zeros(n, bool); enfant = np.zeros(n, bool); role = []
    equipes, classes = {}, {}
    age = (p.jour - p.col("habitant", "naissance_j")[:n]) / JOURS_AN
    for h in H:
        i = h.id
        role.append(h.role)
        if not h.vivant: continue
        vivant[i] = True
        if h.menage is not None: men[i] = h.menage.id
        if h.domicile is not None:
            dom[i] = il[h.domicile.id]; hop[i] = il[h.domicile.marche.id]; region[i] = rl[h.domicile.marche.id]
        faim[i] = h.faim
        if h.role in SOIGNANTS: soignant[i] = True
        if h.role == "enfant":
            enfant[i] = True
            if h.horaire == "ecole" and h.travail is not None:
                classes.setdefault(il[h.travail.id], []).append(i)
        elif h.travail is not None and h.role not in SOIGNANTS:
            equipes.setdefault((il[h.travail.id], h.role), []).append(i)
    equipe = np.full(n, -1, np.int64); classe = np.full(n, -1, np.int64)
    nxt = 0
    for cle_ in sorted(equipes):
        ids = equipes[cle_]
        for r, i in enumerate(ids): equipe[i] = nxt + r // TAILLE_EQUIPE
        nxt += (len(ids) + TAILLE_EQUIPE - 1) // TAILLE_EQUIPE
    nxt = 0
    for cle_ in sorted(classes):                   # une ecole : ses eleves par age, par classes de TAILLE_CLASSE ( une
        ids = sorted(classes[cle_], key=lambda i: (age[i], i))     # petite ecole a des classes a plusieurs niveaux )
        for r, i in enumerate(ids): classe[i] = nxt + r // TAILLE_CLASSE
        nxt += (len(ids) + TAILLE_CLASSE - 1) // TAILLE_CLASSE
    ix.men, ix.dom, ix.hop, ix.region, ix.faim, ix.vivant = men, dom, hop, region, faim, vivant
    ix.soignant, ix.enfant, ix.equipe, ix.classe, ix.age = soignant, enfant, equipe, classe, age
    ix.sexe = p.col("habitant", "sexe")[:n].copy()
    ix.enceinte = p.col("habitant", "enceinte")[:n] == 1
    ix.role = role
    # un menage pauvre : moins de trois jours de nourriture dans sa caisse, au prix de son marche
    pauvre = np.zeros(n, bool)
    prix = {mid: m.prix["nourriture"] for mid, m in w.marches.items()}
    for mg in w.menages:
        viv = [x.id for x in mg.membres if x.vivant]
        if not viv or mg.domicile is None: continue
        if mg.caisse < 3 * len(viv) * C.NOURRITURE_PAR_JOUR * prix.get(mg.domicile.marche.id, C.PRIX_MONDE["nourriture"]):
            pauvre[viv] = True
    ix.pauvre = pauvre
    med.ix = ix
    for ph in med.pharmacies: ph.pop = 0
    for r, c in zip(*np.unique(region[vivant], return_counts=True)): med.pharmacies[int(r)].pop = int(c)


def _purger_morts(p, med):
    H = p.w.habitants
    for hid in [h for h in med.par_hab if not H[h].vivant]:
        for s in list(med.par_hab.get(hid, ())): _retirer_affection(med, s)


def _etalonner(p, med):
    """Au 7e matin, les contacts mesures la premiere semaine donnent a chaque maladie son q : celui pour lequel un cas
    moyen de CE pays, avec ses groupes et ses malades qui restent chez eux, fait R0 infections ( R0 de la litterature,
    mesure sur des epidemies reelles, comportements compris ). Puis q ne bouge plus : une quarantaine qui reduit les
    contacts reduit alors vraiment la transmission."""
    if med.expo_ref is not None or p.jour - med.jour0 < JOURS_ETALONNAGE or med.expo_heures < 24: return
    jours = med.expo_heures / 24.0
    rangs = med.cal_pos[med.cal_pos >= 0]
    ids = np.nonzero(med.cal_pos >= 0)[0]
    vivant = p.col("habitant", "deces_j")[ids] < 0
    h = (med.cal_h[rangs] / jours)[vivant].astype(float)
    nb = np.where(med.cal_h[rangs] > 0, med.cal_n[rangs] / np.maximum(med.cal_h[rangs], 1.0), 1.0)[vivant].astype(float)
    hI = med.cal_hI / (med.cal_malades_h / 24.0) if med.cal_malades_h >= 24 else None
    med.expo_ref = float((h * CONTACTS_H).sum(1).mean())
    med.expo_malade = None if hI is None else float((hI * CONTACTS_H).sum())
    for m in MALADIES:
        if m.transmissible: med.q[IM[m.nom]] = q_reseau(m, h, nb, hI)
    med.cal_h = med.cal_n = None


def _chroniques(p, med, t):
    """Chaque matin : le traitement d entretien sort des pharmacies ( un manque laisse des malades sans traitement ) ;
    les decompensations tombent ; chaque semaine, de nouveaux malades chroniques."""
    ix = med.ix; n = ix.n
    col = p.colonnes["habitant"]
    ch, tr, sj = col["med_chroniques"][:n], col["med_traite"][:n], col["med_sans_traitement_j"]
    viv = ix.vivant
    rng = p.du_jour("medecine_chroniques")
    manque = np.zeros(n, bool)
    for bits, nom in TRAITEMENT_CHRONIQUE:
        if nom == "antidiabetique": qui = viv & (ch & DIABETE > 0) & (ch & INSULINE == 0) & (tr & DIABETE > 0)
        elif nom == "insuline": qui = viv & (ch & INSULINE > 0) & (tr & DIABETE > 0)
        else: qui = viv & (ch & bits > 0) & (tr & bits > 0)
        if nom == "antihypertenseur" and bits == CARDIO: qui &= (ch & HTA == 0)     # un seul traitement par patient
        _entretien(p, med, qui, nom, manque, rng)
    dep = viv & (col["med_mental"][:n] & DEPRESSION > 0) & (col["med_mental"][:n] & DEP_TRAITEE > 0)
    _entretien(p, med, dep, "antidepresseur", np.zeros(n, bool), rng)
    suivis = viv & (tr > 0)
    sj[:n] = np.where(suivis & manque, sj[:n] + 1, 0)
    # decompensations
    u = rng.random((n, len(DECOMPENSATIONS) + 1))
    for j, (bit, nom, a_tr, a_ntr) in enumerate(DECOMPENSATIONS):
        malade = viv & (ch & bit > 0)
        if not malade.any(): continue
        traite = (tr & bit > 0) & (sj[:n] < SEVRAGE_INSULINE_J)
        h_j = np.where(traite, a_tr, a_ntr) / JOURS_AN
        if bit == DIABETE:
            sevre = (ch & INSULINE > 0) & ((tr & DIABETE == 0) | (sj[:n] >= SEVRAGE_INSULINE_J))
            h_j = np.where(sevre, CRISE_SANS_INSULINE_J, h_j)
        for hid in np.nonzero(malade & (u[:, j] < h_j))[0].tolist():
            _cas_non_infectieux(p, med, hid, nom, t, rng)
            p.compter("decompensation")
    if p.jour % 7 == 0: _nouveaux_chroniques(p, med, rng)


def _entretien(p, med, qui, nom, manque, rng):
    ix = med.ix
    if not qui.any(): return
    for r in range(len(med.pharmacies)):
        dans = qui & (ix.region == r)
        besoin = int(dans.sum())
        if not besoin: continue
        pris = prendre(p, med.pharmacies[r], nom, besoin, "traitement_chronique")
        if pris < besoin - 1e-9:
            ids = np.nonzero(dans)[0]
            sans = ids[rng.random(len(ids)) < 1.0 - pris / besoin]
            manque[sans] = True
            p.compter("traitement_chronique_manquant", float(len(sans)))


def _nouveaux_chroniques(p, med, rng):
    ix = med.ix; n = ix.n
    col = p.colonnes["habitant"]
    ch, tr = col["med_chroniques"], col["med_traite"]
    age = ix.age
    u = rng.random((n, 3 * len(PREVALENCE_CHRONIQUE)))
    for j, (bit, tab) in enumerate(PREVALENCE_CHRONIQUE.items()):
        pa, pb = interpole(tab, age), interpole(tab, age + 1.0)
        h_sem = np.maximum(0.0, pb - pa) / np.maximum(1e-9, 1.0 - pa) * 7.0 / JOURS_AN
        neufs = np.nonzero(ix.vivant & (ch[:n] & bit == 0) & (u[:, 3 * j] < h_sem))[0]
        if not len(neufs): continue
        ch[neufs] |= bit
        tr[neufs] |= np.where(u[neufs, 3 * j + 1] < PART_TRAITES[bit], bit, 0).astype(tr.dtype)
        if bit == DIABETE:                     # un diabetique sous insuline est toujours traite : sans elle, il meurt
            ins = (age[neufs] < 30) | (u[neufs, 3 * j + 2] < PART_INSULINE)
            ch[neufs[ins]] |= INSULINE; tr[neufs[ins]] |= DIABETE


def _cas_non_infectieux(p, med, hid, nom, t, rng):
    """Une decompensation, une complication, un effet indesirable : evident ( le medecin le voit ), sans contagion."""
    m = PATHOS[IP[nom]]; h = p.w.habitants[hid]
    if not h.vivant: return None
    lo, hi = m.g_legere
    g = float(rng.uniform(lo, hi))
    dur = float(_gamma(rng, m.maladie, 1)[0])
    symp = 0
    for sy, ps in m.symptomes.items():
        if rng.random() < ps: symp |= BIT[sy]
    s = _creer(p, med, hid, IP[nom], t, t_symp=t, t_gueri=t + max(0.5, dur), t_fin=t + max(0.5, dur), g=g, g2=g, gmax=g,
               letal=float(par_age(m.ifr, [0])[0]), u_issue=rng.random(), u2=rng.random(), symp=symp, phase=CLINIQUE)
    med.compter(("cas", nom))
    _synchroniser(p, med, hid)
    return s


def _mental(p, med):
    """La sante mentale : episodes depressifs et anxieux, lies a la faim, a la pauvrete, a la maladie chronique ;
    remission, traitement, suicide."""
    ix = med.ix; n = ix.n
    col = p.colonnes["habitant"]
    mm, mj = col["med_mental"], col["med_mental_j"]
    rng = p.du_jour("medecine_mental")
    u = rng.random((n, 5))
    adulte = ix.vivant & (ix.age >= 15)
    rr = (np.where(ix.faim > 1.0, RR_FAIM_MENTAL, 1.0) * np.where(ix.pauvre, RR_PAUVRE_MENTAL, 1.0)
          * np.where(col["med_chroniques"][:n] > 0, RR_CHRONIQUE_MENTAL, 1.0)
          * np.where(ix.sexe == POP.FEMME, RR_FEMME_MENTAL, 1.0))
    for bit, prev, duree, j in ((DEPRESSION, PREVALENCE_DEPRESSION, DUREE_DEPRESSION_J, 0),
                                (ANXIETE, PREVALENCE_ANXIETE, DUREE_ANXIETE_J, 1)):
        mu = 1.0 / duree
        lam = mu * prev / (1.0 - prev) / 1.6
        a = mm[:n] & bit > 0
        debut = adulte & ~a & (u[:, j] < lam * rr)
        mu_i = mu * np.where((bit == DEPRESSION) & (mm[:n] & DEP_TRAITEE > 0), 1.5, 1.0)
        fin = a & (u[:, j + 2] < mu_i)
        mm[:n] = np.where(debut, mm[:n] | bit, mm[:n])
        mm[:n] = np.where(fin, mm[:n] & np.uint8(0xFF ^ bit), mm[:n])
        if bit == DEPRESSION:
            mm[:n] = np.where(fin, mm[:n] & np.uint8(0xFF ^ DEP_TRAITEE), mm[:n])
            traite = debut & (u[:, 4] < PART_DEPRESSION_TRAITEE)
            mm[:n] = np.where(traite, mm[:n] | DEP_TRAITEE, mm[:n])
            mj[:n] = np.where(debut, p.jour, mj[:n])
            if debut.any(): p.compter("episode_depressif", float(debut.sum()))
    dep = np.nonzero(ix.vivant & (mm[:n] & DEPRESSION > 0))[0]
    if len(dep):
        risque = SUICIDE_AN_DEPRIME / JOURS_AN * np.where(mm[dep] & DEP_TRAITEE > 0, 1.0, 1.5)
        for hid in dep[p.du_jour("medecine_suicide").random(len(dep)) < risque].tolist():
            _tuer(p, med, hid, "violence", "suicide")


def _grossesses(p, med, t):
    """Pre-eclampsie ( apres 20 semaines ), hemorragie du post-partum ( a l accouchement vu le matin ), et la fin d une
    pre-eclampsie a l accouchement."""
    ix = med.ix; n = ix.n
    col = p.colonnes["habitant"]
    rng = p.du_jour("medecine_grossesse")
    enc, conc = col["enceinte"][:n] == 1, col["conception_j"][:n]
    pe = col["med_pe_conception"]
    h_pe = -math.log(1.0 - 0.03) / 126.0
    cand = np.nonzero(ix.vivant & enc & (p.jour - conc >= 140) & (pe[:n] != conc))[0]
    for hid in cand[rng.random(len(cand)) < h_pe].tolist():
        pe[hid] = conc[hid]
        _cas_non_infectieux(p, med, hid, "pre_eclampsie", t, rng)
        p.noter("complication_grossesse", habitant=hid, complication="pre_eclampsie")
    # une pre-eclampsie se termine avec la grossesse
    A = med.aff
    for hid in list(med.par_hab):
        for s in med.par_hab.get(hid, ()):
            if A.path[s] == IP["pre_eclampsie"] and not col["enceinte"][hid]:
                A.t_gueri[s] = min(A.t_gueri[s], t); A.t_fin[s] = min(A.t_fin[s], t)
    acc, vu = col["accouchement_j"][:n], col["med_accouchement_vu"]
    neuves = np.nonzero(ix.vivant & (acc > vu[:n]) & (acc >= 0))[0]
    vu[neuves] = acc[neuves]
    for hid in neuves[rng.random(len(neuves)) < 0.05].tolist():
        s = _cas_non_infectieux(p, med, hid, "hemorragie_post_partum", t, rng)
        if s is None: continue
        severe = rng.random() < 0.3
        med.aff.g[s] = med.aff.g2[s] = med.aff.gmax[s] = 0.6 if severe else 0.35
        med.aff.letal[s] = 0.03 if severe else 0.003
        med.aff.sang[s] = 2 if severe else 0           # culots de sang necessaires
        _synchroniser(p, med, hid)
        p.noter("complication_grossesse", habitant=hid, complication="hemorragie_post_partum")
        p.w.soigner(p.w.habitants[hid])


def _importations(p, med, t):
    """Les cas qui arrivent de l exterieur ( voyageurs, saison ), et les pneumonies qui tombent sans contagion."""
    ix = med.ix; n = ix.n
    rng = p.du_jour("medecine_importations")
    viv = np.nonzero(ix.vivant)[0]
    if not len(viv): return
    ja = _jour_an(p)
    for m in MALADIES:
        if m.import_100k <= 0: continue
        lam = m.import_100k * len(viv) / 1e5 * facteur_saison(m, ja, med.saison_forcee.get(m.nom))
        k = int(rng.poisson(lam))
        if k: infecter(p, rng.choice(viv, k), m.nom, t, rng, importe=True)
    m = PATHOS[IP["pneumonie"]]
    h_j = par_age(m.incidence, ix.age[viv]) / JOURS_AN * rr_normalise(p.col("habitant", "med_chroniques")[viv], ix.age[viv],
                                                                       RR_PNEUMONIE)
    for hid in viv[rng.random(len(viv)) < h_j].tolist(): _cas_sporadique(p, med, hid, "pneumonie", t)
    # tuberculose latente qui se reveille
    lat = np.nonzero(ix.vivant & (med.statut[:n, IM["tuberculose"]] == 2))[0]
    if len(lat):
        r = REACTIVATION_TB_AN / JOURS_AN * np.where(p.col("habitant", "med_chroniques")[lat] & DIABETE > 0, 3.0, 1.0)
        for hid in lat[rng.random(len(lat)) < r].tolist():
            med.statut[hid, IM["tuberculose"]] = 0
            _reactiver(p, med, hid, t, rng)
            p.compter("reactivation_tb")


def _reactiver(p, med, hid, t, rng):
    m = PATHOS[IP["tuberculose"]]
    hist = tirer_histoires(m, t, _ages(p, [hid]), rng, _rr_individuel(p, med, np.array([hid]), m))
    # une reactivation n a pas de latence : elle devient contagieuse tout de suite
    d = hist["t_inf"][0] - t
    for c in ("t_inf", "t_symp", "t_fin_cont", "t_gueri", "t_fin", "t_aggr"): hist[c] = hist[c] - d
    res = rng.random() < med.resistance[med.ix.region[hid], IABX["antituberculeux"]]
    _creer(p, med, hid, IP["tuberculose"], t, hist, 0, resistant=bool(res))
    med.infecte[hid, IM["tuberculose"]] = 1
    _synchroniser(p, med, hid)


def risque_eau(p, med):
    """Le multiplicateur du risque de gastro-enterite d origine hydrique, par lieu : penurie d eau du bassin sur 7 jours
    ( hygiene, stockage ), pollution de l eau brute, crue en cours, chaleur."""
    T = p.domaine("territoire"); B = T.bassins
    dem = B.h_dem.sum(1)
    pen = np.divide(B.h_manque.sum(1), dem, out=np.zeros_like(dem), where=dem > 0)
    crues = {c.lieu for c in TER.catastrophes_en_cours(p, type_="inondation")}
    out = np.ones(len(med.lieux))
    for k, l in enumerate(med.lieux):
        if l.type not in ("capitale", "ville", "village"): continue
        b = TER.bassin_de(p, l.id)
        eau = TER.pollution(p, l.id)[1]
        tm = TER.meteo(p, l.id).tmoy
        out[k] = ((1.0 + K_PENURIE * pen[b]) * (1.0 + K_POLLUTION * min(3.0, eau)) * (K_CRUE if B.nom[b] in crues else 1.0)
                  * math.exp(K_TEMPERATURE * max(0.0, tm - T_SEUIL)))
    return out


def _eau(p, med, t):
    ix = med.ix
    mult = risque_eau(p, med)
    ok = ix.vivant & (ix.dom >= 0)
    h_j = np.where(ok, GASTRO_EAU_AN / JOURS_AN * mult[np.maximum(ix.dom, 0)], 0.0)
    u = p.du_jour("medecine_eau").random(ix.n)
    cand = np.nonzero(u < h_j)[0]
    if len(cand):
        faits = infecter(p, cand, "gastro", t, p.du_jour("medecine_eau_hist"))
        if faits: p.compter("gastro_hydrique", float(len(faits)))
    med.compter("gastro_hydrique_attendue", float(h_j.sum()))


def vacciner(p, h, vaccin, stock=None):
    """Une dose de vaccin ( ror, grippe, covid ) : sortie de la pharmacie, protection tout ou rien selon l efficacite.
    Rend vrai si la dose a ete faite."""
    if vaccin not in VACCINS: raise ValueError(f"vaccin inconnu {vaccin!r} : {VACCINS}")
    med = p.domaine("medecine")
    ph = stock if stock is not None else pharmacie_de(p, h)
    if prendre(p, ph, "vaccin_" + vaccin, 1.0, "vaccination") < 1.0 - 1e-9:
        p.compter("vaccin_manquant"); return False
    rng = p.hasard("medecine_vaccins")
    v = VACCINS.index(vaccin); hid = h.id
    d = int(med.doses[hid, v]) + 1
    med.doses[hid, v] = min(100, d)
    if vaccin == "ror":
        k = IM["rougeole"]
        deja = med.statut[hid, k] == 1 and med.immun_fin[hid, k] > p.jour + 3650
        p_eff = EFFICACITE_ROR[0] if d == 1 else (EFFICACITE_ROR[1] - EFFICACITE_ROR[0]) / (1.0 - EFFICACITE_ROR[0])
        if not deja and rng.random() < p_eff: med.statut[hid, k] = 1; med.immun_fin[hid, k] = IMMUNITE_A_VIE
    elif vaccin == "grippe":
        k = IM["grippe"]
        if rng.random() < EFFICACITE_GRIPPE:
            d_ = p.socle.calendrier.date(p.w.pas)
            fin = (365 - _jour_an(p)) + 181          # jusqu a la fin juin suivante
            med.statut[hid, k] = 1; med.immun_fin[hid, k] = max(int(med.immun_fin[hid, k]), p.jour + fin)
        med.vacc_saison[hid] = p.socle.calendrier.date(p.w.pas).year
    else:
        k = IM["covid"]
        if rng.random() < 0.6: med.statut[hid, k] = 1; med.immun_fin[hid, k] = p.jour + 180
    p.compter("vaccination")
    return True


def _vaccinations(p, med):
    """Le calendrier vaccinal : ROR a 12 mois et a 5 ans, grippe des plus de 65 ans et des malades chroniques
    d octobre a decembre."""
    ix = med.ix; n = ix.n; H = p.w.habitants
    rng = p.du_jour("medecine_calendrier")
    age_j = p.jour - p.col("habitant", "naissance_j")[:n]
    d = med.doses[:n, 0]
    u = rng.random(n)
    p1 = 1.0 - (1.0 - COUVERTURE_ROR[0]) ** (1.0 / 30.0)                          # la couverture atteinte en un mois
    p2 = 1.0 - (1.0 - COUVERTURE_ROR[1] / COUVERTURE_ROR[0]) ** (1.0 / 30.0)
    for dose, age0, pj in ((0, AGE_ROR_J[0], p1), (1, AGE_ROR_J[1], p2)):
        for hid in np.nonzero(ix.vivant & (d == dose) & (age_j >= age0) & (age_j < age0 + 30) & (u < pj))[0].tolist():
            vacciner(p, H[hid], "ror")
    ja = _jour_an(p)
    if CAMPAGNE_GRIPPE[0] <= ja < CAMPAGNE_GRIPPE[1]:
        annee = p.socle.calendrier.date(p.w.pas).year
        cible = ix.vivant & ((ix.age >= 65) | (p.col("habitant", "med_chroniques")[:n] > 0)) & (med.vacc_saison[:n] != annee)
        pj = 1.0 - (1.0 - COUVERTURE_GRIPPE) ** (1.0 / (CAMPAGNE_GRIPPE[1] - CAMPAGNE_GRIPPE[0]))
        for hid in np.nonzero(cible & (rng.random(n) < pj))[0].tolist(): vacciner(p, H[hid], "grippe")


def _resistance(p, med):
    """L usage du jour ( DDD pour 1 000 habitants ) entre dans la moyenne mobile ; la resistance suit sa loi."""
    for r, ph in enumerate(med.pharmacies):
        pop = max(1, ph.pop)
        for a, ab in enumerate(ANTIBIOTIQUES):
            u = med.ddd_jour[r, a] / (pop / 1000.0)
            med.usage[r, a] += (u - med.usage[r, a]) / EMA_USAGE_J
            med.resistance[r, a] = ab.pas(med.resistance[r, a], med.usage[r, a])
    med.ddd_jour[:] = 0.0
    for ph in med.pharmacies:
        ph.conso += (ph.sortie_jour - ph.conso) / 30.0
        ph.sortie_jour[:] = 0.0


def resistance(p, lieu, antibiotique="amoxicilline"):
    """La part des germes resistants a un antibiotique dans la region d un lieu ( la verite, pour les portes et le
    domaine 17 ; le bulletin public en est la valeur du mois precedent )."""
    med = p.domaine("medecine")
    lid = lieu if isinstance(lieu, str) else lieu.id
    return float(med.resistance[med.region_de_lieu[p.w.carte.lieux[lid].marche.id], IABX[antibiotique]])


def _surveillance(p, med):
    """Les cas declares ( diagnostiques ) des 14 derniers jours, par region et par maladie ; une epidemie se declare
    quand une maladie depasse 1 % de la region en une semaine ( au moins 5 cas )."""
    med.declares = np.roll(med.declares, 1, axis=2); med.declares[:, :, 0] = 0
    semaine = med.declares[:, :, :7].sum(2)
    for r, ph in enumerate(med.pharmacies):
        for k, nom in enumerate(INFECTIEUSES):
            c = int(semaine[r, k])
            if c >= max(5, 0.01 * ph.pop) and p.jour - med.epidemies.get((r, nom), -999) > 30:
                med.epidemies[(r, nom)] = p.jour
                p.noter("epidemie_declaree", maladie=nom, lieu=ph.lieu, cas=c)


def _declarer(med, region, nom):
    if nom in IM: med.declares[region, IM[nom], 0] += 1


def _journee(p):
    """Monde.progression_maladie, a l aube : tout ce qui se decide ou se voit une fois par jour."""
    med = p.domaine("medecine"); w = p.w
    t = w.minutes / 1440.0
    _index_du_jour(p, med)
    _purger_morts(p, med)
    _etalonner(p, med)
    _surveillance(p, med)
    _chroniques(p, med, t)
    _mental(p, med)
    _grossesses(p, med, t)
    _importations(p, med, t)
    _eau(p, med, t)
    _vaccinations(p, med)
    _clinique(p, med, t)
    _perimer(p, med)
    if p.jour % 7 == 0: _reapprovisionner(p, med)
    _resistance(p, med)
    for hid in med.par_hab:
        h = w.habitants[hid]
        if h.vivant and h.etat != "S": h.jours_etat += 1.0


# ================================================================== soins : la ville et l hopital
def _cliniques(med, hid):
    A = med.aff
    return [s for s in med.par_hab.get(hid, ()) if A.phase[s] == CLINIQUE and not A.asym[s] and A.g[s] > 0]


def symptomes_visibles(p, h):
    """Le masque des symptomes que l habitant montre ( ce que voient lui-meme et le medecin )."""
    med = p.domaine("medecine"); A = med.aff
    m = 0
    for s in _cliniques(med, h.id): m |= int(A.symp[s])
    return m


def sante_du_jour(p, h):
    """La sante d un habitant aujourd hui, pour les notes : 0 s il est mort, 1 - gravite / 0,5 sinon."""
    if not h.vivant: return 0.0
    med = p.domaine("medecine")
    g = max((float(med.aff.g[s]) for s in _cliniques(med, h.id)), default=0.0)
    return max(0.0, 1.0 - g / 0.5)


def _a_priori(p, med, region, t):
    ja = _jour_an(p)
    dec = med.declares[region].sum(1)
    pop = max(1, med.pharmacies[region].pop)
    out = {}
    for nom, base in A_PRIORI.items():
        m = PATHOS[IP[nom]]
        out[nom] = base * facteur_saison(m, ja, med.saison_forcee.get(nom)) * (1.0 + 20.0 * dec[IM[nom]] / pop * 100.0)
    return out


def examiner(p, h, examen, slots=None):
    """Fait un examen a h : positif ou negatif, selon qu il porte vraiment la cible, avec la sensibilite et la
    specificite de l examen. Le medecin ne voit que le resultat."""
    ex = EX[examen]
    med = p.domaine("medecine")
    vrai = any(PATHOS[med.aff.path[s]].nom == ex.cible for s in (slots if slots is not None else _cliniques(med, h.id)))
    p.compter("test_diagnostique")
    return bool(resultat_examen(ex, [vrai], p.hasard("medecine_examens").random(1))[0])


def diagnostiquer(p, h, lieu="hopital"):
    """Le diagnostic d un medecin : une affection evidente ( lesion, complication ) est vue telle qu elle est ; sinon
    le plus probable au vu des symptomes et de la surveillance, puis les examens du lieu ( cabinet, hopital ) sur les
    trois premiers candidats : le premier positif l emporte. Rend ( nom diagnostique, examens faits )."""
    med = p.domaine("medecine"); A = med.aff
    cl = _cliniques(med, h.id)
    if not cl: return None, []
    ev = [s for s in cl if PATHOS[A.path[s]].evidente]
    if ev: return PATHOS[A.path[max(ev, key=lambda s: A.g[s])]].nom, []
    masque = 0
    for s in cl: masque |= int(A.symp[s])
    region = med.ix.region[h.id] if h.id < med.ix.n else 0
    diag, tri = diagnostic_clinique(masque, _a_priori(p, med, region, 0))
    faits = []
    for nom in tri[:3]:
        exs = [e for e in EXAMEN_DE.get(nom, ()) if lieu == "hopital" or EX[e].lieu == "cabinet"]
        if not exs: continue
        faits.append(exs[-1])
        if examiner(p, h, exs[-1], cl): return nom, faits
    return diag, faits


def _appliquer(p, med, s, nom_mol, t):
    """L effet d une molecule sur une affection ( si elle en a un ) ; rend vrai si c est son traitement specifique
    efficace."""
    A = med.aff
    m = PATHOS[A.path[s]]
    e = EFFETS.get((m.nom, nom_mol))
    if e is None: return False
    if e.fenetre_j is not None and t - A.t_symp[s] > e.fenetre_j: return False
    if nom_mol in ABX and m.bacterie:
        if nom_mol != "ceftriaxone": resistant = bool(A.resistant[s])
        else:
            r2 = med.resistance[A.region[s], IABX["ceftriaxone"]] * GERME_RESISTANCE.get(m.nom, 1.0)
            resistant = bool(p.hasard("medecine_examens").random() < r2)
        if resistant:
            A.soin[s] |= ECHEC; return False
    A.mult[s] *= e.f_letal
    if e.prevention is not None and t < A.t_aggr[s]: A.prev[s] *= e.prevention
    if e.cure_j is not None: A.t_gueri[s] = t + e.cure_j
    elif e.f_duree is not None and e.f_duree != 1.0 and t < A.t_gueri[s] < INF:
        A.t_gueri[s] = t + (A.t_gueri[s] - t) * e.f_duree
    if e.fin_contagion_j is not None: A.t_fin_cont[s] = min(A.t_fin_cont[s], t + e.fin_contagion_j)
    if not A.asym[s]: A.t_fin[s] = max(A.t_gueri[s] if A.t_gueri[s] < INF else t, A.t_fin_cont[s])
    if e.specifique:
        A.soin[s] |= SPECIFIQUE; A.soin[s] &= ~ECHEC
    return e.specifique


def _indesirable(p, med, hid, nom_mol, t):
    leger, grave = MOL[nom_mol].indesirables
    if leger <= 0 and grave <= 0: return
    rng = p.hasard("medecine_indesirables")
    u = rng.random()
    if u < grave: _cas_non_infectieux(p, med, hid, "effet_indesirable_grave", t, rng); p.compter("effet_indesirable")
    elif u < grave + leger: _cas_non_infectieux(p, med, hid, "effet_indesirable", t, rng); p.compter("effet_indesirable")


def traiter(p, h, slots, molecule, unites, detenteur=None, motif="soin", t=None):
    """Donne `unites` d une molecule a h, prises au detenteur ( sa pharmacie par defaut ), et l applique a ses
    affections `slots` ( toutes ses affections cliniques si None ). Rend ( unites prises, traitement specifique
    efficace sur au moins une ). Le domaine 17 l appelle avec ses propres stocks."""
    med = p.domaine("medecine")
    t = p.w.minutes / 1440.0 if t is None else t
    ph = detenteur if detenteur is not None else pharmacie_de(p, h)
    pris = prendre(p, ph, molecule, unites, motif, region=med.region_de_lieu[h.domicile.marche.id])
    if pris < unites - 1e-9:
        if pris <= 0: p.noter("rupture_sante", bien=molecule, lieu=getattr(ph, "lieu", "?"))
        return pris, False
    ok = False
    for s in (slots if slots is not None else _cliniques(med, h.id)):
        if med.aff.actif[s] and med.aff.hab[s] == h.id: ok |= _appliquer(p, med, s, molecule, t)
    _indesirable(p, med, h.id, molecule, t)
    if molecule in ABX: p.compter("prescription_antibiotique")
    return pris, ok


def _kit_e1(p, h):
    """Le kit de soins du moteur ( remedes ) : du stock public des hopitaux, sinon achete au marche par le menage,
    comme Monde.soigner."""
    w = p.w; L = p.socle.livre
    if w.publics["hopitaux"]["remedes"] >= 1:
        w.publics["hopitaux"]["remedes"] -= 1; L.flux["consomme"]["remedes"] += 1; return True
    m = w.marches[h.domicile.marche.id]
    m.demande["remedes"] += 1
    prix = m.prix["remedes"] * (1 + w.gouv.tva)
    if m.stocks["remedes"] >= 1 and h.menage.caisse >= prix:
        m.stocks["remedes"] -= 1; L.flux["consomme"]["remedes"] += 1
        L.transferer(h.menage, m, m.prix["remedes"], "remede")
        L.transferer(h.menage, w.gouv, m.prix["remedes"] * w.gouv.tva, "tva")
        return True
    return False


def besoins(p, h):
    """Ce qu il faut a h, pour le triage du domaine 17 : { lit, reanimation, chirurgie, sang ( culots ), oxygene }."""
    med = p.domaine("medecine"); A = med.aff
    out = {"lit": False, "reanimation": False, "chirurgie": False, "sang": 0, "oxygene": False}
    for s in _cliniques(med, h.id):
        m = PATHOS[A.path[s]]
        g = max(float(A.g[s]), float(A.g2[s]) if A.t_aggr[s] < INF else 0.0)
        out["lit"] |= float(A.g[s]) > GRAVITE_HOPITAL
        out["reanimation"] |= float(A.g[s]) >= G_CRITIQUE[0]
        if m.groupe == "lesion":
            iss = int(A.iss[s]); pen = m.nom[7:] in PENETRANTES
            out["chirurgie"] |= iss >= 16 or (pen and iss >= 9)
            out["sang"] += 4 if iss >= 25 else 2 if (pen and iss >= 16) else 0
        out["sang"] += int(A.sang[s])
        out["oxygene"] |= m.nom in RESPIRATOIRES and g > GRAVITE_ALITE
    return out


def priorite(p, h):
    """La categorie de triage ( START simplifie ) : 1 immediat, 2 urgent, 3 differe, 4 depasse ( ISS 75 ), 0 rien."""
    med = p.domaine("medecine"); A = med.aff
    cl = _cliniques(med, h.id)
    if not cl: return 0
    if any(A.iss[s] >= 75 for s in cl): return 4
    g = max(float(A.g[s]) for s in cl)
    return 1 if g >= G_CRITIQUE[0] else 2 if g > GRAVITE_HOPITAL else 3


def soigner_defaut(p, h):
    """Le soin par defaut ( Monde.soigner ) : un medecin de l hopital de sa capitale diagnostique, puis donne le
    protocole du diagnostic et le soin de soutien ( kit du moteur, oxygene d un malade respiratoire grave, chirurgie et
    sang d un blesse ). Un diagnostic faux donne le mauvais traitement. Rend vrai si le soutien a ete donne."""
    if not h.vivant: return False
    med = p.domaine("medecine"); A = med.aff
    t = p.w.minutes / 1440.0
    tous = _cliniques(med, h.id)
    cl = [s for s in tous if A.consulte[s] < 2]
    ph = pharmacie_de(p, h)
    if not cl:                                   # deja vu : seul le soutien qui a manque est retente
        manque = [s for s in tous if A.consulte[s] == 2 and not A.soin[s] & SOUTIEN]
        return _soutien(p, med, h, ph, manque) if manque else False
    diag, _ = diagnostiquer(p, h, "hopital")
    region = int(A.region[cl[0]])
    if diag is not None: _declarer(med, region, diag)
    vrai = {PATHOS[A.path[s]].nom for s in cl}
    if diag not in vrai: p.compter("diagnostic_errone"); med.compter("diagnostics_errones")
    med.compter("diagnostics")
    for mol, u, _ in PROTOCOLE_HOPITAL.get(diag, ()): traiter(p, h, cl, mol, u, ph, "soin_hopital", t)
    if diag == "tuberculose":
        for s in cl:
            if PATHOS[A.path[s]].nom == "tuberculose" and A.soin[s] & SPECIFIQUE:
                p.poser(RENOUVELLEMENT_TB[0] * PAS_J, "medecine_renouvellement", h.id, (s, int(A.gen[s]), 1))
    for s in cl:
        if PATHOS[A.path[s]].groupe == "lesion":
            iss = int(A.iss[s])
            prendre(p, ph, "morphine" if iss >= 9 else "paracetamol", 3.0, "soin_hopital")
            if PATHOS[A.path[s]].nom[7:] in PENETRANTES: traiter(p, h, [s], "amoxicilline", 5, ph, "soin_hopital", t)
        A.consulte[s] = 2
    p.compter("hospitalisation")
    return _soutien(p, med, h, ph, cl)


def _soutien(p, med, h, ph, slots):
    """Le soin de soutien d un hospitalise : le kit du moteur, l oxygene d un malade respiratoire grave, l anesthesie et le
    sang d un blesse a operer. Tout ou rien : ce qui manque se retente le lendemain."""
    A = med.aff
    b = besoins(p, h)
    soutien = _kit_e1(p, h)
    if soutien and b["oxygene"]: soutien = prendre(p, ph, "oxygene", 5.0, "soin_hopital") >= 5.0 - 1e-9
    if soutien and b["chirurgie"]: soutien = prendre(p, ph, "anesthesique", 1.0, "soin_hopital") >= 1.0 - 1e-9
    if soutien and b["sang"]: soutien = prendre(p, ph, "sang", float(b["sang"]), "soin_hopital") >= b["sang"] - 1e-9
    if soutien:
        for s in slots: A.soin[s] |= SOUTIEN
    else: p.compter("sans_soin")
    _synchroniser(p, med, h.id)
    return soutien


def a_soigner(p, h):
    """Vrai si h est hospitalise ( gravite > 0,3 ) et qu une de ses affections n a pas encore recu son soin : pas encore
    vue a l hopital, ou vue sans le soutien qu il lui faut."""
    med = p.domaine("medecine"); A = med.aff
    cl = _cliniques(med, h.id)
    if not cl or max(float(A.g[s]) for s in cl) <= GRAVITE_HOPITAL: return False
    return any(A.consulte[s] < 2 or not A.soin[s] & SOUTIEN for s in cl)


def prise_en_charge(p, h, soutien=True, slots=None):
    """Pour le domaine 17 : ses soins ont ete donnes a h ( lit, surveillance, et le soutien s il est vrai ) ; ce domaine
    ne le renverra plus a Monde.soigner pour ces affections. Les molecules se donnent par `traiter`."""
    med = p.domaine("medecine"); A = med.aff
    for s in (slots if slots is not None else _cliniques(med, h.id)):
        A.consulte[s] = 2
        if soutien: A.soin[s] |= SOUTIEN
    _synchroniser(p, med, h.id)


def _renouvellement(p, hid, donnees):
    """Le mois suivant d un traitement de la tuberculose : sans doses, le traitement s interrompt et la maladie reprend
    son cours naturel."""
    s, gen, n = donnees
    med = p.domaine("medecine"); A = med.aff
    if s >= A.k or not A.actif[s] or A.gen[s] != gen or A.hab[s] != hid: return
    h = p.w.habitants[hid]
    if not h.vivant: return
    pris = prendre(p, pharmacie_de(p, h), "antituberculeux", float(RENOUVELLEMENT_TB[0]), "soin_hopital")
    t = p.w.minutes / 1440.0
    if pris < RENOUVELLEMENT_TB[0] - 1e-9:
        m = PATHOS[A.path[s]]
        A.soin[s] = (A.soin[s] & ~SPECIFIQUE) | ECHEC
        A.t_gueri[s] = t + float(_gamma(p.hasard("medecine_infections"), m.maladie, 1)[0])
        A.t_fin_cont[s] = t + float(_gamma(p.hasard("medecine_infections"), m.contagion, 1)[0])
        A.t_fin[s] = max(A.t_gueri[s], A.t_fin_cont[s])
        p.noter("rupture_sante", bien="antituberculeux", lieu=pharmacie_de(p, h).lieu)
    elif n < RENOUVELLEMENT_TB[1]:
        p.poser(RENOUVELLEMENT_TB[0] * PAS_J, "medecine_renouvellement", hid, (s, gen, n + 1))


def _clinique(p, med, t):
    """Chaque matin, pour chaque malade : l hospitalise non encore soigne est soigne ( Monde.soigner, celui qui le
    tient ) ; les autres decident, a leurs jours de decision, s ils consultent."""
    A = med.aff; w = p.w; H = w.habitants
    dec = med.dec_consulter
    for hid in list(med.par_hab):
        h = H[hid]
        if not h.vivant: continue
        cl = _cliniques(med, hid)
        if not cl: continue
        g = max(float(A.g[s]) for s in cl)
        if g > GRAVITE_HOPITAL:
            if a_soigner(p, h): w.soigner(h)
            continue
        nv = [s for s in cl if A.consulte[s] == 0 and PATHOS[A.path[s]].groupe in ("infection", "sporadique", "iatrogene")]
        if not nv: continue
        jours = int(t - min(float(A.t_symp[s]) for s in nv))
        if jours not in JOURS_DECISION: continue
        x = _traits_consulter(p, med, h, cl, jours, g)
        a = dec.decider(hid, ContexteConsulter(x))
        _suivre(med, "consulter", a, hid, cl, p.jour)
        if a == 1:
            dec.ajouter(hid, -COUT_NOTE_CONSULTATION)
            consulter_medecin(p, h, t)


def _traits_consulter(p, med, h, cl, jours, g):
    A = med.aff
    masque = 0
    for s in cl: masque |= int(A.symp[s])
    ix = med.ix; hid = h.id
    mg = h.menage
    viv = max(1, sum(1 for x in mg.membres if x.vivant))
    prix = p.w.marches[h.domicile.marche.id].prix["nourriture"]
    caisse = mg.caisse / max(1e-6, viv * C.NOURRITURE_PAR_JOUR * prix)
    km = p.w.carte.km_route(h.domicile, h.domicile.marche) if h.domicile is not h.domicile.marche else 0.0
    region = ix.region[hid] if hid < ix.n else 0
    rum = med.declares[region, :, :7].sum() / max(1, med.pharmacies[region].pop) * 100.0
    age = ix.age[hid] if hid < ix.n else 0.0
    ch = p.col("habitant", "med_chroniques")[hid] > 0
    return (1.0 if masque & BIT["fievre"] else 0.0, 1.0 if masque & BIT["toux"] else 0.0,
            1.0 if masque & BIT["dyspnee"] else 0.0, 1.0 if masque & (BIT["diarrhee"] | BIT["vomissement"]) else 0.0,
            1.0 if masque & BIT["gorge"] else 0.0, min(1.0, jours / 28.0), min(1.0, g / 0.3),
            min(1.0, max(0.0, age) / 90.0), 1.0 if ch else 0.0, min(1.0, max(0.0, caisse) / 30.0),
            min(1.0, km / 30.0), min(1.0, rum / 5.0))


def consulter_medecin(p, h, t=None):
    """Une consultation en ville : la consultation se paie, le medecin diagnostique ( symptomes, examens du cabinet ),
    decide de l antibiotique ( point `prescrire` ) devant une fievre, une toux ou une angine, et donne ce que son
    diagnostic demande ( antiviral d un malade a risque, rehydratation, traitement de la tuberculose )."""
    med = p.domaine("medecine"); A = med.aff; w = p.w; L = p.socle.livre
    t = w.minutes / 1440.0 if t is None else t
    cl = _cliniques(med, h.id)
    if not cl: return None
    L.transferer(h.menage, w.gouv, TARIF_CONSULTATION, "consultation_medicale")
    p.compter("consultation")
    ph = pharmacie_de(p, h)
    diag, _ = diagnostiquer(p, h, "cabinet")
    region = int(A.region[cl[0]])
    if diag is not None: _declarer(med, region, diag)
    vrai = {PATHOS[A.path[s]].nom for s in cl}
    if diag not in vrai: p.compter("diagnostic_errone"); med.compter("diagnostics_errones")
    med.compter("diagnostics"); med.compter("consultations")
    masque = 0
    for s in cl: masque |= int(A.symp[s])
    jours = t - min(float(A.t_symp[s]) for s in cl)
    age = float(_ages(p, [h.id])[0])
    risque = age >= 65 or p.col("habitant", "med_chroniques")[h.id] > 0 or p.col("habitant", "enceinte")[h.id] == 1
    unites = []
    if masque & (BIT["fievre"] | BIT["toux"] | BIT["gorge"]) and diag != "tuberculose":
        x = _traits_prescrire(p, med, h, masque, jours, age, region, ph)
        a = med.dec_prescrire.decider(h.id, ContextePrescrire(x))
        _suivre(med, "prescrire", a, h.id, cl, p.jour)
        donner = a == ANTIBIOTIQUE
        if a == TESTER:
            ex = "tdr_strep" if masque & BIT["gorge"] and not masque & BIT["toux"] else "radio_thorax"
            donner = examiner(p, h, ex, cl)
        if donner:
            pris, _ = traiter(p, h, cl, "amoxicilline", COURS_ANTIBIOTIQUE, ph, "soin_ville", t)
            unites.append(("amoxicilline", pris))
            med.dec_prescrire.ajouter(h.id, -POIDS_RESISTANCE * pris * MOL["amoxicilline"].ddd / DDD_COURS_REF)
    if diag == "grippe" and risque and jours <= 2:
        unites.append(("oseltamivir", traiter(p, h, cl, "oseltamivir", 5, ph, "soin_ville", t)[0]))
    if diag == "covid" and (age >= 60 or risque) and jours <= 5 and examiner(p, h, "antigene_covid", cl):
        unites.append(("antiviral_covid", traiter(p, h, cl, "antiviral_covid", 5, ph, "soin_ville", t)[0]))
    if diag == "gastro": unites.append(("sro", traiter(p, h, cl, "sro", 3, ph, "soin_ville", t)[0]))
    if masque & BIT["toux"] and jours >= 14 and examiner(p, h, "crachat_bk", cl):
        pris, ok = traiter(p, h, cl, "antituberculeux", RENOUVELLEMENT_TB[0], ph, "soin_ville", t)
        for s in cl:
            if PATHOS[A.path[s]].nom == "tuberculose" and A.soin[s] & SPECIFIQUE:
                p.poser(RENOUVELLEMENT_TB[0] * PAS_J, "medecine_renouvellement", h.id, (s, int(A.gen[s]), 1))
    if masque & BIT["fievre"]: unites.append(("paracetamol", prendre(p, ph, "paracetamol", 3.0, "soin_ville")))
    part = sum(q * MOL[n].prix for n, q in unites) * PARTICIPATION
    if part > 0: L.transferer(h.menage, w.gouv, part, "participation_medicaments")
    for s in cl: A.consulte[s] = max(int(A.consulte[s]), 1)
    _synchroniser(p, med, h.id)
    return diag


def _traits_prescrire(p, med, h, masque, jours, age, region, ph):
    dec = med.declares[region, :, :14].sum(1)
    resp = dec[IM["grippe"]] + dec[IM["covid"]] + dec[IM["rhume"]] + dec[IM["angine"]] + dec[IM["pneumonie"]]
    virale = (dec[IM["grippe"]] + dec[IM["covid"]]) / resp if resp > 0 else 0.0
    b = med.id_mol["amoxicilline"]
    jours_stock = ph.stock[b] / max(1e-6, max(ph.conso[IMOL["amoxicilline"]], 1.0))
    return (1.0 if masque & BIT["fievre"] else 0.0, 1.0 if masque & BIT["toux"] else 0.0,
            1.0 if masque & BIT["gorge"] else 0.0, 1.0 if masque & BIT["dyspnee"] else 0.0,
            min(1.0, max(0.0, jours) / 14.0), min(1.0, max(0.0, age) / 90.0),
            1.0 if p.col("habitant", "med_chroniques")[h.id] > 0 else 0.0, float(virale),
            min(1.0, float(med.resistance[region, IABX["amoxicilline"]]) / 0.5), min(1.0, jours_stock / 60.0))


def _suivre(med, point, action, hid, cl, jour):
    """Le registre des decisions ( pour les portes ) : l action, la verite ( une infection bacterienne ? ) et la sante
    du patient sur l horizon, SANS le cout ni la penalite de la note."""
    A = med.aff
    bact = any(PATHOS[A.path[s]].bacterie for s in cl)
    med.suivi.append([point, int(action), bool(bact), hid, jour, 0.0, 0])
    if len(med.suivi) > 50000: del med.suivi[:10000]


def _cloture(p, comptes):
    """Le soir : chaque decision en attente recoit la sante du jour de son patient."""
    med = p.domaine("medecine"); H = p.w.habitants
    for dec in (med.dec_consulter, med.dec_prescrire):
        for cle in [k for k, a in dec.attentes.items() if a.choix]:
            dec.noter(cle, sante_du_jour(p, H[cle]), p.jour)
        for cle in [k for k, a in dec.attentes.items() if not a.choix]: del dec.attentes[cle]
    for e in reversed(med.suivi):                  # les plus recents d abord ; au-dela de l horizon, tout est note
        if e[4] < p.jour - HORIZON_SOINS: break
        if e[6] < HORIZON_SOINS: e[5] += sante_du_jour(p, H[e[3]]); e[6] += 1


# ================================================================== accidents de fond
def reprendre_accidents(p, quoi):
    """Un domaine ( travail 4, industrie 10, transport 14 ) produit desormais ses accidents : le fond s arrete."""
    if quoi not in ("travail", "route"): raise ValueError(f"accidents {quoi!r} : travail ou route")
    p.domaine("medecine").reprises.add(quoi)


def _tirer_iss(rng, dist):
    u = rng.random(); c = 0.0
    for (a, b), pr in dist:
        c += pr
        if u < c: return int(rng.integers(a, b + 1))
    return int(rng.integers(dist[-1][0][0], dist[-1][0][1] + 1))


def _accidents_travail(p):
    med = p.domaine("medecine")
    if "travail" in med.reprises: return
    H = p.w.habitants
    rng = p.du_jour("medecine_travail")
    par_role = {}
    for h in H:
        if h.vivant and h.poste == "travail" and h.role in ACCIDENTS_TRAVAIL: par_role.setdefault(h.role, []).append(h)
    for role in sorted(par_role):
        gens = par_role[role]
        k = int(rng.poisson(len(gens) * ACCIDENTS_TRAVAIL[role] / 1e5 / JOURS_OUVRES_AN))
        for _ in range(k):
            h = gens[int(rng.integers(0, len(gens)))]
            if h.vivant:
                blesser(p, h, "ecrasement" if role in ("mineur", "ouvrier") else "chute" if role == "paysan" else "travail",
                        _tirer_iss(rng, ISS_TRAVAIL))
                p.compter("accident_travail")


def _accidents_route(p):
    med = p.domaine("medecine")
    if "route" in med.reprises: return
    ix = med.ix
    rng = p.du_jour("medecine_route")
    cand = np.nonzero(ix.vivant & (ix.age >= 5))[0]
    k = int(rng.poisson(ix.vivant.sum() * ROUTE_VICTIMES_100K_AN / 1e5 / JOURS_AN))
    H = p.w.habitants
    for _ in range(k):
        h = H[int(cand[int(rng.integers(0, len(cand)))])]
        if h.vivant and h.poste not in ("hopital", "voyage"):
            blesser(p, h, "route", _tirer_iss(rng, ISS_ROUTE)); p.compter("accident_route")


# ================================================================== l API des autres domaines
def introduire(p, maladie, n=1, lieu=None):
    """Un scenario : `n` cas de `maladie` arrivent maintenant ( au lieu `lieu` s il est donne ), parmi les susceptibles."""
    if maladie not in IM: raise ValueError(f"maladie inconnue {maladie!r} : {INFECTIEUSES}")
    med = p.domaine("medecine"); w = p.w
    _assurer(p, med, len(w.habitants))
    rng = p.hasard("medecine_introduction")
    k = IM[maladie]
    cand = np.array([h.id for h in w.habitants if h.vivant and (lieu is None or h.domicile.id == lieu)], np.int64)
    if len(cand): cand = cand[(med.infecte[cand, k] == 0) & ~_immun(med, cand, k, p.jour)]
    if not len(cand): return []
    faits = infecter(p, rng.choice(cand, min(n, len(cand)), replace=False), maladie, rng=rng, importe=True)
    p.noter("introduction", maladie=maladie, lieu=lieu or "pays", cas=len(faits))
    return faits


def declencher(p, nom, n=1, lieu=None):
    """Un scenario : n cas d une pathologie qui ne s attrape pas d un autre ( pneumonie, decompensation, complication )
    surviennent maintenant, chez des habitants tires au hasard ( de `lieu` s il est donne ). Rend leurs identifiants."""
    if nom not in IP or PATHOS[IP[nom]].groupe not in ("sporadique", "decompensation", "iatrogene"):
        raise ValueError(f"{nom!r} ne se declenche pas ( pneumonie, decompensations, effets indesirables )")
    med = p.domaine("medecine"); w = p.w
    rng = p.hasard("medecine_introduction")
    cand = [h.id for h in w.habitants if h.vivant and (lieu is None or h.domicile.id == lieu)]
    t = w.minutes / 1440.0
    faits = []
    for hid in rng.choice(cand, min(n, len(cand)), replace=False).tolist():
        if nom in IM: _cas_sporadique(p, med, hid, nom, t)
        else: _cas_non_infectieux(p, med, hid, nom, t, rng)
        faits.append(hid)
    return faits


def suivre_transmission(p, ids):
    """Compte desormais les infections causees par les habitants `ids` ( la premiere generation d une epidemie : le R
    realise ). Rend le dictionnaire { id : infections causees }, tenu a jour par la contagion."""
    med = p.domaine("medecine")
    for i in ids: med.traces.setdefault(int(i), 0)
    return med.traces


def forcer_saison(p, maladie, valeur=None):
    """Fixe le facteur de saison d une maladie ( 1 : plein hiver ) ; None rend la saison du calendrier."""
    med = p.domaine("medecine")
    if valeur is None: med.saison_forcee.pop(maladie, None)
    else:
        if not 0.0 <= valeur <= 2.0: raise ValueError("facteur de saison hors [0 ; 2]")
        med.saison_forcee[maladie] = float(valeur)


def affections(p, h):
    """Les affections en cours de h : [ { cle, pathologie, phase, gravite, iss, soin, diagnostic, contagieuse } ]."""
    med = p.domaine("medecine"); A = med.aff
    t = p.w.minutes / 1440.0
    return [{"cle": s, "pathologie": PATHOS[A.path[s]].nom, "phase": ("latente", "contagieuse", "clinique")[A.phase[s]],
             "gravite": float(A.g[s]), "iss": int(A.iss[s]), "soin": int(A.soin[s]),
             "contagieuse": bool(A.t_inf[s] <= t < A.t_fin_cont[s])} for s in med.par_hab.get(h.id, ())]


def risque_sante(p, h):
    """Pour l assurance ( domaine 20 ) : ce qu un assureur peut estimer de h a partir de son age et de ses maladies
    chroniques declarees ( pas de ses infections en cours ) : probabilite de deces dans l annee, jours d hopital et
    cout des traitements d entretien attendus par an. Ordres de grandeur a calibrer ( ELSTAT : ~1 jour d hopital par
    habitant et par an, trois fois plus apres 65 ans )."""
    d = p.domaine("population")
    age = int(max(0, min(POP.AGE_MAX, (p.jour - int(p.col("habitant", "naissance_j")[h.id])) // 365)))
    sexe = int(p.col("habitant", "sexe")[h.id]); sexe = sexe if sexe in (0, 1) else POP.HOMME
    ch = int(p.col("habitant", "med_chroniques")[h.id])
    rr = 1.0
    for bit, v in RR_CHRONIQUE.items():
        if ch & bit: rr *= v
    q = float(d.mortalite.q[sexe, age]) / (1.0 - float(par_age(PART_CAUSES_MODELISEES, [age])[0]))
    jours = (1.0 if age < 65 else 3.0) * (1.0 + 0.5 * bin(ch & ~INSULINE).count("1"))
    cout = 0.0
    for bits, nom in TRAITEMENT_CHRONIQUE:
        prend = ch & INSULINE if nom == "insuline" else ch & bits and not (nom == "antidiabetique" and ch & INSULINE)
        if prend:
            cout += MOL[nom].prix * JOURS_AN
    return {"p_deces_an": min(1.0, q * min(3.0, rr ** 0.5)), "jours_hopital_an": jours, "cout_traitements_an": cout}


def vers_arma(p, h):
    """Le corps d un malade ou d un blesse dans Arma : setDamage ( 0 a 0,9 ) suit la gravite ; un blesse grave ne marche
    plus ( setUnconscious au-dela de 0,8 ). arma_preuve = None : rien n a ete vu en jeu."""
    g = h.gravite if h.etat == "I" else 0.0
    return {"setDamage": round(min(0.9, 0.9 * g), 3), "inconscient": g >= G_CRITIQUE[0], "arma_preuve": None}


# ================================================================== controles ( pour les portes )
def morts_hors_deceder(p):
    """Les morts qui ne sont pas passes par d01.deceder ( deces_j jamais pose ) : un mort ecrit a la main."""
    dj = p.col("habitant", "deces_j")
    return [h.id for h in p.w.habitants if not h.vivant and dj[h.id] < 0]


def incoherences_e1(p):
    """Les habitants dont l etat du moteur ne resume pas les affections, ou dont une ligne active n est pas marquee
    dans infecte ( et l inverse )."""
    med = p.domaine("medecine"); A = med.aff
    out = []
    for h in p.w.habitants:
        if not h.vivant: continue
        g = max((float(A.g[s]) for s in med.par_hab.get(h.id, ()) if A.phase[s] == CLINIQUE and not A.asym[s]), default=0.0)
        if (g >= SEUIL_E1) != (h.etat == "I") or (h.etat == "I" and abs(h.gravite - g) > 1e-6): out.append(("etat", h.id))
    k = A.k
    act = np.nonzero(A.actif[:k])[0]
    lignes = {(int(A.hab[s]), PATHOS[A.path[s]].nom) for s in act.tolist() if PATHOS[A.path[s]].nom in IM}
    n = min(med.cap, len(p.w.habitants))
    marques = {(int(i), INFECTIEUSES[int(j)]) for i, j in zip(*np.nonzero(med.infecte[:n]))}
    out += [("infecte", x) for x in lignes ^ marques]
    return out


def hopital_incoherent(p):
    """Les vivants graves ( gravite > 0,3 ) qui ne sont pas a l hopital de leur capitale, et ceux qui y sont sans l etre.
    A lire a une heure pleine, apres le deplacement du pas."""
    out = []
    for h in p.w.habitants:
        if not h.vivant or h.poste == "voyage" or h.id in p.w.sejours: continue
        grave = h.etat == "I" and h.gravite > GRAVITE_HOPITAL
        la = h.poste == "hopital" and h.lieu is h.domicile.marche
        if grave != la: out.append(h.id)
    return out


# ================================================================== installation
def _pharmacies_du_pays(w): return w.pays.domaines["medecine"].pharmacies


def _recensement_sanitaire(p, med, rng):
    """Le jour de l installation : maladies chroniques et leur traitement, sante mentale, immunites ( vaccination,
    infections passees ), tuberculose latente, et les infections endemiques en cours ( rhume, angine, gastro )."""
    w = p.w; n = len(w.habitants)
    _index_du_jour(p, med)
    ix = med.ix; age = ix.age
    col = p.colonnes["habitant"]
    viv = ix.vivant
    u = rng.random((n, 16))
    for j, (bit, tab) in enumerate(PREVALENCE_CHRONIQUE.items()):
        a = viv & (u[:, j] < interpole(tab, age))
        col["med_chroniques"][:n] |= np.where(a, bit, 0).astype(np.uint8)
        col["med_traite"][:n] |= np.where(a & (u[:, 4 + j] < PART_TRAITES[bit]), bit, 0).astype(np.uint8)
        if bit == DIABETE:
            ins = a & ((age < 30) | (u[:, 8] < PART_INSULINE))
            col["med_chroniques"][:n] |= np.where(ins, INSULINE, 0).astype(np.uint8)
            col["med_traite"][:n] |= np.where(ins, DIABETE, 0).astype(np.uint8)
    adulte = viv & (age >= 15)
    rrf = np.where(ix.sexe == POP.FEMME, RR_FEMME_MENTAL, 1.0) / 1.3
    dep = adulte & (u[:, 9] < PREVALENCE_DEPRESSION * rrf)
    anx = adulte & (u[:, 10] < PREVALENCE_ANXIETE * rrf)
    col["med_mental"][:n] = (np.where(dep, DEPRESSION, 0) | np.where(anx, ANXIETE, 0)
                             | np.where(dep & (u[:, 11] < PART_DEPRESSION_TRAITEE), DEP_TRAITEE, 0)).astype(np.uint8)
    col["med_mental_j"][:n] = np.where(dep | anx, p.jour - (u[:, 12] * DUREE_DEPRESSION_J).astype(np.int64), -1)
    # rougeole : doses et immunite des enfants, adultes immuns
    k = IM["rougeole"]
    age_j = age * JOURS_AN
    d1 = viv & (age_j >= AGE_ROR_J[0]) & (u[:, 13] < COUVERTURE_ROR[0])
    d2 = d1 & (age_j >= AGE_ROR_J[1]) & (u[:, 13] < COUVERTURE_ROR[1])
    med.doses[:n, 0] = np.where(d2, 2, np.where(d1, 1, 0))
    eff = np.where(d2, EFFICACITE_ROR[1], np.where(d1, EFFICACITE_ROR[0], 0.0))
    imm = (u[:, 14] < eff) | ((age >= 18) & (u[:, 14] < ADULTES_IMMUNS_ROUGEOLE)) | (age_j < PROTECTION_MATERNELLE_J)
    med.statut[:n, k] = np.where(imm, 1, 0)
    fin_mat = p.col("habitant", "naissance_j")[:n] + PROTECTION_MATERNELLE_J
    med.immun_fin[:n, k] = np.where(age_j < PROTECTION_MATERNELLE_J, fin_mat, IMMUNITE_A_VIE)
    # tuberculose latente
    kt = IM["tuberculose"]
    med.statut[:n, kt] = np.where(viv & (u[:, 15] < par_age(TB_LATENTE, age)), 2, med.statut[:n, kt])
    # infections endemiques : le regime permanent de chacune a la date de l installation ( SIRS en champ moyen : S = 1 / R,
    # I = ( 1 - S ) x duree de l infection / ( duree + duree de l immunite ) ), pas une epidemie qui s eteint
    r2 = p.du_jour("medecine_recensement_endemie")
    t = p.w.minutes / 1440.0
    ja = _jour_an(p)
    for nom in ENDEMIQUES_AU_DEPART:
        km = IM[nom]; m = PATHOS[IP[nom]]
        immun, en_cours = regime_permanent(m, ja)
        v = r2.random(n)
        im = viv & (v < immun)
        med.statut[:n, km] = np.where(im, 1, med.statut[:n, km])
        med.immun_fin[:n, km] = np.where(im, p.jour + (r2.random(n) * m.immunite_j).astype(np.int64), med.immun_fin[:n, km])
        cas = np.nonzero(viv & ~im & (v >= immun) & (v < immun + en_cours))[0]
        if len(cas): infecter(p, cas, nom, t - r2.random() * 2.0, r2)


ENDEMIQUES_AU_DEPART = ("rhume", "angine", "gastro")


def regime_permanent(m, jour_an):
    """( part immunisee, part infectee ) d une maladie endemique a immunite passagere, a l equilibre de sa saison."""
    R = m.r0 * facteur_saison(m, jour_an)
    if R <= 1.0 or m.immunite_j <= 0: return 0.0, 0.0005
    D = m.latence[0] + m.presympt[0] + max(m.maladie[0], m.contagion[0])
    S = 1.0 / R
    I = (1.0 - S) * D / (D + m.immunite_j)
    return 1.0 - S - I, I


def installer(p):
    w = p.w
    ch = p.colonnes["habitant"]
    for nom, dt, defaut in (("med_chroniques", np.uint8, 0), ("med_traite", np.uint8, 0),
                            ("med_sans_traitement_j", np.int16, 0), ("med_mental", np.uint8, 0),
                            ("med_mental_j", np.int32, -1), ("med_accouchement_vu", np.int32, -100000),
                            ("med_pe_conception", np.int32, -100000)):
        ch.ajouter(nom, dt, defaut)
    ch.assurer(len(w.habitants))
    col = p.colonnes["habitant"]
    col["med_accouchement_vu"][:len(w.habitants)] = col["accouchement_j"][:len(w.habitants)]
    # les produits de sante au catalogue
    cat = p.socle.catalogue
    id_mol = {}
    for m in MOLECULES:
        b = cat.declarer(m.nom, "sante", m.unite, m.prix, categorie_tva="super_reduite", masse_kg=m.masse_kg,
                         volume_l=m.volume_l, conservation_j=float(m.conservation_j), source=m.source)
        id_mol[m.nom] = b.id
    L = p.socle.livre
    for motif, nature in (("consultation_medicale", "achat"), ("participation_medicaments", "achat"),
                          ("import_produits_sante", "achat")):
        L.declarer_motif(motif, nature, "medecine")
    J = p.socle.journal
    for t_, champs in (("blessure", ("habitant", "nature", "iss", "cause")),
                       ("epidemie_declaree", ("maladie", "lieu", "cas")),
                       ("rupture_sante", ("bien", "lieu")), ("complication_grossesse", ("habitant", "complication")),
                       ("introduction", ("maladie", "lieu", "cas"))):
        J.declarer(t_, "medecine", "individuel", champs)
    for t_ in ("infection", "infection_importee", "cas_symptomatique", "hospitalisation", "guerison", "deces_medical",
               "consultation", "prescription_antibiotique", "test_diagnostique", "diagnostic_errone", "effet_indesirable",
               "vaccination", "vaccin_manquant", "peremption_sante", "import_sante", "decompensation", "accident_travail",
               "accident_route", "episode_depressif", "gastro_hydrique", "reactivation_tb", "traitement_chronique_manquant",
               "sans_soin"):
        J.declarer(t_, "medecine", "compte")
    p.echeance("medecine_livraison", _livraison)
    p.echeance("medecine_phase_aigue", _phase_aigue)
    p.echeance("medecine_renouvellement", _renouvellement)
    med = Medecine()
    med.aff = Affections(); med.par_hab = {}
    med.cap = 0; med.n_init = 0
    med.statut = np.zeros((0, M_INF), np.int8); med.immun_fin = np.zeros((0, M_INF), np.int32)
    med.infecte = np.zeros((0, M_INF), np.int8); med.deja = np.zeros((0, M_INF), np.bool_)
    med.doses = np.zeros((0, len(VACCINS)), np.int8); med.vacc_saison = np.zeros(0, np.int16)
    med.lieux = list(w.carte.lieux.values())                   # le meme ordre que l agenda ( agenda_lieu )
    med.index_lieu = {l.id: k for k, l in enumerate(med.lieux)}
    caps = sorted({l.marche.id for l in med.lieux})
    med.region_de_lieu = {c: k for k, c in enumerate(caps)}
    med.id_mol = id_mol
    med.pharmacies = []
    for k, c in enumerate(caps):
        med.pharmacies.append(Pharmacie(k, c, B.Stock(), len(NOMS_MOL)))
    nr = len(caps)
    med.resistance = np.array([[a.r_ref for a in ANTIBIOTIQUES]] * nr, float)
    med.usage = np.array([[a.u_ref for a in ANTIBIOTIQUES]] * nr, float)
    med.ddd_jour = np.zeros((nr, len(ANTIBIOTIQUES)))
    med.declares = np.zeros((nr, M_INF, 14), np.int32)
    med.expo_ref = None; med.expo_malade = None; med.expo_heures = 0; med.jour0 = p.jour
    med.q = np.array([q_contact(m, EXPOSITION_A_PRIORI) for m in MALADIES])
    n0 = len(w.habitants)
    echant = (np.arange(n0) if n0 <= ETALONNAGE_MAX
              else np.sort(p.hasard("medecine_etalonnage").choice(n0, ETALONNAGE_MAX, replace=False)))
    med.cal_pos = np.full(n0, -1, np.int64); med.cal_pos[echant] = np.arange(len(echant))
    med.cal_h = np.zeros((len(echant), len(CADRES)), np.float32)
    med.cal_n = np.zeros((len(echant), len(CADRES)), np.float32)
    med.cal_hI = np.zeros(len(CADRES)); med.cal_malades_h = 0
    med.saison_forcee = {}; med.reprises = set(); med.chaine_externe = False
    med.compteurs = {}; med.tues = {}; med.suivi = []; med.epidemies = {}; med.cas_jour = {}; med.traces = {}
    med.dec_consulter = p.decideur(POINT_CONSULTER); med.dec_prescrire = p.decideur(POINT_PRESCRIRE)
    p.domaines["medecine"] = med
    p.socle.registre.inscrire("pharmacies", "administrations", _pharmacies_du_pays, None, "stock", None)
    # la table de mortalite naturelle perd la part des causes que ce domaine fait mourir lui-meme
    demo = p.domaine("population")
    part = par_age(PART_CAUSES_MODELISEES, np.arange(POP.AGE_MAX))
    demo.mortalite.q[:, :POP.AGE_MAX] *= (1.0 - part)
    _recensement_sanitaire(p, med, p.hasard("medecine_recensement"))
    # le premier stock des pharmacies : STOCK_CIBLE_J jours de la consommation attendue
    for ph in med.pharmacies:
        for k, nom in enumerate(NOMS_MOL):
            q = STOCK_CIBLE_J * CONSO_A_PRIORI.get(nom, 0.0) * ph.pop / 1000.0
            ph.conso[k] = CONSO_A_PRIORI.get(nom, 0.0) * ph.pop / 1000.0
            if q > 0: _entrer(p, med, ph, nom, q, "importe" if MOL[nom].provenance == "importe" else "produit",
                              "dotation_initiale_sante")
    w.contagion = RemplaceContagion(p)
    w.progression_maladie = RemplaceProgression(p)
    w.soigner = RemplaceSoigner(p)
    p.routine(16.0, 50, "medecine", _accidents_travail)
    p.routine(17.0, 50, "medecine", _accidents_route)
    p.cloture("medecine", _cloture)
    return med
