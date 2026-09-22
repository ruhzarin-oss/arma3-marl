"""Constantes de l Oracle autonome : chemins, budget, seuils, et l espace des armes. Tout seuil ici est cite dans
REGLES_DE_L_ORACLE.md ; on ne le change pas sans amender ce fichier."""
H = "/mnt/data/hmt"
DEPOT = f"{H}/depot"
ETAT_DIR = f"{H}/oracle_autonome"
MISSION = f"{DEPOT}/bancs/chacaloracle"
QUEUE, EN_COURS, PREP, RUNS = f"{H}/queue", f"{H}/queue/en_cours", f"{H}/queue_preparation", f"{H}/runs"
CONTROLE = f"{DEPOT}/outils/controle_avant_run.sh"
PREFIXE_CAMPAGNE = "ORACLE-I"
# les iterations 1 a 4 ont ete jouees sous l ancien nom : on les relit toutes
PREFIXES_HISTORIQUES = ("DIABLE-I", "ORACLE-I")
GRAINE = 20260921

# --- budget ---
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
VOL_MAX = 12
K_EXPLOIT, K_EXPLORE, K_CONFIRME = 8, 4, 2          # candidats par iteration
EPISODES_MAX_ITERATION = 64
ITERATIONS_MAX_24H = 20
ITERATIONS_MAX_TOTAL = 50
CANDIDATS_IMAGINES = 20000
REPETITIONS_CONFIRMATION = 2                         # jobs de 2 graines par option : 4 episodes de plus par option, cumules d une iteration a l autre

# --- seuils ---
SEUIL_ACCEPTATION = 0.75
SEUIL_JOUABLE_IMAGINE = 0.50       # la meilleure option imaginee doit compromettre au plus 50 %
SEUIL_JOUABLE_OBSERVE = 0.50       # piege confirme : la meilleure option reussit au moins une fois sur deux
REGRET_MIN_PIEGE = 0.05            # sous ce regret imagine, ce n est pas un piege
ALPHA_CONFIRMATION = 0.05          # test exact de Fisher, unilateral
KAPPA_INCERTITUDE, KAPPA_NOUVEAUTE = 0.5, 0.02
DISTANCE_MIN_DIVERSITE = 3         # deux candidats d une meme iteration different d au moins 3 armes
ARRET_QUARANTAINES = 2             # iterations quarantainees de suite -> arret
ARRET_SANS_PIEGE = 3               # iterations sans piege imagine de suite -> arret, l equation tient
ARRET_IMAGINATION_PIRE = 5         # imagination pire que la constante 5 fois de suite -> arret

# --- l espace des armes de l Oracle ( phase 2, depart a la route ) : valeurs permises par description.ext ---
GRAINES = [4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]   # mondes valides ( test du 21/09 )
ARMES = {
    "situation":    list(range(1, 17)),
    "menace_p2":    [1, 2, 3, 4, 5],                  # 0 = aucune menace : ce n est pas un piege
    "jour":         [0, 1],
    "portee_son":   [0, 300, 600, 900],
    "avant":        [260, 180, 120, 80],
    "balayage":     [0, 1],
    "observation":  [0, 30, 45, 60, 90, 120, 180, 300],
    "palier":       [0, 1, 2, 3, 4],                  # 9 = monde vide : exclu
    "hmg":          [-1, 0, 1, 2],
    "qrf_n":        [-1, 0, 1, 2],
    "qrf_delai":    [-1, 45, 120, 300, 600, 9999],
    "oracle_cmd":   [0, 1],
    "oracle_b":     [0, 2, 4, 6, 8, 12],
    "oracle_delta": [30, 60, 120],
    "effectif":     [10, 20],
}
DEFAUTS = {"situation": 0, "menace_p2": 0, "jour": 0, "portee_son": 600, "avant": 260, "balayage": 0, "observation": 0,
           "palier": 3, "hmg": -1, "qrf_n": -1, "qrf_delai": -1, "oracle_cmd": 0, "oracle_b": 6, "oracle_delta": 60,
           "effectif": 10}
CATEGORIELLES = ["situation", "menace_p2", "palier", "hmg", "qrf_n", "qrf_delai"]
NUMERIQUES = ["portee_son", "avant", "observation", "oracle_b", "oracle_delta", "effectif"]
BINAIRES = ["jour", "balayage", "oracle_cmd"]

# --- sante de l imagination ( amendement 2, 21/09 : le bogue des reseaux arretes trop tot ) ---
TOLERANCE_CALIBRATION = 0.03       # |prediction moyenne - taux reel| sur ses propres episodes d apprentissage
ECART_MIN_PREDICTIONS = 0.005      # ecart-type minimal des predictions : en dessous, elle predit la meme chose partout

# --- la moitie Architecte ( 22/09 ) : il reapprend sa regle toutes les N iterations de l Oracle ---
ARCHITECTE_TOUS_LES = 2
ARCHITECTE_EVOGP_CV = dict(pop=300000, gen=200, graines=3, parc=1e-3)        # dans la validation par monde
ARCHITECTE_EVOGP_FINAL = dict(pop=1000000, gen=400, graines=5, parc=1e-3)    # la formule installee

# --- confirmation de « toujours attendre » ( CONFIRMATION_ATTENDRE.md, 019f54e ) : un seul regard, a 480 paires ---
CONFIRMATION_ATTENDRE = True       # suspend l adoption automatique de l Architecte ( regards repetes )

# --- le multiplexeur ( 22/09, Younes : « lance les vraies choses maintenant » ) : les jobs de l Oracle sont joues sur le banc
# multiple ( multi/CRITERES_MULTI.md ), plusieurs cellules par serveur ; voir multiplexeur.py
MULTIPLEXE = True
K_SERVICE = 3                      # cellules de l Oracle par episode : 3 mondes A au plus tiennent a 3 km les uns des autres
MULTI_ESPACEMENT = 3000            # m entre emprises de deux cellules ( avis de Fable )
MULTI_TMAX = 1500                  # s apres le depart commun : au-dela, la cellule est censuree
POULS_BANDE_MIN = 0.95             # part des intervalles du pouls dans [1,8 ; 2,5] s ( amendement 3 ) ; sinon cellule refusee
MONDES_B = [0, 1, 2, 10, 25, 26, 27, 28, 29, 30, 31]   # tenus hors de tout ( poche/CRITERES_POCHE.md ) : jamais temoins
