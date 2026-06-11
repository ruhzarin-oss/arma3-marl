"""maneuvers — RÉPERTOIRE DOCTRINAL CODÉ [pile 1/5, voie « école de guerre »]. Chaque manœuvre militaire
classique est traduite en PLAN-DICT exécutable par OperationRunner (op_arma) : rôles d'escouade × phases ×
postures {move/assault/suppress/hold} + transitions/contingences. Toutes s'exécutent dans le VRAI Arma via
le cerveau gelé koth_finetuned -> Arma-exécutables PAR CONSTRUCTION (pas de fiction de sim). Le « manager »
ne choisira plus des micro-ordres bruts (où il inventait le parking-CRETE creux) mais UNE manœuvre du
répertoire. On les mesure d'abord une à une en Arma (run_maneuver.py) -> table empirique -> sélecteur.

Indices escouade : 0 SQ_APPUI, 1 SQ_A_OUEST, 2 SQ_A_EST, 3 SQ_RESERVE."""

# --- géographie palier 2 (identique à run_op) + 2 points de flanc pour l'enveloppement réel ---
COMPLEXE  = (15000, 16000)        # objectif : garnison
CRETE     = (14880, 15860)        # position d'appui / base de feu (overwatch SO)
ATTENTE   = (15120, 15820)        # attente assaut ouest
ATTENTE_E = (15260, 15980)        # attente assaut est
LIGNE_O   = (15090, 15930)        # ligne de départ ouest (assaut frontal)
LIGNE_E   = (15200, 16010)        # ligne de départ est (assaut frontal)
FLANC_O   = (14800, 16010)        # flanc OUEST réel du complexe (déborde par l'ouest)
FLANC_E   = (15230, 16110)        # flanc EST/NE réel du complexe (déborde par l'est)
INF_O     = (14960, 15910)        # axe d'infiltration SUD-ouest (sous l'écran de patrouilles nord ~16110)
INF_E     = (15060, 15910)        # axe d'infiltration SUD-est (x à l'ouest de la patrouille nord 15150)
POSTE_RES = (15060, 15800)        # poste d'attente réserve [v3 07/06 : 15740=EAU -> 15800 sec mesuré]
QRF_PT    = (15000, 16350)        # surgissement de la contre-attaque
LZ        = (15180, 15840)        # exfiltration [v3 07/06 : 15620=OCÉAN -> 15840 sec mesuré]

SPAWN_APPUI = (14920, 15830); SPAWN_ASSAUT = (15080, 15830)   # [v3 : anciens spawns DANS L'EAU]
SPAWN_A_EST = (15290, 15900); SPAWN_RESERVE = (15000, 15820)  # [v3 : idem — fini la nage d'approche]
SPAWNS = {"SQ_APPUI": SPAWN_APPUI, "SQ_A_OUEST": SPAWN_ASSAUT, "SQ_A_EST": SPAWN_A_EST, "SQ_RESERVE": SPAWN_RESERVE}
GARRISON = [(COMPLEXE[0], COMPLEXE[1], 12, 80), (15150, 16120, 4, 120), (14860, 16110, 4, 120)]  # 12 + 2 patrouilles
SQUADS = (("SQ_APPUI", 7), ("SQ_A_OUEST", 7), ("SQ_A_EST", 7), ("SQ_RESERVE", 7))

# succès commun = ennemi brisé (>=70 % détruit) + pertes contenues (<=50 %) — déf. « militaire » P-v3b
SUCCESS = ("all", [("enemy_dead_frac", 0.7), ("losses_max", 0.5)])


def _qrf_trigger(qrf):
    """Spawn de la QRF (une seule fois). [v3 07/06] Déclenchée par la CHUTE DE LA GARNISON, vérifiée à
    CHAQUE step par OperationRunner (clé plan 'qrf_on_garrison') — plus par l'entrée en CONSOLIDATION :
    les chemins de contingence sautaient la phase et gagnaient sans jamais affronter la contre-attaque
    (artefact disséqué sur l'op AZALAI-01, flattait M2/M5/M6). Réponse à la PRISE, pas à la position —
    report du trou #6 du sim op."""
    def f(r):
        if "qrf" in r.qrf_done:
            return
        r.qrf_done.add("qrf")
        if qrf == "mech":
            r.env.spawn_qrf_mech(QRF_PT[0], QRF_PT[1], 6, COMPLEXE); r.jlog("QRF", detail="contre-attaque mécanisée")
        else:
            r.env.spawn_qrf(QRF_PT[0], QRF_PT[1], 8, COMPLEXE); r.jlog("QRF", detail="contre-attaque 8 hommes")
    return f


