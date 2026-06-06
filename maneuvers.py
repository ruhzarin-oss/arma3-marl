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
POSTE_RES = (15060, 15740)        # poste d'attente réserve
QRF_PT    = (15000, 16350)        # surgissement de la contre-attaque
LZ        = (15180, 15620)        # exfiltration

SPAWN_APPUI = (14920, 15620); SPAWN_ASSAUT = (15080, 15600)
SPAWN_A_EST = (15290, 15740); SPAWN_RESERVE = (15000, 15560)
SPAWNS = {"SQ_APPUI": SPAWN_APPUI, "SQ_A_OUEST": SPAWN_ASSAUT, "SQ_A_EST": SPAWN_A_EST, "SQ_RESERVE": SPAWN_RESERVE}
GARRISON = [(COMPLEXE[0], COMPLEXE[1], 12, 80), (15150, 16120, 4, 120), (14860, 16110, 4, 120)]  # 12 + 2 patrouilles
SQUADS = (("SQ_APPUI", 7), ("SQ_A_OUEST", 7), ("SQ_A_EST", 7), ("SQ_RESERVE", 7))

# succès commun = ennemi brisé (>=70 % détruit) + pertes contenues (<=50 %) — déf. « militaire » P-v3b
SUCCESS = ("all", [("enemy_dead_frac", 0.7), ("losses_max", 0.5)])


def _qrf_on_enter(qrf):
    """Spawn de la QRF à l'entrée en consolidation (une seule fois)."""
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
         "on_enter": _qrf_on_enter(qrf),
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


MANEUVERS = {"M1": appui_assaut, "M2": double_enveloppement,
             "M3": enveloppement_simple, "M4": assaut_masse,
             "M5": feinte_debordement, "M6": infiltration, "M7": attaque_echelonnee}
