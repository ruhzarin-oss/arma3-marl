"""THÉÂTRE BALTIQUE : premier théâtre de la guerre OTAN contre Russie-Chine ( capture de drapeaux, comme les secteurs
Warlords sur Arma ). Choisi le 29/09 pour tenir dans CMO : peu de pays, une mer fermée, des bases réelles à 200-600 km.

CHOIX PRIS EN COPIANT LE RÉEL, À VALIDER PAR YOUNES ( chacun ici, en clair ) :
- les pays engagés et la PART de leur budget de défense que le théâtre reçoit ( les États-Unis engagent ~5 % de leur
  budget en Europe du Nord, la Pologne et les Baltes 100 %, la Russie ~25 % pour son district militaire de Léningrad ) ;
- les drapeaux : des lieux réels ( bases aériennes, ports militaires, capitales, le corridor de Suwałki, Gotland,
  Bornholm ), leurs coordonnées au kilomètre près, leur valeur ( revenu par tour, comme Warlords : 10 à 30 ) ;
- l'aérodrome de CMO posé sur chaque base aérienne : un « Single-Unit Airfield » générique de la base DB3000 choisi par la
  longueur de piste réelle ( 1712 = 1 piste de 2001-2600 m, 1877 = 2600-3200 m, 1592 = 3201-4000 m ; 80 hangars et 40
  places pour gros avions chacun ) ; un « Single-Unit Port » ( 2980 ) sur chaque port militaire ;
- un QG par camp ( Varsovie, Kaliningrad ) : le perdre, c'est perdre la guerre.
"""

NOM = "Baltique"
CAMPS = ("OTAN", "Russie-Chine")                 # les deux côtés dans CMO ; les pays sont dans les numéros d'unités

# pays : ( camp, part du budget engagée sur le théâtre, raison ). Noms EXACTS de la base DB3000.
PAYS = {
    "Poland": ("OTAN", 1.00, "tout son effort de défense regarde Kaliningrad et la Biélorussie"),
    "Lithuania [1992-]": ("OTAN", 1.00, "pays hôte, sans chasseur ( police du ciel balte de l'OTAN )"),
    "Latvia [1992-]": ("OTAN", 1.00, "pays hôte, sans chasseur"),
    "Estonia [1992-]": ("OTAN", 1.00, "pays hôte, sans chasseur"),
    "Finland": ("OTAN", 0.50, "frontière russe de 1 340 km, moitié au sud ( golfe de Finlande )"),
    "Sweden": ("OTAN", 0.60, "Gotland et la Baltique centrale"),
    "Denmark": ("OTAN", 0.50, "détroits et Bornholm"),
    "Germany [FRG/Reunified]": ("OTAN", 0.20, "brigade en Lituanie, police du ciel balte"),
    "United Kingdom": ("OTAN", 0.10, "présence avancée en Estonie"),
    "United States": ("OTAN", 0.05, "part européenne de l'effort américain qui irait à la Baltique"),
    "Russia [1992-]": ("Russie-Chine", 0.25, "district militaire de Léningrad et Kaliningrad"),
    "Belarus [1992-]": ("Russie-Chine", 1.00, "État de l'Union, tout son effort"),
}