def _consol_exfil(qrf):
    """Phases finales communes : CONSOLIDATION (tenir + encaisser la QRF) puis EXFIL."""
    return [
        {"name": "CONSOLIDATION",
         "orders": {"SQ_APPUI": (COMPLEXE, "hold"), "SQ_A_OUEST": (COMPLEXE, "hold"),
                    "SQ_A_EST": (COMPLEXE, "hold"), "SQ_RESERVE": (COMPLEXE, "assault")},
         "done_when": ("any", [("enemy_dead_frac", 0.85), ("steps", 105)]),
         "contingencies": [{"if": ("losses", 0.6), "reason": "consolidation intenable", "goto": "EXFIL"}]},
        {"name": "EXFIL",
         "orders": {sq: (LZ, "move") for sq in ("SQ_APPUI", "SQ_A_OUEST", "SQ_A_EST", "SQ_RESERVE")},
         # done_when sur N'IMPORTE QUELLE escouade arrivée (squad 0 peut être anéanti) sinon budget — bug smoke M2
         "done_when": ("any", [("squad_at", 0, LZ, 90), ("squad_at", 1, LZ, 90),
                                ("squad_at", 2, LZ, 90), ("squad_at", 3, LZ, 90), ("steps", 120)]),
         "contingencies": []},
    ]


