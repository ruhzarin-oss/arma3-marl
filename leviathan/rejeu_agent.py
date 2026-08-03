#!/usr/bin/env python3
"""rejeu_agent — cuit le rejeu de L'AGENT AU CHAMP, pour l'oeil de Younes.

On le cuit, on ne le juge pas. Un episode du monde a carte typee, ecrit au format que
`replay_player.py` sait deja lire (celui des runs Arma) : objectif a l'origine, positions
des attaquants et des defenseurs a chaque pas.
"""
import sys
import os
import json
import glob
import math
import argparse

sys.path.insert(0, "/home/younes/arma3-marl")
LEV = "/home/younes/arma3-marl/leviathan"
sys.path.insert(0, LEV)
import torch
_av = sys.argv[:]; sys.argv = [sys.argv[0]]      # lire_carte parse a l'import
import lire_carte as LC
sys.argv = _av
from train_koth_gpu import Net

ap = argparse.ArgumentParser()
ap.add_argument("--pt", default=None)
ap.add_argument("--device", default="cuda:0")
ap.add_argument("--out", default="rejeu3_agent_champ.json")
a = ap.parse_args()
DEV = a.device
LC.KC = 9
COURBE = LEV + "/courbe_toucher_juge.json"


def monde(n, seed):
    return LC.MondeCarte(num_envs=n, A=4, D=8, seed=seed, device=DEV, max_steps=60,
                         R_spawn=170.0, postures=True, hull=True, def_line=True,
                         def_arc=math.pi / 3, def_rand=True, secure_task=True,
                         secure_only=True, courbe=COURBE, tir_par_pas=1.15,
                         sec_par_pas=3.28, degat_par_impact=0.233, arc_obs=True,
                         champ_risque=False, kc=9, empan=90.0)


def main():
    cands = ([a.pt] if a.pt else []) + sorted(glob.glob(LEV + "/carte_dense_g*.pt")) \
        + sorted(glob.glob(LEV + "/carte_conv_g*.pt"))
    cands = [c for c in cands if c and os.path.exists(c)]
    if not cands:
        print("aucun .pt disponible : rejeu 3 non cuisinable")
        return 1
    e = monde(64, 4242)
    obs = e.reset()
    O = obs.shape[-1]
    net = None
    for p in cands:
        try:
            n = Net(O, e.n_actions).to(DEV)
            n.load_state_dict(torch.load(p, map_location=DEV))
            n.eval()
            net = n
            nom = os.path.basename(p)
            break
        except Exception:
            continue
    if net is None:
        print("aucun .pt compatible (le bras conv a une autre architecture)")
        return 1
    print("rejeu de %s" % nom)

    frames = []
    with torch.no_grad():
        for t in range(60):
            act = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
            w = [[round(float(e.apx[0, i]), 1), round(float(e.apy[0, i]), 1),
                  int(bool(e._aalive()[0, i])), 0] for i in range(e.A)]
            d = [[round(float(e.dpx[0, j]), 1), round(float(e.dpy[0, j]), 1),
                  int(bool(e._dalive()[0, j]))] for j in range(e.D)]
            fw = [int(act[0, i] == 9) for i in range(e.A)]
            frames.append({"t": t, "west": w, "east": d, "firew": fw})
            obs, _, done, info = e.step(act, auto_reset=False)
            if bool(done[0]):
                break
    out = {"fob": [0, 0], "A": e.A, "B": e.D, "mode": "agent_champ",
           "metrics": {"mode": "agent_champ", "nag": e.A, "source": nom,
                       "steps": len(frames)},
           "frames": frames}
    json.dump(out, open(LEV + "/" + a.out, "w"))
    print("-> leviathan/%s  (%d pas)" % (a.out, len(frames)))
    print("REJEU3_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
