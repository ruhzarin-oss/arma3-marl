"""Budgets de défense réels, en milliards de dollars courants de 2024 ( SIPRI, base de données des dépenses militaires,
édition d'avril 2025, de mémoire : à revérifier avant une mesure qui en dépend ). Noms EXACTS de la base DB3000.

Ce qu'un pays verse à la guerre par minute d'horloge murale : budget x part du théâtre x PART_EQUIPEMENT / JOURS_PAR_AN,
chaque minute valant JOURS_PAR_MINUTE jours de budget. CHOIX À VALIDER : PART_EQUIPEMENT = 0,25 ( la part des achats
d'équipement dans un budget de défense européen, ~25 % en 2024 ) ; JOURS_PAR_MINUTE = 1 ( une minute de guerre = une
journée de budget : la Pologne s'offre un F-16 toutes les trois minutes environ )."""

BUDGET_2024_MDS = {
    "United States": 997.0, "China": 314.0, "Russia [1992-]": 149.0, "Germany [FRG/Reunified]": 88.5,
    "United Kingdom": 81.8, "France": 64.7, "Japan": 55.3, "South Korea": 47.6, "Poland": 38.0, "Italy": 38.0,
    "Australia": 33.8, "Ukraine [1992-]": 64.7, "Canada": 29.3, "Turkey": 25.0, "Spain": 24.6, "Netherlands": 22.9,
    "Taiwan": 16.5, "Sweden": 12.0, "Norway": 11.0, "Denmark": 9.9, "Iran": 7.9, "Finland": 7.3, "Belgium": 7.0,
    "Romania": 8.0, "Greece": 8.1, "Lithuania [1992-]": 2.3, "Latvia [1992-]": 1.7, "Estonia [1992-]": 1.6,
    "Belarus [1992-]": 1.5, "North Korea": 4.0,
}
PART_EQUIPEMENT = 0.25
JOURS_PAR_AN = 365.0
JOURS_PAR_MINUTE = 1.0


def millions_par_minute(pays, part_theatre):
    """Millions de dollars qu'un pays met en achats d'équipement sur le théâtre, par minute d'horloge murale."""
    return BUDGET_2024_MDS.get(pays, 0.0) * 1000.0 * part_theatre * PART_EQUIPEMENT * JOURS_PAR_MINUTE / JOURS_PAR_AN
