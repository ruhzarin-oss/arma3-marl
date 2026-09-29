"""La population de la Grece, copiee sur le reel : les cibles de `population.generer( ..., demographie="grece" )`.

Chaque cible porte sa source ( jeu Eurostat ou tableau ELSTAT, annee, adresse ). Les valeurs viennent de l API de
diffusion d Eurostat, lue le 27/09/2026 :
  https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/<jeu>?geo=EL&time=<annee>
Ce qui n a pas de source est marque « a calibrer ». Les portes : monde/porte_population_grece.py.

Le monde garde l economie d E1 : `echelle` fixe le nombre de travailleurs CIVILS ( 306 par unite, les metiers civils
de config.ROLES a l echelle ) ; la population est ce qu il faut autour d eux pour que le taux d emploi des 20-64 ans
soit celui de la Grece. Enfants, etudiants, chomeurs, inactifs et retraites s y ajoutent."""
import numpy as np

NOM = "grece"
FEMME, HOMME = 0, 1                  # les codes du domaine 1 ( pays/d01_population.py )

# ================================================================== la pyramide des ages
# Eurostat demo_pjangroup ( population au 1er janvier par groupe de 5 ans et sexe ), Grece, 1er janvier 2024, de 0-4 a
# 80-84 ans ; au-dela, demo_pjan ( ages simples 85 a 99 et « 100 ans et plus », Y_OPEN ) regroupes par 5 ans. Les
# totaux de sexe concordent avec demo_pjangroup ( 85 ans et plus : 152 301 hommes, 248 609 femmes ).
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_pjangroup?geo=EL&time=2024
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_pjan?geo=EL&time=2024
GROUPES = tuple(range(0, 101, 5))    # debut de chaque groupe : 0-4, 5-9, ..., 95-99, 100 et plus
AGE_MAX_TIRE = 104                   # les « 100 ans et plus » sont tires de 100 a 104 ans ( a calibrer )
PYRAMIDE = {
    HOMME: (203141, 230976, 264059, 285378, 277838, 270364, 281012, 312302, 384203, 399975, 389380, 377832, 333541,
            304671, 257944, 219359, 139306, 100514, 41617, 9082, 1088),
    FEMME: (192074, 217438, 249107, 260937, 251725, 246241, 264284, 308014, 381365, 402135, 398160, 400602, 368395,
            342938, 296437, 273135, 190586, 156192, 71544, 18377, 2496),
}
POPULATION = 10375764                # demo_pjangroup, total 2024 ( 5 083 582 hommes, 5 292 182 femmes )

# ================================================================== les menages
# Eurostat ilc_lvph03 ( EU-SILC, repartition des menages par taille ), Grece 2024 : 1, 2, 3, 4, 5, 6 personnes et plus.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_lvph03?geo=EL&time=2024
TAILLES = (0.323, 0.284, 0.182, 0.139, 0.055, 0.016)
# Eurostat ilc_lvph01 ( EU-SILC, taille moyenne des menages ), Grece 2024 : 2,4 ( publiee a 0,1 pres ; la repartition
# ci-dessus donne 2,37 en comptant 6,4 personnes pour « 6 et plus » ).
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_lvph01?geo=EL&time=2024
TAILLE_MOYENNE = 2.4
# Eurostat ilc_lvph04 ( EU-SILC, repartition des menages par type ), Grece 2024, en part des menages. « Enfant a
# charge » au sens d EU-SILC : moins de 18 ans, ou 18-24 ans inactif qui vit avec un parent. Mesure rapportee, pas
# une porte.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_lvph04?geo=EL&time=2024
TYPES = {"un_adulte": 0.324, "un_adulte_65_plus": 0.160, "un_adulte_enfants": 0.016, "deux_adultes": 0.275,
         "deux_adultes_65_plus": 0.168, "deux_adultes_1_enfant": 0.090, "deux_adultes_2_enfants": 0.090,
         "deux_adultes_3_enfants_et_plus": 0.039, "trois_adultes_et_plus": 0.119, "trois_adultes_enfants": 0.045}

