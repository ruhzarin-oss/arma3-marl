#!/usr/bin/env python3
# Smoke-test LOS 2.5D : prouve que la hauteur du bati (solidh) et la hauteur d'oeil comptent.
# Scene synthetique : un mur vertical au centre, hauteur H variable. Rayon qui le traverse.
import numpy as np, torch, os, sys
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain

GS = 64; W = 200.0; P = "/tmp/smoke_synth.npz"

def make(H):
    solid = np.zeros((GS, GS), bool);        solid[:, 31:34] = True      # mur vertical au centre
    solidh = np.zeros((GS, GS), "float32");  solidh[:, 31:34] = H        # de hauteur H
    elev = np.zeros((GS, GS), "float32")                                  # sol plat
    np.savez(P, solid=solid, elev=elev, solidh=solidh,
             GS=np.int64(GS), W=np.float64(W), cx=np.float64(0), cy=np.float64(0), obj=np.zeros(2))

def los(H, eye):
    make(H)
    env = AssaultTerrain(num_envs=1, A=4, replica=True, replica_path=P, device="cpu", seed=0)
    ax = torch.tensor([[-100.]]); ay = torch.tensor([[0.]])
    bx = torch.tensor([[100.]]);  by = torch.tensor([[0.]])              # rayon qui traverse le mur
    v = env._losc(env.hm, ax, ay, bx, by, env.scale, eye=eye)
    return float(v.reshape(-1)[0])

print("=== SMOKE-TEST LOS 2.5D (1=voit, 0=bloque) ===")
a  = los(1.0, 1.7)
b  = los(30.0, 1.7)
c1 = los(3.0, 1.7)
c2 = los(3.0, 5.0)
print("(a)  mur bas 1m,  oeil 1.7m        -> %.0f  [attendu 1: passe par-dessus]   %s" % (a,  "OK" if a  == 1 else "FAIL"))
print("(b)  tour 30m,    oeil 1.7m        -> %.0f  [attendu 0: bloque]             %s" % (b,  "OK" if b  == 0 else "FAIL"))
print("(c1) mur 3m,      oeil 1.7m (sol)  -> %.0f  [attendu 0: bloque]             %s" % (c1, "OK" if c1 == 0 else "FAIL"))
print("(c2) mur 3m,      oeil 5.0m (toit) -> %.0f  [attendu 1: voit par-dessus]    %s" % (c2, "OK" if c2 == 1 else "FAIL"))
ok = (a == 1 and b == 0 and c1 == 0 and c2 == 1)
print("\n=== VERDICT : %s ===" % ("2.5D ACTIF ET CORRECT (mur<->tour distingues, hauteur d'oeil active)" if ok else "PROBLEME — a revoir"))
os.remove(P)
sys.exit(0 if ok else 1)
