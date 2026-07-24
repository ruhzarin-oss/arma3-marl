#!/usr/bin/env python3
"""envelop_record — CAMÉRA TOP-DOWN : enregistre le débordement (positions par tick) -> JSON pour le replay web.
Sandbox d'abord (données que j'ai déjà) ; le MÊME format sera produit par envelop_arma.py côté Arma.
Sort: leviathan/envelop_replay.json = {fob, A, B, frames:[{t, west:[[x,y,alive,deb],..], east:[[x,y,alive],..], firew:[0/1,..]}]}"""
import sys, json, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"
OUT = "/home/younes/arma3-marl/leviathan/envelop_replay.json"

e = DuelTerrain(num_envs=64, A=12, B=8, a_form="coin", b_form="demi_cercle", replica=True, replica_path=RP, max_steps=70, device=DEV, seed=1)
e.reset()
e.a_maneuver = torch.full((e.N,), 4, dtype=torch.long, device=DEV)   # ATTAQUANT = débordement
e.b_maneuver = torch.full((e.N,), 1, dtype=torch.long, device=DEV)   # DÉFENSEUR = tient (defend)
e.set_envelop(a_depth=20.0, a_split=0.5)                             # peu profond (le finding), 50% débordeurs
EN = 0; split = 0.5
deb = [1 if (i / max(e.A - 1, 1)) < split else 0 for i in range(e.A)]

frames = []
for t in range(70):
    aA = repertoire_action(e, 0); aB = repertoire_action(e, 1)
    west = [[round(e.ax[EN, i].item(), 1), round(e.ay[EN, i].item(), 1), int(e.admg[EN, i].item() < 0.7), deb[i]] for i in range(e.A)]
    east = [[round(e.bx[EN, j].item(), 1), round(e.by[EN, j].item(), 1), int(e.bdmg[EN, j].item() < 0.7)] for j in range(e.B)]
    firew = [int(aA[EN, i].item() == 9) for i in range(e.A)]
    frames.append({"t": t, "west": west, "east": east, "firew": firew})
    _, _, done, info = e.step(aA, aB, auto_reset=False)
    if bool(done[EN].item()):
        frames.append({"t": t + 1, "west": [[round(e.ax[EN, i].item(), 1), round(e.ay[EN, i].item(), 1), int(e.admg[EN, i].item() < 0.7), deb[i]] for i in range(e.A)],
                       "east": [[round(e.bx[EN, j].item(), 1), round(e.by[EN, j].item(), 1), int(e.bdmg[EN, j].item() < 0.7)] for j in range(e.B)], "firew": [0] * e.A})
        break

json.dump({"fob": [0.0, 0.0], "A": e.A, "B": e.B, "frames": frames}, open(OUT, "w"))
na = sum(f["west"][i][2] for i in range(e.A) for f in [frames[-1]]); nb = sum(f["east"][j][2] for j in range(e.B) for f in [frames[-1]])
print("frames=%d écrites -> %s | fin: WEST vivants=%d/%d, EAST vivants=%d/%d" % (len(frames), OUT, na, e.A, nb, e.B))
