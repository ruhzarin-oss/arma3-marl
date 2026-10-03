"""L'INVENTAIRE RÉEL des forces aériennes ( octobre 2026 ) : ce que chaque pays POSSÈDE, ce qui est DISPONIBLE ( taux de
disponibilité technique ), ce qui sort d'usine par mois, le délai de convoyage. Source : recherche du 03/10
( ordre_de_bataille_2026.md, sources citées, valeurs centrales ).

Le moteur engage depuis cette RÉSERVE. Une perte se comble par la réserve, jamais par un achat : en guerre, un avion ne
s'achète pas ( Younes, 03/10 : « le moteur choisit lui-même les forces qu'il emploie » ). Quand la réserve est vide,
seule la production la remplit, au rythme réel.

CHOIX À VALIDER PAR YOUNES : valeurs centrales, taux de disponibilité, production mensuelle, délais de convoyage.
"""
import re

# ( pays, dbid DB3000, avions présents en octobre 2026 ) — valeurs centrales de la recherche du 03/10
PRESENTS = [
    ("Poland", 7087, 47),                       # F-16C/D Block 52+ ( 48 livrés, 1 perdu le 28/08/2025 )
    ("Poland", 6040, 12),                       # FA-50GF ( AIM-9 seulement ) ; FA-50PL pas avant 2027
    ("Poland", 2840, 10),                       # MiG-29 ( 10 au plus, retrait en cours )
    ("Poland", 6812, 2),                        # Saab 340 AEW
    ("Poland", 5395, 24),                       # Bayraktar TB2
    ("Finland", 2836, 60),                      # F/A-18C/D ( 53 C et 7 D )
    ("Sweden", 6788, 94),                       # Gripen C/D ( 16 promis à l'Ukraine à partir de 2027 )
    ("Denmark", 5180, 19),                      # F-35A au Danemark ( 17 à 21 )
    ("Denmark", 5756, 0),                       # F-16 : dernier vol le 18/01/2026
    ("Germany [FRG/Reunified]", 8261, 138),     # Typhoon
    ("Germany [FRG/Reunified]", 7611, 28),      # Tornado ECR ( 21 à 35 )
    ("Germany [FRG/Reunified]", 1626, 14),      # E-3A de l'OTAN ( NAEW&CF, payés par le pays hôte )
    ("United Kingdom", 8272, 4),                # Typhoon FGR4 de la police du ciel balte
    ("United States", 8094, 12),                # rotation américaine du théâtre ( aucune trouvée en 2025-2026 : à revoir )
    ("United States", 7712, 15),                # KC-135R ( 100th ARW, Mildenhall )
    ("United States", 4518, 6),                 # EA-18G ( déploiement de 2022 )
    ("United States", 4893, 6),                 # B-52H ( 6 à Fairford en mars 2026 )
    ("United States", 7473, 4),                 # MQ-9A ( Mirosławiec )
    ("United States", 5832, 2),                 # RC-135V
    ("Russia [1992-]", 6210, 34),               # Su-30SM2 ( 689e en partie, 4e régiment naval )
    ("Russia [1992-]", 6645, 48),               # Su-35S ( 689e, 159e, 790e )
    ("Russia [1992-]", 8333, 0),                # Su-57 : aucun face à la Baltique
    ("Russia [1992-]", 7023, 20),               # Tu-95MSM ( ~20 prêts dans toute la Russie )
    ("Russia [1992-]", 7021, 10),               # Tu-160M
    ("Russia [1992-]", 7022, 12),               # Tu-22M3M
    ("Russia [1992-]", 3461, 6),                # A-50U ( 2 abattus, 1 endommagé en 2024 )
    ("Russia [1992-]", 2687, 15),               # Il-78M
    ("Russia [1992-]", 4607, 3),                # Il-22PP
    ("Russia [1992-]", 2178, 6),                # Il-20M
    ("Russia [1992-]", 8324, 20),               # Orion
    ("Belarus [1992-]", 7695, 16),              # Su-30SM / SM2
    ("Belarus [1992-]", 5909, 20),              # MiG-29 actifs ( ~32 sur le papier )
    ("United States", 7913, 24),                # AH-64E d'une brigade d'aviation de combat en rotation
    ("Russia [1992-]", 5072, 20),               # Ka-52M ( 15e brigade, Ostrov ; l'essentiel en Ukraine )
    ("Russia [1992-]", 8100, 10),               # Mi-28NM
]

# Disponibilité technique ( part des avions présents en état de voler ), premier motif qui correspond
DISPO = [(r"AH-64|Ka-52|Mi-28", 0.70), (r"F-35", 0.50), (r"F-16", 0.70), (r"F/A-18|Hornet", 0.75), (r"Gripen|JAS 39", 0.80), (r"Typhoon|EF2000|Eurofighter", 0.65),
         (r"Tornado", 0.60), (r"MiG-29|MiG-31", 0.60), (r"^Su-", 0.65), (r"FA-50", 0.75), (r"Tu-|B-52|B-1", 0.60), (r"", 0.70)]

# Production par mois qui renforce la réserve d'un pays en guerre ( à valider )
PRODUCTION_MOIS = {("Russia [1992-]", 6645): 1.5, ("Russia [1992-]", 6210): 1.0, ("Germany [FRG/Reunified]", 8261): 1.0}

# Délai de convoyage d'un renfort ( heures de jeu ) : de sa base d'attache au théâtre, préparation comprise
DELAI_H = {"United States": 24.0}
DELAI_DEFAUT_H = 6.0


def disponibilite(nom):
    return next(t for motif, t in DISPO if re.search(motif, nom or ""))


def engageables(noms):
    """{ ( pays, dbid ) : avions disponibles } ; noms : { dbid : nom }."""
    return {(p, d): int(round(n * disponibilite(noms.get(d, "")))) for p, d, n in PRESENTS}


def delai_s(pays):
    return 3600.0 * DELAI_H.get(pays, DELAI_DEFAUT_H)
