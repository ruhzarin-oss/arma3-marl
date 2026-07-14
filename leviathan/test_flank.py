#!/usr/bin/env python3
"""test_flank — la manœuvre d'ENVELOPPEMENT + l'affordance de flanc paient-elles ENSEMBLE ?
Compare assaut frontal vs envelopper, flanc OFF vs ON. Si envelopper+flanc gagne nettement plus,
la co-conception marche -> le cerveau aura une raison de déborder contre une défense frontale."""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"


@torch.no_grad()
def wr(maneuver, flank, form="ligne"):
    e = DuelTerrain(num_envs=256, A=12, B=8, a_form=form, flank=flank, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=0)
    obsA, obsB = e.reset(); e.a_maneuver = torch.full((e.N,), maneuver, dtype=torch.long, device=DEV)   # manœuvre attaquant fixée
    w = 0.0; nep = 0; done_once = torch.zeros(e.N, dtype=torch.bool, device=DEV)
    for t in range(60):
        aA = repertoire_action(e, 0); aB = repertoire_action(e, 1)
        (obsA, obsB), _, done, info = e.step(aA, aB, auto_reset=False); dm = done.bool() & ~done_once
        if dm.any(): w += info["att_wins"][dm].float().sum().item(); nep += int(dm.sum())
        done_once |= done.bool()
    return w / max(nep, 1)


MAN = {0: "assaut (frontal)", 4: "ENVELOPPER"}
print("=== FLANC × MANŒUVRE : le débordement paie-t-il quand le flanc est actif ? (winrate attaquant) ===")
for man in [0, 4]:
    off = wr(man, 0.0); on = wr(man, 2.0)
    tag = "  <- le flanc PAIE" if (man == 4 and on - off > 0.05) else ""
    print("  %-18s | flanc OFF=%.2f  ON=%.2f  (%+.2f)%s" % (MAN[man], off, on, on - off, tag))
print("FLANK_TEST_DONE")