# Les couples : part des femmes qui vivent en couple, par age ( borne basse de la tranche ). Point de depart : l ordre
# de grandeur ELSTAT du domaine 1 ( d01_population.EN_COUPLE, recensement 2021 ) ; CALE ensuite sur la repartition
# des tailles et des types ci-dessus ( a calibrer : pas de tableau par age lu a la source ). L homme a en moyenne 3 ans
# de plus ( d01 : ECART_AGE_COUPLE ), ecart-type 4 ans ( a calibrer ), jamais plus de 12 ans d ecart a la cible.
EN_COUPLE_FEMMES = ((18, 0.05), (20, 0.13), (25, 0.36), (30, 0.60), (35, 0.72), (50, 0.74), (60, 0.70), (65, 0.64),
                    (70, 0.55), (75, 0.43), (80, 0.27), (85, 0.12), (90, 0.04))
ECART_AGE_COUPLE, ECART_AGE_SD, ECART_AGE_MAX = 3.0, 4.0, 12
# Les jeunes adultes chez leurs parents : Eurostat ilc_lvps08, Grece 2024 - 85,4 % des 18-24 ans, 71,1 % des 25-29
# ans, 54,9 % des 25-34 ans ( d ou 39,6 % des 30-34 ans, a population 2024 egale ). Au-dela de 35 ans, Eurostat ne
# publie pas ce taux : la decroissance jusqu a 55 ans est a calibrer ( calee sur les « un adulte » de moins de 65 ans
# d ilc_lvph04 ). La part vaut pour TOUS les gens de l age ; elle se reporte sur ceux qui vivent hors couple.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_lvps08?geo=EL&time=2024
CHEZ_LES_PARENTS = ((18, 0.854), (25, 0.711), (30, 0.396), (35, 0.22), (40, 0.16), (45, 0.12), (50, 0.08), (55, 0.04),
                    (60, 0.0))
# Les ages de la mere a la naissance : la fecondite par age du domaine 1 ( d01_population.ASFR, ordre de grandeur
# Eurostat, ISF 1,35 ) ; une femme seule a 0,15 fois la fecondite d une femme en couple ( d01 : FECONDITE_SOLO ).
ASFR = {15: 0.008, 20: 0.030, 25: 0.068, 30: 0.094, 35: 0.058, 40: 0.0105, 45: 0.0005}
FECONDITE_SOLO = 0.15
# Les parents ages qui vivent chez un enfant ( menages a plusieurs generations ) : part des 65 ans et plus hors couple
# et seuls, par age ( a calibrer : calee sur « trois adultes et plus » et « un adulte de 65 ans et plus »
# d ilc_lvph04 ).
CHEZ_UN_ENFANT = ((65, 0.15), (75, 0.30), (85, 0.45))
# Les fratries : les mineurs qui ont tire une mere du meme age et de la meme situation sont groupes en fratries de 1,
# 2, 3 ou 4 enfants, une par mere. Parts : celles des menages de deux adultes avec 1, 2, 3 enfants a charge et plus
# d ilc_lvph04 ( 9,0 / 9,0 / 3,9 : 41 %, 41 %, 18 % ) ; le partage de « 3 et plus » entre 3 et 4 est a calibrer.
FRATRIES = ((1, 0.41), (2, 0.41), (3, 0.14), (4, 0.04))

# ================================================================== l activite
# Taux d emploi par sexe et groupe d age : Eurostat lfsa_ergan ( enquete forces de travail ), Grece 2024.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsa_ergan?geo=EL&time=2024
# Groupes 15-19, 20-24, ..., 60-64. Les 20-64 ans : 69,3 % ( hommes 78,7 %, femmes 59,9 % ). Les 65-69 ans en emploi
# ( 16,3 % ) ne sont pas copies : le moteur met a la retraite a 65 ans ( config.AGE_RETRAITE ). Le taux des 15-19 ans
# est porte par les seuls 18-19 ans ( 2,5 fois le taux du groupe ) : les 6-17 ans sont a l ecole.
GROUPES_ACTIFS = (15, 20, 25, 30, 35, 40, 45, 50, 55, 60)
EMPLOI = {HOMME: (0.050, 0.395, 0.715, 0.858, 0.881, 0.899, 0.906, 0.896, 0.808, 0.570),
          FEMME: (0.020, 0.361, 0.651, 0.635, 0.691, 0.679, 0.717, 0.681, 0.571, 0.333)}
