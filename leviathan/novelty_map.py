#!/usr/bin/env python3
"""novelty_map.py — CARTE DES NICHES : distance comportementale entre les 5 manoeuvres du repertoire.
Montre lesquelles sont vraiment DISTINCTES (diversite tactique) vs redondantes."""
import sys, math, torch, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"; NACT = 10
MAN = {0: "assaut", 1: "defend", 2: "hunt", 3: "bounding", 4: "envelopper"}


@torch.no_grad()
def profile(man):
    e = DuelTerrain(num_envs=256, A=12, B=8, a_form="ligne", flank=0.0, replica=True,
                    replica_path=RP, max_steps=60, device=DEV, seed=0)
    e.reset(); e.a_maneuver = torch.full((e.N,), man, dtype=torch.long, device=DEV)
    ah = torch.zeros(NACT, device=DEV); ang = 0.0; spr = 0.0; steps = 0
    for _ in range(60):
        aA = repertoire_action(e, 0); aB = repertoire_action(e, 1)
        ah += torch.bincount(aA.reshape(-1).clamp(0, NACT - 1), minlength=NACT).float()
        al = e._a_alive().float(); bw = e._b_alive().float(); bws = bw.sum(1).clamp(min=1)
        ecx = (e.bx * bw).sum(1) / bws; ecy = (e.by * bw).sum(1) / bws
        dx = e.ax - ecx.unsqueeze(1); dy = e.ay - ecy.unsqueeze(1); nrm = torch.sqrt(dx * dx + dy * dy).clamp(min=1e-3)
        mx = ((dx / nrm) * al).sum(1) / al.sum(1).clamp(min=1); my = ((dy / nrm) * al).sum(1) / al.sum(1).clamp(min=1)
        ang += (1 - torch.sqrt(mx * mx + my * my)).mean().item()
        pdx = e.ax.unsqueeze(1) - e.ax.unsqueeze(2); pdy = e.ay.unsqueeze(1) - e.ay.unsqueeze(2)
        spr += (torch.sqrt(pdx * pdx + pdy * pdy).mean() / e.scale).item()
        e.step(aA, aB, auto_reset=False); steps += 1
    return np.concatenate([(ah / ah.sum()).cpu().numpy(), [ang / steps, spr / steps]])


F = {m: profile(m) for m in MAN}
for m in MAN: print("[%s] fait" % MAN[m], flush=True)
allf = np.stack([F[m] for m in MAN]); sd = np.maximum(np.abs(allf).mean(0), 1e-6)
ids = list(MAN)
print("\n=== CARTE DES NICHES : distance comportementale entre manoeuvres ===")
print("           " + "".join("%-11s" % MAN[m][:10] for m in ids))
for a in ids:
    row = "  %-9s" % MAN[a][:8]
    for b in ids:
        dd = float(np.sqrt((((F[a] - F[b]) / sd) ** 2).mean()))
        row += "%-11s" % ("-" if a == b else "%.2f" % dd)
    print(row)
print("\n  (plus haut = plus distinct = vraie niche ; ~0 = redondant)")