# ============================================================================
# M1 — APPUI-FEU + ASSAUT (attaque délibérée, RÉFÉRENCE = partition P-v3b)
#   APPUI fixe sur CRETE (suppress) ; 2 escouades assaut frontal ; réserve sur pertes.
# ============================================================================
def appui_assaut(qrf="inf"):
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (CRETE, "move"), "SQ_A_OUEST": (ATTENTE, "move"),
                    "SQ_A_EST": (ATTENTE_E, "move"), "SQ_RESERVE": (POSTE_RES, "move")},
         "done_when": ("all", [("squad_at", 0, CRETE, 90), ("squad_at", 1, ATTENTE, 90),
                                ("squad_at", 2, ATTENTE_E, 90)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 210), "reason": "approche enlisée", "goto": "MISE_EN_PLACE"}]},
        {"name": "MISE_EN_PLACE",
         "orders": {"SQ_APPUI": (CRETE, "hold"), "SQ_A_OUEST": (LIGNE_O, "move"),
                    "SQ_A_EST": (LIGNE_E, "move"), "SQ_RESERVE": (POSTE_RES, "hold")},
         "done_when": ("all", [("squad_at", 1, LIGNE_O, 85), ("squad_at", 2, LIGNE_E, 85)]),
         "contingencies": [{"if": ("losses", 0.35), "reason": "pertes avant assaut", "goto": "EXFIL"},
                           {"if": ("steps", 135), "reason": "mise en place lente", "goto": "ASSAUT"}]},
        {"name": "ASSAUT",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                    "SQ_A_EST": (COMPLEXE, "assault"), "SQ_RESERVE": (POSTE_RES, "hold")},
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 1, COMPLEXE, 100), ("squad_at", 2, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.25), "reason": "assaut coûteux -> réserve", "goto": "ASSAUT_RENFORCE"},
                           {"if": ("steps", 330), "reason": "assaut enlisé", "goto": "EXFIL"}]},
        {"name": "ASSAUT_RENFORCE",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                    "SQ_A_EST": (COMPLEXE, "assault"), "SQ_RESERVE": (COMPLEXE, "assault")},
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 1, COMPLEXE, 100), ("squad_at", 3, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.5), "reason": "renfort trop coûteux", "goto": "EXFIL"},
                           {"if": ("steps", 165), "reason": "renfort enlisé", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M1-APPUI-ASSAUT", "phases": phases, "success": SUCCESS}


# ============================================================================
# M2 — DOUBLE ENVELOPPEMENT
#   APPUI fixe l'ennemi frontalement (suppress depuis CRETE) ; AO déborde par l'OUEST (FLANC_O),
#   AE par l'EST (FLANC_E) ; assaut convergent simultané ; réserve renforce.
# ============================================================================
def double_enveloppement(qrf="inf"):
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (CRETE, "move"), "SQ_A_OUEST": (FLANC_O, "move"),
                    "SQ_A_EST": (FLANC_E, "move"), "SQ_RESERVE": (POSTE_RES, "move")},
         # FIXER dès que le prong OUEST + l'appui sont en place ; on n'attend PLUS la branche est saignée
         # (bug smoke M2 : l'infiltration stagnait en attendant une escouade en train de mourir sur FLANC_E)
         "done_when": ("all", [("squad_at", 0, CRETE, 90), ("squad_at", 1, FLANC_O, 100)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en débordement", "goto": "EXFIL"},
                           {"if": ("steps", 200), "reason": "débordement enlisé", "goto": "FIXER"}]},
        {"name": "FIXER",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (FLANC_O, "hold"),
                    "SQ_A_EST": (FLANC_E, "hold"), "SQ_RESERVE": (POSTE_RES, "hold")},
         "done_when": ("steps", 25),
         "contingencies": [{"if": ("losses", 0.35), "reason": "appui décroché", "goto": "EXFIL"}]},
        {"name": "ASSAUT_CONVERGENT",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                    "SQ_A_EST": (COMPLEXE, "assault"), "SQ_RESERVE": (POSTE_RES, "hold")},
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 1, COMPLEXE, 100), ("squad_at", 2, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pince coûteuse -> réserve", "goto": "ASSAUT_RENFORCE"},
                           {"if": ("steps", 300), "reason": "pince enlisée", "goto": "EXFIL"}]},
        {"name": "ASSAUT_RENFORCE",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                    "SQ_A_EST": (COMPLEXE, "assault"), "SQ_RESERVE": (COMPLEXE, "assault")},
         "done_when": ("all", [("zone_clear", COMPLEXE, 60), ("squad_at", 3, COMPLEXE, 100)]),
         "contingencies": [{"if": ("losses", 0.5), "reason": "renfort trop coûteux", "goto": "EXFIL"},
                           {"if": ("steps", 165), "reason": "renfort enlisé", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M2-DOUBLE-ENVELOPPEMENT", "phases": phases, "success": SUCCESS}


# ============================================================================
# M3 — ENVELOPPEMENT SIMPLE (flanc lourd OUEST)
#   Base de feu LOURDE = APPUI (CRETE) + AE (ATTENTE_E) en suppress ; AO + RÉSERVE débordent en MASSE
#   par un seul flanc (FLANC_O) et assaut. Concentration sur un côté.
# ============================================================================
def enveloppement_simple(qrf="inf"):
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (CRETE, "move"), "SQ_A_EST": (ATTENTE_E, "move"),
                    "SQ_A_OUEST": (FLANC_O, "move"), "SQ_RESERVE": (FLANC_O, "move")},
         "done_when": ("all", [("squad_at", 0, CRETE, 90), ("squad_at", 2, ATTENTE_E, 90),
                                ("squad_at", 1, FLANC_O, 110)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 240), "reason": "approche enlisée", "goto": "BASE_DE_FEU"}]},
        {"name": "BASE_DE_FEU",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_EST": (COMPLEXE, "suppress"),
                    "SQ_A_OUEST": (FLANC_O, "hold"), "SQ_RESERVE": (FLANC_O, "hold")},
         "done_when": ("steps", 25),
         "contingencies": [{"if": ("losses", 0.35), "reason": "base de feu décrochée", "goto": "EXFIL"}]},
        {"name": "ASSAUT_FLANC",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_EST": (COMPLEXE, "suppress"),
                    "SQ_A_OUEST": (COMPLEXE, "assault"), "SQ_RESERVE": (COMPLEXE, "assault")},
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 1, COMPLEXE, 100), ("squad_at", 3, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.45), "reason": "assaut de flanc coûteux", "goto": "EXFIL"},
                           {"if": ("steps", 320), "reason": "assaut de flanc enlisé", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M3-ENVELOPPEMENT-SIMPLE", "phases": phases, "success": SUCCESS}


# ============================================================================
# M4 — ASSAUT FRONTAL MASSÉ (surprise / vitesse, SANS base de feu dédiée)
#   Approche couverte par axes puis les 4 escouades assaillent le complexe SIMULTANÉMENT. Rapide, coûteux.
# ============================================================================
def assaut_masse(qrf="inf"):
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (ATTENTE, "move"), "SQ_A_OUEST": (LIGNE_O, "move"),
                    "SQ_A_EST": (LIGNE_E, "move"), "SQ_RESERVE": (ATTENTE, "move")},
         "done_when": ("all", [("squad_at", 1, LIGNE_O, 90), ("squad_at", 2, LIGNE_E, 90)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 200), "reason": "approche enlisée", "goto": "ASSAUT_MASSE"}]},
        {"name": "ASSAUT_MASSE",
         "orders": {sq: (COMPLEXE, "assault") for sq in ("SQ_APPUI", "SQ_A_OUEST", "SQ_A_EST", "SQ_RESERVE")},
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 1, COMPLEXE, 100), ("squad_at", 2, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.55), "reason": "assaut massé saigné", "goto": "EXFIL"},
                           {"if": ("steps", 300), "reason": "assaut massé enlisé", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M4-ASSAUT-MASSE", "phases": phases, "success": SUCCESS}


# ============================================================================
# M5 — FEINTE + DÉBORDEMENT
#   Force de DÉMONSTRATION (APPUI + AE) fixe bruyamment sur l'axe EST (suppress) ; effort principal
#   (AO + RÉSERVE) déborde par l'OUEST (FLANC_O) et assaut.
#   CAVEAT assumé : l'ennemi est statique -> la tromperie ne déplace aucune réserve ; témoin négatif
#   (montrer que la feinte n'ajoute rien ici est un résultat honnête). Mécaniquement = 2 suppress E + 2 assaut O.
# ============================================================================
def feinte_debordement(qrf="inf"):
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (ATTENTE_E, "move"), "SQ_A_EST": (ATTENTE_E, "move"),
                    "SQ_A_OUEST": (FLANC_O, "move"), "SQ_RESERVE": (FLANC_O, "move")},
         "done_when": ("all", [("squad_at", 0, ATTENTE_E, 100), ("squad_at", 1, FLANC_O, 110)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 220), "reason": "approche enlisée", "goto": "DEMONSTRATION"}]},
        {"name": "DEMONSTRATION",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_EST": (COMPLEXE, "suppress"),
                    "SQ_A_OUEST": (FLANC_O, "hold"), "SQ_RESERVE": (FLANC_O, "hold")},
         "done_when": ("steps", 25),
         "contingencies": [{"if": ("losses", 0.35), "reason": "démonstration décrochée", "goto": "EXFIL"}]},
        {"name": "ASSAUT_PRINCIPAL",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_EST": (COMPLEXE, "suppress"),
                    "SQ_A_OUEST": (COMPLEXE, "assault"), "SQ_RESERVE": (COMPLEXE, "assault")},
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 1, COMPLEXE, 100), ("squad_at", 3, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.45), "reason": "effort principal coûteux", "goto": "EXFIL"},
                           {"if": ("steps", 320), "reason": "effort principal enlisé", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M5-FEINTE-DEBORDEMENT", "phases": phases, "success": SUCCESS}


# ============================================================================
# M6 — INFILTRATION PAR AXE COUVERT
#   Approche par le SUD (INF_O/INF_E, sous l'écran de patrouilles nord), PAS de base de feu préparatoire,
#   assaut rapproché simultané. Opérationnalise la leçon de M2 : la ROUTE est une variable physique qui paie.
# ============================================================================
def infiltration(qrf="inf"):
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (INF_O, "move"), "SQ_A_OUEST": (INF_O, "move"),
                    "SQ_A_EST": (INF_E, "move"), "SQ_RESERVE": (INF_E, "move")},
         "done_when": ("all", [("squad_at", 1, INF_O, 90), ("squad_at", 2, INF_E, 90)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "infiltration détectée", "goto": "EXFIL"},
                           {"if": ("steps", 200), "reason": "infiltration lente", "goto": "ASSAUT_RAPPROCHE"}]},
        {"name": "ASSAUT_RAPPROCHE",
         "orders": {sq: (COMPLEXE, "assault") for sq in ("SQ_APPUI", "SQ_A_OUEST", "SQ_A_EST", "SQ_RESERVE")},
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 1, COMPLEXE, 100), ("squad_at", 2, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.5), "reason": "assaut rapproché saigné", "goto": "EXFIL"},
                           {"if": ("steps", 300), "reason": "assaut rapproché enlisé", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M6-INFILTRATION", "phases": phases, "success": SUCCESS}


# ============================================================================
# M7 — ATTAQUE ÉCHELONNÉE (vagues successives + passage de lignes)
#   1er échelon (AO + AE) assaut ; quand il est usé (pertes globales ~25 %), le 2e échelon (APPUI + RÉSERVE)
#   PASSE LES LIGNES et reprend l'assaut, le 1er passe en appui-feu. Mécanisme physique = préservation/relève.
# ============================================================================
def attaque_echelonnee(qrf="inf"):
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_A_OUEST": (LIGNE_O, "move"), "SQ_A_EST": (LIGNE_E, "move"),
                    "SQ_APPUI": (ATTENTE, "move"), "SQ_RESERVE": (POSTE_RES, "move")},
         "done_when": ("all", [("squad_at", 1, LIGNE_O, 90), ("squad_at", 2, LIGNE_E, 90)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 200), "reason": "approche enlisée", "goto": "ASSAUT_ECHELON_1"}]},
        {"name": "ASSAUT_ECHELON_1",
         "orders": {"SQ_A_OUEST": (COMPLEXE, "assault"), "SQ_A_EST": (COMPLEXE, "assault"),
                    "SQ_APPUI": (ATTENTE, "hold"), "SQ_RESERVE": (POSTE_RES, "hold")},
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 1, COMPLEXE, 100), ("squad_at", 2, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.25), "reason": "1er échelon usé -> passage de lignes", "goto": "PASSAGE_ECHELON_2"},
                           {"if": ("steps", 240), "reason": "1er échelon enlisé -> 2e échelon", "goto": "PASSAGE_ECHELON_2"}]},
        {"name": "PASSAGE_ECHELON_2",
         "orders": {"SQ_APPUI": (COMPLEXE, "assault"), "SQ_RESERVE": (COMPLEXE, "assault"),
                    "SQ_A_OUEST": (COMPLEXE, "suppress"), "SQ_A_EST": (COMPLEXE, "suppress")},
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 0, COMPLEXE, 100), ("squad_at", 3, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.5), "reason": "2e échelon trop coûteux", "goto": "EXFIL"},
                           {"if": ("steps", 240), "reason": "2e échelon enlisé", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M7-ATTAQUE-ECHELONNEE", "phases": phases, "success": SUCCESS}


def _with_qrf_trigger(fn):
    """[v3] Greffe le déclencheur QRF-sur-garnison + l'effectif garnison sur le plan (lu par le runner)."""
    def g(qrf="inf"):
        p = fn(qrf)
        p["qrf_on_garrison"] = _qrf_trigger(qrf)
        p["garr_n"] = GARRISON[0][2]
        return p
    return g


MANEUVERS = {"M1": appui_assaut, "M2": double_enveloppement,
             "M3": enveloppement_simple, "M4": assaut_masse,
             "M5": feinte_debordement, "M6": infiltration, "M7": attaque_echelonnee}
MANEUVERS = {k: _with_qrf_trigger(v) for k, v in MANEUVERS.items()}   # [v3] QRF-sur-garnison partout


# ============================================================================
# EXTENSION DU RÉPERTOIRE (10/06) — recherche doctrinale DOCTRINE-REPERTOIRE.md
# Points nouveaux de la géographie (entre l'objectif 16000 et le point QRF 16350 -> terre sûre)
# ============================================================================
ARRIERE = (15000, 16230)   # l'arrière du complexe (axe de fuite/renfort)
PIVOT_E = (15300, 16150)   # point de contournement profond est
BLOC_N  = (15040, 16180)   # position de blocage nord (enclume)


# ============================================================================
# M8 — PERCÉE (penetration) : TOUTE la force sur UN axe étroit -> rupture -> exploitation vers l'arrière.
#   Bat : défenses étalées/cordon. Battue par : défense en profondeur, réserve mobile.
# ============================================================================
def percee(qrf="inf"):
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (CRETE, "move"), "SQ_A_OUEST": (ATTENTE, "move"),
                    "SQ_A_EST": (ATTENTE, "move"), "SQ_RESERVE": (ATTENTE, "move")},
         "done_when": ("all", [("squad_at", 0, CRETE, 90), ("squad_at", 1, ATTENTE, 90),
                                ("squad_at", 2, ATTENTE, 110), ("squad_at", 3, ATTENTE, 110)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 210), "reason": "approche enlisee", "goto": "RUPTURE"}]},
        {"name": "RUPTURE",   # tout sur la ligne ouest, axe etroit
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (LIGNE_O, "assault"),
                    "SQ_A_EST": (LIGNE_O, "assault"), "SQ_RESERVE": (ATTENTE, "hold")},
         "done_when": ("any", [("squad_at", 1, LIGNE_O, 60), ("squad_at", 2, LIGNE_O, 60), ("steps", 120)]),
         "contingencies": [{"if": ("losses", 0.45), "reason": "rupture saignee", "goto": "EXFIL"}]},
        {"name": "EXPLOITATION",   # on passe AU TRAVERS : une escouade file a l ARRIERE, la reserve suit dans la breche
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (ARRIERE, "assault"),
                    "SQ_A_EST": (COMPLEXE, "assault"), "SQ_RESERVE": (LIGNE_O, "move")},
         "done_when": ("any", [("squad_at", 1, ARRIERE, 80), ("enemy_dead_frac", 0.7), ("steps", 150)]),
         "contingencies": [{"if": ("losses", 0.55), "reason": "exploitation intenable", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M8-PERCEE", "phases": phases, "success": SUCCESS}


# ============================================================================
# M9 — MOUVEMENT TOURNANT : prendre l ARRIERE AVANT l objectif -> forcer la defense a sortir de ses trous.
#   Bat : défenses ancrées au terrain. Battue par : hérisson (rien à tourner), réserve mobile.
# ============================================================================
def tournant(qrf="inf"):
    phases = [
        {"name": "FIXATION",
         "orders": {"SQ_APPUI": (CRETE, "move"), "SQ_A_OUEST": (FLANC_E, "move"),
                    "SQ_A_EST": (FLANC_E, "move"), "SQ_RESERVE": (FLANC_E, "move")},
         "done_when": ("all", [("squad_at", 0, CRETE, 90), ("squad_at", 2, FLANC_E, 90)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 210), "reason": "approche enlisee", "goto": "MARCHE_PROFONDE"}]},
        {"name": "MARCHE_PROFONDE",   # l appui FIXE par le feu pendant que 3 escouades contournent profond
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (PIVOT_E, "move"),
                    "SQ_A_EST": (PIVOT_E, "move"), "SQ_RESERVE": (PIVOT_E, "move")},
         "done_when": ("any", [("all", [("squad_at", 1, PIVOT_E, 90), ("squad_at", 2, PIVOT_E, 90)]), ("steps", 150)]),
         "contingencies": [{"if": ("losses", 0.4), "reason": "marche decouverte", "goto": "EXFIL"}]},
        {"name": "PRISE_ARRIERE",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (ARRIERE, "assault"),
                    "SQ_A_EST": (ARRIERE, "assault"), "SQ_RESERVE": (PIVOT_E, "hold")},
         "done_when": ("any", [("squad_at", 1, ARRIERE, 70), ("squad_at", 2, ARRIERE, 70), ("steps", 120)]),
         "contingencies": [{"if": ("losses", 0.5), "reason": "arriere imprenable", "goto": "EXFIL"}]},
        {"name": "ASSAUT_INVERSE",   # l objectif pris PAR LE NORD (sens inverse de toutes les autres manoeuvres)
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                    "SQ_A_EST": (COMPLEXE, "assault"), "SQ_RESERVE": (ARRIERE, "hold")},
         "done_when": ("any", [("enemy_dead_frac", 0.7), ("steps", 150)]),
         "contingencies": [{"if": ("losses", 0.55), "reason": "assaut inverse saigne", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M9-TOURNANT", "phases": phases, "success": SUCCESS}


# ============================================================================
# M10 — MARTEAU-ENCLUME : un bloc au nord (enclume) + l assaut au sud (marteau) ;
#   l ennemi qui rompt vers l arriere meurt sur le bloc. LE contre de la defense elastique.
# ============================================================================
def marteau_enclume(qrf="inf"):
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (CRETE, "move"), "SQ_A_OUEST": (ATTENTE, "move"),
                    "SQ_A_EST": (FLANC_E, "move"), "SQ_RESERVE": (FLANC_E, "move")},
         "done_when": ("all", [("squad_at", 0, CRETE, 90), ("squad_at", 1, ATTENTE, 90), ("squad_at", 2, FLANC_E, 90)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 210), "reason": "approche enlisee", "goto": "ENCLUME"}]},
        {"name": "ENCLUME",   # le bloc se met en place au nord PENDANT que le marteau attend
         "orders": {"SQ_APPUI": (CRETE, "hold"), "SQ_A_OUEST": (ATTENTE, "hold"),
                    "SQ_A_EST": (BLOC_N, "move"), "SQ_RESERVE": (BLOC_N, "move")},
         "done_when": ("any", [("squad_at", 2, BLOC_N, 80), ("squad_at", 3, BLOC_N, 80), ("steps", 135)]),
         "contingencies": [{"if": ("losses", 0.4), "reason": "enclume decouverte", "goto": "EXFIL"}]},
        {"name": "MARTEAU",   # l assaut pousse du sud ; le bloc TIENT (hold) et fauche ce qui reflue
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                    "SQ_A_EST": (BLOC_N, "hold"), "SQ_RESERVE": (BLOC_N, "hold")},
         "done_when": ("any", [("enemy_dead_frac", 0.7), ("steps", 165)]),
         "contingencies": [{"if": ("losses", 0.55), "reason": "marteau brise", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M10-MARTEAU-ENCLUME", "phases": phases, "success": SUCCESS}


# ============================================================================
# M11 — RAID (coup de main) : detruire vite et PARTIR avant la contre-attaque — pas de consolidation.
#   Bat : garnisons isolees. Suicidaire contre : appat.
# ============================================================================
def raid(qrf="inf"):
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (INF_O, "move"), "SQ_A_OUEST": (INF_O, "move"),
                    "SQ_A_EST": (INF_E, "move"), "SQ_RESERVE": (INF_E, "move")},
         "done_when": ("all", [("squad_at", 1, INF_O, 80), ("squad_at", 2, INF_E, 80)]),
         "contingencies": [{"if": ("losses", 0.25), "reason": "raid decele trop tot", "goto": "EXFIL"},
                           {"if": ("steps", 180), "reason": "approche enlisee", "goto": "COUP_DE_MAIN"}]},
        {"name": "COUP_DE_MAIN",   # tout le monde dedans, vite
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                    "SQ_A_EST": (COMPLEXE, "assault"), "SQ_RESERVE": (COMPLEXE, "assault")},
         "done_when": ("any", [("enemy_dead_frac", 0.7), ("steps", 150)]),
         "contingencies": [{"if": ("losses", 0.45), "reason": "coup de main rate", "goto": "EXFIL"}]},
        {"name": "EXFIL",   # PAS de consolidation : on part avant que la QRF ne morde
         "orders": {"SQ_APPUI": (LZ, "move"), "SQ_A_OUEST": (LZ, "move"),
                    "SQ_A_EST": (LZ, "move"), "SQ_RESERVE": (LZ, "move")},
         "done_when": ("any", [("squad_at", 0, LZ, 90), ("squad_at", 1, LZ, 90),
                                ("squad_at", 2, LZ, 90), ("squad_at", 3, LZ, 90), ("steps", 120)]),
         "contingencies": []},
    ]
    return {"name": "M11-RAID", "phases": phases, "success": SUCCESS}


