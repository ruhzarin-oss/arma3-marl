"""run_op — OPÉRATION HARMATTAN-1 : raid de complexe en 5 phases, 2 escouades (cerveau RL gelé en micro),
garnison + QRF ennemies scriptées. Le chef d'opération (machine à phases) donne les ordres ; le journal
de décisions trace tout (op_journal.jsonl). Usage : run_op.py [--reps N] [--acc 4] [--plan A|B]"""
import argparse
import numpy as np
import torch
from op_arma import OpArma, OperationRunner, DEV
from train_koth_gpu import Net

# ---------------------------------------------------------------- géographie de l'opération (autour de la zone rodée)
COMPLEXE = (15000, 16000)        # l'objectif : garnison ennemie
CRETE    = (14880, 15860)        # position d'appui (overwatch)
ATTENTE  = (15120, 15820)        # point d'attente de l'élément d'assaut
LIGNE    = (15090, 15930)        # ligne de départ de l'assaut
QRF_PT   = (15000, 16350)        # d'où surgit la contre-attaque
LZ       = (15180, 15620)        # zone d'exfiltration
SPAWN_APPUI  = (14920, 15620)
SPAWN_ASSAUT = (15080, 15600)


# ---------------------------------------------------------------- PALIER 2 : échelle (4 escouades, ennemi renforcé)
ATTENTE_E     = (15260, 15980)       # point d'attente de l'assaut EST
LIGNE_O       = (15090, 15930)       # ligne de départ ouest (= LIGNE)
LIGNE_E       = (15200, 16010)       # ligne de départ est
SPAWN_A_EST   = (15290, 15740)
SPAWN_RESERVE = (15000, 15560)
POSTE_RES     = (15060, 15740)       # poste d'attente de la réserve

SQUADS_P2 = (("SQ_APPUI", 7), ("SQ_A_OUEST", 7), ("SQ_A_EST", 7), ("SQ_RESERVE", 7))
SPAWNS_P2 = {"SQ_APPUI": SPAWN_APPUI, "SQ_A_OUEST": SPAWN_ASSAUT, "SQ_A_EST": SPAWN_A_EST, "SQ_RESERVE": SPAWN_RESERVE}
GARRISON_P2 = [(COMPLEXE[0], COMPLEXE[1], 12, 80), (15150, 16120, 4, 120), (14860, 16110, 4, 120)]  # 12 + 2 patrouilles de 4


