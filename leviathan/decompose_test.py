#!/usr/bin/env python3
"""decompose_test — le LEVIER FORT de la Phase 2 : décomposer l'escouade (fixe / flanc / rush simultanés).
Hypothèse : le DÉCOMPOSÉ bat le contre-débordeur (qui vide l'objectif) en s'y glissant, MAIS perd
contre le turtle (qui ne bouge pas) -> vraie NON-TRANSITIVITÉ (l'attaquant doit MÉLANGER).
On imprime les MARGES pour ne pas confondre un vrai contre avec du bruit (0.02)."""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"
M = {"assaut": 0, "defend": 1, "hunt": 2, "bound": 3, "envelop": 4, "decomp": 5}


@torch.no_grad()
def duel(a_man, d_man, a_depth=55.0, a_split=0.5, a_fix=0.40, a_rush=0.30, aform="coin", dform="demi_cercle", seeds=4):
    wins = 0.0; took = 0.0; ne = 0
    for sd in range(seeds):
        e = DuelTerrain(num_envs=256, A=12, B=8, a_form=aform, b_form=dform, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)
        e.reset()
        e.a_maneuver = torch.full((e.N,), a_man, dtype=torch.long, device=DEV)
        e.b_maneuver = torch.full((e.N,), d_man, dtype=torch.long, device=DEV)
        e.set_envelop(a_depth=a_depth, a_split=a_split); e.set_decompose(a_fix=a_fix, a_rush=a_rush)
        done_once = torch.zeros(e.N, dtype=torch.bool, device=DEV)
        for t in range(60):
            aA = repertoire_action(e, 0); aB = repertoire_action(e, 1)
            _, _, done, info = e.step(aA, aB, auto_reset=False); d2 = done.bool() & ~done_once
            if d2.any():
                aw = info["att_wins"][d2]
                wins += aw.float().sum().item(); took += (info["took"][d2] & aw).float().sum().item(); ne += int(d2.sum())
            done_once |= done.bool()
    return wins / max(ne, 1), took / max(ne, 1)


# (nom, manœuvre, depth, split, fix, rush)
VAR = [
    ("rush",          M["assaut"],  0.0, 0.0,  0.0, 0.0),
    ("env d20",       M["envelop"], 20.0, 0.50, 0.0, 0.0),
    ("decomp .4/.3",  M["decomp"],  20.0, 0.5,  0.40, 0.30),
    ("decomp .3/.4",  M["decomp"],  20.0, 0.5,  0.30, 0.40),
    ("decomp .5/.2",  M["decomp"],  20.0, 0.5,  0.50, 0.20),
    ("decomp .25/.5", M["decomp"],  20.0, 0.5,  0.25, 0.50),   # gros rush
]
DEF = ["defend", "envelop", "bound"]

print("=== DÉCOMPOSITION : winrate ATTAQUANT (ligne = attaque, colonne = défense) — 4 seeds ===", flush=True)
print("               " + "".join("%-9s" % d for d in DEF), flush=True)
WR = {}; TK = {}
for name, am, dep, spl, fx, rsh in VAR:
    row = []
    for dname in DEF:
        w, t = duel(am, M[dname], a_depth=dep, a_split=spl, a_fix=fx, a_rush=rsh)
        row.append(w); WR[(name, dname)] = w; TK[(name, dname)] = t
    print("%-14s " % name + "".join("%-9.2f" % r for r in row), flush=True)

print("\n=== victoires par OBJECTIF SÉCURISÉ (le rush se glisse-t-il ?) ===", flush=True)
print("               " + "".join("%-9s" % d for d in DEF), flush=True)
for name, *_ in VAR:
    print("%-14s " % name + "".join("%-9.2f" % TK[(name, d)] for d in DEF), flush=True)

print("\n=== VERDICT (avec marge sur le 2e) ===", flush=True)
best = {}
for dname in DEF:
    col = sorted(((name, WR[(name, dname)]) for name, *_ in VAR), key=lambda x: -x[1])
    best[dname] = col[0]; margin = col[0][1] - col[1][1]
    print("  contre %-9s -> %-14s (%.2f)  | marge/2e = %+.2f (%s)" % (dname, col[0][0], col[0][1], margin, "SOLIDE" if margin >= 0.08 else "bruit"), flush=True)
uniq = set(b[0] for b in best.values())
solid = all((best[d][1] - sorted((WR[(n, d)] for n, *_ in VAR))[-2]) >= 0.08 for d in DEF)
if len(uniq) >= 2 and solid:
    print("  >>> NON-TRANSITIVITÉ RÉELLE : réponses distinctes ET marges solides -> l'espace s'ouvre VRAIMENT.", flush=True)
elif len(uniq) >= 2:
    print("  >>> réponses distinctes mais marges FAIBLES -> non-transitivité fragile / bruit.", flush=True)
else:
    print("  >>> une seule attaque domine (%s) -> espace ENCORE pauvre." % list(uniq)[0], flush=True)
print("DECOMP_DONE", flush=True)
