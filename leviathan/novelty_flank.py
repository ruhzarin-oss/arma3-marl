#!/usr/bin/env python3
"""novelty_flank.py — pointe le DÉTECTEUR DE NOUVEAUTÉ sur l'ENVELOPPEMENT.
Compare le COMPORTEMENT frontal (man=0) vs enveloppement (man=4) dans DuelTerrain.
Signature clé = dispersion angulaire de l'attaque (1 angle = frontal, 2 angles = enveloppement)."""
import sys, math, torch, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"; NACT = 10


@torch.no_grad()
def profile(man, name):
    e = DuelTerrain(num_envs=256, A=12, B=8, a_form="ligne", flank=0.0, replica=True,
                    replica_path=RP, max_steps=60, device=DEV, seed=0)
    e.reset(); e.a_maneuver = torch.full((e.N,), man, dtype=torch.long, device=DEV)
    ah = torch.zeros(NACT, device=DEV); spread = 0.0; ang = 0.0; steps = 0; ang_n = 0
    for _ in range(60):
        aA = repertoire_action(e, 0); aB = repertoire_action(e, 1)
        ah += torch.bincount(aA.reshape(-1).clamp(0, NACT - 1), minlength=NACT).float()
        al = e._a_alive().float(); bw = e._b_alive().float(); bws = bw.sum(1).clamp(min=1)
        ecx = (e.bx * bw).sum(1) / bws; ecy = (e.by * bw).sum(1) / bws            # centroide ennemi
        dx = e.ax - ecx.unsqueeze(1); dy = e.ay - ecy.unsqueeze(1); nrm = torch.sqrt(dx * dx + dy * dy).clamp(min=1e-3)
        ux = (dx / nrm); uy = (dy / nrm)                                          # direction attaquant<-ennemi
        _nv = al.sum(1)
        mx = (ux * al).sum(1) / _nv.clamp(min=1); my = (uy * al).sum(1) / _nv.clamp(min=1)
        R = torch.sqrt(mx * mx + my * my)                                         # concentration (1=meme cote)
        # REVUE 17/08 : escouade ANEANTIE -> mx=my=0 -> R=0 -> (1-R)=1, le MAXIMUM, c est
        # a dire exactement la signature lue comme  enveloppement par deux cotes . On
        # n agrege que les env ou il reste au moins DEUX hommes pour former un angle.
        _ok = _nv >= 2
        if bool(_ok.any()):
            ang += float((1 - R)[_ok].mean()); ang_n += 1                          # dispersion angulaire (haut = 2 cotes)
        pdx = e.ax.unsqueeze(1) - e.ax.unsqueeze(2); pdy = e.ay.unsqueeze(1) - e.ay.unsqueeze(2)
        spread += (torch.sqrt(pdx * pdx + pdy * pdy).mean() / e.scale).item()
        e.step(aA, aB, auto_reset=False); steps += 1
    af = (ah / ah.sum()).cpu().numpy()
    feats = np.concatenate([af, [ang / max(ang_n, 1), spread / steps]])
    print("[%s] fait" % name, flush=True)
    return feats


names = ["a%d" % i for i in range(NACT)] + ["dispersion_angulaire", "etalement"]
fF = profile(0, "frontal (man=0)")
fE = profile(4, "ENVELOPPEMENT (man=4)")
sd = np.maximum(np.abs(fF), 1e-6)
dist = float(np.sqrt((((fE - fF) / sd) ** 2).mean()))
delta = fE - fF; order = np.argsort(-np.abs(delta / sd))
print("\n=== DISTANCE COMPORTEMENTALE  frontal -> ENVELOPPEMENT : %.3f ===" % dist)
print("  CE QUI CHANGE (= la manoeuvre inventee, mesuree) :")
for i in order[:6]:
    print("    %-20s : frontal %.3f -> envelop %.3f   (%+.3f)" % (names[i], fF[i], fE[i], delta[i]))
