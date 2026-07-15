#!/usr/bin/env python3
"""formation_fidelity — le cerveau EXÉCUTE-T-IL les formes ? On mesure la distance de chaque soldat
à SON slot au fil du rollout. Converge (petit) = il tient la forme ; reste grand = il blob."""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from train_koth_gpu import Net
DEV = "cuda:0"
RP = "/home/younes/arma3-marl/replica.npz"
net = Net(17, 13, 512, 3).to(DEV)
net.load_state_dict(torch.load("/home/younes/arma3-marl/shamal_arma_win.pt", map_location=DEV)); net.eval()
print("=== FIDÉLITÉ DE FORMATION : distance moyenne soldat->slot (m) ===")
for form in ["coin", "ligne", "echelon_gauche", "demi_cercle", "cercle", "carre"]:
    e = DuelTerrain(num_envs=256, A=12, B=8, R_spawn=120.0, a_form=form,
                    replica=True, replica_path=RP, max_steps=60, device=DEV, seed=0)
    obsA, obsB = e.reset(); ds = []
    z = torch.zeros(e.N, device=DEV)
    with torch.no_grad():
        for t in range(60):
            sx, sy = e._side_slots(e.ax, e.ay, e._a_alive(), e.a_form_idx, e._tmplA, z, z, e.form_forward)
            al = e._a_alive().float()
            d = torch.sqrt((e.ax - sx) ** 2 + (e.ay - sy) ** 2)
            ds.append(((d * al).sum() / al.sum().clamp(min=1)).item())
            aA = net.a_logits(obsA).argmax(-1); aB = net.a_logits(obsB).argmax(-1)
            (obsA, obsB), _, done, info = e.step(aA, aB)
    fin = sum(ds[-10:]) / 10
    verdict = "TIENT la forme" if fin < 8 else ("approximatif" if fin < 16 else "BLOB (ne tient pas)")
    print("  %-14s | début=%4.1f  fin=%4.1f  min=%4.1f  -> %s" % (form, ds[0], fin, min(ds), verdict))
print("FIDELITY_DONE")
