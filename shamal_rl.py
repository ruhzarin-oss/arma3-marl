"""shamal_rl — PHASE 2 : RL fine-tune du warm-start SHAMAL (DÉPASSER LAMBS).

PRÉPARÉ, à NE lancer qu'après validation de la phase 1 (copie >= LAMBS via shamal_eval.py) et sur
ton feu vert explicite. Charge shamal_bc.pt dans un Net, continue par PPO (ppo_iters, train_soldier_pbt)
sur la récompense du sandbox -> la politique part du niveau LAMBS et l'améliore (plancher LAMBS,
plafond illimité). Même env/archi que la copie -> continuité parfaite.

Smoke (prouve que le warm-start charge et que le PPO tourne) :  python shamal_rl.py smoke
"""
import sys, time, os
import torch
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
BASE = "/home/younes/arma3-marl"
RP = BASE + "/replica.npz"
ARMA = os.environ.get("SHAMAL_ARMA") == "1"   # SHAMAL_ARMA=1 -> variante obs Arma-cheap
BC = BASE + ("/shamal_arma_bc.pt" if ARMA else "/shamal_bc.pt")
OUT = BASE + ("/shamal_arma_win.pt" if ARMA else "/shamal_win.pt")
# ENTRAÎNEMENT sur les villes de RELIEF (comme la copie) ; éval ensuite sur les held-out
TRAIN_MAPS = [BASE + "/replica_%s.npz" % c for c in ("ronda", "matera", "positano", "sarajevo")]
# RÉCOMPENSE « GAGNER » : la mort beaucoup moins punie (0.4 au lieu de 1.5), victoire + kills mieux payés
WIN_REWARD = dict(death_pen=0.15, suffer_pen=0.25, win_bonus=2.5, kill_w=2.5)


def mkenv(n, sd, A=9, D=6, path=RP):
    return AssaultTerrain(num_envs=n, A=A, D=D, R_spawn=115.0, relief=40.0, hit=0.10,
                          shell_obs=not ARMA, team_obs=True, suffer=True, postures=True, hull=True,
                          arma_obs=ARMA, replica=True, replica_path=path, max_steps=60, device=DEV, seed=sd,
                          **WIN_REWARD)


if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    ITERS = 2 if SMOKE else 400
    N = 64 if SMOKE else 1024
    A, D = 9, 6
    maps = TRAIN_MAPS[:2] if SMOKE else TRAIN_MAPS
    envs = [mkenv(N, i, A, D, m) for i, m in enumerate(maps)]    # RL multi-carte (villes de relief)
    obs = [e.reset() for e in envs]
    O, NA = envs[0].obs_dim, envs[0].n_actions
    net = Net(O, NA, 512, 3).to(DEV)
    net.load_state_dict(torch.load(BC, map_location=DEV))       # WARM-START = la copie LAMBS
    opt = torch.optim.Adam(net.parameters(), 3e-4)
    print("=== SHAMAL RL 'GAGNER' depuis warm-start BC  SMOKE=%s | %d cartes | recompense %s ===" % (SMOKE, len(maps), WIN_REWARD), flush=True)
    t0 = time.time()
    for it in range(ITERS):
        ei = it % len(envs)                                     # tourne sur les cartes
        obs[ei] = ppo_iters(net, opt, envs[ei], obs[ei], K=1, O=O)
        if it % 20 == 0 or it == ITERS - 1:
            print("  [RL it %d] %.0fs" % (it, time.time() - t0), flush=True)
    torch.save(net.state_dict(), OUT)
    print("SHAMAL_RL_DONE  -> %s" % OUT, flush=True)