# ============================================================================
# M12 — RECONNAISSANCE EN FORCE : une escouade SONDE le front est ; le plan SE DECIDE sur sa reception.
#   Branchement par contingences = mini-officier en dur. Sa valeur attendue = ROBUSTESSE inter-defenses.
#   Si la sonde saigne (front dur) -> debordement ouest ; si elle passe (front mou) -> assaut frontal.
#   Bonus doctrinal : un assaut frontal qui s eternise bascule de lui-meme en debordement (done_when -> +1).
# ============================================================================
def reco_en_force(qrf="inf"):
    phases = [
        {"name": "MISE_EN_PLACE",
         "orders": {"SQ_APPUI": (CRETE, "move"), "SQ_A_OUEST": (ATTENTE, "move"),
                    "SQ_A_EST": (ATTENTE_E, "move"), "SQ_RESERVE": (POSTE_RES, "move")},
         "done_when": ("all", [("squad_at", 0, CRETE, 90), ("squad_at", 2, ATTENTE_E, 90)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 210), "reason": "approche enlisee", "goto": "SONDE"}]},
        {"name": "SONDE",   # SQ_A_EST tate le front ; les autres attendent la lecture
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_EST": (LIGNE_E, "assault"),
                    "SQ_A_OUEST": (ATTENTE, "hold"), "SQ_RESERVE": (POSTE_RES, "hold")},
         "done_when": ("any", [("squad_at", 2, LIGNE_E, 70), ("steps", 75)]),
         "contingencies": [{"if": ("losses", 0.08), "reason": "la sonde saigne -> front dur -> debordement", "goto": "DEBORDEMENT_OUEST"}]},
        {"name": "ASSAUT_FRONTAL",   # front mou : on enfonce ; s il s eternise -> bascule debordement (+1)
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                    "SQ_A_EST": (COMPLEXE, "assault"), "SQ_RESERVE": (COMPLEXE, "assault")},
         "done_when": ("any", [("steps", 165)]),
         "contingencies": [{"if": ("enemy_dead_frac", 0.7), "reason": "ennemi brise -> consolidation", "goto": "CONSOLIDATION"},
                           {"if": ("losses", 0.55), "reason": "front dur finalement", "goto": "EXFIL"}]},
        {"name": "DEBORDEMENT_OUEST",   # front dur : bascule en enveloppement par l ouest
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (FLANC_O, "move"),
                    "SQ_A_EST": (ATTENTE_E, "hold"), "SQ_RESERVE": (FLANC_O, "move")},
         "done_when": ("any", [("squad_at", 1, FLANC_O, 80), ("steps", 120)]),
         "contingencies": [{"if": ("losses", 0.5), "reason": "debordement saigne", "goto": "EXFIL"}]},
        {"name": "ASSAUT_FLANC",
         "orders": {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                    "SQ_RESERVE": (COMPLEXE, "assault"), "SQ_A_EST": (LIGNE_E, "assault")},
         "done_when": ("any", [("enemy_dead_frac", 0.7), ("steps", 165)]),
         "contingencies": [{"if": ("losses", 0.55), "reason": "assaut flanc saigne", "goto": "EXFIL"}]},
    ] + _consol_exfil(qrf)
    return {"name": "M12-RECO-EN-FORCE", "phases": phases, "success": SUCCESS}


_EXT = {"M8": percee, "M9": tournant, "M10": marteau_enclume, "M11": raid, "M12": reco_en_force}
MANEUVERS.update({k: _with_qrf_trigger(v) for k, v in _EXT.items()})
