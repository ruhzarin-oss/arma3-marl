"""Constantes du monde complet ( plans/plan-monde-complet.md ). Decisions de Younes du 22/09 : Altis, 500 habitants,
tout dans la premiere version, economie reelle, vrai gouvernement, aucun ennemi, un eleve qui va a l ecole, une journee
complete du monde en 6 heures reelles."""
GRAINE = 20260922

# --- le temps ---
MINUTES_PAR_PAS = 10                 # un pas du coeur = 10 minutes du monde
PAS_PAR_JOUR = 24 * 60 // MINUTES_PAR_PAS
ACCELERATION = 4                     # 24 h du monde en 6 h reelles
DATE_DEPART = (2035, 6, 15, 6, 0)    # la date des missions CHACAL, a l aube
LEVER, COUCHER = 6.0, 20.7           # heures locales approximatives a Altis a la mi-juin

# --- la population ( 500 habitants ) : effectifs par role ---
ROLES = {
    # role:            ( effectif, classe,      public ? )
    "chef_gouvernement": (1, "aisee", True),
    "ministre":          (6, "aisee", True),
    "officier":          (5, "aisee", True),
    "soldat":            (55, "populaire", True),
    "policier":          (20, "moyenne", True),
    "medecin":           (6, "aisee", True),
    "infirmier":         (6, "moyenne", True),
    "enseignant":        (9, "moyenne", True),
    "patron":            (8, "aisee", False),
    "paysan":            (110, "populaire", False),
    "mineur":            (40, "populaire", False),
    "petrolier":         (15, "populaire", False),
    "ouvrier":           (40, "populaire", False),
    "convoyeur":         (25, "populaire", False),
    "marchand":          (20, "moyenne", False),
    "enfant":            (100, "populaire", False),
    "retraite":          (34, "populaire", False),
}
assert sum(v[0] for v in ROLES.values()) == 500

MINISTERES = ["finances", "sante", "interieur", "defense", "education", "industrie"]

# --- l archipel ( 24/09 ) : six pays, chacun une ile. Le code d une ile ( son rang ici ) entre dans le numero de chaque
# personne nee chez elle : ne jamais changer cet ordre, les numeros deja donnes changeraient de sens.
ILES_ARCHIPEL = ("Altis", "Malden", "Stratis", "Tanoa", "Enoch", "Sara")
BITS_NUMERO_LOCAL = 40                   # numero d archipel = ( code de l ile << 40 ) | numero local : 10^12 par ile
# le passeport, delivre par l Etat de chaque ile ( a calibrer : ordre de grandeur grec, ~84 euros, 1 drachme = 1,15 euro )
FRAIS_PASSEPORT = 73.0                   # drachmes
DELAI_PASSEPORT_J = 7                    # jours entre la demande et la remise
VALIDITE_PASSEPORT_ANS = (5, 10)         # ( mineur, adulte )
PART_PASSEPORT_DEPART = 0.4              # adultes qui en ont deja un au debut du monde ( a calibrer )

# --- les biens ---
BIENS = ["nourriture", "fer", "zinc", "or", "petrole", "carburant", "electricite", "outils", "remedes"]
MONNAIE = "drachme"
# prix mondiaux ( port de Kavala ) : le monde exterieur achete et vend a ces prix, fixes
PRIX_MONDE = {"nourriture": 4.0, "fer": 6.0, "zinc": 9.0, "or": 400.0, "petrole": 5.0, "carburant": 9.0,
              "electricite": 1.0, "outils": 30.0, "remedes": 25.0}

