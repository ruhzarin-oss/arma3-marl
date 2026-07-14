#!/usr/bin/env python3
"""test_flank — l'affordance de flanc rend-elle les formes enveloppantes PAYANTES ?
Winrate attaquant par forme, flanc OFF vs ON. Si ligne/échelon/croissant gagnent PLUS avec ON
(vs colonne/coin serrées), le flanc récompense l'enveloppement -> le cerveau aura une raison de le choisir."""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"


@torch.no_grad()
def wr(form, flank):
    e = DuelTerrain(num_envs=256, A=12, B=8, a_form=form, flank=flank, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=0)
    obsA, obsB = e.reset(); e.a_maneuver = torch.zeros(e.N, dtype=torch.long, device=DEV)   # assaut
    w = 0.0; nep = 0; done_once = torch.zeros(e.N, dtype=torch.bool, device=DEV)
    for t in range(60):
        aA = repertoire_action(e, 0); aB = repertoire_action(e, 1)
        (obsA, obsB), _, done, info = e.step(aA, aB, auto_reset=False); dm = done.bool() & ~done_once
        if dm.any(): w += info["att_wins"][dm].float().sum().item(); nep += int(dm.sum())
        done_once |= done.bool()
    return w / max(nep, 1)


print("=== FLANC : quelle forme paie, avec/sans l'affordance ? (winrate attaquant, def=demi_cercle) ===")
for form in ["colonne", "coin", "ligne", "echelon_gauche", "croissant", "cercle"]:
    off = wr(form, 0.0); on = wr(form, 2.0)
    tag = "  <- ENVELOPPE (gagne + avec le flanc)" if on - off > 0.05 else ""
    print("  %-14s | flanc OFF=%.2f  ON=%.2f  (%+.2f)%s" % (form, off, on, on - off, tag))
print("FLANK_TEST_DONE")
