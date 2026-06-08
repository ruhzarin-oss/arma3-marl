"""Instrumentation : POURQUOI les parties finissent en NUL en mode manœuvre ? Classe chaque fin de partie :
CAPTURE (victoire) / ANÉANTISSEMENT n_alive<=1 (nul, attrition off) / TIMEOUT-avec-contrôle (victoire) / TIMEOUT-sans-contrôle (nul).
auto_reset=False pour lire l'état à la décision, puis reset manuel."""
import torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net

DEV = "cuda:0"; N = 4096; T = 400
env = KothGPU(num_envs=N, device=DEV, attrition_win=False, timeout_decisive=True, seed=0)
net = Net(10, 4, 512, 3).to(DEV)
net.load_state_dict(torch.load("league_maneuver_learner.pt", map_location=DEV)); net.eval()

ot = list(env.reset()); cap = wipe = to_ctrl = to_noctrl = 0
with torch.no_grad():
    for t in range(T):
        acts = [Categorical(logits=net.a_logits(ot[c])).sample() for c in range(env.C)]
        ot2, _, done, info = env.step(acts, auto_reset=False)
        dm = done.bool()
        if dm.any():
            idx = dm.nonzero(as_tuple=True)[0]
            secured = info["secured"][idx]
            nalive = torch.stack([env._alive(c).any(1) for c in range(env.C)], 0)[:, idx].sum(0)
            ct = torch.stack([env.ctrl_time[c] for c in range(env.C)], 0)[:, idx]; mx = ct.max(0).values
            cap += int(secured.sum())
            rest = ~secured
            wipe += int((rest & (nalive <= 1)).sum())
            tor = rest & ~(nalive <= 1)
            to_ctrl += int((tor & (mx > 0)).sum())
            to_noctrl += int((tor & (mx == 0)).sum())
            env._reset_rows(idx)
        ot = list(ot2)

tot = cap + wipe + to_ctrl + to_noctrl
print("=== CAUSES DE FIN DE PARTIE (mode manœuvre + timeout décisif) ===")
for nm, v in (("CAPTURE (victoire)", cap), ("ANÉANTISSEMENT n_alive<=1 (NUL)", wipe),
              ("TIMEOUT avec contrôle (victoire)", to_ctrl), ("TIMEOUT sans contrôle (NUL)", to_noctrl)):
    print("  %-34s : %5d  (%.0f%%)" % (nm, v, 100 * v / max(1, tot)))
print("  total parties:", tot)
print("\nANÉANTISSEMENT domine -> baisser hit (létalité). TIMEOUT-sans-contrôle domine -> ils n'entrent pas dans la zone.")
