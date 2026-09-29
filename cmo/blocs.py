"""Les blocs de la guerre OTAN contre Russie-Chine, pays par pays, avec les noms EXACTS de la base DB3000 de CMO
( EnumOperatorCountry ). Situation de 2026, en copiant le réel ; chaque classement porte sa raison et sa certitude.
« à valider » = choix de Claude que Younes doit trancher ( demande du 29/09 : OTAN contre Russes et Chinois, avec tous
les pays satellites ).

Blocs : OTAN, PARTENAIRE_OTAN, RUSSIE, CHINE, SATELLITE ( du bloc Russie-Chine ), NEUTRE, HISTORIQUE ( n'existe plus en
2026 ), NON_ETATIQUE."""

OTAN, PARTENAIRE_OTAN, RUSSIE, CHINE, SATELLITE = "OTAN", "Partenaire OTAN", "Russie", "Chine", "Satellite Russie-Chine"
NEUTRE, HISTORIQUE, NON_ETATIQUE = "Neutre", "Historique", "Non étatique"
CAMP = {OTAN: "OTAN", PARTENAIRE_OTAN: "OTAN", RUSSIE: "Russie-Chine", CHINE: "Russie-Chine", SATELLITE: "Russie-Chine"}

_MEMBRES_OTAN = {                                # les 32 membres en 2026, année d'adhésion
    "Albania": 2009, "Belgium": 1949, "Bulgaria": 2004, "Canada": 1949, "Croatia [1992-]": 2009,
    "Czech Republic [1993-]": 1999, "Denmark": 1949, "Estonia [1992-]": 2004, "Finland": 2023, "France": 1949,
    "Germany [FRG/Reunified]": 1955, "Greece": 1952, "Hungary": 1999, "Iceland": 1949, "Italy": 1949,
    "Latvia [1992-]": 2004, "Lithuania [1992-]": 2004, "Luxembourg": 1949, "Montenegro [1992-]": 2017,
    "Netherlands": 1949, "North Macedonia [1991-]": 2020, "Norway": 1949, "Poland": 1999, "Portugal": 1949,
    "Romania": 2004, "Slovakia [1993-]": 2004, "Slovenia [1991-]": 2004, "Spain": 1982, "Sweden": 2024,
    "Turkey": 1952, "United Kingdom": 1949, "United States": 1949,
}

