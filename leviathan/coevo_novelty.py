#!/usr/bin/env python3
"""coevo_novelty.py — course aux armements sur le REPERTOIRE + traque de NOUVEAUTE (a part, ne touche
pas coevo_compose). Meilleure-reponse alternee sur les 5 manoeuvres ; a chaque round on mesure la
distance comportementale au frontal de depart. Montre l'arms race marcher vers des tactiques distinctes."""
import sys, math, torch, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"; NACT = 10
MAN = {0: "assaut", 1: "defend", 2: "hunt", 3: "bounding", 4: "envelopper"}; IDS = list(MAN)


@torch.no_grad()
def profile(man):
    e = DuelTerrain(num_envs=256, A=12, B=8, a_form="ligne", flank=0.0, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=1)
    e.reset(); e.a_maneuver = torch.full((e.N,), man, dtype=torch.long, device=DEV)
    ah = torch.zeros(NACT, device=DEV); ang = 0.0; steps = 0
    for _ in range(60):
        aA = repertoire_action(e, 0); aB = repertoire_action(e, 1)
        ah += torch.bincount(aA.reshape(-1).clamp(0, NACT - 1), minlength=NACT).float()
        al = e._a_alive().float(); bw = e._b_alive().float(); bws = bw.sum(1).clamp(min=1)
        ecx = (e.bx * bw).sum(1) / bws; ecy = (e.by * bw).sum(1) / bws
        dx = e.ax - ecx.unsqueeze(1); dy = e.ay - ecy.unsqueeze(1); nrm = torch.sqrt(dx * dx + dy * dy).clamp(min=1e-3)
        mx = ((dx / nrm) * al).sum(1) / al.sum(1).clamp(min=1); my = ((dy / nrm) * al).sum(1) / al.sum(1).clamp(min=1)
        ang += (1 - torch.sqrt(mx * mx + my * my)).mean().item(); e.step(aA, aB, auto_reset=False); steps += 1
    return np.concatenate([(ah / ah.sum()).cpu().numpy(), [ang / steps]])


@torch.no_grad()
def winrate(att, dfd):
    e = DuelTerrain(num_envs=256, A=12, B=8, a_form="ligne", flank=0.0, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=0)
    e.reset(); e.a_maneuver = torch.full((e.N,), att, dtype=torch.long, device=DEV); e.b_maneuver = torch.full((e.N,), dfd, dtype=torch.long, device=DEV)
    w = 0.0; nep = 0; done = torch.zeros(e.N, dtype=torch.bool, device=DEV)
    for _ in range(60):
        (o1, o2), _, dn, info = e.step(repertoire_action(e, 0), repertoire_action(e, 1), auto_reset=False)
        m = dn.bool() & ~done
        if m.any(): w += info["att_wins"][m].float().sum().item(); nep += int(m.sum())
        done |= dn.bool()
    return w / max(nep, 1)


print("Matrice de winrate (att x def)...", flush=True)
W = np.array([[winrate(a, b) for b in IDS] for a in IDS])
F = {m: profile(m) for m in IDS}
sd = np.maximum(np.abs(np.stack([F[m] for m in IDS])).mean(0), 1e-6)
def nov(a, b): return float(np.sqrt((((F[a] - F[b]) / sd) ** 2).mean()))

print("\n=== COURSE AUX ARMEMENTS (meilleure-reponse alternee) ===")
att = 0; start = 0                                                        # depart = frontal
print("  round 0 : ATT=%-10s (depart)" % MAN[att])
for r in range(1, 7):
    dfd = int(np.argmin(W[att, :]))                                      # def minimise le winrate att
    att2 = int(np.argmax(W[:, dfd]))                                     # att maximise vs ce def
    print("  round %d : def repond %-10s -> att repond %-10s | winrate %.2f | NOUVEAUTE vs depart %.2f"
          % (r, MAN[dfd], MAN[att2], W[att2, dfd], nov(att2, start)), flush=True)
    if att2 == att: print("    -> equilibre atteint."); break
    att = att2
