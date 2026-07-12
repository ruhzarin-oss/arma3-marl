"""replica_pbt — PBT (recette du toy souffrance) sur l'assaut d'escouade de la REPLIQUE du complexe.
Population de P squads ; entrainer K iters -> classer par garnison neutralisee -> bas tiers <- copies MUTEES
du haut tiers. But : qu'UNE squad decouvre un assaut qui perce -> propagation a toute la population (exploration).
args: gens kiter P"""
import sys, time
import torch
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import gae, ppo_iters, evaluate
DEV = "cuda:0"
GENS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
K = int(sys.argv[2]) if len(sys.argv) > 2 else 12
P = int(sys.argv[3]) if len(sys.argv) > 3 else 8
NE, NEVAL, A, D = 512, 512, 20, 10
RP = "/home/younes/arma3-marl/replica.npz"

mk = lambda n, sd: AssaultTerrain(num_envs=n, A=A, D=D, relief=40.0, hit=0.10, shell_obs=True, team_obs=True,
                                  replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)
train_envs = [mk(NE, 200 + s) for s in range(P)]
O, NA = train_envs[0].obs_dim, train_envs[0].n_actions
nets = [Net(O, NA, 512, 3).to(DEV) for _ in range(P)]
opts = [torch.optim.Adam(n.parameters(), 3e-4) for n in nets]
obs = [e.reset() for e in train_envs]
ev = mk(NEVAL, 9)
print("===== PBT EXPLORATION sur la REPLIQUE : P=%d squads %dv%d, K=%d/gen, G=%d =====" % (P, A, D, K, GENS), flush=True)
t0 = time.time(); best = -1.0
for gen in range(GENS):
    for p in range(P):
        obs[p] = ppo_iters(nets[p], opts[p], train_envs[p], obs[p], K, O)
    fits = [evaluate(nets[p], ev)[0] for p in range(P)]              # [0] = garnison neutralisee
    order = sorted(range(P), key=lambda p: fits[p], reverse=True); b = order[0]
    print("  gen %d | MEILLEUR garnison neutralisee %.0f%% | moy %.0f%% | %.0fs" %
          (gen, 100 * fits[b], 100 * sum(fits) / P, time.time() - t0), flush=True)
    if fits[b] > best:
        best = fits[b]; torch.save(nets[b].state_dict(), "/home/younes/arma3-marl/squad_pbt.pt")
    nt = max(1, P // 3)                                              # bas tiers <- copies mutees du haut tiers
    for j in range(nt):
        loser, winner = order[-1 - j], order[j]
        nets[loser].load_state_dict(nets[winner].state_dict())
        with torch.no_grad():
            for pr in nets[loser].parameters():
                pr.add_(torch.randn_like(pr) * 0.03)
        opts[loser] = torch.optim.Adam(nets[loser].parameters(), 3e-4); obs[loser] = train_envs[loser].reset()
print("\n>>> PBT REPLIQUE final : MEILLEURE garnison neutralisee %.0f%%" % (100 * best), flush=True)
print("PBT REPLICA FINI", flush=True)
