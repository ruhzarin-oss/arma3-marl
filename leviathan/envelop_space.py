#!/usr/bin/env python3
"""envelop_space — Phase 2 : le débordement devient un CONTINUUM (profondeur × ratio débordeurs).
Question : une seule variante domine-t-elle encore TOUTES les défenses (espace pauvre),
ou la meilleure attaque DÉPEND-elle de la défense (début de non-transitivité) ?
On regarde aussi si les variantes profondes TUENT sans SÉCURISER (arbitrage de l'horloge)."""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"
M = {"assaut": 0, "defend": 1, "hunt": 2, "bound": 3, "envelop": 4}


@torch.no_grad()
def duel(a_man, d_man, a_depth=55.0, a_split=0.5, aform="coin", dform="demi_cercle", seeds=3):
    wins = 0.0; took = 0.0; ne = 0
    for sd in range(seeds):
        e = DuelTerrain(num_envs=256, A=12, B=8, a_form=aform, b_form=dform, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)
        e.reset()
        e.a_maneuver = torch.full((e.N,), a_man, dtype=torch.long, device=DEV)
        e.b_maneuver = torch.full((e.N,), d_man, dtype=torch.long, device=DEV)
        e.set_envelop(a_depth=a_depth, a_split=a_split)
        done_once = torch.zeros(e.N, dtype=torch.bool, device=DEV)
        for t in range(60):
            aA = repertoire_action(e, 0); aB = repertoire_action(e, 1)
            _, _, done, info = e.step(aA, aB, auto_reset=False); d2 = done.bool() & ~done_once
            if d2.any():
                aw = info["att_wins"][d2]
                wins += aw.float().sum().item()
                took += (info["took"][d2] & aw).float().sum().item()
                ne += int(d2.sum())
            done_once |= done.bool()
    return wins / max(ne, 1), took / max(ne, 1)


# variantes ATTAQUANT (nom, manœuvre, profondeur, ratio-débordeurs)
VAR = [
    ("rush(assaut)", M["assaut"], 0.0, 0.0),
    ("env d20 s.50", M["envelop"], 20.0, 0.50),
    ("env d55 s.50", M["envelop"], 55.0, 0.50),
    ("env d90 s.50", M["envelop"], 90.0, 0.50),
    ("env d90 s.25", M["envelop"], 90.0, 0.25),   # profond, GROS fixeur frontal
    ("env d90 s.75", M["envelop"], 90.0, 0.75),   # profond, GROS débordement
    ("env d130 s.50", M["envelop"], 130.0, 0.50), # très profond (brûle l'horloge ?)
]
DEF = ["defend", "envelop", "bound"]   # tenir / contre-déborder / feu-et-mouvement

print("=== ESPACE DU DÉBORDEMENT : winrate ATTAQUANT (ligne = variante att, colonne = défense) ===", flush=True)
print("               " + "".join("%-9s" % d for d in DEF), flush=True)
WR = {}; TK = {}
for name, am, dep, spl in VAR:
    row = []; rowt = []
    for dname in DEF:
        w, t = duel(am, M[dname], a_depth=dep, a_split=spl)
        row.append(w); rowt.append(t); WR[(name, dname)] = w; TK[(name, dname)] = t
    print("%-14s " % name + "".join("%-9.2f" % r for r in row), flush=True)

print("\n=== part des victoires par OBJECTIF SÉCURISÉ (vs par élimination) — l'arbitrage de l'horloge ===", flush=True)
print("               " + "".join("%-9s" % d for d in DEF), flush=True)
for name, am, dep, spl in VAR:
    print("%-14s " % name + "".join("%-9.2f" % TK[(name, d)] for d in DEF), flush=True)

# non-transitivité : la MEILLEURE variante change-t-elle selon la défense ?
print("\n=== VERDICT ===", flush=True)
best = {}
for dname in DEF:
    col = [(name, WR[(name, dname)]) for name, *_ in VAR]
    bn = max(col, key=lambda x: x[1])
    best[dname] = bn
    print("  contre %-9s -> meilleure attaque = %-14s (%.2f)" % (dname, bn[0], bn[1]), flush=True)
uniq = set(b[0] for b in best.values())
if len(uniq) == 1:
    print("  >>> UNE SEULE variante domine toutes les défenses (%s) -> espace ENCORE PAUVRE." % list(uniq)[0], flush=True)
else:
    print("  >>> la meilleure attaque DÉPEND de la défense (%d réponses distinctes) -> NON-TRANSITIVITÉ, l'espace s'ouvre." % len(uniq), flush=True)
print("ENVSPACE_DONE", flush=True)
