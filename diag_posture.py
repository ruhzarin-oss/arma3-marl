#!/usr/bin/env python3
"""diag_posture.py — le bas couvert sert-il VRAIMENT la ou l'agent se bat ?
On amene l'escouade au contact (heuristique : avancer vers le centre), et a CHAQUE position
on compare, en contrefactuel, l'exposition DEBOUT (oeil 1.7) vs COUCHE (oeil 0.3) face aux
defenseurs vivants a portee. Reponse = % des expositions 'debout' qui seraient EVITEES en se couchant."""
import sys, math, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl/replica_%s.npz"

@torch.no_grad()
def diag(name, n=512, steps=55):
    e = AssaultTerrain(num_envs=n, A=9, D=4, R_spawn=80, relief=40.0, hit=0.10, shell_obs=True, team_obs=True,
                       replica=True, replica_path=BASE % name, max_steps=90, device=DEV, seed=1, postures=True)
    e.reset()
    exp_s = exp_p = hidden = pairs = 0.0
    for t in range(steps):
        al = e._aalive()
        for di in range(e.D):
            bx = e.dpx[:, di:di + 1].expand(n, e.A); by = e.dpy[:, di:di + 1].expand(n, e.A)
            dist = torch.sqrt((e.apx - e.dpx[:, di:di + 1]) ** 2 + (e.apy - e.dpy[:, di:di + 1]) ** 2)
            inr = (dist < e.fire_range) & e._dalive()[:, di:di + 1] & al          # defenseur vivant a portee, attaquant vivant
            los_s = e._losc(e.hm, e.apx, e.apy, bx, by, e.scale, eye_a=1.7, eye_b=1.7) > 0.5   # debout
            los_p = e._losc(e.hm, e.apx, e.apy, bx, by, e.scale, eye_a=0.3, eye_b=1.7) > 0.5   # couche
            es = los_s & inr; ep = los_p & inr
            exp_s += es.float().sum().item(); exp_p += ep.float().sum().item()
            hidden += (es & ~ep).float().sum().item(); pairs += inr.float().sum().item()
        # heuristique : cap vers le centre (0,0) pour amener au contact
        th = torch.atan2(-e.apx, -e.apy)                                          # angle vers le centre
        act = (torch.round(th / (math.pi / 4)) % 8).long().clamp(0, 7)
        e.step(act, auto_reset=True)
    print("  %-10s : expo debout=%.3f  couche=%.3f  |  %.0f%% des expositions debout EVITEES en se couchant  (paires=%d)"
          % (name, exp_s / max(pairs, 1), exp_p / max(pairs, 1), 100 * hidden / max(exp_s, 1), int(pairs)))

print("=== DIAG : se coucher casse-t-il l'exposition la ou l'agent se bat ? ===")
for m in ["denver", "chicago", "paris", "madrid", "athens", "delphi", "santorini"]:
    diag(m)