def make_plan_p2(variant, qrf="inf"):
    """Palier 2. A = appui + 2 assauts convergents + réserve en arrière (engagée par contingence).
    B = tout le monde à l'assaut d'emblée. Indices : 0 APPUI, 1 A_OUEST, 2 A_EST, 3 RÉSERVE."""
    assault_orders_A = {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                        "SQ_A_EST": (COMPLEXE, "assault"), "SQ_RESERVE": (POSTE_RES, "hold")}
    assault_orders_B = {sq: (COMPLEXE, "assault") for sq in ("SQ_APPUI", "SQ_A_OUEST", "SQ_A_EST", "SQ_RESERVE")}
    renforce = {"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_A_OUEST": (COMPLEXE, "assault"),
                "SQ_A_EST": (COMPLEXE, "assault"), "SQ_RESERVE": (COMPLEXE, "assault")}
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (CRETE, "move"), "SQ_A_OUEST": (ATTENTE, "move"),
                    "SQ_A_EST": (ATTENTE_E, "move"), "SQ_RESERVE": (POSTE_RES, "move")},
         "done_when": ("all", [("squad_at", 0, CRETE, 90), ("squad_at", 1, ATTENTE, 90),
                                ("squad_at", 2, ATTENTE_E, 90), ("squad_at", 3, POSTE_RES, 90)]),
         "contingencies": [{"if": ("losses", 0.3), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 140), "reason": "approche enlisée", "goto": "MISE_EN_PLACE"}]},
        {"name": "MISE_EN_PLACE",
         "orders": {"SQ_APPUI": (CRETE, "hold"), "SQ_A_OUEST": (LIGNE_O, "move"),
                    "SQ_A_EST": (LIGNE_E, "move"), "SQ_RESERVE": (POSTE_RES, "hold")},
         "done_when": ("all", [("squad_at", 1, LIGNE_O, 85), ("squad_at", 2, LIGNE_E, 85)]),
         "contingencies": [{"if": ("losses", 0.35), "reason": "pertes avant assaut", "goto": "EXFIL"},
                           {"if": ("steps", 90), "reason": "mise en place trop lente", "goto": "ASSAUT"}]},
        {"name": "ASSAUT",
         "orders": (assault_orders_A if variant == "A" else assault_orders_B),
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 1, COMPLEXE, 100), ("squad_at", 2, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.25), "reason": "assaut coûteux -> engagement réserve", "goto": "ASSAUT_RENFORCE"},
                           {"if": ("steps", 220), "reason": "assaut enlisé", "goto": "EXFIL"}]},
        {"name": "ASSAUT_RENFORCE",
         "orders": renforce,
         "done_when": ("all", [("zone_clear", COMPLEXE, 60),
                                ("any", [("squad_at", 1, COMPLEXE, 100), ("squad_at", 2, COMPLEXE, 100),
                                          ("squad_at", 3, COMPLEXE, 100)])]),
         "contingencies": [{"if": ("losses", 0.5), "reason": "assaut renforcé trop coûteux", "goto": "EXFIL"},
                           {"if": ("steps", 110), "reason": "assaut renforcé enlisé", "goto": "EXFIL"}]},
        {"name": "CONSOLIDATION",
         "orders": {"SQ_APPUI": (COMPLEXE, "hold"), "SQ_A_OUEST": (COMPLEXE, "hold"),
                    "SQ_A_EST": (COMPLEXE, "hold"), "SQ_RESERVE": (COMPLEXE, "assault")},
         "on_enter": (lambda r: ((r.env.spawn_qrf_mech(QRF_PT[0], QRF_PT[1], 6, COMPLEXE),
                                  r.jlog("QRF", detail="contre-attaque MÉCANISÉE"))
                                  if qrf == "mech" else
                                  (r.env.spawn_qrf(QRF_PT[0], QRF_PT[1], 8, COMPLEXE),
                                   r.jlog("QRF", detail="contre-attaque : 8 hommes")))
                                  if "qrf" not in r.qrf_done and not r.qrf_done.add("qrf") else None),
         "done_when": ("any", [("enemy_dead_frac", 0.85), ("steps", 70)]),
         "contingencies": [{"if": ("losses", 0.6), "reason": "consolidation intenable", "goto": "EXFIL"}]},
        {"name": "EXFIL",
         "orders": {sq: (LZ, "move") for sq in ("SQ_APPUI", "SQ_A_OUEST", "SQ_A_EST", "SQ_RESERVE")},
         "done_when": ("any", [("all", [("squad_at", 0, LZ, 90), ("squad_at", 1, LZ, 90)]), ("steps", 130)]),
         "contingencies": []},
    ]
    return {"name": "HARMATTAN-2v3%s (plan %s)" % ("-mech" if qrf == "mech" else "", variant), "phases": phases,
            "success": ("all", [("enemy_dead_frac", 0.7), ("losses_max", 0.5),
                                ("any", [("squad_at", 0, LZ, 100), ("squad_at", 1, LZ, 100)])])}


