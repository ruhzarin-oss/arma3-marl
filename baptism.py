"""baptism — BAPTÊME DES OPÉRATIONS. Chaque run reçoit un nom d'op traçable (« OP CIMETERRE-07 »),
affiché dans la mission visuelle et écrit dans le jsonl : chaque ligne de données devient une op nommée,
regardable, citable dans une note. Déterministe (manœuvre, seed) -> reproductible, pas d'horloge."""

NAMES = [
    "CIMETERRE", "SIROCCO", "EPERVIER", "TRAMONTANE", "HARFANG", "GERFAUT", "SAGAIE", "TANEZROUFT",
    "MISTRAL", "BURIN", "FENNEC", "ADRAR", "TASSILI", "SEKKIN", "OURAGAN", "BALISTE",
    "CHERGUI", "AZALAI", "HOGGAR", "TAGANT", "SAHEL", "KHAMSIN", "SIMOUN", "ERG",
    "REG", "BARKANE", "GHIBLI", "HABOOB", "ZEPHYR", "AQUILON", "BOREE", "NOROIT",
]

_MAN_IDX = {"M1": 0, "M2": 1, "M3": 2, "M4": 3, "M5": 4, "M6": 5, "M7": 6}


def op_name(maneuver, seed):
    """Nom de baptême déterministe : la manœuvre décale la liste, le seed numérote."""
    base = NAMES[(_MAN_IDX.get(maneuver, 7) * 16 + seed) % len(NAMES)]
    return "%s-%02d" % (base, seed)