BLOCS = {pays: (OTAN, "sûr", f"membre de l'OTAN depuis {an}") for pays, an in _MEMBRES_OTAN.items()}
BLOCS.update({
    "NATO": (OTAN, "sûr", "moyens communs de l'Alliance ( AWACS E-3 de Geilenkirchen )"),
    "Russia [1992-]": (RUSSIE, "sûr", "puissance principale du bloc"),
    "China": (CHINE, "sûr", "puissance principale du bloc"),
    "Hong Kong": (CHINE, "sûr", "région administrative spéciale de la Chine depuis 1997"),
    # --- le bloc Russie-Chine au-delà des deux puissances
    "Belarus [1992-]": (SATELLITE, "sûr", "État de l'Union avec la Russie, OTSC, armes nucléaires russes stationnées"),
    "North Korea": (SATELLITE, "sûr", "traité de défense mutuelle avec la Russie ( 2024, troupes engagées ), alliance chinoise de 1961"),
    "Iran": (SATELLITE, "à valider", "partenariat stratégique global avec la Russie ( 2025 ), drones et missiles ; pas d'alliance de défense"),
    "Kazakhstan [1992-]": (SATELLITE, "à valider", "OTSC, mais politique « multivectorielle »"),
    "Kyrgyzstan": (SATELLITE, "à valider", "OTSC, base aérienne russe de Kant"),
    "Tajikistan": (SATELLITE, "à valider", "OTSC, 201e base russe"),
    "Myanmar": (SATELLITE, "à valider", "junte armée par la Russie et la Chine"),
    "Cambodia": (SATELLITE, "à valider", "base navale de Ream ouverte à la Chine"),
    "Laos": (SATELLITE, "à valider", "dans l'orbite économique et militaire de la Chine"),
    "Venezuela": (SATELLITE, "à valider", "armé par la Russie ( Su-30, S-300 ), partenaire de la Chine"),
    "Cuba": (SATELLITE, "à valider", "partenaire historique de la Russie"),
    "Nicaragua": (SATELLITE, "à valider", "partenaire de la Russie"),
    "Eritrea [1993-]": (SATELLITE, "à valider", "soutien de la Russie à l'ONU"),
    "Mali [1960-]": (SATELLITE, "à valider", "Alliance des États du Sahel, Africa Corps russe"),
    "Burkina Faso [1960-]": (SATELLITE, "à valider", "Alliance des États du Sahel, Africa Corps russe"),
    "Niger": (SATELLITE, "à valider", "Alliance des États du Sahel, Africa Corps russe"),
    "Central African Republic [1960-]": (SATELLITE, "à valider", "Wagner puis Africa Corps"),
    # --- ceux qui se battraient aux côtés de l'OTAN sans en être membres
    "Ukraine [1992-]": (PARTENAIRE_OTAN, "à valider", "en guerre contre la Russie, armée par l'OTAN"),
    "Japan": (PARTENAIRE_OTAN, "à valider", "allié des États-Unis ( traité de 1960 ), partenaire de l'OTAN"),
    "South Korea": (PARTENAIRE_OTAN, "à valider", "allié des États-Unis ( traité de 1953 ), partenaire de l'OTAN"),
    "Australia": (PARTENAIRE_OTAN, "à valider", "AUKUS, partenaire de l'OTAN"),
    "New Zealand": (PARTENAIRE_OTAN, "à valider", "partenaire de l'OTAN"),
    "Taiwan": (PARTENAIRE_OTAN, "à valider", "menacé par la Chine, armé par les États-Unis ; pas d'alliance formelle"),
    # --- des cas à trancher, laissés neutres
    "Pakistan": (NEUTRE, "à valider", "allié de la Chine ( JF-17, J-10C ), mais pas contre l'OTAN : à trancher"),
    "India": (NEUTRE, "à valider", "matériel russe et occidental, rivale de la Chine"),
    "Algeria": (NEUTRE, "à valider", "grand client de l'armement russe ( Su-30MKA, S-400 ), mais non alignée ( 29/09, Younes )"),
    "Syria": (NEUTRE, "à valider", "matériel soviétique, mais le régime allié de la Russie est tombé en décembre 2024"),
    "Armenia": (NEUTRE, "à valider", "OTSC gelée depuis 2024"),
    "Serbia [1992-]": (NEUTRE, "à valider", "neutralité militaire, matériel russe et chinois"),
    "Georgia [1991-]": (NEUTRE, "à valider", "candidate à l'OTAN sur le papier, gouvernement proche de Moscou"),
    "Moldova [1992-]": (NEUTRE, "à valider", "neutralité constitutionnelle, penche vers l'UE"),
})

_HISTORIQUES = ("Chechnya [1991-2000]", "Czechoslovakia  [-1992]", "Germany [DDR, -1990]", "Germany [Nazi]",
                "North Vietnam [-1975]", "South Vietnam [-1975]", "Soviet Union [-1991]", "Yugoslavia [-1992]", "Rhodesia")
_NON_ETATIQUES = ("None", "Unknown", "Generic", "Civilian", "Commercial", "Pirates", "Rebels", "Terrorists", "Hamas",
                  "Junkyard", "European Union [1993-]")
BLOCS.update({p: (HISTORIQUE, "sûr", "n'existe plus en 2026") for p in _HISTORIQUES})
BLOCS.update({p: (NON_ETATIQUE, "sûr", "pas un État") for p in _NON_ETATIQUES})


def bloc(pays):
    """( bloc, certitude, raison ) ; tout pays non classé est NEUTRE « sûr » ( aucune alliance avec l'un des deux camps )."""
    return BLOCS.get(pays, (NEUTRE, "sûr", "aucune alliance de défense avec l'un des deux camps"))
