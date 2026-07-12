#!/usr/bin/env python3
"""diag_emergent.py — PROUVE que l'exposition emerge de la geometrie AVANT d'entrainer.
A positions fixes (escouade avancee), calcule la fraction de corps touchable pour chaque posture.
Attendu : debout > accroupi > couche (monotone, non asserte) ET forte variance selon la position
(sinon ce n'est pas geometrique). Si oui -> l'asymetrie/defilement est exploitable."""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl/replica_%s.npz"

def mk(name):
    return AssaultTerrain(num_envs=512, A=9, D=6, R_spawn=90, hit=0.25, shell_obs=True, team_obs=True,
                          replica=True, replica_path=BASE % name, max_steps=60, device=DEV, seed=7,
                          postures=True, overwatch=True, hull=False, emergent_expo=True)

@torch.no_grad()
def run(name):
    e = mk(name); e.reset(); e.hit = 0.0
    for _ in range(8):
        th = torch.atan2(-e.apx, -e.apy); a = (torch.round(th / (3.14159 / 4.0)) % 8).long(); e.step(a, auto_reset=False)
    ex = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); ey = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=DEV)
    ed2 = torch.where(e._dalive().unsqueeze(1), ex * ex + ey * ey, BIG); km = ed2.argmin(2)
    bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km)
    out = {}
    for nm, pv in (("debout", 0), ("accroupi", 1), ("couche", 2)):
        e.posture[:] = pv
        f = e._body_exposure(e.apx, e.apy, e._eye(), bx, by)
        out[nm] = (f.mean().item(), f.std().item())
    return out

print("=== EXPOSITION EMERGENTE : fraction du corps touchable par posture (moyenne ± ecart-type sur positions) ===")
for m in ["athens", "delphi", "santorini"]:
    o = run(m)
    print("  %-10s | debout %.2f(+-%.2f)  accroupi %.2f(+-%.2f)  couche %.2f(+-%.2f)" %
          (m, *o["debout"], *o["accroupi"], *o["couche"]))
print("  -> monotone (debout>accroupi>couche) ET grand ecart-type = exposition GEOMETRIQUE, pas un knob.")
