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