def make_plan(variant, qrf="inf"):
    """Variante A = doctrine 'appui d'abord' (suppression avant assaut). Variante B = assaut direct (pas de phase de fixation)."""
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (CRETE, "move"), "SQ_ASSAUT": (ATTENTE, "move")},
         "done_when": ("all", [("squad_at", 0, CRETE, 90), ("squad_at", 1, ATTENTE, 90)]),
         "contingencies": [{"if": ("losses", 0.35), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 120), "reason": "approche enlisée", "goto": "MISE_EN_PLACE"}]},
        {"name": "MISE_EN_PLACE",
         "orders": {"SQ_APPUI": (CRETE, "hold"), "SQ_ASSAUT": (LIGNE, "move")},
         "done_when": ("squad_at", 1, LIGNE, 85),
         "contingencies": [{"if": ("losses", 0.4), "reason": "pertes avant assaut", "goto": "EXFIL"},
                           {"if": ("steps", 80), "reason": "mise en place trop lente", "goto": "ASSAUT"}]},
        {"name": "ASSAUT",
         "orders": ({"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_ASSAUT": (COMPLEXE, "assault")} if variant == "A"
                    else {"SQ_APPUI": (COMPLEXE, "assault"), "SQ_ASSAUT": (COMPLEXE, "assault")}),
         "done_when": ("all", [("zone_clear", COMPLEXE, 60), ("squad_at", 1, COMPLEXE, 85)]),
         "contingencies": [{"if": ("losses", 0.5), "reason": "assaut trop coûteux", "goto": "EXFIL"},
                           {"if": ("steps", 160), "reason": "assaut enlisé", "goto": "EXFIL"}]},
        {"name": "CONSOLIDATION",
         "orders": {"SQ_APPUI": (COMPLEXE, "hold"), "SQ_ASSAUT": (COMPLEXE, "hold")},
         "on_enter": (lambda r: ((r.env.spawn_qrf_mech(QRF_PT[0], QRF_PT[1], 6, COMPLEXE),
                                 r.jlog("QRF", detail="contre-attaque MÉCANISÉE : Ifrit HMG + 6 débarqués"))
                                 if qrf == "mech" else
                                 (r.env.spawn_qrf(QRF_PT[0], QRF_PT[1], 8, COMPLEXE),
                                  r.jlog("QRF", detail="contre-attaque ennemie : 8 hommes depuis le nord")))
                                 if "qrf" not in r.qrf_done and not r.qrf_done.add("qrf") else None),
         "done_when": ("any", [("enemy_dead_frac", 0.85), ("steps", 70)]),
         "contingencies": [{"if": ("losses", 0.6), "reason": "consolidation intenable", "goto": "EXFIL"}]},
        {"name": "EXFIL",
         "orders": {"SQ_APPUI": (LZ, "move"), "SQ_ASSAUT": (LZ, "move")},
         "done_when": ("any", [("all", [("squad_at", 0, LZ, 90), ("squad_at", 1, LZ, 90)]), ("steps", 80)]),
         "contingencies": []},
    ]
    return {"name": "HARMATTAN-1v2%s (plan %s)" % ("-mech" if qrf == "mech" else "", variant), "phases": phases,
            # succès : l'ennemi a été brisé (≥70 % détruit), pertes contenues (≤50 %), au moins un élément à la LZ
            "success": ("all", [("enemy_dead_frac", 0.7), ("losses_max", 0.5),
                                ("any", [("squad_at", 0, LZ, 100), ("squad_at", 1, LZ, 100)])])}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=1)
    p.add_argument("--acc", type=float, default=4.0)
    p.add_argument("--plan", type=str, default="A", choices=["A", "B"])
    p.add_argument("--journal", type=str, default="op_journal.jsonl")
    a = p.parse_args()

    net = Net(10, 4, 512, 3).to(DEV)
    net.load_state_dict(torch.load("/home/younes/arma3-marl/koth_finetuned.pt", map_location=DEV)); net.eval()

    results = []
    for rep in range(a.reps):
        env = OpArma(squads=(("SQ_APPUI", 7), ("SQ_ASSAUT", 7)), acc=a.acc, seed=rep)
        env.spawn({"SQ_APPUI": SPAWN_APPUI, "SQ_ASSAUT": SPAWN_ASSAUT},
                  garrison=[(COMPLEXE[0], COMPLEXE[1], 8, 80)])
        runner = OperationRunner(env, net, make_plan(a.plan), log_path=a.journal)
        ok = runner.run(max_steps=500)
        results.append(bool(ok))
        print("[REP %d/%d] %s | pertes %.0f%% | ennemis restants %d" %
              (rep + 1, a.reps, "SUCCÈS ✅" if ok else "ÉCHEC ❌", runner.losses() * 100, int(env.en_alive().sum())), flush=True)
    print("BILAN plan %s : %d/%d succès" % (a.plan, sum(results), len(results)), flush=True)