# --- la production : recette par heure de travail d un travailleur ---
#   type de site: ( role qui y travaille, intrants par heure, produits par heure )
RECETTES = {
    "ferme":      ("paysan",    {},                                        {"nourriture": 1.2}),
    "mine":       ("mineur",    {},                                        {"fer": 1.5, "zinc": 0.6, "or": 0.02}),
    "carriere":   ("mineur",    {},                                        {"fer": 1.2, "zinc": 0.3}),
    "puits":      ("petrolier", {"electricite": 0.5},                      {"petrole": 6.0}),
    "raffinerie": ("ouvrier",   {"petrole": 5.0, "electricite": 1.0},      {"carburant": 4.0}),
    "centrale":   ("ouvrier",   {"carburant": 1.0},                        {"electricite": 12.0}),
    "fonderie":   ("ouvrier",   {"fer": 2.0, "electricite": 1.5},          {"outils": 0.6}),
    "pharmacie":  ("ouvrier",   {"zinc": 0.5, "nourriture": 0.5, "electricite": 0.5}, {"remedes": 1.0}),
}
BONUS_OUTILS = 0.25                  # +25 % de production si le site a des outils ; un outil s use en 200 heures de travail
USURE_OUTIL_H = 200

# --- la consommation ---
NOURRITURE_PAR_JOUR = 1.0            # par habitant
CARBURANT_PAR_KM = 0.03              # par vehicule ( unites de carburant )
VITESSE_CONVOI_KMH = 40.0
CAPACITE_CAMION = 60.0               # unites de biens par convoi

# --- la sante ---
BETA_CONTACT = 0.004                 # probabilite d infection par heure et par contact infectieux dans un meme lieu
INCUBATION_J, MALADIE_J = 2.0, 5.0
LETALITE = 0.03                      # sans remede ; divisee par 5 avec remede
EFFET_REMEDE_DUREE = 0.5             # un remede divise par deux le reste de la maladie

# --- les echeances ---
HEURE_PAIE = 18                      # la paie tombe chaque jour a 18 h
JOURS_RECOLTE = 3                    # la recolte des fermes est livree tous les 3 jours
HORAIRES = {"jour": (7, 15), "bureau": (8, 17), "nuit": (22, 6), "ecole": (8, 15), "marche": (8, 19)}

# --- calibration du 22/09 soir ( premier essai de 30 jours : marches isoles, argent qui s accumule chez les menages ) ---
REDEVANCE_OR = 0.2                   # la moitie de l or extrait revient a l Etat
PROPENSION_DEPENSE = 0.05            # part de l epargne au-dela d une semaine de nourriture depensee chaque soir
OUVRIERS_PAR_SITE = {"raffinerie": 14, "centrale": 3, "fonderie": 6, "pharmacie": 5}   # 14 + 9 + 12 + 5 = 40
MARGE_ELECTRICITE = 1.3              # le tarif de l electricite suit le cout du carburant des centrales ( 12 unites par unite )
STOCK_CIBLE = 250.0                  # stock moyen par marche au-dela duquel une entreprise ralentit

# les biens qui circulent entre marches ( decision du marchand : regle ou reseau appris )
BIENS_COMMERCE = ("nourriture", "carburant", "remedes", "outils", "fer", "zinc", "petrole")

# --- demographie ( point 5 des douze manques ) : un pays ou l on nait, ou l on vieillit, ou l on part a la retraite ---
AGE_TRAVAIL = 16                     # l enfant qui l atteint entre dans la vie active
AGE_RETRAITE = 65
NAISSANCES_PAR_MENAGE_AN = 0.09      # un menage avec un adulte de moins de 45 ans
MORTALITE_AN = ((40, 0.001), (60, 0.004), (75, 0.02), (85, 0.06), (200, 0.15))   # age limite -> risque annuel
JOURS_PAR_AN = 365

# --- desobeissance ( point 8 ) : une loi peut etre enfreinte, sinon gouverner ne coute rien ---
TVA_TOLEREE = 0.12                   # au-dela, la fraude commence
FRAUDE_PENTE = 2.0                   # part des achats qui echappe a la TVA, par point de taxe au-dessus du seuil
FRAUDE_MAX = 0.7
QUARANTAINE_VIOLEE = 0.2             # part des habitants qui sortent quand meme
ABSENCE_FAIM = 1.5                   # au-dela de cette faim accumulee, on ne va plus travailler
CONTROLE_PAR_POLICIER = 0.2           # chance de controle par policier, pour dix menages de sa region
