#!/usr/bin/env python3
import numpy as np, torch, os, sys
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
GS = 64; W = 200.0; P = "/tmp/verif_synth.npz"
def make(H):
    solid = np.zeros((GS, GS), bool); solid[:, 31:34] = True
    solidh = np.zeros((GS, GS), "float32"); solidh[:, 31:34] = H
    elev = np.zeros((GS, GS), "float32")
    np.savez(P, solid=solid, elev=elev, solidh=solidh, GS=np.int64(GS), W=np.float64(W),
             cx=np.float64(0), cy=np.float64(0), obj=np.zeros(2))
ok = True
def chk(label, cond):
    global ok; ok = ok and cond
    print(("  OK  " if cond else " FAIL ") + label)

print("=== REGRESSION (postures=False) ===")
make(3.0)
e0 = AssaultTerrain(num_envs=8, A=4, D=4, replica=True, replica_path=P, device="cpu", seed=0)
chk("n_actions == 10", e0.n_actions == 10)
o0 = e0.reset(); d0 = o0.shape[-1]
_ = e0.step(torch.randint(0, 10, (8, 4)))              # un step tourne sans erreur
chk("step tourne, obs stable (%d dims)" % d0, True)
ax = torch.tensor([[-100.]]); ay = torch.tensor([[0.]]); bx = torch.tensor([[100.]]); by = torch.tensor([[0.]])
l = float(e0._losc(e0.hm[:1], ax, ay, bx, by, e0.scale).reshape(-1)[0])
chk("LOS defaut = 2.5D Etape1 (mur 3m, oeil 1.7 -> bloque 0) : %.0f" % l, l == 0)

print("=== POSTURES (postures=True) ===")
make(1.0)                                              # mur BAS de 1 m
e1 = AssaultTerrain(num_envs=8, A=4, D=4, replica=True, replica_path=P, device="cpu", seed=0, postures=True)
chk("n_actions == 13", e1.n_actions == 13)
o1 = e1.reset(); d1 = o1.shape[-1]
chk("obs +3 canaux posture (%d -> %d)" % (d0, d1), d1 == d0 + 3)
stand = float(e1._losc(e1.hm[:1], ax, ay, bx, by, e1.scale, eye_a=1.7, eye_b=1.7).reshape(-1)[0])
prone = float(e1._losc(e1.hm[:1], ax, ay, bx, by, e1.scale, eye_a=0.3, eye_b=0.3).reshape(-1)[0])
chk("mur 1m : debout voit (%.0f=1) / couche cache (%.0f=0)" % (stand, prone), stand == 1 and prone == 0)
e1.posture[:] = 0
e1.step(torch.full((8, 4), 12))                        # action 12 = PRONE pour tous
chk("action 12 -> tous couches (posture set = {2})", set(e1.posture.reshape(-1).tolist()) == {2})
ey = e1._eye()
chk("_eye() reflete la posture (couche -> 0.3)", float(ey.min()) == 0.3 and float(ey.max()) == 0.3)
os.remove(P)
print("\n=== VERDICT : %s ===" % ("POSTURES CABLEES + ZERO REGRESSION" if ok else "PROBLEME"))
sys.exit(0 if ok else 1)