CIBLE_EMPLOI_20_64 = 0.693
AGE_ACTIF = 18                       # le premier age en emploi ( les 16-17 ans sont a l ecole, a calibrer )
# Taux de chomage par sexe et groupe d age : Eurostat lfsa_urgan, Grece 2024 ( 10,0 % des 20-64 ans ). Pour les 18-19
# ans, le taux des 15-24 ans.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsa_urgan?geo=EL&time=2024
CHOMAGE = {HOMME: (0.211, 0.208, 0.176, 0.085, 0.075, 0.064, 0.053, 0.052, 0.051, 0.049),
           FEMME: (0.241, 0.207, 0.170, 0.172, 0.120, 0.129, 0.102, 0.100, 0.088, 0.121)}
# Les inactifs par motif ( etudes, au foyer, invalidite, retraite anticipee ; le reste : decourages ) : les parts
# RELATIVES du recensement du domaine 4 ( d04_travail.STATUTS_RECENSEMENT, a calibrer ), recopie ci-dessous : colonnes
# emploi, chomage, etudes, au foyer, invalidite, retraite anticipee ; le reste, decourages. Seules les parts des motifs
# entre eux sont reprises : l emploi et le chomage viennent d Eurostat ci-dessus. Au foyer suppose un autre adulte
# dans le menage ( comme au domaine 4 ) : sans lui, l inactif est compte decourage.
STATUTS_D04 = (
    (16, 20, {HOMME: (0.05, 0.03, 0.90, 0.00, 0.01, 0.00), FEMME: (0.03, 0.03, 0.92, 0.01, 0.01, 0.00)}),
    (20, 25, {HOMME: (0.38, 0.14, 0.42, 0.01, 0.01, 0.00), FEMME: (0.30, 0.14, 0.47, 0.04, 0.01, 0.00)}),
    (25, 35, {HOMME: (0.76, 0.14, 0.03, 0.01, 0.02, 0.00), FEMME: (0.60, 0.17, 0.03, 0.14, 0.02, 0.00)}),
    (35, 45, {HOMME: (0.85, 0.09, 0.00, 0.01, 0.03, 0.00), FEMME: (0.64, 0.12, 0.00, 0.19, 0.02, 0.00)}),
    (45, 55, {HOMME: (0.83, 0.09, 0.00, 0.01, 0.04, 0.00), FEMME: (0.60, 0.11, 0.00, 0.23, 0.03, 0.00)}),
    (55, 65, {HOMME: (0.62, 0.07, 0.00, 0.01, 0.08, 0.18), FEMME: (0.37, 0.06, 0.00, 0.31, 0.06, 0.18)}),
)
MOTIFS_INACTIFS = ("etudes", "au_foyer", "invalide", "retraite_anticipee", "decourage")

# ================================================================== l armee
# Les forces armees grecques : 147 000 personnes ( Banque mondiale, MS.MIL.TOTL.P1, 2020, derniere annee publiee ;
# source IISS, The Military Balance ; forces d active et paramilitaires ), rapportees a la population de 2024 :
# 1,42 %. Un officier pour onze soldats, comme dans le monde E1 ( 5 pour 55, a calibrer ).
#   https://api.worldbank.org/v2/country/GRC/indicator/MS.MIL.TOTL.P1?format=json
MILITAIRES = 147000
PART_MILITAIRES = MILITAIRES / POPULATION
PART_OFFICIERS = 5.0 / 60.0
AGES_MILITAIRES = (19, 55)           # engages et appeles ( service a 19 ans ) ; au-dela de 55 ans, a la retraite ( a calibrer )

