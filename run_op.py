"""run_op — OPÉRATION HARMATTAN-1 : raid de complexe en 5 phases, 2 escouades (cerveau RL gelé en micro),
garnison + QRF ennemies scriptées. Le chef d'opération (machine à phases) donne les ordres ; le journal
de décisions trace tout (op_journal.jsonl). Usage : run_op.py [--reps N] [--acc 4] [--plan A|B]"""
import argparse
import numpy as np
import torch
from op_arma import OpArma, OperationRunner, DEV
from train_koth_gpu import Net

p = argparse.ArgumentParser()
p.add_argument("--reps", type=int, default=1)
p.add_argument("--acc", type=float, default=4.0)
p.add_argument("--plan", type=str, default="A", choices=["A", "B"])
p.add_argument("--journal", type=str, default="op_journal.jsonl")
a = p.parse_args()

# ---------------------------------------------------------------- géographie de l'opération (autour de la zone rodée)
COMPLEXE = (15000, 16000)        # l'objectif : garnison ennemie
CRETE    = (14850, 15800)        # position d'appui (overwatch)
ATTENTE  = (15150, 15750)        # point d'attente de l'élément d'assaut
LIGNE    = (15110, 15910)        # ligne de départ de l'assaut
QRF_PT   = (15000, 16450)        # d'où surgit la contre-attaque
LZ       = (15250, 15350)        # zone d'exfiltration
SPAWN_APPUI  = (14900, 15400)
SPAWN_ASSAUT = (15100, 15400)


def make_plan(variant):
    """Variante A = doctrine 'appui d'abord' (suppression avant assaut). Variante B = assaut direct (pas de phase de fixation)."""
    phases = [
        {"name": "INFILTRATION",
         "orders": {"SQ_APPUI": (CRETE, "move"), "SQ_ASSAUT": (ATTENTE, "move")},
         "done_when": ("all", [("squad_at", 0, CRETE, 70), ("squad_at", 1, ATTENTE, 70)]),
         "contingencies": [{"if": ("losses", 0.35), "reason": "pertes en approche", "goto": "EXFIL"},
                           {"if": ("steps", 60), "reason": "approche enlisée", "goto": "MISE_EN_PLACE"}]},
        {"name": "MISE_EN_PLACE",
         "orders": {"SQ_APPUI": (CRETE, "hold"), "SQ_ASSAUT": (LIGNE, "move")},
         "done_when": ("squad_at", 1, LIGNE, 60),
         "contingencies": [{"if": ("losses", 0.4), "reason": "pertes avant assaut", "goto": "EXFIL"},
                           {"if": ("steps", 40), "reason": "mise en place trop lente", "goto": "ASSAUT"}]},
        {"name": "ASSAUT",
         "orders": ({"SQ_APPUI": (COMPLEXE, "suppress"), "SQ_ASSAUT": (COMPLEXE, "assault")} if variant == "A"
                    else {"SQ_APPUI": (COMPLEXE, "assault"), "SQ_ASSAUT": (COMPLEXE, "assault")}),
         "done_when": ("all", [("zone_clear", COMPLEXE, 60), ("squad_at", 1, COMPLEXE, 60)]),
         "contingencies": [{"if": ("losses", 0.5), "reason": "assaut trop coûteux", "goto": "EXFIL"},
                           {"if": ("steps", 60), "reason": "assaut enlisé", "goto": "EXFIL"}]},
        {"name": "CONSOLIDATION",
         "orders": {"SQ_APPUI": (COMPLEXE, "hold"), "SQ_ASSAUT": (COMPLEXE, "hold")},
         "on_enter": lambda r: (r.env.spawn_qrf(QRF_PT[0], QRF_PT[1], 8, COMPLEXE),
                                r.jlog("QRF", detail="contre-attaque ennemie : 8 hommes depuis le nord"))
                                if "qrf" not in r.qrf_done and not r.qrf_done.add("qrf") else None,
         "done_when": ("any", [("enemy_dead_frac", 0.85), ("steps", 45)]),
         "contingencies": [{"if": ("losses", 0.6), "reason": "consolidation intenable", "goto": "EXFIL"}]},
        {"name": "EXFIL",
         "orders": {"SQ_APPUI": (LZ, "move"), "SQ_ASSAUT": (LZ, "move")},
         "done_when": ("any", [("all", [("squad_at", 0, LZ, 70), ("squad_at", 1, LZ, 70)]), ("steps", 50)]),
         "contingencies": []},
    ]
    return {"name": "HARMATTAN-1 (plan %s)" % variant, "phases": phases,
            # succès : l'ennemi a été brisé (≥70 % détruit), pertes contenues (≤50 %), au moins un élément à la LZ
            "success": ("all", [("enemy_dead_frac", 0.7), ("losses_max", 0.5),
                                ("any", [("squad_at", 0, LZ, 80), ("squad_at", 1, LZ, 80)])])}


net = Net(10, 4, 512, 3).to(DEV)
net.load_state_dict(torch.load("/home/younes/arma3-marl/koth_finetuned.pt", map_location=DEV)); net.eval()

results = []
for rep in range(a.reps):
    env = OpArma(squads=(("SQ_APPUI", 7), ("SQ_ASSAUT", 7)), acc=a.acc, seed=rep)
    env.spawn({"SQ_APPUI": SPAWN_APPUI, "SQ_ASSAUT": SPAWN_ASSAUT},
              garrison=[(COMPLEXE[0], COMPLEXE[1], 8, 80)])
    runner = OperationRunner(env, net, make_plan(a.plan), log_path=a.journal)
    ok = runner.run(max_steps=300)
    results.append(bool(ok))
    print("[REP %d/%d] %s | pertes %.0f%% | ennemis restants %d" %
          (rep + 1, a.reps, "SUCCÈS ✅" if ok else "ÉCHEC ❌", runner.losses() * 100, int(env.en_alive().sum())), flush=True)
print("BILAN plan %s : %d/%d succès" % (a.plan, sum(results), len(results)), flush=True)