# drapeaux : ( nom, pays hôte, lat, lon, genre, valeur, camp de départ, dbid de l'installation CMO ou None, QG ? )
DRAPEAUX = [
    ("Varsovie", "Poland", 52.23, 21.01, "capitale", 30, "OTAN", None, True),
    ("Łask ( 32e base aérienne )", "Poland", 51.55, 19.18, "base aérienne", 20, "OTAN", 1712, False),
    ("Malbork ( 22e base aérienne )", "Poland", 54.03, 19.13, "base aérienne", 20, "OTAN", 1712, False),
    ("Gdynia ( port militaire )", "Poland", 54.52, 18.55, "port", 20, "OTAN", 2980, False),
    ("Corridor de Suwałki", "Poland", 54.10, 22.93, "point clé", 30, "OTAN", None, False),
    ("Šiauliai ( police du ciel balte )", "Lithuania [1992-]", 55.89, 23.39, "base aérienne", 20, "OTAN", 1592, False),
    ("Vilnius", "Lithuania [1992-]", 54.69, 25.28, "capitale", 25, "OTAN", None, False),
    ("Lielvārde", "Latvia [1992-]", 56.78, 24.85, "base aérienne", 15, "OTAN", 1712, False),
    ("Riga", "Latvia [1992-]", 56.95, 24.11, "capitale", 20, "OTAN", None, False),
    ("Ämari", "Estonia [1992-]", 59.26, 24.21, "base aérienne", 15, "OTAN", 1877, False),
    ("Tallinn", "Estonia [1992-]", 59.44, 24.75, "capitale", 20, "OTAN", None, False),
    ("Gotland ( Visby )", "Sweden", 57.66, 18.35, "île", 25, "OTAN", 1712, False),
    ("Bornholm ( Rønne )", "Denmark", 55.06, 14.76, "île", 15, "OTAN", 1712, False),
    ("Helsinki", "Finland", 60.17, 24.94, "capitale", 20, "OTAN", None, False),
    ("Kaliningrad", "Russia [1992-]", 54.71, 20.51, "capitale régionale", 30, "Russie-Chine", None, True),
    ("Tchkalovsk ( base aérienne )", "Russia [1992-]", 54.77, 20.40, "base aérienne", 20, "Russie-Chine", 1712, False),
    ("Baltiïsk ( flotte de la Baltique )", "Russia [1992-]", 54.65, 19.91, "port", 25, "Russie-Chine", 2980, False),
    ("Pskov ( Kresty )", "Russia [1992-]", 57.78, 28.39, "base aérienne", 20, "Russie-Chine", 1712, False),
    ("Saint-Pétersbourg ( Levachovo )", "Russia [1992-]", 60.09, 30.19, "base aérienne", 20, "Russie-Chine", 1712, False),
    ("Kronstadt", "Russia [1992-]", 59.99, 29.77, "port", 20, "Russie-Chine", 2980, False),
    ("Minsk", "Belarus [1992-]", 53.90, 27.56, "capitale", 25, "Russie-Chine", None, False),
    ("Baranovitchi ( 61e base aérienne )", "Belarus [1992-]", 53.10, 26.05, "base aérienne", 20, "Russie-Chine", 1877, False),
    ("Hrodna", "Belarus [1992-]", 53.68, 23.83, "point clé", 20, "Russie-Chine", None, False),
]

# D'où décollent les avions de chaque pays ( noms de drapeaux ci-dessus ). Les alliés sans base sur le théâtre se déploient
# chez un hôte, comme dans le réel : les Américains à Łask ( rotations F-16 et F-35 en Pologne ), les Allemands à Šiauliai
# et les Britanniques à Ämari ( police du ciel balte ), les Finlandais à Ämari ( en face d'Helsinki ), les Danois à Bornholm,
# les Suédois sur Gotland. Les Baltes n'achètent pas d'avions ( aucun chasseur ).
BASES_DE = {
    "Poland": ["Łask ( 32e base aérienne )", "Malbork ( 22e base aérienne )"],
    "United States": ["Łask ( 32e base aérienne )"],
    "Germany [FRG/Reunified]": ["Šiauliai ( police du ciel balte )"],
    "United Kingdom": ["Ämari"],
    "Finland": ["Ämari"],
    "Denmark": ["Bornholm ( Rønne )"],
    "Sweden": ["Gotland ( Visby )"],
    "Russia [1992-]": ["Tchkalovsk ( base aérienne )", "Pskov ( Kresty )", "Saint-Pétersbourg ( Levachovo )"],
    "Belarus [1992-]": ["Baranovitchi ( 61e base aérienne )"],
}