# Part d hommes par metier ( d01_population.PART_HOMMES, a calibrer sur ELSTAT ) : l affectation des metiers suit le
# sexe des personnes en emploi, ces parts decalees ensemble pour que le compte des hommes tombe juste.
PART_HOMMES = {"chef_gouvernement": 0.6, "ministre": 0.7, "officier": 0.85, "soldat": 0.9, "policier": 0.8,
               "medecin": 0.5, "infirmier": 0.15, "enseignant": 0.3, "patron": 0.7, "paysan": 0.6, "mineur": 0.95,
               "petrolier": 0.9, "ouvrier": 0.7, "convoyeur": 0.9, "marchand": 0.5, "hotellerie": 0.5,
               # 29/09, CHOIX DECLARE ( a calibrer sur ELSTAT ) : les metiers publics ajoutes a config.ROLES
               "administration": 0.45, "pompier": 0.9, "juge": 0.35, "gardien": 0.8}

# ================================================================== l emploi par secteur ( mesure, pas une porte )
# Eurostat lfsa_egan2 ( emploi par section NACE rev. 2, 15-74 ans, milliers ), Grece 2024.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsa_egan2?geo=EL&time=2024
EMPLOI_NACE = {"A": 467.8, "B": 8.7, "C": 417.7, "D": 45.0, "E": 41.3, "F": 185.2, "G": 712.9, "H": 240.4,
               "I": 398.8, "J": 106.6, "K": 82.6, "L": 11.5, "M": 283.1, "N": 100.4, "O": 354.3, "P": 331.1,
               "Q": 306.5, "R": 55.5, "S": 88.0, "T": 24.7, "NRP": 2.6}
SECTEURS = {"agriculture": ("A",), "industrie": ("B", "C", "D", "E"), "construction": ("F",),
            "services_marchands": ("G", "H", "I", "J", "K", "L", "M", "N", "R", "S", "T"),
            "public_education_sante": ("O", "P", "Q")}
# le secteur de chaque metier du moteur ( a calibrer : le patron possede les sites industriels )
SECTEUR_DU_METIER = {"paysan": "agriculture", "mineur": "industrie", "petrolier": "industrie", "ouvrier": "industrie",
                     "patron": "industrie", "marchand": "services_marchands", "convoyeur": "services_marchands",
                     "hotellerie": "services_marchands", "chef_gouvernement": "public_education_sante",
                     "ministre": "public_education_sante", "policier": "public_education_sante",
                     "medecin": "public_education_sante", "infirmier": "public_education_sante",
                     "enseignant": "public_education_sante", "soldat": "public_education_sante",
                     "officier": "public_education_sante", "administration": "public_education_sante",
                     "pompier": "public_education_sante", "juge": "public_education_sante",
                     "gardien": "public_education_sante"}


def par_age(table, age):
    """La valeur d une table ( ( age de debut, valeur ), ... ) pour un tableau d ages : celle de la derniere tranche
    commencee ( 0 avant la premiere )."""
    age = np.asarray(age)
    out = np.zeros(age.shape)
    for a, v in table: out[age >= a] = v
    return out


def motifs_inactifs(age, sexe):
    """Pour chaque inactif ( ages, sexes ), les probabilites de ses motifs ( MOTIFS_INACTIFS ) : les parts relatives de
    STATUTS_D04 dans sa tranche. Rend un tableau ( n, 5 ), chaque ligne de somme 1."""
    age = np.asarray(age); sexe = np.asarray(sexe)
    out = np.zeros((age.size, len(MOTIFS_INACTIFS)))
    out[:, -1] = 1.0                           # hors des tranches : decourage
    for a0, a1, t in STATUTS_D04:
        for s, (e, u, et, f, i, r) in t.items():
            m = (age >= a0) & (age < a1) & (sexe == s)
            reste = max(0.0, 1.0 - e - u - et - f - i - r)
            v = np.array([et, f, i, r, reste])
            out[m] = v / v.sum()
    return out


def emploi_par_habitant():
    """Les personnes en emploi par habitant, a la pyramide et aux taux d emploi de 2024 ( sans les 65 ans et plus )."""
    tot = 0.0
    for s in (HOMME, FEMME):
        for k, a in enumerate(GROUPES_ACTIFS):
            tot += PYRAMIDE[s][GROUPES.index(a)] * EMPLOI[s][k]
    return tot / POPULATION
