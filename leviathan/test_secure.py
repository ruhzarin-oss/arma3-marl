#!/usr/bin/env python3
"""test_secure.py — valide la TÂCHE SÉCURISER dans assault_terrain + baselines sandbox (téméraire/timide).
Doit reproduire Arma : le téméraire (avance pure) prend-il le FOB ? à quel prix ? le timide (se fixe au feu) cale-t-il ?"""
import sys, math, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from assault_terrain import AssaultTerrain
DEV = "cuda:0"


def reckless(e):   # avance pure vers l'objectif
    return (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4)) % 8).long()


def timid(e):      # avance, mais se fixe au feu (SUPPRESS) dès qu'il a une cible en LOS+portée
    cap = reckless(e)
    dx = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); dy = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=DEV)
    d2 = torch.where(e._dalive().unsqueeze(1), dx * dx + dy * dy, BIG)
    km = d2.argmin(2); bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km); nd = d2.min(2).values.sqrt()
    los = e._losc(e.hm, e.apx, e.apy, bx, by, e.scale)
    fire = (los > 0.5) & (nd < e.fire_range)
    return torch.where(fire, torch.full_like(cap, 9), cap)


@torch.no_grad()
def rollout(policy, hit=0.18, supp_kill=1.0, seed=1):
    e = AssaultTerrain(num_envs=1024, A=18, D=12, R_spawn=140.0, secure_r=25.0, max_steps=55, hit=hit,
                       secure_task=True, secure_only=True, supp_kill=supp_kill, approach_w=0.5, device=DEV, seed=seed)
    e.reset(); done_once = torch.zeros(e.N, dtype=torch.bool, device=DEV)
    took = win = loss = mind = nep = 0.0
    minr = torch.full((e.N,), 999.0, device=DEV)
    for t in range(55):
        act = policy(e)
        _, _, done, info = e.step(act, auto_reset=False)
        minr = torch.minimum(minr, torch.sqrt(e.apx ** 2 + e.apy ** 2).min(1).values)
        d2 = done.bool() & ~done_once
        if d2.any():
            took += info["took"][d2].float().sum().item(); win += info["win"][d2].float().sum().item()
            loss += (info["losses"][d2] * e.A).sum().item(); mind += minr[d2].sum().item(); nep += int(d2.sum())
        done_once |= done.bool()
    n = max(nep, 1)
    return took / n, win / n, loss / n, mind / n


print("=== RECALIBRATION Arma : secure_only=True, hit=0.18, balayage de supp_kill (efficacité du feu) ===", flush=True)
print("  cible = le feu ne doit plus payer (timide ≈ téméraire), comme sur Arma où tirer ne délogem pas les retranchés", flush=True)
for sk in [1.0, 0.5, 0.25, 0.1, 0.0]:
    tk_r, _, ls_r, md_r = rollout(reckless, supp_kill=sk)
    tk_t, _, ls_t, md_t = rollout(timid, supp_kill=sk)
    print("  supp_kill=%.2f | TÉMÉRAIRE pris %2.0f%% pertes %4.1f dmin %2.0fm  |  TIMIDE pris %2.0f%% pertes %4.1f dmin %2.0fm" % (
        sk, 100 * tk_r, ls_r, md_r, 100 * tk_t, ls_t, md_t), flush=True)
print("SECURE_DONE", flush=True)
